import random
from datetime import datetime, timedelta

import pandas as pd

from data_generator.config.settings import (
    DATA_END_DATE,
    DATA_START_DATE,
    SELLER_COUNT,
)
from data_generator.config.seller_config import (
    SELLER_NAME_MIDDLES,
    SELLER_NAME_PREFIXES,
    SELLER_NAME_SUFFIXES,
    SELLER_STATUS_DISTRIBUTION,
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
            "Duplicate location_id found in location reference."
        )

    return location_ids

def generate_seller_name(used_names):
    while True:
        prefix = random.choice(
            SELLER_NAME_PREFIXES
        )

        middle = random.choice(
            SELLER_NAME_MIDDLES
        )

        suffix = random.choice(
            SELLER_NAME_SUFFIXES
        )

        seller_name = (
            f"{prefix} {middle} {suffix}"
        )

        if seller_name not in used_names:
            used_names.add(seller_name)
            return seller_name


def generate_seller_status():
    statuses = list(
        SELLER_STATUS_DISTRIBUTION.keys()
    )

    probabilities = list(
        SELLER_STATUS_DISTRIBUTION.values()
    )

    return random.choices(
        statuses,
        weights=probabilities,
        k=1,
    )[0]

def generate_sellers():
    location_ids = load_location_ids()

    sellers = []
    used_names = set()

    for seller_id in range(1, SELLER_COUNT + 1):

        seller_name = generate_seller_name(
            used_names
        )

        location_id = random.choice(
            location_ids
        )

        seller_status = generate_seller_status()

        # Generate a seller creation date
        date_range = (
            DATA_END_DATE - DATA_START_DATE
        ).days

        created_date = (
            DATA_START_DATE
            + timedelta(
                days=random.randint(
                    0,
                    date_range
                )
            )
        )

        created_at = datetime.combine(
            created_date,
            datetime.min.time()
        )

        # Most sellers are unchanged initially.
        # Some receive a later update.
        if random.random() < 0.20:
            remaining_days = (
                DATA_END_DATE - created_date
            ).days

            if remaining_days > 0:
                updated_date = (
                    created_date
                    + timedelta(
                        days=random.randint(
                            1,
                            remaining_days
                        )
                    )
                )
            else:
                updated_date = created_date

            updated_at = datetime.combine(
                updated_date,
                datetime.min.time()
            )

        else:
            updated_at = created_at

        sellers.append(
            {
                "seller_id": seller_id,
                "seller_name": seller_name,
                "location_id": location_id,
                "seller_status": seller_status,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

    return sellers

if __name__ == "__main__":
    sellers = generate_sellers()

    print(f"Generated sellers: {len(sellers)}")

    for seller in sellers[:10]:
        print(seller)