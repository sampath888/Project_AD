"""
Application configuration loaded from environment variables.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "PROJECT_AD"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Database ─────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://project_ad:project_ad_pass@localhost:5432/project_ad_db"
    DATABASE_URL_SYNC: str = "postgresql://project_ad:project_ad_pass@localhost:5432/project_ad_db"

    # ── Redis ────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Celery ───────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── S3 / MinIO ───────────────────────────────────────
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "ad-creatives"

    # ── Ad Platform APIs ─────────────────────────────────
    GOOGLE_ADS_DEVELOPER_TOKEN: str = ""
    GOOGLE_ADS_CLIENT_ID: str = ""
    GOOGLE_ADS_CLIENT_SECRET: str = ""
    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""
    TWITTER_API_KEY: str = ""
    TWITTER_API_SECRET: str = ""

    # ── Email ────────────────────────────────────────────
    SENDGRID_API_KEY: str = ""
    FROM_EMAIL: str = "noreply@projectad.com"

    # ── Admin Defaults ───────────────────────────────────
    ADMIN_EMAIL: str = "admin@projectad.com"
    ADMIN_PASSWORD: str = "admin123change_me"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
