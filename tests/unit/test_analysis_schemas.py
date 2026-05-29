"""Tests for structured analysis schema validation."""

import pytest

pydantic = pytest.importorskip("pydantic")

from pydantic import ValidationError  # noqa: E402

from app.schemas.analysis import StructuredAnalysisOutput  # noqa: E402


def test_structured_analysis_requires_traceable_sentiment_source() -> None:
    output = StructuredAnalysisOutput(
        document_id="processed-1",
        summary="Residents raised concerns about service reliability.",
        sentiment={
            "label": "negative",
            "confidence": 0.8,
            "rationale": "The source expresses concern.",
            "source_document_ids": ["raw-1"],
        },
        viewpoints=[],
        risks=[],
    )

    assert output.sentiment.source_document_ids == ["raw-1"]


def test_structured_analysis_rejects_missing_sentiment_sources() -> None:
    with pytest.raises(ValidationError):
        StructuredAnalysisOutput(
            document_id="processed-1",
            summary="Residents raised concerns.",
            sentiment={
                "label": "negative",
                "confidence": 0.8,
                "rationale": "The source expresses concern.",
                "source_document_ids": [],
            },
        )
