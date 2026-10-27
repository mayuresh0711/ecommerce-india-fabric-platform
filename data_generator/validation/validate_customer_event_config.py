from data_generator.config.customer_event_config import (
    EVENT_TYPES,
    EVENT_TYPE_DISTRIBUTION,
    DEVICE_TYPES,
    DEVICE_TYPE_DISTRIBUTION,
    SESSION_ID_LENGTH,
)


def validate_customer_event_config():

    if not EVENT_TYPES:
        raise ValueError("Event type list is empty.")

    if set(EVENT_TYPES) != set(EVENT_TYPE_DISTRIBUTION.keys()):
        raise ValueError(
            "Event types and event distribution do not match."
        )

    event_total = sum(
        EVENT_TYPE_DISTRIBUTION.values()
    )

    if round(event_total, 5) != 1.0:
        raise ValueError(
            f"Event distribution must equal 1.0, got {event_total}"
        )

    if not DEVICE_TYPES:
        raise ValueError("Device type list is empty.")

    if set(DEVICE_TYPES) != set(DEVICE_TYPE_DISTRIBUTION.keys()):
        raise ValueError(
            "Device types and device distribution do not match."
        )

    device_total = sum(
        DEVICE_TYPE_DISTRIBUTION.values()
    )

    if round(device_total, 5) != 1.0:
        raise ValueError(
            f"Device distribution must equal 1.0, got {device_total}"
        )

    if SESSION_ID_LENGTH <= 0:
        raise ValueError(
            "Session ID length must be positive."
        )

    if any(
        probability < 0
        for probability in EVENT_TYPE_DISTRIBUTION.values()
    ):
        raise ValueError(
            "Event probabilities cannot be negative."
        )

    if any(
        probability < 0
        for probability in DEVICE_TYPE_DISTRIBUTION.values()
    ):
        raise ValueError(
            "Device probabilities cannot be negative."
        )

    print("Customer event configuration validation passed.")
    print(f"Event types: {len(EVENT_TYPES)}")
    print(f"Device types: {len(DEVICE_TYPES)}")


if __name__ == "__main__":
    validate_customer_event_config()