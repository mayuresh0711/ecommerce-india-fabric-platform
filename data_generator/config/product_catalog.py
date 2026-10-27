# ============================================================
# Product Catalog Configuration
# ============================================================
#
# Structure:
#
# Category
#   -> Product Type
#       -> Valid Brands
#       -> Minimum Price
#       -> Maximum Price
#
# This configuration is used by products.py to generate
# category-consistent synthetic products.
# ============================================================


PRODUCT_CATALOG = {

    "Mobiles": {
        "Smartphone": {
            "brands": [
                "Samsung",
                "OnePlus",
                "Xiaomi",
                "Motorola",
            ],
            "min_price": 8000,
            "max_price": 100000,
        },
    },

    "Laptops": {
        "Laptop": {
            "brands": [
                "Dell",
                "HP",
                "Lenovo",
                "Asus",
            ],
            "min_price": 30000,
            "max_price": 150000,
        },
    },

    "Tablets": {
        "Tablet": {
            "brands": [
                "Samsung",
                "Lenovo",
                "OnePlus",
                "Xiaomi",
            ],
            "min_price": 10000,
            "max_price": 80000,
        },
    },

    "Televisions": {
        "Smart TV": {
            "brands": [
                "Samsung",
                "LG",
                "Sony",
                "TCL",
            ],
            "min_price": 15000,
            "max_price": 200000,
        },
    },

    "Audio": {
        "Headphones": {
            "brands": [
                "Sony",
                "JBL",
                "Bose",
                "Sennheiser",
            ],
            "min_price": 800,
            "max_price": 40000,
        },
        "Earbuds": {
            "brands": [
                "Apple",
                "Samsung",
                "OnePlus",
                "JBL",
            ],
            "min_price": 1000,
            "max_price": 30000,
        },
        "Bluetooth Speaker": {
            "brands": [
                "JBL",
                "Sony",
                "Bose",
                "Boat",
            ],
            "min_price": 1000,
            "max_price": 50000,
        },
    },

    "Cameras": {
        "Digital Camera": {
            "brands": [
                "Canon",
                "Nikon",
                "Sony",
                "Fujifilm",
            ],
            "min_price": 20000,
            "max_price": 250000,
        },
        "Action Camera": {
            "brands": [
                "GoPro",
                "DJI",
                "Insta360",
            ],
            "min_price": 15000,
            "max_price": 80000,
        },
    },

    "Computer Accessories": {
        "Keyboard": {
            "brands": [
                "Logitech",
                "HP",
                "Lenovo",
                "Redragon",
            ],
            "min_price": 800,
            "max_price": 15000,
        },
        "Mouse": {
            "brands": [
                "Logitech",
                "HP",
                "Lenovo",
                "Razer",
            ],
            "min_price": 400,
            "max_price": 10000,
        },
        "Monitor": {
            "brands": [
                "Dell",
                "LG",
                "Samsung",
                "Acer",
            ],
            "min_price": 7000,
            "max_price": 80000,
        },
    },

    "Home Appliances": {
        "Refrigerator": {
            "brands": [
                "LG",
                "Samsung",
                "Whirlpool",
                "Godrej",
            ],
            "min_price": 20000,
            "max_price": 100000,
        },
        "Washing Machine": {
            "brands": [
                "LG",
                "Samsung",
                "IFB",
                "Whirlpool",
            ],
            "min_price": 18000,
            "max_price": 80000,
        },
        "Air Conditioner": {
            "brands": [
                "LG",
                "Voltas",
                "Daikin",
                "Blue Star",
            ],
            "min_price": 25000,
            "max_price": 100000,
        },
    },

    "Kitchen Appliances": {
        "Coffee Maker": {
            "brands": [
                "Philips",
                "Morphy Richards",
                "Prestige",
                "Bajaj",
            ],
            "min_price": 1500,
            "max_price": 20000,
        },
        "Air Fryer": {
            "brands": [
                "Philips",
                "Havells",
                "Prestige",
                "Agaro",
            ],
            "min_price": 3000,
            "max_price": 20000,
        },
        "Mixer Grinder": {
            "brands": [
                "Preethi",
                "Bajaj",
                "Philips",
                "Sujata",
            ],
            "min_price": 2000,
            "max_price": 12000,
        },
    },

    "Furniture": {
        "Office Chair": {
            "brands": [
                "Green Soul",
                "Featherlite",
                "Sleep Company",
            ],
            "min_price": 5000,
            "max_price": 30000,
        },
        "Study Table": {
            "brands": [
                "Wakefit",
                "Nilkamal",
                "HomeTown",
            ],
            "min_price": 3000,
            "max_price": 25000,
        },
    },

    "Home Decor": {
        "Wall Art": {
            "brands": [
                "Homesake",
                "Chumbak",
                "India Circus",
            ],
            "min_price": 300,
            "max_price": 5000,
        },
        "Table Lamp": {
            "brands": [
                "Philips",
                "Wipro",
                "Havells",
            ],
            "min_price": 500,
            "max_price": 8000,
        },
    },

    "Grocery": {
        "Rice": {
            "brands": [
                "India Gate",
                "Daawat",
                "Fortune",
            ],
            "min_price": 100,
            "max_price": 2500,
        },
        "Cooking Oil": {
            "brands": [
                "Fortune",
                "Saffola",
                "Gemini",
            ],
            "min_price": 100,
            "max_price": 2000,
        },
        "Biscuits": {
            "brands": [
                "Britannia",
                "Parle",
                "Sunfeast",
            ],
            "min_price": 20,
            "max_price": 500,
        },
        "Coffee": {
            "brands": [
                "Nescafé",
                "Bru",
                "Tata Coffee",
            ],
            "min_price": 100,
            "max_price": 1500,
        },
        "Tea": {
            "brands": [
                "Tata Tea",
                "Brooke Bond",
                "Wagh Bakri",
            ],
            "min_price": 100,
            "max_price": 1500,
        },
        "Spices": {
            "brands": [
                "Everest",
                "MDH",
                "Catch",
            ],
            "min_price": 30,
            "max_price": 800,
        },
    },

    "Beauty & Personal Care": {
        "Face Wash": {
            "brands": [
                "Cetaphil",
                "Neutrogena",
                "Nivea",
            ],
            "min_price": 200,
            "max_price": 1500,
        },
        "Shampoo": {
            "brands": [
                "Dove",
                "L'Oréal",
                "Head & Shoulders",
            ],
            "min_price": 200,
            "max_price": 1500,
        },
        "Moisturizer": {
            "brands": [
                "Cetaphil",
                "Nivea",
                "Neutrogena",
            ],
            "min_price": 250,
            "max_price": 2000,
        },
        "Perfume": {
            "brands": [
                "Titan",
                "Davidoff",
                "Calvin Klein",
            ],
            "min_price": 500,
            "max_price": 10000,
        },
        "Hair Dryer": {
            "brands": [
                "Philips",
                "Havells",
                "Dyson",
            ],
            "min_price": 1000,
            "max_price": 40000,
        },
        "Trimmer": {
            "brands": [
                "Philips",
                "Braun",
                "Xiaomi",
            ],
            "min_price": 800,
            "max_price": 8000,
        },
    },

    "Fashion": {
        "T-Shirt": {
            "brands": [
                "Levi's",
                "Puma",
                "Adidas",
                "U.S. Polo Assn.",
            ],
            "min_price": 500,
            "max_price": 4000,
        },
        "Jeans": {
            "brands": [
                "Levi's",
                "Wrangler",
                "Lee",
            ],
            "min_price": 1000,
            "max_price": 6000,
        },
        "Jacket": {
            "brands": [
                "Levi's",
                "Puma",
                "Adidas",
            ],
            "min_price": 1500,
            "max_price": 12000,
        },
        "Saree": {
            "brands": [
                "Biba",
                "W",
                "FabIndia",
            ],
            "min_price": 1000,
            "max_price": 15000,
        },
        "Formal Shirt": {
            "brands": [
                "Van Heusen",
                "Louis Philippe",
                "Peter England",
            ],
            "min_price": 800,
            "max_price": 5000,
        },
    },

    "Footwear": {
        "Sneakers": {
            "brands": [
                "Nike",
                "Adidas",
                "Puma",
                "Reebok",
            ],
            "min_price": 2000,
            "max_price": 15000,
        },
        "Running Shoes": {
            "brands": [
                "Nike",
                "Adidas",
                "Asics",
                "Skechers",
            ],
            "min_price": 2500,
            "max_price": 18000,
        },
        "Formal Shoes": {
            "brands": [
                "Bata",
                "Hush Puppies",
                "Clarks",
            ],
            "min_price": 2000,
            "max_price": 12000,
        },
    },

    "Sports & Fitness": {
        "Yoga Mat": {
            "brands": [
                "Nike",
                "Boldfit",
                "Decathlon",
            ],
            "min_price": 400,
            "max_price": 5000,
        },
        "Dumbbell Set": {
            "brands": [
                "AmazonBasics",
                "Boldfit",
                "Kore",
            ],
            "min_price": 1000,
            "max_price": 15000,
        },
        "Treadmill": {
            "brands": [
                "PowerMax",
                "Lifelong",
                "Fitkit",
            ],
            "min_price": 15000,
            "max_price": 100000,
        },
        "Exercise Cycle": {
            "brands": [
                "PowerMax",
                "Reach",
                "Lifelong",
            ],
            "min_price": 8000,
            "max_price": 50000,
        },
    },

    "Books": {
        "Fiction": {
            "brands": [
                "Penguin",
                "HarperCollins",
                "Hachette",
            ],
            "min_price": 200,
            "max_price": 1000,
        },
        "Non-Fiction": {
            "brands": [
                "Penguin",
                "HarperCollins",
            ],
            "min_price": 250,
            "max_price": 1500,
        },
        "Academic": {
            "brands": [
                "Pearson",
                "McGraw Hill",
                "Oxford",
            ],
            "min_price": 400,
            "max_price": 4000,
        },
        "Competitive Exam": {
            "brands": [
                "Arihant",
                "Oswaal",
                "Disha",
            ],
            "min_price": 150,
            "max_price": 1500,
        },
        "Programming Books": {
            "brands": [
                "O'Reilly",
                "Packt",
                "Manning",
            ],
            "min_price": 500,
            "max_price": 4000,
        },
    },

    "Toys & Games": {
        "Board Game": {
            "brands": [
                "Hasbro",
                "Mattel",
                "Funskool",
            ],
            "min_price": 300,
            "max_price": 4000,
        },
        "Building Blocks": {
            "brands": [
                "LEGO",
                "Funskool",
            ],
            "min_price": 500,
            "max_price": 15000,
        },
        "Remote Control Car": {
            "brands": [
                "Rastar",
                "Maisto",
            ],
            "min_price": 800,
            "max_price": 8000,
        },
        "Educational Toy": {
            "brands": [
                "Funskool",
                "Smartivity",
            ],
            "min_price": 300,
            "max_price": 5000,
        },
        "Action Figure": {
            "brands": [
                "Hasbro",
                "Mattel",
            ],
            "min_price": 500,
            "max_price": 5000,
        },
        "Puzzle": {
            "brands": [
                "Funskool",
                "Ravensburger",
            ],
            "min_price": 200,
            "max_price": 3000,
        },
    },

    "Automotive": {
        "Car Battery": {
            "brands": [
                "Exide",
                "Amaron",
                "Luminous",
            ],
            "min_price": 4000,
            "max_price": 20000,
        },
        "Car Floor Mat": {
            "brands": [
                "3M",
                "Autoform",
            ],
            "min_price": 1000,
            "max_price": 8000,
        },
        "Car Air Purifier": {
            "brands": [
                "Philips",
                "Honeywell",
            ],
            "min_price": 2000,
            "max_price": 15000,
        },
        "Engine Oil": {
            "brands": [
                "Castrol",
                "Mobil",
                "Shell",
            ],
            "min_price": 500,
            "max_price": 8000,
        },
        "Car Charger": {
            "brands": [
                "Portronics",
                "Belkin",
            ],
            "min_price": 300,
            "max_price": 3000,
        },
        "Dash Camera": {
            "brands": [
                "70mai",
                "DDPAI",
            ],
            "min_price": 3000,
            "max_price": 20000,
        },
    },

    "Pet Supplies": {
        "Dog Food": {
            "brands": [
                "Pedigree",
                "Royal Canin",
                "Drools",
            ],
            "min_price": 200,
            "max_price": 8000,
        },
        "Cat Food": {
            "brands": [
                "Whiskas",
                "Royal Canin",
                "Me-O",
            ],
            "min_price": 200,
            "max_price": 8000,
        },
        "Pet Bed": {
            "brands": [
                "Heads Up For Tails",
                "AmazonBasics",
            ],
            "min_price": 500,
            "max_price": 8000,
        },
        "Pet Collar": {
            "brands": [
                "Heads Up For Tails",
                "Trixie",
            ],
            "min_price": 200,
            "max_price": 2000,
        },
        "Pet Shampoo": {
            "brands": [
                "Himalaya",
                "Beaphar",
            ],
            "min_price": 200,
            "max_price": 1500,
        },
        "Pet Toy": {
            "brands": [
                "Kong",
                "Trixie",
            ],
            "min_price": 200,
            "max_price": 3000,
        },
    },
}