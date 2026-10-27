from data_generator.config.product_catalog import PRODUCT_CATALOG
from data_generator.config.product_models import PRODUCT_MODELS


def validate_product_models():
    validated_types = 0
    validated_brand_mappings = 0

    for product_type, brand_models in PRODUCT_MODELS.items():

        # Product type must exist somewhere in the catalog
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

        if not brand_models:
            raise ValueError(
                f"No model configuration for '{product_type}'."
            )

        for brand, models in brand_models.items():

            # Brand must be valid for this product type
            valid_brands = set()

            for category_name in catalog_matches:
                valid_brands.update(
                    PRODUCT_CATALOG[category_name][product_type]["brands"]
                )

            if brand not in valid_brands:
                raise ValueError(
                    f"Invalid brand '{brand}' for "
                    f"product type '{product_type}'."
                )

            if not models:
                raise ValueError(
                    f"No models defined for "
                    f"{brand} -> {product_type}."
                )

            if len(models) != len(set(models)):
                raise ValueError(
                    f"Duplicate models found for "
                    f"{brand} -> {product_type}."
                )

            for model in models:
                if not isinstance(model, str) or not model.strip():
                    raise ValueError(
                        f"Invalid model name for "
                        f"{brand} -> {product_type}."
                    )

            validated_brand_mappings += 1

        validated_types += 1

    print("Product model validation passed.")
    print(f"Product types validated: {validated_types}")
    print(f"Brand mappings validated: {validated_brand_mappings}")


if __name__ == "__main__":
    validate_product_models()