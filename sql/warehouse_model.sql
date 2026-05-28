CREATE TABLE sales_analytics.dim_store (
    store_id INT64,
    store_name STRING
);

CREATE TABLE sales_analytics.dim_product (
    product_id INT64,
    product_name STRING
);

CREATE TABLE sales_analytics.dim_date (
    date_id DATE
);

CREATE TABLE sales_analytics.fact_sales (
    sale_id INT64,
    store_id INT64,
    product_id INT64,
    date_id DATE,
    total_amount FLOAT64,
    quantity INT64
);