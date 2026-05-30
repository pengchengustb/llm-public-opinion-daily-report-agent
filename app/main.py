"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.db.session import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    if settings.create_db_on_startup:
        create_db_and_tables(settings)
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)

    app = FastAPI(
        title=resolved_settings.app_name,
        version=resolved_settings.app_version,
        description="Backend API for public opinion monitoring and daily risk reporting.",
        lifespan=lifespan,
    )
    app.state.settings = resolved_settings

    if resolved_settings.backend_cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=resolved_settings.backend_cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(api_router)
    return app


app = create_app()
