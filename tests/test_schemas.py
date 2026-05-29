from __future__ import annotations

from datetime import UTC, datetime

import pytest

pytest.importorskip("pydantic")

from app.llm.contracts import DailyReportAnalysisOutput, SentimentAnalysisOutput  # noqa: E402
from app.schemas.domain import ArticleSchema, SentimentLabel, SentimentResultSchema  # noqa: E402


def test_article_schema_requires_traceable_content() -> None:
    article = ArticleSchema(
        id="article-1",
        title="Public service update draws attention",
        collected_at=datetime.now(UTC),
        raw_text="Residents discussed the policy update online.",
        content_hash="a" * 64,
    )

    assert article.id == "article-1"
    assert article.content_hash == "a" * 64


def test_sentiment_schema_uses_bounded_confidence() -> None:
    result = SentimentResultSchema(
        id="sentiment-1",
        analysis_run_id="run-1",
        entity_type="article",
        entity_id="article-1",
        label=SentimentLabel.negative,
        confidence=0.76,
        rationale="Evidence indicates concern.",
        evidence_ids=["article-1"],
    )

    assert result.label == SentimentLabel.negative
    assert result.evidence_ids == ["article-1"]


def test_llm_contracts_require_structured_output() -> None:
    output = SentimentAnalysisOutput(
        entity_id="comment-1",
        entity_type="comment",
        label="mixed",
        confidence=0.5,
        rationale="样例中同时包含支持和担忧。",
        evidence_ids=["article-1", "comment-1"],
    )
    report = DailyReportAnalysisOutput(
        executive_summary="当前为模拟输出。",
        key_risks=[],
        evidence_highlights=["article-1"],
        recommended_actions=["继续监测。"],
    )

    assert output.label == "mixed"
    assert report.recommended_actions
