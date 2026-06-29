import asyncio
from contextlib import suppress
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.exceptions import BaseDomainException
from app.core.handlers import (
    handle_domain_exception,
    handle_http_exception,
    handle_unhandled_exception,
    handle_validation_exception,
)
from app.core.middleware import RequestIdMiddleware
from app.core.settings import get_settings
from app.infrastructure.database import init_db
from app.services.scheduler_service import scheduler_loop


settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    scheduler_task = None
    if settings.enable_scheduler:
        scheduler_task = asyncio.create_task(
            scheduler_loop(interval_seconds=settings.scheduler_interval_seconds)
        )

    try:
        yield
    finally:
        if scheduler_task is not None:
            scheduler_task.cancel()
            with suppress(asyncio.CancelledError):
                await scheduler_task


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_docs else None,
    lifespan=lifespan,
)

app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(BaseDomainException, handle_domain_exception)
app.add_exception_handler(StarletteHTTPException, handle_http_exception)
app.add_exception_handler(RequestValidationError, handle_validation_exception)
app.add_exception_handler(Exception, handle_unhandled_exception)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": "web"}
