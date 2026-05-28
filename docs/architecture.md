# Arquitectura — Restaurant Data Platform

```
 ┌─────────────────────────────────────────────────────────────┐
 │                        FUENTES                              │
 │  ┌─────────────────┐  ┌──────────────┐  ┌───────────────┐  │
 │  │ ventas_pos.csv  │  │inventario.csv│  │Insomnia/POST  │  │
 │  │ (POS cada 5min) │  │ (ERP diario) │  │ /delivery     │  │
 │  └────────┬────────┘  └──────┬───────┘  └───────┬───────┘  │
 └───────────┼──────────────────┼──────────────────┼──────────┘
             │                  │                  │
             ▼                  ▼                  ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                      INGESTA                                 │
 │  ┌────────────────────────────────────┐  ┌───────────────┐  │
 │  │  Cloud Storage                     │  │    Pub/Sub    │  │
 │  │  gs://restaurant-data-bucket-...   │  │ delivery-topic│  │
 │  └────────┬───────────────────────────┘  └───────┬───────┘  │
 └───────────┼──────────────────────────────────────┼──────────┘
             │                                      │
             ▼                                      ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                    PROCESAMIENTO                             │
 │  ┌──────────────────┐  ┌──────────────┐  ┌──────────────┐  │
 │  │ Batch Scripts    │  │ Airflow      │  │  Dataflow    │  │
 │  │ load_sales/inv.. │─▶│ Composer     │  │  streaming   │  │
 │  │ .py              │  │ DAG diario   │  │  pipeline    │  │
 │  └────────┬─────────┘  └──────┬───────┘  └──────┬───────┘  │
 └───────────┼───────────────────┼──────────────────┼──────────┘
             │                   │                  │
             ▼                   ▼                  ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                    ALMACENAMIENTO                            │
 │  ┌──────────────────────────────────────────────────────┐   │
 │  │  BigQuery - sales_analytics                          │   │
 │  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │   │
 │  │  │ sales_staging│  │ sales_final  │  │ delivery   │ │   │
 │  │  │ inventory_.. │  │ inventory_.. │  │ _realtime  │ │   │
 │  │  └──────────────┘  └──────┬───────┘  └────────────┘ │   │
 │  │                           │                          │   │
 │  │                     ┌─────▼──────┐                   │   │
 │  │                     │ fact_sales │                   │   │
 │  │                     │ dim_store  │                   │   │
 │  │                     │ dim_product│                   │   │
 │  │                     │ dim_date   │                   │   │
 │  │                     └─────┬──────┘                   │   │
 │  │                           ▼                          │   │
 │  │  ┌────────────────────────────────────────────────┐  │   │
 │  │  │ Vistas: vw_sales_daily, vw_top_products, ...   │  │   │
 │  │  └──────────────────────┬─────────────────────────┘  │   │
 │  └─────────────────────────┼────────────────────────────┘   │
 └────────────────────────────┼────────────────────────────────┘
                              ▼
              ┌──────────────────────────────┐
              │          CONSUMO             │
              │         Power BI             │
              └──────────────────────────────┘
```

> Si ves esto en GitHub, abajo está el diagrama interactivo en Mermaid.

```mermaid
flowchart TB
    subgraph Fuentes
        CSV1[ventas_pos.csv]
        CSV2[inventario.csv]
        API[Flask /delivery]
    end

    subgraph Ingesta
        GCS[(Cloud Storage)]
        PUBSUB[(Pub/Sub delivery-topic)]
    end

    subgraph Procesamiento
        BATCH[Batch Scripts]
        DAG[Airflow Composer]
        DATAFLOW[Dataflow streaming]
    end

    subgraph Almacenamiento
        BQ_STAGING[(sales_staging\ninventory_staging)]
        BQ_FINAL[(sales_final\ninventory_final\ndelivery_realtime)]
        BQ_STAR[(dim_store\ndim_product\ndim_date\nfact_sales)]
        BQ_VIEWS[(Vistas analíticas)]
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
    BQ_FINAL --> BQ_STAR
    BQ_STAR --> BQ_VIEWS

    API --> PUBSUB
    PUBSUB --> DATAFLOW
    DATAFLOW --> BQ_FINAL

    BQ_VIEWS --> POWER_BI
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
