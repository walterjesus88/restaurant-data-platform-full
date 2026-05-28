import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import json
import logging


logging.basicConfig(
    level=logging.INFO
)


class ValidateEvent(beam.DoFn):

    def process(self, element):

        try:

            record = json.loads(
                element.decode("utf-8")
            )

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


options = PipelineOptions(
    streaming=True
)

with beam.Pipeline(options=options) as pipeline:

    (
        pipeline

        | "Read From PubSub" >> beam.io.ReadFromPubSub(
            subscription=(
                "projects/realtime-sales-pipeline/"
                "subscriptions/delivery-sub"
            )
        )

        | "Validate Event" >> beam.ParDo(
            ValidateEvent()
        )

        | "Log Records" >> beam.ParDo(
            LogInsertedRecord()
        )

        | "Write To BigQuery" >> beam.io.WriteToBigQuery(

            table=(
                "realtime-sales-pipeline:"
                "sales_analytics.delivery_realtime"
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