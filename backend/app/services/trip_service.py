from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import (
    ACCEPTED_REQUEST_STATUS,
    ACTIVE_TRIP_STATUSES,
    CANCELLED_BY_FINALIZATION_REQUEST_STATUS,
    DEFAULT_USER_ID,
    FINALIZED_REQUEST_STATUS,
    PENDING_REQUEST_STATUS,
    TRIP_STATUS_ACTIVE,
    TRIP_STATUS_CANCELLED,
    TRIP_STATUS_FINALIZED,
    TRIP_STATUS_FULL,
)
from app.core.exceptions import DomainNotFoundException
from app.core.utils import utc_isoformat
from app.infrastructure.models import Profile, Trip, TripRequest, Vehicle


def find_trip_or_raise(db: Session, trip_id: int) -> Trip:
    trip = db.scalar(
        select(Trip).where(
            Trip.id == trip_id,
            Trip.user_id == DEFAULT_USER_ID,
        )
    )
    if trip is None:
        raise DomainNotFoundException(
            code="ERR_TRIP_NOT_FOUND",
            message="Viaje no encontrado.",
        )
    return trip


def trip_available_seats(db: Session, trip: Trip) -> int:
    accepted = db.scalar(
        select(func.coalesce(func.sum(TripRequest.requested_seats), 0)).where(
            TripRequest.trip_id == trip.id,
            TripRequest.status == ACCEPTED_REQUEST_STATUS,
        )
    )
    used_seats = int(accepted or 0)
    return max(0, trip.total_seats - used_seats)


def trip_payload(db: Session, trip: Trip, driver: Profile, vehicle: Vehicle) -> dict[str, Any]:
    return {
        "id": trip.id,
        "direction": trip.direction,
        "origin_label": trip.origin_label,
        "departure_at": utc_isoformat(trip.departure_at),
        "published_at": utc_isoformat(trip.published_at),
        "status": trip.status,
        "total_seats": trip.total_seats,
        "available_seats": trip_available_seats(db, trip),
        "driver": {
            "user_id": driver.user_id,
            "display_name": driver.display_name,
            "photo_url": driver.photo_url,
        },
        "vehicle": {
            "id": vehicle.id,
            "brand": vehicle.brand,
            "reference": vehicle.reference,
            "color": vehicle.color,
            "plate": vehicle.plate,
        },
    }


def recompute_trip_status_by_capacity(db: Session, trip: Trip) -> None:
    if trip.status in {TRIP_STATUS_CANCELLED, TRIP_STATUS_FINALIZED}:
        return

    db.flush()
    available = trip_available_seats(db, trip)
    trip.status = TRIP_STATUS_FULL if available == 0 else TRIP_STATUS_ACTIVE
    db.add(trip)


def find_my_active_trip_query():
    return (
        select(Trip, Profile, Vehicle)
        .join(Profile, Profile.user_id == Trip.user_id)
        .join(Vehicle, Vehicle.id == Trip.vehicle_id)
        .where(
            Trip.user_id == DEFAULT_USER_ID,
            Trip.status.in_(ACTIVE_TRIP_STATUSES),
        )
        .order_by(Trip.published_at.desc())
        .limit(1)
    )


def finalize_trip_and_close_requests(
    db: Session,
    trip: Trip,
    *,
    now_utc: datetime | None = None,
) -> set[int]:
    now = now_utc or datetime.now(timezone.utc)
    impacted_requests = db.scalars(
        select(TripRequest).where(
            TripRequest.trip_id == trip.id,
            TripRequest.status.in_({PENDING_REQUEST_STATUS, ACCEPTED_REQUEST_STATUS}),
        )
    ).all()

    requester_user_ids: set[int] = set()
    for request_item in impacted_requests:
        requester_user_ids.add(request_item.requester_user_id)
        if request_item.status == PENDING_REQUEST_STATUS:
            request_item.status = CANCELLED_BY_FINALIZATION_REQUEST_STATUS
        else:
            request_item.status = FINALIZED_REQUEST_STATUS

        request_item.decided_at = now
        db.add(request_item)

    trip.status = TRIP_STATUS_FINALIZED
    db.add(trip)
    return requester_user_ids
