EVENT_TYPES = [
    "ProductViewed",
    "ProductSearched",
    "AddedToCart",
    "RemovedFromCart",
    "WishlistAdded",
    "CheckoutStarted",
    "OrderPlaced",
]

EVENT_TYPE_DISTRIBUTION = {
    "ProductViewed": 0.45,
    "ProductSearched": 0.20,
    "AddedToCart": 0.12,
    "RemovedFromCart": 0.05,
    "WishlistAdded": 0.05,
    "CheckoutStarted": 0.08,
    "OrderPlaced": 0.05,
}

DEVICE_TYPES = [
    "Android",
    "iOS",
    "Web",
]

DEVICE_TYPE_DISTRIBUTION = {
    "Android": 0.50,
    "iOS": 0.25,
    "Web": 0.25,
}

SESSION_ID_LENGTH = 16