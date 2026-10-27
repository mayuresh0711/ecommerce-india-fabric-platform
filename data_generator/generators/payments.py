import random
from datetime import timedelta

from data_generator.config.payment_config import (
    MIN_PAYMENT_AMOUNT,
    PAYMENT_METHOD_DISTRIBUTION,
    PAYMENT_STATUS_DISTRIBUTION,
    PAYMENT_SCENARIO_DISTRIBUTION,
)

def generate_payment_scenario():
    scenarios = list(PAYMENT_SCENARIO_DISTRIBUTION.keys())
    probabilities = list(
        PAYMENT_SCENARIO_DISTRIBUTION.values()
    )

    return random.choices(
        scenarios,
        weights=probabilities,
        k=1
    )[0]


def build_payment_record(
    payment_id,
    order,
    payment_status,
    payment_amount,
    payment_method=None,
    timestamp_offset_minutes=1,
):
    payment_timestamp = (
        order["order_date"]
        + timedelta(minutes=timestamp_offset_minutes)
    )

    if payment_method is None:
        payment_method = generate_payment_method()

    return {
        "payment_id": payment_id,
        "order_id": order["order_id"],
        "payment_timestamp": payment_timestamp,
        "payment_method": payment_method,
        "payment_amount": round(payment_amount, 2),
        "payment_status": payment_status,
        "transaction_reference":
            generate_transaction_reference(payment_id),
        "created_at": payment_timestamp,
        "updated_at": payment_timestamp,
    }

def generate_payment_method():
    methods = list(PAYMENT_METHOD_DISTRIBUTION.keys())
    probabilities = list(
        PAYMENT_METHOD_DISTRIBUTION.values()
    )

    return random.choices(
        methods,
        weights=probabilities,
        k=1
    )[0]


def generate_payment_status():
    statuses = list(
        PAYMENT_STATUS_DISTRIBUTION.keys()
    )
    probabilities = list(
        PAYMENT_STATUS_DISTRIBUTION.values()
    )

    return random.choices(
        statuses,
        weights=probabilities,
        k=1
    )[0]


def generate_transaction_reference(payment_id):
    return f"TXN-{payment_id:08d}"


def generate_payment_timestamp(order):
    order_date = order["order_date"]

    return order_date + timedelta(
        minutes=random.randint(1, 1440)
    )


def generate_payment_amount(order):
    total_amount = order["total_amount"]

    if total_amount < MIN_PAYMENT_AMOUNT:
        raise ValueError(
            f"Order {order['order_id']} has invalid "
            f"total amount: {total_amount}"
        )

    return round(total_amount, 2)


def generate_payments(orders):
    payments = []

    payment_id = 1

    for order in orders:

        scenario = generate_payment_scenario()

        total_amount = order["total_amount"]

        if scenario == "Single Payment":

            payment_status = generate_payment_status()

            payments.append(
                build_payment_record(
                    payment_id=payment_id,
                    order=order,
                    payment_status=payment_status,
                    payment_amount=total_amount,
                )
            )

            payment_id += 1

        elif scenario == "Payment Retry":

            failed_amount = round(
                total_amount,
                2
            )

            payments.append(
                build_payment_record(
                    payment_id=payment_id,
                    order=order,
                    payment_status="Failed",
                    payment_amount=failed_amount,
                    timestamp_offset_minutes=5,
                )
            )

            payment_id += 1

            payments.append(
                build_payment_record(
                    payment_id=payment_id,
                    order=order,
                    payment_status="Completed",
                    payment_amount=total_amount,
                    timestamp_offset_minutes=15,
                )
            )

            payment_id += 1

        elif scenario == "Multiple Completed Payments":

            first_amount = round(
                total_amount * 0.50,
                2
            )

            second_amount = round(
                total_amount - first_amount,
                2
            )

            payments.append(
                build_payment_record(
                    payment_id=payment_id,
                    order=order,
                    payment_status="Completed",
                    payment_amount=first_amount,
                    timestamp_offset_minutes=10,
                )
            )

            payment_id += 1

            payments.append(
                build_payment_record(
                    payment_id=payment_id,
                    order=order,
                    payment_status="Completed",
                    payment_amount=second_amount,
                    timestamp_offset_minutes=30,
                )
            )

            payment_id += 1

        else:
            raise ValueError(
                f"Unknown payment scenario: {scenario}"
            )

    return payments

if __name__ == "__main__":
    from data_generator.generators.orders import (
        generate_orders,
    )
    from data_generator.generators.order_items import (
        generate_order_items,
    )
    from data_generator.generators.order_financials import (
        calculate_order_financials,
    )
    from data_generator.generators.orders import (
        apply_order_financials,
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

    print(
        f"Generated payments: {len(payments)}"
    )

    for payment in payments[:10]:
        print(payment)