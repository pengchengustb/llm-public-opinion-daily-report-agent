"""Connector contracts and raw ingestion payload schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from pydantic import BaseModel, Field, HttpUrl


class RawArticle(BaseModel):
    external_id: str | None = None
    title: str
    raw_text: str
    url: HttpUrl | None = None
    author: str | None = None
    published_at: datetime | None = None
    engagement: dict[str, Any] = Field(default_factory=dict)


class RawComment(BaseModel):
    external_id: str | None = None
    article_external_id: str | None = None
    raw_text: str
    platform: str | None = None
    author_alias: str | None = None
    published_at: datetime | None = None
    like_count: int = Field(default=0, ge=0)
    reply_count: int = Field(default=0, ge=0)
    share_count: int = Field(default=0, ge=0)


class IngestionPayload(BaseModel):
    source_name: str
    source_type: str
    uri: str | None = None
    articles: list[RawArticle] = Field(default_factory=list)
    comments: list[RawComment] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SourceConnector(Protocol):
    name: str
    source_type: str
    uri: str | None

    def load(self) -> IngestionPayload:
        """Load raw records from the connector source."""


class IngestionSummary(BaseModel):
    source_id: str
    batch_id: str
    inserted_articles: int = 0
    skipped_duplicate_articles: int = 0
    inserted_comments: int = 0
    skipped_duplicate_comments: int = 0
    quality_issue_count: int = 0
    quality_issues_by_severity: dict[str, int] = Field(default_factory=dict)
    quality_issues_by_type: dict[str, int] = Field(default_factory=dict)
