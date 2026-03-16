"""Schemas para DomainDefinition — administração de domínios pelo master."""
from __future__ import annotations

from typing import Any

from pydantic import Field

from app.schemas.common import BaseSchema, IDSchema, TimestampSchema


class DomainDefinitionBase(BaseSchema):
    display_name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    icon: str | None = None
    is_active: bool = True


class DomainDefinitionCreate(DomainDefinitionBase):
    key: str = Field(min_length=2, max_length=60, pattern=r"^[a-z0-9_]+$")
    is_builtin: bool = False
    config_json: dict[str, Any] = Field(default_factory=dict)


class DomainDefinitionUpdate(BaseSchema):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    icon: str | None = None
    is_active: bool | None = None
    config_json: dict[str, Any] | None = None


class DomainDefinitionResponse(IDSchema, TimestampSchema, DomainDefinitionBase):
    key: str
    is_builtin: bool
    config_json: dict[str, Any]

    class Config:
        from_attributes = True


class DomainDefinitionListItem(IDSchema, TimestampSchema, DomainDefinitionBase):
    key: str
    is_builtin: bool

    class Config:
        from_attributes = True


class DomainSyncResult(BaseSchema):
    synced: int
    created: int
    skipped: int
    keys: list[str]
