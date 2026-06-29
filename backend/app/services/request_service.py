from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.constants import (
    ACCEPTED_REQUEST_STATUS,
    ACTIVE_TRIP_STATUSES,
    CANCELLED_REQUEST_STATUS,
    DEFAULT_USER_ID,
    PENDING_REQUEST_STATUS,
    TRIP_STATUS_ACTIVE,
)
from app.core.exceptions import DomainConflictException, DomainNotFoundException
from app.core.utils import utc_isoformat
from app.infrastructure.models import Profile, Trip, TripRequest
from app.services.trip_service import recompute_trip_status_by_capacity, trip_available_seats

LOCK_NOT_AVAILABLE_SQLSTATE = "55P03"


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


def _is_lock_not_available(error: OperationalError) -> bool:
    original = getattr(error, "orig", None)
    if original is None:
        return False

    return (
        getattr(original, "pgcode", None) == LOCK_NOT_AVAILABLE_SQLSTATE
        or getattr(original, "sqlstate", None) == LOCK_NOT_AVAILABLE_SQLSTATE
    )


def _raise_concurrent_update(db: Session) -> None:
    db.rollback()
    raise DomainConflictException(
        code="ERR_CONCURRENT_UPDATE",
        message="Conflicto de concurrencia. Intenta nuevamente.",
    )


def accept_request_with_lock(db: Session, request_id: int) -> TripRequest:
    try:
        trip_request = db.scalar(
            select(TripRequest)
            .where(TripRequest.id == request_id)
            .with_for_update(nowait=True)
        )
        if trip_request is None:
            raise DomainNotFoundException(
                code="ERR_TRIP_REQUEST_NOT_FOUND",
                message="Solicitud no encontrada.",
            )

        trip = db.scalar(
            select(Trip)
            .where(
                Trip.id == trip_request.trip_id,
                Trip.user_id == DEFAULT_USER_ID,
            )
            .with_for_update(nowait=True)
        )
        if trip is None:
            raise DomainNotFoundException(
                code="ERR_TRIP_NOT_FOUND",
                message="Viaje no encontrado.",
            )

        # Serializes accept flows for the same requester.
        db.scalars(
            select(TripRequest.id)
            .where(TripRequest.requester_user_id == trip_request.requester_user_id)
            .with_for_update(nowait=True)
        ).all()
    except OperationalError as exc:
        if _is_lock_not_available(exc):
            _raise_concurrent_update(db)
        raise

    if trip_request.status != PENDING_REQUEST_STATUS:
        raise DomainConflictException(
            code="ERR_REQUEST_NOT_PENDING",
            message="La solicitud no esta pendiente.",
        )

    if trip.status != TRIP_STATUS_ACTIVE:
        raise DomainConflictException(
            code="ERR_TRIP_NOT_ACCEPTING_REQUESTS",
            message="El viaje no esta recibiendo solicitudes.",
        )

    ensure_requester_has_no_active_acceptance(
        db,
        trip_request.requester_user_id,
        exclude_request_id=trip_request.id,
    )

    available = trip_available_seats(db, trip)
    if trip_request.requested_seats > available:
        raise DomainConflictException(
            code="ERR_TRIP_CAPACITY_EXCEEDED",
            message="No hay cupos disponibles para aceptar la solicitud.",
        )

    now_utc = datetime.now(timezone.utc)
    trip_request.status = ACCEPTED_REQUEST_STATUS
    trip_request.decided_at = now_utc
    db.add(trip_request)

    cancel_other_pending_requests(
        db,
        requester_user_id=trip_request.requester_user_id,
        exclude_request_id=trip_request.id,
        decided_at=now_utc,
    )

    recompute_trip_status_by_capacity(db, trip)
    return trip_request
