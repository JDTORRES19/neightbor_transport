from fastapi import APIRouter

from app.api.v1.schemas import ApiErrorEnvelope, HealthSuccessEnvelope
from app.core.exceptions import DomainConflictException
from app.core.responses import success_response

router = APIRouter()


@router.get(
    "/health",
    tags=["health"],
    response_model=HealthSuccessEnvelope,
    responses={500: {"model": ApiErrorEnvelope}},
)
def api_healthcheck():
    return success_response({"status": "ok", "service": "web"})


@router.get(
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
