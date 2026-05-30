"""Structured LLM input and output contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    evidence_id: str
    entity_type: Literal["article", "comment"]
    text: str = Field(min_length=1)
    title: str | None = None
    engagement_score: int = Field(default=0, ge=0)


class AnalysisInput(BaseModel):
    evidence_items: list[EvidenceItem] = Field(min_length=1)
    report_language: str = "zh-CN"


class SentimentAnalysisOutput(BaseModel):
    entity_id: str
    entity_type: Literal["article", "comment"]
    label: Literal["positive", "neutral", "negative", "mixed"]
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    evidence_ids: list[str] = Field(default_factory=list)


class ViewpointOutput(BaseModel):
    title: str
    stance: str
    summary: str
    prevalence_score: float = Field(ge=0.0, le=1.0)
    evidence_ids: list[str] = Field(default_factory=list)


class ViewpointExtractionOutput(BaseModel):
    viewpoints: list[ViewpointOutput] = Field(default_factory=list)


class TopicSummaryOutput(BaseModel):
    topic: str
    keywords: list[str] = Field(default_factory=list)
    summary: str
    trend_explanation: str
    evidence_ids: list[str] = Field(default_factory=list)


class RiskClassificationOutput(BaseModel):
    category: str
    severity: Literal["low", "medium", "high", "critical"]
    explanation: str
    uncertainty_score: float = Field(ge=0.0, le=1.0)
    evidence_ids: list[str] = Field(default_factory=list)


class RecommendationOutput(BaseModel):
    action: str
    priority: Literal["low", "medium", "high", "urgent"]
    responsible_role: str
    expected_effect: str
    evidence_ids: list[str] = Field(default_factory=list)


class DailyReportAnalysisOutput(BaseModel):
    executive_summary: str
    key_risks: list[RiskClassificationOutput] = Field(default_factory=list)
    evidence_highlights: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


class StructuredAnalysisOutput(BaseModel):
    sentiments: list[SentimentAnalysisOutput] = Field(default_factory=list)
    viewpoints: list[ViewpointOutput] = Field(default_factory=list)
    topics: list[TopicSummaryOutput] = Field(default_factory=list)
    risks: list[RiskClassificationOutput] = Field(default_factory=list)
    recommendations: list[RecommendationOutput] = Field(default_factory=list)
    daily_report: DailyReportAnalysisOutput
