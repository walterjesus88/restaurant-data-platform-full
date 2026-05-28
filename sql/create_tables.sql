CREATE SCHEMA IF NOT EXISTS sales_analytics;

CREATE TABLE IF NOT EXISTS sales_analytics.sales_staging (
    fecha DATE,
    tienda STRING,
    producto STRING,
    cantidad INT64,
    total FLOAT64
);

CREATE TABLE IF NOT EXISTS sales_analytics.sales_final (
    fecha DATE,
    tienda STRING,
    producto STRING,
    cantidad INT64,
    total FLOAT64
);

CREATE TABLE IF NOT EXISTS sales_analytics.delivery_realtime (
    pedido_id INT64,
    estado STRING,
    fecha_evento TIMESTAMP,
    monto FLOAT64,
    created_at TIMESTAMP
);


CREATE TABLE IF NOT EXISTS sales_analytics.inventory_staging (
    fecha DATE,
    tienda STRING,
    producto STRING,
    stock INT64
);

CREATE TABLE IF NOT EXISTS sales_analytics.inventory_final (
    fecha DATE,
    tienda STRING,
    producto STRING,
    stock INT64
);

