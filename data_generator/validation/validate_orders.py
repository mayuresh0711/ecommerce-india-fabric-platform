import pandas as pd

from data_generator.generators.customers import generate_customers
from data_generator.generators.products import generate_products
from data_generator.generators.sellers import generate_sellers


LOCATION_FILE = "data_generator/reference-data/india_locations.csv"


def validate_order_structure(orders):
    if not orders:
        raise ValueError("No orders were generated.")

    order_ids = [
        order["order_id"]
        for order in orders
    ]

    if len(order_ids) != len(set(order_ids)):
        raise ValueError(
            "Duplicate order_id detected."
        )

    if any(order["order_id"] <= 0 for order in orders):
        raise ValueError(
            "Invalid order_id detected."
        )

    required_fields = {
        "order_id",
        "customer_id",
        "order_date",
        "order_status",
        "shipping_location_id",
        "subtotal_amount",
        "discount_amount",
        "tax_amount",
        "shipping_amount",
        "total_amount",
        "created_at",
        "updated_at",
    }

    for order in orders:
        missing_fields = required_fields - order.keys()

        if missing_fields:
            raise ValueError(
                f"Order {order['order_id']} is missing fields: "
                f"{missing_fields}"
            )


def validate_order_dates(orders):
    for order in orders:

        if order["order_date"] < order["created_at"]:
            raise ValueError(
                f"Order {order['order_id']} has order_date "
                f"before created_at."
            )

        if order["updated_at"] < order["created_at"]:
            raise ValueError(
                f"Order {order['order_id']} has updated_at "
                f"before created_at."
            )


def validate_order_financials(orders, order_items):
    items_by_order = {}

    for item in order_items:
        items_by_order.setdefault(
            item["order_id"],
            []
        ).append(item)

    for order in orders:
        order_id = order["order_id"]

        if order_id not in items_by_order:
            raise ValueError(
                f"Order {order_id} has no order items."
            )

        items = items_by_order[order_id]

        calculated_subtotal = round(
            sum(
                item["quantity"] * item["unit_price"]
                for item in items
            ),
            2
        )

        calculated_discount = round(
            sum(
                item["discount_amount"]
                for item in items
            ),
            2
        )

        if order["subtotal_amount"] != calculated_subtotal:
            raise ValueError(
                f"Order {order_id} subtotal mismatch. "
                f"Expected {calculated_subtotal}, "
                f"got {order['subtotal_amount']}."
            )

        if order["discount_amount"] != calculated_discount:
            raise ValueError(
                f"Order {order_id} discount mismatch. "
                f"Expected {calculated_discount}, "
                f"got {order['discount_amount']}."
            )

        if order["discount_amount"] > order["subtotal_amount"]:
            raise ValueError(
                f"Order {order_id} discount exceeds subtotal."
            )

        calculated_total = round(
            order["subtotal_amount"]
            - order["discount_amount"]
            + order["tax_amount"]
            + order["shipping_amount"],
            2
        )

        if order["total_amount"] != calculated_total:
            raise ValueError(
                f"Order {order_id} total mismatch. "
                f"Expected {calculated_total}, "
                f"got {order['total_amount']}."
            )

        financial_fields = [
            "subtotal_amount",
            "discount_amount",
            "tax_amount",
            "shipping_amount",
            "total_amount",
        ]

        for field in financial_fields:
            if order[field] < 0:
                raise ValueError(
                    f"Order {order_id} has negative "
                    f"{field}: {order[field]}"
                )


def validate_order_references(
    orders,
    order_items,
    customers,
    locations,
    products,
    sellers,
):
    customer_ids = {
        customer["customer_id"]
        for customer in customers
    }

    location_ids = {
        location["location_id"]
        for location in locations
    }

    product_ids = {
        product["product_id"]
        for product in products
    }

    seller_ids = {
        seller["seller_id"]
        for seller in sellers
    }

    order_ids = {
        order["order_id"]
        for order in orders
    }

    for order in orders:

        if order["customer_id"] not in customer_ids:
            raise ValueError(
                f"Order {order['order_id']} references "
                f"unknown customer "
                f"{order['customer_id']}."
            )

        if order["shipping_location_id"] not in location_ids:
            raise ValueError(
                f"Order {order['order_id']} references "
                f"unknown shipping location "
                f"{order['shipping_location_id']}."
            )

    for item in order_items:

        if item["order_id"] not in order_ids:
            raise ValueError(
                f"Order item {item['order_item_id']} references "
                f"unknown order {item['order_id']}."
            )

        if item["product_id"] not in product_ids:
            raise ValueError(
                f"Order item {item['order_item_id']} references "
                f"unknown product {item['product_id']}."
            )

        if item["seller_id"] not in seller_ids:
            raise ValueError(
                f"Order item {item['order_item_id']} references "
                f"unknown seller {item['seller_id']}."
            )


def validate_orders_have_items(orders, order_items):
    order_ids_with_items = {
        item["order_id"]
        for item in order_items
    }

    for order in orders:
        if order["order_id"] not in order_ids_with_items:
            raise ValueError(
                f"Order {order['order_id']} has no order items."
            )


def validate_active_sellers(order_items, sellers):
    seller_status_lookup = {
        seller["seller_id"]: seller["seller_status"]
        for seller in sellers
    }

    invalid_items = [
        item
        for item in order_items
        if seller_status_lookup.get(item["seller_id"]) != "Active"
    ]

    if invalid_items:
        raise ValueError(
            f"Found {len(invalid_items)} order items assigned "
            f"to non-active sellers."
        )


if __name__ == "__main__":

    from data_generator.generators.orders import (
        generate_orders,
        apply_order_financials,
    )

    from data_generator.generators.order_items import (
        generate_order_items,
    )

    from data_generator.generators.order_financials import (
        calculate_order_financials,
    )

    from data_generator.generators.seller_product_mapping import (
        build_seller_product_mapping,
    )

    # ---------------------------------------------------------
    # Generate source data
    # ---------------------------------------------------------

    customers = generate_customers()

    products = generate_products()

    sellers = generate_sellers()

    locations = pd.read_csv(
        LOCATION_FILE,
        dtype={"Pincode": "string"}
    ).to_dict("records")

    seller_product_mapping = build_seller_product_mapping(
        products,
        sellers
    )

    orders = generate_orders(
        customers
    )

    order_items = generate_order_items(
        orders,
        products,
        sellers,
        seller_product_mapping
    )

    # ---------------------------------------------------------
    # Calculate order-level financials
    # ---------------------------------------------------------

    items_by_order = {}

    for item in order_items:
        items_by_order.setdefault(
            item["order_id"],
            []
        ).append(item)

    for order in orders:

        financials = calculate_order_financials(
            items_by_order[order["order_id"]]
        )

        apply_order_financials(
            order,
            financials
        )

    # ---------------------------------------------------------
    # Run validations
    # ---------------------------------------------------------

    validate_order_structure(
        orders
    )

    validate_order_dates(
        orders
    )

    validate_order_financials(
        orders,
        order_items
    )

    validate_order_references(
        orders,
        order_items,
        customers,
        locations,
        products,
        sellers,
    )

    validate_orders_have_items(
        orders,
        order_items
    )

    validate_active_sellers(
        order_items,
        sellers
    )

    # ---------------------------------------------------------
    # Validation results
    # ---------------------------------------------------------

    print(
        "Order structure validation passed."
    )

    print(
        "Order date validation passed."
    )

    print(
        "Order financial validation passed."
    )

    print(
        "Order reference validation passed."
    )

    print(
        "Order item coverage validation passed."
    )

    print(
        "Active seller validation passed."
    )