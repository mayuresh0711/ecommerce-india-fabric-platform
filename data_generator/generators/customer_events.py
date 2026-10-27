import random
import string
from datetime import datetime, timedelta

from data_generator.config.customer_event_config import (
    EVENT_TYPE_DISTRIBUTION,
    DEVICE_TYPE_DISTRIBUTION,
    SESSION_ID_LENGTH,
)
from data_generator.config.settings import (
    CUSTOMER_EVENT_COUNT,
    DATA_START_DATE,
    DATA_END_DATE,
)


def generate_event_type():
    event_types = list(EVENT_TYPE_DISTRIBUTION.keys())
    probabilities = list(EVENT_TYPE_DISTRIBUTION.values())

    return random.choices(
        event_types,
        weights=probabilities,
        k=1,
    )[0]


def generate_device_type():
    device_types = list(DEVICE_TYPE_DISTRIBUTION.keys())
    probabilities = list(DEVICE_TYPE_DISTRIBUTION.values())

    return random.choices(
        device_types,
        weights=probabilities,
        k=1,
    )[0]


def generate_session_id():
    characters = string.ascii_letters + string.digits

    return "".join(
        random.choices(
            characters,
            k=SESSION_ID_LENGTH,
        )
    )


def generate_event_timestamp():
    start_datetime = datetime.combine(
        DATA_START_DATE,
        datetime.min.time(),
    )

    end_datetime = datetime.combine(
        DATA_END_DATE,
        datetime.max.time(),
    )

    total_seconds = int(
        (end_datetime - start_datetime).total_seconds()
    )

    random_seconds = random.randint(
        0,
        total_seconds,
    )

    return start_datetime + timedelta(
        seconds=random_seconds
    )


def generate_customer_events(customers, products):

    customer_ids = [
        customer["customer_id"]
        for customer in customers
    ]

    product_ids = [
        product["product_id"]
        for product in products
    ]

    events = []

    for event_id in range(
        1,
        CUSTOMER_EVENT_COUNT + 1,
    ):
        event_type = generate_event_type()

        event = {
            "event_id": event_id,
            "customer_id": random.choice(customer_ids),
            "product_id": random.choice(product_ids),
            "event_type": event_type,
            "event_timestamp": generate_event_timestamp(),
            "device_type": generate_device_type(),
            "session_id": generate_session_id(),
        }

        events.append(event)

    return events


if __name__ == "__main__":
    from data_generator.generators.customers import (
        generate_customers,
    )
    from data_generator.generators.products import (
        generate_products,
    )

    customers = generate_customers()
    products = generate_products()

    events = generate_customer_events(
        customers,
        products,
    )

    print(f"Generated customer events: {len(events)}")

    for event in events[:10]:
        print(event)