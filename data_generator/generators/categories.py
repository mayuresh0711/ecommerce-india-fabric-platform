from datetime import datetime

from data_generator.config.settings import DATA_START_DATE

# ============================================================
# Category master data
# ============================================================

CATEGORY_NAMES = [
    "Mobiles",
    "Laptops",
    "Tablets",
    "Televisions",
    "Audio",
    "Cameras",
    "Computer Accessories",
    "Home Appliances",
    "Kitchen Appliances",
    "Furniture",
    "Home Decor",
    "Grocery",
    "Beauty & Personal Care",
    "Fashion",
    "Footwear",
    "Sports & Fitness",
    "Books",
    "Toys & Games",
    "Automotive",
    "Pet Supplies",
]


# ============================================================
# Category generator
# ============================================================

def generate_categories():
    """
    Generate the category master data.

    Returns:
        list[dict]: Generated category records.
    """

    created_at = datetime.combine(
        DATA_START_DATE,
        datetime.min.time()
    )

    categories = []

    for category_id, category_name in enumerate(
        CATEGORY_NAMES,
        start=1
    ):
        categories.append(
            {
                "category_id": category_id,
                "category_name": category_name,
                "category_status": "Active",
                "created_at": created_at,
                "updated_at": created_at,
            }
        )

    return categories

# ============================================================
# Category validation
# ============================================================

def validate_categories(categories):
    """
    Validate generated category master data.

    Raises:
        ValueError: If any category violates the expected rules.
    """

    category_ids = [
        category["category_id"]
        for category in categories
    ]

    category_names = [
        category["category_name"]
        for category in categories
    ]

    # Expected category count
    if len(categories) != 20:
        raise ValueError(
            f"Expected 20 categories, got {len(categories)}"
        )

    # category_id must be unique
    if len(category_ids) != len(set(category_ids)):
        raise ValueError(
            "Duplicate category_id detected."
        )

    # category_name must be unique
    if len(category_names) != len(set(category_names)):
        raise ValueError(
            "Duplicate category_name detected."
        )

    # Validate status
    valid_statuses = {
        "Active",
        "Inactive",
    }

    invalid_statuses = {
        category["category_status"]
        for category in categories
        if category["category_status"] not in valid_statuses
    }

    if invalid_statuses:
        raise ValueError(
            f"Invalid category statuses: {invalid_statuses}"
        )

    # Validate dates
    for category in categories:
        if category["updated_at"] < category["created_at"]:
            raise ValueError(
                f"Invalid dates for category "
                f"{category['category_id']}"
            )


if __name__ == "__main__":
    categories = generate_categories()

    validate_categories(categories)

    print(f"Generated categories: {len(categories)}")

    for category in categories:
        print(category)