"""Typed runtime settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LLM-enhanced Public Opinion Monitoring"
    app_version: str = "0.1.0"
    app_env: str = "local"
    log_level: str = "INFO"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    backend_cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:8501"])

    database_url: str = "sqlite:///./data/generated/opinion_monitor.db"
    create_db_on_startup: bool = True

    dashboard_backend_url: str = "http://localhost:8000"

    llm_provider: str = "openai"
    llm_model: str = "gpt-4.1-mini"
    llm_mock_mode: bool = True
    openai_api_key: SecretStr | None = None

    report_language: str = "zh-CN"
    report_output_dir: Path = Path("reports")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        normalized = value.upper()
        if normalized not in allowed:
            raise ValueError(f"log_level must be one of {sorted(allowed)}")
        return normalized

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if not value.startswith(("sqlite://", "postgresql://", "postgresql+psycopg://")):
            raise ValueError("database_url must use sqlite or postgresql")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()

