"""Database engine and session helpers."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy.engine import Engine, make_url
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import Settings, get_settings


def ensure_sqlite_parent_directory(database_url: str) -> None:
    """Create the parent directory for file-based SQLite databases."""
    url = make_url(database_url)
    if url.drivername != "sqlite" or not url.database or url.database == ":memory:":
        return

    database_path = Path(url.database)
    parent = database_path.parent
    if str(parent) not in {"", "."}:
        parent.mkdir(parents=True, exist_ok=True)


def create_database_engine(settings: Settings | None = None) -> Engine:
    resolved = settings or get_settings()
    ensure_sqlite_parent_directory(resolved.database_url)
    connect_args = (
        {"check_same_thread": False}
        if resolved.database_url.startswith("sqlite")
        else {}
    )
    engine_kwargs = {"connect_args": connect_args, "echo": False}
    if resolved.database_url == "sqlite:///:memory:":
        engine_kwargs["poolclass"] = StaticPool
    return create_engine(resolved.database_url, **engine_kwargs)


def create_db_and_tables(settings: Settings | None = None) -> None:
    from app.db import models  # noqa: F401

    engine = create_database_engine(settings)
    try:
        SQLModel.metadata.create_all(engine)
    finally:
        engine.dispose()


def get_session() -> Generator[Session, None, None]:
    engine = create_database_engine()
    try:
        with Session(engine) as session:
            yield session
    finally:
        engine.dispose()
