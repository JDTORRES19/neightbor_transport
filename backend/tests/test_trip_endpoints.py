from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy import select

from app.main import app
from app.infrastructure.database import SessionLocal, init_db
from app.infrastructure.models import Profile, Trip, Vehicle

client = TestClient(app)
SEEDED_VEHICLE_ID = 1


@pytest.fixture(autouse=True)
def reset_db_state() -> None:
    global SEEDED_VEHICLE_ID

    init_db()
    with SessionLocal() as db:
        db.execute(delete(Trip))
        db.execute(delete(Vehicle))
        db.execute(delete(Profile))

        db.add(
            Profile(
                user_id=1,
                display_name="Usuario Demo",
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


def _trip_payload(vehicle_id: int | None = None) -> dict:
    return {
        "direction": "to_cali",
        "origin_label": "Unidad La Arboleda",
        "departure_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "total_seats": 4,
        "vehicle_id": vehicle_id or SEEDED_VEHICLE_ID,
    }


def test_create_trip_and_get_mine_active() -> None:
    create_response = client.post("/api/v1/trips", json=_trip_payload())

    assert create_response.status_code == 201
    payload = create_response.json()
    assert payload["ok"] is True
    assert payload["data"]["status"] == "activo"

    mine_response = client.get("/api/v1/trips/mine/active")
    assert mine_response.status_code == 200
    assert mine_response.json()["data"]["id"] == payload["data"]["id"]


def test_create_trip_enforces_single_active_trip() -> None:
    first_response = client.post("/api/v1/trips", json=_trip_payload())
    assert first_response.status_code == 201

    second_response = client.post("/api/v1/trips", json=_trip_payload())
    assert second_response.status_code == 409
    assert second_response.json()["error"]["code"] == "ERR_DRIVER_ACTIVE_TRIP_EXISTS"


def test_cancel_trip_changes_status_and_clears_active() -> None:
    created = client.post("/api/v1/trips", json=_trip_payload()).json()["data"]

    cancel_response = client.post(f"/api/v1/trips/{created['id']}/cancel")
    assert cancel_response.status_code == 200
    assert cancel_response.json()["data"]["status"] == "cancelado"

    mine_response = client.get("/api/v1/trips/mine/active")
    assert mine_response.status_code == 200
    assert mine_response.json()["data"] is None


def test_list_trips_returns_only_active() -> None:
    active_trip = client.post("/api/v1/trips", json=_trip_payload()).json()["data"]
    client.post(f"/api/v1/trips/{active_trip['id']}/finalize")

    # create a new active trip after finalizing previous one
    client.post("/api/v1/trips", json=_trip_payload())

    list_response = client.get("/api/v1/trips")
    assert list_response.status_code == 200
    payload = list_response.json()["data"]["items"]
    assert len(payload) == 1
    assert payload[0]["status"] == "activo"
