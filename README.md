# Restaurant Data Platform

Proyecto completo Data Engineering GCP — cadena de restaurantes.

## Architecture

Ver diagrama completo en [`docs/architecture.md`](docs/architecture.md).

## Servicios utilizados

- Cloud Storage, BigQuery, Pub/Sub, Apache Beam, Dataflow, Cloud Composer, GitHub Actions

## Batch

CSV → Cloud Storage → BigQuery → Star Schema (dim + fact) → Vistas analíticas

## Streaming

Flask → Pub/Sub → Dataflow (Beam stateful dedup) → BigQuery

## Modelo de datos

Star schema documentado en [`docs/star_schema.md`](docs/star_schema.md).

## Comandos rápidos

```bash
# Instalar dependencias
pip install -r requirements.txt

# Tests
python -m pytest tests/

# Streaming app (local)
python streaming/app.py

# Beam local
python streaming/streaming_pipeline.py

# Dataflow (nube)
python streaming/dataflow_runner.py

# Batch (local)
python batch/load_sales.py
python batch/load_inventory.py

# Batch (GCS → BigQuery)
python batch/load_sales_bucket.py
python batch/load_inventory_bucket.py

# Crear tablas en BigQuery
bq query --use_legacy_sql=false < sql/create_tables.sql
bq query --use_legacy_sql=false < sql/warehouse_model.sql

# Vistas analíticas
bq query --use_legacy_sql=false < sql/analytics_views.sql

# Poblar star schema
bq query --use_legacy_sql=false < sql/populate_star_schema.sql

# Subir CSV a GCS
gcloud storage cp data/ventas_pos.csv gs://restaurant-data-bucket-walter/
gcloud storage cp data/inventario.csv gs://restaurant-data-bucket-walter/
```

## CI/CD

Push a `main` → tests → deploy automático a Composer + buckets GCS.
Requiere `GCP_CREDENTIALS`, `COMPOSER_BUCKET`, `SQL_BUCKET`, `BATCH_BUCKET` en GitHub Secrets.

## Consultas
## Vistas analíticas
-- Ventas diarias por tienda
SELECT * FROM sales_analytics.vw_sales_daily ORDER BY fecha DESC LIMIT 20;
-- Top productos más vendidos
SELECT * FROM sales_analytics.vw_top_products LIMIT 20;
-- Ticket promedio por tienda
SELECT * FROM sales_analytics.vw_ticket_promedio;
-- Resumen delivery
SELECT * FROM sales_analytics.vw_delivery_summary ORDER BY fecha DESC LIMIT 20;
-- Stock actual por tienda y producto
SELECT * FROM sales_analytics.vw_inventory_current ORDER BY stock;
-- Consolidado ventas + delivery
SELECT * FROM sales_analytics.vw_consolidado ORDER BY fecha DESC LIMIT 20;
## Star schema (Gold)
-- Tabla de hechos ventas + dimensiones (denormalizado)
SELECT * FROM sales_analytics.fact_sales ORDER BY sale_id DESC LIMIT 20;
-- Tabla de hechos inventario + dimensiones
SELECT * FROM sales_analytics.fact_inventory ORDER BY inventory_id DESC LIMIT 20;
-- Dimensiones
SELECT * FROM sales_analytics.dim_store;
SELECT * FROM sales_analytics.dim_product;
SELECT * FROM sales_analytics.dim_date ORDER BY date_id DESC;

## Base tables (Silver)

SELECT * FROM sales_analytics.sales_final ORDER BY fecha DESC LIMIT 20;
SELECT * FROM sales_analytics.inventory_final ORDER BY fecha DESC LIMIT 20;
SELECT * FROM sales_analytics.delivery_realtime ORDER BY created_at DESC LIMIT 20;

## Staging (Bronze)

SELECT * FROM sales_analytics.sales_staging LIMIT 20;
SELECT * FROM sales_analytics.inventory_staging LIMIT 20;