"""Application configuration.

All settings are loaded from environment variables (and an optional ``.env``
file) using Pydantic v2 settings management. The single ``settings`` instance
exported here is the source of truth for the rest of the application.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from typing import Annotated

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings.

    PostgreSQL is the primary database. When ``DATABASE_URL`` is not provided
    we transparently fall back to a local async SQLite database, which makes
    local development zero-config.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ----------------------------------------------------------------- app
    PROJECT_NAME: str = "LedgerIQ"
    PROJECT_DESCRIPTION: str = "Personal Finance Management Platform"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: Literal["local", "development", "staging", "production"] = "local"
    DEBUG: bool = True
    # When false, the /auth/register endpoint is disabled (single-user lockdown).
    ALLOW_REGISTRATION: bool = True

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    # --------------------------------------------------------------- server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ------------------------------------------------------------------ cors
    # Comma-separated string in the environment, parsed into a list.
    # ``NoDecode`` stops pydantic-settings from JSON-decoding the dotenv value
    # first, so the validator below receives the raw comma-separated string.
    CORS_ORIGINS: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _assemble_cors(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    # ------------------------------------------------------------- database
    # If unset, we build a local SQLite URL from SQLITE_PATH.
    DATABASE_URL: str | None = None
    SQLITE_PATH: str = "./ledgeriq.db"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    @model_validator(mode="after")
    def _build_database_url(self) -> "Settings":
        """Resolve the final async database URL.

        - No URL provided           -> async SQLite fallback.
        - Sync Postgres URL provided -> upgraded to the asyncpg driver.
        - Sync SQLite URL provided   -> upgraded to the aiosqlite driver.
        """
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"sqlite+aiosqlite:///{self.SQLITE_PATH}"
            return self

        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("sqlite://") and "+aiosqlite" not in url:
            url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        self.DATABASE_URL = url
        return self

    @property
    def is_sqlite(self) -> bool:
        return bool(self.DATABASE_URL and self.DATABASE_URL.startswith("sqlite"))

    @property
    def sync_database_url(self) -> str:
        """Synchronous URL (used by tooling that cannot use async drivers)."""
        assert self.DATABASE_URL is not None
        return (
            self.DATABASE_URL.replace("+asyncpg", "")
            .replace("+aiosqlite", "")
        )

    # ------------------------------------------------------------------- jwt
    JWT_SECRET: str = "CHANGE_ME_IN_PRODUCTION_use_a_long_random_string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # -------------------------------------------------------------- locale
    DEFAULT_CURRENCY: str = "INR"
    DEFAULT_LOCALE: str = "en-IN"
    DEFAULT_TIMEZONE: str = "Asia/Kolkata"

    # ---------------------------------------------------- background tasks
    ENABLE_SCHEDULER: bool = True
    # Daily notification scan time (hour, in DEFAULT_TIMEZONE).
    NOTIFICATION_SCAN_HOUR: int = 8
    # Lead time (days) for "due soon" reminders.
    EMI_DUE_REMINDER_DAYS: int = 5

    # -------------------------------------------------------------- LLM (AI)
    # When LLM_API_KEY is unset, both AI services gracefully fall back to the
    # rule-based implementations. The key lives in the backend .env ONLY.
    LLM_PROVIDER: str = "anthropic"
    LLM_API_KEY: str | None = None
    LLM_MODEL: str = "claude-haiku-4-5-20251001"
    LLM_TIMEOUT_SECONDS: float = 20.0
    # Scheduled refresh of LLM insights (only runs when a key is configured).
    LLM_INSIGHTS_ENABLED: bool = True
    LLM_INSIGHTS_DAY_OF_WEEK: str = "mon"
    LLM_INSIGHTS_HOUR: int = 7
    LLM_INSIGHTS_PERIOD: Literal["weekly", "monthly", "yearly"] = "monthly"
    # How long a cached LLM insight set is served before falling back to rules.
    LLM_INSIGHTS_TTL_DAYS: int = 8


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor (instantiated once per process)."""
    return Settings()


settings = get_settings()
