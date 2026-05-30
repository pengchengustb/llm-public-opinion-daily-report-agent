"""Risk scoring service over persisted analysis outputs."""

from __future__ import annotations

from collections.abc import Sequence

from sqlmodel import Session, col, select

from app.db.models import Article, Comment, RiskInsight, SentimentResult, TopicSummary
from app.risk.scoring import DeterministicRiskScore, RiskSignals, score_risk, sensitive_topic_score


class RiskScoringService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def score_analysis_run(self, analysis_run_id: str) -> list[RiskInsight]:
        sentiments = self.session.exec(
            select(SentimentResult).where(SentimentResult.analysis_run_id == analysis_run_id)
        ).all()
        topics = self.session.exec(
            select(TopicSummary).where(TopicSummary.analysis_run_id == analysis_run_id)
        ).all()
        risks = self.session.exec(
            select(RiskInsight).where(RiskInsight.analysis_run_id == analysis_run_id)
        ).all()

        scoring = self.compute_score(sentiments=sentiments, topics=topics, risks=risks)
        for risk in risks:
            risk.deterministic_score = scoring.score
            risk.severity = max_severity(risk.severity, scoring.severity)
            risk.uncertainty_score = max(risk.uncertainty_score, scoring.signals.uncertainty_score)
            risk.llm_explanation = merge_explanations(risk.llm_explanation, scoring.explanation)
            self.session.add(risk)
        self.session.commit()
        for risk in risks:
            self.session.refresh(risk)
        return risks

    def score_latest_analysis_run(self) -> list[RiskInsight]:
        latest_run_id = self.session.exec(
            select(RiskInsight.analysis_run_id)
            .order_by(col(RiskInsight.created_at).desc())
            .limit(1)
        ).first()
        if latest_run_id is None:
            raise ValueError("No risk insights are available to score.")
        return self.score_analysis_run(latest_run_id)

    def compute_score(
        self,
        sentiments: Sequence[SentimentResult],
        topics: Sequence[TopicSummary],
        risks: Sequence[RiskInsight],
    ) -> DeterministicRiskScore:
        negative_sentiments = [
            sentiment for sentiment in sentiments if sentiment.label in {"negative", "mixed"}
        ]
        negative_ratio = len(negative_sentiments) / len(sentiments) if sentiments else 0.0
        high_engagement_negative_count = self._high_engagement_negative_count(negative_sentiments)
        topic_growth_score = max((topic.growth_score for topic in topics), default=0.0)
        sensitive_score = sensitive_topic_score(self._evidence_texts(sentiments, topics, risks))
        uncertainty = max((risk.uncertainty_score for risk in risks), default=0.0)

        return score_risk(
            RiskSignals(
                negative_ratio=negative_ratio,
                topic_growth_score=topic_growth_score,
                high_engagement_negative_count=high_engagement_negative_count,
                sensitive_topic_score=sensitive_score,
                uncertainty_score=uncertainty,
            )
        )

    def _high_engagement_negative_count(self, sentiments: Sequence[SentimentResult]) -> int:
        count = 0
        for sentiment in sentiments:
            if sentiment.entity_type != "comment":
                continue
            comment = self.session.get(Comment, sentiment.entity_id)
            if comment and comment.like_count + comment.reply_count + comment.share_count >= 10:
                count += 1
        return count

    def _evidence_texts(
        self,
        sentiments: Sequence[SentimentResult],
        topics: Sequence[TopicSummary],
        risks: Sequence[RiskInsight],
    ) -> list[str]:
        texts: list[str] = []
        evidence_ids: set[str] = set()
        for sentiment in sentiments:
            evidence_ids.update(sentiment.evidence_ids)
        for topic in topics:
            evidence_ids.update(topic.evidence_ids)
            texts.extend([topic.topic, topic.summary, topic.trend_explanation or ""])
        for risk in risks:
            evidence_ids.update(risk.evidence_ids)
            texts.extend([risk.category, risk.llm_explanation or ""])

        for evidence_id in evidence_ids:
            article = self.session.get(Article, evidence_id)
            if article:
                texts.extend([article.title, article.cleaned_text or article.raw_text])
                continue
            comment = self.session.get(Comment, evidence_id)
            if comment:
                texts.append(comment.cleaned_text or comment.raw_text)
        return texts


SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def max_severity(left: str, right: str) -> str:
    return left if SEVERITY_RANK.get(left, 0) >= SEVERITY_RANK.get(right, 0) else right


def merge_explanations(llm_explanation: str | None, deterministic_explanation: str) -> str:
    if not llm_explanation:
        return deterministic_explanation
    if "deterministic_score=" in llm_explanation:
        return llm_explanation
    return f"{llm_explanation}\n\nDeterministic risk signals: {deterministic_explanation}"
