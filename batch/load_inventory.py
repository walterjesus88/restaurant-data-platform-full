import logging
import pandas as pd
from google.cloud import bigquery

from config import PROJECT_ID, DATASET, INVENTORY_FILE, TABLE_INVENTORY_STAGING
from transformations import validate_dataframe

logging.basicConfig(level=logging.INFO)

client = bigquery.Client()

def main():

    client.query(
        f"TRUNCATE TABLE {DATASET}.inventory_staging"
    ).result()

    logging.info("Reading inventory CSV")

    df = pd.read_csv(f"data/{INVENTORY_FILE}")

    df = validate_dataframe(df, table_type="inventory")

    job = client.load_table_from_dataframe(
        df,
        TABLE_INVENTORY_STAGING
    )

    job.result()

    logging.info("Inventory loaded successfully")


if __name__ == "__main__":
    main()
