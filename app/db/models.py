"""Database models for the project foundation.

The first PR defines durable entities and relationships without implementing ingestion,
LLM calls, or report generation. Later PRs will add repositories and migrations around
these models.
"""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import Column
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel


class SourceType(StrEnum):
    """Supported source families for future ingestion connectors."""

    rss = "rss"
    news_api = "news_api"
    reddit = "reddit"
    local_json = "local_json"


class AnalysisRunType(StrEnum):
    """Reasons an analysis run can be created."""

    daily = "daily"
    backfill = "backfill"
    evaluation = "evaluation"
    manual = "manual"


class Source(SQLModel, table=True):
    """Configured data source."""

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    name: str = Field(index=True)
    source_type: SourceType = Field(index=True)
    base_url: str | None = None
    config_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    enabled: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
    updated_at: datetime | None = None


class RawDocument(SQLModel, table=True):
    """Source-native document captured before cleaning and deduplication."""

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    source_id: str = Field(foreign_key="source.id", index=True)
    external_id: str | None = Field(default=None, index=True)
    url: str | None = None
    title: str | None = None
    body: str
    author: str | None = None
    published_at: datetime | None = Field(default=None, index=True)
    collected_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
    raw_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))
    content_hash: str = Field(index=True)


class ProcessedDocument(SQLModel, table=True):
    """Normalized document prepared for analysis."""

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    raw_document_id: str = Field(foreign_key="rawdocument.id", index=True)
    canonical_url: str | None = None
    normalized_title: str | None = None
    normalized_text: str
    language: str | None = Field(default=None, index=True)
    token_count: int | None = None
    text_hash: str = Field(index=True)
    duplicate_group_id: str | None = Field(default=None, index=True)
    is_duplicate: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)


class AnalysisRun(SQLModel, table=True):
    """Metadata for a structured analysis execution."""

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    run_type: AnalysisRunType = Field(index=True)
    status: str = Field(default="pending", index=True)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
    completed_at: datetime | None = None
    model_name: str = "mock-structured-analyzer-v1"
    prompt_version: str = "not-yet-implemented"
    mock_mode: bool = True
    input_count: int = 0
    output_count: int = 0
    error_message: str | None = None
