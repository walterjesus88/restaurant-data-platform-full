CREATE TABLE IF NOT EXISTS sales_analytics.dim_store (
    store_id INT64,
    store_name STRING
);

CREATE TABLE IF NOT EXISTS sales_analytics.dim_product (
    product_id INT64,
    product_name STRING
);

CREATE TABLE IF NOT EXISTS sales_analytics.dim_date (
    date_id DATE
    EXTRACT(YEAR FROM date_id) AS year,
    EXTRACT(MONTH FROM date_id) AS month,
    EXTRACT(DAY FROM date_id) AS day,
    EXTRACT(DAYOFWEEK FROM date_id) AS day_of_week
);

CREATE TABLE IF NOT EXISTS sales_analytics.fact_sales (
    sale_id INT64,
    store_id INT64,
    product_id INT64,
    date_id DATE,
    total_amount FLOAT64,
    quantity INT64
);

CREATE TABLE IF NOT EXISTS sales_analytics.fact_inventory (
    inventory_id INT64,
    store_id INT64,
    product_id INT64,
    date_id DATE,
    stock INT64
);