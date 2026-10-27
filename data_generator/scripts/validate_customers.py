from data_generator.config.settings import CUSTOMER_COUNT
from data_generator.generators.customers import (
    generate_customers,
    load_location_ids,
)


def validate_customers(customers):

    if len(customers) != CUSTOMER_COUNT:
        raise ValueError(
            f"Expected {CUSTOMER_COUNT} customers, "
            f"got {len(customers)}"
        )

    # Customer ID uniqueness
    customer_ids = [
        customer["customer_id"]
        for customer in customers
    ]

    if len(customer_ids) != len(set(customer_ids)):
        raise ValueError(
            "Duplicate customer_id detected."
        )

    # Email uniqueness
    emails = [
        customer["email"]
        for customer in customers
    ]

    if len(emails) != len(set(emails)):
        raise ValueError(
            "Duplicate customer email detected."
        )

    # Location validity
    valid_location_ids = set(
        load_location_ids()
    )

    valid_statuses = {
        "Active",
        "Inactive",
        "Blocked",
    }

    for customer in customers:

        customer_id = customer["customer_id"]

        if customer["location_id"] not in valid_location_ids:
            raise ValueError(
                f"Invalid location_id "
                f"{customer['location_id']} "
                f"for customer {customer_id}"
            )

        if customer["customer_status"] not in valid_statuses:
            raise ValueError(
                f"Invalid customer status "
                f"for customer {customer_id}"
            )

        if customer["signup_date"] > customer["created_at"].date():
            raise ValueError(
                f"signup_date occurs after created_at "
                f"for customer {customer_id}"
            )

        if customer["updated_at"] < customer["created_at"]:
            raise ValueError(
                f"updated_at occurs before created_at "
                f"for customer {customer_id}"
            )

        if len(customer["phone"]) != 10:
            raise ValueError(
                f"Invalid phone length "
                f"for customer {customer_id}"
            )

        if not customer["phone"].isdigit():
            raise ValueError(
                f"Invalid phone format "
                f"for customer {customer_id}"
            )

    print("Customer validation passed.")
    print(f"Customers validated: {len(customers)}")


if __name__ == "__main__":
    customers = generate_customers()
    validate_customers(customers)