from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ============================================================
    # APP
    # ============================================================
    app_name: str = "AlphaSync"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = True
    app_version: str = "1.0.0"
    api_v1_prefix: str = "/api/v1"

    # ============================================================
    # SECURITY / AUTH
    # ============================================================
    secret_key: str = Field(..., min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # ============================================================
    # DATABASE / CACHE
    # ============================================================
    database_url: str
    redis_url: str = "redis://localhost:6379/0"

    # ============================================================
    # CORS
    # ============================================================
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]
    )

    # ============================================================
    # MULTI-TENANT / PLATFORM
    # ============================================================
    default_timezone: str = "America/Sao_Paulo"
    default_currency: str = "BRL"

    # ============================================================
    # WHATSAPP / META
    # ============================================================
    whatsapp_api_base_url: str = "https://graph.facebook.com"
    whatsapp_api_version: str = "v21.0"
    whatsapp_webhook_verify_token: str | None = None
    whatsapp_app_secret: str | None = None

    # ============================================================
    # GOOGLE CALENDAR
    # ============================================================
    google_calendar_enabled: bool = False
    google_credentials_json_path: str | None = None

    # ============================================================
    # PDF / STORAGE
    # ============================================================
    media_base_url: str | None = None
    storage_path: str = "storage"

    # ============================================================
    # LOGGING
    # ============================================================
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()