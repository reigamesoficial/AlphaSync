"""Fluxo de chatbot — Ar Condicionado (HVAC)"""
from __future__ import annotations
from typing import Any

from app.domains._shared.flow_helpers import (
    safe_text, current_context, save_state,
    reply_text, reply_buttons, is_yes, is_no, is_reset,
    resolve_by_number_or_text, build_numbered_list, money_br, quote_summary_text,
)
from app.domains.hvac import pricing_rules as PRICING

DOMAIN_LABEL = "Ar Condicionado"
SERVICE_DISPLAY = ["Instalação de Ar Condicionado", "Manutenção Preventiva", "Limpeza / Higienização", "Carga de Gás", "Reparo / Defeito"]
SERVICE_IDS = ["instalacao_ar", "manutencao_ar", "limpeza_ar", "carga_gas", "reparo_ar"]
EQUIP_DISPLAY = ["Split", "Split Inverter", "Janeleiro", "Portátil", "Cassete / Central"]
EQUIP_IDS = ["split", "split_inverter", "janeleiro", "portatil", "cassete"]
BTU_DISPLAY = ["Até 9.000 BTU", "12.000 BTU", "18.000 BTU", "24.000 BTU", "30.000 BTU", "36.000 BTU ou mais"]
BTU_IDS = ["ate_9000", "12000", "18000", "24000", "30000", "36000_mais"]


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
            text=f"Olá, *{name}*! ❄️ Bem-vindo(a) ao serviço de *Ar Condicionado*!\n\nQual serviço você precisa?\n\n{build_numbered_list(SERVICE_DISPLAY)}\n\nDigite o número ou nome do serviço.",
            next_step="service_type", context=ctx)

    if step == "service_type":
        picked = resolve_by_number_or_text(txt, SERVICE_IDS) or resolve_by_number_or_text(txt, SERVICE_DISPLAY)
        if not picked:
            return reply_text(conversation, db, text=f"Não entendi. Informe o número de 1 a {len(SERVICE_IDS)}.\n\n{build_numbered_list(SERVICE_DISPLAY)}", next_step="service_type", context=ctx)
        if picked in SERVICE_DISPLAY:
            picked = SERVICE_IDS[SERVICE_DISPLAY.index(picked)]
        ctx["service_type"] = picked
        return reply_text(conversation, db,
            text=f"Qual o tipo de equipamento?\n\n{build_numbered_list(EQUIP_DISPLAY)}",
            next_step="equipment_type", context=ctx)

    if step == "equipment_type":
        picked = resolve_by_number_or_text(txt, EQUIP_IDS) or resolve_by_number_or_text(txt, EQUIP_DISPLAY)
        if not picked:
            return reply_text(conversation, db, text=f"Informe o número de 1 a {len(EQUIP_IDS)}.\n\n{build_numbered_list(EQUIP_DISPLAY)}", next_step="equipment_type", context=ctx)
        if picked in EQUIP_DISPLAY:
            picked = EQUIP_IDS[EQUIP_DISPLAY.index(picked)]
        ctx["equipment_type"] = picked
        return reply_text(conversation, db,
            text=f"Qual a capacidade do equipamento (BTU)?\n\n{build_numbered_list(BTU_DISPLAY)}\n\nSe não souber, informe a marca e modelo.",
            next_step="btu", context=ctx)

    if step == "btu":
        picked = resolve_by_number_or_text(txt, BTU_IDS) or resolve_by_number_or_text(txt, BTU_DISPLAY)
        if picked:
            if picked in BTU_DISPLAY:
                picked = BTU_IDS[BTU_DISPLAY.index(picked)]
            ctx["btu"] = picked
        else:
            ctx["btu"] = "12000"
            ctx["btu_nota"] = txt
        service = ctx.get("service_type", "")
        if service in ("reparo_ar", "manutencao_ar"):
            return reply_text(conversation, db,
                text="Descreva o problema ou sintoma do equipamento:\nEx: *não gela, fazendo barulho, gotejando*",
                next_step="problem_description", context=ctx)
        return reply_text(conversation, db,
            text="Qual o *endereço completo* para o atendimento? (Rua, número, bairro, cidade)",
            next_step="address", context=ctx)

    if step == "problem_description":
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
                text=f"✅ *Orçamento confirmado!*\nTotal: *{money_br(ctx.get('estimated_total', 0))}*\n\n📅 Qual data e período você prefere? Ex: *quarta-feira, manhã*",
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
