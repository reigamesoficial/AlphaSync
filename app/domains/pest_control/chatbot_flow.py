from __future__ import annotations

from app.domains.chatbot_runtime import build_prompt_from_settings
from app.domains.pest_control.domain import domain


def handle_inbound_message(*, company, conversation, client, inbound_message, db):
    defaults = domain.get_default_settings()
    return build_prompt_from_settings(
        domain_key=domain.key,
        company=company,
        conversation=conversation,
        client=client,
        inbound_message=inbound_message,
        defaults=defaults,
    )