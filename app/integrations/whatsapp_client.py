from __future__ import annotations

import hashlib
import hmac
from typing import Any

import requests

from app.core.config import settings


class WhatsAppClient:
    def __init__(self, access_token: str | None = None):
        self.access_token = access_token
        self.base_url = f"{settings.whatsapp_api_base_url}/{settings.whatsapp_api_version}"

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def verify_signature(self, raw_body: bytes, signature_header: str | None) -> bool:
        app_secret = settings.whatsapp_app_secret
        if not app_secret:
            return True

        if not signature_header or not signature_header.startswith("sha256="):
            return False

        expected = hmac.new(
            key=app_secret.encode("utf-8"),
            msg=raw_body,
            digestmod=hashlib.sha256,
        ).hexdigest()

        received = signature_header.replace("sha256=", "", 1)
        return hmac.compare_digest(expected, received)

    def get_media_url(self, media_id: str) -> str | None:
        if not self.access_token or not media_id:
            return None

        response = requests.get(
            f"{self.base_url}/{media_id}",
            headers=self._headers(),
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("url")

    def send_text_message(self, phone_number_id: str, to: str, body: str) -> dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/{phone_number_id}/messages",
            headers=self._headers(),
            json={
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": body},
            },
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def send_document_message(
        self,
        phone_number_id: str,
        to: str,
        document_url: str,
        filename: str,
        caption: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "document",
            "document": {
                "link": document_url,
                "filename": filename,
            },
        }
        if caption:
            payload["document"]["caption"] = caption

        response = requests.post(
            f"{self.base_url}/{phone_number_id}/messages",
            headers=self._headers(),
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def send_template_message(
        self,
        phone_number_id: str,
        to: str,
        template_name: str,
        language_code: str = "pt_BR",
        components: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
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

        response = requests.post(
            f"{self.base_url}/{phone_number_id}/messages",
            headers=self._headers(),
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def send_buttons_message(
        self,
        phone_number_id: str,
        to: str,
        body: str,
        buttons: list[dict[str, str]],
    ) -> dict[str, Any]:
        interactive_buttons = []
        for btn in buttons[:3]:
            interactive_buttons.append(
                {
                    "type": "reply",
                    "reply": {
                        "id": btn["id"],
                        "title": btn["title"][:20],
                    },
                }
            )

        response = requests.post(
            f"{self.base_url}/{phone_number_id}/messages",
            headers=self._headers(),
            json={
                "messaging_product": "whatsapp",
                "to": to,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {"text": body},
                    "action": {"buttons": interactive_buttons},
                },
            },
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def send_list_message(
        self,
        phone_number_id: str,
        to: str,
        header: str,
        body: str,
        button_text: str,
        sections: list[dict[str, Any]],
    ) -> dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/{phone_number_id}/messages",
            headers=self._headers(),
            json={
                "messaging_product": "whatsapp",
                "to": to,
                "type": "interactive",
                "interactive": {
                    "type": "list",
                    "header": {"type": "text", "text": header[:60]},
                    "body": {"text": body},
                    "action": {
                        "button": button_text[:20],
                        "sections": sections[:10],
                    },
                },
            },
            timeout=20,
        )
        response.raise_for_status()
        return response.json()