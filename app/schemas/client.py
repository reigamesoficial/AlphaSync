from pydantic import Field

from app.db.models import ClientLeadSource, ClientStatus
from app.schemas.common import BaseSchema, IDSchema, TimestampSchema


class ClientBase(BaseSchema):
    whatsapp_id: str | None = Field(default=None, max_length=40)
    name: str = Field(min_length=2, max_length=200)
    phone: str = Field(min_length=8, max_length=30)
    email: str | None = Field(default=None, max_length=150)
    address: str | None = None
    lead_source: ClientLeadSource = ClientLeadSource.WHATSAPP
    status: ClientStatus = ClientStatus.LEAD
    notes: str | None = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseSchema):
    whatsapp_id: str | None = Field(default=None, max_length=40)
    name: str | None = Field(default=None, min_length=2, max_length=200)
    phone: str | None = Field(default=None, min_length=8, max_length=30)
    email: str | None = Field(default=None, max_length=150)
    address: str | None = None
    lead_source: ClientLeadSource | None = None
    status: ClientStatus | None = None
    notes: str | None = None


class ClientResponse(ClientBase, IDSchema, TimestampSchema):
    company_id: int