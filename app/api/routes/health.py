from datetime import UTC, datetime

from fastapi import APIRouter, Request

from app.schemas.health import HealthCheck

router = APIRouter()


@router.get("/health", response_model=HealthCheck)
def health_check(request: Request) -> HealthCheck:
    settings = request.app.state.settings
    return HealthCheck(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        timestamp=datetime.now(UTC),
    )

