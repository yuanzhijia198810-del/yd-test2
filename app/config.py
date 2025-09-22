from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    database_url: str = Field(
        default="sqlite:///./monitoring.db",
        description="SQLAlchemy compatible database URL.",
    )
    app_name: str = Field(default="Frontend Monitoring Backend")
    debug: bool = Field(default=False)

    class Config:
        env_prefix = "MONITORING_"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()


def override_settings(**kwargs: Optional[str]) -> Settings:
    """Utility used by tests to override configuration values."""

    settings = get_settings()
    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    return settings
