from __future__ import annotations

import logging
from typing import Any

LOG = logging.getLogger("alphasync.whatsapp_service")

from fastapi import HTTPException, status

from app.core.config import settings
from app.integrations.whatsapp_client import WhatsAppClient


class WhatsAppService:
    def verify_webhook(
        self,
        *,
        mode: str | None,
        token: str | None,
        challenge: str | None,
    ) -> str:
        if mode != "subscribe":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Modo de verificação inválido.",
            )

        expected_token = settings.whatsapp_webhook_verify_token
        if not expected_token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="WHATSAPP_WEBHOOK_VERIFY_TOKEN não configurado.",
            )

        if token != expected_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token de verificação inválido.",
            )

        if challenge is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Challenge ausente.",
            )

        return challenge

    def verify_signature(self, raw_body: bytes, signature_header: str | None) -> None:
        client = WhatsAppClient()
        if not client.verify_signature(raw_body, signature_header):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Assinatura do webhook inválida.",
            )

    def extract_inbound_events(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []

        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {}) or {}
                metadata = value.get("metadata", {}) or {}
                phone_number_id = metadata.get("phone_number_id")

                contacts = value.get("contacts", []) or []
                contact_name = None
                whatsapp_contact_id = None
                if contacts:
                    first_contact = contacts[0]
                    contact_name = ((first_contact.get("profile") or {}).get("name"))
                    whatsapp_contact_id = first_contact.get("wa_id")

                for message in value.get("messages", []) or []:
                    from_phone = message.get("from")
                    message_id = message.get("id")
                    message_type = message.get("type", "text")

                    text_body = None
                    interactive_reply_id = None
                    interactive_reply_title = None
                    media_id = None
                    media_mime_type = None
                    media_filename = None

                    if message_type == "text":
                        text_body = (message.get("text") or {}).get("body")

                    elif message_type == "interactive":
                        interactive = message.get("interactive") or {}
                        if interactive.get("type") == "button_reply":
                            reply = interactive.get("button_reply") or {}
                            interactive_reply_id = reply.get("id")
                            interactive_reply_title = reply.get("title")
                            text_body = interactive_reply_id or interactive_reply_title
                        elif interactive.get("type") == "list_reply":
                            reply = interactive.get("list_reply") or {}
                            interactive_reply_id = reply.get("id")
                            interactive_reply_title = reply.get("title")
                            text_body = interactive_reply_id or interactive_reply_title

                    elif message_type in {"image", "audio", "video", "document"}:
                        media_obj = message.get(message_type) or {}
                        media_id = media_obj.get("id")
                        media_mime_type = media_obj.get("mime_type")
                        media_filename = media_obj.get("filename")

                    if not phone_number_id or not from_phone:
                        continue

                    events.append(
                        {
                            "kind": "message",
                            "phone_number_id": phone_number_id,
                            "from_phone": from_phone,
                            "contact_name": contact_name,
                            "whatsapp_contact_id": whatsapp_contact_id,
                            "whatsapp_message_id": message_id,
                            "message_type": message_type,
                            "message_text": text_body,
                            "interactive_reply_id": interactive_reply_id,
                            "interactive_reply_title": interactive_reply_title,
                            "media_id": media_id,
                            "media_mime_type": media_mime_type,
                            "media_filename": media_filename,
                            "raw_payload": {
                                "entry": entry,
                                "change": change,
                                "message": message,
                            },
                        }
                    )

        return events

    def extract_status_events(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []

        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {}) or {}
                metadata = value.get("metadata", {}) or {}
                phone_number_id = metadata.get("phone_number_id")

                for status_obj in value.get("statuses", []) or []:
                    events.append(
                        {
                            "kind": "status",
                            "phone_number_id": phone_number_id,
                            "whatsapp_message_id": status_obj.get("id"),
                            "status": status_obj.get("status"),
                            "recipient_id": status_obj.get("recipient_id"),
                            "timestamp": status_obj.get("timestamp"),
                            "conversation": status_obj.get("conversation"),
                            "pricing": status_obj.get("pricing"),
                            "raw_payload": {
                                "entry": entry,
                                "change": change,
                                "status": status_obj,
                            },
                        }
                    )

        return events

    def resolve_media_url(self, *, access_token: str | None, media_id: str | None) -> str | None:
        if not access_token or not media_id:
            return None

        client = WhatsAppClient(access_token=access_token)
        try:
            return client.get_media_url(media_id)
        except Exception:
            return None

    def send_text(
        self,
        *,
        access_token: str,
        phone_number_id: str,
        to: str,
        body: str,
    ) -> dict[str, Any]:
        client = WhatsAppClient(access_token=access_token)
        return client.send_text_message(
            phone_number_id=phone_number_id,
            to=to,
            body=body,
        )

    def send_buttons(
        self,
        *,
        access_token: str,
        phone_number_id: str,
        to: str,
        body: str,
        buttons: list[dict[str, str]],
    ) -> dict[str, Any]:
        client = WhatsAppClient(access_token=access_token)
        return client.send_buttons_message(
            phone_number_id=phone_number_id,
            to=to,
            body=body,
            buttons=buttons,
        )

    def send_list_message(
        self,
        *,
        access_token: str,
        phone_number_id: str,
        to: str,
        header: str,
        body: str,
        button_text: str,
        sections: list[dict[str, Any]],
    ) -> dict[str, Any]:
        LOG.info(
            "[wa:send_list_message] to=%s header=%r button_text=%r sections_count=%s",
            to, header, button_text, len(sections),
        )
        client = WhatsAppClient(access_token=access_token)
        try:
            result = client.send_list_message(
                phone_number_id=phone_number_id,
                to=to,
                header=header,
                body=body,
                button_text=button_text,
                sections=sections,
            )
            LOG.info("[wa:send_list_message] to=%s provider_response=%s", to, result)
            return result
        except Exception as exc:
            LOG.error("[wa:send_list_message] to=%s FAILED: %s", to, exc)
            raise

    def send_document(
        self,
        *,
        access_token: str,
        phone_number_id: str,
        to: str,
        document_url: str,
        filename: str,
        caption: str | None = None,
    ) -> dict[str, Any]:
        client = WhatsAppClient(access_token=access_token)
        return client.send_document_message(
            phone_number_id=phone_number_id,
            to=to,
            document_url=document_url,
            filename=filename,
            caption=caption,
        )

    def send_template_message(
        self,
        *,
        access_token: str,
        phone_number_id: str,
        to: str,
        template_name: str,
        language_code: str = "pt_BR",
        components: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Send an approved HSM template message.
        Used for outbound messages outside the 24h customer-service window.
        """
        import httpx
        url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
            },
        }
        if components:
            payload["template"]["components"] = components
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        response = httpx.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()