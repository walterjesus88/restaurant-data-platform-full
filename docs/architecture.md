# Arquitectura — Restaurant Data Platform

```mermaid
flowchart TB
    subgraph Fuentes
        CSV1[ventas_pos.csv<br/>POS cada 5 min]
        CSV2[inventario.csv<br/>ERP diario]
        API[Flask /delivery<br/>App Delivery]
    end

    subgraph Ingesta
        GCS[(Cloud Storage<br/>restaurant-data-bucket-walter)]
        PUBSUB[(Pub/Sub<br/>delivery-topic)]
    end

    subgraph Procesamiento
        BATCH[Batch Scripts<br/>load_sales_bucket.py<br/>load_inventory_bucket.py]
        DAG[Airflow Composer<br/>restaurant_data_platform]
        DATAFLOW[Dataflow<br/>dataflow_runner.py<br/>Beam Streaming]
    end

    subgraph Almacenamiento
        BQ_STAGING[(BigQuery<br/>sales_staging<br/>inventory_staging)]
        BQ_FINAL[(BigQuery<br/>sales_final<br/>inventory_final<br/>delivery_realtime)]
        BQ_ANALYTICS[(BigQuery<br/>Vistas analíticas<br/>vw_sales_daily<br/>vw_top_products<br/>vw_ticket_promedio)]
    end

    subgraph Consumo
        POWER_BI[Power BI]
    end

    CSV1 --> GCS
    CSV2 --> GCS
    GCS --> BATCH
    BATCH --> BQ_STAGING
    BQ_STAGING --> DAG
    DAG --> BQ_FINAL
    BQ_FINAL --> BQ_ANALYTICS

    API --> PUBSUB
    PUBSUB --> DATAFLOW
    DATAFLOW --> BQ_FINAL

    BQ_ANALYTICS --> POWER_BI
```

## Flujo batch

1. CSV se suben a Cloud Storage (`data/` → `gs://restaurant-data-bucket-walter/`)
2. Scripts (`load_sales_bucket.py`, `load_inventory_bucket.py`) leen del bucket, validan, transforman y cargan a staging
3. Airflow DAG orquesta: load staging → MERGE a finales → ejecuta vistas analíticas
4. Vistas (`vw_sales_daily`, `vw_top_products`, etc.) disponibles para Power BI

## Flujo streaming

1. App Flask (`app.py`) recibe POST en `/delivery` y publica en Pub/Sub
2. Dataflow (`dataflow_runner.py`) consume desde la suscripción, deduplica por `pedido_id`, valida, y escribe a `delivery_realtime`
3. Datos disponibles en vistas analíticas

## Tecnologías

| Servicio | Uso |
|---|---|
| Cloud Storage | Almacenamiento CSV fuente |
| BigQuery | Data warehouse analítico |
| Pub/Sub | Mensajería streaming |
| Dataflow | Procesamiento streaming Beam |
| Cloud Composer | Orquestación batch |
| GitHub Actions | CI/CD |
| Docker | Contenedor Flask |
