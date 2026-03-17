"""
PMW Agents — Application Settings

Single source of truth for all configuration. Uses pydantic-settings to load
from environment variables (Railway injects these) with sensible defaults
for local development.

Usage everywhere in the codebase:
    from config.settings import settings

    dsn = settings.DATABASE_URL
    key = settings.ANTHROPIC_API_KEY

Every field referenced by any module in the repo is declared here:
  - infrastructure.py reads: DATABASE_URL, REDIS_URL, ANTHROPIC_API_KEY,
    OPENAI_API_KEY, DEEPSEEK_API_KEY, HUGGINGFACE_API_KEY, WORDPRESS_URL,
    WORDPRESS_USERNAME, WORDPRESS_PASSWORD, SERP_API_KEY
  - llm_service.py / base.py reads: model configs via ModelConfig
  - nodes read: thresholds, max_retries via env
  - main.py reads: SCHEDULER_*, LOG_LEVEL
  - seeds / migrations read: DATABASE_URL
"""

from __future__ import annotations

import os
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All settings loaded from environment variables.
    Pydantic-settings reads these automatically — no manual os.getenv() needed.

    For local dev: create agents/.env with your values.
    For Railway: set in the service Variables tab.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",          # don't fail on extra env vars Railway injects
        case_sensitive=False,    # DATABASE_URL == database_url
    )

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql://pmw:pmw@localhost:5432/pmw"

    # ── Redis ─────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379"

    # ── LLM Provider API Keys ─────────────────────────────────────────────
    ANTHROPIC_API_KEY: str = os.getenviron("ANTHROPIC_API_KEY") 
    OPENAI_API_KEY: str = os.getenviron("OPENAI_API_KEY")
    DEEPSEEK_API_KEY: str = os.getenviron("DEEPSEEK_API_KEY")
    HUGGINGFACE_API_KEY: str = os.getenviron("HUGGINGFACE_API_KEY")

    # ── WordPress REST API ────────────────────────────────────────────────
    # Used by infrastructure/owned/wordpress/wp_db_client.py
    WP_BASE_URL: str = Field(
        default="https://www.preciousmarketwatch.com/wp",
        alias="WP_BASE_URL",
    )
    WP_APP_USERNAME: str = Field(default="", alias="WP_APP_USERNAME")
    WP_APP_PASSWORD: str = Field(default="", alias="WP_APP_PASSWORD")
    WP_DEFAULT_POST_STATUS: str = "draft"

    # Convenience aliases used by Infrastructure.__init__
    @property
    def WORDPRESS_URL(self) -> str:
        return self.WP_BASE_URL

    @property
    def WORDPRESS_USERNAME(self) -> str:
        return self.WP_APP_USERNAME

    @property
    def WORDPRESS_PASSWORD(self) -> str:
        return self.WP_APP_PASSWORD

    # ── WordPress MySQL (direct DB reads for reporting/intelligence) ──────
    WP_DB_HOST: str = ""
    WP_DB_PORT: int = 3306
    WP_DB_NAME: str = ""
    WP_DB_USER: str = ""
    WP_DB_PASSWORD: str = ""
    WP_DB_SSL: bool = True
    WP_TABLE_PREFIX: str = "wp_"

    # ── SERP API ──────────────────────────────────────────────────────────
    SERP_API_KEY: str = ""

    # ── News API (for MarketService / NewsClient) ─────────────────────────
    NEWS_API_KEY: str = ""

    # ── Pipeline Model Configuration ──────────────────────────────────────
    PIPELINE_MODEL: str = "claude-sonnet-4-6"
    JUDGE_MODEL: str = "claude-opus-4-6"
    JUDGE_MODEL_FAST: str = "claude-sonnet-4-6"
    JUDGE_TEMPERATURE: float = 0.1

    # ── Scoring Thresholds ────────────────────────────────────────────────
    RESEARCH_THRESHOLD: float = 0.75
    PLANNING_THRESHOLD: float = 0.80
    CONTENT_THRESHOLD: float = 0.80
    SOCIAL_THRESHOLD: float = 0.75

    # ── Retry Configuration ───────────────────────────────────────────────
    RESEARCH_MAX_RETRIES: int = 3
    PLANNING_MAX_RETRIES: int = 3
    CONTENT_MAX_RETRIES: int = 3

    # ── Worker ────────────────────────────────────────────────────────────
    SERVICE_ROLE: str = "agents"
    WORKER_CONCURRENCY: int = 2

    # ── Image Generation ──────────────────────────────────────────────────
    IMAGE_GENERATION_ENABLED: bool = True
    IMAGE_QUALITY: str = "standard"       # "standard" | "hd"
    INFOGRAPHIC_ENABLED: bool = False     # Phase 2

    # ── LangSmith / Tracing ───────────────────────────────────────────────
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_PROJECT: str = "pmw-local"

    # ── Scheduler ─────────────────────────────────────────────────────────
    SCHEDULER_ENABLED: bool = False
    SCHEDULER_CRON: str = "0 8 * * *"
    SCHEDULER_TIMEZONE: str = "Europe/London"

    # ── Logging ───────────────────────────────────────────────────────────
    LOG_LEVEL: str = "info"

    # ── Phase 2: Analytics Integrations ───────────────────────────────────
    GA4_PROPERTY_ID: str = ""
    GA4_SERVICE_ACCOUNT: str = ""         # base64 JSON
    CLARITY_API_KEY: str = ""
    GSC_SERVICE_ACCOUNT: str = ""         # base64 JSON

    # ── Bridge (JWT — only used if this process serves the Bridge) ────────
    JWT_SECRET: str = "change-me-32-chars-minimum-in-production"
    JWT_EXPIRY: str = "8h"

    # ── Validators ────────────────────────────────────────────────────────

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_postgres_scheme(cls, v: str) -> str:
        """Railway often provides postgres:// — asyncpg needs postgresql://."""
        if isinstance(v, str) and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def normalise_log_level(cls, v: str) -> str:
        return v.upper() if isinstance(v, str) else v


# ── Singleton instance ────────────────────────────────────────────────────
# Import this everywhere:  from config.settings import settings

settings = Settings()