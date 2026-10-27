from data_generator.config.product_catalog import PRODUCT_CATALOG
from data_generator.generators.categories import CATEGORY_NAMES


def validate_product_catalog():
    # 1. Check all categories exist
    missing_categories = set(CATEGORY_NAMES) - set(PRODUCT_CATALOG.keys())

    if missing_categories:
        raise ValueError(
            f"Missing categories in product catalog: {missing_categories}"
        )

    # 2. Check for unexpected categories
    unexpected_categories = set(PRODUCT_CATALOG.keys()) - set(CATEGORY_NAMES)

    if unexpected_categories:
        raise ValueError(
            f"Unexpected categories in product catalog: {unexpected_categories}"
        )

    # 3. Validate every category
    for category_name in CATEGORY_NAMES:

        product_types = PRODUCT_CATALOG[category_name]

        if not product_types:
            raise ValueError(
                f"Category '{category_name}' has no product types."
            )

        for product_type, config in product_types.items():

            # Brands
            brands = config.get("brands")

            if not brands:
                raise ValueError(
                    f"No brands defined for "
                    f"{category_name} -> {product_type}"
                )

            if len(brands) != len(set(brands)):
                raise ValueError(
                    f"Duplicate brands found for "
                    f"{category_name} -> {product_type}"
                )

            # Prices
            min_price = config.get("min_price")
            max_price = config.get("max_price")

            if min_price is None or max_price is None:
                raise ValueError(
                    f"Missing price range for "
                    f"{category_name} -> {product_type}"
                )

            if min_price < 0:
                raise ValueError(
                    f"Negative min_price for "
                    f"{category_name} -> {product_type}"
                )

            if max_price < 0:
                raise ValueError(
                    f"Negative max_price for "
                    f"{category_name} -> {product_type}"
                )

            if min_price > max_price:
                raise ValueError(
                    f"Invalid price range for "
                    f"{category_name} -> {product_type}"
                )

    print("Product catalog validation passed.")
    print(f"Categories validated: {len(PRODUCT_CATALOG)}")

    product_type_count = sum(
        len(product_types)
        for product_types in PRODUCT_CATALOG.values()
    )

    print(f"Product types configured: {product_type_count}")


if __name__ == "__main__":
    validate_product_catalog()