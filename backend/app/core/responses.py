from typing import Any

from fastapi.responses import JSONResponse

from app.core.request_context import get_request_id


def success_response(data: Any, status_code: int = 200) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"ok": True, "data": data})


def error_response(
    code: str,
    message: str,
    status_code: int,
    details: dict | None = None,
    request_id: str | None = None,
) -> JSONResponse:
    rid = request_id or get_request_id()
    payload = {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "request_id": rid,
        },
    }
    return JSONResponse(status_code=status_code, content=payload)
