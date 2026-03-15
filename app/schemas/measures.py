from __future__ import annotations

import re
import unicodedata
from typing import Any

from pydantic import Field, field_validator, model_validator

from app.schemas.common import BaseSchema, IDSchema, TimestampSchema


def _normalize_address(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower().strip()
    value = re.sub(r"[,\.;:\-\(\)\[\]#]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value


class AddressCreate(BaseSchema):
    raw_address: str = Field(min_length=3, max_length=500)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=60)
    zipcode: str | None = Field(default=None, max_length=20)
    notes: str | None = None

    @field_validator("raw_address")
    @classmethod
    def strip_raw(cls, v: str) -> str:
        return v.strip()


class AddressUpdate(BaseSchema):
    raw_address: str | None = Field(default=None, min_length=3, max_length=500)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=60)
    zipcode: str | None = Field(default=None, max_length=20)
    notes: str | None = None
    is_active: bool | None = None

    @field_validator("raw_address")
    @classmethod
    def strip_raw(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class PlantResponse(IDSchema):
    address_catalog_id: int
    company_id: int
    name: str
    sort_order: int
    is_active: bool


class ItemResponse(IDSchema):
    address_catalog_id: int
    company_id: int
    plant_id: int | None
    label: str
    width_m: float
    height_m: float
    quantity: int
    notes: str | None
    is_active: bool
    area_m2: float

    @model_validator(mode="before")
    @classmethod
    def compute_area(cls, data: Any) -> Any:
        if isinstance(data, dict):
            w = float(data.get("width_m") or 0)
            h = float(data.get("height_m") or 0)
            q = int(data.get("quantity") or 1)
            data["area_m2"] = round(w * h * q, 4)
        else:
            w = float(getattr(data, "width_m", 0) or 0)
            h = float(getattr(data, "height_m", 0) or 0)
            q = int(getattr(data, "quantity", 1) or 1)
            data.__dict__["area_m2"] = round(w * h * q, 4)
        return data


class PlantWithItems(BaseSchema):
    plant: PlantResponse
    items: list[ItemResponse]


class AddressResponse(IDSchema):
    company_id: int
    raw_address: str
    normalized_address: str
    city: str | None
    state: str | None
    zipcode: str | None
    notes: str | None
    is_active: bool


class AddressWithHierarchy(BaseSchema):
    address: AddressResponse
    plants: list[PlantWithItems]
    direct_items: list[ItemResponse]


class PlantCreate(BaseSchema):
    address_catalog_id: int
    name: str = Field(min_length=1, max_length=200)
    sort_order: int = 0

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()


class PlantUpdate(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    sort_order: int | None = None
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class ItemCreate(BaseSchema):
    address_catalog_id: int
    plant_id: int | None = None
    label: str = Field(min_length=1, max_length=200)
    width_m: float = Field(gt=0)
    height_m: float = Field(gt=0)
    quantity: int = Field(default=1, ge=1)
    notes: str | None = None

    @field_validator("label")
    @classmethod
    def strip_label(cls, v: str) -> str:
        return v.strip()


class ItemUpdate(BaseSchema):
    plant_id: int | None = None
    label: str | None = Field(default=None, min_length=1, max_length=200)
    width_m: float | None = Field(default=None, gt=0)
    height_m: float | None = Field(default=None, gt=0)
    quantity: int | None = Field(default=None, ge=1)
    notes: str | None = None
    is_active: bool | None = None

    @field_validator("label")
    @classmethod
    def strip_label(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class MeasureStats(BaseSchema):
    total_addresses: int
    total_plants: int
    total_items: int


class PNSettingsResponse(BaseSchema):
    show_measures_to_customer: bool
    default_price_per_m2: float
    minimum_order_value: float
    visit_fee: float
    available_colors: list[str]
    available_mesh_types: list[str]
    mesh_prices: dict[str, float]


class PNSettingsUpdate(BaseSchema):
    show_measures_to_customer: bool | None = None
    default_price_per_m2: float | None = Field(default=None, ge=0)
    minimum_order_value: float | None = Field(default=None, ge=0)
    visit_fee: float | None = Field(default=None, ge=0)
    available_colors: list[str] | None = None
    available_mesh_types: list[str] | None = None
    mesh_prices: dict[str, float] | None = None
