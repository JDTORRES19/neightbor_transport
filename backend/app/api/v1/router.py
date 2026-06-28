from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.schemas import (
    ApiErrorEnvelope,
    HealthSuccessEnvelope,
    ProfileEnvelope,
    ProfileUpdateRequest,
    TripCreateRequest,
    TripEnvelope,
    TripMaybeEnvelope,
    TripRequestCreateRequest,
    TripRequestEnvelope,
    TripRequestsListEnvelope,
    TripsListEnvelope,
    VehicleCreateRequest,
    VehicleEnvelope,
    VehiclesListEnvelope,
    VehicleUpdateRequest,
)
from app.core.exceptions import (
    DomainConflictException,
    DomainNotFoundException,
    DomainValidationException,
)
from app.core.responses import success_response
from app.infrastructure.database import get_db
from app.infrastructure.models import Profile, Trip, TripRequest, Vehicle

api_router = APIRouter()

DEFAULT_USER_ID = 1
DEFAULT_REQUESTER_USER_ID = 2
ACTIVE_TRIP_STATUSES = {"activo", "lleno"}
VALID_DIRECTIONS = {"to_cali", "to_jamundi"}
PENDING_REQUEST_STATUS = "pendiente"
ACCEPTED_REQUEST_STATUS = "aceptada"
REJECTED_REQUEST_STATUS = "rechazada"
CANCELLED_REQUEST_STATUS = "cancelada"


def _normalize_phone(phone_prefix: str, phone_number: str) -> str:
    if not phone_prefix or not phone_prefix.startswith("+"):
        raise DomainValidationException(
            code="ERR_PHONE_PREFIX_INVALID",
            message="El prefijo telefonico debe iniciar con +.",
        )

    normalized_number = "".join(ch for ch in phone_number if ch.isdigit())
    if not normalized_number:
        raise DomainValidationException(
            code="ERR_PHONE_INVALID",
            message="El numero de telefono no es valido.",
        )

    return f"{phone_prefix}{normalized_number}"


def _find_vehicle_or_raise(db: Session, vehicle_id: int) -> Vehicle:
    vehicle = db.scalar(
        select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.user_id == DEFAULT_USER_ID,
        )
    )
    if vehicle is None:
        raise DomainNotFoundException(
            code="ERR_VEHICLE_NOT_FOUND",
            message="Vehiculo no encontrado.",
        )
    return vehicle


def _is_plate_taken(db: Session, plate: str, exclude_vehicle_id: int | None = None) -> bool:
    normalized_plate = plate.replace(" ", "").upper()
    query = select(Vehicle).where(
        Vehicle.plate == normalized_plate,
        Vehicle.is_active.is_(True),
    )
    if exclude_vehicle_id is not None:
        query = query.where(Vehicle.id != exclude_vehicle_id)
    return db.scalar(query) is not None


def _vehicle_payload(vehicle: Vehicle) -> dict[str, Any]:
    return {
        "id": vehicle.id,
        "brand": vehicle.brand,
        "reference": vehicle.reference,
        "color": vehicle.color,
        "plate": vehicle.plate,
        "is_active": vehicle.is_active,
    }


def _ensure_profile_for_user(db: Session, user_id: int, fallback_name: str) -> Profile:
    profile = db.scalar(select(Profile).where(Profile.user_id == user_id))
    if profile is not None:
        return profile

    profile = Profile(
        user_id=user_id,
        display_name=fallback_name,
        photo_url=None,
        country_code="CO",
        phone_prefix="+57",
        phone_number="3001234567",
        phone_e164="+573001234567",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def _ensure_profile(db: Session) -> Profile:
    return _ensure_profile_for_user(db, DEFAULT_USER_ID, "Usuario Demo")


def _profile_payload(profile: Profile) -> dict[str, Any]:
    return {
        "user_id": profile.user_id,
        "display_name": profile.display_name,
        "photo_url": profile.photo_url,
        "country_code": profile.country_code,
        "phone_prefix": profile.phone_prefix,
        "phone_number": profile.phone_number,
        "phone_e164": profile.phone_e164,
    }


def _trip_available_seats(db: Session, trip: Trip) -> int:
    accepted = db.scalar(
        select(func.coalesce(func.sum(TripRequest.requested_seats), 0)).where(
            TripRequest.trip_id == trip.id,
            TripRequest.status == ACCEPTED_REQUEST_STATUS,
        )
    )
    used_seats = int(accepted or 0)
    return max(0, trip.total_seats - used_seats)


def _trip_payload(db: Session, trip: Trip, driver: Profile, vehicle: Vehicle) -> dict[str, Any]:
    return {
        "id": trip.id,
        "direction": trip.direction,
        "origin_label": trip.origin_label,
        "departure_at": trip.departure_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "published_at": trip.published_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": trip.status,
        "total_seats": trip.total_seats,
        "available_seats": _trip_available_seats(db, trip),
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


def _find_trip_or_raise(db: Session, trip_id: int) -> Trip:
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


def _find_request_or_raise(db: Session, request_id: int) -> TripRequest:
    trip_request = db.scalar(select(TripRequest).where(TripRequest.id == request_id))
    if trip_request is None:
        raise DomainNotFoundException(
            code="ERR_TRIP_REQUEST_NOT_FOUND",
            message="Solicitud no encontrada.",
        )
    return trip_request


def _request_payload(trip_request: TripRequest, requester: Profile) -> dict[str, Any]:
    return {
        "id": trip_request.id,
        "trip_id": trip_request.trip_id,
        "pickup_label": trip_request.pickup_label,
        "requested_seats": trip_request.requested_seats,
        "comment": trip_request.comment,
        "status": trip_request.status,
        "created_at": trip_request.created_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "decided_at": (
            trip_request.decided_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
            if trip_request.decided_at is not None
            else None
        ),
        "requester": {
            "user_id": requester.user_id,
            "display_name": requester.display_name,
            "photo_url": requester.photo_url,
        },
    }


def _ensure_requester_has_no_active_acceptance(
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


def _recompute_trip_status_by_capacity(db: Session, trip: Trip) -> None:
    if trip.status in {"cancelado", "finalizado"}:
        return

    db.flush()
    available = _trip_available_seats(db, trip)
    trip.status = "lleno" if available == 0 else "activo"
    db.add(trip)


@api_router.get(
    "/health",
    tags=["health"],
    response_model=HealthSuccessEnvelope,
    responses={500: {"model": ApiErrorEnvelope}},
)
def api_healthcheck():
    return success_response({"status": "ok", "service": "web"})


@api_router.get(
    "/health/conflict",
    tags=["health"],
    status_code=409,
    responses={409: {"model": ApiErrorEnvelope}},
)
def api_health_conflict_probe():
    raise DomainConflictException(
        code="ERR_DEMO_CONFLICT",
        message="Conflicto de prueba para validar envelope de error.",
    )


@api_router.patch(
    "/me",
    tags=["profile"],
    response_model=ProfileEnvelope,
    responses={422: {"model": ApiErrorEnvelope}},
)
def update_my_profile(payload: ProfileUpdateRequest, db: Session = Depends(get_db)):
    profile = _ensure_profile(db)

    if payload.display_name is not None:
        profile.display_name = payload.display_name.strip() or profile.display_name
    if payload.photo_url is not None:
        profile.photo_url = payload.photo_url
    if payload.country_code is not None:
        profile.country_code = payload.country_code

    prefix = payload.phone_prefix if payload.phone_prefix is not None else profile.phone_prefix
    number = payload.phone_number if payload.phone_number is not None else profile.phone_number
    if payload.phone_prefix is not None or payload.phone_number is not None:
        profile.phone_prefix = prefix
        profile.phone_number = number
        profile.phone_e164 = _normalize_phone(prefix, number)

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return success_response(_profile_payload(profile))


@api_router.get(
    "/vehicles",
    tags=["vehicles"],
    response_model=VehiclesListEnvelope,
)
def list_vehicles(db: Session = Depends(get_db)):
    items = [
        _vehicle_payload(item)
        for item in db.scalars(
            select(Vehicle)
            .where(Vehicle.user_id == DEFAULT_USER_ID)
            .order_by(Vehicle.id.asc())
        ).all()
    ]
    return success_response({"items": items})


@api_router.post(
    "/vehicles",
    tags=["vehicles"],
    status_code=201,
    response_model=VehicleEnvelope,
    responses={409: {"model": ApiErrorEnvelope}},
)
def create_vehicle(payload: VehicleCreateRequest, db: Session = Depends(get_db)):
    normalized_plate = payload.plate.replace(" ", "").upper()
    if _is_plate_taken(db, normalized_plate):
        raise DomainConflictException(
            code="ERR_VEHICLE_PLATE_EXISTS",
            message="Ya existe un vehiculo activo con esa placa.",
        )

    vehicle = Vehicle(
        user_id=DEFAULT_USER_ID,
        brand=payload.brand,
        reference=payload.reference,
        color=payload.color,
        plate=normalized_plate,
        is_active=True,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return success_response(_vehicle_payload(vehicle), status_code=201)


@api_router.patch(
    "/vehicles/{vehicle_id}",
    tags=["vehicles"],
    response_model=VehicleEnvelope,
    responses={404: {"model": ApiErrorEnvelope}, 409: {"model": ApiErrorEnvelope}},
)
def update_vehicle(vehicle_id: int, payload: VehicleUpdateRequest, db: Session = Depends(get_db)):
    vehicle = _find_vehicle_or_raise(db, vehicle_id)

    if payload.plate is not None:
        normalized_plate = payload.plate.replace(" ", "").upper()
        if _is_plate_taken(db, normalized_plate, exclude_vehicle_id=vehicle_id):
            raise DomainConflictException(
                code="ERR_VEHICLE_PLATE_EXISTS",
                message="Ya existe un vehiculo activo con esa placa.",
            )
        vehicle.plate = normalized_plate
    if payload.brand is not None:
        vehicle.brand = payload.brand
    if payload.reference is not None:
        vehicle.reference = payload.reference
    if payload.color is not None:
        vehicle.color = payload.color

    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return success_response(_vehicle_payload(vehicle))


@api_router.delete(
    "/vehicles/{vehicle_id}",
    tags=["vehicles"],
    response_model=VehicleEnvelope,
    responses={404: {"model": ApiErrorEnvelope}},
)
def deactivate_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = _find_vehicle_or_raise(db, vehicle_id)
    vehicle.is_active = False
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return success_response(_vehicle_payload(vehicle))


@api_router.get(
    "/me",
    tags=["profile"],
    response_model=ProfileEnvelope,
    responses={422: {"model": ApiErrorEnvelope}},
)
def get_my_profile(db: Session = Depends(get_db)):
    profile = _ensure_profile(db)
    return success_response(_profile_payload(profile))


@api_router.get(
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
        .where(Trip.status == "activo")
        .order_by(Trip.departure_at.asc())
    )
    if direction:
        query = query.where(Trip.direction == direction)

    offset = (max(page, 1) - 1) * max(page_size, 1)
    rows = db.execute(query.offset(offset).limit(max(page_size, 1))).all()
    items = [_trip_payload(db, trip, profile, vehicle) for trip, profile, vehicle in rows]
    return success_response({"items": items})


@api_router.get(
    "/trips/mine/active",
    tags=["trips"],
    response_model=TripMaybeEnvelope,
)
def get_my_active_trip(db: Session = Depends(get_db)):
    row = db.execute(
        select(Trip, Profile, Vehicle)
        .join(Profile, Profile.user_id == Trip.user_id)
        .join(Vehicle, Vehicle.id == Trip.vehicle_id)
        .where(
            Trip.user_id == DEFAULT_USER_ID,
            Trip.status.in_(ACTIVE_TRIP_STATUSES),
        )
        .order_by(Trip.published_at.desc())
        .limit(1)
    ).first()

    if row is None:
        return success_response(None)

    trip, profile, vehicle = row
    return success_response(_trip_payload(db, trip, profile, vehicle))


@api_router.post(
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

    profile = _ensure_profile(db)
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
        departure_at = datetime.fromisoformat(payload.departure_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DomainValidationException(
            code="ERR_TRIP_DEPARTURE_INVALID",
            message="Formato de fecha de salida invalido.",
        ) from exc

    if departure_at.tzinfo is None:
        departure_at = departure_at.replace(tzinfo=timezone.utc)

    trip = Trip(
        user_id=DEFAULT_USER_ID,
        vehicle_id=vehicle.id,
        direction=payload.direction,
        origin_label=payload.origin_label,
        departure_at=departure_at.astimezone(timezone.utc),
        total_seats=payload.total_seats,
        status="activo",
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)

    return success_response(_trip_payload(db, trip, profile, vehicle), status_code=201)


@api_router.post(
    "/trips/{trip_id}/cancel",
    tags=["trips"],
    response_model=TripEnvelope,
    responses={404: {"model": ApiErrorEnvelope}, 409: {"model": ApiErrorEnvelope}},
)
def cancel_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = _find_trip_or_raise(db, trip_id)
    if trip.status not in ACTIVE_TRIP_STATUSES:
        raise DomainConflictException(
            code="ERR_TRIP_NOT_ACTIVE",
            message="El viaje no esta activo para cancelar.",
        )

    trip.status = "cancelado"
    db.add(trip)
    db.commit()
    db.refresh(trip)

    profile = _ensure_profile(db)
    vehicle = _find_vehicle_or_raise(db, trip.vehicle_id)
    return success_response(_trip_payload(db, trip, profile, vehicle))


@api_router.post(
    "/trips/{trip_id}/finalize",
    tags=["trips"],
    response_model=TripEnvelope,
    responses={404: {"model": ApiErrorEnvelope}, 409: {"model": ApiErrorEnvelope}},
)
def finalize_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = _find_trip_or_raise(db, trip_id)
    if trip.status not in ACTIVE_TRIP_STATUSES:
        raise DomainConflictException(
            code="ERR_TRIP_NOT_ACTIVE",
            message="El viaje no esta activo para finalizar.",
        )

    trip.status = "finalizado"
    db.add(trip)
    db.commit()
    db.refresh(trip)

    profile = _ensure_profile(db)
    vehicle = _find_vehicle_or_raise(db, trip.vehicle_id)
    return success_response(_trip_payload(db, trip, profile, vehicle))


@api_router.get(
    "/trips/{trip_id}/requests",
    tags=["requests"],
    response_model=TripRequestsListEnvelope,
    responses={404: {"model": ApiErrorEnvelope}},
)
def list_trip_requests(trip_id: int, db: Session = Depends(get_db)):
    _find_trip_or_raise(db, trip_id)
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
            requester = _ensure_profile_for_user(db, item.requester_user_id, f"Solicitante {item.requester_user_id}")
            requester_profiles[item.requester_user_id] = requester
        items.append(_request_payload(item, requester))

    return success_response({"items": items})


@api_router.post(
    "/trips/{trip_id}/requests",
    tags=["requests"],
    status_code=201,
    response_model=TripRequestEnvelope,
    responses={404: {"model": ApiErrorEnvelope}, 409: {"model": ApiErrorEnvelope}, 422: {"model": ApiErrorEnvelope}},
)
def create_trip_request(trip_id: int, payload: TripRequestCreateRequest, db: Session = Depends(get_db)):
    trip = _find_trip_or_raise(db, trip_id)
    if trip.status != "activo":
        raise DomainConflictException(
            code="ERR_TRIP_NOT_ACCEPTING_REQUESTS",
            message="El viaje no esta recibiendo solicitudes.",
        )

    if DEFAULT_REQUESTER_USER_ID == trip.user_id:
        raise DomainValidationException(
            code="ERR_REQUEST_OWN_TRIP_FORBIDDEN",
            message="No puedes solicitar cupos en tu propio viaje.",
        )

    _ensure_requester_has_no_active_acceptance(db, DEFAULT_REQUESTER_USER_ID)

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

    available = _trip_available_seats(db, trip)
    if payload.requested_seats > available:
        raise DomainConflictException(
            code="ERR_TRIP_CAPACITY_EXCEEDED",
            message="No hay cupos suficientes para esta solicitud.",
        )

    requester = _ensure_profile_for_user(db, DEFAULT_REQUESTER_USER_ID, "Solicitante Demo")
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

    return success_response(_request_payload(trip_request, requester), status_code=201)


@api_router.post(
    "/requests/{request_id}/accept",
    tags=["requests"],
    response_model=TripRequestEnvelope,
    responses={404: {"model": ApiErrorEnvelope}, 409: {"model": ApiErrorEnvelope}},
)
def accept_request(request_id: int, db: Session = Depends(get_db)):
    trip_request = _find_request_or_raise(db, request_id)
    trip = _find_trip_or_raise(db, trip_request.trip_id)

    if trip_request.status != PENDING_REQUEST_STATUS:
        raise DomainConflictException(
            code="ERR_REQUEST_NOT_PENDING",
            message="La solicitud no esta pendiente.",
        )

    if trip.status != "activo":
        raise DomainConflictException(
            code="ERR_TRIP_NOT_ACCEPTING_REQUESTS",
            message="El viaje no esta recibiendo solicitudes.",
        )

    _ensure_requester_has_no_active_acceptance(db, trip_request.requester_user_id, exclude_request_id=trip_request.id)

    available = _trip_available_seats(db, trip)
    if trip_request.requested_seats > available:
        raise DomainConflictException(
            code="ERR_TRIP_CAPACITY_EXCEEDED",
            message="No hay cupos disponibles para aceptar la solicitud.",
        )

    now_utc = datetime.now(timezone.utc)
    trip_request.status = ACCEPTED_REQUEST_STATUS
    trip_request.decided_at = now_utc
    db.add(trip_request)

    pending_others = db.scalars(
        select(TripRequest).where(
            TripRequest.requester_user_id == trip_request.requester_user_id,
            TripRequest.status == PENDING_REQUEST_STATUS,
            TripRequest.id != trip_request.id,
        )
    ).all()
    for item in pending_others:
        item.status = CANCELLED_REQUEST_STATUS
        item.decided_at = now_utc
        db.add(item)

    _recompute_trip_status_by_capacity(db, trip)

    db.commit()
    db.refresh(trip_request)
    requester = _ensure_profile_for_user(db, trip_request.requester_user_id, "Solicitante Demo")
    return success_response(_request_payload(trip_request, requester))


@api_router.post(
    "/requests/{request_id}/reject",
    tags=["requests"],
    response_model=TripRequestEnvelope,
    responses={404: {"model": ApiErrorEnvelope}, 409: {"model": ApiErrorEnvelope}},
)
def reject_request(request_id: int, db: Session = Depends(get_db)):
    trip_request = _find_request_or_raise(db, request_id)
    _find_trip_or_raise(db, trip_request.trip_id)

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

    requester = _ensure_profile_for_user(db, trip_request.requester_user_id, "Solicitante Demo")
    return success_response(_request_payload(trip_request, requester))


@api_router.post(
    "/requests/{request_id}/cancel",
    tags=["requests"],
    response_model=TripRequestEnvelope,
    responses={404: {"model": ApiErrorEnvelope}, 409: {"model": ApiErrorEnvelope}},
)
def cancel_request(request_id: int, db: Session = Depends(get_db)):
    trip_request = _find_request_or_raise(db, request_id)

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
        _recompute_trip_status_by_capacity(db, trip)

    db.commit()
    db.refresh(trip_request)

    requester = _ensure_profile_for_user(db, trip_request.requester_user_id, "Solicitante Demo")
    return success_response(_request_payload(trip_request, requester))


@api_router.get(
    "/requests/mine",
    tags=["requests"],
    response_model=TripRequestsListEnvelope,
)
def list_my_requests(db: Session = Depends(get_db)):
    requester = _ensure_profile_for_user(db, DEFAULT_REQUESTER_USER_ID, "Solicitante Demo")
    rows = db.scalars(
        select(TripRequest)
        .where(TripRequest.requester_user_id == DEFAULT_REQUESTER_USER_ID)
        .order_by(TripRequest.created_at.desc())
    ).all()
    items = [_request_payload(item, requester) for item in rows]
    return success_response({"items": items})
