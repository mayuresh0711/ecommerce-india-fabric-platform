from data_generator.config.settings import SELLER_COUNT
from data_generator.generators.sellers import (
    generate_sellers,
    load_location_ids,
)


def validate_sellers(sellers):

    if len(sellers) != SELLER_COUNT:
        raise ValueError(
            f"Expected {SELLER_COUNT} sellers, "
            f"got {len(sellers)}"
        )

    # Seller ID uniqueness
    seller_ids = [
        seller["seller_id"]
        for seller in sellers
    ]

    if len(seller_ids) != len(set(seller_ids)):
        raise ValueError(
            "Duplicate seller_id detected."
        )

    # Seller name uniqueness
    seller_names = [
        seller["seller_name"]
        for seller in sellers
    ]

    if len(seller_names) != len(set(seller_names)):
        raise ValueError(
            "Duplicate seller_name detected."
        )

    # Valid locations
    valid_location_ids = set(
        load_location_ids()
    )

    # Valid statuses
    valid_statuses = {
        "Active",
        "Inactive",
        "Suspended",
    }

    for seller in sellers:

        if seller["location_id"] not in valid_location_ids:
            raise ValueError(
                f"Invalid location_id "
                f"{seller['location_id']} "
                f"for seller {seller['seller_id']}"
            )

        if seller["seller_status"] not in valid_statuses:
            raise ValueError(
                f"Invalid seller status "
                f"{seller['seller_status']}"
            )

        if seller["updated_at"] < seller["created_at"]:
            raise ValueError(
                f"Invalid timestamps for seller "
                f"{seller['seller_id']}"
            )

    print("Seller validation passed.")
    print(f"Sellers validated: {len(sellers)}")


if __name__ == "__main__":
    sellers = generate_sellers()
    validate_sellers(sellers)