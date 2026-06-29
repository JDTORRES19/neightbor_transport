from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.constants import NOTIFICATION_TYPE_TRIP_FINALIZED
from app.core.exceptions import DomainNotFoundException
from app.core.utils import utc_isoformat
from app.infrastructure.models import Notification, Trip


def notification_payload(notification: Notification) -> dict[str, Any]:
    return {
        "id": notification.id,
        "user_id": notification.user_id,
        "type": notification.type,
        "title": notification.title,
        "body": notification.body,
        "payload": notification.payload or {},
        "is_read": notification.is_read,
        "read_at": utc_isoformat(notification.read_at),
        "created_at": utc_isoformat(notification.created_at),
    }


def create_notification(
    db: Session,
    *,
    user_id: int,
    notification_type: str,
    title: str,
    body: str,
    payload: dict[str, Any] | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        body=body,
        payload=payload or {},
        is_read=False,
    )
    db.add(notification)
    return notification


def create_trip_finalized_notifications(db: Session, trip: Trip, user_ids: set[int]) -> None:
    for user_id in user_ids:
        create_notification(
            db,
            user_id=user_id,
            notification_type=NOTIFICATION_TYPE_TRIP_FINALIZED,
            title="Viaje finalizado",
            body="Tu solicitud fue cerrada por finalizacion del viaje.",
            payload={"trip_id": trip.id, "direction": trip.direction},
        )


def list_notifications(
    db: Session,
    *,
    user_id: int,
    unread_only: bool = False,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Notification], int]:
    safe_page = max(page, 1)
    safe_page_size = max(page_size, 1)
    offset = (safe_page - 1) * safe_page_size

    query = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        query = query.where(Notification.is_read.is_(False))

    rows = db.scalars(
        query.order_by(Notification.created_at.desc()).offset(offset).limit(safe_page_size)
    ).all()

    unread_count = db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
    )
    return rows, int(unread_count or 0)


def mark_notification_as_read(db: Session, *, notification_id: int, user_id: int) -> Notification:
    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    )
    if notification is None:
        raise DomainNotFoundException(
            code="ERR_NOTIFICATION_NOT_FOUND",
            message="Notificacion no encontrada.",
        )

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        db.add(notification)

    return notification


def mark_all_notifications_as_read(db: Session, *, user_id: int) -> int:
    now_utc = datetime.now(timezone.utc)
    result = db.execute(
        update(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        .values(is_read=True, read_at=now_utc)
    )
    return int(result.rowcount or 0)
