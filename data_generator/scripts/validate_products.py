from data_generator.config.product_catalog import PRODUCT_CATALOG
from data_generator.config.settings import PRODUCT_COUNT
from data_generator.generators.products import generate_products


def validate_products(products):
    if len(products) != PRODUCT_COUNT:
        raise ValueError(
            f"Expected {PRODUCT_COUNT} products, "
            f"got {len(products)}"
        )

    # Product IDs
    product_ids = [
        product["product_id"]
        for product in products
    ]

    if len(product_ids) != len(set(product_ids)):
        raise ValueError(
            "Duplicate product_id detected."
        )

    # Product names
    product_names = [
        product["product_name"]
        for product in products
    ]

    if len(product_names) != len(set(product_names)):
        raise ValueError(
            "Duplicate product_name detected."
        )

    # Validate every product against catalog configuration
    for product in products:

        category_id = product["category_id"]
        product_type = product["product_type"]
        brand = product["brand"]
        unit_price = product["unit_price"]

        matching_categories = [
            category_name
            for category_name, product_types in PRODUCT_CATALOG.items()
            if product_type in product_types
        ]

        if not matching_categories:
            raise ValueError(
                f"Unknown product_type: {product_type}"
            )

        valid_configuration = False

        for category_name in matching_categories:

            config = PRODUCT_CATALOG[
                category_name
            ].get(product_type)

            if config and brand in config["brands"]:
                if (
                    config["min_price"]
                    <= unit_price
                    <= config["max_price"]
                ):
                    valid_configuration = True
                    break

        if not valid_configuration:
            raise ValueError(
                f"Invalid product configuration: "
                f"{product}"
            )

        if unit_price < 0:
            raise ValueError(
                f"Negative price for product "
                f"{product['product_id']}"
            )

        if product["product_status"] not in {
            "Active",
            "Inactive",
            "Discontinued",
        }:
            raise ValueError(
                f"Invalid product status for "
                f"{product['product_id']}"
            )

        if product["updated_at"] < product["created_at"]:
            raise ValueError(
                f"Invalid timestamps for "
                f"{product['product_id']}"
            )

    print("Product validation passed.")
    print(f"Products validated: {len(products)}")


if __name__ == "__main__":
    products = generate_products()
    validate_products(products)