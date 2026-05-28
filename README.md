# Restaurant Data Platform

Proyecto completo Data Engineering GCP.

## Servicios utilizados

- Cloud Storage
- BigQuery
- Pub/Sub
- Apache Beam
- Dataflow
- Composer
- GitHub Actions

## Batch

CSV -> Cloud Storage -> BigQuery

## Streaming

Flask -> Pub/Sub -> Dataflow -> BigQuery

## Ejecutar tests

pytest tests/

## Ejecutar Flask

python streaming/app.py

## Ejecutar Beam local

python streaming/streaming_pipeline.py

## Ejecutar GCP
python streaming/dataflow_runner.py



## usar el proyecto
gcloud config set project realtime-sales-pipeline
## Crear las tablas
bq query --use_legacy_sql=false < sql/create_tables.sql



## crear bucket
gcloud storage buckets create gs://restaurant-data-bucket-walter

## subir csv sales
gcloud storage cp data/ventas_pos.csv gs://restaurant-data-bucket-walter/

## subir csv inventory
gcloud storage cp data/inventario.csv gs://restaurant-data-bucket-walter/

## Ejecutar Batch sales y inventory
gcloud storage cp data/ventas_pos.csv gs://restaurant-data-bucket-walter/   ##si hay datos nuevos
python batch/load_sales_bucket.py
bq query --use_legacy_sql=false < sql/incremental.sql
#################################################################################################
gcloud storage cp data/inventario.csv gs://restaurant-data-bucket-walter/  ##si hay datos nuevos
python batch/load_inventory_bucket.py
bq query --use_legacy_sql=false < sql/incremental_inventory.sql

## Ejecutar Streaming
## Crear topic Pub/Sub
gcloud pubsub topics create delivery-topic
## Crear subscription
gcloud pubsub subscriptions create delivery-sub --topic=delivery-topic

## Verificar topic
gcloud pubsub topics list

## Verificar subscription
gcloud pubsub subscriptions list


## activar dataflow 
gcloud services enable dataflow.googleapis.com --project=realtime-sales-pipeline


## ver jobs corriendo
C:\Users\Walter\AppData\Local\Google\Cloud SDK>gcloud dataflow jobs list --project=realtime-sales-pipeline  --region=us-central1  --filter="STATE=RUNNING"
JOB_ID: 2026-05-28_10_22_06-11049737308960551491
NAME: delivery-streaming-pipeline-20260528-122148
TYPE: Streaming
CREATION_TIME: 2026-05-28 17:22:06
STATE: Running
REGION: us-central1

JOB_ID: 2026-05-28_10_16_33-9711468695474425057
NAME: delivery-streaming-pipeline-20260528-121615
TYPE: Streaming
CREATION_TIME: 2026-05-28 17:16:33
STATE: Running
REGION: us-central1

C:\Users\Walter\AppData\Local\Google\Cloud SDK>gcloud pubsub subscriptions describe delivery-sub --project=realtime-sales-pipeline --format="value(pushConfig,ackDeadlineSeconds)"
        10

## cancela job
gcloud dataflow jobs cancel --project=realtime-sales-pipeline --region=us-central1   2026-05-28_10_16_33-9711468695474425057


## consulta bigquery
bq query --use_legacy_sql=false "SELECT * FROM sales_analytics.delivery_realtime ORDER BY created_at DESC LIMIT 10"