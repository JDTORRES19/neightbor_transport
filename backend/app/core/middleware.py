import uuid
from time import perf_counter

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.request_context import set_request_id
from app.core.telemetry import record_request_latency


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        set_request_id(request_id)

        started = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (perf_counter() - started) * 1000
            record_request_latency(request.method, request.url.path, 500, duration_ms)
            raise

        duration_ms = (perf_counter() - started) * 1000
        record_request_latency(request.method, request.url.path, response.status_code, duration_ms)
        response.headers["X-Request-ID"] = request_id
        return response
