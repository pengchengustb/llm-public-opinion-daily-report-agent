from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

pytest.importorskip("sqlmodel")

from sqlmodel import Session, SQLModel, select  # noqa: E402

from app.automation.daily import AutomationRunError, DailyAutomationService  # noqa: E402
from app.core.config import Settings  # noqa: E402
from app.db import models  # noqa: E402, F401
from app.db.models import AnalysisRun, DailyReport  # noqa: E402
from app.db.session import create_database_engine  # noqa: E402


def create_memory_session() -> Session:
    engine = create_database_engine(Settings(database_url="sqlite:///:memory:"))
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_daily_automation_runs_seed_analysis_scoring_and_report(tmp_path: Path) -> None:
    with create_memory_session() as session:
        settings = Settings(report_output_dir=tmp_path)

        result = DailyAutomationService(
            session,
            settings,
            log_dir=tmp_path / "automation_logs",
        ).run(
            report_date=date(2026, 5, 30),
            seed_sample=True,
        )

        reports = session.exec(select(DailyReport)).all()
        runs = session.exec(select(AnalysisRun)).all()

        assert result.status == "completed"
        assert result.analysis_run_id == runs[0].id
        assert result.report_id == reports[0].id
        assert Path(result.markdown_path).exists()
        assert Path(result.html_path).exists()
        assert Path(result.log_path).exists()
        assert [step.status for step in result.steps] == [
            "completed",
            "completed",
            "completed",
            "completed",
        ]
        assert "python -m app run-daily" in result.replay_commands[0]


def test_daily_automation_logs_failed_step(tmp_path: Path) -> None:
    with create_memory_session() as session:
        service = DailyAutomationService(
            session,
            Settings(report_output_dir=tmp_path),
            log_dir=tmp_path / "automation_logs",
        )

        with pytest.raises(AutomationRunError) as exc_info:
            service.run(report_date=date(2026, 5, 30), seed_sample=False)

        result = exc_info.value.result
        assert result.status == "failed"
        assert result.steps[-1].name == "analyze_recent_evidence"
        assert result.steps[-1].status == "failed"
        assert "No articles or comments" in result.steps[-1].error
        assert Path(result.log_path).exists()
