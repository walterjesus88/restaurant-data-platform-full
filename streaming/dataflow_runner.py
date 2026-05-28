import os
import apache_beam as beam
from apache_beam.coders import coders
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.transforms.userstate import ReadModifyWriteStateSpec
from datetime import datetime
import json
import logging


logging.basicConfig(
    level=logging.INFO
)

PROJECT = os.getenv("PROJECT_ID", "realtime-sales-pipeline")
BUCKET = os.getenv("BUCKET_NAME", "restaurant-data-bucket-walter")
REGION = os.getenv("REGION", "us-central1")
TOPIC = os.getenv("TOPIC_ID", "delivery-topic")
SUBSCRIPTION = os.getenv("SUBSCRIPTION_ID", "delivery-sub")
DATASET = os.getenv("DATASET", "sales_analytics")


class DeduplicatePedidos(beam.DoFn):
    """Deduplica eventos por pedido_id usando estado Beam.

    La entrada debe ser KV(pedido_id, evento_dict).
    Emite el evento si el pedido_id no se ha visto antes.
    """

    SEEN_IDS = ReadModifyWriteStateSpec(
        "seen_ids",
        coders.PickleCoder()
    )

    def process(self, element, seen_ids=beam.DoFn.StateParam(SEEN_IDS)):
        pedido_id, event = element
        if pedido_id is not None:
            seen = seen_ids.read()
            if seen is None:
                seen = set()
            if pedido_id not in seen:
                seen.add(pedido_id)
                seen_ids.write(seen)
                yield event


class ValidateEvent(beam.DoFn):

    def process(self, element):

        try:

            record = element

            required_fields = [
                "pedido_id",
                "estado",
                "fecha_evento",
                "monto"
            ]

            for field in required_fields:

                if field not in record:

                    logging.error(
                        f"Missing field: {field}"
                    )

                    return

            if float(record["monto"]) < 0:

                logging.error(
                    "Negative amount detected"
                )

                return

            logging.info(
                f"Valid event: {record}"
            )

            yield record

        except Exception as e:

            logging.error(
                f"Error processing event: {e}"
            )


class LogInsertedRecord(beam.DoFn):

    def process(self, element):

        logging.info(
            f"Inserted into BigQuery: {element}"
        )

        yield element


def run():

    options = PipelineOptions(
        runner="DataflowRunner",
        project=PROJECT,
        region=REGION,
        staging_location=f"gs://{BUCKET}/dataflow/staging",
        temp_location=f"gs://{BUCKET}/dataflow/temp",
        job_name=(
            f"delivery-streaming-pipeline-"
            f"{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        ),
        streaming=True,
    )

    with beam.Pipeline(options=options) as pipeline:

        (
            pipeline

            | "Read From PubSub" >> beam.io.ReadFromPubSub(
                subscription=(
                    f"projects/{PROJECT}/"
                    f"subscriptions/{SUBSCRIPTION}"
                )
            )

            | "Parse JSON" >> beam.Map(
                lambda x: json.loads(
                    x.decode("utf-8")
                )
            )

            | "Key By pedido_id" >> beam.Map(
                lambda x: (x.get("pedido_id"), x)
            )

            | "Deduplicate" >> beam.ParDo(
                DeduplicatePedidos()
            )

            | "Validate Event" >> beam.ParDo(
                ValidateEvent()
            )

            | "Log Records" >> beam.ParDo(
                LogInsertedRecord()
            )

            | "Write To BigQuery" >> beam.io.WriteToBigQuery(

                table=(
                    f"{PROJECT}:"
                    f"{DATASET}.delivery_realtime"
                ),

                schema=(
                    "pedido_id:INTEGER,"
                    "estado:STRING,"
                    "fecha_evento:TIMESTAMP,"
                    "monto:FLOAT,"
                    "created_at:TIMESTAMP"
                ),

                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,

                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED
            )
        )


if __name__ == "__main__":
    run()
