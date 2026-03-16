"""Fluxo de chatbot — Vidraçaria / Glass Installation"""
from __future__ import annotations
from typing import Any

from app.domains._shared.flow_helpers import (
    safe_text, current_context, save_state,
    reply_text, reply_buttons, is_yes, is_no, is_reset,
    resolve_by_number_or_text, build_numbered_list, money_br, quote_summary_text,
)
from app.domains.glass_installation import pricing_rules as PRICING

DOMAIN_LABEL = "Vidraçaria"
SERVICE_DISPLAY = ["Box de Banheiro", "Janela de Vidro", "Porta de Vidro", "Espelho Sob Medida", "Fechamento de Varanda", "Divisória de Vidro"]
SERVICE_IDS = ["box_banheiro", "janela_vidro", "porta_vidro", "espelho_medida", "fechamento_varanda", "divisoria_vidro"]
GLASS_DISPLAY = ["Temperado (segurança)", "Laminado (anti-estilhaço)", "Jateado (privacidade)", "Cristal (transparente)", "Espelhado"]
GLASS_IDS = ["temperado", "laminado", "jateado", "cristal", "espelhado"]
FINISH_DISPLAY = ["Alumínio Natural", "Alumínio Preto", "Inox Escovado", "Box Click", "Embutido / Sem perfil"]
FINISH_IDS = ["aluminio", "aluminio_preto", "inox", "box_click", "embutido"]


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
            text=f"Olá, *{name}*! 🪟 Bem-vindo(a) à *Vidraçaria*!\n\nQual serviço você precisa?\n\n{build_numbered_list(SERVICE_DISPLAY)}\n\nDigite o número ou nome do serviço.",
            next_step="service_type", context=ctx)

    if step == "service_type":
        picked = resolve_by_number_or_text(txt, SERVICE_IDS) or resolve_by_number_or_text(txt, SERVICE_DISPLAY)
        if not picked:
            return reply_text(conversation, db, text=f"Não entendi. Informe o número de 1 a {len(SERVICE_IDS)}.\n\n{build_numbered_list(SERVICE_DISPLAY)}", next_step="service_type", context=ctx)
        if picked in SERVICE_DISPLAY:
            picked = SERVICE_IDS[SERVICE_DISPLAY.index(picked)]
        ctx["service_type"] = picked
        if picked == "espelho_medida":
            ctx["glass_type"] = "espelhado"
            return reply_text(conversation, db,
                text="Quais as medidas do espelho?\nInforme *largura x altura* em metros. Ex: *1.20x0.80*",
                next_step="dimensions", context=ctx)
        return reply_text(conversation, db,
            text=f"Qual o tipo de vidro?\n\n{build_numbered_list(GLASS_DISPLAY)}",
            next_step="glass_type", context=ctx)

    if step == "glass_type":
        picked = resolve_by_number_or_text(txt, GLASS_IDS) or resolve_by_number_or_text(txt, GLASS_DISPLAY)
        if not picked:
            return reply_text(conversation, db, text=f"Informe o número de 1 a {len(GLASS_IDS)}.\n\n{build_numbered_list(GLASS_DISPLAY)}", next_step="glass_type", context=ctx)
        if picked in GLASS_DISPLAY:
            picked = GLASS_IDS[GLASS_DISPLAY.index(picked)]
        ctx["glass_type"] = picked
        return reply_text(conversation, db,
            text="Quais as medidas?\nInforme *largura x altura* em metros. Ex: *0.90x2.10* ou *1.50x2.00*",
            next_step="dimensions", context=ctx)

    if step == "dimensions":
        dims = txt.strip().replace(" ", "").replace("X", "x")
        if "x" not in dims.lower() and "," not in dims:
            return reply_text(conversation, db,
                text="Por favor, informe as medidas no formato *LarguraXAltura*. Ex: *0.90x2.10*",
                next_step="dimensions", context=ctx)
        ctx["dimensions"] = dims
        return reply_text(conversation, db,
            text=f"Qual o acabamento desejado?\n\n{build_numbered_list(FINISH_DISPLAY)}",
            next_step="finish_type", context=ctx)

    if step == "finish_type":
        picked = resolve_by_number_or_text(txt, FINISH_IDS) or resolve_by_number_or_text(txt, FINISH_DISPLAY)
        if not picked:
            return reply_text(conversation, db, text=f"Informe o número de 1 a {len(FINISH_IDS)}.\n\n{build_numbered_list(FINISH_DISPLAY)}", next_step="finish_type", context=ctx)
        if picked in FINISH_DISPLAY:
            picked = FINISH_IDS[FINISH_DISPLAY.index(picked)]
        ctx["finish_type"] = picked
        return reply_text(conversation, db,
            text="Qual o *endereço completo* para medição/instalação? (Rua, número, bairro, cidade)",
            next_step="address", context=ctx)

    if step == "address":
        if len(txt) < 5:
            return reply_text(conversation, db, text="Por favor, informe o endereço completo.", next_step="address", context=ctx)
        ctx["address"] = txt
        quote_data = PRICING.calculate(ctx)
        ctx["estimated_total"] = quote_data["totals"]["total_value"]
        ctx["_quote_data"] = quote_data
        ctx_display = dict(ctx)
        dims = ctx.get("dimensions", "")
        if dims:
            try:
                parts = dims.replace("x", ",").replace("X", ",").split(",")
                w, h = float(parts[0]), float(parts[1])
                ctx_display["dimensions"] = f"{w:.2f}m x {h:.2f}m = {round(w*h, 2)}m²"
            except Exception:
                pass
        return reply_buttons(conversation, db,
            text=quote_summary_text(ctx_display, DOMAIN_LABEL),
            buttons=[{"id": "confirm_yes", "title": "✅ Confirmar"}, {"id": "confirm_no", "title": "✏️ Alterar dados"}],
            next_step="quote_confirm", context=ctx)

    if step == "quote_confirm":
        if is_yes(txt) or "confirm" in txt.lower():
            quote_data = ctx.get("_quote_data") or PRICING.calculate(ctx)
            return reply_text(conversation, db,
                text=f"✅ *Orçamento confirmado!*\nTotal estimado: *{money_br(ctx.get('estimated_total', 0))}*\n\n_Valor final confirmado após visita de medição._\n\n📅 Qual data e período você prefere para a visita? Ex: *segunda, tarde*",
                next_step="schedule", context=ctx,
                extra={"quote_preview": quote_data, "action_create_quote": True})
        save_state(conversation, db, next_step="start", context={})
        return reply_text(conversation, db, text=f"Vamos recomeçar!\n\n{build_numbered_list(SERVICE_DISPLAY)}", next_step="service_type", context={})

    if step == "schedule":
        ctx["schedule_preference"] = txt
        return reply_text(conversation, db,
            text=f"🎉 Perfeito, *{name}*! Visita agendada para *{txt}*.\nEntraremos em contato para confirmar. Posso ajudar em mais alguma coisa?",
            next_step="done", context=ctx)

    return reply_text(conversation, db, text="Digite *menu* para reiniciar o atendimento.", next_step="start", context=ctx)
