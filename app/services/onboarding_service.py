from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models import Company, CompanySettings, ServiceDomain, User, UserRole
from app.repositories.companies import CompaniesRepository
from app.repositories.company_settings import CompanySettingsRepository
from app.repositories.users import UsersRepository

_DEFAULT_SETTINGS: dict[str, Any] = {
    "bot_name": "Assistente",
    "quote_prefix": "ORC",
    "currency": "BRL",
    "timezone": "America/Sao_Paulo",
    "extra_settings": {},
}

DOMAIN_DEFAULTS: dict[str, dict[str, Any]] = {
    ServiceDomain.PROTECTION_NETWORK: {
        **_DEFAULT_SETTINGS,
        "extra_settings": {
            "show_measures_to_customer": True,
            "pricing_rules": {
                "minimum_order_value": 150.0,
                "visit_fee": 0.0,
                "mesh_price_overrides": {
                    "3x3": 50.0,
                    "5x5": 40.0,
                    "10x10": 35.0,
                },
                "color_price_overrides": {},
            },
            "available_colors": ["branca", "preta", "cinza", "bege"],
            "available_mesh_types": ["3x3", "5x5", "10x10"],
        },
    },
}


def get_domain_defaults(domain: str) -> dict[str, Any]:
    return DOMAIN_DEFAULTS.get(domain, _DEFAULT_SETTINGS)


class OnboardingService:
    def __init__(self, db: Session):
        self.db = db
        self.companies_repo = CompaniesRepository(db)
        self.settings_repo = CompanySettingsRepository(db)
        self.users_repo = UsersRepository(db)

    def bootstrap_company(
        self,
        *,
        name: str,
        slug: str,
        service_domain: str = ServiceDomain.PROTECTION_NETWORK,
        plan_name: str | None = None,
        whatsapp_phone_number_id: str | None = None,
        support_email: str | None = None,
        admin_name: str,
        admin_email: str,
        admin_password: str,
    ) -> tuple[Company, CompanySettings, User]:
        slug_clean = slug.strip().lower()
        email_clean = admin_email.strip().lower()

        if self.companies_repo.get_by_slug(slug_clean):
            raise ValueError(f"Slug '{slug_clean}' já está em uso.")

        if self.users_repo.get_by_email(email_clean):
            raise ValueError(f"E-mail '{email_clean}' já está em uso por outro usuário.")

        company = self.companies_repo.create_company(
            slug=slug_clean,
            name=name.strip(),
            service_domain=service_domain,
            plan_name=plan_name,
            whatsapp_phone_number_id=whatsapp_phone_number_id or None,
            support_email=support_email,
            is_active=True,
        )
        self.db.flush()

        defaults = get_domain_defaults(service_domain)
        settings = self.settings_repo.create_for_company(
            company_id=company.id,
            brand_name=name.strip(),
            bot_name=defaults.get("bot_name"),
            quote_prefix=defaults.get("quote_prefix"),
            currency=defaults.get("currency", "BRL"),
            timezone=defaults.get("timezone", "America/Sao_Paulo"),
            extra_settings=defaults.get("extra_settings", {}),
        )
        self.db.flush()

        admin = self.users_repo.create_user(
            company_id=company.id,
            email=email_clean,
            password_hash=hash_password(admin_password),
            role=UserRole.COMPANY_ADMIN,
            name=admin_name.strip(),
            is_active=True,
        )
        self.db.flush()

        return company, settings, admin

    def create_admin_for_company(
        self,
        *,
        company: Company,
        admin_name: str,
        admin_email: str,
        admin_password: str,
    ) -> User:
        email_clean = admin_email.strip().lower()

        if self.users_repo.get_by_email(email_clean):
            raise ValueError(f"E-mail '{email_clean}' já está em uso.")

        admin = self.users_repo.create_user(
            company_id=company.id,
            email=email_clean,
            password_hash=hash_password(admin_password),
            role=UserRole.COMPANY_ADMIN,
            name=admin_name.strip(),
            is_active=True,
        )
        self.db.flush()
        return admin
