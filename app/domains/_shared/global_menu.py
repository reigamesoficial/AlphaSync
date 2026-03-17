"""
Global Menu Layer — AlphaSync

Implements the initial interactive menu for ALL service domains.
Injected by ConversationService._execute_domain_flow() before any
domain-specific chatbot flow is invoked.

Steps handled by this module (all prefixed 'global_', plus 'start'):
  global_main_menu                → route based on user choice
  global_tech_visit_reason        → collect tech visit reason → ASSUMED
  global_tech_visit_waiting       → waiting for seller action (bot paused)
  global_tech_visit_schedule_day  → day list for tech visit appointment
  global_tech_visit_schedule_slot → slot list for tech visit appointment
  global_has_quote_schedule_day   → day list after finding existing quote
  global_has_quote_schedule_slot  → slot list after finding existing quote
  global_reschedule_day           → day list for reschedule
  global_reschedule_slot          → slot list for reschedule
  global_cancel_reason            → ask cancel reason
  global_cancel_reversible        → ask if reversible
  global_cancel_help              → ask how to help → ASSUMED
  global_done                     → end-of-flow confirmation
  global_done_confirm             → user confirms end or restarts
"""
from __future__ import annotations

from typing import Any, Callable

from sqlalchemy.orm.attributes import flag_modified

from app.domains._shared.flow_helpers import (
    current_context,
    json_safe,
    reply_buttons,
    reply_list,
    reply_text,
    safe_text,
)

# ─── Constants ────────────────────────────────────────────────────────────────

GLOBAL_STEPS = {
    "global_main_menu",
    "global_tech_visit_reason",
    "global_tech_visit_waiting",
    "global_tech_visit_schedule_day",
    "global_tech_visit_schedule_slot",
    "global_has_quote_schedule_day",
    "global_has_quote_schedule_slot",
    "global_reschedule_day",
    "global_reschedule_slot",
    "global_cancel_reason",
    "global_cancel_reversible",
    "global_cancel_help",
    "global_done",
    "global_done_confirm",
}

_WEEKDAYS_FULL = [
    "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira",
    "Sexta-feira", "Sábado", "Domingo",
]
_WEEKDAYS_SHORT = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

# ─── Predicates ──────────────────────────────────────────────────────────────

def is_global_step(step: str) -> bool:
    return step in GLOBAL_STEPS


# ─── Schedule utilities ───────────────────────────────────────────────────────

def _full_weekday_date_pt(d) -> str:
    return f"{_WEEKDAYS_FULL[d.weekday()]}, {d.day:02d}/{d.month:02d}"


def _get_schedule_cfg(company, db) -> dict[str, Any]:
    from sqlalchemy import select as _sel
    from app.db.models import CompanySettings as _CS
    cs = db.scalar(_sel(_CS).where(_CS.company_id == company.id))
    extra = (cs.extra_settings or {}) if cs else {}
    cfg = extra.get("schedule") or {}
    return {
        "slot_minutes": int(cfg.get("slot_minutes", 120)),
        "workday_start": cfg.get("workday_start", "08:00"),
        "workday_end": cfg.get("workday_end", "18:00"),
        "allowed_weekdays": list(cfg.get("allowed_weekdays", [0, 1, 2, 3, 4])),
        "tech_visit_slot_minutes": int(cfg.get("tech_visit_slot_minutes", 60)),
    }


def _compute_slots(target_date, cfg: dict[str, Any], slot_minutes: int | None = None) -> list[dict[str, Any]]:
    from datetime import datetime as _dt, timedelta as _td
    if target_date.weekday() not in list(cfg.get("allowed_weekdays", [0, 1, 2, 3, 4])):
        return []
    start_h, start_m = map(int, cfg.get("workday_start", "08:00").split(":"))
    end_h, end_m = map(int, cfg.get("workday_end", "18:00").split(":"))
    sm = slot_minutes or int(cfg.get("slot_minutes", 120))
    day_start = _dt(target_date.year, target_date.month, target_date.day, start_h, start_m)
    day_end = _dt(target_date.year, target_date.month, target_date.day, end_h, end_m)
    slots: list[dict[str, Any]] = []
    current = day_start
    while current + _td(minutes=sm) <= day_end:
        slot_end = current + _td(minutes=sm)
        slots.append({
            "id": f"slot_{current.strftime('%H%M')}",
            "label": f"{current.strftime('%H:%M')} às {slot_end.strftime('%H:%M')}",
            "start_dt": current.isoformat(),
            "end_dt": slot_end.isoformat(),
        })
        current = slot_end
    return slots


def _compute_available_days(cfg: dict[str, Any], days_ahead: int = 21) -> list[dict[str, Any]]:
    from datetime import datetime as _dt, timedelta as _td
    today = _dt.today().date()
    days: list[dict[str, Any]] = []
    for i in range(1, days_ahead + 1):
        candidate = today + _td(days=i)
        if _compute_slots(candidate, cfg):
            label = f"{_WEEKDAYS_SHORT[candidate.weekday()]} {candidate.day:02d}/{candidate.month:02d}"
            days.append({"id": f"day_{candidate.strftime('%Y%m%d')}", "date": candidate.isoformat(), "label": label})
        if len(days) >= 10:
            break
    return days


def _send_day_list(conversation, db, *, ctx: dict, days: list[dict], body: str, next_step: str) -> dict[str, Any]:
    ctx["global_available_days"] = days
    rows = [{"id": d["id"], "title": d["label"], "description": ""} for d in days]
    return reply_list(conversation, db,
        header="Dias disponíveis",
        body=body,
        button_text="Ver dias",
        sections=[{"title": "Próximos dias disponíveis", "rows": rows}],
        next_step=next_step,
        context=ctx,
    )


def _send_slot_list(conversation, db, *, ctx: dict, chosen_day: dict, cfg: dict, next_step: str, slot_minutes: int | None = None) -> dict[str, Any]:
    from datetime import date as _date_cls
    chosen_date = _date_cls.fromisoformat(chosen_day["date"])
    slots = _compute_slots(chosen_date, cfg, slot_minutes=slot_minutes)
    if not slots:
        available_days = _compute_available_days(cfg)
        if not available_days:
            return reply_text(conversation, db,
                text="No momento não há dias disponíveis. Entre em contato com nossa equipe.",
                next_step="global_done", context=ctx)
        day_step = next_step.rsplit("_slot", 1)[0] + "_day" if "_slot" in next_step else next_step
        return _send_day_list(conversation, db, ctx=ctx, days=available_days,
            body=f"Não há horários disponíveis em *{chosen_day['label']}*. Escolha outro dia:",
            next_step=day_step)
    ctx["global_schedule_date"] = chosen_day["date"]
    ctx["global_schedule_day_label"] = chosen_day["label"]
    ctx["global_schedule_slots"] = slots
    rows = [{"id": s["id"], "title": s["label"], "description": ""} for s in slots[:10]]
    return reply_list(conversation, db,
        header="Horários disponíveis",
        body=f"Ótimo! Escolha o horário para *{chosen_day['label']}*:",
        button_text="Ver horários",
        sections=[{"title": "Horários disponíveis", "rows": rows}],
        next_step=next_step,
        context=ctx,
    )


def _resolve_day(txt: str, available_days: list[dict]) -> dict | None:
    normalized = txt.strip().lower()
    for d in available_days:
        if d["id"] == txt.strip() or normalized in d["id"] or normalized in d["label"].lower():
            return d
    if len(available_days) == 1:
        return available_days[0]
    return None


def _resolve_slot(txt: str, slots: list[dict]) -> dict | None:
    normalized = txt.strip().lower()
    for s in slots:
        if s["id"] == txt.strip() or normalized in s["id"] or normalized in s["label"].lower():
            return s
    if len(slots) == 1:
        return slots[0]
    return None


def _cannot_pick_day(conversation, db, *, ctx: dict, cfg: dict, next_step: str) -> dict[str, Any]:
    available_days = _compute_available_days(cfg)
    if not available_days:
        return reply_text(conversation, db,
            text="No momento não há dias disponíveis. Entre em contato com nossa equipe.",
            next_step="global_done", context=ctx)
    return _send_day_list(conversation, db, ctx=ctx, days=available_days,
        body="Por favor, selecione um dos dias disponíveis:", next_step=next_step)


def _cannot_pick_slot(conversation, db, *, ctx: dict, slots: list[dict], next_step: str) -> dict[str, Any]:
    rows = [{"id": s["id"], "title": s["label"], "description": ""} for s in slots[:10]]
    return reply_list(conversation, db,
        header="Escolha um horário",
        body="Por favor, selecione um horário disponível:",
        button_text="Ver horários",
        sections=[{"title": "Horários", "rows": rows}],
        next_step=next_step, context=ctx)


# ─── Public API ───────────────────────────────────────────────────────────────

def show_main_menu(conversation, db, *, client, ctx: dict) -> dict[str, Any]:
    """Show the global initial menu. Sets bot_step = 'global_main_menu'."""
    name = client.name or ctx.get("customer_name") or "cliente"
    return reply_list(conversation, db,
        header="Menu de Atendimento",
        body=f"Olá, *{name}*! 👋 Em que posso ajudar hoje?",
        button_text="Ver opções",
        sections=[{
            "title": "Como posso ajudar?",
            "rows": [
                {"id": "opt_quote",      "title": "Solicitar orçamento",   "description": ""},
                {"id": "opt_tech_visit", "title": "Agendar visita técnica", "description": ""},
                {"id": "opt_has_quote",  "title": "Tenho orçamento",        "description": "Já tenho orçamento, quero agendar"},
                {"id": "opt_reschedule", "title": "Reagendar serviço",      "description": ""},
                {"id": "opt_cancel",     "title": "Cancelar agendamento",   "description": ""},
            ],
        }],
        next_step="global_main_menu",
        context=ctx,
    )


def handle_global_step(
    *,
    company,
    conversation,
    client,
    inbound_message: dict[str, Any],
    db,
    current_step: str,
    domain_caller: Callable[[], dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """
    Handle a global step.

    Returns a reply dict to send to the client, or None to delegate to the
    domain-specific chatbot flow (only possible from global_main_menu → 'opt_quote').

    `domain_caller` is a zero-arg callable that invokes the domain flow and
    returns its result; used when the user picks "Solicitar orçamento" so the
    domain greeting is sent immediately.
    """
    txt = safe_text(inbound_message)
    ctx = current_context(conversation)
    normalized = txt.strip().lower()

    # ── MAIN MENU CHOICE ──────────────────────────────────────────────────────
    if current_step == "global_main_menu":
        if normalized in {
            "opt_quote", "1",
            "solicitar orçamento", "solicitar orcamento",
            "orçamento", "orcamento", "quero orçamento", "quero orcamento",
        }:
            ctx["global_intent"] = "quote"
            ctx["global_menu_done"] = True
            if domain_caller:
                return domain_caller()
            return reply_text(conversation, db,
                text="Perfeito! Vamos iniciar seu orçamento. 😊",
                next_step="start", context=ctx)

        if normalized in {
            "opt_tech_visit", "2",
            "visita técnica", "visita tecnica",
            "agendar visita", "visita", "visita tecnica", "quero visita",
        }:
            ctx["global_intent"] = "tech_visit"
            return reply_text(conversation, db,
                text=(
                    "Certo! Para agendar a visita técnica, me descreva brevemente o motivo:\n\n"
                    "_Ex: Quero avaliar o ambiente antes de fazer a instalação._"
                ),
                next_step="global_tech_visit_reason", context=ctx)

        if normalized in {
            "opt_has_quote", "3",
            "tenho orçamento", "tenho orcamento",
            "já tenho orçamento", "ja tenho orcamento",
        }:
            ctx["global_intent"] = "has_quote"
            return _handle_has_quote(conversation, db, company=company, client=client, ctx=ctx, domain_caller=domain_caller)

        if normalized in {
            "opt_reschedule", "4",
            "reagendar", "reagendar serviço", "reagendar servico",
        }:
            ctx["global_intent"] = "reschedule"
            return _handle_reschedule_check(conversation, db, company=company, client=client, ctx=ctx)

        if normalized in {
            "opt_cancel", "5",
            "cancelar", "cancelar agendamento",
        }:
            ctx["global_intent"] = "cancel"
            return reply_text(conversation, db,
                text="Entendido. Para continuar, me informe o motivo do cancelamento:",
                next_step="global_cancel_reason", context=ctx)

        if normalized in {"opt_new_menu", "menu", "voltar", "inicio", "início", "recomeçar", "reiniciar"}:
            return show_main_menu(conversation, db, client=client, ctx=ctx)

        if normalized in {"opt_done_no", "não", "nao", "não obrigado", "nao obrigado", "tchau", "obrigado"}:
            return reply_text(conversation, db,
                text="Até logo! 😊 Se precisar de mais ajuda, é só enviar uma mensagem.",
                next_step="global_done", context=ctx)

        return show_main_menu(conversation, db, client=client, ctx=ctx)

    # ── TECH VISIT — REASON ───────────────────────────────────────────────────
    if current_step == "global_tech_visit_reason":
        ctx["global_tech_visit_reason"] = txt
        from app.db.models import ConversationStatus
        conversation.status = ConversationStatus.ASSUMED
        conversation.bot_step = "global_tech_visit_waiting"
        conversation.bot_context = json_safe(ctx)
        flag_modified(conversation, "bot_context")
        db.flush()
        return {
            "action": "assumed",
            "text": (
                "Obrigado! Recebi o motivo da visita técnica. 📋\n\n"
                "Nossa equipe vai avaliar e entrar em contato para confirmar o agendamento. "
                "Fique à vontade para adicionar mais informações se quiser!"
            ),
            "context": ctx,
        }

    # ── TECH VISIT — WAITING ──────────────────────────────────────────────────
    if current_step == "global_tech_visit_waiting":
        return reply_text(conversation, db,
            text="Sua solicitação de visita técnica já está registrada. Nossa equipe entrará em contato em breve. 😊",
            next_step="global_tech_visit_waiting", context=ctx)

    # ── TECH VISIT — SCHEDULE DAY ─────────────────────────────────────────────
    if current_step == "global_tech_visit_schedule_day":
        available_days = ctx.get("global_available_days") or []
        cfg = _get_schedule_cfg(company, db)
        if not available_days:
            available_days = _compute_available_days(cfg)
        chosen_day = _resolve_day(txt, available_days)
        if chosen_day is None:
            return _cannot_pick_day(conversation, db, ctx=ctx, cfg=cfg, next_step="global_tech_visit_schedule_day")
        return _send_slot_list(conversation, db, ctx=ctx, chosen_day=chosen_day, cfg=cfg,
            next_step="global_tech_visit_schedule_slot",
            slot_minutes=cfg.get("tech_visit_slot_minutes", 60))

    # ── TECH VISIT — SCHEDULE SLOT ────────────────────────────────────────────
    if current_step == "global_tech_visit_schedule_slot":
        slots = ctx.get("global_schedule_slots") or []
        chosen_slot = _resolve_slot(txt, slots)
        if chosen_slot is None:
            return _cannot_pick_slot(conversation, db, ctx=ctx, slots=slots, next_step="global_tech_visit_schedule_slot")
        return _confirm_tech_visit(conversation, db, company=company, client=client, ctx=ctx, chosen_slot=chosen_slot)

    # ── HAS QUOTE — SCHEDULE DAY ──────────────────────────────────────────────
    if current_step == "global_has_quote_schedule_day":
        available_days = ctx.get("global_available_days") or []
        cfg = _get_schedule_cfg(company, db)
        if not available_days:
            available_days = _compute_available_days(cfg)
        chosen_day = _resolve_day(txt, available_days)
        if chosen_day is None:
            return _cannot_pick_day(conversation, db, ctx=ctx, cfg=cfg, next_step="global_has_quote_schedule_day")
        return _send_slot_list(conversation, db, ctx=ctx, chosen_day=chosen_day, cfg=cfg,
            next_step="global_has_quote_schedule_slot")

    # ── HAS QUOTE — SCHEDULE SLOT ─────────────────────────────────────────────
    if current_step == "global_has_quote_schedule_slot":
        slots = ctx.get("global_schedule_slots") or []
        chosen_slot = _resolve_slot(txt, slots)
        if chosen_slot is None:
            return _cannot_pick_slot(conversation, db, ctx=ctx, slots=slots, next_step="global_has_quote_schedule_slot")
        return _confirm_generic_appointment(conversation, db, company=company, client=client, ctx=ctx, chosen_slot=chosen_slot)

    # ── RESCHEDULE — DAY ──────────────────────────────────────────────────────
    if current_step == "global_reschedule_day":
        available_days = ctx.get("global_available_days") or []
        cfg = _get_schedule_cfg(company, db)
        if not available_days:
            available_days = _compute_available_days(cfg)
        chosen_day = _resolve_day(txt, available_days)
        if chosen_day is None:
            return _cannot_pick_day(conversation, db, ctx=ctx, cfg=cfg, next_step="global_reschedule_day")
        return _send_slot_list(conversation, db, ctx=ctx, chosen_day=chosen_day, cfg=cfg, next_step="global_reschedule_slot")

    # ── RESCHEDULE — SLOT ─────────────────────────────────────────────────────
    if current_step == "global_reschedule_slot":
        slots = ctx.get("global_schedule_slots") or []
        chosen_slot = _resolve_slot(txt, slots)
        if chosen_slot is None:
            return _cannot_pick_slot(conversation, db, ctx=ctx, slots=slots, next_step="global_reschedule_slot")
        return _confirm_reschedule(conversation, db, company=company, client=client, ctx=ctx, chosen_slot=chosen_slot)

    # ── CANCEL — REASON ───────────────────────────────────────────────────────
    if current_step == "global_cancel_reason":
        ctx["global_cancel_reason"] = txt
        return reply_buttons(conversation, db,
            text="Entendido. Tem algo que eu possa fazer para reverter a situação?",
            buttons=[
                {"id": "cancel_reverse_yes", "title": "Sim"},
                {"id": "cancel_reverse_no", "title": "Não"},
            ],
            next_step="global_cancel_reversible", context=ctx)

    # ── CANCEL — REVERSIBLE ───────────────────────────────────────────────────
    if current_step == "global_cancel_reversible":
        if normalized in {"cancel_reverse_yes", "sim", "s", "yes", "y", "1"}:
            return reply_text(conversation, db,
                text="Como posso te ajudar? Me conte o que podemos fazer por você:",
                next_step="global_cancel_help", context=ctx)
        _cancel_latest_appointment(db, company=company, client=client)
        return reply_text(conversation, db,
            text=(
                "Agradecemos o contato. Seu cancelamento foi registrado. ✅\n\n"
                "Ficamos à disposição caso precise de nós no futuro. 😊"
            ),
            next_step="global_done", context=ctx)

    # ── CANCEL — HELP ─────────────────────────────────────────────────────────
    if current_step == "global_cancel_help":
        ctx["global_cancel_help_text"] = txt
        from app.db.models import ConversationStatus
        conversation.status = ConversationStatus.ASSUMED
        conversation.bot_step = "global_done"
        conversation.bot_context = json_safe(ctx)
        flag_modified(conversation, "bot_context")
        db.flush()
        return {
            "action": "assumed",
            "text": "Obrigado! Registrei sua mensagem. Nossa equipe entrará em contato para te ajudar. 😊",
            "context": ctx,
        }

    # ── DONE / DONE CONFIRM ───────────────────────────────────────────────────
    if current_step in {"global_done", "global_done_confirm"}:
        if normalized in {"opt_new_menu", "sim", "s", "yes", "y", "1", "menu", "voltar", "inicio", "início"}:
            ctx_clean = {k: v for k, v in ctx.items() if k.startswith("customer_name")}
            return show_main_menu(conversation, db, client=client, ctx=ctx_clean)
        if current_step == "global_done":
            return reply_buttons(conversation, db,
                text="Posso te ajudar em mais alguma coisa?",
                buttons=[
                    {"id": "opt_new_menu", "title": "Sim, voltar ao menu"},
                    {"id": "opt_done_no",  "title": "Não, obrigado"},
                ],
                next_step="global_done_confirm", context=ctx)
        return reply_text(conversation, db,
            text="Até logo! 😊 Se precisar de mais ajuda, é só enviar uma mensagem.",
            next_step="global_done", context=ctx)

    return None


# ─── Internal sub-flows ───────────────────────────────────────────────────────

def _handle_has_quote(conversation, db, *, company, client, ctx: dict, domain_caller=None) -> dict[str, Any]:
    from sqlalchemy import select
    from app.db.models import Quote, QuoteStatus

    quote = db.scalar(
        select(Quote)
        .where(
            Quote.company_id == company.id,
            Quote.client_id == client.id,
            Quote.status.in_([QuoteStatus.DRAFT, QuoteStatus.CONFIRMED]),
        )
        .order_by(Quote.created_at.desc())
    )

    if not quote:
        ctx["global_menu_done"] = True
        if domain_caller:
            result = reply_text(conversation, db,
                text="Não encontrei um orçamento disponível para este atendimento. Vou te ajudar a criar um novo! 😊",
                next_step="start", context=ctx)
            return result
        return reply_text(conversation, db,
            text="Não encontrei um orçamento disponível. Vou te ajudar a criar um novo! 😊",
            next_step="start", context=ctx)

    total_raw = float(quote.total_value or 0)
    total_str = f"R$ {total_raw:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    ctx["global_found_quote_id"] = quote.id
    ctx["global_found_quote_code"] = quote.code or f"#{quote.id}"

    cfg = _get_schedule_cfg(company, db)
    available_days = _compute_available_days(cfg)
    if not available_days:
        return reply_text(conversation, db,
            text=(
                f"Encontrei seu orçamento *{ctx['global_found_quote_code']}* — Total: {total_str}.\n\n"
                f"No momento não há dias disponíveis para agendamento. "
                f"Entre em contato com nossa equipe para finalizar."
            ),
            next_step="global_done", context=ctx)

    return _send_day_list(conversation, db, ctx=ctx, days=available_days,
        body=(
            f"Encontrei seu orçamento *{ctx['global_found_quote_code']}* — Total: {total_str}. ✅\n\n"
            f"Escolha um dia para o agendamento:"
        ),
        next_step="global_has_quote_schedule_day")


def _handle_reschedule_check(conversation, db, *, company, client, ctx: dict) -> dict[str, Any]:
    from sqlalchemy import select
    from app.db.models import Appointment, AppointmentStatus
    from datetime import datetime as _dt, timezone as _tz

    now = _dt.now(_tz.utc)
    appointment = db.scalar(
        select(Appointment)
        .where(
            Appointment.company_id == company.id,
            Appointment.client_id == client.id,
            Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]),
            Appointment.start_at > now,
        )
        .order_by(Appointment.start_at.asc())
    )

    if not appointment:
        return reply_text(conversation, db,
            text=(
                "Não encontrei um agendamento ativo para reagendar. "
                "Posso te ajudar com outra opção? Volte ao menu principal."
            ),
            next_step="global_main_menu", context=ctx)

    ctx["global_reschedule_appointment_id"] = appointment.id
    try:
        start = appointment.start_at
        if start.tzinfo is None:
            from datetime import timezone
            start = start.replace(tzinfo=timezone.utc)
        old_label = f"{_full_weekday_date_pt(start.date())} às {start.strftime('%H:%M')}"
    except Exception:
        old_label = "data anterior"
    ctx["global_reschedule_old_label"] = old_label

    cfg = _get_schedule_cfg(company, db)
    available_days = _compute_available_days(cfg)
    if not available_days:
        return reply_text(conversation, db,
            text="No momento não há dias disponíveis para reagendamento. Entre em contato com nossa equipe.",
            next_step="global_done", context=ctx)

    return _send_day_list(conversation, db, ctx=ctx, days=available_days,
        body=f"Encontrei seu agendamento de *{old_label}*. Escolha um novo dia:",
        next_step="global_reschedule_day")


def _confirm_tech_visit(conversation, db, *, company, client, ctx: dict, chosen_slot: dict) -> dict[str, Any]:
    from datetime import datetime as _dt, date as _d
    from app.repositories.appointments import AppointmentsRepository

    start_at = _dt.fromisoformat(chosen_slot["start_dt"])
    end_at = _dt.fromisoformat(chosen_slot["end_dt"])
    repo = AppointmentsRepository(db)
    repo.create_appointment(
        company_id=company.id,
        client_id=client.id,
        quote_id=None,
        address_raw=ctx.get("address") or "",
        start_at=start_at,
        end_at=end_at,
        service_type="tech_visit",
        event_title=f"Visita técnica – {client.name or 'Cliente'}",
        valor=None,
        notes=f"Motivo: {ctx.get('global_tech_visit_reason', 'não informado')}. Agendado pelo chatbot.",
    )
    db.flush()
    try:
        full_date = _full_weekday_date_pt(_d.fromisoformat(chosen_slot["start_dt"][:10]))
    except Exception:
        full_date = ctx.get("global_schedule_day_label") or chosen_slot["start_dt"][:10]
    return reply_text(conversation, db,
        text=(
            f"Visita técnica confirmada! 🎉\n\n"
            f"📅 *{full_date}*\n"
            f"⏰ *{chosen_slot['label']}*\n\n"
            f"Nossa equipe estará no local nesse horário. "
            f"Se precisar alterar, é só avisar 😊"
        ),
        next_step="global_done", context=ctx)


def _confirm_generic_appointment(conversation, db, *, company, client, ctx: dict, chosen_slot: dict) -> dict[str, Any]:
    from datetime import datetime as _dt, date as _d
    from app.repositories.appointments import AppointmentsRepository

    start_at = _dt.fromisoformat(chosen_slot["start_dt"])
    end_at = _dt.fromisoformat(chosen_slot["end_dt"])
    repo = AppointmentsRepository(db)
    repo.create_appointment(
        company_id=company.id,
        client_id=client.id,
        quote_id=ctx.get("global_found_quote_id"),
        address_raw=ctx.get("address") or "",
        start_at=start_at,
        end_at=end_at,
        service_type="service",
        event_title=f"Serviço – {client.name or 'Cliente'}",
        valor=None,
        notes="Agendado pelo chatbot via opção 'Tenho orçamento'.",
    )
    db.flush()
    try:
        full_date = _full_weekday_date_pt(_d.fromisoformat(chosen_slot["start_dt"][:10]))
    except Exception:
        full_date = ctx.get("global_schedule_day_label") or chosen_slot["start_dt"][:10]
    return reply_text(conversation, db,
        text=(
            f"Agendamento confirmado! 🎉\n\n"
            f"📅 *{full_date}*\n"
            f"⏰ *{chosen_slot['label']}*\n\n"
            f"Nossa equipe estará no local nesse horário. Se precisar de mais alguma coisa, é só avisar 😊"
        ),
        next_step="global_done", context=ctx)


def _confirm_reschedule(conversation, db, *, company, client, ctx: dict, chosen_slot: dict) -> dict[str, Any]:
    from datetime import datetime as _dt, date as _d
    from app.db.models import Appointment, AppointmentStatus
    from app.repositories.appointments import AppointmentsRepository
    from sqlalchemy import select as _sel

    repo = AppointmentsRepository(db)
    old_id = ctx.get("global_reschedule_appointment_id")
    if old_id:
        old_appt = db.scalar(
            _sel(Appointment).where(
                Appointment.id == old_id,
                Appointment.company_id == company.id,
            )
        )
        if old_appt:
            repo.update_appointment(old_appt,
                status=AppointmentStatus.CANCELLED,
                reschedule_reason="Reagendado pelo cliente via chatbot")

    start_at = _dt.fromisoformat(chosen_slot["start_dt"])
    end_at = _dt.fromisoformat(chosen_slot["end_dt"])
    repo.create_appointment(
        company_id=company.id,
        client_id=client.id,
        quote_id=None,
        address_raw=ctx.get("address") or "",
        start_at=start_at,
        end_at=end_at,
        service_type="service",
        event_title=f"Serviço (reagendado) – {client.name or 'Cliente'}",
        valor=None,
        notes="Reagendado pelo cliente via chatbot WhatsApp.",
    )
    db.flush()
    try:
        full_date = _full_weekday_date_pt(_d.fromisoformat(chosen_slot["start_dt"][:10]))
    except Exception:
        full_date = ctx.get("global_schedule_day_label") or chosen_slot["start_dt"][:10]
    old_label = ctx.get("global_reschedule_old_label", "data anterior")
    return reply_text(conversation, db,
        text=(
            f"Reagendamento confirmado! 🎉\n\n"
            f"📅 *{full_date}*\n"
            f"⏰ *{chosen_slot['label']}*\n\n"
            f"Seu agendamento anterior (*{old_label}*) foi cancelado. "
            f"Se precisar de mais alguma coisa, é só avisar 😊"
        ),
        next_step="global_done", context=ctx)


def _cancel_latest_appointment(db, *, company, client) -> None:
    from sqlalchemy import select
    from app.db.models import Appointment, AppointmentStatus
    from app.repositories.appointments import AppointmentsRepository
    from datetime import datetime as _dt, timezone as _tz
    try:
        now = _dt.now(_tz.utc)
        appt = db.scalar(
            select(Appointment)
            .where(
                Appointment.company_id == company.id,
                Appointment.client_id == client.id,
                Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]),
                Appointment.start_at > now,
            )
            .order_by(Appointment.start_at.asc())
        )
        if appt:
            repo = AppointmentsRepository(db)
            repo.update_appointment(appt,
                status=AppointmentStatus.CANCELLED,
                notes="Cancelado pelo cliente via chatbot")
    except Exception:
        pass
