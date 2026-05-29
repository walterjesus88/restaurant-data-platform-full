-- ============================================
-- ANALYTICS VIEWS — Restaurant Data Platform
-- Basadas en el star schema (dim + fact)
-- Consumidas por Power BI / reporting
-- ============================================

-- Venta total por tienda y día
CREATE OR REPLACE VIEW sales_analytics.vw_sales_daily AS
SELECT
    f.date_id AS fecha,
    st.store_name AS tienda,
    SUM(f.total_amount) AS venta_total,
    SUM(f.quantity) AS cantidad_vendida,
    COUNT(*) AS transacciones,
    ROUND(SUM(f.total_amount) / COUNT(*), 2) AS ticket_promedio
FROM sales_analytics.fact_sales f
LEFT JOIN sales_analytics.dim_store st 
ON f.store_id = st.store_id
GROUP BY f.date_id, st.store_name
ORDER BY fecha DESC, venta_total DESC;


-- Productos más vendidos
CREATE OR REPLACE VIEW sales_analytics.vw_top_products AS
SELECT
    p.product_name AS producto,
    SUM(f.quantity) AS total_vendido,
    SUM(f.total_amount) AS ingreso_total,
    ROUND(AVG(f.total_amount / SAFE_DIVIDE(f.quantity, 1.0)), 2) AS precio_promedio
FROM sales_analytics.fact_sales f
LEFT JOIN sales_analytics.dim_product p ON f.product_id = p.product_id
GROUP BY p.product_name
ORDER BY total_vendido DESC;


-- Ticket promedio por tienda
CREATE OR REPLACE VIEW sales_analytics.vw_ticket_promedio AS
SELECT
    st.store_name AS tienda,
    ROUND(SUM(f.total_amount) / COUNT(*), 2) AS ticket_promedio,
    SUM(f.total_amount) AS venta_total,
    COUNT(*) AS transacciones
FROM sales_analytics.fact_sales f
LEFT JOIN sales_analytics.dim_store st ON f.store_id = st.store_id
GROUP BY st.store_name
ORDER BY ticket_promedio DESC;


-- Delivery summary (no cambia, no pertenece al star schema)
CREATE OR REPLACE VIEW sales_analytics.vw_delivery_summary AS
SELECT
    DATE(fecha_evento) AS fecha,
    estado,
    COUNT(*) AS pedidos,
    SUM(monto) AS monto_total,
    ROUND(AVG(monto), 2) AS monto_promedio
FROM sales_analytics.delivery_realtime
GROUP BY DATE(fecha_evento), estado
ORDER BY fecha DESC, estado;


-- Último inventario disponible por tienda y producto
CREATE OR REPLACE VIEW sales_analytics.vw_inventory_current AS
SELECT
    st.store_name AS tienda,
    p.product_name AS producto,
    fi.stock,
    fi.date_id AS fecha
FROM sales_analytics.fact_inventory fi
LEFT JOIN sales_analytics.dim_store st 
ON fi.store_id = st.store_id
LEFT JOIN sales_analytics.dim_product p
ON fi.product_id = p.product_id
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY fi.store_id, fi.product_id
    ORDER BY fi.date_id DESC
) = 1;


-- Vista consolidada ventas + delivery
CREATE OR REPLACE VIEW sales_analytics.vw_consolidado AS
SELECT
    COALESCE(s.fecha, d.fecha) AS fecha,
    s.tienda,
    s.venta_total,
    s.cantidad_vendida,
    s.transacciones,
    s.ticket_promedio,
    d.pedidos AS delivery_pedidos,
    d.monto_total AS delivery_monto
FROM sales_analytics.vw_sales_daily s
FULL OUTER JOIN sales_analytics.vw_delivery_summary d
    ON s.fecha = d.fecha
ORDER BY fecha DESC;
