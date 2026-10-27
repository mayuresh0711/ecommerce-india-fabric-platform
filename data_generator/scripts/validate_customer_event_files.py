import json
from pathlib import Path


EVENT_ROOT = Path("data_generator/output/customer_events")

EXPECTED_EVENT_COUNT = 250_000

EXPECTED_FIELDS = {
    "event_id",
    "customer_id",
    "product_id",
    "event_type",
    "event_timestamp",
    "device_type",
    "session_id",
}


def validate_event_file(file_path):
    record_count = 0

    with file_path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):

            if not line.strip():
                continue

            try:
                event = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON in {file_path} "
                    f"at line {line_number}: {error}"
                )

            missing_fields = EXPECTED_FIELDS - event.keys()

            if missing_fields:
                raise ValueError(
                    f"Missing fields in {file_path} "
                    f"at line {line_number}: "
                    f"{sorted(missing_fields)}"
                )

            record_count += 1

    return record_count


def main():

    print("========================================")
    print(" CUSTOMER EVENT FILE VALIDATION")
    print("========================================")

    if not EVENT_ROOT.exists():
        raise FileNotFoundError(
            f"Event directory does not exist: {EVENT_ROOT}"
        )

    event_files = sorted(
        EVENT_ROOT.glob(
            "event_month=*/customer_events.jsonl"
        )
    )

    print(f"\nMonthly event files found: {len(event_files)}")

    if len(event_files) != 12:
        raise ValueError(
            f"Expected 12 monthly files, "
            f"found {len(event_files)}"
        )

    total_records = 0

    for file_path in event_files:

        count = validate_event_file(file_path)

        total_records += count

        print(
            f"{file_path.parent.name}: "
            f"{count} valid records"
        )

    print(f"\nTotal records: {total_records}")

    if total_records != EXPECTED_EVENT_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_EVENT_COUNT} records, "
            f"found {total_records}"
        )

    print("\n========================================")
    print(" CUSTOMER EVENT FILE VALIDATION PASSED")
    print("========================================")


if __name__ == "__main__":
    main()