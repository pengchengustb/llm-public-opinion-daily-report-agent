from __future__ import annotations

import pytest

pytest.importorskip("pydantic")
pytest.importorskip("sqlmodel")

from sqlmodel import Session, SQLModel, select  # noqa: E402

from app.analysis.structured import StructuredAnalysisService, build_analysis_input  # noqa: E402
from app.core.config import Settings  # noqa: E402
from app.db import models  # noqa: E402, F401
from app.db.models import (  # noqa: E402
    AnalysisRun,
    Recommendation,
    RiskInsight,
    SentimentResult,
    TopicSummary,
    Viewpoint,
)
from app.db.seed import seed_sample_data  # noqa: E402
from app.db.session import create_database_engine  # noqa: E402
from app.llm.client import MockLLMClient, OpenAILLMClient, build_llm_client  # noqa: E402
from app.llm.contracts import AnalysisInput, EvidenceItem  # noqa: E402


def create_memory_session() -> Session:
    engine = create_database_engine(Settings(database_url="sqlite:///:memory:"))
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_mock_llm_client_returns_traceable_structured_outputs() -> None:
    client = MockLLMClient()
    output = client.analyze(
        AnalysisInput(
            evidence_items=[
                EvidenceItem(
                    evidence_id="comment-1",
                    entity_type="comment",
                    text="用户担心系统高峰期不稳定，但认可服务效率有所提升。",
                    engagement_score=10,
                )
            ]
        )
    )

    assert output.sentiments[0].label == "mixed"
    assert output.sentiments[0].evidence_ids == ["comment-1"]
    assert output.risks[0].evidence_ids == ["comment-1"]
    assert output.recommendations[0].responsible_role == "communications"
    assert output.daily_report.recommended_actions


def test_build_llm_client_keeps_real_openai_calls_disabled() -> None:
    mock_client = build_llm_client(Settings(llm_mock_mode=True))
    openai_client = build_llm_client(Settings(llm_mock_mode=False, openai_api_key="unit-test-key"))

    assert isinstance(mock_client, MockLLMClient)
    assert isinstance(openai_client, OpenAILLMClient)
    with pytest.raises(NotImplementedError):
        openai_client.analyze(
            AnalysisInput(
                evidence_items=[
                    EvidenceItem(evidence_id="article-1", entity_type="article", text="sample")
                ]
            )
        )


def test_structured_analysis_service_persists_mock_outputs() -> None:
    with create_memory_session() as session:
        seed_sample_data(session)
        run = StructuredAnalysisService(
            session,
            Settings(llm_mock_mode=True),
        ).analyze_recent_evidence()

        sentiment_results = session.exec(select(SentimentResult)).all()
        viewpoints = session.exec(select(Viewpoint)).all()
        topics = session.exec(select(TopicSummary)).all()
        risks = session.exec(select(RiskInsight)).all()
        recommendations = session.exec(select(Recommendation)).all()
        analysis_runs = session.exec(select(AnalysisRun)).all()

        assert run.status == "completed"
        assert run.mock_mode is True
        assert run.prompt_version == "structured-analysis-v0.1-mock-ready"
        assert len(analysis_runs) == 1
        assert len(sentiment_results) == 2
        assert len(viewpoints) == 1
        assert len(topics) == 1
        assert len(risks) == 1
        assert len(recommendations) == 1
        assert sentiment_results[0].evidence_ids
        assert risks[0].llm_explanation


def test_build_analysis_input_rejects_empty_evidence() -> None:
    with pytest.raises(ValueError):
        build_analysis_input([], [])
