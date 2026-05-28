-- ============================================
-- POPULATE STAR SCHEMA
-- Idempotente: solo inserta lo que no existe
-- ============================================

-- Dimensión tienda
INSERT INTO sales_analytics.dim_store (store_id, store_name)
SELECT
    ROW_NUMBER() OVER (ORDER BY tienda)
    + (SELECT COALESCE(MAX(store_id), 0) FROM sales_analytics.dim_store),
    tienda
FROM (SELECT DISTINCT tienda FROM sales_analytics.sales_final)
WHERE tienda NOT IN (
    SELECT store_name FROM sales_analytics.dim_store
);

-- Dimensión producto
INSERT INTO sales_analytics.dim_product (product_id, product_name)
SELECT
    ROW_NUMBER() OVER (ORDER BY producto)
    + (SELECT COALESCE(MAX(product_id), 0) FROM sales_analytics.dim_product),
    producto
FROM (SELECT DISTINCT producto FROM sales_analytics.sales_final)
WHERE producto NOT IN (
    SELECT product_name FROM sales_analytics.dim_product
);

-- Dimensión fecha (solo días con ventas)
INSERT INTO sales_analytics.dim_date (date_id)
SELECT DISTINCT fecha
FROM sales_analytics.sales_final
WHERE fecha NOT IN (
    SELECT date_id FROM sales_analytics.dim_date
);

-- Tabla de hechos (se reconstruye completa cada vez)
TRUNCATE TABLE sales_analytics.fact_sales;

INSERT INTO sales_analytics.fact_sales (sale_id, store_id, product_id, date_id, total_amount, quantity)
SELECT
    ROW_NUMBER() OVER (ORDER BY s.fecha, s.tienda, s.producto),
    st.store_id,
    p.product_id,
    s.fecha,
    s.total,
    s.cantidad
FROM sales_analytics.sales_final s
LEFT JOIN sales_analytics.dim_store st ON st.store_name = s.tienda
LEFT JOIN sales_analytics.dim_product p ON p.product_name = s.producto;
