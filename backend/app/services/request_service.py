from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import (
    ACCEPTED_REQUEST_STATUS,
    ACTIVE_TRIP_STATUSES,
    CANCELLED_REQUEST_STATUS,
    PENDING_REQUEST_STATUS,
)
from app.core.exceptions import DomainConflictException, DomainNotFoundException
from app.core.utils import utc_isoformat
from app.infrastructure.models import Profile, Trip, TripRequest


def find_request_or_raise(db: Session, request_id: int) -> TripRequest:
    trip_request = db.scalar(select(TripRequest).where(TripRequest.id == request_id))
    if trip_request is None:
        raise DomainNotFoundException(
            code="ERR_TRIP_REQUEST_NOT_FOUND",
            message="Solicitud no encontrada.",
        )
    return trip_request


def request_payload(trip_request: TripRequest, requester: Profile) -> dict[str, Any]:
    return {
        "id": trip_request.id,
        "trip_id": trip_request.trip_id,
        "pickup_label": trip_request.pickup_label,
        "requested_seats": trip_request.requested_seats,
        "comment": trip_request.comment,
        "status": trip_request.status,
        "created_at": utc_isoformat(trip_request.created_at),
        "decided_at": utc_isoformat(trip_request.decided_at),
        "requester": {
            "user_id": requester.user_id,
            "display_name": requester.display_name,
            "photo_url": requester.photo_url,
        },
    }


def ensure_requester_has_no_active_acceptance(
    db: Session, requester_user_id: int, exclude_request_id: int | None = None
) -> None:
    query = (
        select(TripRequest.id)
        .join(Trip, Trip.id == TripRequest.trip_id)
        .where(
            TripRequest.requester_user_id == requester_user_id,
            TripRequest.status == ACCEPTED_REQUEST_STATUS,
            Trip.status.in_(ACTIVE_TRIP_STATUSES),
        )
    )
    if exclude_request_id is not None:
        query = query.where(TripRequest.id != exclude_request_id)

    if db.scalar(query) is not None:
        raise DomainConflictException(
            code="ERR_REQUESTER_ACTIVE_ACCEPTED_EXISTS",
            message="El solicitante ya tiene una solicitud aceptada activa.",
        )


def cancel_other_pending_requests(
    db: Session,
    requester_user_id: int,
    exclude_request_id: int,
    decided_at,
):
    pending_others = db.scalars(
        select(TripRequest).where(
            TripRequest.requester_user_id == requester_user_id,
            TripRequest.status == PENDING_REQUEST_STATUS,
            TripRequest.id != exclude_request_id,
        )
    ).all()
    for item in pending_others:
        item.status = CANCELLED_REQUEST_STATUS
        item.decided_at = decided_at
        db.add(item)
    return pending_others
