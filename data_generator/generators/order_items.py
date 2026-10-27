import random

from data_generator.config.order_config import (
    ORDER_ITEM_COUNT_MIN,
    ORDER_ITEM_COUNT_MAX,
)


def build_product_lookup(products):
    product_lookup = {
        product["product_id"]: product
        for product in products
    }

    if len(product_lookup) != len(products):
        raise ValueError(
            "Duplicate product_id detected."
        )

    return product_lookup


def build_seller_lookup(sellers):
    seller_lookup = {
        seller["seller_id"]: seller
        for seller in sellers
    }

    if len(seller_lookup) != len(sellers):
        raise ValueError(
            "Duplicate seller_id detected."
        )

    return seller_lookup


def build_product_seller_lookup(seller_product_mapping):
    product_seller_lookup = {}

    for seller_id, product_ids in seller_product_mapping.items():

        for product_id in product_ids:

            product_seller_lookup.setdefault(
                product_id,
                []
            ).append(seller_id)

    if not product_seller_lookup:
        raise ValueError(
            "No product-seller relationships were generated."
        )

    return product_seller_lookup


def generate_order_items(
    orders,
    products,
    sellers,
    seller_product_mapping,
):
    product_lookup = build_product_lookup(
        products
    )

    seller_lookup = build_seller_lookup(
        sellers
    )

    product_seller_lookup = build_product_seller_lookup(
        seller_product_mapping
    )

    order_items = []
    order_item_id = 1

    for order in orders:

        available_product_ids = list(
            product_seller_lookup.keys()
        )

        item_count = random.randint(
            ORDER_ITEM_COUNT_MIN,
            min(
                ORDER_ITEM_COUNT_MAX,
                len(available_product_ids)
            )
        )

        selected_product_ids = random.sample(
            available_product_ids,
            item_count
        )

        for product_id in selected_product_ids:

            eligible_seller_ids = (
                product_seller_lookup[product_id]
            )

            seller_id = random.choice(
                eligible_seller_ids
            )

            product = product_lookup[product_id]
            seller = seller_lookup[seller_id]

            quantity = random.randint(1, 5)

            unit_price = product["unit_price"]

            gross_amount = quantity * unit_price

            discount_amount = round(
                gross_amount * random.uniform(0.00, 0.20),
                2
            )

            order_items.append(
                {
                    "order_item_id": order_item_id,
                    "order_id": order["order_id"],
                    "product_id": product_id,
                    "seller_id": seller["seller_id"],
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "discount_amount": discount_amount,
                    "created_at": order["created_at"],
                    "updated_at": order["updated_at"],
                }
            )

            order_item_id += 1

    return order_items