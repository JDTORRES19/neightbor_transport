from datetime import datetime, timedelta, timezone
import logging

from sqlalchemy import select

from app.core.constants import (
    ACTIVE_TRIP_STATUSES,
    AUTO_FINALIZE_GRACE_MINUTES,
    AUTO_FINALIZE_JOB_NAME,
    SCHEDULER_DEFAULT_INTERVAL_SECONDS,
    SCHEDULER_JOB_STATUS_FAILED,
    SCHEDULER_JOB_STATUS_RUNNING,
    SCHEDULER_JOB_STATUS_SUCCESS,
)
from app.infrastructure.database import SessionLocal
from app.infrastructure.models import SchedulerJobRun, Trip
from app.services.audit_service import record_automatic_trip_finalized_audit
from app.services.notification_service import create_trip_finalized_notifications
from app.services.trip_service import finalize_trip_and_close_requests

logger = logging.getLogger(__name__)


def run_auto_finalize_trips_job(now_utc: datetime | None = None) -> dict[str, int | str]:
    now = now_utc or datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=AUTO_FINALIZE_GRACE_MINUTES)

    processed_count = 0
    failed_count = 0
    latest_error: str | None = None

    with SessionLocal() as db:
        job_run = SchedulerJobRun(
            job_name=AUTO_FINALIZE_JOB_NAME,
            started_at=now,
            status=SCHEDULER_JOB_STATUS_RUNNING,
            processed_count=0,
        )
        db.add(job_run)
        db.flush()

        due_trip_ids = db.scalars(
            select(Trip.id).where(
                Trip.status.in_(ACTIVE_TRIP_STATUSES),
                Trip.departure_at <= cutoff,
            )
        ).all()

        for trip_id in due_trip_ids:
            try:
                with db.begin_nested():
                    trip = db.scalar(
                        select(Trip)
                        .where(Trip.id == trip_id)
                        .with_for_update(skip_locked=True)
                    )
                    if trip is None or trip.status not in ACTIVE_TRIP_STATUSES:
                        continue

                    previous_state = trip.status
                    impacted_users = finalize_trip_and_close_requests(db, trip, now_utc=now)
                    create_trip_finalized_notifications(db, trip, impacted_users)
                    record_automatic_trip_finalized_audit(
                        db,
                        trip=trip,
                        previous_state=previous_state,
                        impacted_requests_count=len(impacted_users),
                        job_run_id=job_run.id,
                    )
                    processed_count += 1
            except Exception as exc:  # pragma: no cover
                failed_count += 1
                latest_error = str(exc)
                logger.exception("Auto-finalize failed for trip_id=%s", trip_id)

        job_run.finished_at = datetime.now(timezone.utc)
        job_run.processed_count = processed_count
        if failed_count > 0:
            job_run.status = SCHEDULER_JOB_STATUS_FAILED
            job_run.error_detail = latest_error
        else:
            job_run.status = SCHEDULER_JOB_STATUS_SUCCESS

        db.add(job_run)
        db.commit()

    return {
        "processed_count": processed_count,
        "failed_count": failed_count,
        "status": SCHEDULER_JOB_STATUS_FAILED if failed_count > 0 else SCHEDULER_JOB_STATUS_SUCCESS,
    }


async def scheduler_loop(interval_seconds: int = SCHEDULER_DEFAULT_INTERVAL_SECONDS) -> None:
    import asyncio

    while True:
        await asyncio.sleep(max(interval_seconds, 1))
        run_auto_finalize_trips_job()
