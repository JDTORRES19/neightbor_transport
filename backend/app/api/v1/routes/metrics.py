from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.schemas import MetricsOverviewEnvelope
from app.core.responses import success_response
from app.infrastructure.database import get_db
from app.services.metrics_service import metrics_overview_payload

router = APIRouter()


@router.get(
    "/metrics/overview",
    tags=["metrics"],
    response_model=MetricsOverviewEnvelope,
)
def metrics_overview(
    window_seconds: int = Query(default=300, ge=1, le=3600),
    limit: int = Query(default=12, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return success_response(
        metrics_overview_payload(
            db,
            latency_window_seconds=window_seconds,
            latency_limit=limit,
        )
    )
