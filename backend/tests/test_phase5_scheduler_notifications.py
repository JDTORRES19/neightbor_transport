from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.main import app
from app.core.constants import (
    ACCEPTED_REQUEST_STATUS,
    AUDIT_ACTION_FINALIZE_TRIP_AUTOMATIC,
    AUDIT_ACTION_FINALIZE_TRIP_MANUAL,
    CANCELLED_BY_FINALIZATION_REQUEST_STATUS,
    DEFAULT_REQUESTER_USER_ID,
    DEFAULT_USER_ID,
    FINALIZED_REQUEST_STATUS,
    NOTIFICATION_TYPE_TRIP_FINALIZED,
    PENDING_REQUEST_STATUS,
    TRIP_STATUS_ACTIVE,
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
            Profile(
                user_id=3,
                display_name="Solicitante Extra",
                photo_url=None,
                country_code="CO",
                phone_prefix="+57",
                phone_number="3010000000",
                phone_e164="+573010000000",
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
            "comment": "Voy con maleta",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _create_manual_request(
    trip_id: int,
    *,
    requester_user_id: int,
    status: str,
    requested_seats: int = 1,
) -> int:
    with SessionLocal() as db:
        request_item = TripRequest(
            trip_id=trip_id,
            requester_user_id=requester_user_id,
            pickup_label="Manual pickup",
            requested_seats=requested_seats,
            comment="Manual request",
            status=status,
        )
        db.add(request_item)
        db.commit()
        db.refresh(request_item)
        return request_item.id


def test_manual_finalize_closes_requests_and_creates_notifications() -> None:
    trip_id = _create_trip(total_seats=2)
    accepted_request_id = _create_request(trip_id, seats=1)
    accepted = client.post(f"/api/v1/requests/{accepted_request_id}/accept")
    assert accepted.status_code == 200

    pending_request_id = _create_manual_request(
        trip_id,
        requester_user_id=3,
        status=PENDING_REQUEST_STATUS,
    )

    finalized = client.post(f"/api/v1/trips/{trip_id}/finalize")
    assert finalized.status_code == 200
    assert finalized.json()["data"]["status"] == TRIP_STATUS_FINALIZED

    requests_response = client.get(f"/api/v1/trips/{trip_id}/requests")
    assert requests_response.status_code == 200
    by_id = {item["id"]: item for item in requests_response.json()["data"]["items"]}
    assert by_id[accepted_request_id]["status"] == FINALIZED_REQUEST_STATUS
    assert by_id[pending_request_id]["status"] == CANCELLED_BY_FINALIZATION_REQUEST_STATUS

    my_notifications = client.get("/api/v1/notifications")
    assert my_notifications.status_code == 200
    items = my_notifications.json()["data"]["items"]
    assert len(items) >= 1
    assert items[0]["type"] == NOTIFICATION_TYPE_TRIP_FINALIZED
    assert my_notifications.json()["data"]["unread_count"] >= 1

    notification_id = items[0]["id"]
    mark_read = client.post(f"/api/v1/notifications/{notification_id}/read")
    assert mark_read.status_code == 200
    assert mark_read.json()["data"]["is_read"] is True

    read_all = client.post("/api/v1/notifications/read-all")
    assert read_all.status_code == 200
    assert read_all.json()["data"]["updated_count"] >= 0

    with SessionLocal() as db:
        audit_events = db.scalars(
            select(AuditEvent).where(
                AuditEvent.entity_type == "trip",
                AuditEvent.entity_id == trip_id,
            )
        ).all()
        assert len(audit_events) == 1
        assert audit_events[0].action == AUDIT_ACTION_FINALIZE_TRIP_MANUAL
        assert audit_events[0].actor_user_id == DEFAULT_USER_ID


def test_scheduler_auto_finalize_is_idempotent_and_logs_runs() -> None:
    now_utc = datetime.now(timezone.utc)
    expired_departure = now_utc - timedelta(minutes=21)

    trip_id = _create_trip(departure_at=expired_departure, total_seats=2)
    _create_manual_request(
        trip_id,
        requester_user_id=DEFAULT_REQUESTER_USER_ID,
        status=ACCEPTED_REQUEST_STATUS,
        requested_seats=1,
    )
    _create_manual_request(
        trip_id,
        requester_user_id=3,
        status=PENDING_REQUEST_STATUS,
        requested_seats=1,
    )

    first_run = run_auto_finalize_trips_job(now_utc=now_utc)
    assert first_run["status"] == "success"
    assert first_run["processed_count"] == 1
    assert first_run["failed_count"] == 0

    with SessionLocal() as db:
        trip = db.scalar(select(Trip).where(Trip.id == trip_id))
        assert trip is not None
        assert trip.status == TRIP_STATUS_FINALIZED

        requests = db.scalars(select(TripRequest).where(TripRequest.trip_id == trip_id)).all()
        statuses = {item.status for item in requests}
        assert FINALIZED_REQUEST_STATUS in statuses
        assert CANCELLED_BY_FINALIZATION_REQUEST_STATUS in statuses

        created_notifications = db.scalars(
            select(Notification).where(Notification.type == NOTIFICATION_TYPE_TRIP_FINALIZED)
        ).all()
        assert len(created_notifications) == 2

    second_run = run_auto_finalize_trips_job(now_utc=now_utc)
    assert second_run["status"] == "success"
    assert second_run["processed_count"] == 0

    with SessionLocal() as db:
        runs = db.scalars(
            select(SchedulerJobRun)
            .order_by(SchedulerJobRun.id.asc())
        ).all()
        assert len(runs) == 2
        assert all(run.status == "success" for run in runs)

        audit_events = db.scalars(
            select(AuditEvent).where(
                AuditEvent.entity_type == "trip",
                AuditEvent.entity_id == trip_id,
            )
        ).all()
        assert len(audit_events) == 1
        assert audit_events[0].action == AUDIT_ACTION_FINALIZE_TRIP_AUTOMATIC
        assert audit_events[0].actor_user_id is None
