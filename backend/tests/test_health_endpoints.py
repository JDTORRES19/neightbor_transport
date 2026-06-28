from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_api_health_success_envelope() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["status"] == "ok"
    assert payload["data"]["service"] == "web"
    assert response.headers.get("X-Request-ID")


def test_api_health_conflict_error_envelope() -> None:
    response = client.get("/api/v1/health/conflict")

    assert response.status_code == 409
    payload = response.json()
    assert payload["ok"] is False
    assert payload["error"]["code"] == "ERR_DEMO_CONFLICT"
    assert payload["error"]["request_id"]


def test_docs_and_redoc_available_in_dev() -> None:
    docs_response = client.get("/docs")
    redoc_response = client.get("/redoc")

    assert docs_response.status_code == 200
    assert redoc_response.status_code == 200
