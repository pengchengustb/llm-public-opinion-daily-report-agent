"""Common Pydantic schemas shared by API responses and internal services."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """Health check response returned by the backend."""

    status: str = "ok"
    service: str
    version: str
    environment: str


class RunStatus(StrEnum):
    """Lifecycle states for ingestion, analysis, evaluation, and report runs."""

    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class TimestampedSchema(BaseModel):
    """Base schema for API models carrying creation/update timestamps."""

    model_config = ConfigDict(from_attributes=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None
