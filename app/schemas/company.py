from typing import Any

from pydantic import EmailStr, Field

from app.db.models import CompanyStatus, ServiceDomain
from app.schemas.common import BaseSchema, IDSchema, TimestampSchema


class CompanyBase(BaseSchema):
    slug: str = Field(min_length=2, max_length=60)
    name: str = Field(min_length=2, max_length=200)
    status: CompanyStatus = CompanyStatus.ACTIVE
    service_domain: ServiceDomain = ServiceDomain.PROTECTION_NETWORK
    plan_name: str | None = Field(default=None, max_length=50)
    whatsapp_phone_number_id: str | None = Field(default=None, max_length=40)
    whatsapp_business_account_id: str | None = Field(default=None, max_length=80)
    support_email: EmailStr | None = None
    support_phone: str | None = Field(default=None, max_length=30)
    is_active: bool = True


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseSchema):
    slug: str | None = Field(default=None, min_length=2, max_length=60)
    name: str | None = Field(default=None, min_length=2, max_length=200)
    status: CompanyStatus | None = None
    service_domain: ServiceDomain | None = None
    plan_name: str | None = Field(default=None, max_length=50)
    whatsapp_phone_number_id: str | None = Field(default=None, max_length=40)
    whatsapp_business_account_id: str | None = Field(default=None, max_length=80)
    support_email: EmailStr | None = None
    support_phone: str | None = Field(default=None, max_length=30)
    is_active: bool | None = None


class CompanyResponse(CompanyBase, IDSchema, TimestampSchema):
    pass


class CompanySettingsBase(BaseSchema):
    brand_name: str | None = Field(default=None, max_length=150)
    primary_color: str | None = Field(default=None, max_length=20)
    secondary_color: str | None = Field(default=None, max_length=20)
    logo_url: str | None = Field(default=None, max_length=255)

    bot_name: str | None = Field(default=None, max_length=100)
    quote_prefix: str | None = Field(default=None, max_length=20)

    whatsapp_access_token: str | None = None
    whatsapp_verify_token: str | None = Field(default=None, max_length=255)

    calendar_provider: str | None = Field(default=None, max_length=50)
    calendar_id: str | None = Field(default=None, max_length=255)

    currency: str = Field(default="BRL", max_length=10)
    timezone: str = Field(default="America/Sao_Paulo", max_length=80)

    extra_settings: dict[str, Any] = Field(default_factory=dict)


class CompanySettingsCreate(CompanySettingsBase):
    company_id: int


class CompanySettingsUpdate(BaseSchema):
    brand_name: str | None = Field(default=None, max_length=150)
    primary_color: str | None = Field(default=None, max_length=20)
    secondary_color: str | None = Field(default=None, max_length=20)
    logo_url: str | None = Field(default=None, max_length=255)

    bot_name: str | None = Field(default=None, max_length=100)
    quote_prefix: str | None = Field(default=None, max_length=20)

    whatsapp_access_token: str | None = None
    whatsapp_verify_token: str | None = Field(default=None, max_length=255)

    calendar_provider: str | None = Field(default=None, max_length=50)
    calendar_id: str | None = Field(default=None, max_length=255)

    currency: str | None = Field(default=None, max_length=10)
    timezone: str | None = Field(default=None, max_length=80)

    extra_settings: dict[str, Any] | None = None


class CompanySettingsResponse(CompanySettingsBase, IDSchema, TimestampSchema):
    company_id: int