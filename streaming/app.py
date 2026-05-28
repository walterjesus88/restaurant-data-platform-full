from flask import Flask, request, jsonify
from google.cloud import pubsub_v1
from datetime import datetime, UTC
import json

app = Flask(__name__)

PROJECT_ID = "realtime-sales-pipeline"
TOPIC_ID = "delivery-topic"

publisher = pubsub_v1.PublisherClient()

topic_path = publisher.topic_path(
    PROJECT_ID,
    TOPIC_ID
)


@app.route("/delivery", methods=["POST"])
def publish_event():

    try:
        data = request.get_json()

        required_fields = [
            "pedido_id",
            "estado",
            "fecha_evento",
            "monto"
        ]

        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error",
                    "message": f"Missing field: {field}"
                }), 400

        data["created_at"] = datetime.now(
            UTC
        ).isoformat()

        message_json = json.dumps(data)

        future = publisher.publish(
            topic_path,
            message_json.encode("utf-8")
        )

        message_id = future.result()

        return jsonify({

            "status": "success",
            "message":
                "Delivery event published successfully",
            "message_id": message_id,
            "event": data
        }), 200

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":

    app.run(debug=True)
