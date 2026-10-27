from data_generator.config.product_catalog import PRODUCT_CATALOG
from data_generator.config.product_variants import PRODUCT_VARIANTS


def validate_product_variants():
    validated_types = 0
    validated_variants = 0

    for product_type, variants in PRODUCT_VARIANTS.items():

        # Confirm product type exists in the catalog
        catalog_matches = [
            category_name
            for category_name, product_types in PRODUCT_CATALOG.items()
            if product_type in product_types
        ]

        if not catalog_matches:
            raise ValueError(
                f"Product type '{product_type}' "
                f"does not exist in PRODUCT_CATALOG."
            )

        if not variants:
            raise ValueError(
                f"No variants defined for '{product_type}'."
            )

        if len(variants) != len(set(variants)):
            raise ValueError(
                f"Duplicate variants found for '{product_type}'."
            )

        for variant in variants:
            if not isinstance(variant, str) or not variant.strip():
                raise ValueError(
                    f"Invalid variant for '{product_type}'."
                )

            validated_variants += 1

        validated_types += 1

    print("Product variant validation passed.")
    print(f"Product types validated: {validated_types}")
    print(f"Variants validated: {validated_variants}")


if __name__ == "__main__":
    validate_product_variants()