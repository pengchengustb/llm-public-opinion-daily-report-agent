from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("sqlmodel")

from sqlmodel import Session, SQLModel, select  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.db import models  # noqa: E402, F401
from app.db.models import EvaluationMetric, EvaluationRun  # noqa: E402
from app.db.session import create_database_engine  # noqa: E402
from app.evaluation.metrics import accuracy, evidence_coverage, macro_f1  # noqa: E402
from app.evaluation.service import EvaluationService  # noqa: E402


def create_memory_session() -> Session:
    engine = create_database_engine(Settings(database_url="sqlite:///:memory:"))
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_metric_helpers_compute_accuracy_macro_f1_and_coverage() -> None:
    expected = ["positive", "negative", "neutral"]
    predicted = ["positive", "negative", "negative"]

    assert accuracy(expected, predicted) == 0.6667
    assert macro_f1(expected, predicted) == 0.5556
    assert evidence_coverage({"a", "b", "missing"}, {"a", "b"}) == 0.6667


def test_mock_evaluation_persists_metrics_and_writes_artifacts(tmp_path: Path) -> None:
    with create_memory_session() as session:
        artifacts = EvaluationService(
            session,
            Settings(report_output_dir=tmp_path),
            output_dir=tmp_path / "evaluation",
        ).run_mock_evaluation()

        runs = session.exec(select(EvaluationRun)).all()
        metrics = session.exec(select(EvaluationMetric)).all()
        report_text = artifacts.report_path.read_text(encoding="utf-8")

        assert runs[0].status == "completed"
        assert len(metrics) == 5
        assert artifacts.metrics["sentiment_accuracy"] == 1.0
        assert artifacts.metrics["evidence_citation_coverage"] == 1.0
        assert artifacts.report_path.exists()
        assert artifacts.metrics_path.exists()
        assert "Evaluation Report" in report_text
        assert "sentiment_accuracy" in report_text
