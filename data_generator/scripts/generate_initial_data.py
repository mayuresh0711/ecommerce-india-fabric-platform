import random
import pandas as pd

from data_generator.config.settings import RANDOM_SEED

from data_generator.generators.categories import (
    generate_categories,
)

from data_generator.generators.products import (
    generate_products,
)

from data_generator.generators.sellers import (
    generate_sellers,
)

from data_generator.generators.customers import (
    generate_customers,
)

from data_generator.generators.orders import (
    generate_orders,
    apply_order_financials,
)

from data_generator.generators.order_items import (
    generate_order_items,
)

from data_generator.generators.seller_product_mapping import (
    build_seller_product_mapping,
)

from data_generator.generators.order_financials import (
    calculate_order_financials,
)

from data_generator.generators.payments import (
    generate_payments,
)

from data_generator.generators.customer_events import (
    generate_customer_events,
)

from data_generator.validation.validate_initial_data import (
    validate_initial_data,
)


LOCATION_FILE = "data_generator/reference-data/india_locations.csv"


def group_items_by_order(order_items):
    items_by_order = {}

    for item in order_items:
        items_by_order.setdefault(
            item["order_id"],
            []
        ).append(item)

    return items_by_order


def generate_source_snapshot():
    """
    Generate one complete, internally consistent source snapshot.

    The returned snapshot is the single source of truth that can
    be passed to RDS persistence and file persistence.
    """

    random.seed(RANDOM_SEED)

    print("Starting source snapshot generation...")

    # ---------------------------------------------------------
    # Master data
    # ---------------------------------------------------------

    categories = generate_categories()

    print(
        f"Categories: {len(categories)}"
    )

    products = generate_products()

    print(
        f"Products: {len(products)}"
    )

    sellers = generate_sellers()

    print(
        f"Sellers: {len(sellers)}"
    )

    customers = generate_customers()

    print(
        f"Customers: {len(customers)}"
    )

    # ---------------------------------------------------------
    # Locations
    # ---------------------------------------------------------

    locations = pd.read_csv(
        LOCATION_FILE,
        dtype={"Pincode": "string"}
    ).to_dict("records")

    print(
        f"Locations: {len(locations)}"
    )

    # ---------------------------------------------------------
    # Seller-product relationships
    # ---------------------------------------------------------

    seller_product_mapping = build_seller_product_mapping(
        products,
        sellers,
    )

    print(
        f"Seller-product mappings: "
        f"{len(seller_product_mapping)} sellers"
    )

    # ---------------------------------------------------------
    # Orders
    # ---------------------------------------------------------

    orders = generate_orders(
        customers
    )

    print(
        f"Orders: {len(orders)}"
    )

    # ---------------------------------------------------------
    # Order items
    # ---------------------------------------------------------

    order_items = generate_order_items(
        orders,
        products,
        sellers,
        seller_product_mapping,
    )

    print(
        f"Order items: {len(order_items)}"
    )

    # ---------------------------------------------------------
    # Order financials
    # ---------------------------------------------------------

    items_by_order = group_items_by_order(
        order_items
    )

    for order in orders:

        financials = calculate_order_financials(
            items_by_order[order["order_id"]]
        )

        apply_order_financials(
            order,
            financials,
        )

    print(
        "Order financials calculated."
    )

    # ---------------------------------------------------------
    # Payments
    # ---------------------------------------------------------

    payments = generate_payments(
        orders
    )

    print(
        f"Payments: {len(payments)}"
    )

    # ---------------------------------------------------------
    # Customer events
    # ---------------------------------------------------------

    customer_events = generate_customer_events(
        customers,
        products,
    )

    print(
        f"Customer events: {len(customer_events)}"
    )

    # ---------------------------------------------------------
    # Final source-data validation
    # ---------------------------------------------------------

    validate_initial_data(
        customers=customers,
        products=products,
        sellers=sellers,
        orders=orders,
        order_items=order_items,
        payments=payments,
        customer_events=customer_events,
        locations=locations,
    )

    print(
        "Source snapshot validation passed."
    )

    # ---------------------------------------------------------
    # Return one consistent snapshot
    # ---------------------------------------------------------

    return {
        "locations": locations,
        "categories": categories,
        "customers": customers,
        "sellers": sellers,
        "products": products,
        "orders": orders,
        "order_items": order_items,
        "payments": payments,
        "customer_events": customer_events,
    }


def main():
    generate_source_snapshot()

    print(
        "Initial source snapshot generation completed."
    )


if __name__ == "__main__":
    main()