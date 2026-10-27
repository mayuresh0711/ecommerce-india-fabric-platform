import json
from pathlib import Path
from collections import defaultdict

from data_generator.generators.customer_events import generate_customer_events
from data_generator.generators.customers import generate_customers
from data_generator.generators.products import generate_products
from data_generator.config.settings import RANDOM_SEED

import random


OUTPUT_DIR = Path("data_generator/output/customer_events")


def group_events_by_month(events):
    events_by_month = defaultdict(list)

    for event in events:
        event_month = event["event_timestamp"].strftime("%Y-%m")
        events_by_month[event_month].append(event)

    return events_by_month


def serialize_event(event):
    return {
        "event_id": event["event_id"],
        "customer_id": event["customer_id"],
        "product_id": event["product_id"],
        "event_type": event["event_type"],
        "event_timestamp": event["event_timestamp"].isoformat(),
        "device_type": event["device_type"],
        "session_id": event["session_id"],
    }


def write_monthly_event_files(events):
    events_by_month = group_events_by_month(events)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    total_written = 0

    for month, month_events in sorted(events_by_month.items()):

        month_directory = OUTPUT_DIR / f"event_month={month}"
        month_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file = month_directory / "customer_events.jsonl"

        with output_file.open(
            "w",
            encoding="utf-8"
        ) as file:

            for event in month_events:
                file.write(
                    json.dumps(
                        serialize_event(event),
                        ensure_ascii=False
                    )
                )
                file.write("\n")

        total_written += len(month_events)

        print(
            f"{month}: "
            f"{len(month_events)} events written → "
            f"{output_file}"
        )

    return total_written


def main():

    print("========================================")
    print(" CUSTOMER EVENTS JSON GENERATION")
    print("========================================")

    random.seed(RANDOM_SEED)

    print("\nGenerating source data...")

    customers = generate_customers()
    products = generate_products()

    print(f"Customers: {len(customers)}")
    print(f"Products: {len(products)}")

    events = generate_customer_events(
        customers,
        products
    )

    print(f"Customer events generated: {len(events)}")

    print("\nWriting monthly JSON files...")

    total_written = write_monthly_event_files(events)

    print("\n========================================")
    print(" JSON GENERATION COMPLETED")
    print("========================================")

    print(f"\nTotal events written: {total_written}")


if __name__ == "__main__":
    main()