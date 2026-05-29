from __future__ import annotations

from datetime import UTC, datetime

import pytest

pytest.importorskip("sqlmodel")

from sqlmodel import Session, SQLModel, select  # noqa: E402

from app.analysis.structured import StructuredAnalysisService  # noqa: E402
from app.core.config import Settings  # noqa: E402
from app.db import models  # noqa: E402, F401
from app.db.models import (  # noqa: E402
    AnalysisRun,
    Article,
    Comment,
    RiskInsight,
    SentimentResult,
    TopicSummary,
)
from app.db.repositories import Repository  # noqa: E402
from app.db.session import create_database_engine  # noqa: E402
from app.risk.scoring import RiskSignals, score_risk, sensitive_topic_score  # noqa: E402
from app.risk.service import RiskScoringService  # noqa: E402


def create_memory_session() -> Session:
    engine = create_database_engine(Settings(database_url="sqlite:///:memory:"))
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_score_risk_combines_required_signals() -> None:
    result = score_risk(
        RiskSignals(
            negative_ratio=0.75,
            topic_growth_score=80.0,
            high_engagement_negative_count=3,
            sensitive_topic_score=60.0,
            uncertainty_score=0.5,
        )
    )

    assert result.score == 68.25
    assert result.severity == "high"
    assert "negative_ratio=0.75" in result.explanation


def test_sensitive_topic_score_detects_uncertainty_terms() -> None:
    score = sensitive_topic_score(["用户担心系统不稳定，并质疑是否存在误导信息。"])

    assert score > 0


def test_risk_scoring_service_updates_persisted_risk_insight() -> None:
    with create_memory_session() as session:
        article = Repository(session, Article).add(
            Article(
                title="公共服务风险受到关注",
                published_at=datetime.now(UTC),
                raw_text="用户担心服务不稳定，并持续讨论投诉处理进展。",
                cleaned_text="用户担心服务不稳定，并持续讨论投诉处理进展。",
                language="zh-CN",
                content_hash="risk-article-hash-000000000000000000000000000000000000000001",
            )
        )
        comment = Repository(session, Comment).add(
            Comment(
                article_id=article.id,
                platform="demo_forum",
                raw_text="高峰期系统不稳定让人担心。",
                cleaned_text="高峰期系统不稳定让人担心。",
                language="zh-CN",
                content_hash="risk-comment-hash-000000000000000000000000000000000000000001",
                like_count=20,
                reply_count=4,
                share_count=2,
            )
        )
        run = Repository(session, AnalysisRun).add(
            AnalysisRun(run_type="structured_analysis", status="running")
        )
        Repository(session, SentimentResult).add(
            SentimentResult(
                analysis_run_id=run.id,
                entity_type="comment",
                entity_id=comment.id,
                label="negative",
                confidence=0.9,
                rationale="担心不稳定。",
                evidence_ids=[comment.id],
            )
        )
        Repository(session, TopicSummary).add(
            TopicSummary(
                analysis_run_id=run.id,
                topic="系统稳定性",
                summary="投诉和不稳定讨论增长。",
                growth_score=80.0,
                evidence_ids=[article.id, comment.id],
            )
        )
        risk = Repository(session, RiskInsight).add(
            RiskInsight(
                analysis_run_id=run.id,
                category="service_stability",
                severity="medium",
                deterministic_score=0.0,
                llm_explanation="LLM mock explanation.",
                uncertainty_score=0.3,
                evidence_ids=[article.id, comment.id],
            )
        )

        scored = RiskScoringService(session).score_analysis_run(run.id)

        refreshed = session.get(RiskInsight, risk.id)
        assert scored[0].id == risk.id
        assert refreshed.deterministic_score > 50
        assert refreshed.severity in {"high", "critical"}
        assert "deterministic_score=" in refreshed.llm_explanation


def test_structured_analysis_service_applies_deterministic_risk_score() -> None:
    with create_memory_session() as session:
        article = Repository(session, Article).add(
            Article(
                title="服务稳定性引发担心",
                raw_text="部分用户担心系统不稳定，也认可效率有所提升。",
                cleaned_text="部分用户担心系统不稳定，也认可效率有所提升。",
                language="zh-CN",
                content_hash="structured-risk-article-hash-00000000000000000000000000000001",
            )
        )

        run = StructuredAnalysisService(session, Settings(llm_mock_mode=True)).analyze_evidence(
            articles=[article],
            comments=[],
        )
        risk = session.exec(select(RiskInsight).where(RiskInsight.analysis_run_id == run.id)).one()

        assert risk.deterministic_score > 0
        assert run.runtime_metadata["deterministic_risk_scores"] == [risk.deterministic_score]
