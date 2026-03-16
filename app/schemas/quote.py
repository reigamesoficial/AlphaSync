from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import Field

from app.db.models import QuoteItemStatus, QuoteStatus
from app.schemas.common import BaseSchema, IDSchema, TimestampSchema


class QuoteItemBase(BaseSchema):
    description: str
    service_type: str | None = Field(default=None, max_length=60)
    width_cm: Decimal | None = None
    height_cm: Decimal | None = None
    quantity: int = Field(default=1, ge=1)
    unit_price: Decimal = Field(default=Decimal("0.00"))
    total_price: Decimal = Field(default=Decimal("0.00"))
    status: QuoteItemStatus = QuoteItemStatus.PENDING
    notes: str | None = None
    domain_data: dict[str, Any] | None = None


class QuoteItemCreate(QuoteItemBase):
    pass


class QuoteItemUpdate(BaseSchema):
    description: str | None = None
    service_type: str | None = Field(default=None, max_length=60)
    width_cm: Decimal | None = None
    height_cm: Decimal | None = None
    quantity: int | None = Field(default=None, ge=1)
    unit_price: Decimal | None = None
    total_price: Decimal | None = None
    status: QuoteItemStatus | None = None
    notes: str | None = None
    domain_data: dict[str, Any] | None = None


class QuoteItemResponse(QuoteItemBase, IDSchema, TimestampSchema):
    quote_id: int
    company_id: int


class QuoteBase(BaseSchema):
    client_id: int
    conversation_id: int | None = None
    seller_id: int | None = None
    code: str | None = Field(default=None, max_length=50)
    service_type: str = Field(default="protection_network", max_length=60)
    title: str | None = Field(default=None, max_length=150)
    description: str | None = None
    subtotal: Decimal = Field(default=Decimal("0.00"))
    discount: Decimal = Field(default=Decimal("0.00"))
    total_value: Decimal = Field(default=Decimal("0.00"))
    status: QuoteStatus = QuoteStatus.DRAFT
    valid_until: date | None = None
    notes: str | None = None
    pdf_url: str | None = None
    domain_data: dict[str, Any] | None = None


class QuoteCreate(QuoteBase):
    items: list[QuoteItemCreate] = Field(default_factory=list)


class QuoteUpdate(BaseSchema):
    client_id: int | None = None
    conversation_id: int | None = None
    seller_id: int | None = None
    code: str | None = Field(default=None, max_length=50)
    service_type: str | None = Field(default=None, max_length=60)
    title: str | None = Field(default=None, max_length=150)
    description: str | None = None
    subtotal: Decimal | None = None
    discount: Decimal | None = None
    total_value: Decimal | None = None
    status: QuoteStatus | None = None
    valid_until: date | None = None
    notes: str | None = None
    pdf_url: str | None = None
    domain_data: dict[str, Any] | None = None


class ClientSummary(BaseSchema):
    id: int
    name: str
    phone: str | None = None


class QuoteResponse(QuoteBase, IDSchema, TimestampSchema):
    company_id: int
    items: list[QuoteItemResponse] = Field(default_factory=list)
    client: ClientSummary | None = None