from fastapi import APIRouter

from app.api.routes import dashboard, health, placeholders

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(placeholders.router, prefix="/api/v1", tags=["roadmap"])
api_router.include_router(dashboard.router, prefix="/api/v1", tags=["dashboard"])
