"""Fluxo de chatbot — Câmeras de Segurança"""
from __future__ import annotations
from typing import Any

from app.domains._shared.flow_helpers import (
    safe_text, current_context, save_state,
    reply_text, reply_buttons, is_yes, is_no, is_reset,
    resolve_by_number_or_text, build_numbered_list, money_br, quote_summary_text,
)
from app.domains.security_cameras import pricing_rules as PRICING

DOMAIN_LABEL = "Câmeras de Segurança"
SERVICE_DISPLAY = ["Instalação de Câmeras", "Manutenção do Sistema", "Ampliação do Sistema", "Configuração de Acesso Remoto", "Troca de DVR / NVR", "Visita Técnica"]
SERVICE_IDS = ["instalacao_cameras", "manutencao_cameras", "ampliacao_cameras", "configuracao_remota", "troca_dvr_nvr", "visita_tecnica"]
PROP_DISPLAY = ["Residência", "Comércio / Loja", "Empresa / Escritório", "Indústria", "Condomínio", "Estacionamento"]
PROP_IDS = ["residencia", "comercio", "empresa", "industria", "condominio", "estacionamento"]
CAM_DISPLAY = ["1 a 2 câmeras", "3 a 4 câmeras", "5 a 8 câmeras", "9 a 16 câmeras", "Acima de 16 câmeras"]
CAM_IDS = ["1_2", "3_4", "5_8", "9_16", "acima_16"]
REC_DISPLAY = ["DVR (câmeras analógicas)", "NVR (câmeras IP)", "Nuvem (cloud)", "Não sei / quero indicação"]
REC_IDS = ["dvr", "nvr", "nuvem", "nao_sei"]


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
            text=f"Olá, *{name}*! 📷 Bem-vindo(a) ao serviço de *Câmeras de Segurança*!\n\nQual serviço você precisa?\n\n{build_numbered_list(SERVICE_DISPLAY)}\n\nDigite o número ou nome do serviço.",
            next_step="service_type", context=ctx)

    if step == "service_type":
        picked = resolve_by_number_or_text(txt, SERVICE_IDS) or resolve_by_number_or_text(txt, SERVICE_DISPLAY)
        if not picked:
            return reply_text(conversation, db, text=f"Não entendi. Informe o número de 1 a {len(SERVICE_IDS)}.\n\n{build_numbered_list(SERVICE_DISPLAY)}", next_step="service_type", context=ctx)
        if picked in SERVICE_DISPLAY:
            picked = SERVICE_IDS[SERVICE_DISPLAY.index(picked)]
        ctx["service_type"] = picked
        if picked in ("configuracao_remota", "visita_tecnica"):
            return reply_text(conversation, db, text="Qual o *endereço completo* para o atendimento? (Rua, número, bairro, cidade)", next_step="address", context=ctx)
        return reply_text(conversation, db,
            text=f"Qual o tipo de local?\n\n{build_numbered_list(PROP_DISPLAY)}",
            next_step="property_type", context=ctx)

    if step == "property_type":
        picked = resolve_by_number_or_text(txt, PROP_IDS) or resolve_by_number_or_text(txt, PROP_DISPLAY)
        if not picked:
            return reply_text(conversation, db, text=f"Informe o número de 1 a {len(PROP_IDS)}.\n\n{build_numbered_list(PROP_DISPLAY)}", next_step="property_type", context=ctx)
        if picked in PROP_DISPLAY:
            picked = PROP_IDS[PROP_DISPLAY.index(picked)]
        ctx["property_type"] = picked
        return reply_text(conversation, db,
            text=f"Quantas câmeras serão instaladas/adicionadas?\n\n{build_numbered_list(CAM_DISPLAY)}",
            next_step="camera_count", context=ctx)

    if step == "camera_count":
        picked = resolve_by_number_or_text(txt, CAM_IDS) or resolve_by_number_or_text(txt, CAM_DISPLAY)
        if not picked:
            return reply_text(conversation, db, text=f"Informe o número de 1 a {len(CAM_IDS)}.\n\n{build_numbered_list(CAM_DISPLAY)}", next_step="camera_count", context=ctx)
        if picked in CAM_DISPLAY:
            picked = CAM_IDS[CAM_DISPLAY.index(picked)]
        ctx["camera_count"] = picked
        return reply_text(conversation, db,
            text=f"Qual o tipo de gravação/armazenamento?\n\n{build_numbered_list(REC_DISPLAY)}",
            next_step="recording_type", context=ctx)

    if step == "recording_type":
        picked = resolve_by_number_or_text(txt, REC_IDS) or resolve_by_number_or_text(txt, REC_DISPLAY)
        if not picked:
            return reply_text(conversation, db, text=f"Informe o número de 1 a {len(REC_IDS)}.\n\n{build_numbered_list(REC_DISPLAY)}", next_step="recording_type", context=ctx)
        if picked in REC_DISPLAY:
            picked = REC_IDS[REC_DISPLAY.index(picked)]
        ctx["recording_type"] = picked
        return reply_text(conversation, db, text="Qual o *endereço completo* para o atendimento? (Rua, número, bairro, cidade)", next_step="address", context=ctx)

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
                text=f"✅ *Orçamento confirmado!*\nTotal: *{money_br(ctx.get('estimated_total', 0))}*\n\n📅 Qual data e período você prefere? Ex: *sábado, manhã*",
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
