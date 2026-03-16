"""Fluxo de chatbot — Limpeza"""
from __future__ import annotations
from typing import Any

from app.domains._shared.flow_helpers import (
    safe_text, current_context, save_state,
    reply_text, reply_buttons, is_yes, is_no, is_reset,
    resolve_by_number_or_text, build_numbered_list, money_br, quote_summary_text,
)
from app.domains.cleaning import pricing_rules as PRICING

DOMAIN_LABEL = "Limpeza"
SERVICE_DISPLAY = ["Limpeza Residencial", "Limpeza Comercial", "Limpeza Pós-Obra", "Limpeza Pesada", "Limpeza de Mudança", "Limpeza de Estofados"]
SERVICE_IDS = ["limpeza_residencial", "limpeza_comercial", "limpeza_pos_obra", "limpeza_pesada", "limpeza_mudanca", "limpeza_estofados"]
SIZE_DISPLAY = ["Até 50 m²", "51 a 100 m²", "101 a 200 m²", "Acima de 200 m²"]
SIZE_IDS = ["ate_50m2", "51_100m2", "101_200m2", "acima_200m2"]
PROP_DISPLAY = ["Casa", "Apartamento", "Comercial / Escritório", "Outro"]
PROP_IDS = ["casa", "apartamento", "comercial", "outro"]
EXTRAS_MAP = {"1": "extra_janelas", "2": "extra_sacada", "3": "extra_area_externa", "4": "extra_armarios", "5": "extra_fogao"}


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
            text=f"Olá, *{name}*! 👋 Bem-vindo(a) ao serviço de *Limpeza*!\n\nQue tipo de limpeza você precisa?\n\n{build_numbered_list(SERVICE_DISPLAY)}\n\nDigite o número ou nome do serviço.",
            next_step="service_type", context=ctx)

    if step == "service_type":
        picked = resolve_by_number_or_text(txt, SERVICE_IDS) or resolve_by_number_or_text(txt, SERVICE_DISPLAY)
        if not picked:
            return reply_text(conversation, db, text=f"Não entendi. Informe o número de 1 a {len(SERVICE_IDS)}.\n\n{build_numbered_list(SERVICE_DISPLAY)}", next_step="service_type", context=ctx)
        if picked in SERVICE_DISPLAY:
            picked = SERVICE_IDS[SERVICE_DISPLAY.index(picked)]
        ctx["service_type"] = picked
        if picked == "limpeza_estofados":
            ctx["property_size"] = "ate_50m2"
            return reply_text(conversation, db, text="Quantas peças deseja higienizar? Ex: *2 sofás, 1 colchão*", next_step="rooms_count", context=ctx)
        return reply_text(conversation, db,
            text=f"Qual o tipo de imóvel?\n\n{build_numbered_list(PROP_DISPLAY)}",
            next_step="property_type", context=ctx)

    if step == "property_type":
        picked = resolve_by_number_or_text(txt, PROP_IDS) or resolve_by_number_or_text(txt, PROP_DISPLAY)
        if not picked:
            return reply_text(conversation, db, text=f"Informe o número de 1 a {len(PROP_IDS)}.\n\n{build_numbered_list(PROP_DISPLAY)}", next_step="property_type", context=ctx)
        if picked in PROP_DISPLAY:
            picked = PROP_IDS[PROP_DISPLAY.index(picked)]
        ctx["property_type"] = picked
        return reply_text(conversation, db,
            text=f"Qual o tamanho aproximado do imóvel?\n\n{build_numbered_list(SIZE_DISPLAY)}",
            next_step="property_size", context=ctx)

    if step == "property_size":
        picked = resolve_by_number_or_text(txt, SIZE_IDS) or resolve_by_number_or_text(txt, SIZE_DISPLAY)
        if not picked:
            return reply_text(conversation, db, text=f"Informe o número de 1 a {len(SIZE_IDS)}.\n\n{build_numbered_list(SIZE_DISPLAY)}", next_step="property_size", context=ctx)
        if picked in SIZE_DISPLAY:
            picked = SIZE_IDS[SIZE_DISPLAY.index(picked)]
        ctx["property_size"] = picked
        return reply_text(conversation, db, text="Quantos cômodos tem o imóvel? (quartos + salas + banheiros) Ex: *5*", next_step="rooms_count", context=ctx)

    if step == "rooms_count":
        ctx["rooms_count"] = txt.strip() or "não informado"
        return reply_buttons(conversation, db,
            text="Deseja adicionar serviços extras?\n\n1) Limpeza de janelas (+R$80)\n2) Sacada/varanda (+R$60)\n3) Área externa (+R$90)\n4) Interior de armários (+R$50)\n5) Fogão/forno (+R$40)",
            buttons=[{"id": "extras_sim", "title": "Sim, quero extras"}, {"id": "extras_nao", "title": "Não obrigado"}],
            next_step="extras_choice", context=ctx)

    if step == "extras_choice":
        if is_yes(txt) or "sim" in txt.lower():
            return reply_text(conversation, db,
                text="Informe os números dos extras separados por vírgula. Ex: *1, 3*\n\n1) Limpeza de janelas (+R$80)\n2) Sacada/varanda (+R$60)\n3) Área externa (+R$90)\n4) Interior de armários (+R$50)\n5) Fogão/forno (+R$40)",
                next_step="extras_select", context=ctx)
        ctx["selected_extras"] = []
        return reply_text(conversation, db, text="Qual o *endereço completo* para o atendimento? (Rua, número, bairro, cidade)", next_step="address", context=ctx)

    if step == "extras_select":
        ctx["selected_extras"] = [EXTRAS_MAP[n.strip()] for n in txt.split(",") if n.strip() in EXTRAS_MAP]
        return reply_text(conversation, db, text="Qual o *endereço completo* para o atendimento? (Rua, número, bairro, cidade)", next_step="address", context=ctx)

    if step == "address":
        if len(txt) < 5:
            return reply_text(conversation, db, text="Por favor, informe o endereço completo.", next_step="address", context=ctx)
        ctx["address"] = txt
        return reply_text(conversation, db, text="Tem alguma observação especial? (responda *não* para pular)", next_step="notes", context=ctx)

    if step == "notes":
        if not is_no(txt):
            ctx["notes"] = txt
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
                text=f"✅ *Orçamento confirmado!*\nTotal: *{money_br(ctx.get('estimated_total', 0))}*\n\nAgora vamos agendar. 📅\nQual data e período você prefere? Ex: *segunda-feira, manhã*",
                next_step="schedule", context=ctx,
                extra={"quote_preview": quote_data, "action_create_quote": True})
        save_state(conversation, db, next_step="start", context={})
        return reply_text(conversation, db, text=f"Tudo bem! Vamos recomeçar.\n\n{build_numbered_list(SERVICE_DISPLAY)}", next_step="service_type", context={})

    if step == "schedule":
        ctx["schedule_preference"] = txt
        return reply_text(conversation, db,
            text=f"🎉 Perfeito, *{name}*! Agendamento para *{txt}* registrado.\nEntraremos em contato para confirmar. Posso ajudar em mais alguma coisa?",
            next_step="done", context=ctx)

    return reply_text(conversation, db, text="Digite *menu* para reiniciar o atendimento.", next_step="start", context=ctx)
