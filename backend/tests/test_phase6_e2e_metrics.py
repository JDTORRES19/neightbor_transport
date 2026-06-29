from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.main import app
from app.core.constants import (
    DEFAULT_REQUESTER_USER_ID,
    DEFAULT_USER_ID,
    TRIP_STATUS_FINALIZED,
)
from app.infrastructure.database import SessionLocal, init_db
from app.infrastructure.models import AuditEvent, Notification, Profile, SchedulerJobRun, Trip, TripRequest, Vehicle
from app.services.scheduler_service import run_auto_finalize_trips_job

client = TestClient(app)
SEEDED_VEHICLE_ID = 1


@pytest.fixture(autouse=True)
def reset_db_state() -> None:
    global SEEDED_VEHICLE_ID

    init_db()
    with SessionLocal() as db:
        db.execute(delete(AuditEvent))
        db.execute(delete(Notification))
        db.execute(delete(SchedulerJobRun))
        db.execute(delete(TripRequest))
        db.execute(delete(Trip))
        db.execute(delete(Vehicle))
        db.execute(delete(Profile))

        db.add(
            Profile(
                user_id=DEFAULT_USER_ID,
                display_name="Conductor Demo",
                photo_url=None,
                country_code="CO",
                phone_prefix="+57",
                phone_number="3001234567",
                phone_e164="+573001234567",
            )
        )
        db.add(
            Profile(
                user_id=DEFAULT_REQUESTER_USER_ID,
                display_name="Solicitante Demo",
                photo_url=None,
                country_code="CO",
                phone_prefix="+57",
                phone_number="3007654321",
                phone_e164="+573007654321",
            )
        )
        db.add(
            Vehicle(
                user_id=DEFAULT_USER_ID,
                brand="Mazda",
                reference="3 Touring",
                color="Rojo",
                plate="ABC123",
                is_active=True,
            )
        )
        db.commit()

        seeded_vehicle = db.scalar(
            select(Vehicle)
            .where(Vehicle.user_id == DEFAULT_USER_ID)
            .order_by(Vehicle.id.asc())
            .limit(1)
        )
        assert seeded_vehicle is not None
        SEEDED_VEHICLE_ID = seeded_vehicle.id


def _create_trip(*, departure_at: datetime | None = None, total_seats: int = 2) -> int:
    when = departure_at or datetime.now(timezone.utc)
    response = client.post(
        "/api/v1/trips",
        json={
            "direction": "to_cali",
            "origin_label": "Unidad La Arboleda",
            "departure_at": when.isoformat().replace("+00:00", "Z"),
            "total_seats": total_seats,
            "vehicle_id": SEEDED_VEHICLE_ID,
        },
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _create_request(trip_id: int, seats: int = 1) -> int:
    response = client.post(
        f"/api/v1/trips/{trip_id}/requests",
        json={
            "pickup_label": "Porteria principal",
            "requested_seats": seats,
            "comment": "Viajo hoy",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def test_end_to_end_flow_with_metrics_overview() -> None:
    trip_id = _create_trip(total_seats=2)
    request_id = _create_request(trip_id, seats=1)

    accepted = client.post(f"/api/v1/requests/{request_id}/accept")
    assert accepted.status_code == 200

    finalized = client.post(f"/api/v1/trips/{trip_id}/finalize")
    assert finalized.status_code == 200
    assert finalized.json()["data"]["status"] == TRIP_STATUS_FINALIZED

    mine_requests = client.get("/api/v1/requests/mine")
    assert mine_requests.status_code == 200
    assert mine_requests.json()["data"]["items"][0]["status"] == "finalizada"

    notifications = client.get("/api/v1/notifications?unread_only=true")
    assert notifications.status_code == 200
    assert notifications.json()["data"]["unread_count"] >= 1

    run_auto_finalize_trips_job(now_utc=datetime.now(timezone.utc) + timedelta(minutes=30))

    metrics = client.get("/api/v1/metrics/overview?window_seconds=60&limit=5")
    assert metrics.status_code == 200

    metrics_data = metrics.json()["data"]
    assert metrics_data["trips_by_status"].get("finalizado", 0) >= 1
    assert metrics_data["requests_by_status"].get("finalizada", 0) >= 1
    assert metrics_data["unread_notifications"] >= 1
    assert metrics_data["total_audit_events"] >= 1
    assert metrics_data["latency_window_seconds"] == 60
    assert isinstance(metrics_data["endpoint_latency_ms"], list)
    assert len(metrics_data["endpoint_latency_ms"]) >= 1
    assert len(metrics_data["endpoint_latency_ms"]) <= 5
    assert any(item["path"].startswith("/api/v1/trips") for item in metrics_data["endpoint_latency_ms"])

    last_scheduler = metrics_data["last_scheduler_run"]
    assert last_scheduler is not None
    assert last_scheduler["status"] in {"success", "failed"}
    assert isinstance(last_scheduler["processed_count"], int)


def test_end_to_end_invalid_transitions_after_finalize_return_domain_errors() -> None:
    trip_id = _create_trip(total_seats=2)
    request_id = _create_request(trip_id, seats=1)

    accepted = client.post(f"/api/v1/requests/{request_id}/accept")
    assert accepted.status_code == 200

    finalized = client.post(f"/api/v1/trips/{trip_id}/finalize")
    assert finalized.status_code == 200
    assert finalized.json()["data"]["status"] == TRIP_STATUS_FINALIZED

    # Re-finalizing a closed trip must fail with the domain conflict code.
    finalize_again = client.post(f"/api/v1/trips/{trip_id}/finalize")
    assert finalize_again.status_code == 409
    assert finalize_again.json()["error"]["code"] == "ERR_TRIP_NOT_ACTIVE"

    # New requests on a finalized trip are not allowed.
    create_on_finalized = client.post(
        f"/api/v1/trips/{trip_id}/requests",
        json={
            "pickup_label": "Porteria secundaria",
            "requested_seats": 1,
            "comment": "Intento tardio",
        },
    )
    assert create_on_finalized.status_code == 409
    assert create_on_finalized.json()["error"]["code"] == "ERR_TRIP_NOT_ACCEPTING_REQUESTS"

    # Re-accepting a finalized request must remain blocked.
    accept_again = client.post(f"/api/v1/requests/{request_id}/accept")
    assert accept_again.status_code == 409
    assert accept_again.json()["error"]["code"] == "ERR_REQUEST_NOT_PENDING"


def test_notification_read_with_unknown_id_returns_not_found() -> None:
    missing_notification = client.post("/api/v1/notifications/999999/read")
    assert missing_notification.status_code == 404
    assert missing_notification.json()["error"]["code"] == "ERR_NOTIFICATION_NOT_FOUND"
