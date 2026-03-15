from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.db.models import AppointmentStatus, ReminderStatus
from app.schemas.common import BaseSchema, IDSchema, TimestampSchema


class AppointmentBase(BaseSchema):
    client_id: int
    quote_id: int | None = None
    assigned_installer_id: int | None = None
    parent_appointment_id: int | None = None

    address_raw: str | None = None
    start_at: datetime
    end_at: datetime

    service_type: str | None = Field(default=None, max_length=100)
    event_title: str | None = Field(default=None, max_length=200)

    calendar_event_id: str | None = None
    installers: list[str] | None = None
    valor: Decimal | None = None

    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    reminder_status: ReminderStatus = ReminderStatus.PENDING
    reminder_sent_at: datetime | None = None

    reschedule_reason: str | None = None

    finish_installer: str | None = None
    finish_payment: str | None = None
    finish_card_type: str | None = None
    finish_at: datetime | None = None

    notes: str | None = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseSchema):
    client_id: int | None = None
    quote_id: int | None = None
    assigned_installer_id: int | None = None
    parent_appointment_id: int | None = None

    address_raw: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None

    service_type: str | None = Field(default=None, max_length=100)
    event_title: str | None = Field(default=None, max_length=200)

    calendar_event_id: str | None = None
    installers: list[str] | None = None
    valor: Decimal | None = None

    status: AppointmentStatus | None = None
    reminder_status: ReminderStatus | None = None
    reminder_sent_at: datetime | None = None

    reschedule_reason: str | None = None

    finish_installer: str | None = None
    finish_payment: str | None = None
    finish_card_type: str | None = None
    finish_at: datetime | None = None

    notes: str | None = None


class AppointmentResponse(AppointmentBase, IDSchema, TimestampSchema):
    company_id: int