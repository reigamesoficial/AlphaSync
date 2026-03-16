"""
WhatsApp 24h Window Service — AlphaSync

Regra do Meta: após uma mensagem do cliente, a empresa tem 24h para responder
com mensagens normais (sem template). Se o prazo expirar, só é possível enviar
templates aprovados pelo Meta.

Este serviço:
  1. Identifica conversas cuja janela de 24h está prestes a expirar.
  2. Envia uma mensagem amigável de reengajamento ("Posso te ajudar em mais alguma coisa?").
  3. É configurável por empresa via extra_settings.whatsapp_nudge_hours_before (padrão: 2h).
  4. Nunca envia para a mesma conversa mais de uma vez por janela.

Como usar:
  - Chame `check_and_nudge_expiring_windows(db)` periodicamente (recomendado: a cada 30 min).
  - Ou use o endpoint POST /api/v1/admin/whatsapp/check-windows.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger("alphasync.whatsapp_window")

_DEFAULT_NUDGE_HOURS_BEFORE = 2      # envia quando faltam N horas para fechar
_DEFAULT_NUDGE_MIN_HOURS = 1         # mínimo de horas desde a última msg para evitar spam
_NUDGE_CONTEXT_KEY = "window_nudge_sent_at"
_NUDGE_MESSAGE_DEFAULT = (
    "Olá! 😊 Posso te ajudar em mais alguma coisa? "
    "Estou aqui caso precise de mais informações sobre o orçamento."
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _get_nudge_settings(company) -> dict[str, Any]:
    settings = getattr(company, "settings", None)
    extra = {}
    if settings and getattr(settings, "extra_settings", None):
        extra = settings.extra_settings or {}

    return {
        "enabled": extra.get("whatsapp_nudge_enabled", True),
        "hours_before": float(extra.get("whatsapp_nudge_hours_before", _DEFAULT_NUDGE_HOURS_BEFORE)),
        "message": str(extra.get("whatsapp_nudge_message", "") or _NUDGE_MESSAGE_DEFAULT),
        "min_hours": float(extra.get("whatsapp_nudge_min_hours", _DEFAULT_NUDGE_MIN_HOURS)),
    }


def check_and_nudge_expiring_windows(db: Session) -> dict[str, Any]:
    """
    Verifica todas as empresas ativas e envia nudges para conversas
    cuja janela de 24h está prestes a expirar.

    Retorna um resumo: {checked, nudged, skipped, errors}
    """
    from app.db.models import Company, Conversation, ConversationStatus
    from app.repositories.company_settings import CompanySettingsRepository
    from app.services.whatsapp_service import WhatsAppService

    now = _utc_now()
    stats = {"checked": 0, "nudged": 0, "skipped": 0, "errors": 0}

    try:
        companies = (
            db.query(Company)
            .filter(Company.is_active == True)  # noqa: E712
            .all()
        )
    except Exception as exc:
        logger.error("Failed to query companies: %s", exc)
        stats["errors"] += 1
        return stats

    settings_repo = CompanySettingsRepository(db)
    whatsapp_service = WhatsAppService()

    for company in companies:
        nudge_cfg = _get_nudge_settings(company)
        if not nudge_cfg["enabled"]:
            continue

        hours_before = nudge_cfg["hours_before"]
        min_hours = nudge_cfg["min_hours"]

        # Janela expira em 24h da última msg do cliente.
        # Queremos enviar nudge quando last_message_at está entre (24-hours_before)h e 24h atrás.
        window_end = now - timedelta(hours=24 - hours_before)
        window_start = now - timedelta(hours=24)
        min_hours_ago = now - timedelta(hours=min_hours)

        try:
            conversations = (
                db.query(Conversation)
                .filter(
                    Conversation.company_id == company.id,
                    Conversation.status == ConversationStatus.BOT,
                    Conversation.last_message_at >= window_start,
                    Conversation.last_message_at <= window_end,
                    Conversation.last_message_at <= min_hours_ago,
                )
                .all()
            )
        except Exception as exc:
            logger.error("Failed to query conversations for company %s: %s", company.id, exc)
            stats["errors"] += 1
            continue

        company_settings = settings_repo.get_by_company_id(company.id)
        access_token = company_settings.whatsapp_access_token if company_settings else None
        phone_number_id = company_settings.whatsapp_phone_number_id if company_settings else None

        if not access_token or not phone_number_id:
            continue

        for conv in conversations:
            stats["checked"] += 1
            context = dict(conv.bot_context or {})

            # Verifica se já enviamos nudge nesta janela (evita duplicata)
            nudge_sent_at_str = context.get(_NUDGE_CONTEXT_KEY)
            if nudge_sent_at_str:
                try:
                    nudge_sent_at = datetime.fromisoformat(nudge_sent_at_str)
                    if nudge_sent_at.tzinfo is None:
                        nudge_sent_at = nudge_sent_at.replace(tzinfo=timezone.utc)
                    # Se já enviamos nudge e a última msg do cliente foi ANTES do nudge,
                    # significa que a janela ainda é a mesma → pular.
                    last_msg = conv.last_message_at
                    if last_msg and last_msg.tzinfo is None:
                        last_msg = last_msg.replace(tzinfo=timezone.utc)
                    if last_msg and nudge_sent_at > last_msg:
                        stats["skipped"] += 1
                        continue
                except Exception:
                    pass

            try:
                nudge_text = nudge_cfg["message"]
                whatsapp_service.send_text(
                    access_token=access_token,
                    phone_number_id=phone_number_id,
                    to=conv.phone,
                    body=nudge_text,
                )

                # Marca no contexto que o nudge foi enviado
                context[_NUDGE_CONTEXT_KEY] = now.isoformat()
                conv.bot_context = context

                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(conv, "bot_context")
                db.flush()

                logger.info(
                    "Nudge sent to conversation %s (company %s, phone %s)",
                    conv.id, company.id, conv.phone,
                )
                stats["nudged"] += 1
            except Exception as exc:
                logger.warning(
                    "Failed to send nudge to conversation %s: %s", conv.id, exc
                )
                stats["errors"] += 1

    try:
        db.commit()
    except Exception as exc:
        logger.error("Failed to commit nudge updates: %s", exc)
        db.rollback()

    return stats
