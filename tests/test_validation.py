from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

pytest.importorskip("sqlmodel")

from sqlmodel import Session, SQLModel  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.db import models  # noqa: E402, F401
from app.db.session import create_database_engine  # noqa: E402
from app.validation.demo import DemoValidationService  # noqa: E402


def create_memory_session() -> Session:
    engine = create_database_engine(Settings(database_url="sqlite:///:memory:"))
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_demo_validation_runs_full_deterministic_workflow(tmp_path: Path) -> None:
    with create_memory_session() as session:
        result = DemoValidationService(
            session,
            Settings(report_output_dir=tmp_path),
            output_dir=tmp_path / "validation",
        ).run(report_date=date(2026, 5, 30))

        assert result.status == "passed"
        assert result.analysis_run_id
        assert result.report_id
        assert result.evaluation_run_id
        assert Path(result.validation_report_path).exists()
        assert all(check.status == "passed" for check in result.checks)
