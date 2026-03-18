from __future__ import annotations

from datetime import datetime

from app.schemas.common import BaseSchema, IDSchema, TimestampSchema


class WarrantyConfigSchema(BaseSchema):
    """Configuração padrão de garantia por empresa — salvo em extra_settings."""
    service_description: str = ""
    warranty_period: str = "12 meses"
    warranty_covers: str = ""
    additional_notes: str = ""
    signature: str = ""


class WarrantyCreate(BaseSchema):
    appointment_id: int
    service_description: str
    warranty_period: str
    warranty_covers: str
    additional_notes: str | None = None
    signature: str | None = None


class WarrantyResponse(IDSchema, TimestampSchema):
    company_id: int
    appointment_id: int
    client_id: int
    client_name: str
    client_phone: str
    address_raw: str | None
    service_description: str
    warranty_period: str
    warranty_covers: str
    additional_notes: str | None
    signature: str | None
    sent_at: datetime | None
    sent_by_user_id: int | None
