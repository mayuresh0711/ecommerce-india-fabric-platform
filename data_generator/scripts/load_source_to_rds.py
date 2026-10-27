from data_generator.database.connection import get_connection
from data_generator.database.bulk_insert import bulk_insert
from data_generator.scripts.generate_initial_data import generate_source_snapshot


CLEAN_RELOAD = True


LOAD_ORDER = [
    "locations",
    "categories",
    "customers",
    "sellers",
    "products",
    "orders",
    "order_items",
    "payments",
]


DELETE_ORDER = [
    "payments",
    "order_items",
    "orders",
    "products",
    "sellers",
    "customers",
    "categories",
    "locations",
]


def clear_target_tables(connection):
    cursor = connection.cursor()

    try:
        print("\nCleaning existing target data...")

        for table_name in DELETE_ORDER:
            cursor.execute(f"DELETE FROM dbo.[{table_name}]")
            print(f"  Cleared {table_name}")

    finally:
        cursor.close()


def prepare_location_rows(locations):
    return [
        {
            "location_id": row["location_id"],
            "pincode": row["Pincode"],
            "city": row["City"],
            "district": row["District"],
            "state": row["State"],
            "region": row["Region"],
            "country": "India",
        }
        for row in locations
    ]


def verify_row_counts(connection, expected_counts):
    cursor = connection.cursor()

    try:
        print("\nVerifying database row counts...")

        for table_name, expected_count in expected_counts.items():
            cursor.execute(
                f"SELECT COUNT(*) FROM dbo.[{table_name}]"
            )

            actual_count = cursor.fetchone()[0]

            print(
                f"  {table_name}: "
                f"expected={expected_count}, actual={actual_count}"
            )

            if actual_count != expected_count:
                raise ValueError(
                    f"Row-count mismatch for {table_name}: "
                    f"expected {expected_count}, got {actual_count}"
                )

    finally:
        cursor.close()


def load_source_snapshot(snapshot, connection):
    locations = prepare_location_rows(snapshot["locations"])

    table_config = {
        "locations": {
            "columns": [
                "location_id",
                "pincode",
                "city",
                "district",
                "state",
                "region",
                "country",
            ],
            "rows": locations,
        },

        "categories": {
            "columns": [
                "category_id",
                "category_name",
                "category_status",
                "created_at",
                "updated_at",
            ],
            "rows": snapshot["categories"],
        },

        "customers": {
            "columns": [
                "customer_id",
                "customer_name",
                "email",
                "phone",
                "location_id",
                "customer_status",
                "signup_date",
                "created_at",
                "updated_at",
            ],
            "rows": snapshot["customers"],
        },

        "sellers": {
            "columns": [
                "seller_id",
                "seller_name",
                "location_id",
                "seller_status",
                "created_at",
                "updated_at",
            ],
            "rows": snapshot["sellers"],
        },

        "products": {
            "columns": [
                "product_id",
                "category_id",
                "product_name",
                "brand",
                "product_type",
                "unit_price",
                "product_status",
                "created_at",
                "updated_at",
            ],
            "rows": snapshot["products"],
        },

        "orders": {
            "columns": [
                "order_id",
                "customer_id",
                "order_date",
                "order_status",
                "shipping_location_id",
                "subtotal_amount",
                "discount_amount",
                "tax_amount",
                "shipping_amount",
                "total_amount",
                "created_at",
                "updated_at",
            ],
            "rows": snapshot["orders"],
        },

        "order_items": {
            "columns": [
                "order_item_id",
                "order_id",
                "product_id",
                "seller_id",
                "quantity",
                "unit_price",
                "discount_amount",
                "created_at",
                "updated_at",
            ],
            "rows": snapshot["order_items"],
        },

        "payments": {
            "columns": [
                "payment_id",
                "order_id",
                "payment_timestamp",
                "payment_method",
                "payment_amount",
                "payment_status",
                "transaction_reference",
                "created_at",
                "updated_at",
            ],
            "rows": snapshot["payments"],
        },
    }

    expected_counts = {}

    for table_name in LOAD_ORDER:
        config = table_config[table_name]

        print(f"\nLoading {table_name}...")

        inserted_count = bulk_insert(
            connection=connection,
            table_name=table_name,
            columns=config["columns"],
            rows=config["rows"],
        )

        expected_counts[table_name] = inserted_count

        print(
            f"{table_name}: "
            f"{inserted_count} rows loaded successfully."
        )

    verify_row_counts(
        connection=connection,
        expected_counts=expected_counts,
    )


def main():
    print("========================================")
    print(" E-COMMERCE SOURCE INITIAL LOAD")
    print("========================================")

    print("\nGenerating and validating source snapshot...")
    snapshot = generate_source_snapshot()

    print("\nSource snapshot ready.")

    connection = get_connection()
    connection.autocommit = False

    try:
        if CLEAN_RELOAD:
            clear_target_tables(connection)

        print("\nStarting database transaction...")

        load_source_snapshot(
            snapshot=snapshot,
            connection=connection,
        )

        print("\nAll tables loaded and verified.")
        print("Committing transaction...")

        connection.commit()

        print("\n========================================")
        print(" INITIAL LOAD COMPLETED SUCCESSFULLY")
        print("========================================")

    except Exception as error:
        print("\n========================================")
        print(" INITIAL LOAD FAILED")
        print("========================================")

        print(f"\nError: {error}")
        print("\nRolling back transaction...")

        connection.rollback()

        print("Transaction rolled back successfully.")

        raise

    finally:
        connection.close()
        print("\nDatabase connection closed.")


if __name__ == "__main__":
    main()