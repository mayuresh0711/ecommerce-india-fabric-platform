"""
Apply a generated incremental batch to AWS RDS transactionally.

Run from the project root:

    python -m data_generator.scripts.apply_incremental_data 2026-10-06

The script:
- selects the batch from the command-line batch ID
- validates the manifest and generated CSV/JSONL files before touching RDS
- refuses to re-apply a batch whose manifest is not NOT_APPLIED
- detects already-existing insert keys to protect against accidental re-application
- applies CSV changes transactionally to ecommerce_source
- propagates batch updated_at values for every mutable-table update
- verifies inserted keys, update timestamps, and operation counts before commit
- does NOT load customer-event JSON into RDS
- marks the manifest APPLIED only after a successful database commit

Important:
If the database commit succeeds but the manifest file cannot be updated,
DO NOT rerun the batch blindly. The pre-apply duplicate-key check is designed
to detect that situation and stop a subsequent run safely.
"""

import csv
import json
import sys
from datetime import datetime
from pathlib import Path


from data_generator.database.connection import get_connection


PROJECT_ROOT = Path(".")
INCREMENTAL_ROOT = PROJECT_ROOT / "data_generator" / "output" / "incremental"


INSERT_SPECS = {
    "new_customers": ("customers", "customer_id", "new_customers.csv"),
    "new_sellers": ("sellers", "seller_id", "new_sellers.csv"),
    "new_products": ("products", "product_id", "new_products.csv"),
    "new_orders": ("orders", "order_id", "new_orders.csv"),
    "new_order_items": ("order_items", "order_item_id", "new_order_items.csv"),
    "new_payments": ("payments", "payment_id", "new_payments.csv"),
}

UPDATE_SPECS = {
    "customer_updates": (
        "customers",
        "customer_id",
        ["location_id", "customer_status"],
        ["location_id", "customer_status"],
        "customer_updates.csv",
    ),
    "product_updates": (
        "products",
        "product_id",
        ["unit_price", "product_status"],
        ["unit_price", "product_status"],
        "product_updates.csv",
    ),
    "order_updates": (
        "orders",
        "order_id",
        ["order_status", "shipping_location_id"],
        ["order_status", "shipping_location_id"],
        "order_updates.csv",
    ),
    "payment_updates": (
        "payments",
        "payment_id",
        ["payment_status"],
        ["payment_status"],
        "payment_updates.csv",
    ),
}


def get_batch_id():
    """Return the required YYYY-MM-DD batch ID from the command line."""
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python -m data_generator.scripts.apply_incremental_data "
            "YYYY-MM-DD"
        )

    batch_id = sys.argv[1].strip()

    try:
        datetime.strptime(batch_id, "%Y-%m-%d")
    except ValueError:
        raise SystemExit(
            f"Invalid batch ID '{batch_id}'. Expected format YYYY-MM-DD."
        )

    return batch_id


def get_batch_paths(batch_id):
    batch_root = INCREMENTAL_ROOT / batch_id
    manifest_path = batch_root / "batch_manifest.json"
    return batch_root, manifest_path


def read_manifest(manifest_path):
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Manifest not found: {manifest_path}"
        )

    with manifest_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_csv(batch_root, filename):
    path = batch_root / filename

    if not path.exists():
        raise FileNotFoundError(f"Required CSV not found: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def qident(name):
    return "[" + name.replace("]", "]]") + "]"


def validate_unique_keys(rows, table, key_column, label):
    if not rows:
        return

    keys = [row.get(key_column, "") for row in rows]

    if any(key == "" for key in keys):
        raise ValueError(
            f"{label}: {key_column} contains a blank value."
        )

    seen = set()
    duplicates_set = set()
    for key in keys:
        if key in seen:
            duplicates_set.add(key)
        seen.add(key)
    duplicates = sorted(duplicates_set)

    if duplicates:
        preview = ", ".join(duplicates[:10])
        raise ValueError(
            f"{label}: duplicate {key_column} values found: {preview}"
        )


def validate_manifest_and_files(batch_id, batch_root, manifest):
    """Validate the generated batch without modifying RDS."""
    if manifest.get("batch_id") != batch_id:
        raise ValueError(
            f"Manifest batch_id is {manifest.get('batch_id')!r}, "
            f"but requested batch is {batch_id!r}."
        )

    if manifest.get("apply_status") != "NOT_APPLIED":
        raise RuntimeError(
            f"Batch status is {manifest.get('apply_status')!r}. "
            "Refusing to apply the batch again."
        )

    counts = manifest.get("counts")
    if not isinstance(counts, dict):
        raise ValueError("Manifest is missing the 'counts' object.")

    loaded = {}

    for name, (table, key_column, filename) in INSERT_SPECS.items():
        rows = read_csv(batch_root, filename)
        loaded[name] = rows

        expected = counts.get(name)
        if expected is None:
            raise ValueError(f"Manifest is missing count: {name}")

        if len(rows) != expected:
            raise ValueError(
                f"Count mismatch before RDS access for {name}: "
                f"manifest={expected}, file={len(rows)}."
            )

        validate_unique_keys(rows, table, key_column, name)

    for name, (
        table,
        key_column,
        old_columns,
        new_columns,
        filename,
    ) in UPDATE_SPECS.items():
        rows = read_csv(batch_root, filename)
        loaded[name] = rows

        expected = counts.get(name)
        if expected is None:
            raise ValueError(f"Manifest is missing count: {name}")

        if len(rows) != expected:
            raise ValueError(
                f"Count mismatch before RDS access for {name}: "
                f"manifest={expected}, file={len(rows)}."
            )

        validate_unique_keys(rows, table, key_column, name)

        for row in rows:
            if not row.get("updated_at"):
                raise ValueError(
                    f"{name}: missing updated_at for "
                    f"{key_column}={row.get(key_column)}"
                )

            for column in old_columns + new_columns:
                if f"old_{column}" not in row:
                    raise ValueError(
                        f"{name}: missing old_{column} column."
                    )
                if f"new_{column}" not in row:
                    raise ValueError(
                        f"{name}: missing new_{column} column."
                    )

    new_events_expected = counts.get("new_events")
    if new_events_expected is None:
        raise ValueError("Manifest is missing count: new_events")

    event_file_value = manifest.get("event_file")
    if not event_file_value:
        raise ValueError("Manifest is missing event_file.")

    event_file = Path(event_file_value)
    if not event_file.is_absolute():
        event_file = PROJECT_ROOT / event_file

    if not event_file.exists():
        raise FileNotFoundError(
            f"Customer-event JSONL not found: {event_file}"
        )

    # Validate every JSONL record before connecting to RDS. Events remain in
    # JSONL for Fabric ingestion; this script never inserts them into RDS.
    required_event_fields = {
        "event_id",
        "customer_id",
        "product_id",
        "event_type",
        "event_timestamp",
        "device_type",
        "session_id",
    }

    try:
        batch_start = datetime.fromisoformat(manifest["batch_start"])
        batch_end = datetime.fromisoformat(manifest["batch_end"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "Manifest must contain valid ISO-8601 batch_start and batch_end."
        ) from exc

    if batch_start > batch_end:
        raise ValueError("Manifest batch_start is after batch_end.")

    next_ids = manifest.get("next_ids")
    if not isinstance(next_ids, dict) or type(next_ids.get("event_id")) is not int:
        raise ValueError("Manifest is missing integer next_ids.event_id.")

    first_event_id = next_ids["event_id"]
    seen_event_ids = set()
    event_count = 0

    with event_file.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            if not line.strip():
                continue

            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON in customer-event file at line {line_number}: {exc}"
                ) from exc

            if not isinstance(event, dict):
                raise ValueError(
                    f"Customer-event line {line_number} must be a JSON object."
                )

            missing_fields = required_event_fields - set(event)
            if missing_fields:
                raise ValueError(
                    f"Customer-event line {line_number} is missing fields: "
                    f"{sorted(missing_fields)}."
                )

            event_id = event["event_id"]
            if type(event_id) is not int or event_id <= 0:
                raise ValueError(
                    f"Customer-event line {line_number}: event_id must be a positive integer."
                )
            if event_id in seen_event_ids:
                raise ValueError(
                    f"Customer-event line {line_number}: duplicate event_id {event_id}."
                )
            seen_event_ids.add(event_id)

            for field in ("customer_id", "product_id"):
                if type(event[field]) is not int or event[field] <= 0:
                    raise ValueError(
                        f"Customer-event line {line_number}: {field} must be a positive integer."
                    )

            for field in ("event_type", "device_type", "session_id"):
                if not isinstance(event[field], str) or not event[field].strip():
                    raise ValueError(
                        f"Customer-event line {line_number}: {field} must be a non-empty string."
                    )

            try:
                event_timestamp = datetime.fromisoformat(event["event_timestamp"])
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Customer-event line {line_number}: invalid event_timestamp "
                    f"{event['event_timestamp']!r}."
                ) from exc

            if event_timestamp.tzinfo != batch_start.tzinfo:
                raise ValueError(
                    f"Customer-event line {line_number}: event_timestamp timezone "
                    "does not match the manifest batch window."
                )

            if not batch_start <= event_timestamp <= batch_end:
                raise ValueError(
                    f"Customer-event line {line_number}: timestamp {event_timestamp} "
                    "is outside the manifest batch window."
                )

            event_count += 1

    if event_count != new_events_expected:
        raise ValueError(
            f"Customer-event count mismatch: "
            f"manifest={new_events_expected}, file={event_count}."
        )

    expected_event_ids = set(
        range(first_event_id, first_event_id + new_events_expected)
    )
    if seen_event_ids != expected_event_ids:
        missing_ids = sorted(expected_event_ids - seen_event_ids)
        unexpected_ids = sorted(seen_event_ids - expected_event_ids)
        raise ValueError(
            "Customer-event ID range mismatch. "
            f"Missing IDs (first 10): {missing_ids[:10]}; "
            f"unexpected IDs (first 10): {unexpected_ids[:10]}."
        )

    return loaded


def insert_rows(cursor, table, rows):
    if not rows:
        return 0

    columns = list(rows[0].keys())

    sql = (
        f"INSERT INTO dbo.{qident(table)} "
        f"({', '.join(qident(c) for c in columns)}) "
        f"VALUES ({', '.join('?' for _ in columns)})"
    )

    values = [
        tuple(row[column] for column in columns)
        for row in rows
    ]

    cursor.fast_executemany = True
    cursor.executemany(sql, values)

    return len(values)


def update_rows(
    cursor,
    table,
    rows,
    key_column,
    old_columns,
    new_columns,
):
    """
    Apply controlled source updates.

    The old business values are included in the WHERE clause so a stale
    generated batch cannot silently overwrite a newer source-system change.

    Every update also writes the generated batch's updated_at value, which
    is required for Fabric CDC/incremental extraction.
    """
    if not rows:
        return 0

    if len(old_columns) != len(new_columns):
        raise ValueError("Old/new column mapping lengths do not match.")

    affected = 0

    for row in rows:
        set_columns = list(new_columns) + ["updated_at"]

        set_clause = ", ".join(
            f"{qident(column)} = ?"
            for column in set_columns
        )

        where_clause = (
            f"{qident(key_column)} = ?"
            + "".join(
                f" AND {qident(column)} = ?"
                for column in old_columns
            )
        )

        sql = (
            f"UPDATE dbo.{qident(table)} "
            f"SET {set_clause} "
            f"WHERE {where_clause}"
        )

        values = [
            row[f"new_{column}"]
            for column in new_columns
        ]

        values.append(row["updated_at"])
        values.append(row[key_column])
        values.extend(
            row[f"old_{column}"]
            for column in old_columns
        )

        cursor.execute(sql, values)

        if cursor.rowcount != 1:
            raise RuntimeError(
                f"Update conflict for {table} "
                f"{key_column}={row[key_column]}. "
                "The source row may have changed since the batch "
                "was generated."
            )

        affected += cursor.rowcount

    return affected


def verify_new_keys_do_not_exist(cursor, table, key_column, rows):
    """
    Protect against accidental re-application.

    This is especially important if RDS committed successfully but the
    manifest could not be changed to APPLIED afterward.
    """
    if not rows:
        return

    keys = [row[key_column] for row in rows]
    placeholders = ", ".join("?" for _ in keys)

    sql = (
        f"SELECT COUNT(*) "
        f"FROM dbo.{qident(table)} "
        f"WHERE {qident(key_column)} IN ({placeholders})"
    )

    cursor.execute(sql, keys)
    found = cursor.fetchone()[0]

    if found:
        raise RuntimeError(
            f"Pre-apply safety check failed for {table}: "
            f"{found} generated key(s) already exist in RDS. "
            "The batch may already have been applied or the source "
            "contains conflicting keys. No changes were made."
        )


def verify_inserted_keys(cursor, table, key_column, rows):
    if not rows:
        return

    keys = [row[key_column] for row in rows]
    placeholders = ", ".join("?" for _ in keys)

    sql = (
        f"SELECT COUNT(*) "
        f"FROM dbo.{qident(table)} "
        f"WHERE {qident(key_column)} IN ({placeholders})"
    )

    cursor.execute(sql, keys)
    found = cursor.fetchone()[0]

    if found != len(keys):
        raise RuntimeError(
            f"Verification failed for {table}: "
            f"expected {len(keys)} keys, found {found}."
        )


def verify_updated_timestamps(cursor, table, rows, key_column):
    for row in rows:
        sql = (
            f"SELECT updated_at "
            f"FROM dbo.{qident(table)} "
            f"WHERE {qident(key_column)} = ?"
        )

        cursor.execute(sql, [row[key_column]])
        result = cursor.fetchone()

        if result is None:
            raise RuntimeError(
                f"Missing updated row: {table} "
                f"{key_column}={row[key_column]}"
            )

        actual = str(result[0])
        expected = row["updated_at"]

        if not actual.startswith(expected):
            raise RuntimeError(
                f"updated_at verification failed for {table} "
                f"{key_column}={row[key_column]}: "
                f"expected {expected}, got {actual}"
            )


def preflight_rds_checks(cursor, loaded):
    """
    Run all non-mutating database safety checks before the transaction.

    No INSERT/UPDATE is executed until these checks pass.
    """
    for name, (table, key_column, _) in INSERT_SPECS.items():
        verify_new_keys_do_not_exist(
            cursor,
            table,
            key_column,
            loaded[name],
        )

    for name, (
        table,
        key_column,
        old_columns,
        _new_columns,
        _filename,
    ) in UPDATE_SPECS.items():
        rows = loaded[name]

        for row in rows:
            where_clause = (
                f"{qident(key_column)} = ?"
                + "".join(
                    f" AND {qident(column)} = ?"
                    for column in old_columns
                )
            )

            sql = (
                f"SELECT COUNT(*) "
                f"FROM dbo.{qident(table)} "
                f"WHERE {where_clause}"
            )

            values = [row[key_column]]
            values.extend(
                row[f"old_{column}"]
                for column in old_columns
            )

            cursor.execute(sql, values)
            found = cursor.fetchone()[0]

            if found != 1:
                raise RuntimeError(
                    f"Pre-apply update check failed for {table} "
                    f"{key_column}={row[key_column]}. "
                    "The expected old values are not present. "
                    "The source may have changed since the batch "
                    "was generated. No changes were made."
                )


def verify_reference_ids_exist(cursor, table, key_column, ids):
    """Ensure all referenced IDs exist, checking in safe parameter chunks."""
    missing = set()
    ids = set(ids)
    if not ids:
        return

    for start in range(0, len(ids), 1000):
        chunk = sorted(ids)[start:start + 1000]
        placeholders = ", ".join("?" for _ in chunk)
        sql = (
            f"SELECT {qident(key_column)} "
            f"FROM dbo.{qident(table)} "
            f"WHERE {qident(key_column)} IN ({placeholders})"
        )
        cursor.execute(sql, chunk)
        found = {int(row[0]) for row in cursor.fetchall()}
        missing.update(set(chunk) - found)

    if missing:
        raise RuntimeError(
            f"Reference validation failed for dbo.{table}.{key_column}; "
            f"missing IDs (first 20): {sorted(missing)[:20]}."
        )


def preflight_batch_foreign_keys(cursor, loaded):
    """Validate insert-batch foreign keys against existing plus new rows."""
    def ids(name, column):
        return {int(row[column]) for row in loaded[name]}

    # These parent rows are not created by this incremental batch.
    location_ids = (
        ids("new_customers", "location_id")
        | ids("new_sellers", "location_id")
        | ids("new_orders", "shipping_location_id")
        | {int(row["new_location_id"]) for row in loaded["customer_updates"]}
        | {int(row["new_shipping_location_id"]) for row in loaded["order_updates"]}
    )
    verify_reference_ids_exist(cursor, "locations", "location_id", location_ids)
    verify_reference_ids_exist(
        cursor, "categories", "category_id", ids("new_products", "category_id")
    )

    # New parent IDs are valid for child rows in this same transaction; all
    # other IDs must already exist in RDS.
    new_customer_ids = ids("new_customers", "customer_id")
    verify_reference_ids_exist(
        cursor, "customers", "customer_id",
        ids("new_orders", "customer_id") - new_customer_ids,
    )

    new_order_ids = ids("new_orders", "order_id")
    verify_reference_ids_exist(
        cursor, "orders", "order_id",
        (ids("new_order_items", "order_id") | ids("new_payments", "order_id"))
        - new_order_ids,
    )

    new_product_ids = ids("new_products", "product_id")
    verify_reference_ids_exist(
        cursor, "products", "product_id",
        ids("new_order_items", "product_id") - new_product_ids,
    )

    new_seller_ids = ids("new_sellers", "seller_id")
    verify_reference_ids_exist(
        cursor, "sellers", "seller_id",
        ids("new_order_items", "seller_id") - new_seller_ids,
    )


def preflight_event_references(cursor, manifest, loaded):
    """Validate JSONL customer/product references before any RDS mutation."""
    event_file = Path(manifest["event_file"])
    if not event_file.is_absolute():
        event_file = PROJECT_ROOT / event_file

    event_customer_ids = set()
    event_product_ids = set()
    with event_file.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                event = json.loads(line)
                event_customer_ids.add(event["customer_id"])
                event_product_ids.add(event["product_id"])

    # New customers/products do not exist in RDS until the transaction inserts
    # them, so exclude those IDs from the existing-source lookup.
    new_customer_ids = {int(row["customer_id"]) for row in loaded["new_customers"]}
    new_product_ids = {int(row["product_id"]) for row in loaded["new_products"]}

    verify_reference_ids_exist(
        cursor, "customers", "customer_id", event_customer_ids - new_customer_ids
    )
    verify_reference_ids_exist(
        cursor, "products", "product_id", event_product_ids - new_product_ids
    )


def apply_batch(batch_id, batch_root, manifest_path, manifest):
    loaded = validate_manifest_and_files(
        batch_id,
        batch_root,
        manifest,
    )

    print("=" * 40)
    print(" PRE-APPLY VALIDATION PASSED")
    print("=" * 40)
    print(f"Batch: {batch_id}")
    print(f"Manifest status: {manifest['apply_status']}")
    print()

    connection = get_connection()
    cursor = None
    committed = False

    try:
        connection.autocommit = False
        cursor = connection.cursor()

        # These checks only read RDS. No source data is modified.
        preflight_rds_checks(cursor, loaded)
        preflight_batch_foreign_keys(cursor, loaded)
        preflight_event_references(cursor, manifest, loaded)

        print("RDS pre-apply safety checks passed.")
        print("Batch foreign-key references validated.")
        print("Customer-event customer/product references validated.")
        print("No conflicting insert keys found.")
        print("All expected update values are still present.")
        print()

        inserted_customers = insert_rows(
            cursor, "customers", loaded["new_customers"]
        )
        inserted_sellers = insert_rows(
            cursor, "sellers", loaded["new_sellers"]
        )
        inserted_products = insert_rows(
            cursor, "products", loaded["new_products"]
        )

        updated_customers = update_rows(
            cursor,
            "customers",
            loaded["customer_updates"],
            "customer_id",
            ["location_id", "customer_status"],
            ["location_id", "customer_status"],
        )

        updated_products = update_rows(
            cursor,
            "products",
            loaded["product_updates"],
            "product_id",
            ["unit_price", "product_status"],
            ["unit_price", "product_status"],
        )

        inserted_orders = insert_rows(
            cursor, "orders", loaded["new_orders"]
        )

        inserted_order_items = insert_rows(
            cursor, "order_items", loaded["new_order_items"]
        )

        inserted_payments = insert_rows(
            cursor, "payments", loaded["new_payments"]
        )

        updated_orders = update_rows(
            cursor,
            "orders",
            loaded["order_updates"],
            "order_id",
            ["order_status", "shipping_location_id"],
            ["order_status", "shipping_location_id"],
        )

        updated_payments = update_rows(
            cursor,
            "payments",
            loaded["payment_updates"],
            "payment_id",
            ["payment_status"],
            ["payment_status"],
        )

        expected_operations = {
            "new_customers": inserted_customers,
            "new_sellers": inserted_sellers,
            "new_products": inserted_products,
            "new_orders": inserted_orders,
            "new_order_items": inserted_order_items,
            "new_payments": inserted_payments,
            "customer_updates": updated_customers,
            "product_updates": updated_products,
            "order_updates": updated_orders,
            "payment_updates": updated_payments,
        }

        expected_counts = manifest["counts"]

        for name, actual in expected_operations.items():
            if actual != expected_counts[name]:
                raise RuntimeError(
                    f"Count mismatch for {name}: "
                    f"expected {expected_counts[name]}, got {actual}."
                )

        verify_inserted_keys(
            cursor,
            "customers",
            "customer_id",
            loaded["new_customers"],
        )
        verify_inserted_keys(
            cursor,
            "sellers",
            "seller_id",
            loaded["new_sellers"],
        )
        verify_inserted_keys(
            cursor,
            "products",
            "product_id",
            loaded["new_products"],
        )
        verify_inserted_keys(
            cursor,
            "orders",
            "order_id",
            loaded["new_orders"],
        )
        verify_inserted_keys(
            cursor,
            "order_items",
            "order_item_id",
            loaded["new_order_items"],
        )
        verify_inserted_keys(
            cursor,
            "payments",
            "payment_id",
            loaded["new_payments"],
        )

        # Critical CDC regression check:
        # every mutable-table update must carry its generated updated_at.
        verify_updated_timestamps(
            cursor,
            "customers",
            loaded["customer_updates"],
            "customer_id",
        )
        verify_updated_timestamps(
            cursor,
            "products",
            loaded["product_updates"],
            "product_id",
        )
        verify_updated_timestamps(
            cursor,
            "orders",
            loaded["order_updates"],
            "order_id",
        )
        verify_updated_timestamps(
            cursor,
            "payments",
            loaded["payment_updates"],
            "payment_id",
        )

        connection.commit()
        committed = True

        print("Transaction committed successfully.")
        print()
        print("Applied:")
        for name, actual in expected_operations.items():
            print(f"  {name}: {actual}")

    except Exception:
        if not committed:
            connection.rollback()
            print()
            print("ERROR: transaction rolled back.")
            print("No partial RDS changes were committed.")
        raise

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()

    # The database is now committed. If manifest persistence fails,
    # do NOT pretend the batch failed; the RDS transaction already exists.
    manifest["apply_status"] = "APPLIED"

    try:
        with manifest_path.open("w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
    except Exception as exc:
        print()
        print("=" * 40)
        print(" WARNING: RDS COMMIT SUCCEEDED")
        print("=" * 40)
        print(
            "The database transaction was committed, but the manifest "
            "could not be updated to APPLIED."
        )
        print(f"Manifest path: {manifest_path}")
        print(f"Manifest write error: {exc}")
        print(
            "DO NOT rerun this batch blindly. Reconcile the manifest "
            "after confirming the RDS changes."
        )
        raise

    print()
    print("=" * 40)
    print(" BATCH APPLIED SUCCESSFULLY")
    print("=" * 40)
    print(f"Batch: {batch_id}")
    print("Manifest status: APPLIED")
    print()
    print(
        "Customer events were NOT inserted into RDS. "
        "They remain in JSONL for Fabric file ingestion."
    )


def main():
    batch_id = get_batch_id()
    batch_root, manifest_path = get_batch_paths(batch_id)
    manifest = read_manifest(manifest_path)

    apply_batch(
        batch_id,
        batch_root,
        manifest_path,
        manifest,
    )


if __name__ == "__main__":
    main()
