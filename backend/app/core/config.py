"""Application configuration via Pydantic Settings.

All secrets and environment-specific values must come from environment
variables or a local .env file. Never hardcode credentials.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "COBBS Intelligence"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"
    secret_key: str = Field(..., min_length=32)

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # Database
    database_url: str = "postgresql+asyncpg://cobbs:cobbs@localhost:5432/cobbs"
    database_url_sync: str = "postgresql://cobbs:cobbs@localhost:5432/cobbs"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # AI
    ai_mode: Literal["FREE_FIRST", "PREMIUM"] = "FREE_FIRST"
    xai_api_key: str | None = None
    xai_base_url: str = "https://api.x.ai/v1"
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    google_api_key: str | None = None
    groq_api_key: str | None = None
    openrouter_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"
    ai_token_budget_daily: int = 100_000
    ai_spend_budget_daily_usd: float = 10.0

    # Security / limits
    max_tool_calls_per_request: int = 20
    request_timeout_seconds: int = 60
    worker_concurrency: int = 4

    # Observability
    otel_exporter_otlp_endpoint: str | None = None
    otel_service_name: str = "cobbs-intelligence"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance. Call get_settings.cache_clear() in tests if needed."""
    return Settings()
