import pytest
import json
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    with patch("streaming.app.publisher") as mock_publisher:
        mock_future = MagicMock()
        mock_future.result.return_value = "mock-message-id"
        mock_publisher.publish.return_value = mock_future

        from streaming.app import app
        app.config["TESTING"] = True
        with app.test_client() as c:
            yield c


def test_valid_delivery(client):
    payload = {
        "pedido_id": "del-999",
        "estado": "entregado",
        "fecha_evento": "2026-05-28T15:30:00",
        "monto": 150.0
    }
    resp = client.post(
        "/delivery",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "success"
    assert data["message_id"] == "mock-message-id"


def test_missing_pedido_id(client):
    payload = {
        "estado": "entregado",
        "fecha_evento": "2026-05-28T15:30:00",
        "monto": 150.0
    }
    resp = client.post(
        "/delivery",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["status"] == "error"
    assert "pedido_id" in data["message"]


def test_missing_estado(client):
    payload = {
        "pedido_id": "del-999",
        "fecha_evento": "2026-05-28T15:30:00",
        "monto": 150.0
    }
    resp = client.post(
        "/delivery",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["status"] == "error"
    assert "estado" in data["message"]


def test_invalid_json_body(client):
    resp = client.post(
        "/delivery",
        data="not json",
        content_type="application/json"
    )
    assert resp.status_code == 500


def test_missing_all_fields(client):
    payload = {}
    resp = client.post(
        "/delivery",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert resp.status_code == 400
