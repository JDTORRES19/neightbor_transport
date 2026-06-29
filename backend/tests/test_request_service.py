from datetime import datetime, timezone

import pytest
from sqlalchemy import delete

from app.core.constants import (
    ACCEPTED_REQUEST_STATUS,
    CANCELLED_REQUEST_STATUS,
    DEFAULT_REQUESTER_USER_ID,
    DEFAULT_USER_ID,
    PENDING_REQUEST_STATUS,
    TRIP_STATUS_ACTIVE,
    TRIP_STATUS_CANCELLED,
)
from app.core.exceptions import DomainConflictException
from app.infrastructure.database import SessionLocal, init_db
from app.infrastructure.models import Profile, Trip, TripRequest, Vehicle
from app.services.request_service import (
    cancel_other_pending_requests,
    ensure_requester_has_no_active_acceptance,
)


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


def _create_trip(db, *, status: str = TRIP_STATUS_ACTIVE) -> Trip:
    vehicle = db.query(Vehicle).filter(Vehicle.user_id == DEFAULT_USER_ID).first()
    assert vehicle is not None

    trip = Trip(
        user_id=DEFAULT_USER_ID,
        vehicle_id=vehicle.id,
        direction="to_cali",
        origin_label="Unidad La Arboleda",
        departure_at=datetime.now(timezone.utc),
        total_seats=4,
        status=status,
    )
    db.add(trip)
    db.flush()
    return trip


def _create_request(db, *, trip_id: int, status: str, seats: int = 1) -> TripRequest:
    request = TripRequest(
        trip_id=trip_id,
        requester_user_id=DEFAULT_REQUESTER_USER_ID,
        pickup_label="Porteria principal",
        requested_seats=seats,
        comment="Test",
        status=status,
    )
    db.add(request)
    db.flush()
    return request


def test_ensure_requester_has_no_active_acceptance_raises_when_exists() -> None:
    with SessionLocal() as db:
        trip = _create_trip(db, status=TRIP_STATUS_ACTIVE)
        _create_request(db, trip_id=trip.id, status=ACCEPTED_REQUEST_STATUS)
        db.commit()

        with pytest.raises(DomainConflictException) as exc_info:
            ensure_requester_has_no_active_acceptance(db, DEFAULT_REQUESTER_USER_ID)

        assert exc_info.value.code == "ERR_REQUESTER_ACTIVE_ACCEPTED_EXISTS"


def test_ensure_requester_has_no_active_acceptance_ignores_non_active_trip_status() -> None:
    with SessionLocal() as db:
        trip = _create_trip(db, status=TRIP_STATUS_CANCELLED)
        _create_request(db, trip_id=trip.id, status=ACCEPTED_REQUEST_STATUS)
        db.commit()

        ensure_requester_has_no_active_acceptance(db, DEFAULT_REQUESTER_USER_ID)


def test_cancel_other_pending_requests_only_updates_other_pending() -> None:
    with SessionLocal() as db:
        trip_a = _create_trip(db, status=TRIP_STATUS_ACTIVE)
        trip_b = _create_trip(db, status=TRIP_STATUS_ACTIVE)

        target = _create_request(db, trip_id=trip_a.id, status=PENDING_REQUEST_STATUS)
        other_pending = _create_request(db, trip_id=trip_b.id, status=PENDING_REQUEST_STATUS)
        other_accepted = _create_request(db, trip_id=trip_b.id, status=ACCEPTED_REQUEST_STATUS)

        decided_at = datetime.now(timezone.utc)
        cancel_other_pending_requests(
            db,
            requester_user_id=DEFAULT_REQUESTER_USER_ID,
            exclude_request_id=target.id,
            decided_at=decided_at,
        )
        db.flush()

        db.refresh(target)
        db.refresh(other_pending)
        db.refresh(other_accepted)

        assert target.status == PENDING_REQUEST_STATUS
        assert other_pending.status == CANCELLED_REQUEST_STATUS
        assert other_pending.decided_at is not None
        assert other_accepted.status == ACCEPTED_REQUEST_STATUS
