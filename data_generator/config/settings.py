# Development dataset configuration
from datetime import date

# Reproducibility
RANDOM_SEED = 42

# Initial dataset volumes
LOCATION_COUNT = 500
CUSTOMER_COUNT = 10_000
SELLER_COUNT = 500
CATEGORY_COUNT = 20
PRODUCT_COUNT = 2_000
ORDER_COUNT = 50_000

# Transaction expectations
AVG_ITEMS_PER_ORDER = 3
PAYMENTS_PER_ORDER = 1

# Customer events
CUSTOMER_EVENT_COUNT = 250_000

# Historical period
DATA_START_DATE = date(2025, 1, 1)
DATA_END_DATE = date(2025, 12, 31)

# Source database
DATABASE_NAME = "ecommerce_source"