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

## Crear el Composer
gcloud composer environments create restaurant-composer --project=realtime-sales-pipeline   --location=us-central1 --environment-size=small --python-version=3.11 --scheduler-count=1 --worker-count=1

## obtiene el bucket del composer
gcloud composer environments describe restaurant-composer --project=realtime-sales-pipeline --location=us-central1 --format="value(config.dagGcsPrefix)"
Y guardarlo como COMPOSER_BUCKET en GitHub Secrets (Settings > Secrets and variables > Actions), junto con GCP_CREDENTIALS.

result: gs://us-central1-restaurant-comp-74c72f4f-bucket/dags

## subes el dag
gsutil cp dags/restaurant_pipeline.py gs://us-central1-restaurant-comp-74c72f4f-bucket/dags  

gcloud storage cp dags/restaurant_pipeline.py gs://us-central1-restaurant-comp-74c72f4f-bucket/dags/restaurant_pipeline.py

gcloud storage cp sql/analytics_views.sql gs://us-central1-restaurant-comp-74c72f4f-bucket/dags/sql/analytics_views.sql

## truncate
bq query --use_legacy_sql=false "
TRUNCATE TABLE sales_analytics.sales_staging;
TRUNCATE TABLE sales_analytics.sales_final;
TRUNCATE TABLE sales_analytics.inventory_staging;
TRUNCATE TABLE sales_analytics.inventory_final;
TRUNCATE TABLE sales_analytics.delivery_realtime;
TRUNCATE TABLE sales_analytics.fact_sales;
DELETE FROM sales_analytics.dim_store WHERE TRUE;
DELETE FROM sales_analytics.dim_product WHERE TRUE;
DELETE FROM sales_analytics.dim_date WHERE TRUE;
"

## suir dag 
gcloud storage cp dags/restaurant_pipeline.py gs://us-central1-restaurant-comp-74c72f4f-bucket/dags/
gcloud storage cp sql/populate_star_schema.sql gs://us-central1-restaurant-comp-74c72f4f-bucket/dags/sql/
gcloud storage cp sql/analytics_views.sql gs://us-central1-restaurant-comp-74c72f4f-bucket/dags/sql/


## Para el CI/CD
## Paso 1 — Crear una key del service account
gcloud iam service-accounts keys create ~\gcp-key.json --iam-account=275517521418-compute@developer.gserviceaccount.com --project=realtime-sales-pipeline
## Paso 2 — Inicializar git y subir a GitHub
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git push -u origin main
(Pon tu usuario y nombre del repo)
Paso 3 — Agregar Secrets en GitHub
1. Ve a https://github.com/TU_USUARIO/TU_REPO/settings/secrets/actions
2. Clic en "New repository secret"
3. Agrega estos secrets:


## disparar el DAG:
gcloud composer environments run restaurant-composer \
  --project=realtime-sales-pipeline \
  --location=us-central1 \
  dags trigger -- restaurant_data_platform
O desde la UI de Airflow: ▶️ Trigger DAG. Después verifica:
bq query --use_legacy_sql=false "SELECT * FROM sales_analytics.vw_sales_daily LIMIT 10"


## Arquitectura 
Arquitectura Medallón (Bronze → Silver → Gold) sobre GCP:
Bronze: Cloud Storage (CSV raw) + Pub/Sub (eventos streaming)
Silver: BigQuery staging tables (datos validados y transformados)
Gold: BigQuery star schema (dim + fact) + vistas analíticas → Power BI
Combinada con Arquitectura Lambda (batch + streaming en paralelo):
Batch layer: CSV → Airflow → BigQuery (procesamiento diario)
Speed layer: Flask → Pub/Sub → Dataflow → BigQuery (tiempo real)
Serving layer: Star schema en BigQuery consumido por Power BI