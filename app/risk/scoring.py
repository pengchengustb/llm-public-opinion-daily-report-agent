"""Deterministic risk scoring primitives."""

from __future__ import annotations

from dataclasses import dataclass

SENSITIVE_TERMS = {
    "风险",
    "投诉",
    "不稳定",
    "谣言",
    "误导",
    "恐慌",
    "舆情",
    "担心",
    "质疑",
    "risk",
    "complaint",
    "unstable",
    "misinformation",
    "uncertain",
}


@dataclass(frozen=True)
class RiskSignals:
    negative_ratio: float
    topic_growth_score: float
    high_engagement_negative_count: int
    sensitive_topic_score: float
    uncertainty_score: float


@dataclass(frozen=True)
class DeterministicRiskScore:
    score: float
    severity: str
    explanation: str
    signals: RiskSignals


def clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    return max(lower, min(upper, value))


def score_risk(signals: RiskSignals) -> DeterministicRiskScore:
    high_engagement_component = min(signals.high_engagement_negative_count, 5) / 5
    raw_score = (
        signals.negative_ratio * 35
        + (signals.topic_growth_score / 100) * 20
        + high_engagement_component * 20
        + (signals.sensitive_topic_score / 100) * 15
        + signals.uncertainty_score * 10
    )
    score = round(clamp(raw_score), 2)
    severity = severity_for_score(score)
    explanation = (
        f"deterministic_score={score}; "
        f"negative_ratio={signals.negative_ratio:.2f}; "
        f"topic_growth={signals.topic_growth_score:.2f}; "
        f"high_engagement_negative={signals.high_engagement_negative_count}; "
        f"sensitive_topic={signals.sensitive_topic_score:.2f}; "
        f"uncertainty={signals.uncertainty_score:.2f}"
    )
    return DeterministicRiskScore(
        score=score,
        severity=severity,
        explanation=explanation,
        signals=signals,
    )


def severity_for_score(score: float) -> str:
    if score >= 75:
        return "critical"
    if score >= 55:
        return "high"
    if score >= 30:
        return "medium"
    return "low"


def sensitive_topic_score(texts: list[str]) -> float:
    if not texts:
        return 0.0
    combined = "\n".join(text.lower() for text in texts)
    hits = sum(1 for term in SENSITIVE_TERMS if term in combined)
    return round(clamp((hits / max(1, len(SENSITIVE_TERMS))) * 100), 2)
