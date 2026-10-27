import random
from datetime import datetime

from data_generator.config.product_models import PRODUCT_MODELS
from data_generator.config.product_variants import PRODUCT_VARIANTS
from data_generator.config.product_catalog import PRODUCT_CATALOG
from data_generator.config.settings import (
    DATA_START_DATE,
    PRODUCT_COUNT,
)
from data_generator.generators.categories import generate_categories


def build_category_lookup():
    categories = generate_categories()

    return {
        category["category_name"]: category["category_id"]
        for category in categories
    }


def build_product_type_pool():
    product_type_pool = []

    for category_name, product_types in PRODUCT_CATALOG.items():

        for product_type in product_types:

            product_type_pool.append(
                {
                    "category_name": category_name,
                    "product_type": product_type,
                }
            )

    return product_type_pool


def generate_product_name(
    brand,
    product_type,
    product_number,
    used_names,
):
    product_type_models = PRODUCT_MODELS.get(
        product_type,
        {}
    )

    brand_models = product_type_models.get(
        brand,
        []
    )

    if brand_models:
        model = random.choice(brand_models)

        variants = PRODUCT_VARIANTS.get(
            product_type,
            []
        )

        if variants:
            variant = random.choice(variants)
            product_name = f"{brand} {model} {variant}"
        else:
            product_name = f"{brand} {model}"

    else:
        product_name = (
            f"{brand} {product_type} {product_number}"
        )

    # Safety mechanism to guarantee uniqueness
    if product_name in used_names:
        product_name = (
            f"{product_name} Variant {product_number}"
        )

    used_names.add(product_name)

    return product_name


def generate_unit_price(
    min_price,
    max_price,
):
    return round(
        random.uniform(min_price, max_price),
        2,
    )


def generate_products():
    category_lookup = build_category_lookup()
    product_type_pool = build_product_type_pool()

    products = []
    used_names = set()

    created_at = datetime.combine(
        DATA_START_DATE,
        datetime.min.time()
    )

    for product_id in range(1, PRODUCT_COUNT + 1):

        product_type_info = random.choice(product_type_pool)

        category_name = product_type_info["category_name"]
        product_type = product_type_info["product_type"]

        category_id = category_lookup[category_name]

        product_config = PRODUCT_CATALOG[category_name][product_type]

        brand = random.choice(
            product_config["brands"]
        )

        unit_price = generate_unit_price(
            product_config["min_price"],
            product_config["max_price"]
        )

        product_name = generate_product_name(
            brand,
            product_type,
            product_id,
            used_names,
        )

        products.append(
            {
                "product_id": product_id,
                "category_id": category_id,
                "product_name": product_name,
                "brand": brand,
                "product_type": product_type,
                "unit_price": unit_price,
                "product_status": "Active",
                "created_at": created_at,
                "updated_at": created_at,
            }
        )

    return products


if __name__ == "__main__":
    products = generate_products()

    print(f"Generated products: {len(products)}")

    for product in products[:10]:
        print(product)