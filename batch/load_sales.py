import logging
import pandas as pd
from google.cloud import bigquery

from config import PROJECT_ID, DATASET, SALES_FILE
from validations import validate_record
from transformations import transform_data

logging.basicConfig(level=logging.INFO)

client = bigquery.Client()

def main():

    logging.info("Reading CSV file")

    df = pd.read_csv(f"data/{SALES_FILE}")

    df = transform_data(df)

    valid_records = []

    for _, row in df.iterrows():

        record = row.to_dict()

        if validate_record(record):
            valid_records.append(record)

    final_df = pd.DataFrame(valid_records)

    table_id = f"{PROJECT_ID}.{DATASET}.sales_staging"

    job = client.load_table_from_dataframe(
        final_df,
        table_id
    )

    job.result()

    logging.info("Batch load completed")


if __name__ == "__main__":
    main()