from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.db.connection import get_db
from app.repositories.companies import CompaniesRepository
from app.repositories.company_settings import CompanySettingsRepository
from app.services.conversation_service import ConversationService
from app.services.whatsapp_service import WhatsAppService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.get("/whatsapp", response_class=PlainTextResponse)
def verify_whatsapp_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
):
    service = WhatsAppService()
    challenge = service.verify_webhook(
        mode=hub_mode,
        token=hub_verify_token,
        challenge=hub_challenge,
    )
    return challenge


@router.post("/whatsapp")
async def receive_whatsapp_webhook(
    request: Request,
    payload: dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
):
    raw_body = await request.body()

    whatsapp_service = WhatsAppService()
    whatsapp_service.verify_signature(
        raw_body=raw_body,
        signature_header=request.headers.get("X-Hub-Signature-256"),
    )

    conversation_service = ConversationService(db)
    companies_repo = CompaniesRepository(db)
    settings_repo = CompanySettingsRepository(db)

    message_events = whatsapp_service.extract_inbound_events(payload)
    status_events = whatsapp_service.extract_status_events(payload)

    processed_messages: list[dict] = []
    skipped_messages: list[dict] = []
    processed_statuses: list[dict] = []

    for event in message_events:
        company = companies_repo.get_by_whatsapp_phone_number_id(event["phone_number_id"])

        if not company:
            skipped_messages.append(
                {
                    "reason": "company_not_found_for_phone_number_id",
                    "phone_number_id": event["phone_number_id"],
                }
            )
            continue

        company_settings = settings_repo.get_by_company_id(company.id)
        access_token = company_settings.whatsapp_access_token if company_settings else None

        media_url = whatsapp_service.resolve_media_url(
            access_token=access_token,
            media_id=event.get("media_id"),
        )

        result = conversation_service.handle_inbound_whatsapp_message(
            company=company,
            phone_number_id=event["phone_number_id"],
            from_phone=event["from_phone"],
            contact_name=event.get("contact_name"),
            message_text=event.get("message_text"),
            whatsapp_message_id=event.get("whatsapp_message_id"),
            whatsapp_contact_id=event.get("whatsapp_contact_id"),
            interactive_reply_id=event.get("interactive_reply_id"),
            interactive_reply_title=event.get("interactive_reply_title"),
            media_url=media_url,
            raw_payload=event.get("raw_payload"),
        )
        processed_messages.append(result)

    for status_event in status_events:
        processed_statuses.append(
            {
                "phone_number_id": status_event.get("phone_number_id"),
                "whatsapp_message_id": status_event.get("whatsapp_message_id"),
                "status": status_event.get("status"),
                "recipient_id": status_event.get("recipient_id"),
            }
        )

    db.commit()

    return {
        "ok": True,
        "received_message_events": len(message_events),
        "processed_message_events": len(processed_messages),
        "skipped_message_events": len(skipped_messages),
        "received_status_events": len(status_events),
        "processed_status_events": len(processed_statuses),
        "processed_messages": processed_messages,
        "skipped_messages": skipped_messages,
        "processed_statuses": processed_statuses,
    }