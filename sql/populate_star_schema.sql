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

-- Dimensión producto (desde sales + inventory)
INSERT INTO sales_analytics.dim_product (product_id, product_name)
SELECT
    ROW_NUMBER() OVER (ORDER BY producto)
    + (SELECT COALESCE(MAX(product_id), 0) FROM sales_analytics.dim_product),
    producto
FROM (
    SELECT DISTINCT producto FROM sales_analytics.sales_final
    UNION DISTINCT
    SELECT DISTINCT producto FROM sales_analytics.inventory_final
)
WHERE producto NOT IN (
    SELECT product_name FROM sales_analytics.dim_product
);

-- Dimensión fecha (rango completo: 5 años atrás → 1 año adelante)
INSERT INTO sales_analytics.dim_date
    (date_id, year, month, day, day_of_week, quarter, month_name, is_weekend)
SELECT
    d, EXTRACT(YEAR FROM d), EXTRACT(MONTH FROM d), EXTRACT(DAY FROM d),
    EXTRACT(DAYOFWEEK FROM d), EXTRACT(QUARTER FROM d),
    FORMAT_TIMESTAMP('%B', TIMESTAMP(d)),
    EXTRACT(DAYOFWEEK FROM d) IN (1, 7)
FROM UNNEST(GENERATE_DATE_ARRAY(
    DATE_SUB(CURRENT_DATE(), INTERVAL 5 YEAR),
    DATE_ADD(CURRENT_DATE(), INTERVAL 1 YEAR),
    INTERVAL 1 DAY
)) AS d
WHERE d NOT IN (
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

-- Tabla de hechos de inventario (se reconstruye completa cada vez)
TRUNCATE TABLE sales_analytics.fact_inventory;

INSERT INTO sales_analytics.fact_inventory (inventory_id, store_id, product_id, date_id, stock)
SELECT
    ROW_NUMBER() OVER (ORDER BY i.fecha, i.tienda, i.producto),
    st.store_id,
    p.product_id,
    i.fecha,
    i.stock
FROM sales_analytics.inventory_final i
LEFT JOIN sales_analytics.dim_store st ON st.store_name = i.tienda
LEFT JOIN sales_analytics.dim_product p ON p.product_name = i.producto;
