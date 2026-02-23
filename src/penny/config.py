"""
config.py — Application Configuration
──────────────────────────────────────
Pydantic Settings-based configuration with automatic .env loading,
type validation, and sensible defaults.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed, validated application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Gemini API ────────────────────────────────────────────────────────
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-pro"
    gemini_max_tokens: int = 8192
    gemini_temperature: float = Field(default=0.3, ge=0.0, le=2.0)

    # ── Application ───────────────────────────────────────────────────────
    app_title: str = "AI Financial Advisor"
    app_env: str = "development"
    log_level: str = "INFO"
    cache_ttl_seconds: int = 300

    # ── Data ──────────────────────────────────────────────────────────────
    data_source: str = "user_input"
    alpha_vantage_key: str = ""

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, v: str) -> str:
        v = v.upper()
        if v not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            raise ValueError(f"Invalid log level: {v}")
        return v

    @property
    def has_api_key(self) -> bool:
        """Return True if a real Gemini API key is configured."""
        return bool(self.gemini_api_key) and self.gemini_api_key != "your_google_gemini_api_key_here"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached singleton Settings instance."""
    return Settings()


def setup_logging(settings: Settings | None = None) -> logging.Logger:
    """Configure application-wide logging and return the 'penny' logger."""
    if settings is None:
        settings = get_settings()

    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )
    return logging.getLogger("penny")


logger = setup_logging()
