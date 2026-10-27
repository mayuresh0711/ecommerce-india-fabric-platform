import random

from data_generator.config.order_config import (
    DISCOUNT_RATE_MIN,
    DISCOUNT_RATE_MAX,
    TAX_RATE_MIN,
    TAX_RATE_MAX,
    SHIPPING_AMOUNT_MIN,
    SHIPPING_AMOUNT_MAX,
)


def calculate_order_financials(order_items):
    if not order_items:
        raise ValueError("Order must contain at least one item.")

    subtotal_amount = round(
        sum(
            item["quantity"] * item["unit_price"]
            for item in order_items
        ),
        2
    )

    discount_amount = round(
        sum(
            item["discount_amount"]
            for item in order_items
        ),
        2
    )

    if discount_amount > subtotal_amount:
        raise ValueError(
            "Discount cannot exceed subtotal."
        )

    tax_rate  = random.uniform(
        TAX_RATE_MIN,
        TAX_RATE_MAX
    )

    tax_amount = round(
        (subtotal_amount - discount_amount) * tax_rate,
        2
    )

    shipping_amount = round(
        random.uniform(
            SHIPPING_AMOUNT_MIN,
            SHIPPING_AMOUNT_MAX
        ),
        2
    )

    total_amount = round(
        subtotal_amount
        - discount_amount
        + tax_amount
        + shipping_amount,
        2
    )

    return {
        "subtotal_amount": subtotal_amount,
        "discount_amount": discount_amount,
        "tax_amount": tax_amount,
        "shipping_amount": shipping_amount,
        "total_amount": total_amount,
    }


if __name__ == "__main__":
    sample_order_items = [
        {
            "quantity": 2,
            "unit_price": 1000.00,
            "discount_amount": 100.00,
        },
        {
            "quantity": 1,
            "unit_price": 500.00,
            "discount_amount": 50.00,
        },
    ]

    financials = calculate_order_financials(
        sample_order_items
    )

    print("Calculated order financials:")

    for key, value in financials.items():
        print(f"{key}: {value}")