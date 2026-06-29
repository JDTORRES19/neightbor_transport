import pytest
from sqlalchemy import delete

from app.core.constants import DEFAULT_USER_ID
from app.core.exceptions import DomainNotFoundException, DomainValidationException
from app.infrastructure.database import SessionLocal, init_db
from app.infrastructure.models import Profile, Vehicle
from app.services.profile_service import normalize_phone
from app.services.vehicle_service import find_vehicle_or_raise, is_plate_taken


@pytest.fixture(autouse=True)
def reset_db_state() -> None:
    init_db()
    with SessionLocal() as db:
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
            Vehicle(
                user_id=DEFAULT_USER_ID,
                brand="Mazda",
                reference="3 Touring",
                color="Rojo",
                plate="ABC123",
                is_active=True,
            )
        )
        db.add(
            Vehicle(
                user_id=DEFAULT_USER_ID,
                brand="Renault",
                reference="Kwid",
                color="Gris",
                plate="ZZZ999",
                is_active=False,
            )
        )
        db.add(
            Vehicle(
                user_id=999,
                brand="Kia",
                reference="Picanto",
                color="Azul",
                plate="OTR111",
                is_active=True,
            )
        )
        db.commit()


def test_normalize_phone_happy_path() -> None:
    normalized = normalize_phone("+57", "300 123-4567")

    assert normalized == "+573001234567"


def test_normalize_phone_raises_for_invalid_prefix() -> None:
    with pytest.raises(DomainValidationException) as exc_info:
        normalize_phone("57", "3001234567")

    assert exc_info.value.code == "ERR_PHONE_PREFIX_INVALID"


def test_normalize_phone_raises_for_invalid_number() -> None:
    with pytest.raises(DomainValidationException) as exc_info:
        normalize_phone("+57", "abc-def")

    assert exc_info.value.code == "ERR_PHONE_INVALID"


def test_is_plate_taken_matches_active_plate_even_with_spaces_and_case() -> None:
    with SessionLocal() as db:
        assert is_plate_taken(db, " aBc 123 ") is True


def test_is_plate_taken_ignores_inactive_plate() -> None:
    with SessionLocal() as db:
        assert is_plate_taken(db, "zzz999") is False


def test_is_plate_taken_respects_exclude_vehicle_id() -> None:
    with SessionLocal() as db:
        active_vehicle = db.query(Vehicle).filter(Vehicle.plate == "ABC123").first()
        assert active_vehicle is not None

        assert is_plate_taken(db, "ABC123", exclude_vehicle_id=active_vehicle.id) is False


def test_find_vehicle_or_raise_returns_default_user_vehicle() -> None:
    with SessionLocal() as db:
        active_vehicle = db.query(Vehicle).filter(Vehicle.user_id == DEFAULT_USER_ID).first()
        assert active_vehicle is not None

        found = find_vehicle_or_raise(db, active_vehicle.id)
        assert found.id == active_vehicle.id


def test_find_vehicle_or_raise_rejects_non_default_user_vehicle() -> None:
    with SessionLocal() as db:
        external_vehicle = db.query(Vehicle).filter(Vehicle.user_id == 999).first()
        assert external_vehicle is not None

        with pytest.raises(DomainNotFoundException) as exc_info:
            find_vehicle_or_raise(db, external_vehicle.id)

        assert exc_info.value.code == "ERR_VEHICLE_NOT_FOUND"
