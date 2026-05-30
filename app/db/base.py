"""Shared SQLModel base helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class TimestampMixin(SQLModel):
    created_at: datetime = Field(default_factory=utc_now, index=True)
    updated_at: datetime = Field(default_factory=utc_now)


class UUIDModel(SQLModel):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)

