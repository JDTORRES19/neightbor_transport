from typing import Any

from sqlalchemy.orm import Session

from app.core.constants import (
    AUDIT_ACTION_FINALIZE_TRIP_AUTOMATIC,
    AUDIT_ACTION_FINALIZE_TRIP_MANUAL,
    AUDIT_ACTOR_SYSTEM,
    AUDIT_ACTOR_USER,
    AUDIT_SOURCE_BACKEND,
    AUDIT_SOURCE_SCHEDULER,
    TRIP_STATUS_FINALIZED,
)
from app.infrastructure.models import AuditEvent, Trip


def record_audit_event(
    db: Session,
    *,
    entity_type: str,
    entity_id: int,
    action: str,
    previous_state: str | None,
    new_state: str | None,
    actor_type: str,
    actor_user_id: int | None,
    source: str,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        previous_state=previous_state,
        new_state=new_state,
        actor_type=actor_type,
        actor_user_id=actor_user_id,
        source=source,
        event_metadata=metadata or {},
    )
    db.add(event)
    return event


def record_manual_trip_finalized_audit(
    db: Session,
    *,
    trip: Trip,
    previous_state: str,
    actor_user_id: int,
    impacted_requests_count: int,
) -> AuditEvent:
    return record_audit_event(
        db,
        entity_type="trip",
        entity_id=trip.id,
        action=AUDIT_ACTION_FINALIZE_TRIP_MANUAL,
        previous_state=previous_state,
        new_state=TRIP_STATUS_FINALIZED,
        actor_type=AUDIT_ACTOR_USER,
        actor_user_id=actor_user_id,
        source=AUDIT_SOURCE_BACKEND,
        metadata={
            "impacted_requests_count": impacted_requests_count,
            "direction": trip.direction,
        },
    )


def record_automatic_trip_finalized_audit(
    db: Session,
    *,
    trip: Trip,
    previous_state: str,
    impacted_requests_count: int,
    job_run_id: int,
) -> AuditEvent:
    return record_audit_event(
        db,
        entity_type="trip",
        entity_id=trip.id,
        action=AUDIT_ACTION_FINALIZE_TRIP_AUTOMATIC,
        previous_state=previous_state,
        new_state=TRIP_STATUS_FINALIZED,
        actor_type=AUDIT_ACTOR_SYSTEM,
        actor_user_id=None,
        source=AUDIT_SOURCE_SCHEDULER,
        metadata={
            "impacted_requests_count": impacted_requests_count,
            "direction": trip.direction,
            "job_run_id": job_run_id,
        },
    )
