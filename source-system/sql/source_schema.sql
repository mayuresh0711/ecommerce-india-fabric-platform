IF OBJECT_ID('dbo.locations', 'U') IS NULL
BEGIN
    CREATE TABLE locations
    (
        location_id INT NOT NULL,
        pincode CHAR(6) NOT NULL,
        city VARCHAR(100) NOT NULL,
        district VARCHAR(100) NOT NULL,
        state VARCHAR(100) NOT NULL,
        region VARCHAR(20) NOT NULL,
        country VARCHAR(50) NOT NULL,

        CONSTRAINT PK_locations
            PRIMARY KEY (location_id),

        CONSTRAINT UQ_locations_pincode
            UNIQUE (pincode),

        CONSTRAINT CK_locations_country
            CHECK (country = 'India')
    );
END;


IF OBJECT_ID('dbo.customers', 'U') IS NULL
BEGIN
    CREATE TABLE customers
    (
        customer_id BIGINT NOT NULL,
        customer_name VARCHAR(150) NOT NULL,
        email VARCHAR(150) NOT NULL,
        phone VARCHAR(15) NOT NULL,
        location_id INT NOT NULL,
        customer_status VARCHAR(20) NOT NULL,
        signup_date DATE NOT NULL,
        created_at DATETIME2 NOT NULL,
        updated_at DATETIME2 NOT NULL,

        CONSTRAINT PK_customers
            PRIMARY KEY (customer_id),

        CONSTRAINT UQ_customers_email
            UNIQUE (email),

        CONSTRAINT FK_customers_locations
            FOREIGN KEY (location_id)
            REFERENCES locations(location_id),

        CONSTRAINT CK_customers_status
            CHECK (customer_status IN
                ('Active', 'Inactive', 'Blocked')),

        CONSTRAINT CK_customers_dates
            CHECK (updated_at >= created_at)
    );
END;


IF OBJECT_ID('dbo.sellers', 'U') IS NULL
BEGIN
    CREATE TABLE sellers
    (
        seller_id BIGINT NOT NULL,
        seller_name VARCHAR(150) NOT NULL,
        location_id INT NOT NULL,
        seller_status VARCHAR(20) NOT NULL,
        created_at DATETIME2 NOT NULL,
        updated_at DATETIME2 NOT NULL,

        CONSTRAINT PK_sellers
            PRIMARY KEY (seller_id),

        CONSTRAINT FK_sellers_locations
            FOREIGN KEY (location_id)
            REFERENCES locations(location_id),

        CONSTRAINT CK_sellers_status
            CHECK (seller_status IN
                ('Active', 'Inactive', 'Suspended')),

        CONSTRAINT CK_sellers_dates
            CHECK (updated_at >= created_at)
    );
END;


IF OBJECT_ID('dbo.categories', 'U') IS NULL
BEGIN
    CREATE TABLE categories
    (
        category_id INT NOT NULL,
        category_name VARCHAR(100) NOT NULL,
        category_status VARCHAR(20) NOT NULL,
        created_at DATETIME2 NOT NULL,
        updated_at DATETIME2 NOT NULL,

        CONSTRAINT PK_categories
            PRIMARY KEY (category_id),

        CONSTRAINT UQ_categories_name
            UNIQUE (category_name),

        CONSTRAINT CK_categories_status
            CHECK (category_status IN
                ('Active', 'Inactive')),

        CONSTRAINT CK_categories_dates
            CHECK (updated_at >= created_at)
    );
END;


IF OBJECT_ID('dbo.products', 'U') IS NULL
BEGIN
    CREATE TABLE products
    (
        product_id BIGINT NOT NULL,
        category_id INT NOT NULL,
        product_name VARCHAR(200) NOT NULL,
        brand VARCHAR(100) NOT NULL,
        product_type VARCHAR(100) NOT NULL,
        unit_price DECIMAL(12,2) NOT NULL,
        product_status VARCHAR(20) NOT NULL,
        created_at DATETIME2 NOT NULL,
        updated_at DATETIME2 NOT NULL,

        CONSTRAINT PK_products
            PRIMARY KEY (product_id),

        CONSTRAINT FK_products_categories
            FOREIGN KEY (category_id)
            REFERENCES categories(category_id),

        CONSTRAINT CK_products_price
            CHECK (unit_price >= 0),

        CONSTRAINT CK_products_status
            CHECK (product_status IN
                ('Active', 'Inactive', 'Discontinued')),

        CONSTRAINT CK_products_dates
            CHECK (updated_at >= created_at)
    );
END;


IF OBJECT_ID('dbo.orders', 'U') IS NULL
BEGIN
    CREATE TABLE orders
    (
        order_id BIGINT NOT NULL,
        customer_id BIGINT NOT NULL,
        order_date DATETIME2 NOT NULL,
        order_status VARCHAR(20) NOT NULL,
        shipping_location_id INT NOT NULL,
        subtotal_amount DECIMAL(12,2) NOT NULL,
        discount_amount DECIMAL(12,2) NOT NULL,
        tax_amount DECIMAL(12,2) NOT NULL,
        shipping_amount DECIMAL(12,2) NOT NULL,
        total_amount DECIMAL(12,2) NOT NULL,
        created_at DATETIME2 NOT NULL,
        updated_at DATETIME2 NOT NULL,

        CONSTRAINT PK_orders
            PRIMARY KEY (order_id),

        CONSTRAINT FK_orders_customers
            FOREIGN KEY (customer_id)
            REFERENCES customers(customer_id),

        CONSTRAINT FK_orders_shipping_location
            FOREIGN KEY (shipping_location_id)
            REFERENCES locations(location_id),

        CONSTRAINT CK_orders_status
            CHECK (order_status IN
                ('Pending', 'Confirmed', 'Shipped',
                 'Delivered', 'Cancelled', 'Returned')),

        CONSTRAINT CK_orders_amounts
            CHECK (
                subtotal_amount >= 0
                AND discount_amount >= 0
                AND tax_amount >= 0
                AND shipping_amount >= 0
                AND discount_amount <= subtotal_amount
            ),

        CONSTRAINT CK_orders_total
            CHECK (
                total_amount =
                subtotal_amount
                - discount_amount
                + tax_amount
                + shipping_amount
            ),

        CONSTRAINT CK_orders_dates
            CHECK (updated_at >= created_at)
    );
END;


IF OBJECT_ID('dbo.order_items', 'U') IS NULL
BEGIN
    CREATE TABLE order_items
    (
        order_item_id BIGINT NOT NULL,
        order_id BIGINT NOT NULL,
        product_id BIGINT NOT NULL,
        seller_id BIGINT NOT NULL,
        quantity INT NOT NULL,
        unit_price DECIMAL(12,2) NOT NULL,
        discount_amount DECIMAL(12,2) NOT NULL,
        created_at DATETIME2 NOT NULL,
        updated_at DATETIME2 NOT NULL,

        CONSTRAINT PK_order_items
            PRIMARY KEY (order_item_id),

        CONSTRAINT FK_order_items_orders
            FOREIGN KEY (order_id)
            REFERENCES orders(order_id),

        CONSTRAINT FK_order_items_products
            FOREIGN KEY (product_id)
            REFERENCES products(product_id),

        CONSTRAINT FK_order_items_sellers
            FOREIGN KEY (seller_id)
            REFERENCES sellers(seller_id),

        CONSTRAINT CK_order_items_quantity
            CHECK (quantity > 0),

        CONSTRAINT CK_order_items_price
            CHECK (unit_price >= 0),

        CONSTRAINT CK_order_items_discount
            CHECK (
                discount_amount >= 0
                AND discount_amount <= quantity * unit_price
            ),

        CONSTRAINT CK_order_items_dates
            CHECK (updated_at >= created_at)
    );
END;


IF OBJECT_ID('dbo.payments', 'U') IS NULL
BEGIN
    CREATE TABLE payments
    (
        payment_id BIGINT NOT NULL,
        order_id BIGINT NOT NULL,
        payment_timestamp DATETIME2 NOT NULL,
        payment_method VARCHAR(30) NOT NULL,
        payment_amount DECIMAL(12,2) NOT NULL,
        payment_status VARCHAR(20) NOT NULL,
        transaction_reference VARCHAR(100) NOT NULL,
        created_at DATETIME2 NOT NULL,
        updated_at DATETIME2 NOT NULL,

        CONSTRAINT PK_payments
            PRIMARY KEY (payment_id),

        CONSTRAINT FK_payments_orders
            FOREIGN KEY (order_id)
            REFERENCES orders(order_id),

        CONSTRAINT UQ_payments_transaction_reference
            UNIQUE (transaction_reference),

        CONSTRAINT CK_payments_amount
            CHECK (payment_amount > 0),

        CONSTRAINT CK_payments_method
            CHECK (payment_method IN
                ('UPI', 'Credit Card', 'Debit Card',
                 'Net Banking', 'Wallet',
                 'Cash on Delivery', 'EMI')),

        CONSTRAINT CK_payments_status
            CHECK (payment_status IN
                ('Pending', 'Completed', 'Failed', 'Refunded')),

        CONSTRAINT CK_payments_dates
            CHECK (updated_at >= created_at)
    );
END;


SELECT
    TABLE_SCHEMA,
    TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'dbo'
  AND TABLE_NAME IN
  (
      'locations',
      'customers',
      'sellers',
      'categories',
      'products',
      'orders',
      'order_items',
      'payments'
  )
ORDER BY TABLE_NAME;