import random
from datetime import datetime, timedelta

import pandas as pd

from data_generator.config.order_config import (
    ORDER_STATUS_DISTRIBUTION,
)
from data_generator.config.settings import (
    DATA_END_DATE,
    ORDER_COUNT,
)

LOCATION_FILE = "data_generator/reference-data/india_locations.csv"


def load_location_ids():
    locations = pd.read_csv(
        LOCATION_FILE,
        dtype={"Pincode": "string"}
    )

    if locations.empty:
        raise ValueError("Location master is empty.")

    location_ids = (
        locations["location_id"]
        .dropna()
        .astype(int)
        .tolist()
    )

    if not location_ids:
        raise ValueError(
            "No valid location IDs found."
        )

    if len(location_ids) != len(set(location_ids)):
        raise ValueError(
            "Duplicate location_id found."
        )

    return location_ids


def build_eligible_customers(customers):
    eligible_customers = [
        customer
        for customer in customers
        if customer["customer_status"] == "Active"
    ]

    if not eligible_customers:
        raise ValueError(
            "No active customers available "
            "for order generation."
        )

    return eligible_customers


def generate_order_date(customer):
    signup_date = customer["signup_date"]

    if signup_date > DATA_END_DATE:
        raise ValueError(
            f"Customer {customer['customer_id']} "
            f"has signup date after the data end date."
        )

    available_days = (
        DATA_END_DATE - signup_date
    ).days

    order_date = signup_date + timedelta(
        days=random.randint(
            0,
            available_days
        )
    )

    return datetime.combine(
        order_date,
        datetime.min.time()
    )


def generate_order_status():
    statuses = list(
        ORDER_STATUS_DISTRIBUTION.keys()
    )

    probabilities = list(
        ORDER_STATUS_DISTRIBUTION.values()
    )

    return random.choices(
        statuses,
        weights=probabilities,
        k=1
    )[0]


def apply_order_financials(order, financials):
    order.update(
        {
            "subtotal_amount": financials[
                "subtotal_amount"
            ],
            "discount_amount": financials[
                "discount_amount"
            ],
            "tax_amount": financials[
                "tax_amount"
            ],
            "shipping_amount": financials[
                "shipping_amount"
            ],
            "total_amount": financials[
                "total_amount"
            ],
        }
    )

    return order


def generate_orders(customers):
    eligible_customers = build_eligible_customers(
        customers
    )

    location_ids = load_location_ids()

    orders = []

    for order_id in range(
        1,
        ORDER_COUNT + 1
    ):
        customer = random.choice(
            eligible_customers
        )

        order_date = generate_order_date(
            customer
        )

        order_status = generate_order_status()

        shipping_location_id = random.choice(
            location_ids
        )

        created_at = order_date
        updated_at = order_date

        orders.append(
            {
                "order_id": order_id,
                "customer_id": customer[
                    "customer_id"
                ],
                "order_date": order_date,
                "order_status": order_status,
                "shipping_location_id": (
                    shipping_location_id
                ),
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

    return orders


if __name__ == "__main__":
    from data_generator.generators.customers import (
        generate_customers,
    )

    customers = generate_customers()

    orders = generate_orders(
        customers
    )

    print(
        f"Generated orders: {len(orders)}"
    )

    for order in orders[:10]:
        print(order)