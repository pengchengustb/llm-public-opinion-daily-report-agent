"""Tests for application settings."""

import pytest

pytest.importorskip("pydantic")
pytest.importorskip("pydantic_settings")

from app.config.settings import Settings  # noqa: E402


def test_default_settings_use_mock_llm() -> None:
    settings = Settings()

    assert settings.is_mock_llm is True
    assert settings.llm_model == "mock-structured-analyzer-v1"
    assert settings.openai_api_key == ""
