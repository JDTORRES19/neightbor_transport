from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.telemetry import endpoint_latency_snapshot
from app.core.utils import utc_isoformat
from app.infrastructure.models import AuditEvent, Notification, SchedulerJobRun, Trip, TripRequest


def _count_by_status(rows: list[tuple[str, int]]) -> dict[str, int]:
    return {status: int(total) for status, total in rows}


def metrics_overview_payload(
    db: Session,
    *,
    latency_window_seconds: int = 300,
    latency_limit: int = 12,
) -> dict[str, Any]:
    trip_status_rows = db.execute(
        select(Trip.status, func.count(Trip.id)).group_by(Trip.status)
    ).all()

    request_status_rows = db.execute(
        select(TripRequest.status, func.count(TripRequest.id)).group_by(TripRequest.status)
    ).all()

    total_notifications = int(db.scalar(select(func.count(Notification.id))) or 0)
    unread_notifications = int(
        db.scalar(
            select(func.count(Notification.id)).where(Notification.is_read.is_(False))
        )
        or 0
    )

    total_audit_events = int(db.scalar(select(func.count(AuditEvent.id))) or 0)

    last_scheduler_run = db.scalar(
        select(SchedulerJobRun)
        .order_by(SchedulerJobRun.started_at.desc(), SchedulerJobRun.id.desc())
        .limit(1)
    )

    last_scheduler_payload: dict[str, Any] | None = None
    if last_scheduler_run is not None:
        last_scheduler_payload = {
            "id": last_scheduler_run.id,
            "job_name": last_scheduler_run.job_name,
            "status": last_scheduler_run.status,
            "processed_count": last_scheduler_run.processed_count,
            "started_at": utc_isoformat(last_scheduler_run.started_at),
            "finished_at": utc_isoformat(last_scheduler_run.finished_at),
        }

    return {
        "trips_by_status": _count_by_status(trip_status_rows),
        "requests_by_status": _count_by_status(request_status_rows),
        "total_notifications": total_notifications,
        "unread_notifications": unread_notifications,
        "total_audit_events": total_audit_events,
        "last_scheduler_run": last_scheduler_payload,
        "latency_window_seconds": max(1, latency_window_seconds),
        "endpoint_latency_ms": endpoint_latency_snapshot(
            limit=latency_limit,
            window_seconds=latency_window_seconds,
        ),
    }
