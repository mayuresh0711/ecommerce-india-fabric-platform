from data_generator.config.payment_config import (
    PAYMENT_METHODS,
    PAYMENT_METHOD_DISTRIBUTION,
    PAYMENT_STATUS_DISTRIBUTION,
    PAYMENT_SCENARIO_DISTRIBUTION,
    MIN_PAYMENT_AMOUNT,
)
def validate_payment_config():

    if not PAYMENT_METHODS:
        raise ValueError(
            "Payment method list is empty."
        )

    if len(PAYMENT_METHODS) != len(
        PAYMENT_METHOD_DISTRIBUTION
    ):
        raise ValueError(
            "Payment method list and distribution do not match."
        )

    method_total = sum(
        PAYMENT_METHOD_DISTRIBUTION.values()
    )

    if round(method_total, 5) != 1.0:
        raise ValueError(
            f"Payment method distribution must equal 1.0, "
            f"got {method_total}"
        )

    status_total = sum(
        PAYMENT_STATUS_DISTRIBUTION.values()
    )

    if round(status_total, 5) != 1.0:
        raise ValueError(
            f"Payment status distribution must equal 1.0, "
            f"got {status_total}"
        )

    if MIN_PAYMENT_AMOUNT <= 0:
        raise ValueError(
            "Minimum payment amount must be positive."
        )

    print("Payment configuration validation passed.")
    print(
        f"Payment methods: {len(PAYMENT_METHODS)}"
    )

    scenario_total = sum(
        PAYMENT_SCENARIO_DISTRIBUTION.values()
    )

    if round(scenario_total, 5) != 1.0:
        raise ValueError(
            f"Payment scenario distribution must equal 1.0, "
            f"got {scenario_total}"
        )

    if any(
        probability < 0
        for probability in PAYMENT_SCENARIO_DISTRIBUTION.values()
    ):
        raise ValueError(
            "Payment scenario probabilities cannot be negative."
        )
    print(
        f"Payment scenarios: "
        f"{len(PAYMENT_SCENARIO_DISTRIBUTION)}"
    )


if __name__ == "__main__":
    validate_payment_config()