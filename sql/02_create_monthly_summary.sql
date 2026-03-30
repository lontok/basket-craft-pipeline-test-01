CREATE OR REPLACE VIEW monthly_sales_summary AS
SELECT
    DATE_TRUNC('month', order_date) AS month,
    cuisine_type,
    COUNT(*) AS order_count,
    SUM(order_value) AS total_revenue,
    AVG(order_value) AS avg_order_value
FROM raw_orders
GROUP BY DATE_TRUNC('month', order_date), cuisine_type
ORDER BY DATE_TRUNC('month', order_date), cuisine_type;
