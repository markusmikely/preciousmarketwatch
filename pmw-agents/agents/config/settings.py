"""
PMW Agents — Application Settings

Single source of truth for all configuration. Uses pydantic-settings to load
from environment variables (Railway injects these) with sensible defaults.

Usage:
    from config.settings import settings
    dsn = settings.DATABASE_URL
"""

from __future__ import annotations
import os
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Database ──────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql://pmw:pmw@localhost:5432/pmw"

    # ── Redis ─────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379"

    # ── LLM Provider API Keys ─────────────────────────────────────────
    ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    DEEPSEEK_API_KEY: str = os.environ.get("DEEPSEEK_API_KEY", "")
    HUGGINGFACE_API_KEY: str = os.environ.get("HUGGINGFACE_API_KEY", "")

    # ── WordPress ─────────────────────────────────────────────────────
    WP_BASE_URL: str = Field(default="https://www.preciousmarketwatch.com/wp", alias="WP_BASE_URL")
    WP_APP_USERNAME: str = Field(default="", alias="WP_APP_USERNAME")
    WP_APP_PASSWORD: str = Field(default="", alias="WP_APP_PASSWORD")
    WP_DEFAULT_POST_STATUS: str = "draft"

    @property
    def WORDPRESS_URL(self) -> str:
        return self.WP_BASE_URL

    @property
    def WORDPRESS_USERNAME(self) -> str:
        return self.WP_APP_USERNAME

    @property
    def WORDPRESS_PASSWORD(self) -> str:
        return self.WP_APP_PASSWORD

    # ── WordPress MySQL ───────────────────────────────────────────────
    WP_DB_HOST: str = ""
    WP_DB_PORT: int = 3306
    WP_DB_NAME: str = ""
    WP_DB_USER: str = ""
    WP_DB_PASSWORD: str = ""
    WP_DB_SSL: bool = True
    WP_TABLE_PREFIX: str = "wp_"

    # ── SERP API ──────────────────────────────────────────────────────
    SERP_API_KEY: str = ""

    # ── News API ──────────────────────────────────────────────────────
    NEWS_API_KEY: str = ""

    # ── Pipeline Model Configuration ──────────────────────────────────
    PIPELINE_MODEL: str = "claude-sonnet-4-6"
    JUDGE_MODEL: str = "claude-opus-4-6"
    JUDGE_MODEL_FAST: str = "claude-sonnet-4-6"
    JUDGE_TEMPERATURE: float = 0.1

    # ── Scoring Thresholds ────────────────────────────────────────────
    RESEARCH_THRESHOLD: float = 0.75
    PLANNING_THRESHOLD: float = 0.80
    CONTENT_THRESHOLD: float = 0.80
    SOCIAL_THRESHOLD: float = 0.75
    AFFILIATE_FIT_THRESHOLD: float = 0.40
    COHERENCE_THRESHOLD: float = 0.60

    # ── Retry Configuration ───────────────────────────────────────────
    RESEARCH_MAX_RETRIES: int = 3
    PLANNING_MAX_RETRIES: int = 3
    CONTENT_MAX_RETRIES: int = 3

    # ── Multi-topic batching ──────────────────────────────────────────
    # How many topics to process per pipeline run.
    # Set to 0 for unlimited (process all eligible topics).
    TOPICS_PER_RUN: int = 10

    # Max concurrent briefs being researched simultaneously.
    # Each concurrent brief makes LLM + HTTP calls, so this controls
    # both API rate pressure and memory usage.
    BRIEF_CONCURRENCY: int = 3

    # ── Worker ────────────────────────────────────────────────────────
    SERVICE_ROLE: str = "agents"
    WORKER_CONCURRENCY: int = 2

    # ── Image Generation ──────────────────────────────────────────────
    IMAGE_GENERATION_ENABLED: bool = True
    IMAGE_QUALITY: str = "standard"
    INFOGRAPHIC_ENABLED: bool = False

    # ── LangSmith / Tracing ───────────────────────────────────────────
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_PROJECT: str = "pmw-local"

    # ── Scheduler ─────────────────────────────────────────────────────
    SCHEDULER_ENABLED: bool = False
    SCHEDULER_CRON: str = "0 8 * * *"
    SCHEDULER_TIMEZONE: str = "Europe/London"

    # ── Logging ───────────────────────────────────────────────────────
    LOG_LEVEL: str = "info"

    # ── Phase 2: Analytics ────────────────────────────────────────────
    GA4_PROPERTY_ID: str = ""
    GA4_SERVICE_ACCOUNT: str = ""
    CLARITY_API_KEY: str = ""
    GSC_SERVICE_ACCOUNT: str = ""

    # ── Bridge JWT ────────────────────────────────────────────────────
    JWT_SECRET: str = "change-me-32-chars-minimum-in-production"
    JWT_EXPIRY: str = "8h"

    # ── Validators ────────────────────────────────────────────────────

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_postgres_scheme(cls, v: str) -> str:
        if isinstance(v, str) and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def normalise_log_level(cls, v: str) -> str:
        return v.upper() if isinstance(v, str) else v


settings = Settings()