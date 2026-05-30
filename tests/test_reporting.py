from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

pytest.importorskip("jinja2")
pytest.importorskip("sqlmodel")

from sqlmodel import Session, SQLModel, select  # noqa: E402

from app.analysis.structured import StructuredAnalysisService  # noqa: E402
from app.core.config import Settings  # noqa: E402
from app.db import models  # noqa: E402, F401
from app.db.models import AnalysisRun, DailyReport, RiskInsight  # noqa: E402
from app.db.repositories import Repository  # noqa: E402
from app.db.seed import seed_sample_data  # noqa: E402
from app.db.session import create_database_engine  # noqa: E402
from app.reporting.service import ReportGenerationService, ReportTraceabilityError  # noqa: E402


def create_memory_session() -> Session:
    engine = create_database_engine(Settings(database_url="sqlite:///:memory:"))
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_report_generation_exports_markdown_html_and_persists_report(tmp_path: Path) -> None:
    with create_memory_session() as session:
        seed_sample_data(session)
        run = StructuredAnalysisService(
            session,
            Settings(llm_mock_mode=True),
        ).analyze_recent_evidence()

        artifacts = ReportGenerationService(
            session,
            Settings(report_output_dir=tmp_path),
        ).generate_daily_report(
            report_date=date(2026, 5, 30),
            analysis_run_id=run.id,
        )

        markdown = artifacts.markdown_path.read_text(encoding="utf-8")
        html = artifacts.html_path.read_text(encoding="utf-8")
        persisted_report = session.exec(select(DailyReport)).one()

        assert artifacts.markdown_path.exists()
        assert artifacts.html_path.exists()
        assert "舆情风险日报 2026-05-30" in markdown
        assert "证据追溯" in markdown
        assert run.id in markdown
        assert "<html" in html
        assert persisted_report.status == "generated"
        assert persisted_report.analysis_run_ids == [run.id]
        assert Path(persisted_report.markdown_path) == artifacts.markdown_path


def test_report_generation_rejects_unresolved_evidence_ids(tmp_path: Path) -> None:
    with create_memory_session() as session:
        run = Repository(session, AnalysisRun).add(
            AnalysisRun(run_type="structured_analysis", status="completed")
        )
        Repository(session, RiskInsight).add(
            RiskInsight(
                analysis_run_id=run.id,
                category="traceability",
                severity="high",
                deterministic_score=88.0,
                llm_explanation="Missing evidence should block the report.",
                uncertainty_score=0.2,
                evidence_ids=["missing-evidence-id"],
            )
        )

        with pytest.raises(ReportTraceabilityError, match="missing-evidence-id"):
            ReportGenerationService(
                session,
                Settings(report_output_dir=tmp_path),
            ).generate_daily_report(analysis_run_id=run.id)
