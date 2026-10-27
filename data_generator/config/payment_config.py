PAYMENT_METHODS = [
    "UPI",
    "Credit Card",
    "Debit Card",
    "Net Banking",
    "Wallet",
    "Cash on Delivery",
    "EMI",
]


PAYMENT_METHOD_DISTRIBUTION = {
    "UPI": 0.35,
    "Credit Card": 0.20,
    "Debit Card": 0.15,
    "Net Banking": 0.10,
    "Wallet": 0.08,
    "Cash on Delivery": 0.07,
    "EMI": 0.05,
}


PAYMENT_STATUS_DISTRIBUTION = {
    "Completed": 0.85,
    "Pending": 0.05,
    "Failed": 0.07,
    "Refunded": 0.03,
}


MIN_PAYMENT_AMOUNT = 1.00

PAYMENT_SCENARIO_DISTRIBUTION = {
    "Single Payment": 0.90,
    "Payment Retry": 0.07,
    "Multiple Completed Payments": 0.03,
}