from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

pytest.importorskip("sqlmodel")

from sqlmodel import Session, SQLModel  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.db import models  # noqa: E402, F401
from app.db.models import (  # noqa: E402
    AnalysisRun,
    Article,
    Comment,
    DailyReport,
    EvaluationMetric,
    EvaluationRun,
    IngestionBatch,
    Recommendation,
    RiskInsight,
    SentimentResult,
    Source,
    TopicSummary,
    Viewpoint,
)
from app.db.repositories import (  # noqa: E402
    Repository,
    get_article_by_content_hash,
    list_reports_by_date,
)
from app.db.seed import seed_sample_data  # noqa: E402
from app.db.session import create_database_engine  # noqa: E402


def create_memory_session() -> Session:
    engine = create_database_engine(Settings(database_url="sqlite:///:memory:"))
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_domain_tables_cover_pr2_persistence_scope() -> None:
    expected_tables = {
        "sources",
        "ingestion_batches",
        "articles",
        "comments",
        "data_quality_records",
        "analysis_runs",
        "sentiment_results",
        "viewpoints",
        "topic_summaries",
        "risk_insights",
        "recommendations",
        "reports",
        "evaluation_runs",
        "evaluation_metrics",
    }

    assert expected_tables.issubset(SQLModel.metadata.tables.keys())


def test_repository_persists_traceable_analysis_workflow() -> None:
    with create_memory_session() as session:
        source = Repository(session, Source).add(
            Source(
                name="Demo Source",
                source_type="local_json",
                uri="data/samples/opinion_sample.json",
            )
        )
        batch = Repository(session, IngestionBatch).add(
            IngestionBatch(
                source_id=source.id,
                status="completed",
                connector_name="local_json",
                article_count=1,
                comment_count=1,
            )
        )
        article = Repository(session, Article).add(
            Article(
                source_id=source.id,
                title="Public service platform upgrade",
                published_at=datetime.now(UTC),
                raw_text="Residents discussed service quality and stability.",
                cleaned_text="Residents discussed service quality and stability.",
                language="en",
                content_hash="article-hash-00000000000000000000000000000000000000000001",
            )
        )
        comment = Repository(session, Comment).add(
            Comment(
                article_id=article.id,
                platform="demo_forum",
                raw_text="The peak-hour stability still worries me.",
                cleaned_text="Peak-hour stability worries me.",
                language="en",
                content_hash="comment-hash-00000000000000000000000000000000000000000001",
                like_count=7,
            )
        )
        run = Repository(session, AnalysisRun).add(
            AnalysisRun(
                run_type="daily_report",
                status="completed",
                provider="mock",
                model_name="mock",
                mock_mode=True,
                prompt_version="test-v1",
            )
        )
        sentiment = Repository(session, SentimentResult).add(
            SentimentResult(
                analysis_run_id=run.id,
                entity_type="comment",
                entity_id=comment.id,
                label="negative",
                confidence=0.82,
                rationale="Concern about stability.",
                evidence_ids=[comment.id],
            )
        )
        viewpoint = Repository(session, Viewpoint).add(
            Viewpoint(
                analysis_run_id=run.id,
                title="Stability concern",
                stance="concerned",
                summary="Users worry about peak-hour reliability.",
                prevalence_score=0.4,
                evidence_ids=[comment.id],
            )
        )
        topic = Repository(session, TopicSummary).add(
            TopicSummary(
                analysis_run_id=run.id,
                topic="platform stability",
                summary="Stability is a recurring concern.",
                keywords=["stability", "peak hour"],
                growth_score=12.0,
                evidence_ids=[article.id, comment.id],
            )
        )
        risk = Repository(session, RiskInsight).add(
            RiskInsight(
                analysis_run_id=run.id,
                category="service_stability",
                severity="medium",
                deterministic_score=55.0,
                llm_explanation="Mock explanation.",
                uncertainty_score=0.2,
                evidence_ids=[comment.id],
            )
        )
        recommendation = Repository(session, Recommendation).add(
            Recommendation(
                risk_insight_id=risk.id,
                action="Publish peak-hour stability notice.",
                priority="medium",
                responsible_role="operations",
                expected_effect="Reduce uncertainty.",
                evidence_ids=[comment.id],
            )
        )
        report = Repository(session, DailyReport).add(
            DailyReport(
                report_date=date(2026, 5, 29),
                status="generated",
                title="Daily Public Opinion Risk Report",
                summary="Stability concern requires monitoring.",
                analysis_run_ids=[run.id],
            )
        )
        evaluation_run = Repository(session, EvaluationRun).add(
            EvaluationRun(
                benchmark_name="mock-sentiment",
                status="completed",
                artifact_path="data/generated/evaluation/mock.json",
            )
        )
        metric = Repository(session, EvaluationMetric).add(
            EvaluationMetric(
                evaluation_run_id=evaluation_run.id,
                metric_name="accuracy",
                metric_value=1.0,
            )
        )

        assert batch.source_id == source.id
        assert get_article_by_content_hash(session, article.content_hash).id == article.id
        assert sentiment.evidence_ids == [comment.id]
        assert viewpoint.analysis_run_id == run.id
        assert topic.evidence_ids == [article.id, comment.id]
        assert recommendation.risk_insight_id == risk.id
        assert list_reports_by_date(session, date(2026, 5, 29))[0].id == report.id
        assert metric.evaluation_run_id == evaluation_run.id


def test_seed_sample_data_is_idempotent() -> None:
    with create_memory_session() as session:
        first = seed_sample_data(session)
        second = seed_sample_data(session)

        assert first == {
            "inserted_sources": 1,
            "inserted_articles": 1,
            "inserted_comments": 1,
        }
        assert second == {
            "inserted_sources": 0,
            "inserted_articles": 0,
            "inserted_comments": 0,
        }
        assert len(Repository(session, Article).list()) == 1
        assert len(Repository(session, Comment).list()) == 1
