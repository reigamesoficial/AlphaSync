from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CompanySettings
from app.repositories.base import BaseRepository


class CompanySettingsRepository(BaseRepository[CompanySettings]):
    def __init__(self, db: Session):
        super().__init__(db, CompanySettings)

    def get_by_company_id(self, company_id: int) -> CompanySettings | None:
        stmt = select(CompanySettings).where(CompanySettings.company_id == company_id)
        return self.db.scalar(stmt)

    def create_for_company(
        self,
        *,
        company_id: int,
        brand_name: str | None = None,
        primary_color: str | None = None,
        secondary_color: str | None = None,
        logo_url: str | None = None,
        bot_name: str | None = None,
        quote_prefix: str | None = None,
        whatsapp_access_token: str | None = None,
        whatsapp_verify_token: str | None = None,
        calendar_provider: str | None = None,
        calendar_id: str | None = None,
        currency: str = "BRL",
        timezone: str = "America/Sao_Paulo",
        extra_settings: dict[str, Any] | None = None,
    ) -> CompanySettings:
        settings = CompanySettings(
            company_id=company_id,
            brand_name=brand_name,
            primary_color=primary_color,
            secondary_color=secondary_color,
            logo_url=logo_url,
            bot_name=bot_name,
            quote_prefix=quote_prefix,
            whatsapp_access_token=whatsapp_access_token,
            whatsapp_verify_token=whatsapp_verify_token,
            calendar_provider=calendar_provider,
            calendar_id=calendar_id,
            currency=currency,
            timezone=timezone,
            extra_settings=extra_settings or {},
        )
        return self.add(settings)

    def update_settings(
        self,
        settings_obj: CompanySettings,
        *,
        brand_name: str | None = None,
        primary_color: str | None = None,
        secondary_color: str | None = None,
        logo_url: str | None = None,
        bot_name: str | None = None,
        quote_prefix: str | None = None,
        whatsapp_access_token: str | None = None,
        whatsapp_verify_token: str | None = None,
        calendar_provider: str | None = None,
        calendar_id: str | None = None,
        currency: str | None = None,
        timezone: str | None = None,
        extra_settings: dict[str, Any] | None = None,
    ) -> CompanySettings:
        if brand_name is not None:
            settings_obj.brand_name = brand_name
        if primary_color is not None:
            settings_obj.primary_color = primary_color
        if secondary_color is not None:
            settings_obj.secondary_color = secondary_color
        if logo_url is not None:
            settings_obj.logo_url = logo_url
        if bot_name is not None:
            settings_obj.bot_name = bot_name
        if quote_prefix is not None:
            settings_obj.quote_prefix = quote_prefix
        if whatsapp_access_token is not None:
            settings_obj.whatsapp_access_token = whatsapp_access_token
        if whatsapp_verify_token is not None:
            settings_obj.whatsapp_verify_token = whatsapp_verify_token
        if calendar_provider is not None:
            settings_obj.calendar_provider = calendar_provider
        if calendar_id is not None:
            settings_obj.calendar_id = calendar_id
        if currency is not None:
            settings_obj.currency = currency
        if timezone is not None:
            settings_obj.timezone = timezone
        if extra_settings is not None:
            settings_obj.extra_settings = extra_settings

        self.db.flush()
        self.db.refresh(settings_obj)
        return settings_obj

    def upsert_by_company_id(
        self,
        *,
        company_id: int,
        **data: Any,
    ) -> CompanySettings:
        existing = self.get_by_company_id(company_id)
        if existing:
            return self.update_settings(existing, **data)
        return self.create_for_company(company_id=company_id, **data)