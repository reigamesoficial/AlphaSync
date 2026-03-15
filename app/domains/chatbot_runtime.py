from __future__ import annotations

from typing import Any


def build_prompt_from_settings(
    *,
    domain_key: str,
    company: Any,
    conversation: Any,
    client: Any,
    inbound_message: dict[str, Any],
    defaults: dict[str, Any],
) -> dict[str, Any]:
    bot_cfg = defaults.get("bot", {})
    fields_cfg = defaults.get("fields", {})
    required_fields = fields_cfg.get("required", [])
    catalog = ((defaults.get("catalog") or {}).get("services") or [])

    context = conversation.bot_context or {}

    if "service_type" in required_fields and not context.get("service_type"):
        options = ", ".join(catalog[:6]) if catalog else "serviço"
        return {
            "action": "reply_text",
            "next_step": "service_type",
            "text": f"Olá, {client.name}. Qual serviço você precisa? Exemplos: {options}.",
        }

    if "address" in required_fields and not context.get("address"):
        return {
            "action": "reply_text",
            "next_step": "address",
            "text": "Perfeito. Me envie o endereço completo do atendimento.",
        }

    return {
        "action": "reply_text",
        "next_step": "human_or_quote",
        "text": "Recebi seus dados. Vou seguir com o atendimento e orçamento.",
        "domain_key": domain_key,
    }