"""Structured analysis schemas for future LLM and baseline outputs."""

from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class SentimentLabel(StrEnum):
    """Supported sentiment labels for public opinion documents."""

    positive = "positive"
    negative = "negative"
    neutral = "neutral"
    mixed = "mixed"
    uncertain = "uncertain"


class RiskCategory(StrEnum):
    """Initial risk taxonomy used across prompts, storage, reports, and evaluation."""

    reputation = "reputation"
    policy = "policy"
    safety = "safety"
    legal = "legal"
    financial = "financial"
    service_quality = "service_quality"
    misinformation = "misinformation"
    social_unrest = "social_unrest"
    equity = "equity"
    environmental = "environmental"
    other = "other"


class EvidenceReference(BaseModel):
    """Evidence reference that grounds a model conclusion in source data."""

    source_document_id: str = Field(min_length=1)
    quote: str | None = None
    relevance_score: float | None = Field(default=None, ge=0.0, le=1.0)


class SentimentResult(BaseModel):
    """Validated sentiment conclusion with required source traceability."""

    label: SentimentLabel
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    source_document_ids: list[str] = Field(min_length=1)


class ViewpointResult(BaseModel):
    """Extracted viewpoint or claim with evidence."""

    claim: str = Field(min_length=1)
    stance: str = Field(min_length=1)
    target: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[EvidenceReference] = Field(min_length=1)


class RiskFindingResult(BaseModel):
    """Risk conclusion with severity, likelihood, rationale, and evidence."""

    risk_category: RiskCategory
    risk_statement: str = Field(min_length=1)
    severity: int = Field(ge=1, le=5)
    likelihood: int = Field(ge=1, le=5)
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(min_length=1)
    evidence: list[EvidenceReference] = Field(min_length=1)


class StructuredAnalysisOutput(BaseModel):
    """Top-level structured output expected from future LLM analysis."""

    document_id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    sentiment: SentimentResult
    viewpoints: list[ViewpointResult] = Field(default_factory=list)
    risks: list[RiskFindingResult] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)

    @field_validator("viewpoints", "risks")
    @classmethod
    def keep_lists_bounded(cls, value: list[object]) -> list[object]:
        """Prevent unbounded model outputs from entering persistence later."""

        if len(value) > 20:
            raise ValueError("structured analysis lists must contain at most 20 items")
        return value
