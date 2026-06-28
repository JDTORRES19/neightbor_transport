import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.main import app
from app.infrastructure.database import SessionLocal, init_db
from app.infrastructure.models import Profile, Trip, TripRequest, Vehicle

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db_state() -> None:
    init_db()
    with SessionLocal() as db:
        db.execute(delete(TripRequest))
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


def test_get_me_success_envelope() -> None:
    response = client.get("/api/v1/me")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["phone_e164"] == "+573001234567"


def test_patch_me_updates_phone_and_keeps_envelope() -> None:
    response = client.patch(
        "/api/v1/me",
        json={"phone_prefix": "+57", "phone_number": "311 555 0000"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["phone_e164"] == "+573115550000"


def test_vehicle_crud_and_plate_conflict() -> None:
    create_response = client.post(
        "/api/v1/vehicles",
        json={
            "brand": "Kia",
            "reference": "Picanto",
            "color": "Blanco",
            "plate": "XYZ987",
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()["data"]

    conflict_response = client.post(
        "/api/v1/vehicles",
        json={
            "brand": "Renault",
            "reference": "Logan",
            "color": "Gris",
            "plate": "xyz987",
        },
    )
    assert conflict_response.status_code == 409
    assert conflict_response.json()["error"]["code"] == "ERR_VEHICLE_PLATE_EXISTS"

    deactivate_response = client.delete(f"/api/v1/vehicles/{created['id']}")
    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["data"]["is_active"] is False
