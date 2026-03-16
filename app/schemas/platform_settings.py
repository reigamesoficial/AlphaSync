from typing import Any

from pydantic import EmailStr, Field

from app.schemas.common import BaseSchema, IDSchema, TimestampSchema


class PlatformSettingsBase(BaseSchema):
    platform_name: str = Field(default="AlphaSync", max_length=100)
    default_company_plan: str | None = None
    default_service_domain: str = "protection_network"
    allow_self_signup: bool = False
    support_email: EmailStr | None = None
    support_phone: str | None = Field(default=None, max_length=30)
    public_app_url: str | None = Field(default=None, max_length=255)
    logo_url: str | None = Field(default=None, max_length=255)
    extra_flags: dict[str, Any] = Field(default_factory=dict)


class PlatformSettingsUpdate(BaseSchema):
    platform_name: str | None = Field(default=None, max_length=100)
    default_company_plan: str | None = None
    default_service_domain: str | None = None
    allow_self_signup: bool | None = None
    support_email: EmailStr | None = None
    support_phone: str | None = Field(default=None, max_length=30)
    public_app_url: str | None = Field(default=None, max_length=255)
    logo_url: str | None = Field(default=None, max_length=255)
    extra_flags: dict[str, Any] | None = None


class PlatformSettingsResponse(PlatformSettingsBase, IDSchema, TimestampSchema):
    pass
