"""
Helpers compartilhados entre todos os domínios de chatbot.

Esses helpers seguem o mesmo padrão do protection_network.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy.orm.attributes import flag_modified

RESET_WORDS = {"reiniciar", "recomeçar", "menu", "reset", "inicio", "início", "voltar"}
YES_WORDS = {"sim", "s", "yes", "y", "1"}
NO_WORDS = {"não", "nao", "n", "no", "2"}
CONFIRM_WORDS = {"confirmar", "fechar", "ok", "seguir", "continuar", "confirmo"}


def safe_text(inbound_message: dict[str, Any]) -> str:
    return (
        inbound_message.get("interactive_reply_id")
        or inbound_message.get("interactive_reply_title")
        or inbound_message.get("message_text")
        or ""
    ).strip()


def current_context(conversation) -> dict[str, Any]:
    return dict(conversation.bot_context or {})


def json_safe(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [json_safe(i) for i in obj]
    return obj


def save_state(conversation, db, *, next_step: str, context: dict[str, Any]) -> None:
    conversation.bot_step = next_step
    conversation.bot_context = json_safe(context)
    flag_modified(conversation, "bot_context")
    db.flush()


def reply_text(
    conversation, db, *, text: str, next_step: str, context: dict[str, Any],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    save_state(conversation, db, next_step=next_step, context=context)
    payload = {"action": "reply_text", "text": text, "next_step": next_step, "context": context}
    if extra:
        payload.update(extra)
    return payload


def reply_buttons(
    conversation, db, *, text: str, next_step: str, context: dict[str, Any],
    buttons: list[dict[str, str]], extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    save_state(conversation, db, next_step=next_step, context=context)
    payload = {
        "action": "reply_buttons", "text": text, "buttons": buttons,
        "next_step": next_step, "context": context,
    }
    if extra:
        payload.update(extra)
    return payload


def reply_list(
    conversation, db, *, header: str, body: str, button_text: str,
    sections: list[dict[str, Any]], next_step: str, context: dict[str, Any],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    save_state(conversation, db, next_step=next_step, context=context)
    payload = {
        "action": "reply_list", "header": header, "text": body,
        "button_text": button_text, "sections": sections,
        "next_step": next_step, "context": context,
    }
    if extra:
        payload.update(extra)
    return payload


def money_br(value: Any) -> str:
    try:
        v = Decimal(str(value)).quantize(Decimal("0.01"))
        s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {s}"
    except Exception:
        return "R$ 0,00"


def is_yes(text: str) -> bool:
    return text.strip().lower() in YES_WORDS


def is_no(text: str) -> bool:
    return text.strip().lower() in NO_WORDS


def is_reset(text: str) -> bool:
    return text.strip().lower() in RESET_WORDS


def build_numbered_list(items: list[str]) -> str:
    return "\n".join(f"{i}) {item}" for i, item in enumerate(items, 1))


def resolve_by_number_or_text(text: str, options: list[str]) -> str | None:
    t = text.strip().lower()
    if t.isdigit():
        idx = int(t) - 1
        if 0 <= idx < len(options):
            return options[idx]
    for opt in options:
        if opt.lower() == t:
            return opt
    return None


def build_list_rows(items: list[str], prefix: str = "opt") -> list[dict[str, str]]:
    return [{"id": f"{prefix}_{i}", "title": item[:24], "description": ""} for i, item in enumerate(items, 1)]


def quote_summary_text(context: dict[str, Any], domain_label: str) -> str:
    lines = [f"📋 *Resumo do Orçamento — {domain_label}*\n"]
    field_labels = {
        "customer_name": "Nome",
        "address": "Endereço",
        "service_type": "Serviço",
        "property_type": "Tipo de imóvel",
        "property_size": "Tamanho",
        "rooms_count": "Cômodos",
        "urgency": "Urgência",
        "equipment_type": "Equipamento",
        "btu": "BTU",
        "pest_type": "Praga",
        "infestation_level": "Infestação",
        "has_pets": "Tem pets",
        "camera_count": "Câmeras",
        "recording_type": "Gravação",
        "service_location": "Local",
        "glass_type": "Tipo de vidro",
        "finish_type": "Acabamento",
        "dimensions": "Medidas",
        "notes": "Observações",
    }
    for key, label in field_labels.items():
        val = context.get(key)
        if val and str(val).strip():
            lines.append(f"• {label}: {val}")

    total = context.get("estimated_total")
    if total:
        lines.append(f"\n💰 *Total estimado: {money_br(total)}*")

    lines.append("\nDeseja confirmar ou alterar algum dado?")
    return "\n".join(lines)
