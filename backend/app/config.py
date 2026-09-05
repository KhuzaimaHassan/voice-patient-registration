"""
app/config.py
-------------
Application settings loaded from environment variables / .env file.
Uses pydantic-settings so every variable is typed and validated at startup.
Reference: docs/05-env-and-secrets.md
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All environment variables the application needs.
    Values are read from the process environment, then fall back to a .env
    file in the working directory (or /backend/.env when running locally).
    """

    # ------------------------------------------------------------------
    # Database — required
    # Must use the asyncpg driver scheme: postgresql+asyncpg://...
    # ------------------------------------------------------------------
    DATABASE_URL: str

    # ------------------------------------------------------------------
    # Vapi — required
    # Webhook secret to verify inbound tool-call requests from Vapi.
    # ------------------------------------------------------------------
    VAPI_WEBHOOK_SECRET: str

    # ------------------------------------------------------------------
    # Application environment — required
    # "development" enables debug logging; "production" uses INFO.
    # ------------------------------------------------------------------
    ENVIRONMENT: Literal["development", "production"] = "production"

    # ------------------------------------------------------------------
    # Logging — optional, default INFO
    # ------------------------------------------------------------------
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # ------------------------------------------------------------------
    # CORS — optional
    # Comma-separated origins, e.g. "https://dashboard.vapi.ai"
    # ------------------------------------------------------------------
    ALLOWED_ORIGINS: str = ""

    # ------------------------------------------------------------------
    # Derived helpers
    # ------------------------------------------------------------------

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse ALLOWED_ORIGINS into a list, filtering empty strings."""
        if not self.ALLOWED_ORIGINS:
            return []
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    model_config = SettingsConfigDict(
        # Look for a .env file relative to the process working directory.
        # Works for both `uvicorn app.main:app` (from /backend) and tests.
        env_file=".env",
        env_file_encoding="utf-8",
        # Extra env vars are ignored rather than raising an error.
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached singleton Settings instance.
    The cache means .env is parsed only once at startup.
    Call get_settings.cache_clear() in tests to reset between cases.
    """
    return Settings()
