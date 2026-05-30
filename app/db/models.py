"""SQLModel persistence models for the public opinion monitoring domain."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import Column
from sqlalchemy.types import JSON
from sqlmodel import Field

from app.db.base import TimestampMixin, UUIDModel, utc_now


class Source(UUIDModel, TimestampMixin, table=True):
    __tablename__ = "sources"

    name: str = Field(index=True, max_length=255)
    source_type: str = Field(index=True, max_length=50)
    uri: str | None = Field(default=None, max_length=2048)
    trust_tier: str = Field(default="unrated", max_length=50)
    enabled: bool = Field(default=True)
    source_metadata: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))


class IngestionBatch(UUIDModel, TimestampMixin, table=True):
    __tablename__ = "ingestion_batches"

    source_id: str | None = Field(default=None, foreign_key="sources.id", index=True)
    status: str = Field(default="pending", index=True, max_length=50)
    connector_name: str = Field(max_length=100)
    started_at: datetime = Field(default_factory=utc_now, index=True)
    finished_at: datetime | None = Field(default=None, index=True)
    article_count: int = Field(default=0, ge=0)
    comment_count: int = Field(default=0, ge=0)
    failure_count: int = Field(default=0, ge=0)
    failure_summary: str | None = None
    batch_metadata: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))


class Article(UUIDModel, TimestampMixin, table=True):
    __tablename__ = "articles"

    source_id: str | None = Field(default=None, foreign_key="sources.id", index=True)
    title: str = Field(max_length=500)
    url: str | None = Field(default=None, max_length=2048)
    author: str | None = Field(default=None, max_length=255)
    published_at: datetime | None = Field(default=None, index=True)
    collected_at: datetime = Field(default_factory=utc_now, index=True)
    raw_text: str
    cleaned_text: str | None = None
    language: str | None = Field(default=None, max_length=20)
    content_hash: str = Field(index=True, max_length=128)
    engagement: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))


class Comment(UUIDModel, TimestampMixin, table=True):
    __tablename__ = "comments"

    article_id: str | None = Field(default=None, foreign_key="articles.id", index=True)
    platform: str | None = Field(default=None, index=True, max_length=100)
    author_alias: str | None = Field(default=None, max_length=255)
    published_at: datetime | None = Field(default=None, index=True)
    raw_text: str
    cleaned_text: str | None = None
    language: str | None = Field(default=None, max_length=20)
    content_hash: str = Field(index=True, max_length=128)
    like_count: int = 0
    reply_count: int = 0
    share_count: int = 0


class DataQualityRecord(UUIDModel, TimestampMixin, table=True):
    __tablename__ = "data_quality_records"

    ingestion_batch_id: str | None = Field(
        default=None,
        foreign_key="ingestion_batches.id",
        index=True,
    )
    entity_type: str = Field(index=True, max_length=50)
    entity_id: str | None = Field(default=None, index=True, max_length=64)
    issue_type: str = Field(index=True, max_length=100)
    severity: str = Field(default="info", index=True, max_length=50)
    message: str


class AnalysisRun(UUIDModel, TimestampMixin, table=True):
    __tablename__ = "analysis_runs"

    run_type: str = Field(index=True, max_length=100)
    status: str = Field(default="pending", index=True, max_length=50)
    provider: str = Field(default="mock", max_length=100)
    model_name: str = Field(default="mock", max_length=255)
    mock_mode: bool = Field(default=True)
    prompt_version: str | None = Field(default=None, max_length=100)
    input_start_date: date | None = Field(default=None, index=True)
    input_end_date: date | None = Field(default=None, index=True)
    runtime_metadata: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))


class SentimentResult(UUIDModel, TimestampMixin, table=True):
    __tablename__ = "sentiment_results"

    analysis_run_id: str = Field(foreign_key="analysis_runs.id", index=True)
    entity_type: str = Field(index=True, max_length=50)
    entity_id: str = Field(index=True, max_length=64)
    label: str = Field(index=True, max_length=50)
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    evidence_ids: list[str] = Field(default_factory=list, sa_column=Column(JSON))


class Viewpoint(UUIDModel, TimestampMixin, table=True):
    __tablename__ = "viewpoints"

    analysis_run_id: str = Field(foreign_key="analysis_runs.id", index=True)
    title: str = Field(index=True, max_length=255)
    stance: str = Field(max_length=100)
    summary: str
    prevalence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_ids: list[str] = Field(default_factory=list, sa_column=Column(JSON))


class TopicSummary(UUIDModel, TimestampMixin, table=True):
    __tablename__ = "topic_summaries"

    analysis_run_id: str = Field(foreign_key="analysis_runs.id", index=True)
    topic: str = Field(index=True, max_length=255)
    summary: str
    keywords: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    growth_score: float = Field(default=0.0, ge=0.0, le=100.0)
    trend_explanation: str | None = None
    evidence_ids: list[str] = Field(default_factory=list, sa_column=Column(JSON))


class RiskInsight(UUIDModel, TimestampMixin, table=True):
    __tablename__ = "risk_insights"

    analysis_run_id: str = Field(foreign_key="analysis_runs.id", index=True)
    category: str = Field(index=True, max_length=100)
    severity: str = Field(index=True, max_length=50)
    deterministic_score: float = Field(default=0.0, ge=0.0, le=100.0)
    llm_explanation: str | None = None
    uncertainty_score: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_ids: list[str] = Field(default_factory=list, sa_column=Column(JSON))


class Recommendation(UUIDModel, TimestampMixin, table=True):
    __tablename__ = "recommendations"

    risk_insight_id: str = Field(foreign_key="risk_insights.id", index=True)
    action: str
    priority: str = Field(index=True, max_length=50)
    responsible_role: str = Field(max_length=100)
    expected_effect: str
    evidence_ids: list[str] = Field(default_factory=list, sa_column=Column(JSON))


class DailyReport(UUIDModel, TimestampMixin, table=True):
    __tablename__ = "reports"

    report_date: date = Field(index=True)
    status: str = Field(default="draft", index=True, max_length=50)
    title: str = Field(max_length=255)
    summary: str
    markdown_path: str | None = Field(default=None, max_length=1024)
    html_path: str | None = Field(default=None, max_length=1024)
    pdf_path: str | None = Field(default=None, max_length=1024)
    analysis_run_ids: list[str] = Field(default_factory=list, sa_column=Column(JSON))


class EvaluationRun(UUIDModel, TimestampMixin, table=True):
    __tablename__ = "evaluation_runs"

    benchmark_name: str = Field(index=True, max_length=255)
    status: str = Field(default="pending", index=True, max_length=50)
    provider: str = Field(default="mock", max_length=100)
    model_name: str = Field(default="mock", max_length=255)
    mock_mode: bool = Field(default=True)
    artifact_path: str | None = Field(default=None, max_length=1024)
    started_at: datetime = Field(default_factory=utc_now, index=True)
    finished_at: datetime | None = Field(default=None, index=True)
    run_metadata: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))


class EvaluationMetric(UUIDModel, TimestampMixin, table=True):
    __tablename__ = "evaluation_metrics"

    evaluation_run_id: str = Field(foreign_key="evaluation_runs.id", index=True)
    metric_name: str = Field(index=True, max_length=255)
    metric_value: float
    metric_metadata: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
