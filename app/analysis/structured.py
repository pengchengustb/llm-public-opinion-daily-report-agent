"""Structured analysis orchestration over persisted evidence."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Session, select

from app.core.config import Settings, get_settings
from app.db.models import (
    AnalysisRun,
    Article,
    Comment,
    Recommendation,
    RiskInsight,
    SentimentResult,
    TopicSummary,
    Viewpoint,
)
from app.db.repositories import Repository
from app.llm.client import LLMClient, build_llm_client
from app.llm.contracts import AnalysisInput, EvidenceItem, StructuredAnalysisOutput
from app.llm.prompts import STRUCTURED_ANALYSIS_PROMPT_VERSION
from app.risk.service import RiskScoringService


def build_analysis_input(
    articles: list[Article],
    comments: list[Comment],
    report_language: str = "zh-CN",
) -> AnalysisInput:
    evidence_items: list[EvidenceItem] = []
    for article in articles:
        evidence_items.append(
            EvidenceItem(
                evidence_id=article.id,
                entity_type="article",
                title=article.title,
                text=article.cleaned_text or article.raw_text,
                engagement_score=int(article.engagement.get("views", 0))
                + int(article.engagement.get("shares", 0)),
            )
        )
    for comment in comments:
        evidence_items.append(
            EvidenceItem(
                evidence_id=comment.id,
                entity_type="comment",
                text=comment.cleaned_text or comment.raw_text,
                engagement_score=comment.like_count + comment.reply_count + comment.share_count,
            )
        )
    return AnalysisInput(evidence_items=evidence_items, report_language=report_language)


class StructuredAnalysisService:
    def __init__(
        self,
        session: Session,
        settings: Settings | None = None,
        client: LLMClient | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.client = client or build_llm_client(self.settings)

    def analyze_recent_evidence(self, limit: int = 50) -> AnalysisRun:
        articles = self.session.exec(select(Article).limit(limit)).all()
        comments = self.session.exec(select(Comment).limit(limit)).all()
        if not articles and not comments:
            raise ValueError("No articles or comments are available for analysis.")
        return self.analyze_evidence(articles=articles, comments=comments)

    def analyze_evidence(self, articles: list[Article], comments: list[Comment]) -> AnalysisRun:
        analysis_run = Repository(self.session, AnalysisRun).add(
            AnalysisRun(
                run_type="structured_analysis",
                status="running",
                provider=self.client.provider_name,
                model_name=self.client.model_name,
                mock_mode=self.client.mock_mode,
                prompt_version=STRUCTURED_ANALYSIS_PROMPT_VERSION,
                runtime_metadata={
                    "article_count": len(articles),
                    "comment_count": len(comments),
                    "started_at": datetime.now(UTC).isoformat(),
                },
            )
        )

        analysis_input = build_analysis_input(
            articles,
            comments,
            report_language=self.settings.report_language,
        )
        output = self.client.analyze(analysis_input)
        self._persist_output(analysis_run.id, output)
        scored_risks = RiskScoringService(self.session).score_analysis_run(analysis_run.id)

        analysis_run.status = "completed"
        analysis_run.runtime_metadata = {
            **analysis_run.runtime_metadata,
            "completed_at": datetime.now(UTC).isoformat(),
            "sentiment_count": len(output.sentiments),
            "risk_count": len(scored_risks),
            "deterministic_risk_scores": [risk.deterministic_score for risk in scored_risks],
        }
        self.session.add(analysis_run)
        self.session.commit()
        self.session.refresh(analysis_run)
        return analysis_run

    def _persist_output(self, analysis_run_id: str, output: StructuredAnalysisOutput) -> None:
        sentiment_repo = Repository(self.session, SentimentResult)
        viewpoint_repo = Repository(self.session, Viewpoint)
        topic_repo = Repository(self.session, TopicSummary)
        risk_repo = Repository(self.session, RiskInsight)
        recommendation_repo = Repository(self.session, Recommendation)

        for sentiment in output.sentiments:
            sentiment_repo.add(
                SentimentResult(
                    analysis_run_id=analysis_run_id,
                    entity_type=sentiment.entity_type,
                    entity_id=sentiment.entity_id,
                    label=sentiment.label,
                    confidence=sentiment.confidence,
                    rationale=sentiment.rationale,
                    evidence_ids=sentiment.evidence_ids,
                )
            )

        for viewpoint in output.viewpoints:
            viewpoint_repo.add(
                Viewpoint(
                    analysis_run_id=analysis_run_id,
                    title=viewpoint.title,
                    stance=viewpoint.stance,
                    summary=viewpoint.summary,
                    prevalence_score=viewpoint.prevalence_score,
                    evidence_ids=viewpoint.evidence_ids,
                )
            )

        for topic in output.topics:
            topic_repo.add(
                TopicSummary(
                    analysis_run_id=analysis_run_id,
                    topic=topic.topic,
                    summary=topic.summary,
                    keywords=topic.keywords,
                    trend_explanation=topic.trend_explanation,
                    evidence_ids=topic.evidence_ids,
                )
            )

        persisted_risks: list[RiskInsight] = []
        for risk in output.risks:
            persisted_risks.append(
                risk_repo.add(
                    RiskInsight(
                        analysis_run_id=analysis_run_id,
                        category=risk.category,
                        severity=risk.severity,
                        deterministic_score=0.0,
                        llm_explanation=risk.explanation,
                        uncertainty_score=risk.uncertainty_score,
                        evidence_ids=risk.evidence_ids,
                    )
                )
            )

        primary_risk_id = persisted_risks[0].id if persisted_risks else None
        for recommendation in output.recommendations:
            if primary_risk_id is None:
                continue
            recommendation_repo.add(
                Recommendation(
                    risk_insight_id=primary_risk_id,
                    action=recommendation.action,
                    priority=recommendation.priority,
                    responsible_role=recommendation.responsible_role,
                    expected_effect=recommendation.expected_effect,
                    evidence_ids=recommendation.evidence_ids,
                )
            )
