from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.schemas import (
    ApiErrorEnvelope,
    NotificationEnvelope,
    NotificationsListEnvelope,
    ReadAllNotificationsEnvelope,
)
from app.core.constants import DEFAULT_REQUESTER_USER_ID
from app.core.responses import success_response
from app.infrastructure.database import get_db
from app.services.notification_service import (
    list_notifications,
    mark_all_notifications_as_read,
    mark_notification_as_read,
    notification_payload,
)

router = APIRouter()


@router.get(
    "/notifications",
    tags=["notifications"],
    response_model=NotificationsListEnvelope,
)
def list_my_notifications(
    unread_only: bool = False,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    rows, unread_count = list_notifications(
        db,
        user_id=DEFAULT_REQUESTER_USER_ID,
        unread_only=unread_only,
        page=page,
        page_size=page_size,
    )
    return success_response(
        {
            "items": [notification_payload(item) for item in rows],
            "unread_count": unread_count,
        }
    )


@router.post(
    "/notifications/{notification_id}/read",
    tags=["notifications"],
    response_model=NotificationEnvelope,
    responses={404: {"model": ApiErrorEnvelope}},
)
def read_notification(notification_id: int, db: Session = Depends(get_db)):
    notification = mark_notification_as_read(
        db,
        notification_id=notification_id,
        user_id=DEFAULT_REQUESTER_USER_ID,
    )
    db.commit()
    db.refresh(notification)
    return success_response(notification_payload(notification))


@router.post(
    "/notifications/read-all",
    tags=["notifications"],
    response_model=ReadAllNotificationsEnvelope,
)
def read_all_notifications(db: Session = Depends(get_db)):
    updated_count = mark_all_notifications_as_read(db, user_id=DEFAULT_REQUESTER_USER_ID)
    db.commit()
    return success_response({"updated_count": updated_count})
