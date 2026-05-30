from __future__ import annotations

from datetime import date

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlmodel")

from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import Session  # noqa: E402

from app.analysis.structured import StructuredAnalysisService  # noqa: E402
from app.core.config import Settings  # noqa: E402
from app.db.seed import seed_sample_data  # noqa: E402
from app.db.session import create_database_engine, create_db_and_tables  # noqa: E402
from app.main import create_app  # noqa: E402
from app.reporting.service import ReportGenerationService  # noqa: E402


def test_dashboard_summary_returns_latest_analysis_and_report(tmp_path) -> None:
    database_path = tmp_path / "dashboard.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        report_output_dir=tmp_path / "reports",
        create_db_on_startup=False,
    )
    create_db_and_tables(settings)
    engine = create_database_engine(settings)
    try:
        with Session(engine) as session:
            seed_sample_data(session)
            run = StructuredAnalysisService(session, settings).analyze_recent_evidence()
            run_id = run.id
            ReportGenerationService(session, settings).generate_daily_report(
                report_date=date(2026, 5, 30),
                analysis_run_id=run_id,
            )
    finally:
        engine.dispose()

    client = TestClient(create_app(settings))
    response = client.get("/api/v1/dashboard/summary?report_date=2026-05-30")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["latest_analysis_run"]["id"] == run_id
    assert payload["metrics"]["risk_count"] == 1
    assert payload["metrics"]["report_count"] == 1
    assert payload["risks"][0]["deterministic_score"] > 0
    assert payload["topics"]
    assert payload["evidence"]
    assert payload["reports"][0]["analysis_run_ids"] == [run_id]


def test_dashboard_summary_handles_empty_database(tmp_path) -> None:
    database_path = tmp_path / "empty-dashboard.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        create_db_on_startup=False,
    )
    create_db_and_tables(settings)
    client = TestClient(create_app(settings))

    response = client.get("/api/v1/dashboard/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "empty"
    assert payload["latest_analysis_run"] is None
    assert payload["risks"] == []
