from __future__ import annotations

import pytest

pydantic_settings = pytest.importorskip("pydantic_settings")

from app.core.config import Settings  # noqa: E402


def test_settings_defaults_are_development_safe() -> None:
    settings = Settings()

    assert settings.llm_mock_mode is True
    assert settings.openai_api_key is None
    assert settings.database_url.startswith("sqlite:///")
    assert settings.report_language == "zh-CN"


def test_settings_accept_postgresql_url() -> None:
    settings = Settings(database_url="postgresql://user:pass@localhost:5432/opinion")

    assert settings.database_url.startswith("postgresql://")


def test_invalid_log_level_is_rejected() -> None:
    with pytest.raises(ValueError):
        Settings(log_level="verbose")

