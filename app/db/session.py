"""Database session helpers."""

from collections.abc import Generator

from sqlmodel import Session, SQLModel

from app.db.engine import engine


def init_db() -> None:
    """Create database tables for local development and tests.

    Alembic migrations will be introduced once feature tables stabilize.
    """

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Yield a database session for FastAPI dependencies."""

    with Session(engine) as session:
        yield session
