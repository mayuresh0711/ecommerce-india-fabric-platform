from data_generator.config.payment_config import (
    PAYMENT_METHODS,
    PAYMENT_STATUS_DISTRIBUTION,
)


def validate_payment_structure(payments):
    if not payments:
        raise ValueError("No payments were generated.")

    payment_ids = [payment["payment_id"] for payment in payments]

    if len(payment_ids) != len(set(payment_ids)):
        raise ValueError("Duplicate payment_id detected.")

    transaction_references = [
        payment["transaction_reference"]
        for payment in payments
    ]

    if len(transaction_references) != len(set(transaction_references)):
        raise ValueError(
            "Duplicate transaction_reference detected."
        )

    required_fields = {
        "payment_id",
        "order_id",
        "payment_timestamp",
        "payment_method",
        "payment_amount",
        "payment_status",
        "transaction_reference",
        "created_at",
        "updated_at",
    }

    for payment in payments:
        missing_fields = required_fields - payment.keys()

        if missing_fields:
            raise ValueError(
                f"Payment {payment['payment_id']} "
                f"is missing fields: {missing_fields}"
            )


def validate_payment_values(payments):
    valid_methods = set(PAYMENT_METHODS)
    valid_statuses = set(PAYMENT_STATUS_DISTRIBUTION.keys())

    for payment in payments:

        if payment["payment_method"] not in valid_methods:
            raise ValueError(
                f"Payment {payment['payment_id']} "
                f"has invalid payment method: "
                f"{payment['payment_method']}"
            )

        if payment["payment_status"] not in valid_statuses:
            raise ValueError(
                f"Payment {payment['payment_id']} "
                f"has invalid payment status: "
                f"{payment['payment_status']}"
            )

        if payment["payment_amount"] <= 0:
            raise ValueError(
                f"Payment {payment['payment_id']} "
                f"has invalid payment amount: "
                f"{payment['payment_amount']}"
            )

        if payment["updated_at"] < payment["created_at"]:
            raise ValueError(
                f"Payment {payment['payment_id']} "
                f"has updated_at before created_at."
            )


def validate_payment_order_references(payments, orders):
    order_lookup = {
        order["order_id"]: order
        for order in orders
    }

    for payment in payments:

        order_id = payment["order_id"]

        if order_id not in order_lookup:
            raise ValueError(
                f"Payment {payment['payment_id']} "
                f"references unknown order {order_id}."
            )

        order = order_lookup[order_id]

        if payment["payment_timestamp"] < order["order_date"]:
            raise ValueError(
                f"Payment {payment['payment_id']} "
                f"occurs before order {order_id}."
            )


def validate_orders_have_payments(payments, orders):
    payment_order_ids = {
        payment["order_id"]
        for payment in payments
    }

    for order in orders:
        if order["order_id"] not in payment_order_ids:
            raise ValueError(
                f"Order {order['order_id']} has no payment record."
            )


def validate_payment_reconciliation(payments, orders):
    payments_by_order = {}

    for payment in payments:
        payments_by_order.setdefault(
            payment["order_id"],
            []
        ).append(payment)

    for order in orders:

        order_id = order["order_id"]

        order_payments = payments_by_order.get(
            order_id,
            []
        )

        completed_amount = round(
            sum(
                payment["payment_amount"]
                for payment in order_payments
                if payment["payment_status"] == "Completed"
            ),
            2,
        )

        failed_amount = round(
            sum(
                payment["payment_amount"]
                for payment in order_payments
                if payment["payment_status"] == "Failed"
            ),
            2,
        )

        pending_amount = round(
            sum(
                payment["payment_amount"]
                for payment in order_payments
                if payment["payment_status"] == "Pending"
            ),
            2,
        )

        refunded_amount = round(
            sum(
                payment["payment_amount"]
                for payment in order_payments
                if payment["payment_status"] == "Refunded"
            ),
            2,
        )

        # Completed payments should normally reconcile
        # to the order total when the order has been paid.
        if completed_amount > 0:
            if completed_amount != round(order["total_amount"], 2):
                raise ValueError(
                    f"Order {order_id} completed payment mismatch. "
                    f"Expected {order['total_amount']}, "
                    f"got {completed_amount}."
                )

        # Failed, pending and refunded transactions are
        # not counted as successfully collected revenue.
        if failed_amount < 0:
            raise ValueError(
                f"Order {order_id} has invalid failed payment amount."
            )

        if pending_amount < 0:
            raise ValueError(
                f"Order {order_id} has invalid pending payment amount."
            )

        if refunded_amount < 0:
            raise ValueError(
                f"Order {order_id} has invalid refunded payment amount."
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
    from data_generator.generators.payments import (
        generate_payments,
    )

    orders = generate_orders()

    order_items = generate_order_items(orders)

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

    payments = generate_payments(orders)

    validate_payment_structure(payments)
    validate_payment_values(payments)
    validate_payment_order_references(payments, orders)
    validate_orders_have_payments(payments, orders)
    validate_payment_reconciliation(payments, orders)

    print("Payment structure validation passed.")
    print("Payment value validation passed.")
    print("Payment order reference validation passed.")
    print("Payment coverage validation passed.")
    print("Payment reconciliation validation passed.")