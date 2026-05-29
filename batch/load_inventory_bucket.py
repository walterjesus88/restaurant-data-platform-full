from google.cloud import storage
from google.cloud import bigquery
import pandas as pd
from io import BytesIO

from config import PROJECT_ID, DATASET, BUCKET_NAME, INVENTORY_FILE, TABLE_INVENTORY_STAGING

FILE_NAME = INVENTORY_FILE

TABLE_ID = TABLE_INVENTORY_STAGING


# BIGQUERY

bq_client = bigquery.Client()

# TRUNCATE STAGING

truncate_query = f"""
TRUNCATE TABLE
`{PROJECT_ID}.{DATASET}.inventory_staging`
"""

bq_client.query(
    truncate_query
).result()

print(
    "inventory_staging truncated"
)



# CLOUD STORAGE

storage_client = storage.Client()

bucket = storage_client.bucket(
    BUCKET_NAME
)

blob = bucket.blob(
    FILE_NAME
)

data = blob.download_as_bytes()

# PANDAS

df = pd.read_csv(
    BytesIO(data)
)

df["fecha"] = pd.to_datetime( df["fecha"] ).dt.date

# VALIDACIONES

df = df.dropna()

df = df[df["stock"] >= 0]

df = df.drop_duplicates()

print(df.head())

job = bq_client.load_table_from_dataframe(
    df,
    TABLE_ID
)

job.result()

print(
    "Inventory loaded successfully"
)
