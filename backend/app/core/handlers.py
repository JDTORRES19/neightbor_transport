import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import BaseDomainException
from app.core.responses import error_response

logger = logging.getLogger(__name__)


def _request_id_from_request(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


async def handle_domain_exception(request: Request, exc: BaseDomainException):
    request_id = _request_id_from_request(request)
    logger.info(
        "domain_error code=%s status=%s request_id=%s path=%s",
        exc.code,
        exc.http_status,
        request_id,
        request.url.path,
    )
    return error_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.http_status,
        details=exc.details,
        request_id=request_id,
    )


async def handle_http_exception(request: Request, exc: StarletteHTTPException):
    request_id = _request_id_from_request(request)
    status = exc.status_code
    return error_response(
        code=f"ERR_HTTP_{status}",
        message=str(exc.detail),
        status_code=status,
        request_id=request_id,
    )


async def handle_validation_exception(request: Request, exc: RequestValidationError):
    request_id = _request_id_from_request(request)
    return error_response(
        code="ERR_REQUEST_VALIDATION",
        message="Solicitud invalida.",
        status_code=422,
        details={"errors": exc.errors()},
        request_id=request_id,
    )


async def handle_unhandled_exception(request: Request, exc: Exception):
    request_id = _request_id_from_request(request)
    logger.exception("unhandled_error request_id=%s path=%s", request_id, request.url.path)
    return error_response(
        code="ERR_INTERNAL_SERVER_ERROR",
        message="Error interno del servidor.",
        status_code=500,
        request_id=request_id,
    )
