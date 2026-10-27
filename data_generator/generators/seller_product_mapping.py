import random


MIN_PRODUCTS_PER_SELLER = 20
MAX_PRODUCTS_PER_SELLER = 100


def build_seller_product_mapping(products, sellers):

    product_ids = [
        product["product_id"]
        for product in products
    ]

    active_sellers = [
        seller
        for seller in sellers
        if seller["seller_status"] == "Active"
    ]

    seller_ids = [
        seller["seller_id"]
        for seller in active_sellers
    ]

    if not product_ids:
        raise ValueError(
            "No products available."
        )

    if not seller_ids:
        raise ValueError(
            "No active sellers available."
        )

    seller_product_mapping = {}

    for seller_id in seller_ids:

        product_count = random.randint(
            MIN_PRODUCTS_PER_SELLER,
            MAX_PRODUCTS_PER_SELLER
        )

        product_count = min(
            product_count,
            len(product_ids)
        )

        seller_product_mapping[seller_id] = (
            random.sample(
                product_ids,
                product_count
            )
        )

    return seller_product_mapping