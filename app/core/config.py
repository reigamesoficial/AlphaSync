from __future__ import annotations

import json
from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_KEY_FRAGMENTS = {
    "change_this",
    "changeme",
    "your_secret",
    "secret_key",
    "example",
    "placeholder",
    "insecure",
    "default",
    "test",
}


def _parse_cors_str(value: str | list) -> list[str]:
    """Converte CORS_ORIGINS de string (JSON ou CSV) para lista."""
    if isinstance(value, list):
        return [str(o).strip() for o in value if str(o).strip()]
    if not isinstance(value, str):
        return []
    value = value.strip()
    if not value:
        return []
    # JSON array: ["*"] ou ["https://app.com","http://localhost:3000"]
    if value.startswith("["):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(o).strip() for o in parsed if str(o).strip()]
        except (json.JSONDecodeError, ValueError):
            pass
    # Comma-separated: https://app.com,http://localhost:3000
    return [item.strip() for item in value.split(",") if item.strip()]


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
    # CORS — armazenado como str para evitar JSON-parse automático
    # do pydantic_settings. Formatos aceitos:
    #   JSON array : ["*"]  ou  ["https://app.com","http://localhost:3000"]
    #   CSV        : https://app.com,http://localhost:3000
    #   Wildcard   : *
    # ============================================================
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @computed_field  # type: ignore[misc]
    @property
    def cors_origins_list(self) -> list[str]:
        return _parse_cors_str(self.cors_origins)

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

    @field_validator("database_url", mode="before")
    @classmethod
    def _fix_database_url(cls, value: str) -> str:
        if isinstance(value, str) and value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg2://", 1)
        return value

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

    # ============================================================
    # SCHEDULER — habilitar/desabilitar scheduler interno de tarefas
    # Em deploy distribuído (5 VPS): false no APP, true apenas no WORKER
    # Em deploy single-host: true (padrão)
    # ============================================================
    enable_scheduler: bool = True

    # ============================================================
    # SEED (primeiro admin — só usado pelo script scripts/seed_admin.py)
    # ============================================================
    seed_admin_email: str = "admin@alphasync.app"
    seed_admin_password: str = "changeme123"
    seed_admin_name: str = "Admin"
    seed_company_slug: str = "default"
    seed_company_name: str = "AlphaSync"

    # ============================================================
    # VALIDAÇÕES DE PRODUÇÃO
    # ============================================================
    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.app_env == "production":
            key_lower = self.secret_key.lower()
            for fragment in _INSECURE_KEY_FRAGMENTS:
                if fragment in key_lower:
                    raise ValueError(
                        f"SECRET_KEY contém fragmento inseguro '{fragment}'. "
                        "Gere uma chave forte: "
                        "python -c \"import secrets; print(secrets.token_hex(32))\""
                    )
            if self.app_debug:
                raise ValueError(
                    "APP_DEBUG=true não é permitido em APP_ENV=production. "
                    "Defina APP_DEBUG=false no .env de produção."
                )
        return self

    # ============================================================
    # HELPERS
    # ============================================================
    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def masked_database_url(self) -> str:
        try:
            from urllib.parse import urlparse
            parsed = urlparse(self.database_url)
            if parsed.password:
                return self.database_url.replace(parsed.password, "***")
        except Exception:
            pass
        return "***"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
