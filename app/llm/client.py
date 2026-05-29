"""LLM client boundary with deterministic mock behavior.

Real provider calls must stay isolated in this module. PR #4 adds the abstraction and
mock implementation, but still refuses to perform real OpenAI calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.core.config import Settings
from app.llm.contracts import (
    AnalysisInput,
    DailyReportAnalysisOutput,
    RecommendationOutput,
    RiskClassificationOutput,
    SentimentAnalysisOutput,
    StructuredAnalysisOutput,
    TopicSummaryOutput,
    ViewpointOutput,
)

NEGATIVE_TERMS = {
    "担心",
    "质疑",
    "风险",
    "不满",
    "投诉",
    "延误",
    "不稳定",
    "uncertain",
    "worry",
    "risk",
    "complaint",
    "delay",
}
POSITIVE_TERMS = {"提升", "改善", "平稳", "支持", "满意", "stable", "improve", "support"}
SENSITIVE_TERMS = {"稳定", "投诉", "风险", "舆情", "misinformation", "uncertain"}


class LLMClient(Protocol):
    provider_name: str
    model_name: str
    mock_mode: bool

    def analyze(self, analysis_input: AnalysisInput) -> StructuredAnalysisOutput:
        """Return structured public opinion analysis."""

    def analyze_daily_report(self, evidence_text: str) -> DailyReportAnalysisOutput:
        """Return structured report analysis for supplied evidence text."""


@dataclass(frozen=True)
class MockLLMClient:
    language: str = "zh-CN"
    provider_name: str = "mock"
    model_name: str = "mock-structured-analysis-v1"
    mock_mode: bool = True

    def analyze(self, analysis_input: AnalysisInput) -> StructuredAnalysisOutput:
        sentiments = [self._sentiment_for_item(item) for item in analysis_input.evidence_items]
        evidence_ids = [item.evidence_id for item in analysis_input.evidence_items]
        negative_count = sum(1 for sentiment in sentiments if sentiment.label == "negative")
        severity = "medium" if negative_count else "low"

        viewpoint = ViewpointOutput(
            title="服务体验与风险关注",
            stance="mixed" if negative_count else "observational",
            summary="公众反馈集中在服务体验、稳定性和信息透明度，需要结合后续数据持续观察。",
            prevalence_score=min(1.0, max(0.2, len(evidence_ids) / 10)),
            evidence_ids=evidence_ids[:5],
        )
        topic = TopicSummaryOutput(
            topic="公共服务反馈",
            keywords=["服务体验", "稳定性", "信息透明度"],
            summary="样例证据显示，讨论主要围绕公共服务运行效果与潜在风险。",
            trend_explanation="当前为 mock 模式，趋势解释基于输入证据数量和关键词规则生成。",
            evidence_ids=evidence_ids[:5],
        )
        risk = RiskClassificationOutput(
            category="public_service_reputation",
            severity=severity,
            explanation="检测到负面或不确定表达时，应关注公共服务口碑风险和沟通透明度。",
            uncertainty_score=0.35 if negative_count else 0.2,
            evidence_ids=evidence_ids[:5],
        )
        recommendation = RecommendationOutput(
            action="发布清晰的进度说明，并持续跟踪高互动负面反馈。",
            priority="medium" if negative_count else "low",
            responsible_role="communications",
            expected_effect="降低信息不确定性，提升公众对处理进展的理解。",
            evidence_ids=evidence_ids[:5],
        )
        daily_report = DailyReportAnalysisOutput(
            executive_summary="当前为 mock 分析模式，已基于结构化证据生成可追溯的舆情摘要。",
            key_risks=[risk],
            evidence_highlights=evidence_ids[:5],
            recommended_actions=[recommendation.action],
        )
        return StructuredAnalysisOutput(
            sentiments=sentiments,
            viewpoints=[viewpoint],
            topics=[topic],
            risks=[risk],
            recommendations=[recommendation],
            daily_report=daily_report,
        )

    def analyze_daily_report(self, evidence_text: str) -> DailyReportAnalysisOutput:
        analysis_input = AnalysisInput(
            evidence_items=[
                {
                    "evidence_id": "inline-evidence",
                    "entity_type": "article",
                    "text": evidence_text,
                }
            ],
            report_language=self.language,
        )
        return self.analyze(analysis_input).daily_report

    def _sentiment_for_item(self, item) -> SentimentAnalysisOutput:
        text = item.text.lower()
        negative_hits = sum(1 for term in NEGATIVE_TERMS if term in text)
        positive_hits = sum(1 for term in POSITIVE_TERMS if term in text)
        sensitive_hits = sum(1 for term in SENSITIVE_TERMS if term in text)

        if negative_hits and positive_hits:
            label = "mixed"
            confidence = 0.68
            rationale = "证据同时包含积极变化和担忧表达。"
        elif negative_hits or sensitive_hits >= 2:
            label = "negative"
            confidence = 0.74
            rationale = "证据包含担忧、风险或不稳定相关表达。"
        elif positive_hits:
            label = "positive"
            confidence = 0.7
            rationale = "证据包含改善、支持或运行平稳相关表达。"
        else:
            label = "neutral"
            confidence = 0.62
            rationale = "证据未呈现明显正向或负向倾向。"

        return SentimentAnalysisOutput(
            entity_id=item.evidence_id,
            entity_type=item.entity_type,
            label=label,
            confidence=confidence,
            rationale=rationale,
            evidence_ids=[item.evidence_id],
        )


@dataclass(frozen=True)
class OpenAILLMClient:
    model_name: str
    api_key_configured: bool
    provider_name: str = "openai"
    mock_mode: bool = False

    def analyze(self, analysis_input: AnalysisInput) -> StructuredAnalysisOutput:
        raise NotImplementedError("Real OpenAI structured analysis is planned for a later PR.")

    def analyze_daily_report(self, evidence_text: str) -> DailyReportAnalysisOutput:
        raise NotImplementedError("Real OpenAI structured analysis is planned for a later PR.")


def build_llm_client(settings: Settings) -> LLMClient:
    if settings.llm_mock_mode:
        return MockLLMClient(language=settings.report_language)
    return OpenAILLMClient(
        model_name=settings.llm_model,
        api_key_configured=settings.openai_api_key is not None,
    )
