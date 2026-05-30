from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlmodel")

from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.db.session import create_db_and_tables  # noqa: E402
from app.main import create_app  # noqa: E402


def test_health_endpoint_returns_service_metadata() -> None:
    settings = Settings(
        database_url="sqlite:///:memory:",
        create_db_on_startup=False,
    )
    client = TestClient(create_app(settings))

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == settings.app_name
    assert payload["environment"] == "local"


def test_database_startup_creates_missing_sqlite_parent_directory(tmp_path) -> None:
    runtime_dir = tmp_path / "test-db-startup"
    database_path = runtime_dir / "nested" / "opinion.db"

    create_db_and_tables(Settings(database_url=f"sqlite:///{database_path}"))

    assert database_path.exists()
