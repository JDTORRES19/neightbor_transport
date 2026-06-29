from fastapi import APIRouter

from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.metrics import router as metrics_router
from app.api.v1.routes.notifications import router as notifications_router
from app.api.v1.routes.profile import router as profile_router
from app.api.v1.routes.requests import router as requests_router
from app.api.v1.routes.trips import router as trips_router
from app.api.v1.routes.vehicles import router as vehicles_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(profile_router)
api_router.include_router(vehicles_router)
api_router.include_router(trips_router)
api_router.include_router(requests_router)
api_router.include_router(notifications_router)
api_router.include_router(metrics_router)
