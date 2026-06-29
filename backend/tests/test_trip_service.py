from datetime import datetime, timedelta, timezone

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
    TRIP_STATUS_FINALIZED,
    TRIP_STATUS_FULL,
)
from app.infrastructure.database import SessionLocal, init_db
from app.infrastructure.models import Profile, Trip, TripRequest, Vehicle
from app.services.trip_service import (
    find_my_active_trip_query,
    recompute_trip_status_by_capacity,
    trip_available_seats,
    trip_payload,
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


def _create_trip(
    db,
    *,
    total_seats: int = 4,
    status: str = TRIP_STATUS_ACTIVE,
    published_at: datetime | None = None,
) -> Trip:
    vehicle = db.query(Vehicle).filter(Vehicle.user_id == DEFAULT_USER_ID).first()
    assert vehicle is not None

    now_utc = datetime.now(timezone.utc)
    trip = Trip(
        user_id=DEFAULT_USER_ID,
        vehicle_id=vehicle.id,
        direction="to_cali",
        origin_label="Unidad La Arboleda",
        departure_at=now_utc,
        published_at=published_at or now_utc,
        total_seats=total_seats,
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


def test_trip_available_seats_only_counts_accepted_requests() -> None:
    with SessionLocal() as db:
        trip = _create_trip(db, total_seats=4)
        _create_request(db, trip_id=trip.id, status=ACCEPTED_REQUEST_STATUS, seats=1)
        _create_request(db, trip_id=trip.id, status=PENDING_REQUEST_STATUS, seats=2)

        available = trip_available_seats(db, trip)
        assert available == 3


def test_recompute_trip_status_by_capacity_sets_full_and_active() -> None:
    with SessionLocal() as db:
        trip = _create_trip(db, total_seats=2, status=TRIP_STATUS_ACTIVE)
        accepted = _create_request(db, trip_id=trip.id, status=ACCEPTED_REQUEST_STATUS, seats=2)

        recompute_trip_status_by_capacity(db, trip)
        db.flush()
        assert trip.status == TRIP_STATUS_FULL

        accepted.status = CANCELLED_REQUEST_STATUS
        db.add(accepted)
        recompute_trip_status_by_capacity(db, trip)
        db.flush()
        assert trip.status == TRIP_STATUS_ACTIVE


def test_recompute_trip_status_by_capacity_does_not_change_closed_statuses() -> None:
    with SessionLocal() as db:
        cancelled_trip = _create_trip(db, total_seats=2, status=TRIP_STATUS_CANCELLED)
        finalized_trip = _create_trip(db, total_seats=2, status=TRIP_STATUS_FINALIZED)

        recompute_trip_status_by_capacity(db, cancelled_trip)
        recompute_trip_status_by_capacity(db, finalized_trip)
        db.flush()

        assert cancelled_trip.status == TRIP_STATUS_CANCELLED
        assert finalized_trip.status == TRIP_STATUS_FINALIZED


def test_trip_payload_includes_utc_dates_and_available_seats() -> None:
    with SessionLocal() as db:
        trip = _create_trip(db, total_seats=3, status=TRIP_STATUS_ACTIVE)
        _create_request(db, trip_id=trip.id, status=ACCEPTED_REQUEST_STATUS, seats=1)

        driver = db.query(Profile).filter(Profile.user_id == DEFAULT_USER_ID).first()
        vehicle = db.query(Vehicle).filter(Vehicle.user_id == DEFAULT_USER_ID).first()
        assert driver is not None
        assert vehicle is not None

        payload = trip_payload(db, trip, driver, vehicle)

        assert payload["id"] == trip.id
        assert payload["status"] == TRIP_STATUS_ACTIVE
        assert payload["available_seats"] == 2
        assert payload["departure_at"].endswith("Z")
        assert payload["published_at"].endswith("Z")


def test_find_my_active_trip_query_returns_latest_active_or_full() -> None:
    with SessionLocal() as db:
        now_utc = datetime.now(timezone.utc)
        _create_trip(db, status=TRIP_STATUS_CANCELLED, published_at=now_utc - timedelta(minutes=3))
        _create_trip(db, status=TRIP_STATUS_ACTIVE, published_at=now_utc - timedelta(minutes=2))
        latest_full = _create_trip(db, status=TRIP_STATUS_FULL, published_at=now_utc - timedelta(minutes=1))

        row = db.execute(find_my_active_trip_query()).first()
        assert row is not None

        trip, _, _ = row
        assert trip.id == latest_full.id
