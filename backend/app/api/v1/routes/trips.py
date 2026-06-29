from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.schemas import ApiErrorEnvelope, TripCreateRequest, TripEnvelope, TripMaybeEnvelope, TripsListEnvelope
from app.core.constants import (
    ACTIVE_TRIP_STATUSES,
    DEFAULT_USER_ID,
    TRIP_STATUS_ACTIVE,
    TRIP_STATUS_CANCELLED,
    TRIP_STATUS_FINALIZED,
    VALID_DIRECTIONS,
)
from app.core.exceptions import DomainConflictException, DomainValidationException
from app.core.responses import success_response
from app.core.utils import parse_iso_datetime_to_utc
from app.infrastructure.database import get_db
from app.infrastructure.models import Profile, Trip, Vehicle
from app.services.profile_service import ensure_profile
from app.services.trip_service import find_my_active_trip_query, find_trip_or_raise, trip_payload
from app.services.vehicle_service import find_vehicle_or_raise

router = APIRouter()


@router.get(
    "/trips",
    tags=["trips"],
    response_model=TripsListEnvelope,
)
def list_trips(
    direction: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    if direction and direction not in VALID_DIRECTIONS:
        raise DomainValidationException(
            code="ERR_TRIP_DIRECTION_INVALID",
            message="La direccion del viaje no es valida.",
        )

    query = (
        select(Trip, Profile, Vehicle)
        .join(Profile, Profile.user_id == Trip.user_id)
        .join(Vehicle, Vehicle.id == Trip.vehicle_id)
        .where(Trip.status == TRIP_STATUS_ACTIVE)
        .order_by(Trip.departure_at.asc())
    )
    if direction:
        query = query.where(Trip.direction == direction)

    offset = (max(page, 1) - 1) * max(page_size, 1)
    rows = db.execute(query.offset(offset).limit(max(page_size, 1))).all()
    items = [trip_payload(db, trip, profile, vehicle) for trip, profile, vehicle in rows]
    return success_response({"items": items})


@router.get(
    "/trips/mine/active",
    tags=["trips"],
    response_model=TripMaybeEnvelope,
)
def get_my_active_trip(db: Session = Depends(get_db)):
    row = db.execute(find_my_active_trip_query()).first()

    if row is None:
        return success_response(None)

    trip, profile, vehicle = row
    return success_response(trip_payload(db, trip, profile, vehicle))


@router.post(
    "/trips",
    tags=["trips"],
    status_code=201,
    response_model=TripEnvelope,
    responses={409: {"model": ApiErrorEnvelope}, 422: {"model": ApiErrorEnvelope}},
)
def create_trip(payload: TripCreateRequest, db: Session = Depends(get_db)):
    if payload.direction not in VALID_DIRECTIONS:
        raise DomainValidationException(
            code="ERR_TRIP_DIRECTION_INVALID",
            message="La direccion del viaje no es valida.",
        )

    profile = ensure_profile(db)
    if not profile.phone_e164:
        raise DomainValidationException(
            code="ERR_PHONE_REQUIRED",
            message="Se requiere telefono valido para publicar viaje.",
        )

    vehicle = db.scalar(
        select(Vehicle).where(
            Vehicle.id == payload.vehicle_id,
            Vehicle.user_id == DEFAULT_USER_ID,
            Vehicle.is_active.is_(True),
        )
    )
    if vehicle is None:
        raise DomainValidationException(
            code="ERR_DRIVER_VEHICLE_REQUIRED",
            message="Se requiere un vehiculo activo para publicar viaje.",
        )

    has_active = db.scalar(
        select(Trip.id).where(
            Trip.user_id == DEFAULT_USER_ID,
            Trip.status.in_(ACTIVE_TRIP_STATUSES),
        )
    )
    if has_active is not None:
        raise DomainConflictException(
            code="ERR_DRIVER_ACTIVE_TRIP_EXISTS",
            message="El ofertante ya tiene un viaje activo o lleno.",
        )

    try:
        departure_at = parse_iso_datetime_to_utc(payload.departure_at)
    except ValueError as exc:
        raise DomainValidationException(
            code="ERR_TRIP_DEPARTURE_INVALID",
            message="Formato de fecha de salida invalido.",
        ) from exc

    trip = Trip(
        user_id=DEFAULT_USER_ID,
        vehicle_id=vehicle.id,
        direction=payload.direction,
        origin_label=payload.origin_label,
        departure_at=departure_at,
        total_seats=payload.total_seats,
        status=TRIP_STATUS_ACTIVE,
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)

    return success_response(trip_payload(db, trip, profile, vehicle), status_code=201)


@router.post(
    "/trips/{trip_id}/cancel",
    tags=["trips"],
    response_model=TripEnvelope,
    responses={404: {"model": ApiErrorEnvelope}, 409: {"model": ApiErrorEnvelope}},
)
def cancel_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = find_trip_or_raise(db, trip_id)
    if trip.status not in ACTIVE_TRIP_STATUSES:
        raise DomainConflictException(
            code="ERR_TRIP_NOT_ACTIVE",
            message="El viaje no esta activo para cancelar.",
        )

    trip.status = TRIP_STATUS_CANCELLED
    db.add(trip)
    db.commit()
    db.refresh(trip)

    profile = ensure_profile(db)
    vehicle = find_vehicle_or_raise(db, trip.vehicle_id)
    return success_response(trip_payload(db, trip, profile, vehicle))


@router.post(
    "/trips/{trip_id}/finalize",
    tags=["trips"],
    response_model=TripEnvelope,
    responses={404: {"model": ApiErrorEnvelope}, 409: {"model": ApiErrorEnvelope}},
)
def finalize_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = find_trip_or_raise(db, trip_id)
    if trip.status not in ACTIVE_TRIP_STATUSES:
        raise DomainConflictException(
            code="ERR_TRIP_NOT_ACTIVE",
            message="El viaje no esta activo para finalizar.",
        )

    trip.status = TRIP_STATUS_FINALIZED
    db.add(trip)
    db.commit()
    db.refresh(trip)

    profile = ensure_profile(db)
    vehicle = find_vehicle_or_raise(db, trip.vehicle_id)
    return success_response(trip_payload(db, trip, profile, vehicle))
