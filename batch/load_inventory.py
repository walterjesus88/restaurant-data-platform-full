import logging
import pandas as pd
from google.cloud import bigquery

from config import PROJECT_ID, DATASET, INVENTORY_FILE, TABLE_INVENTORY_STAGING

logging.basicConfig(level=logging.INFO)

client = bigquery.Client()

client.query(
    f"TRUNCATE TABLE {DATASET}.inventory_staging"
).result()

def main():

    logging.info("Reading inventory CSV")

    df = pd.read_csv(f"data/{INVENTORY_FILE}")

    df.columns = [c.lower() for c in df.columns]

    df = df.drop_duplicates()

    df["fecha"] = pd.to_datetime(df["fecha"])

    df = df[df["stock"] >= 0]

    job = client.load_table_from_dataframe(
        df,
        TABLE_INVENTORY_STAGING
    )

    job.result()

    logging.info("Inventory loaded successfully")


if __name__ == "__main__":
    main()
