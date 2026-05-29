"""Database engine factory."""

from sqlmodel import create_engine

from app.config.settings import Settings, get_settings


def build_engine(settings: Settings | None = None):
    """Build a SQLModel engine from settings."""

    resolved = settings or get_settings()
    connect_args = (
        {"check_same_thread": False}
        if resolved.database_url.startswith("sqlite")
        else {}
    )
    return create_engine(resolved.database_url, echo=False, connect_args=connect_args)


engine = build_engine()
