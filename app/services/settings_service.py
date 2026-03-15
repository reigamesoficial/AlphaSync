from __future__ import annotations

from copy import deepcopy
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.tenancy import assert_company_match
from app.db.models import Company, CompanySettings, User
from app.domains.engine import domain_engine
from app.repositories.companies import CompaniesRepository
from app.repositories.company_settings import CompanySettingsRepository
from app.schemas.company import CompanySettingsResponse, CompanySettingsUpdate


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value

    return result


class SettingsService:
    def __init__(self, db: Session):
        self.db = db
        self.settings_repo = CompanySettingsRepository(db)
        self.companies_repo = CompaniesRepository(db)

    def _get_company_or_404(self, company_id: int) -> Company:
        company = self.companies_repo.get_by_id(company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa não encontrada.",
            )
        return company

    def _build_domain_defaults(self, company: Company) -> dict[str, Any]:
        return domain_engine.get_default_settings_for_company(company)

    def _get_or_create_settings(self, company: Company) -> CompanySettings:
        settings_obj = self.settings_repo.get_by_company_id(company.id)
        if settings_obj:
            return settings_obj

        domain_defaults = self._build_domain_defaults(company)

        return self.settings_repo.create_for_company(
            company_id=company.id,
            brand_name=company.name,
            currency="BRL",
            timezone="America/Sao_Paulo",
            extra_settings=domain_defaults,
        )

    def _build_response(self, settings_obj: CompanySettings, company: Company) -> CompanySettingsResponse:
        domain_defaults = self._build_domain_defaults(company)
        effective_extra_settings = _deep_merge(
            domain_defaults,
            settings_obj.extra_settings or {},
        )

        payload = {
            "id": settings_obj.id,
            "company_id": settings_obj.company_id,
            "brand_name": settings_obj.brand_name,
            "primary_color": settings_obj.primary_color,
            "secondary_color": settings_obj.secondary_color,
            "logo_url": settings_obj.logo_url,
            "bot_name": settings_obj.bot_name,
            "quote_prefix": settings_obj.quote_prefix,
            "whatsapp_access_token": settings_obj.whatsapp_access_token,
            "whatsapp_verify_token": settings_obj.whatsapp_verify_token,
            "calendar_provider": settings_obj.calendar_provider,
            "calendar_id": settings_obj.calendar_id,
            "currency": settings_obj.currency,
            "timezone": settings_obj.timezone,
            "extra_settings": effective_extra_settings,
            "created_at": settings_obj.created_at,
            "updated_at": settings_obj.updated_at,
        }

        return CompanySettingsResponse.model_validate(payload)

    def get_company_settings(
        self,
        *,
        tenant_company_id: int,
        current_user: User,
    ) -> CompanySettingsResponse:
        company = self._get_company_or_404(tenant_company_id)
        assert_company_match(company.id, tenant_company_id, current_user)

        settings_obj = self._get_or_create_settings(company)
        return self._build_response(settings_obj, company)

    def upsert_company_settings(
        self,
        *,
        tenant_company_id: int,
        current_user: User,
        payload: CompanySettingsUpdate,
    ) -> CompanySettingsResponse:
        company = self._get_company_or_404(tenant_company_id)
        assert_company_match(company.id, tenant_company_id, current_user)

        settings_obj = self._get_or_create_settings(company)
        current_overrides = settings_obj.extra_settings or {}
        update_data = payload.model_dump(exclude_unset=True)

        if "extra_settings" in update_data:
            new_extra = update_data.pop("extra_settings") or {}
            update_data["extra_settings"] = _deep_merge(current_overrides, new_extra)

        updated = self.settings_repo.update_settings(settings_obj, **update_data)
        return self._build_response(updated, company)

    def get_domain_default_settings(
        self,
        *,
        tenant_company_id: int,
        current_user: User,
    ) -> dict[str, Any]:
        company = self._get_company_or_404(tenant_company_id)
        assert_company_match(company.id, tenant_company_id, current_user)
        return self._build_domain_defaults(company)

    def get_effective_extra_settings(
        self,
        *,
        tenant_company_id: int,
        current_user: User,
    ) -> dict[str, Any]:
        company = self._get_company_or_404(tenant_company_id)
        assert_company_match(company.id, tenant_company_id, current_user)

        settings_obj = self._get_or_create_settings(company)
        domain_defaults = self._build_domain_defaults(company)

        return _deep_merge(domain_defaults, settings_obj.extra_settings or {})