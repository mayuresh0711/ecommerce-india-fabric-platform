from datetime import datetime

from data_generator.config.customer_event_config import (
    EVENT_TYPES,
    DEVICE_TYPES,
)
from data_generator.config.settings import (
    DATA_START_DATE,
    DATA_END_DATE,
)


def validate_event_structure(events):
    if not events:
        raise ValueError("No customer events were generated.")

    event_ids = [
        event["event_id"]
        for event in events
    ]

    if len(event_ids) != len(set(event_ids)):
        raise ValueError(
            "Duplicate event_id detected."
        )

    required_fields = {
        "event_id",
        "customer_id",
        "product_id",
        "event_type",
        "event_timestamp",
        "device_type",
        "session_id",
    }

    for event in events:
        missing_fields = required_fields - event.keys()

        if missing_fields:
            raise ValueError(
                f"Event {event['event_id']} "
                f"is missing fields: {missing_fields}"
            )


def validate_event_values(events):

    valid_event_types = set(EVENT_TYPES)
    valid_device_types = set(DEVICE_TYPES)

    start_datetime = datetime.combine(
        DATA_START_DATE,
        datetime.min.time(),
    )

    end_datetime = datetime.combine(
        DATA_END_DATE,
        datetime.max.time(),
    )

    for event in events:

        if event["event_id"] <= 0:
            raise ValueError(
                f"Invalid event_id: {event['event_id']}"
            )

        if event["customer_id"] <= 0:
            raise ValueError(
                f"Invalid customer_id for event "
                f"{event['event_id']}"
            )

        if event["product_id"] <= 0:
            raise ValueError(
                f"Invalid product_id for event "
                f"{event['event_id']}"
            )

        if event["event_type"] not in valid_event_types:
            raise ValueError(
                f"Invalid event type for event "
                f"{event['event_id']}: "
                f"{event['event_type']}"
            )

        if event["device_type"] not in valid_device_types:
            raise ValueError(
                f"Invalid device type for event "
                f"{event['event_id']}: "
                f"{event['device_type']}"
            )

        if not isinstance(
            event["event_timestamp"],
            datetime,
        ):
            raise ValueError(
                f"Event {event['event_id']} "
                f"does not have a datetime timestamp."
            )

        if not (
            start_datetime
            <= event["event_timestamp"]
            <= end_datetime
        ):
            raise ValueError(
                f"Event {event['event_id']} "
                f"has timestamp outside the "
                f"configured data period."
            )

        if not event["session_id"]:
            raise ValueError(
                f"Event {event['event_id']} "
                f"has an empty session_id."
            )


def validate_event_references(
    events,
    customers,
    products,
):
    customer_ids = {
        customer["customer_id"]
        for customer in customers
    }

    product_ids = {
        product["product_id"]
        for product in products
    }

    for event in events:

        if event["customer_id"] not in customer_ids:
            raise ValueError(
                f"Event {event['event_id']} references "
                f"unknown customer "
                f"{event['customer_id']}."
            )

        if event["product_id"] not in product_ids:
            raise ValueError(
                f"Event {event['event_id']} references "
                f"unknown product "
                f"{event['product_id']}."
            )


if __name__ == "__main__":

    from data_generator.generators.customer_events import (
        generate_customer_events,
    )
    from data_generator.generators.customers import (
        generate_customers,
    )
    from data_generator.generators.products import (
        generate_products,
    )

    customers = generate_customers()
    products = generate_products()
    events = generate_customer_events()

    validate_event_structure(events)

    validate_event_values(events)

    validate_event_references(
        events,
        customers,
        products,
    )

    print("Customer event structure validation passed.")
    print("Customer event value validation passed.")
    print("Customer event reference validation passed.")