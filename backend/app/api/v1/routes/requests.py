from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.schemas import ApiErrorEnvelope, TripRequestCreateRequest, TripRequestEnvelope, TripRequestsListEnvelope
from app.core.constants import (
    ACCEPTED_REQUEST_STATUS,
    CANCELLED_REQUEST_STATUS,
    DEFAULT_REQUESTER_USER_ID,
    DEFAULT_USER_ID,
    PENDING_REQUEST_STATUS,
    REJECTED_REQUEST_STATUS,
    TRIP_STATUS_ACTIVE,
)
from app.core.exceptions import DomainConflictException, DomainNotFoundException, DomainValidationException
from app.core.responses import success_response
from app.infrastructure.database import get_db
from app.infrastructure.models import Profile, Trip, TripRequest
from app.services.profile_service import ensure_profile_for_user
from app.services.request_service import (
    accept_request_with_lock,
    ensure_requester_has_no_active_acceptance,
    find_request_or_raise,
    request_payload,
)
from app.services.trip_service import (
    find_trip_or_raise,
    recompute_trip_status_by_capacity,
    trip_available_seats,
)

router = APIRouter()


@router.get(
    "/trips/{trip_id}/requests",
    tags=["requests"],
    response_model=TripRequestsListEnvelope,
    responses={404: {"model": ApiErrorEnvelope}},
)
def list_trip_requests(trip_id: int, db: Session = Depends(get_db)):
    find_trip_or_raise(db, trip_id)
    requester_profiles = {
        profile.user_id: profile
        for profile in db.scalars(select(Profile).where(Profile.user_id != DEFAULT_USER_ID)).all()
    }

    rows = db.scalars(
        select(TripRequest)
        .where(TripRequest.trip_id == trip_id)
        .order_by(TripRequest.created_at.desc())
    ).all()

    items = []
    for item in rows:
        requester = requester_profiles.get(item.requester_user_id)
        if requester is None:
            requester = ensure_profile_for_user(db, item.requester_user_id, f"Solicitante {item.requester_user_id}")
            requester_profiles[item.requester_user_id] = requester
        items.append(request_payload(item, requester))

    return success_response({"items": items})


@router.post(
    "/trips/{trip_id}/requests",
    tags=["requests"],
    status_code=201,
    response_model=TripRequestEnvelope,
    responses={404: {"model": ApiErrorEnvelope}, 409: {"model": ApiErrorEnvelope}, 422: {"model": ApiErrorEnvelope}},
)
def create_trip_request(trip_id: int, payload: TripRequestCreateRequest, db: Session = Depends(get_db)):
    trip = find_trip_or_raise(db, trip_id)
    if trip.status != TRIP_STATUS_ACTIVE:
        raise DomainConflictException(
            code="ERR_TRIP_NOT_ACCEPTING_REQUESTS",
            message="El viaje no esta recibiendo solicitudes.",
        )

    if DEFAULT_REQUESTER_USER_ID == trip.user_id:
        raise DomainValidationException(
            code="ERR_REQUEST_OWN_TRIP_FORBIDDEN",
            message="No puedes solicitar cupos en tu propio viaje.",
        )

    ensure_requester_has_no_active_acceptance(db, DEFAULT_REQUESTER_USER_ID)

    existing_pending = db.scalar(
        select(TripRequest.id).where(
            TripRequest.trip_id == trip.id,
            TripRequest.requester_user_id == DEFAULT_REQUESTER_USER_ID,
            TripRequest.status == PENDING_REQUEST_STATUS,
        )
    )
    if existing_pending is not None:
        raise DomainConflictException(
            code="ERR_TRIP_REQUEST_DUPLICATED",
            message="Ya tienes una solicitud pendiente para este viaje.",
        )

    available = trip_available_seats(db, trip)
    if payload.requested_seats > available:
        raise DomainConflictException(
            code="ERR_TRIP_CAPACITY_EXCEEDED",
            message="No hay cupos suficientes para esta solicitud.",
        )

    requester = ensure_profile_for_user(db, DEFAULT_REQUESTER_USER_ID, "Solicitante Demo")
    trip_request = TripRequest(
        trip_id=trip.id,
        requester_user_id=DEFAULT_REQUESTER_USER_ID,
        pickup_label=payload.pickup_label,
        requested_seats=payload.requested_seats,
        comment=payload.comment,
        status=PENDING_REQUEST_STATUS,
    )
    db.add(trip_request)
    db.commit()
    db.refresh(trip_request)

    return success_response(request_payload(trip_request, requester), status_code=201)


@router.post(
    "/requests/{request_id}/accept",
    tags=["requests"],
    response_model=TripRequestEnvelope,
    responses={404: {"model": ApiErrorEnvelope}, 409: {"model": ApiErrorEnvelope}},
)
def accept_request(request_id: int, db: Session = Depends(get_db)):
    trip_request = accept_request_with_lock(db, request_id)

    db.commit()
    db.refresh(trip_request)
    requester = ensure_profile_for_user(db, trip_request.requester_user_id, "Solicitante Demo")
    return success_response(request_payload(trip_request, requester))


@router.post(
    "/requests/{request_id}/reject",
    tags=["requests"],
    response_model=TripRequestEnvelope,
    responses={404: {"model": ApiErrorEnvelope}, 409: {"model": ApiErrorEnvelope}},
)
def reject_request(request_id: int, db: Session = Depends(get_db)):
    trip_request = find_request_or_raise(db, request_id)
    find_trip_or_raise(db, trip_request.trip_id)

    if trip_request.status != PENDING_REQUEST_STATUS:
        raise DomainConflictException(
            code="ERR_REQUEST_NOT_PENDING",
            message="La solicitud no esta pendiente.",
        )

    trip_request.status = REJECTED_REQUEST_STATUS
    trip_request.decided_at = datetime.now(timezone.utc)
    db.add(trip_request)
    db.commit()
    db.refresh(trip_request)

    requester = ensure_profile_for_user(db, trip_request.requester_user_id, "Solicitante Demo")
    return success_response(request_payload(trip_request, requester))


@router.post(
    "/requests/{request_id}/cancel",
    tags=["requests"],
    response_model=TripRequestEnvelope,
    responses={404: {"model": ApiErrorEnvelope}, 409: {"model": ApiErrorEnvelope}},
)
def cancel_request(request_id: int, db: Session = Depends(get_db)):
    trip_request = find_request_or_raise(db, request_id)

    if trip_request.requester_user_id != DEFAULT_REQUESTER_USER_ID:
        raise DomainNotFoundException(
            code="ERR_TRIP_REQUEST_NOT_FOUND",
            message="Solicitud no encontrada.",
        )

    if trip_request.status not in {PENDING_REQUEST_STATUS, ACCEPTED_REQUEST_STATUS}:
        raise DomainConflictException(
            code="ERR_REQUEST_NOT_CANCELLABLE",
            message="La solicitud no se puede cancelar en su estado actual.",
        )

    trip = db.scalar(select(Trip).where(Trip.id == trip_request.trip_id))
    if trip is None:
        raise DomainNotFoundException(
            code="ERR_TRIP_NOT_FOUND",
            message="Viaje no encontrado.",
        )

    was_accepted = trip_request.status == ACCEPTED_REQUEST_STATUS
    trip_request.status = CANCELLED_REQUEST_STATUS
    trip_request.decided_at = datetime.now(timezone.utc)
    db.add(trip_request)

    if was_accepted:
        recompute_trip_status_by_capacity(db, trip)

    db.commit()
    db.refresh(trip_request)

    requester = ensure_profile_for_user(db, trip_request.requester_user_id, "Solicitante Demo")
    return success_response(request_payload(trip_request, requester))


@router.get(
    "/requests/mine",
    tags=["requests"],
    response_model=TripRequestsListEnvelope,
)
def list_my_requests(db: Session = Depends(get_db)):
    requester = ensure_profile_for_user(db, DEFAULT_REQUESTER_USER_ID, "Solicitante Demo")
    rows = db.scalars(
        select(TripRequest)
        .where(TripRequest.requester_user_id == DEFAULT_REQUESTER_USER_ID)
        .order_by(TripRequest.created_at.desc())
    ).all()
    items = [request_payload(item, requester) for item in rows]
    return success_response({"items": items})
