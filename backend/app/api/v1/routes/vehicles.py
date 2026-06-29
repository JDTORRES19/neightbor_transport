from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.schemas import (
    ApiErrorEnvelope,
    VehicleCreateRequest,
    VehicleEnvelope,
    VehiclesListEnvelope,
    VehicleUpdateRequest,
)
from app.core.constants import DEFAULT_USER_ID
from app.core.exceptions import DomainConflictException
from app.core.responses import success_response
from app.core.utils import normalize_plate
from app.infrastructure.database import get_db
from app.infrastructure.models import Vehicle
from app.services.vehicle_service import find_vehicle_or_raise, is_plate_taken, vehicle_payload

router = APIRouter()


@router.get(
    "/vehicles",
    tags=["vehicles"],
    response_model=VehiclesListEnvelope,
)
def list_vehicles(db: Session = Depends(get_db)):
    items = [
        vehicle_payload(item)
        for item in db.scalars(
            select(Vehicle)
            .where(Vehicle.user_id == DEFAULT_USER_ID)
            .order_by(Vehicle.id.asc())
        ).all()
    ]
    return success_response({"items": items})


@router.post(
    "/vehicles",
    tags=["vehicles"],
    status_code=201,
    response_model=VehicleEnvelope,
    responses={409: {"model": ApiErrorEnvelope}},
)
def create_vehicle(payload: VehicleCreateRequest, db: Session = Depends(get_db)):
    normalized_plate = normalize_plate(payload.plate)
    if is_plate_taken(db, normalized_plate):
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
    return success_response(vehicle_payload(vehicle), status_code=201)


@router.patch(
    "/vehicles/{vehicle_id}",
    tags=["vehicles"],
    response_model=VehicleEnvelope,
    responses={404: {"model": ApiErrorEnvelope}, 409: {"model": ApiErrorEnvelope}},
)
def update_vehicle(vehicle_id: int, payload: VehicleUpdateRequest, db: Session = Depends(get_db)):
    vehicle = find_vehicle_or_raise(db, vehicle_id)

    if payload.plate is not None:
        normalized_plate = normalize_plate(payload.plate)
        if is_plate_taken(db, normalized_plate, exclude_vehicle_id=vehicle_id):
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
    return success_response(vehicle_payload(vehicle))


@router.delete(
    "/vehicles/{vehicle_id}",
    tags=["vehicles"],
    response_model=VehicleEnvelope,
    responses={404: {"model": ApiErrorEnvelope}},
)
def deactivate_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = find_vehicle_or_raise(db, vehicle_id)
    vehicle.is_active = False
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return success_response(vehicle_payload(vehicle))
