"""

Generate a controlled incremental batch for the e-commerce source system.

IMPORTANT:

- This script GENERATES files only. It does not mutate RDS.

- Review/validate the generated batch before applying it to RDS.

- Run from the project root:

    python -m data_generator.scripts.generate_incremental_data

"""

import csv

import json

import random

import string

from collections import defaultdict

from datetime import datetime, timedelta

from pathlib import Path

import pandas as pd

from data_generator.database.connection import get_connection

from data_generator.config.customer_config import (

    CUSTOMER_FIRST_NAMES,

    CUSTOMER_LAST_NAMES,

    EMAIL_DOMAINS,

)

from data_generator.config.customer_event_config import (

    DEVICE_TYPE_DISTRIBUTION,

    EVENT_TYPE_DISTRIBUTION,

)

from data_generator.config.product_catalog import PRODUCT_CATALOG

from data_generator.config.product_models import PRODUCT_MODELS

from data_generator.config.product_variants import PRODUCT_VARIANTS

from data_generator.config.seller_config import (

    SELLER_NAME_MIDDLES,

    SELLER_NAME_PREFIXES,

    SELLER_NAME_SUFFIXES,

)

from data_generator.config.order_config import (

    ORDER_ITEM_COUNT_MIN,

    ORDER_ITEM_COUNT_MAX,

)

from data_generator.config.payment_config import (

    PAYMENT_METHOD_DISTRIBUTION,

)

from data_generator.generators.order_financials import calculate_order_financials

from data_generator.generators.products import (

    build_product_type_pool,

    generate_product_name,

)

# -------------------------------------------------------------------

# -------------------------------------------------------------------
# Runtime batch configuration
# -------------------------------------------------------------------
# Batch dates, update timestamps, random seed, and source watermark are
# discovered automatically at runtime. Nothing below should be edited for
# a new batch.
#
# Simulation policy:
# - The batch folder and event partition use the current UTC date.
# - The batch window is current UTC midnight (or just after the source
#   watermark) through the generation time.
# - Update timestamps are distributed inside that window so they are <= utcNow().
#
NEW_CUSTOMERS = 10
NEW_SELLERS = 5
NEW_PRODUCTS = 10
NEW_ORDERS = 50
NEW_EVENTS = 500

CUSTOMER_UPDATES = 5
PRODUCT_UPDATES = 5
ORDER_UPDATES = 10
PAYMENT_UPDATES = 5

HISTORICAL_EVENT_MAX_ID = 250000
UPDATE_OFFSETS = {
    "customers": timedelta(hours=1),
    "products": timedelta(hours=2),
    "orders": timedelta(hours=3),
    "payments": timedelta(hours=4),
}

PROJECT_ROOT = Path(".")
INCREMENTAL_BASE = (
    PROJECT_ROOT / "data_generator" / "output" / "incremental"
)
EVENT_OUTPUT_BASE = (
    PROJECT_ROOT / "data_generator" / "output" / "customer_events"
)

# These are populated by discover_batch_context().
RANDOM_SEED = None
SOURCE_WATERMARK = None
BATCH_START = None
BATCH_END = None
BATCH_ID = None
EVENT_MONTH = None
OUTPUT_ROOT = None
EVENT_OUTPUT_ROOT = None
UPDATE_CUSTOMERS_AT = None
UPDATE_PRODUCTS_AT = None
UPDATE_ORDERS_AT = None
UPDATE_PAYMENTS_AT = None

def fetch_df(connection, sql, params=()):

    return pd.read_sql(sql, connection, params=params)

def write_csv(path, rows):

    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:

        path.write_text("", encoding="utf-8")

        return

    columns = list(rows[0].keys())

    with path.open("w", newline="", encoding="utf-8") as f:

        writer = csv.DictWriter(f, fieldnames=columns)

        writer.writeheader()

        for row in rows:

            writer.writerow(row)

def serialize_value(value):

    if isinstance(value, datetime):

        return value.isoformat()

    return value

def write_json(path, payload):

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:

        json.dump(

            payload,

            f,

            indent=2,

            default=serialize_value,

        )

def weighted_choice(distribution):

    values = list(distribution.keys())

    weights = list(distribution.values())

    return random.choices(values, weights=weights, k=1)[0]

def random_timestamp(start, end):

    total_seconds = int((end - start).total_seconds())

    return start + timedelta(

        seconds=random.randint(0, total_seconds)

    )

def generate_session_id(length=16):

    characters = string.ascii_letters + string.digits

    return "".join(

        random.choices(characters, k=length)

    )

def generate_seller_name(used_names):

    while True:

        name = (

            f"{random.choice(SELLER_NAME_PREFIXES)} "

            f"{random.choice(SELLER_NAME_MIDDLES)} "

            f"{random.choice(SELLER_NAME_SUFFIXES)}"

        )

        if name not in used_names:

            used_names.add(name)

            return name

def generate_customer_identity(customer_id):

    first_name = random.choice(CUSTOMER_FIRST_NAMES)

    last_name = random.choice(CUSTOMER_LAST_NAMES)

    domain = random.choice(EMAIL_DOMAINS)

    return {

        "first_name": first_name,

        "last_name": last_name,

        "customer_name": f"{first_name} {last_name}",

        "email": (

            f"{first_name.lower()}."

            f"{last_name.lower()}."

            f"{customer_id}@{domain}"

        ),

    }

def get_next_event_id():
    """
    Return the next event_id.

    Existing incremental JSONL files are the runtime state for event IDs.
    If no incremental event exists yet, continue after the historical
    event range defined by HISTORICAL_EVENT_MAX_ID.
    """
    max_event_id = HISTORICAL_EVENT_MAX_ID

    if EVENT_OUTPUT_BASE.exists():
        event_files = sorted(
            EVENT_OUTPUT_BASE.glob("event_month=*/customer_events_*.jsonl")
        )

        for event_file in event_files:
            with event_file.open("r", encoding="utf-8") as f:
                for line_number, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ValueError(
                            f"Invalid JSON in {event_file} at line "
                            f"{line_number}: {exc}"
                        ) from exc

                    event_id = record.get("event_id")
                    if not isinstance(event_id, int):
                        raise ValueError(
                            f"Invalid event_id in {event_file} at line "
                            f"{line_number}: expected integer."
                        )

                    max_event_id = max(max_event_id, event_id)

    return max_event_id + 1

def parse_timestamp(value, field_name):
    """Parse an ISO timestamp from a local manifest."""
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid {field_name} timestamp in batch manifest: {value!r}"
        ) from exc

def find_unapplied_local_batches():
    """
    Prevent generation of a second batch while an earlier generated batch
    is still waiting to be applied.

    This protects the source simulation from creating gaps or ambiguous
    batch ordering.
    """
    if not INCREMENTAL_BASE.exists():
        return []

    pending = []

    for manifest_path in sorted(
        INCREMENTAL_BASE.glob("*/batch_manifest.json")
    ):
        with manifest_path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)

        status = manifest.get("apply_status")
        if status != "APPLIED":
            pending.append(
                {
                    "batch_id": manifest.get("batch_id"),
                    "status": status,
                    "path": manifest_path,
                }
            )

    return pending

def get_latest_local_batch_end():
    """Return the end timestamp of the latest successfully applied batch."""
    if not INCREMENTAL_BASE.exists():
        return None

    latest_end = None

    for manifest_path in sorted(
        INCREMENTAL_BASE.glob("*/batch_manifest.json")
    ):
        with manifest_path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)

        if manifest.get("apply_status") != "APPLIED":
            continue

        batch_end = parse_timestamp(
            manifest.get("batch_end"),
            "batch_end",
        )

        if latest_end is None or batch_end > latest_end:
            latest_end = batch_end

    return latest_end

def get_source_watermark(connection):
    """
    Discover the latest source-system updated_at value.

    The generator uses the source database as the source-of-truth for
    deciding where the next simulated batch begins. Fabric maintains its
    own extraction/processing watermark separately.
    """
    sql = """
    SELECT MAX(source_updated_at) AS source_watermark
    FROM
    (
        SELECT MAX(updated_at) AS source_updated_at
        FROM dbo.customers

        UNION ALL

        SELECT MAX(updated_at)
        FROM dbo.sellers

        UNION ALL

        SELECT MAX(updated_at)
        FROM dbo.products

        UNION ALL

        SELECT MAX(updated_at)
        FROM dbo.orders

        UNION ALL

        SELECT MAX(updated_at)
        FROM dbo.order_items

        UNION ALL

        SELECT MAX(updated_at)
        FROM dbo.payments
    ) AS source_watermarks
    """

    row = fetch_df(connection, sql).iloc[0]
    watermark = row["source_watermark"]

    if pd.isna(watermark):
        raise ValueError(
            "Could not determine the source-system watermark."
        )

    if not isinstance(watermark, datetime):
        watermark = pd.to_datetime(watermark).to_pydatetime()

    return watermark

def next_calendar_day_start(timestamp):
    """Return midnight at the start of the next calendar day."""
    return (
        timestamp + timedelta(days=1)
    ).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

def discover_batch_context(connection):
    """
    Build one incremental batch for the current UTC date.

    The source watermark is used as a safety boundary, not to choose a
    historical batch date. All generated timestamps must be newer than the
    current source watermark and no later than the current UTC time, matching
    the Fabric pipeline's utcNow() upper bound.

    The project currently supports one batch directory per calendar date.
    """
    pending = find_unapplied_local_batches()

    if pending:
        details = ", ".join(
            f"{item['batch_id']} ({item['status']})"
            for item in pending
        )
        raise RuntimeError(
            "An incremental batch is already generated but not marked "
            f"APPLIED: {details}. Apply or resolve that batch before "
            "generating another batch."
        )

    source_watermark = get_source_watermark(connection)

    # SQL Server source timestamps are stored as timezone-naive UTC values.
    # Use the same UTC clock basis as Fabric's utcNow().
    now_utc = datetime.utcnow().replace(microsecond=0)
    batch_start = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    batch_end = now_utc

    if source_watermark >= batch_end:
        raise RuntimeError(
            "The source watermark is at or beyond the current UTC time. "
            "A current-date batch cannot safely create newer source timestamps."
        )

    if source_watermark >= batch_start:
        batch_start = source_watermark + timedelta(microseconds=1)

    if batch_start >= batch_end:
        raise RuntimeError(
            "There is no time window after the source watermark to generate "
            "this batch. Try again later or review source timestamps."
        )

    batch_id = now_utc.strftime("%Y-%m-%d")
    event_month = now_utc.strftime("%Y-%m")

    output_root = INCREMENTAL_BASE / batch_id
    event_output_root = EVENT_OUTPUT_BASE / f"event_month={event_month}"

    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(
            f"Batch output directory already exists and is not empty: "
            f"{output_root}. Resolve the existing batch instead of overwriting it."
        )

    # Spread the four table updates through the available current-date window.
    # This keeps every update newer than the source watermark and <= utcNow().
    window = batch_end - batch_start
    update_times = {
        "customers": batch_start + window * 1 / 5,
        "products": batch_start + window * 2 / 5,
        "orders": batch_start + window * 3 / 5,
        "payments": batch_start + window * 4 / 5,
    }

    return {
        "source_watermark": source_watermark,
        "batch_start": batch_start,
        "batch_end": batch_end,
        "batch_id": batch_id,
        "event_month": event_month,
        "output_root": output_root,
        "event_output_root": event_output_root,
        "random_seed": int(now_utc.strftime("%Y%m%d")),
        "update_customers_at": update_times["customers"],
        "update_products_at": update_times["products"],
        "update_orders_at": update_times["orders"],
        "update_payments_at": update_times["payments"],
    }

def activate_batch_context(context):
    """Expose the discovered context to the existing generator functions."""
    global RANDOM_SEED
    global SOURCE_WATERMARK
    global BATCH_START
    global BATCH_END
    global BATCH_ID
    global EVENT_MONTH
    global OUTPUT_ROOT
    global EVENT_OUTPUT_ROOT
    global UPDATE_CUSTOMERS_AT
    global UPDATE_PRODUCTS_AT
    global UPDATE_ORDERS_AT
    global UPDATE_PAYMENTS_AT

    RANDOM_SEED = context["random_seed"]
    SOURCE_WATERMARK = context["source_watermark"]
    BATCH_START = context["batch_start"]
    BATCH_END = context["batch_end"]
    BATCH_ID = context["batch_id"]
    EVENT_MONTH = context["event_month"]
    OUTPUT_ROOT = context["output_root"]
    EVENT_OUTPUT_ROOT = context["event_output_root"]
    UPDATE_CUSTOMERS_AT = context["update_customers_at"]
    UPDATE_PRODUCTS_AT = context["update_products_at"]
    UPDATE_ORDERS_AT = context["update_orders_at"]
    UPDATE_PAYMENTS_AT = context["update_payments_at"]

def get_next_ids(connection):

    sql = """

    SELECT

        (SELECT ISNULL(MAX(customer_id), 0) FROM dbo.customers) AS max_customer_id,

        (SELECT ISNULL(MAX(seller_id), 0) FROM dbo.sellers) AS max_seller_id,

        (SELECT ISNULL(MAX(product_id), 0) FROM dbo.products) AS max_product_id,

        (SELECT ISNULL(MAX(order_id), 0) FROM dbo.orders) AS max_order_id,

        (SELECT ISNULL(MAX(order_item_id), 0) FROM dbo.order_items) AS max_order_item_id,

        (SELECT ISNULL(MAX(payment_id), 0) FROM dbo.payments) AS max_payment_id

    """

    row = fetch_df(connection, sql).iloc[0]

    return {

        "customer_id": int(row["max_customer_id"]) + 1,

        "seller_id": int(row["max_seller_id"]) + 1,

        "product_id": int(row["max_product_id"]) + 1,

        "order_id": int(row["max_order_id"]) + 1,

        "order_item_id": int(row["max_order_item_id"]) + 1,

        "payment_id": int(row["max_payment_id"]) + 1,

        "event_id": get_next_event_id(),

    }

def load_reference_data(connection):

    locations = fetch_df(

        connection,

        """

        SELECT

            location_id,

            pincode,

            city,

            district,

            state,

            region,

            country

        FROM dbo.locations

        """,

    )

    categories = fetch_df(

        connection,

        """

        SELECT

            category_id,

            category_name,

            category_status

        FROM dbo.categories

        """,

    )

    existing_product_names = set(

        fetch_df(

            connection,

            "SELECT product_name FROM dbo.products",

        )["product_name"].tolist()

    )

    existing_seller_names = set(

        fetch_df(

            connection,

            "SELECT seller_name FROM dbo.sellers",

        )["seller_name"].tolist()

    )

    return (

        locations,

        categories,

        existing_product_names,

        existing_seller_names,

    )

def get_recently_updated_customer_ids(max_batches=3):
    """Return customer IDs updated in the most recent applied local batches.

    This local history prevents the generator from selecting the same small
    set of low customer IDs for every consecutive batch. Only manifests marked
    APPLIED are considered; generated-but-unapplied batches are not history.
    """
    if not INCREMENTAL_BASE.exists():
        return set()

    applied_batches = []
    for manifest_path in INCREMENTAL_BASE.glob("*/batch_manifest.json"):
        try:
            with manifest_path.open("r", encoding="utf-8") as f:
                manifest = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                f"Cannot read batch manifest {manifest_path}: {exc}"
            ) from exc

        if manifest.get("apply_status") != "APPLIED":
            continue

        applied_batches.append((
            parse_timestamp(manifest.get("batch_end"), "batch_end"),
            manifest_path.parent,
        ))

    applied_batches.sort(key=lambda item: item[0], reverse=True)
    recent_customer_ids = set()

    for _, batch_dir in applied_batches[:max_batches]:
        updates_path = batch_dir / "customer_updates.csv"
        if not updates_path.exists():
            # An applied batch without this file cannot provide update history.
            continue

        with updates_path.open("r", newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                raw_id = row.get("customer_id")
                if raw_id not in (None, ""):
                    try:
                        recent_customer_ids.add(int(raw_id))
                    except ValueError as exc:
                        raise ValueError(
                            f"Invalid customer_id {raw_id!r} in {updates_path}."
                        ) from exc

    return recent_customer_ids

def get_recently_updated_product_ids(max_batches=3):
    """Return product IDs updated in the most recent applied local batches.

    The local manifests provide a short history for this portfolio simulation,
    preventing the product selector from repeatedly choosing the lowest IDs.
    Only batches marked APPLIED are considered; pending batches are not history.
    """
    if not INCREMENTAL_BASE.exists():
        return set()

    applied_batches = []
    for manifest_path in INCREMENTAL_BASE.glob("*/batch_manifest.json"):
        try:
            with manifest_path.open("r", encoding="utf-8") as f:
                manifest = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                f"Cannot read batch manifest {manifest_path}: {exc}"
            ) from exc

        if manifest.get("apply_status") != "APPLIED":
            continue

        applied_batches.append((
            parse_timestamp(manifest.get("batch_end"), "batch_end"),
            manifest_path.parent,
        ))

    applied_batches.sort(key=lambda item: item[0], reverse=True)
    recent_product_ids = set()

    for _, batch_dir in applied_batches[:max_batches]:
        updates_path = batch_dir / "product_updates.csv"
        if not updates_path.exists():
            # A missing history file cannot contribute product IDs.
            continue

        with updates_path.open("r", newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                raw_id = row.get("product_id")
                if raw_id not in (None, ""):
                    try:
                        recent_product_ids.add(int(raw_id))
                    except ValueError as exc:
                        raise ValueError(
                            f"Invalid product_id {raw_id!r} in {updates_path}."
                        ) from exc

    return recent_product_ids

def select_existing_updates(connection, location_ids):
    """Select update candidates without repeatedly updating recent customers.

    Recent applied local batches are excluded, then the oldest source
    updated_at values are preferred. The source database remains authoritative
    for current values; local manifests are used only to avoid consecutive
    repeat selections in this portfolio simulation.
    """
    recently_updated_ids = get_recently_updated_customer_ids(max_batches=3)

    customer_sql = """
        SELECT TOP (?)
            customer_id,
            customer_status,
            location_id,
            updated_at
        FROM dbo.customers
    """
    customer_params = [CUSTOMER_UPDATES]

    if recently_updated_ids:
        placeholders = ", ".join("?" for _ in recently_updated_ids)
        customer_sql += f" WHERE customer_id NOT IN ({placeholders})"
        customer_params.extend(sorted(recently_updated_ids))

    customer_sql += " ORDER BY updated_at ASC, customer_id ASC"
    customer_updates = fetch_df(
        connection, customer_sql, tuple(customer_params)
    ).to_dict("records")

    if len(customer_updates) != CUSTOMER_UPDATES:
        raise ValueError(
            f"Could not select {CUSTOMER_UPDATES} customer rows for update "
            f"after excluding {len(recently_updated_ids)} customers updated "
            "in recent applied batches. Check source row availability and "
            "local batch manifests."
        )

    selected_customer_ids = [int(row["customer_id"]) for row in customer_updates]
    if len(selected_customer_ids) != len(set(selected_customer_ids)):
        raise ValueError("Customer update selection contains duplicate customer IDs.")
    repeated_ids = set(selected_customer_ids) & recently_updated_ids
    if repeated_ids:
        raise ValueError(
            f"Customer update selection reused recently updated IDs: "
            f"{sorted(repeated_ids)}"
        )

    customer_update_rows = []
    for row in customer_updates:
        old_location_id = int(row["location_id"])
        alternatives = [x for x in location_ids if x != old_location_id]
        if not alternatives:
            raise ValueError(
                f"No alternative location exists for customer {row['customer_id']}."
            )

        new_location_id = random.choice(alternatives)
        customer_update_rows.append({
            "customer_id": int(row["customer_id"]),
            "old_location_id": old_location_id,
            "new_location_id": int(new_location_id),
            "old_customer_status": row["customer_status"],
            "new_customer_status": row["customer_status"],
            "updated_at": UPDATE_CUSTOMERS_AT,
        })

    # Exclude products changed in the most recent applied batches. Without this
    # history filter, ORDER BY product_id repeatedly selects the same first IDs.
    recently_updated_product_ids = get_recently_updated_product_ids(max_batches=3)

    product_sql = """
        SELECT TOP (?)
            product_id,
            unit_price,
            product_status
        FROM dbo.products
        WHERE product_status = 'Active'
    """
    product_params = [PRODUCT_UPDATES]

    if recently_updated_product_ids:
        placeholders = ", ".join("?" for _ in recently_updated_product_ids)
        product_sql += f" AND product_id NOT IN ({placeholders})"
        product_params.extend(sorted(recently_updated_product_ids))

    product_sql += " ORDER BY NEWID()"
    product_updates = fetch_df(
        connection, product_sql, tuple(product_params)
    ).to_dict("records")

    if len(product_updates) != PRODUCT_UPDATES:
        raise ValueError(
            f"Could not select {PRODUCT_UPDATES} active products for update "
            f"after excluding {len(recently_updated_product_ids)} product IDs "
            "updated in recent applied batches. Check source rows and local manifests."
        )

    selected_product_ids = [int(row["product_id"]) for row in product_updates]
    if len(selected_product_ids) != len(set(selected_product_ids)):
        raise ValueError("Product update selection contains duplicate product IDs.")
    repeated_product_ids = set(selected_product_ids) & recently_updated_product_ids
    if repeated_product_ids:
        raise ValueError(
            f"Product update selection reused recently updated IDs: "
            f"{sorted(repeated_product_ids)}"
        )

    product_update_rows = []
    for row in product_updates:
        old_price = float(row["unit_price"])
        new_price = round(old_price * 1.05, 2)
        if new_price == old_price:
            raise ValueError(
                f"Price update for product {row['product_id']} did not change the price."
            )
        product_update_rows.append({
            "product_id": int(row["product_id"]),
            "old_unit_price": old_price,
            "new_unit_price": new_price,
            "old_product_status": row["product_status"],
            "new_product_status": row["product_status"],
            "updated_at": UPDATE_PRODUCTS_AT,
        })

    order_updates = fetch_df(
        connection,
        """
        SELECT TOP (10)
            order_id,
            order_status,
            shipping_location_id
        FROM dbo.orders
        WHERE order_status IN ('Pending', 'Confirmed', 'Shipped')
        ORDER BY order_id
        """,
    ).to_dict("records")

    if len(order_updates) != ORDER_UPDATES:
        raise ValueError("Could not select 10 orders in a valid transition state.")

    transition = {
        "Pending": "Confirmed",
        "Confirmed": "Shipped",
        "Shipped": "Delivered",
    }
    order_update_rows = []
    for row in order_updates:
        old_location_id = int(row["shipping_location_id"])
        alternatives = [x for x in location_ids if x != old_location_id]
        if not alternatives:
            raise ValueError(
                f"No alternative shipping location exists for order {row['order_id']}."
            )
        order_update_rows.append({
            "order_id": int(row["order_id"]),
            "old_order_status": row["order_status"],
            "new_order_status": transition[row["order_status"]],
            "old_shipping_location_id": old_location_id,
            "new_shipping_location_id": int(random.choice(alternatives)),
            "updated_at": UPDATE_ORDERS_AT,
        })

    payment_updates = fetch_df(
        connection,
        """
        SELECT TOP (5)
            p.payment_id,
            p.order_id,
            p.payment_status,
            p.payment_amount
        FROM dbo.payments AS p
        WHERE p.payment_status IN ('Pending', 'Failed')
          AND NOT EXISTS (
              SELECT 1
              FROM dbo.payments AS p2
              WHERE p2.order_id = p.order_id
                AND p2.payment_status = 'Completed'
          )
        ORDER BY p.payment_id
        """,
    ).to_dict("records")

    if len(payment_updates) != PAYMENT_UPDATES:
        raise ValueError("Could not select 5 safe payment updates.")

    payment_update_rows = [
        {
            "payment_id": int(row["payment_id"]),
            "order_id": int(row["order_id"]),
            "old_payment_status": row["payment_status"],
            "new_payment_status": "Completed",
            "payment_amount": float(row["payment_amount"]),
            "updated_at": UPDATE_PAYMENTS_AT,
        }
        for row in payment_updates
    ]

    return (
        customer_update_rows,
        product_update_rows,
        order_update_rows,
        payment_update_rows,
    )

def generate_new_customers(

    start_id,

    location_ids,

):

    rows = []

    for offset in range(NEW_CUSTOMERS):

        customer_id = start_id + offset

        identity = generate_customer_identity(customer_id)

        created_at = BATCH_START

        rows.append(

            {

                "customer_id": customer_id,

                "customer_name": identity["customer_name"],

                "email": identity["email"],

                "phone": f"9{random.randint(100000000, 999999999)}",

                "location_id": random.choice(location_ids),

                "customer_status": "Active",

                "signup_date": BATCH_START.date(),

                "created_at": created_at,

                "updated_at": created_at,

            }

        )

    return rows

def generate_new_sellers(

    start_id,

    location_ids,

    used_names,

):

    rows = []

    for offset in range(NEW_SELLERS):

        seller_id = start_id + offset

        rows.append(

            {

                "seller_id": seller_id,

                "seller_name": generate_seller_name(used_names),

                "location_id": random.choice(location_ids),

                "seller_status": "Active",

                "created_at": BATCH_START,

                "updated_at": BATCH_START,

            }

        )

    return rows

def generate_new_products(

    start_id,

    categories,

    used_names,

):

    category_lookup = {

        row["category_name"]: int(row["category_id"])

        for row in categories

        if row["category_status"] == "Active"

    }

    product_type_pool = build_product_type_pool()

    rows = []

    for offset in range(NEW_PRODUCTS):

        product_id = start_id + offset

        info = random.choice(product_type_pool)

        category_name = info["category_name"]

        product_type = info["product_type"]

        if category_name not in category_lookup:

            raise ValueError(

                f"Category '{category_name}' not found in RDS."

            )

        config = PRODUCT_CATALOG[category_name][product_type]

        brand = random.choice(config["brands"])

        product_name = generate_product_name(

            brand,

            product_type,

            product_id,

            used_names,

        )

        unit_price = round(

            random.uniform(

                config["min_price"],

                config["max_price"],

            ),

            2,

        )

        rows.append(

            {

                "product_id": product_id,

                "category_id": category_lookup[category_name],

                "product_name": product_name,

                "brand": brand,

                "product_type": product_type,

                "unit_price": unit_price,

                "product_status": "Active",

                "created_at": BATCH_START,

                "updated_at": BATCH_START,

            }

        )

    return rows

def build_seller_product_mapping(

    seller_ids,

    product_ids,

):

    if not seller_ids or not product_ids:

        raise ValueError("Seller/product pools cannot be empty.")

    mapping = {seller_id: set() for seller_id in seller_ids}

    # Guarantee every product has at least one eligible seller.

    for index, product_id in enumerate(product_ids):

        seller_id = seller_ids[index % len(seller_ids)]

        mapping[seller_id].add(product_id)

    # Add additional relationships.

    for seller_id in seller_ids:

        target = random.randint(6, min(10, len(product_ids)))

        while len(mapping[seller_id]) < target:

            mapping[seller_id].add(random.choice(product_ids))

    return mapping

def generate_new_orders(

    start_id,

    new_customers,

    location_ids,

):

    rows = []

    for offset in range(NEW_ORDERS):

        order_id = start_id + offset

        customer = random.choice(new_customers)

        # Payments are generated up to 120 minutes after the order.
        # Keep order timestamps at least 120 minutes before BATCH_END so
        # payment created_at/updated_at cannot spill into the next day.
        latest_order_timestamp = BATCH_END - timedelta(minutes=120)
        order_date = random_timestamp(
            BATCH_START,
            latest_order_timestamp,
        )

        rows.append(

            {

                "order_id": order_id,

                "customer_id": customer["customer_id"],

                "order_date": order_date,

                "order_status": "Confirmed",

                "shipping_location_id": random.choice(location_ids),

                "created_at": order_date,

                "updated_at": order_date,

            }

        )

    return rows

def generate_new_order_items(

    start_id,

    orders,

    products,

    sellers,

    seller_product_mapping,

):

    product_lookup = {

        product["product_id"]: product

        for product in products

    }

    product_to_sellers = defaultdict(list)

    for seller_id, product_ids in seller_product_mapping.items():

        for product_id in product_ids:

            product_to_sellers[product_id].append(seller_id)

    rows = []

    next_item_id = start_id

    for order in orders:

        available_product_ids = list(product_to_sellers.keys())

        item_count = random.randint(

            ORDER_ITEM_COUNT_MIN,

            min(ORDER_ITEM_COUNT_MAX, len(available_product_ids)),

        )

        selected_products = random.sample(

            available_product_ids,

            item_count,

        )

        for product_id in selected_products:

            seller_id = random.choice(

                product_to_sellers[product_id]

            )

            product = product_lookup[product_id]

            quantity = random.randint(1, 5)

            gross = quantity * float(product["unit_price"])

            rows.append(

                {

                    "order_item_id": next_item_id,

                    "order_id": order["order_id"],

                    "product_id": product_id,

                    "seller_id": seller_id,

                    "quantity": quantity,

                    "unit_price": round(

                        float(product["unit_price"]),

                        2,

                    ),

                    "discount_amount": round(

                        gross * random.uniform(0.00, 0.20),

                        2,

                    ),

                    "created_at": order["created_at"],

                    "updated_at": order["updated_at"],

                }

            )

            next_item_id += 1

    return rows

def generate_new_payments(

    start_id,

    orders,

):

    methods = list(PAYMENT_METHOD_DISTRIBUTION.keys())

    weights = list(PAYMENT_METHOD_DISTRIBUTION.values())

    rows = []

    for offset, order in enumerate(orders):

        payment_id = start_id + offset

        payment_timestamp = order["order_date"] + timedelta(

            minutes=random.randint(1, 120)

        )

        rows.append(

            {

                "payment_id": payment_id,

                "order_id": order["order_id"],

                "payment_timestamp": payment_timestamp,

                "payment_method": random.choices(

                    methods,

                    weights=weights,

                    k=1,

                )[0],

                "payment_amount": round(

                    order["total_amount"],

                    2,

                ),

                "payment_status": "Completed",

                "transaction_reference": (

                    f"TXN-{payment_id:08d}"

                ),

                "created_at": payment_timestamp,

                "updated_at": payment_timestamp,

            }

        )

    return rows

def generate_new_events(

    start_id,

    customer_ids,

    product_ids,

):

    rows = []

    for offset in range(NEW_EVENTS):

        event_id = start_id + offset

        rows.append(

            {

                "event_id": event_id,

                "customer_id": random.choice(customer_ids),

                "product_id": random.choice(product_ids),

                "event_type": weighted_choice(

                    EVENT_TYPE_DISTRIBUTION

                ),

                "event_timestamp": random_timestamp(

                    BATCH_START,

                    BATCH_END,

                ),

                "device_type": weighted_choice(

                    DEVICE_TYPE_DISTRIBUTION

                ),

                "session_id": generate_session_id(),

            }

        )

    return rows

def validate_batch(

    new_customers,

    new_sellers,

    new_products,

    new_orders,

    new_order_items,

    new_payments,

    new_events,

    customer_updates,

    product_updates,

    order_updates,

    payment_updates,

    next_ids,

):

    # ID ranges must continue from the source.

    checks = [

        (

            "customers",

            [x["customer_id"] for x in new_customers],

            next_ids["customer_id"],

        ),

        (

            "sellers",

            [x["seller_id"] for x in new_sellers],

            next_ids["seller_id"],

        ),

        (

            "products",

            [x["product_id"] for x in new_products],

            next_ids["product_id"],

        ),

        (

            "orders",

            [x["order_id"] for x in new_orders],

            next_ids["order_id"],

        ),

        (

            "order_items",

            [x["order_item_id"] for x in new_order_items],

            next_ids["order_item_id"],

        ),

        (

            "payments",

            [x["payment_id"] for x in new_payments],

            next_ids["payment_id"],

        ),

        (

            "events",

            [x["event_id"] for x in new_events],

            next_ids["event_id"],

        ),

    ]

    for name, ids, expected_start in checks:

        if len(ids) != len(set(ids)):

            raise ValueError(f"Duplicate IDs in {name}.")

        if ids and min(ids) != expected_start:

            raise ValueError(

                f"{name} IDs do not start at expected {expected_start}."

            )

    # New customer references.

    customer_ids = {

        x["customer_id"] for x in new_customers

    }

    if any(

        order["customer_id"] not in customer_ids

        for order in new_orders

    ):

        raise ValueError("New order references an unexpected customer.")

    # Order item references and financials.

    # Order item references.

    # Financials were already calculated during generation.

    # Do NOT recalculate them here because the financial generator

    # may contain randomized discount/tax/shipping logic.

    order_lookup = {

        x["order_id"]: x for x in new_orders

    }

    items_by_order = defaultdict(list)

    for item in new_order_items:

        if item["order_id"] not in order_lookup:

            raise ValueError(

                "Order item references unknown new order."

            )

        items_by_order[item["order_id"]].append(item)

    for order in new_orders:

        items = items_by_order[order["order_id"]]

        if not items:

            raise ValueError(

                f"Order {order['order_id']} has no items."

            )

    # Payment reconciliation for the new batch.

    payment_by_order = {

        p["order_id"]: p

        for p in new_payments

    }

    for order in new_orders:

        payment = payment_by_order.get(order["order_id"])

        if payment is None:

            raise ValueError(

                f"Order {order['order_id']} has no new payment."

            )

        if round(payment["payment_amount"], 2) != round(

            order["total_amount"], 2

        ):

            raise ValueError(

                f"Payment mismatch for order {order['order_id']}."

            )

    # All updates must be after the source-system watermark discovered
    # for this generated batch.

    update_groups = [
        customer_updates,
        product_updates,
        order_updates,
        payment_updates,
    ]

    for group in update_groups:
        for row in group:
            if row["updated_at"] <= SOURCE_WATERMARK:
                raise ValueError(
                    "Generated update is not after the current source watermark."
                )
            if row["updated_at"] > BATCH_END:
                raise ValueError(
                    "Generated update timestamp is outside the batch window."
                )

    # New source rows must also belong to the generated batch window.
    # Keep entity/key context in errors so failures are diagnosable.
    timestamped_groups = [
        ("customers", new_customers, "customer_id"),
        ("sellers", new_sellers, "seller_id"),
        ("products", new_products, "product_id"),
        ("orders", new_orders, "order_id"),
        ("order_items", new_order_items, "order_item_id"),
        ("payments", new_payments, "payment_id"),
    ]

    for group_name, group, key_column in timestamped_groups:
        for row in group:
            for column in ("created_at", "updated_at"):
                value = row.get(column)

                if value is None:
                    raise ValueError(
                        f"{group_name}: record "
                        f"{row.get(key_column)!r} is missing {column}."
                    )

                if value < BATCH_START or value > BATCH_END:
                    raise ValueError(
                        f"{group_name}: record "
                        f"{row.get(key_column)!r} has {column}={value!r}, "
                        f"outside batch window "
                        f"[{BATCH_START!r}, {BATCH_END!r}]."
                    )

    # Customer update actually changes location.

    if any(

        x["old_location_id"] == x["new_location_id"]

        for x in customer_updates

    ):

        raise ValueError("A customer update did not change location.")

    # Product update actually changes price.

    if any(

        x["old_unit_price"] == x["new_unit_price"]

        for x in product_updates

    ):

        raise ValueError("A product update did not change price.")

    # Event IDs and timestamps.

    event_ids = [x["event_id"] for x in new_events]

    if event_ids != list(

        range(

            next_ids["event_id"],

            next_ids["event_id"] + len(new_events),

        )

    ):

        raise ValueError(

            "Event IDs are not sequential from the expected starting event_id."

        )

    if any(

        x["event_timestamp"] < BATCH_START

        or x["event_timestamp"] > BATCH_END

        for x in new_events

    ):

        raise ValueError(

            "An incremental event timestamp is outside the batch window."

        )

    if BATCH_START > BATCH_END:

        raise ValueError(

            "BATCH_START must be earlier than or equal to BATCH_END."

        )

    if BATCH_START.strftime("%Y-%m") != BATCH_END.strftime("%Y-%m"):

        raise ValueError(

            "BATCH_START and BATCH_END must belong to the same month "

            "for the event_month partition."

        )

    print("Incremental batch validation passed.")

def write_event_jsonl(events):

    EVENT_OUTPUT_ROOT.mkdir(

        parents=True,

        exist_ok=True,

    )

    output_file = (

        EVENT_OUTPUT_ROOT

        / f"customer_events_{BATCH_ID}.jsonl"

    )

    if output_file.exists():

        raise FileExistsError(

            f"Event output file already exists: {output_file}. "

            "Use a new BATCH_START date instead of overwriting an existing batch."

        )

    with output_file.open(

        "w",

        encoding="utf-8",

    ) as f:

        for event in events:

            row = dict(event)

            row["event_timestamp"] = event[

                "event_timestamp"

            ].isoformat()

            f.write(

                json.dumps(

                    row,

                    ensure_ascii=False,

                )

            )

            f.write("\n")

    return output_file

def main():
    print("========================================")
    print(" INCREMENTAL BATCH GENERATION")
    print("========================================")

    with get_connection() as connection:
        context = discover_batch_context(connection)
        activate_batch_context(context)
        random.seed(RANDOM_SEED)

        print(f"Source watermark: {SOURCE_WATERMARK.isoformat()}")
        print(f"Batch ID: {BATCH_ID}")
        print(f"Batch start: {BATCH_START.isoformat()}")
        print(f"Batch end: {BATCH_END.isoformat()}")
        print(f"Random seed: {RANDOM_SEED}")
        print()

        if BATCH_START > BATCH_END:
            raise ValueError(
                "Discovered batch_start is later than batch_end."
            )

        if BATCH_START.strftime("%Y-%m") != BATCH_END.strftime("%Y-%m"):
            raise ValueError(
                "Generated batch crosses a month boundary, which is not "
                "supported by the event_month partitioning design."
            )

        OUTPUT_ROOT.mkdir(
            parents=True,
            exist_ok=True,
        )

        (

            locations,

            categories,

            existing_product_names,

            existing_seller_names,

        ) = load_reference_data(connection)

        location_ids = [

            int(x) for x in locations["location_id"].tolist()

        ]

        next_ids = get_next_ids(connection)

        (

            customer_updates,

            product_updates,

            order_updates,

            payment_updates,

        ) = select_existing_updates(

            connection,

            location_ids,

        )

    new_customers = generate_new_customers(

        next_ids["customer_id"],

        location_ids,

    )

    new_sellers = generate_new_sellers(

        next_ids["seller_id"],

        location_ids,

        existing_seller_names,

    )

    new_products = generate_new_products(

        next_ids["product_id"],

        categories.to_dict("records"),

        existing_product_names,

    )

    # Use new + updated products for the new transaction batch.

    updated_product_ids = [

        row["product_id"] for row in product_updates

    ]

    product_pool = (

        new_products

        + [

            {

                "product_id": row["product_id"],

                "unit_price": row["new_unit_price"],

            }

            for row in product_updates

        ]

    )

    seller_ids = [

        row["seller_id"] for row in new_sellers

    ]

    product_ids = [

        row["product_id"] for row in product_pool

    ]

    seller_product_mapping = build_seller_product_mapping(

        seller_ids,

        product_ids,

    )

    new_orders = generate_new_orders(

        next_ids["order_id"],

        new_customers,

        location_ids,

    )

    new_order_items = generate_new_order_items(

        next_ids["order_item_id"],

        new_orders,

        product_pool,

        new_sellers,

        seller_product_mapping,

    )

    # Calculate order financials before generating payments.

    items_by_order = defaultdict(list)

    for item in new_order_items:

        items_by_order[item["order_id"]].append(item)

    for order in new_orders:

        financials = calculate_order_financials(

            items_by_order[order["order_id"]]

        )

        order.update(financials)

    new_payments = generate_new_payments(

        next_ids["payment_id"],

        new_orders,

    )

    # Include updated customers in events so the later SCD2 test

    # has events after their new effective timestamp.

    event_customer_ids = (

        [x["customer_id"] for x in new_customers]

        + [x["customer_id"] for x in customer_updates]

    )

    event_product_ids = [

        x["product_id"] for x in product_pool

    ]

    new_events = generate_new_events(

        next_ids["event_id"],

        event_customer_ids,

        event_product_ids,

    )

    validate_batch(

        new_customers,

        new_sellers,

        new_products,

        new_orders,

        new_order_items,

        new_payments,

        new_events,

        customer_updates,

        product_updates,

        order_updates,

        payment_updates,

        next_ids,

    )

    # Write INSERT batches.

    write_csv(

        OUTPUT_ROOT / "new_customers.csv",

        new_customers,

    )

    write_csv(

        OUTPUT_ROOT / "new_sellers.csv",

        new_sellers,

    )

    write_csv(

        OUTPUT_ROOT / "new_products.csv",

        new_products,

    )

    write_csv(

        OUTPUT_ROOT / "new_orders.csv",

        new_orders,

    )

    write_csv(

        OUTPUT_ROOT / "new_order_items.csv",

        new_order_items,

    )

    write_csv(

        OUTPUT_ROOT / "new_payments.csv",

        new_payments,

    )

    # Write UPDATE batches.

    write_csv(

        OUTPUT_ROOT / "customer_updates.csv",

        customer_updates,

    )

    write_csv(

        OUTPUT_ROOT / "product_updates.csv",

        product_updates,

    )

    write_csv(

        OUTPUT_ROOT / "order_updates.csv",

        order_updates,

    )

    write_csv(

        OUTPUT_ROOT / "payment_updates.csv",

        payment_updates,

    )

    event_file = write_event_jsonl(new_events)

    manifest = {

        "batch_id": BATCH_ID,

        "random_seed": RANDOM_SEED,

        "watermark_used": SOURCE_WATERMARK,

        "batch_start": BATCH_START,

        "batch_end": BATCH_END,

        "next_ids": next_ids,

        "counts": {

            "new_customers": len(new_customers),

            "new_sellers": len(new_sellers),

            "new_products": len(new_products),

            "new_orders": len(new_orders),

            "new_order_items": len(new_order_items),

            "new_payments": len(new_payments),

            "new_events": len(new_events),

            "customer_updates": len(customer_updates),

            "product_updates": len(product_updates),

            "order_updates": len(order_updates),

            "payment_updates": len(payment_updates),

        },

        "event_file": str(event_file),

        "apply_status": "NOT_APPLIED",

    }

    write_json(

        OUTPUT_ROOT / "batch_manifest.json",

        manifest,

    )

    print("\n========================================")

    print(" BATCH GENERATED SUCCESSFULLY")

    print("========================================")

    print(f"Output: {OUTPUT_ROOT}")

    print(f"Events: {event_file}")

    print(

        f"Event ID range: "

        f"{new_events[0]['event_id']} - {new_events[-1]['event_id']}"

    )

    print("\nNo RDS records were modified.")

if __name__ == "__main__":

    main()
