from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Select, and_, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Appointment, AppointmentStatus, ReminderStatus
from app.repositories.base import TenantRepository


class AppointmentsRepository(TenantRepository[Appointment]):
    def __init__(self, db: Session):
        super().__init__(db, Appointment)

    def get_full_by_id_and_company(self, appointment_id: int, company_id: int) -> Appointment | None:
        stmt = (
            select(Appointment)
            .where(
                Appointment.id == appointment_id,
                Appointment.company_id == company_id,
            )
            .options(
                selectinload(Appointment.client),
                selectinload(Appointment.assigned_installer),
                selectinload(Appointment.quote),
                selectinload(Appointment.warranty),
            )
        )
        return self.db.scalar(stmt)

    def list_company_appointments(
        self,
        company_id: int,
        *,
        assigned_installer_id: int | None = None,
        client_id: int | None = None,
        status: AppointmentStatus | None = None,
        start_from: datetime | None = None,
        start_to: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Appointment]:
        stmt: Select[tuple[Appointment]] = (
            select(Appointment)
            .where(Appointment.company_id == company_id)
            .options(
                selectinload(Appointment.client),
                selectinload(Appointment.assigned_installer),
                selectinload(Appointment.quote),
                selectinload(Appointment.warranty),
            )
        )

        if assigned_installer_id is not None:
            stmt = stmt.where(Appointment.assigned_installer_id == assigned_installer_id)

        if client_id is not None:
            stmt = stmt.where(Appointment.client_id == client_id)

        if status is not None:
            stmt = stmt.where(Appointment.status == status)

        if start_from is not None:
            stmt = stmt.where(Appointment.start_at >= start_from)

        if start_to is not None:
            stmt = stmt.where(Appointment.start_at <= start_to)

        stmt = stmt.order_by(Appointment.start_at.asc()).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())

    def has_installer_conflict(
        self,
        company_id: int,
        installer_id: int,
        start_at: datetime,
        end_at: datetime,
        exclude_appointment_id: int | None = None,
    ) -> bool:
        """Return True if the installer has an overlapping active appointment in the given window."""
        active_statuses = [
            AppointmentStatus.SCHEDULED,
            AppointmentStatus.CONFIRMED,
            AppointmentStatus.IN_PROGRESS,
            AppointmentStatus.RESCHEDULED,
        ]
        stmt = select(Appointment).where(
            Appointment.company_id == company_id,
            Appointment.assigned_installer_id == installer_id,
            Appointment.status.in_(active_statuses),
            Appointment.start_at < end_at,
            Appointment.end_at > start_at,
        )
        if exclude_appointment_id is not None:
            stmt = stmt.where(Appointment.id != exclude_appointment_id)
        return self.db.scalar(stmt) is not None

    def list_due_reminders(
        self,
        company_id: int,
        *,
        until: datetime,
        limit: int = 100,
    ) -> list[Appointment]:
        stmt = (
            select(Appointment)
            .where(
                Appointment.company_id == company_id,
                Appointment.reminder_status == ReminderStatus.PENDING,
                Appointment.start_at <= until,
                Appointment.status.in_(
                    [
                        AppointmentStatus.SCHEDULED,
                        AppointmentStatus.CONFIRMED,
                    ]
                ),
            )
            .order_by(Appointment.start_at.asc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def create_appointment(
        self,
        *,
        company_id: int,
        client_id: int,
        quote_id: int | None = None,
        assigned_installer_id: int | None = None,
        parent_appointment_id: int | None = None,
        address_raw: str | None = None,
        start_at: datetime,
        end_at: datetime,
        service_type: str | None = None,
        event_title: str | None = None,
        calendar_event_id: str | None = None,
        installers: list[str] | None = None,
        valor: Decimal | None = None,
        status: AppointmentStatus = AppointmentStatus.SCHEDULED,
        reminder_status: ReminderStatus = ReminderStatus.PENDING,
        notes: str | None = None,
    ) -> Appointment:
        appointment = Appointment(
            company_id=company_id,
            client_id=client_id,
            quote_id=quote_id,
            assigned_installer_id=assigned_installer_id,
            parent_appointment_id=parent_appointment_id,
            address_raw=address_raw,
            start_at=start_at,
            end_at=end_at,
            service_type=service_type,
            event_title=event_title,
            calendar_event_id=calendar_event_id,
            installers=installers,
            valor=valor,
            status=status,
            reminder_status=reminder_status,
            notes=notes,
        )
        return self.add(appointment)

    def update_appointment(
        self,
        appointment: Appointment,
        *,
        assigned_installer_id: int | None = None,
        address_raw: str | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        service_type: str | None = None,
        event_title: str | None = None,
        calendar_event_id: str | None = None,
        installers: list[str] | None = None,
        valor: Decimal | None = None,
        status: AppointmentStatus | None = None,
        reminder_status: ReminderStatus | None = None,
        reminder_sent_at: datetime | None = None,
        reschedule_reason: str | None = None,
        finish_installer: str | None = None,
        finish_payment: str | None = None,
        finish_card_type: str | None = None,
        finish_at: datetime | None = None,
        notes: str | None = None,
    ) -> Appointment:
        if assigned_installer_id is not None:
            appointment.assigned_installer_id = assigned_installer_id
        if address_raw is not None:
            appointment.address_raw = address_raw
        if start_at is not None:
            appointment.start_at = start_at
        if end_at is not None:
            appointment.end_at = end_at
        if service_type is not None:
            appointment.service_type = service_type
        if event_title is not None:
            appointment.event_title = event_title
        if calendar_event_id is not None:
            appointment.calendar_event_id = calendar_event_id
        if installers is not None:
            appointment.installers = installers
        if valor is not None:
            appointment.valor = valor
        if status is not None:
            appointment.status = status
        if reminder_status is not None:
            appointment.reminder_status = reminder_status
        if reminder_sent_at is not None:
            appointment.reminder_sent_at = reminder_sent_at
        if reschedule_reason is not None:
            appointment.reschedule_reason = reschedule_reason
        if finish_installer is not None:
            appointment.finish_installer = finish_installer
        if finish_payment is not None:
            appointment.finish_payment = finish_payment
        if finish_card_type is not None:
            appointment.finish_card_type = finish_card_type
        if finish_at is not None:
            appointment.finish_at = finish_at
        if notes is not None:
            appointment.notes = notes

        self.db.flush()
        self.db.refresh(appointment)
        return appointment
