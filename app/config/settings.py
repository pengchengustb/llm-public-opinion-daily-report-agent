"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the monitoring system."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Public Opinion Daily Report Agent"
    app_version: str = "0.1.0"
    environment: Literal["local", "test", "staging", "production"] = "local"
    log_level: str = "INFO"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    backend_url: str = "http://localhost:8000"

    database_url: str = "sqlite:///./opinion_monitor.db"

    llm_provider: Literal["mock", "openai"] = "mock"
    llm_model: str = "mock-structured-analyzer-v1"
    openai_api_key: str = Field(default="", repr=False)

    @property
    def is_mock_llm(self) -> bool:
        """Return whether the system is configured for deterministic mock analysis."""

        return self.llm_provider == "mock"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()
