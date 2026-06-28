from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy import select

from app.main import app
from app.infrastructure.database import SessionLocal, init_db
from app.infrastructure.models import Profile, Trip, TripRequest, Vehicle

client = TestClient(app)
SEEDED_VEHICLE_ID = 1


@pytest.fixture(autouse=True)
def reset_db_state() -> None:
    global SEEDED_VEHICLE_ID

    init_db()
    with SessionLocal() as db:
        db.execute(delete(TripRequest))
        db.execute(delete(Trip))
        db.execute(delete(Vehicle))
        db.execute(delete(Profile))

        db.add(
            Profile(
                user_id=1,
                display_name="Conductor Demo",
                photo_url=None,
                country_code="CO",
                phone_prefix="+57",
                phone_number="3001234567",
                phone_e164="+573001234567",
            )
        )
        db.add(
            Vehicle(
                user_id=1,
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
            .where(Vehicle.user_id == 1)
            .order_by(Vehicle.id.asc())
            .limit(1)
        )
        assert seeded_vehicle is not None
        SEEDED_VEHICLE_ID = seeded_vehicle.id


def _create_trip(total_seats: int = 2) -> int:
    response = client.post(
        "/api/v1/trips",
        json={
            "direction": "to_cali",
            "origin_label": "Unidad La Arboleda",
            "departure_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "total_seats": total_seats,
            "vehicle_id": SEEDED_VEHICLE_ID,
        },
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _create_request(trip_id: int, seats: int = 1) -> dict:
    response = client.post(
        f"/api/v1/trips/{trip_id}/requests",
        json={
            "pickup_label": "Porteria principal",
            "requested_seats": seats,
            "comment": "Voy con maleta",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


def test_create_request_and_list_mine() -> None:
    trip_id = _create_trip(total_seats=3)
    created = _create_request(trip_id, seats=1)

    mine = client.get("/api/v1/requests/mine")
    assert mine.status_code == 200
    assert mine.json()["data"]["items"][0]["id"] == created["id"]
    assert mine.json()["data"]["items"][0]["status"] == "pendiente"


def test_duplicate_pending_request_is_rejected() -> None:
    trip_id = _create_trip(total_seats=3)
    _create_request(trip_id, seats=1)

    duplicate = client.post(
        f"/api/v1/trips/{trip_id}/requests",
        json={
            "pickup_label": "Porteria principal",
            "requested_seats": 1,
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "ERR_TRIP_REQUEST_DUPLICATED"


def test_accept_request_marks_trip_full_when_capacity_reaches_zero() -> None:
    trip_id = _create_trip(total_seats=2)
    request_data = _create_request(trip_id, seats=2)

    accepted = client.post(f"/api/v1/requests/{request_data['id']}/accept")
    assert accepted.status_code == 200
    assert accepted.json()["data"]["status"] == "aceptada"

    my_trip = client.get("/api/v1/trips/mine/active")
    assert my_trip.status_code == 200
    assert my_trip.json()["data"]["status"] == "lleno"
    assert my_trip.json()["data"]["available_seats"] == 0


def test_cancel_accepted_request_reopens_trip_capacity() -> None:
    trip_id = _create_trip(total_seats=2)
    request_data = _create_request(trip_id, seats=2)
    accepted = client.post(f"/api/v1/requests/{request_data['id']}/accept")
    assert accepted.status_code == 200

    cancelled = client.post(f"/api/v1/requests/{request_data['id']}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["data"]["status"] == "cancelada"

    my_trip = client.get("/api/v1/trips/mine/active")
    assert my_trip.status_code == 200
    assert my_trip.json()["data"]["status"] == "activo"
    assert my_trip.json()["data"]["available_seats"] == 2


def test_reject_pending_request_changes_status() -> None:
    trip_id = _create_trip(total_seats=3)
    request_data = _create_request(trip_id, seats=1)

    rejected = client.post(f"/api/v1/requests/{request_data['id']}/reject")
    assert rejected.status_code == 200
    assert rejected.json()["data"]["status"] == "rechazada"
