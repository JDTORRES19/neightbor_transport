from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import DEFAULT_USER_ID
from app.core.exceptions import DomainNotFoundException
from app.core.utils import normalize_plate
from app.infrastructure.models import Vehicle


def find_vehicle_or_raise(db: Session, vehicle_id: int) -> Vehicle:
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


def is_plate_taken(db: Session, plate: str, exclude_vehicle_id: int | None = None) -> bool:
    normalized = normalize_plate(plate)
    query = select(Vehicle).where(
        Vehicle.plate == normalized,
        Vehicle.is_active.is_(True),
    )
    if exclude_vehicle_id is not None:
        query = query.where(Vehicle.id != exclude_vehicle_id)
    return db.scalar(query) is not None


def vehicle_payload(vehicle: Vehicle) -> dict[str, Any]:
    return {
        "id": vehicle.id,
        "brand": vehicle.brand,
        "reference": vehicle.reference,
        "color": vehicle.color,
        "plate": vehicle.plate,
        "is_active": vehicle.is_active,
    }
