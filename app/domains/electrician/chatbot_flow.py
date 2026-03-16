"""Fluxo de chatbot — Eletricista"""
from __future__ import annotations
from typing import Any

from app.domains._shared.flow_helpers import (
    safe_text, current_context, save_state,
    reply_text, reply_buttons, is_yes, is_no, is_reset,
    resolve_by_number_or_text, build_numbered_list, money_br, quote_summary_text,
)
from app.domains.electrician import pricing_rules as PRICING

DOMAIN_LABEL = "Eletricista"
SERVICE_DISPLAY = ["Instalação Elétrica", "Troca de Tomada / Interruptor", "Troca de Disjuntor", "Instalação de Luminária", "Instalação de Chuveiro Elétrico", "Curto Circuito / Falha Elétrica", "Manutenção Elétrica Geral"]
SERVICE_IDS = ["instalacao_eletrica", "troca_tomada", "troca_disjuntor", "instalacao_luminaria", "instalacao_chuveiro", "curto_circuito", "manutencao_eletrica"]
URGENCY_DISPLAY = ["Normal (1-3 dias)", "Urgente (hoje ou amanhã)", "Emergência (agora)"]
URGENCY_IDS = ["normal", "urgente", "emergencia"]


def handle_inbound_message(*, company, conversation, client, inbound_message, db) -> dict[str, Any]:
    txt = safe_text(inbound_message)
    ctx = current_context(conversation)
    step = conversation.bot_step or "start"
    if is_reset(txt):
        save_state(conversation, db, next_step="start", context={})
        step, ctx = "start", {}
    name = client.name or ctx.get("customer_name") or "cliente"

    if step in ("start", "greeting"):
        return reply_text(conversation, db,
            text=f"Olá, *{name}*! ⚡ Bem-vindo(a) ao serviço de *Eletricista*!\n\nQual serviço você precisa?\n\n{build_numbered_list(SERVICE_DISPLAY)}\n\nDigite o número ou nome do serviço.",
            next_step="service_type", context=ctx)

    if step == "service_type":
        picked = resolve_by_number_or_text(txt, SERVICE_IDS) or resolve_by_number_or_text(txt, SERVICE_DISPLAY)
        if not picked:
            return reply_text(conversation, db, text=f"Não entendi. Informe o número de 1 a {len(SERVICE_IDS)}.\n\n{build_numbered_list(SERVICE_DISPLAY)}", next_step="service_type", context=ctx)
        if picked in SERVICE_DISPLAY:
            picked = SERVICE_IDS[SERVICE_DISPLAY.index(picked)]
        ctx["service_type"] = picked
        return reply_text(conversation, db,
            text=f"Qual a urgência do atendimento?\n\n{build_numbered_list(URGENCY_DISPLAY)}",
            next_step="urgency", context=ctx)

    if step == "urgency":
        picked = resolve_by_number_or_text(txt, URGENCY_IDS) or resolve_by_number_or_text(txt, URGENCY_DISPLAY)
        if not picked:
            return reply_text(conversation, db, text=f"Informe o número de 1 a {len(URGENCY_IDS)}.\n\n{build_numbered_list(URGENCY_DISPLAY)}", next_step="urgency", context=ctx)
        if picked in URGENCY_DISPLAY:
            picked = URGENCY_IDS[URGENCY_DISPLAY.index(picked)]
        ctx["urgency"] = picked
        return reply_text(conversation, db,
            text="Descreva brevemente o problema ou o que precisa ser feito:\nEx: *troca de 3 tomadas na sala e cozinha*",
            next_step="description", context=ctx)

    if step == "description":
        ctx["notes"] = txt
        return reply_text(conversation, db,
            text="Qual o *endereço completo* para o atendimento? (Rua, número, bairro, cidade)",
            next_step="address", context=ctx)

    if step == "address":
        if len(txt) < 5:
            return reply_text(conversation, db, text="Por favor, informe o endereço completo.", next_step="address", context=ctx)
        ctx["address"] = txt
        quote_data = PRICING.calculate(ctx)
        ctx["estimated_total"] = quote_data["totals"]["total_value"]
        ctx["_quote_data"] = quote_data
        return reply_buttons(conversation, db,
            text=quote_summary_text(ctx, DOMAIN_LABEL),
            buttons=[{"id": "confirm_yes", "title": "✅ Confirmar"}, {"id": "confirm_no", "title": "✏️ Alterar dados"}],
            next_step="quote_confirm", context=ctx)

    if step == "quote_confirm":
        if is_yes(txt) or "confirm" in txt.lower():
            quote_data = ctx.get("_quote_data") or PRICING.calculate(ctx)
            return reply_text(conversation, db,
                text=f"✅ *Orçamento confirmado!*\nTotal: *{money_br(ctx.get('estimated_total', 0))}*\n\n📅 Qual data e período você prefere? Ex: *terça-feira, tarde*",
                next_step="schedule", context=ctx,
                extra={"quote_preview": quote_data, "action_create_quote": True})
        save_state(conversation, db, next_step="start", context={})
        return reply_text(conversation, db, text=f"Vamos recomeçar!\n\n{build_numbered_list(SERVICE_DISPLAY)}", next_step="service_type", context={})

    if step == "schedule":
        ctx["schedule_preference"] = txt
        return reply_text(conversation, db,
            text=f"🎉 Perfeito, *{name}*! Agendamento para *{txt}* registrado.\nEntraremos em contato para confirmar. Posso ajudar em mais alguma coisa?",
            next_step="done", context=ctx)

    return reply_text(conversation, db, text="Digite *menu* para reiniciar o atendimento.", next_step="start", context=ctx)
