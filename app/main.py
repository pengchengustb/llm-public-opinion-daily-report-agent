"""FastAPI application entrypoint."""

import uvicorn
from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.config.settings import get_settings
from app.db.session import init_db
from app.utils.logging import configure_logging


def create_app() -> FastAPI:
    """Create and configure the backend application."""

    settings = get_settings()
    configure_logging(settings)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Backend API for public opinion monitoring and daily risk reporting.",
    )
    app.include_router(health_router)

    @app.on_event("startup")
    def on_startup() -> None:
        init_db()

    return app


app = create_app()


def run() -> None:
    """Run the backend with uvicorn for local script entrypoints."""

    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.api_host, port=settings.api_port, reload=False)
