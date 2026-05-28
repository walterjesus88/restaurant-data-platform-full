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
