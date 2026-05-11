CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    customer_group_id INTEGER,
    customer_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    product_desc VARCHAR(255),
    product_min_weight NUMERIC(18, 2),
    product_max_weight NUMERIC(18, 2),
    product_group VARCHAR(100),
    product_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS resources (
    resource_id INTEGER PRIMARY KEY,
    resource_desc VARCHAR(255),
    wearout INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sales_orders (
    sales_order_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    product_id INTEGER,
    target_weight NUMERIC(18, 2),
    tolerance NUMERIC(10, 2),
    unit_weight NUMERIC(18, 2),
    due_date DATE,
    priority INTEGER,
    status INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Связи
    CONSTRAINT fk_sales_orders_customer FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id) ON DELETE CASCADE,
    CONSTRAINT fk_sales_orders_product FOREIGN KEY (product_id)
        REFERENCES products(product_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS standard_operations (
    operation_ref INTEGER PRIMARY KEY,
    product_id INTEGER,
    resource_id INTEGER,
    alternate_pref INTEGER,
    operation_id INTEGER,
    performance INTEGER,
    yield DOUBLE PRECISION,

    -- Связи
    CONSTRAINT fk_std_ops_product FOREIGN KEY (product_id)
        REFERENCES products(product_id) ON DELETE CASCADE,
    CONSTRAINT fk_std_ops_resource FOREIGN KEY (resource_id)
        REFERENCES resources(resource_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS calendar (
    production_date DATE,
    resource_id INTEGER,
    available_hours NUMERIC(5, 2),

    PRIMARY KEY (production_date, resource_id),

    -- Связь
    CONSTRAINT fk_calendar_resource FOREIGN KEY (resource_id)
        REFERENCES resources(resource_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS mrp_plan (
    plan_id BIGSERIAL PRIMARY KEY,
    sales_order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    resource_id INTEGER NOT NULL,
    operation_id INTEGER NOT NULL,
    plan_date DATE NOT NULL,
    hours NUMERIC(12, 3) NOT NULL,
    tons NUMERIC(18, 3) NOT NULL,
    units NUMERIC(18, 3) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_mrp_plan_sales_order FOREIGN KEY (sales_order_id)
        REFERENCES sales_orders(sales_order_id) ON DELETE CASCADE,
    CONSTRAINT fk_mrp_plan_product FOREIGN KEY (product_id)
        REFERENCES products(product_id) ON DELETE CASCADE,
    CONSTRAINT fk_mrp_plan_resource FOREIGN KEY (resource_id)
        REFERENCES resources(resource_id) ON DELETE CASCADE
);
