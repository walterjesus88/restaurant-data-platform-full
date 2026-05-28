import os

PROJECT_ID = os.getenv("PROJECT_ID", "realtime-sales-pipeline")
DATASET = os.getenv("DATASET", "sales_analytics")
REGION = os.getenv("REGION", "us-central1")

BUCKET_NAME = os.getenv("BUCKET_NAME", "restaurant-data-bucket-walter")
SALES_FILE = os.getenv("SALES_FILE", "ventas_pos.csv")
INVENTORY_FILE = os.getenv("INVENTORY_FILE", "inventario.csv")

TABLE_SALES_STAGING = os.getenv(
    "TABLE_SALES_STAGING",
    f"{PROJECT_ID}.{DATASET}.sales_staging"
)
TABLE_SALES_FINAL = os.getenv(
    "TABLE_SALES_FINAL",
    f"{PROJECT_ID}.{DATASET}.sales_final"
)
TABLE_INVENTORY_STAGING = os.getenv(
    "TABLE_INVENTORY_STAGING",
    f"{PROJECT_ID}.{DATASET}.inventory_staging"
)
TABLE_INVENTORY_FINAL = os.getenv(
    "TABLE_INVENTORY_FINAL",
    f"{PROJECT_ID}.{DATASET}.inventory_final"
)
TABLE_DELIVERY = os.getenv(
    "TABLE_DELIVERY",
    f"{PROJECT_ID}:{DATASET}.delivery_realtime"
)

TOPIC_ID = os.getenv("TOPIC_ID", "delivery-topic")
SUBSCRIPTION_ID = os.getenv("SUBSCRIPTION_ID", "delivery-sub")
