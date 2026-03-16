"""Fluxo de chatbot — Dedetização / Pest Control"""
from __future__ import annotations
from typing import Any

from app.domains._shared.flow_helpers import (
    safe_text, current_context, save_state,
    reply_text, reply_buttons, is_yes, is_no, is_reset,
    resolve_by_number_or_text, build_numbered_list, money_br, quote_summary_text,
)
from app.domains.pest_control import pricing_rules as PRICING

DOMAIN_LABEL = "Dedetização"
PEST_DISPLAY = ["Baratas", "Ratos / Camundongos", "Cupins", "Formigas", "Mosquitos / Dengue", "Percevejos", "Pombos", "Múltiplas pragas"]
PEST_IDS = ["baratas", "ratos", "cupins", "formigas", "mosquitos", "percevejos", "pombos", "multiplas"]
PROP_DISPLAY = ["Residência", "Comércio / Loja", "Restaurante / Alimentação", "Indústria / Armazém", "Condomínio"]
PROP_IDS = ["residencia", "comercio", "restaurante", "industria", "condominio"]
SIZE_DISPLAY = ["Até 100 m²", "101 a 300 m²", "301 a 600 m²", "Acima de 600 m²"]
SIZE_IDS = ["ate_100m2", "101_300m2", "301_600m2", "acima_600m2"]
INFESTATION_DISPLAY = ["Leve (poucos insetos)", "Moderada (frequente)", "Severa (alta presença)"]
INFESTATION_IDS = ["leve", "moderada", "severa"]


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
            text=f"Olá, *{name}*! 🐛 Bem-vindo(a) ao serviço de *Dedetização*!\n\nQual tipo de praga está com problema?\n\n{build_numbered_list(PEST_DISPLAY)}\n\nDigite o número ou tipo de praga.",
            next_step="pest_type", context=ctx)

    if step == "pest_type":
        picked = resolve_by_number_or_text(txt, PEST_IDS) or resolve_by_number_or_text(txt, PEST_DISPLAY)
        if not picked:
            return reply_text(conversation, db, text=f"Não entendi. Informe o número de 1 a {len(PEST_IDS)}.\n\n{build_numbered_list(PEST_DISPLAY)}", next_step="pest_type", context=ctx)
        if picked in PEST_DISPLAY:
            picked = PEST_IDS[PEST_DISPLAY.index(picked)]
        ctx["pest_type"] = picked
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
            text=f"Qual o tamanho aproximado do local?\n\n{build_numbered_list(SIZE_DISPLAY)}",
            next_step="property_size", context=ctx)

    if step == "property_size":
        picked = resolve_by_number_or_text(txt, SIZE_IDS) or resolve_by_number_or_text(txt, SIZE_DISPLAY)
        if not picked:
            return reply_text(conversation, db, text=f"Informe o número de 1 a {len(SIZE_IDS)}.\n\n{build_numbered_list(SIZE_DISPLAY)}", next_step="property_size", context=ctx)
        if picked in SIZE_DISPLAY:
            picked = SIZE_IDS[SIZE_DISPLAY.index(picked)]
        ctx["property_size"] = picked
        return reply_text(conversation, db,
            text=f"Qual o nível de infestação?\n\n{build_numbered_list(INFESTATION_DISPLAY)}",
            next_step="infestation_level", context=ctx)

    if step == "infestation_level":
        picked = resolve_by_number_or_text(txt, INFESTATION_IDS) or resolve_by_number_or_text(txt, INFESTATION_DISPLAY)
        if not picked:
            return reply_text(conversation, db, text=f"Informe o número de 1 a {len(INFESTATION_IDS)}.\n\n{build_numbered_list(INFESTATION_DISPLAY)}", next_step="infestation_level", context=ctx)
        if picked in INFESTATION_DISPLAY:
            picked = INFESTATION_IDS[INFESTATION_DISPLAY.index(picked)]
        ctx["infestation_level"] = picked
        return reply_buttons(conversation, db,
            text="⚠️ Há animais domésticos (pets) no local?\n\n_Isso é importante para definirmos o produto adequado._",
            buttons=[{"id": "pets_sim", "title": "Sim, tenho pets"}, {"id": "pets_nao", "title": "Não tenho pets"}],
            next_step="has_pets", context=ctx)

    if step == "has_pets":
        if is_yes(txt) or "sim" in txt.lower() or "pet" in txt.lower():
            ctx["has_pets"] = "Sim"
        else:
            ctx["has_pets"] = "Não"
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
                text=f"✅ *Orçamento confirmado!*\nTotal: *{money_br(ctx.get('estimated_total', 0))}*\n\n📅 Qual data e período você prefere? Ex: *sexta-feira, manhã*",
                next_step="schedule", context=ctx,
                extra={"quote_preview": quote_data, "action_create_quote": True})
        save_state(conversation, db, next_step="start", context={})
        return reply_text(conversation, db, text=f"Vamos recomeçar!\n\n{build_numbered_list(PEST_DISPLAY)}", next_step="pest_type", context={})

    if step == "schedule":
        ctx["schedule_preference"] = txt
        return reply_text(conversation, db,
            text=f"🎉 Perfeito, *{name}*! Agendamento para *{txt}* registrado.\nEntraremos em contato para confirmar. Posso ajudar em mais alguma coisa?",
            next_step="done", context=ctx)

    return reply_text(conversation, db, text="Digite *menu* para reiniciar o atendimento.", next_step="start", context=ctx)
