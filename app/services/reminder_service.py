"""
AlphaSync — Serviço de lembretes de agendamento (24h antes)

Dispara uma mensagem WhatsApp ao cliente 24h antes do appointment.start_at.

Controles anti-duplicata:
  - reminder_status PENDING → SENT | FAILED | SKIPPED
  - reminder_sent_at: timestamp do envio registrado no banco

Como usar:
  - Chamado pelo scheduler interno a cada 30 minutos.
  - Ou manualmente via endpoint POST /admin/reminders/send-pending.

Configurações por empresa via extra_settings:
  - reminder_enabled: bool (default True)
  - reminder_hours_before: float (default 24.0)
  - reminder_message: str com placeholder {time} (default abaixo)
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

logger = logging.getLogger("alphasync.reminder")

_DEFAULT_HOURS_BEFORE = 24.0
_DEFAULT_MESSAGE = (
    "Olá! 😊 Passando para confirmar seu atendimento agendado para *amanhã* às *{time}*. "
    "Se precisar de alguma informação ou precisar reagendar, é só me avisar!"
)


def _get_cfg(company) -> dict:
    extra: dict = {}
    if getattr(company, "settings", None) and getattr(company.settings, "extra_settings", None):
        extra = company.settings.extra_settings or {}
    return {
        "enabled": bool(extra.get("reminder_enabled", True)),
        "hours_before": float(extra.get("reminder_hours_before", _DEFAULT_HOURS_BEFORE)),
        "message": str(extra.get("reminder_message", "") or _DEFAULT_MESSAGE),
    }


def send_pending_reminders(db: Session) -> dict[str, int]:
    """
    Verifica todos os agendamentos com reminder_status=PENDING cujo start_at
    está a <= `hours_before` horas do momento atual, e envia o lembrete.

    Retorna: {"sent": N, "failed": N, "skipped": N}
    """
    from sqlalchemy import select
    from app.db.models import Company, CompanyStatus, ReminderStatus
    from app.repositories.appointments import AppointmentsRepository
    from app.services.whatsapp_service import WhatsAppService

    companies = list(
        db.scalars(select(Company).where(Company.status == CompanyStatus.ACTIVE)).all()
    )

    total_sent = 0
    total_failed = 0
    total_skipped = 0

    wa = WhatsAppService()
    now = datetime.now(timezone.utc)

    for company in companies:
        cfg = _get_cfg(company)
        if not cfg["enabled"]:
            continue

        until = now + timedelta(hours=cfg["hours_before"])
        repo = AppointmentsRepository(db)
        due = repo.list_due_reminders(company.id, until=until)

        if not due:
            continue

        access_token = (
            company.settings.whatsapp_access_token
            if company.settings
            else None
        )
        phone_id = company.whatsapp_phone_number_id

        for appointment in due:
            if not access_token or not phone_id:
                repo.update_appointment(
                    appointment.id,
                    company_id=company.id,
                    reminder_status=ReminderStatus.SKIPPED,
                )
                total_skipped += 1
                logger.debug(
                    "Reminder skipped (no WA credentials): appointment %s company %s",
                    appointment.id, company.id,
                )
                continue

            client_phone = (
                appointment.client.phone if appointment.client else None
            )
            if not client_phone:
                repo.update_appointment(
                    appointment.id,
                    company_id=company.id,
                    reminder_status=ReminderStatus.SKIPPED,
                )
                total_skipped += 1
                continue

            try:
                start_at = appointment.start_at
                if start_at.tzinfo is None:
                    start_at = start_at.replace(tzinfo=timezone.utc)
                time_str = start_at.strftime("%H:%M")
                message = cfg["message"].format(time=time_str)

                wa.send_text(
                    access_token=access_token,
                    phone_number_id=phone_id,
                    to=client_phone,
                    body=message,
                )

                repo.update_appointment(
                    appointment.id,
                    company_id=company.id,
                    reminder_status=ReminderStatus.SENT,
                    reminder_sent_at=now,
                )
                total_sent += 1
                logger.info(
                    "Reminder sent: appointment %s, company %s, phone %s",
                    appointment.id, company.id, client_phone,
                )
            except Exception as exc:
                logger.error(
                    "Reminder failed: appointment %s, company %s: %s",
                    appointment.id, company.id, exc,
                )
                repo.update_appointment(
                    appointment.id,
                    company_id=company.id,
                    reminder_status=ReminderStatus.FAILED,
                )
                total_failed += 1

        try:
            db.commit()
        except Exception as exc:
            logger.error("DB commit failed for company %s reminders: %s", company.id, exc)
            db.rollback()

    return {"sent": total_sent, "failed": total_failed, "skipped": total_skipped}
