"""Core domain schemas shared across API, services, and future LLM contracts."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl


class SentimentLabel(StrEnum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"
    mixed = "mixed"


class RiskSeverity(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class EvidenceReference(BaseModel):
    source_id: str | None = None
    article_id: str | None = None
    comment_id: str | None = None
    quote: str | None = Field(default=None, max_length=500)


class ArticleSchema(BaseModel):
    id: str
    source_id: str | None = None
    title: str = Field(min_length=1, max_length=500)
    url: HttpUrl | None = None
    author: str | None = None
    published_at: datetime | None = None
    collected_at: datetime
    raw_text: str = Field(min_length=1)
    cleaned_text: str | None = None
    language: str | None = Field(default=None, max_length=20)
    content_hash: str = Field(min_length=16, max_length=128)
    engagement: dict[str, Any] = Field(default_factory=dict)


class CommentSchema(BaseModel):
    id: str
    article_id: str | None = None
    platform: str | None = None
    author_alias: str | None = None
    published_at: datetime | None = None
    raw_text: str = Field(min_length=1)
    cleaned_text: str | None = None
    language: str | None = Field(default=None, max_length=20)
    content_hash: str = Field(min_length=16, max_length=128)
    like_count: int = Field(default=0, ge=0)
    reply_count: int = Field(default=0, ge=0)
    share_count: int = Field(default=0, ge=0)


class AnalysisRunSchema(BaseModel):
    id: str
    run_type: Literal["sentiment", "viewpoint", "topic", "risk", "daily_report", "evaluation"]
    status: Literal["pending", "running", "completed", "failed"]
    provider: str
    model_name: str
    mock_mode: bool = True
    prompt_version: str | None = None
    input_start_date: date | None = None
    input_end_date: date | None = None
    runtime_metadata: dict[str, Any] = Field(default_factory=dict)


class SentimentResultSchema(BaseModel):
    id: str
    analysis_run_id: str
    entity_type: Literal["article", "comment"]
    entity_id: str
    label: SentimentLabel
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    evidence_ids: list[str] = Field(default_factory=list)


class ViewpointSchema(BaseModel):
    id: str
    analysis_run_id: str
    title: str
    stance: str
    summary: str
    prevalence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_ids: list[str] = Field(default_factory=list)


class RiskInsightSchema(BaseModel):
    id: str
    analysis_run_id: str
    category: str
    severity: RiskSeverity
    deterministic_score: float = Field(ge=0.0, le=100.0)
    llm_explanation: str | None = None
    uncertainty_score: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_ids: list[str] = Field(default_factory=list)


class DailyReportSchema(BaseModel):
    id: str
    report_date: date
    status: Literal["draft", "generated", "failed", "archived"]
    title: str
    summary: str
    markdown_path: str | None = None
    html_path: str | None = None
    pdf_path: str | None = None
    analysis_run_ids: list[str] = Field(default_factory=list)

