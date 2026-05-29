"""Tests for database model metadata."""

import pytest

sqlmodel = pytest.importorskip("sqlmodel")

from sqlmodel import SQLModel, create_engine  # noqa: E402

from app.db.models import AnalysisRun, AnalysisRunType, Source, SourceType  # noqa: E402


def test_sqlmodel_tables_can_be_created() -> None:
    engine = create_engine("sqlite:///:memory:")

    SQLModel.metadata.create_all(engine)

    assert Source(name="Example RSS", source_type=SourceType.rss, config_json={}).enabled is True
    assert AnalysisRun(run_type=AnalysisRunType.daily).mock_mode is True
