CREATE TABLE IF NOT EXISTS raw_orders (
    order_id INT PRIMARY KEY,
    order_date DATE NOT NULL,
    order_time TIME NOT NULL,
    customer_segment VARCHAR(20) NOT NULL,
    order_value NUMERIC(10,2) NOT NULL,
    cuisine_type VARCHAR(20) NOT NULL,
    delivery_time_mins INT NOT NULL,
    promo_code_used VARCHAR(3) NOT NULL,
    is_reorder VARCHAR(3)
);
