from data_generator.validation.validate_orders import (
    validate_order_structure,
    validate_order_dates,
    validate_order_financials,
    validate_order_references,
    validate_orders_have_items,
    validate_active_sellers,
)

from data_generator.validation.validate_payments import (
    validate_payment_structure,
    validate_payment_values,
    validate_payment_order_references,
    validate_orders_have_payments,
    validate_payment_reconciliation,
)

from data_generator.validation.validate_customer_events import (
    validate_event_structure,
    validate_event_values,
    validate_event_references,
)


def validate_initial_data(
    customers,
    products,
    sellers,
    orders,
    order_items,
    payments,
    customer_events,
    locations,
):
    print("Starting final source-data validation...")

    # --------------------------------------------------
    # Orders
    # --------------------------------------------------

    validate_order_structure(
        orders
    )

    validate_order_dates(
        orders
    )

    validate_order_financials(
        orders,
        order_items,
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
        order_items,
    )

    validate_active_sellers(
        order_items,
        sellers,
    )

    print("Order validation passed.")

    # --------------------------------------------------
    # Payments
    # --------------------------------------------------

    validate_payment_structure(
        payments
    )

    validate_payment_values(
        payments
    )

    validate_payment_order_references(
        payments,
        orders,
    )

    validate_orders_have_payments(
        payments,
        orders,
    )

    validate_payment_reconciliation(
        payments,
        orders,
    )

    print("Payment validation passed.")

    # --------------------------------------------------
    # Customer Events
    # --------------------------------------------------

    validate_event_structure(
        customer_events
    )

    validate_event_values(
        customer_events
    )

    validate_event_references(
        customer_events,
        customers,
        products,
    )

    print("Customer event validation passed.")

    # --------------------------------------------------
    # Final result
    # --------------------------------------------------

    print(
        "Final source-data validation passed."
    )