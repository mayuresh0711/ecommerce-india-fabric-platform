import random
from datetime import datetime, timedelta

import pandas as pd

from data_generator.config.customer_config import (
    CUSTOMER_FIRST_NAMES,
    CUSTOMER_LAST_NAMES,
    CUSTOMER_STATUS_DISTRIBUTION,
    EMAIL_DOMAINS,
)
from data_generator.config.settings import (
    CUSTOMER_COUNT,
    DATA_END_DATE,
    DATA_START_DATE,
)


LOCATION_FILE = (
    "data_generator/reference-data/india_locations.csv"
)


def load_location_ids():
    locations = pd.read_csv(
        LOCATION_FILE,
        dtype={
            "location_id": "int64",
            "Pincode": "string",
        },
    )

    if locations.empty:
        raise ValueError(
            "Location reference file is empty."
        )

    location_ids = locations["location_id"].tolist()

    if len(location_ids) != len(set(location_ids)):
        raise ValueError(
            "Duplicate location_id found."
        )

    return location_ids

def generate_customer_name():
    first_name = random.choice(
        CUSTOMER_FIRST_NAMES
    )

    last_name = random.choice(
        CUSTOMER_LAST_NAMES
    )

    return first_name, last_name


def generate_customer_email(
    first_name,
    last_name,
    customer_id,
):
    domain = random.choice(
        EMAIL_DOMAINS
    )

    return (
        f"{first_name.lower()}."
        f"{last_name.lower()}."
        f"{customer_id}@{domain}"
    )


def generate_customer_status():
    statuses = list(
        CUSTOMER_STATUS_DISTRIBUTION.keys()
    )

    probabilities = list(
        CUSTOMER_STATUS_DISTRIBUTION.values()
    )

    return random.choices(
        statuses,
        weights=probabilities,
        k=1,
    )[0]

def generate_customers():
    location_ids = load_location_ids()

    customers = []

    date_range = (
        DATA_END_DATE - DATA_START_DATE
    ).days

    for customer_id in range(1, CUSTOMER_COUNT + 1):

        first_name, last_name = generate_customer_name()

        customer_name = (
            f"{first_name} {last_name}"
        )

        email = generate_customer_email(
            first_name,
            last_name,
            customer_id,
        )

        phone = (
            f"9{random.randint(100000000, 999999999)}"
        )

        signup_date = (
            DATA_START_DATE
            + timedelta(
                days=random.randint(
                    0,
                    date_range
                )
            )
        )

        created_at = datetime.combine(
            signup_date,
            datetime.min.time()
        )

        customer_status = generate_customer_status()

        # Some customers have a later profile/status update.
        if random.random() < 0.20:

            remaining_days = (
                DATA_END_DATE - signup_date
            ).days

            if remaining_days > 0:
                updated_date = (
                    signup_date
                    + timedelta(
                        days=random.randint(
                            1,
                            remaining_days
                        )
                    )
                )
            else:
                updated_date = signup_date

        else:
            updated_date = signup_date

        updated_at = datetime.combine(
            updated_date,
            datetime.min.time()
        )

        location_id = random.choice(
            location_ids
        )

        customers.append(
            {
                "customer_id": customer_id,
                "customer_name": customer_name,
                "email": email,
                "phone": phone,
                "location_id": location_id,
                "customer_status": customer_status,
                "signup_date": signup_date,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

    return customers


if __name__ == "__main__":
    customers = generate_customers()

    print(
        f"Generated customers: {len(customers)}"
    )

    for customer in customers[:10]:
        print(customer)