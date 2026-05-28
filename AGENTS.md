# Restaurant Data Platform — Agent Guide

## Project structure

```
batch/           # Batch pipeline (CSV → GCS → BigQuery)
streaming/       # Streaming pipeline (Flask → Pub/Sub → Dataflow/Beam → BigQuery)
dags/            # Airflow DAG (orchestrates batch)
sql/             # BigQuery DDL, MERGE statements & analytics views
docs/            # Architecture diagram
data/            # Sample CSV/JSON
tests/           # pytest tests
docker/          # Dockerfile for streaming app
.github/workflows/  # CI/CD (push to main only)
```

## Architecture

- **GCP project**: `realtime-sales-pipeline` (configurable via env vars)
- **BigQuery dataset**: `sales_analytics`
- **Bucket**: `restaurant-data-bucket-walter` (batch), `composer-bucket` / `sql-scripts-bucket` / `batch-scripts-bucket` (CD)
- **Pub/Sub**: topic `delivery-topic`, subscription `delivery-sub`

## Key quirks

- **Spanish-locale data**: columns (`fecha`, `tienda`, `producto`, `cantidad`, `total`, `pedido_id`, `estado`), comments, README are all Spanish
- **Two parallel batch ingestion styles**: `load_sales_bucket.py` / `load_inventory_bucket.py` read from GCS and truncate staging; `load_sales.py` / `load_inventory.py` read local CSVs (used by Airflow DAG)
- **Streaming dedup**: `ReadModifyWriteStateSpec` stateful DoFn — deduplica por `pedido_id` en el worker de Dataflow
- **Config parametrizable**: `batch/config.py` con fallbacks a valores por defecto via `os.getenv`

## Commands

```bash
# Install
pip install -r requirements.txt

# Run tests
pytest tests/
pytest tests/test_validations.py -v

# Run streaming app
python streaming/app.py

# Run Beam pipeline locally
python streaming/streaming_pipeline.py

# Run Dataflow (streaming en nube)
python streaming/dataflow_runner.py

# Run batch (local CSV → BigQuery)
python batch/load_sales.py
python batch/load_inventory.py

# Run batch (GCS → BigQuery)
python batch/load_sales_bucket.py
python batch/load_inventory_bucket.py

# BigQuery table setup
bq query --use_legacy_sql=false < sql/create_tables.sql

# Analytics views
bq query --use_legacy_sql=false < sql/analytics_views.sql

# GCS upload
gcloud storage cp data/ventas_pos.csv gs://restaurant-data-bucket-walter/
gcloud storage cp data/inventario.csv gs://restaurant-data-bucket-walter/

# Pub/Sub setup
gcloud pubsub topics create delivery-topic
gcloud pubsub subscriptions create delivery-sub --topic=delivery-topic
```

## Retry e idempotencia

### Batch
- **MERGE idempotente**: `incremental.sql` usa `WHEN NOT MATCHED THEN INSERT` — re-ejecutar no duplica registros
- **Truncate staging**: staging se trunca antes de cada carga, operación idempotente
- **Retry manual**: si falla `load_sales_bucket.py`, se relanza; la tabla staging se trunca primero

### Streaming
- **Deduplicación**: `StatefulDoFn` con `ReadModifyWriteStateSpec` mantiene un set de `pedido_id` vistos por worker — mensajes duplicados de Pub/Sub se descartan
- **Pub/Sub at-least-once**: la suscripción retiene mensajes hasta 7 días; si Dataflow falla y se recupera, reprocesa desde el último checkpoint (Beam gestiona checkpoints automáticos)
- **Dataflow restart**: Beam hace snapshots periódicos del estado de dedup y posición en Pub/Sub; al reiniciar retoma desde donde quedó sin perder el set de ids vistos
- **Flask**: no tiene retry interno — el cliente (Insomnia/POST) reintenta si recibe error 500

## CI/CD

- **Trigger**: push to `main` only
- **CI**: `pip install -r requirements.txt && pip install pytest` → `pytest tests/`
- **CD**: uploads `dags/`, `sql/`, `batch/` to respective GCS buckets via `gsutil cp`
- Requires secrets in GitHub:
  - `GCP_CREDENTIALS` — service account key
  - `COMPOSER_BUCKET` — DAGs bucket (ej. `gs://us-central1-restaurant-composer-xxxxx-bucket`)
  - `SQL_BUCKET` — scripts bucket (ej. `gs://sql-scripts-bucket`)
  - `BATCH_BUCKET` — batch scripts bucket (ej. `gs://batch-scripts-bucket`)

## Airflow

- DAG: `restaurant_data_platform`, scheduled `@daily`, no catchup
- Tasks: load sales staging → incremental MERGE, load inventory staging → incremental MERGE, then analytics views
- Para deploy local: copiar `dags/` al bucket del Composer: `gsutil cp dags/* gs://<composer-bucket>/dags/`

## Gotchas

- Tests import `from batch.validations` — run `pytest` from repo root (not from `tests/` directory)
- Only `validate_record` has tests
- Docker entrypoint only runs the Flask streaming app
- `load_sales_bucket.py` and `load_inventory_bucket.py` re-init `bq_client` twice
- Inventory pipeline uses `stock` column; sales uses `cantidad`/`total`
- Dataflow requiere API habilitada: `gcloud services enable dataflow.googleapis.com`
