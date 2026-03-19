
from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy.orm.attributes import flag_modified

from app.db.models import ConversationStatus
from app.domains.protection_network.address_catalog import (
    AddressCatalog,
    format_measure_choice_title,
    parse_manual_measurements_block,
)
from app.domains.protection_network.domain import domain
from app.domains.protection_network.job_rules import (
    resolve_address_rule,
    validate_color_for_rule,
    validate_mesh_for_rule,
)
from app.domains.protection_network.pricing import (
    build_quote_items_from_selection,
    calculate_quote_totals,
)

RESET_WORDS = {"reiniciar", "recomeçar", "menu", "reset", "inicio", "início"}
YES_WORDS = {"sim", "s", "yes", "y"}
NO_WORDS = {"nao", "não", "n", "no"}
ALTER_WORDS = {"alterar", "mudar", "editar"}
CONFIRM_WORDS = {"confirmar", "fechar", "seguir", "continuar"}

SCHEDULE_YES_WORDS = {"sim", "s", "yes", "y", "1", "schedule_yes", "agendar", "quero"}
SCHEDULE_LATER_WORDS = {"nao", "não", "n", "no", "2", "schedule_later", "depois", "prefiro", "agora não", "agora nao"}


def _domain_settings(company) -> dict[str, Any]:
    base = domain.get_default_settings()
    extra = {}
    if getattr(company, "settings", None) and getattr(company.settings, "extra_settings", None):
        extra = company.settings.extra_settings or {}

    merged = dict(base)
    for key, value in extra.items():
        if isinstance(merged.get(key), dict) and isinstance(value, dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    return merged


def _safe_text(inbound_message: dict[str, Any]) -> str:
    return (
        inbound_message.get("interactive_reply_id")
        or inbound_message.get("interactive_reply_title")
        or inbound_message.get("message_text")
        or ""
    ).strip()


def _current_context(conversation) -> dict[str, Any]:
    return dict(conversation.bot_context or {})


def _json_safe(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(i) for i in obj]
    return obj


def _save_state(conversation, db, *, next_step: str, context: dict[str, Any]) -> None:
    conversation.bot_step = next_step
    conversation.bot_context = _json_safe(context)
    flag_modified(conversation, "bot_context")
    db.flush()


def _reply_text(conversation, db, *, text: str, next_step: str, context: dict[str, Any], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    _save_state(conversation, db, next_step=next_step, context=context)
    payload = {
        "action": "reply_text",
        "text": text,
        "next_step": next_step,
        "context": context,
    }
    if extra:
        payload.update(extra)
    return payload


def _reply_buttons(conversation, db, *, text: str, next_step: str, context: dict[str, Any], buttons: list[dict[str, str]], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    _save_state(conversation, db, next_step=next_step, context=context)
    payload = {
        "action": "reply_buttons",
        "text": text,
        "buttons": buttons,
        "next_step": next_step,
        "context": context,
    }
    if extra:
        payload.update(extra)
    return payload


def _reply_list(conversation, db, *, header: str, body: str, button_text: str, sections: list[dict[str, Any]], next_step: str, context: dict[str, Any], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    _save_state(conversation, db, next_step=next_step, context=context)
    payload = {
        "action": "reply_list",
        "header": header,
        "text": body,
        "button_text": button_text,
        "sections": sections,
        "next_step": next_step,
        "context": context,
    }
    if extra:
        payload.update(extra)
    return payload


def _full_weekday_date_pt(d) -> str:
    """Retorna data no formato 'Quinta-feira, 20/03' (nome completo do dia)."""
    WEEKDAYS_FULL = [
        "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira",
        "Sexta-feira", "Sábado", "Domingo",
    ]
    return f"{WEEKDAYS_FULL[d.weekday()]}, {d.day:02d}/{d.month:02d}"


def _reply_assumed(conversation, db, *, text: str, context: dict[str, Any]) -> dict[str, Any]:
    """Encaminha a conversa para atendimento humano (status ASSUMED)."""
    conversation.status = ConversationStatus.ASSUMED
    conversation.bot_step = "awaiting_quote"
    conversation.bot_context = _json_safe(context)
    flag_modified(conversation, "bot_context")
    db.flush()
    return {"action": "assumed", "text": text, "context": context}


def _normalize_yes_no(text: str) -> str | None:
    value = (text or "").strip().lower()
    if value in YES_WORDS or value.startswith("add_more_yes"):
        return "yes"
    if value in NO_WORDS or value.startswith("add_more_no"):
        return "no"
    if value in {"1"}:
        return "yes"
    if value in {"2"}:
        return "no"
    return None


def _normalize_catalog_item(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        return item

    normalized: dict[str, Any] = {}
    if hasattr(item, 'to_quote_item_dict'):
        try:
            normalized.update(item.to_quote_item_dict())
        except Exception:
            pass

    if hasattr(item, 'selection_id'):
        try:
            sel = item.selection_id() if callable(item.selection_id) else item.selection_id
            normalized['selection_id'] = sel
        except Exception:
            pass

    field_map = {
        'legacy_id': ['legacy_id', 'id'],
        'tipo': ['tipo', 'type'],
        'descricao': ['descricao', 'description', 'label'],
        'width': ['width', 'width_m', 'lado_a_m'],
        'height': ['height', 'height_m', 'lado_b_m'],
        'lado_a_m': ['lado_a_m'],
        'lado_b_m': ['lado_b_m'],
        'observacao': ['observacao', 'notes'],
        'planta': ['planta', 'plant'],
        'source': ['source'],
    }
    for target, candidates in field_map.items():
        if target in normalized and normalized[target] is not None:
            continue
        for cand in candidates:
            if hasattr(item, cand):
                try:
                    value = getattr(item, cand)
                    normalized[target] = value() if callable(value) else value
                    break
                except Exception:
                    continue

    if 'selection_id' not in normalized:
        legacy_id = normalized.get('legacy_id')
        if legacy_id is not None:
            normalized['selection_id'] = f'medida_{legacy_id}'

    normalized.setdefault('source', 'address_catalog')
    return normalized


def _build_measure_rows(items: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows = []
    for idx, raw_item in enumerate(items[:10], start=1):
        item = _normalize_catalog_item(raw_item)
        rows.append(
            {
                "id": f"pick_{item['selection_id']}",
                "title": f"{idx}) {format_measure_choice_title(item)}"[:24],
                "description": "",
            }
        )
    return rows


def _items_from_catalog_lookup(lookup_result: dict[str, Any], chosen_plant: str | None = None) -> list[dict[str, Any]]:
    plants = lookup_result.get("plants") or {}
    raw_items = []
    if plants and chosen_plant:
        raw_items = plants.get(chosen_plant) or []
    else:
        raw_items = lookup_result.get("items") or []
    return [_normalize_catalog_item(item) for item in raw_items]


def _extract_selected_item_from_context(context: dict[str, Any], selection_id: str) -> dict[str, Any] | None:
    for raw_item in context.get("address_items_available", []) or []:
        item = _normalize_catalog_item(raw_item)
        if item.get("selection_id") == selection_id:
            return item
    return None


def _ensure_selected_items(context: dict[str, Any]) -> list[dict[str, Any]]:
    selected = context.get("selected_items")
    if not isinstance(selected, list):
        selected = []
    context["selected_items"] = selected

    ids = context.get("selected_item_ids")
    if not isinstance(ids, list):
        ids = []
    context["selected_item_ids"] = ids
    return selected


def _rebuild_selected_items(context: dict[str, Any]) -> None:
    selected_ids = context.get("selected_item_ids") or []
    available = context.get("address_items_available") or []
    if not selected_ids or not available:
        return

    rebuilt: list[dict[str, Any]] = []
    seen: set[str] = set()
    for selection_id in selected_ids:
        item = _extract_selected_item_from_context(context, selection_id)
        if item and selection_id not in seen:
            rebuilt.append(item)
            seen.add(selection_id)

    if rebuilt:
        context["selected_items"] = rebuilt


def _append_selected_item(context: dict[str, Any], item: dict[str, Any]) -> None:
    selected = _ensure_selected_items(context)
    already = {it.get("selection_id") for it in selected}
    selected_ids = context.setdefault("selected_item_ids", [])

    selection_id = item.get("selection_id")
    if selection_id and selection_id not in already:
        selected.append(item)
    if selection_id and selection_id not in selected_ids:
        selected_ids.append(selection_id)


def _build_colors(company) -> list[str]:
    settings = _domain_settings(company)
    # stored as "network_colors" in extra_settings / domain defaults
    colors = settings.get("network_colors") or settings.get("available_colors") or ["branca", "preta", "areia", "cinza"]
    return [str(c).strip().lower() for c in colors if str(c).strip()]


def _build_mesh_types(company) -> list[str]:
    settings = _domain_settings(company)
    # stored as "mesh_types" in extra_settings / domain defaults
    meshes = settings.get("mesh_types") or settings.get("available_mesh_types") or ["3x3", "5x5", "10x10"]
    return [str(m).strip().lower().replace("×", "x") for m in meshes if str(m).strip()]


def _resolve_plant_choice(text: str, plant_names: list[str]) -> str | None:
    if not plant_names:
        return None

    # pick_plant_N — interactive list reply ID
    if text.startswith("pick_plant_"):
        try:
            idx = int(text.replace("pick_plant_", "", 1)) - 1
            if 0 <= idx < len(plant_names):
                return plant_names[idx]
        except ValueError:
            pass

    # planta_{name} — legacy format
    if text.startswith("planta_"):
        candidate = text.replace("planta_", "", 1)
        for plant in plant_names:
            if plant == candidate:
                return plant

    if text.isdigit():
        idx = int(text) - 1
        if 0 <= idx < len(plant_names):
            return plant_names[idx]

    lowered = text.strip().lower()
    for plant in plant_names:
        if plant.lower() == lowered:
            return plant

    return None


def _resolve_measure_selection(text: str, items: list[dict[str, Any]]) -> dict[str, Any] | None:
    normalized = (text or "").strip()

    if normalized.startswith("pick_"):
        picked_id = normalized.replace("pick_", "", 1)
        for raw_item in items:
            item = _normalize_catalog_item(raw_item)
            if item.get("selection_id") == picked_id:
                return item

    if normalized.startswith("medida_"):
        for raw_item in items:
            item = _normalize_catalog_item(raw_item)
            if item.get("selection_id") == normalized:
                return item

    if normalized.isdigit():
        idx = int(normalized) - 1
        if 0 <= idx < len(items):
            return _normalize_catalog_item(items[idx])

    lowered = normalized.lower()
    for raw_item in items:
        item = _normalize_catalog_item(raw_item)
        descricao = str(item.get("descricao") or "").strip().lower()
        titulo = format_measure_choice_title(item).strip().lower()
        if lowered == descricao or lowered == titulo:
            return item

    return None


def _resolve_color_choice(text: str, colors: list[str]) -> str | None:
    normalized = text.strip().lower()
    if normalized.startswith("color_"):
        candidate = normalized[6:].replace("_", " ")
        for color in colors:
            if color.lower() == candidate or color.lower().replace(" ", "_") == normalized[6:]:
                return color
    if normalized.isdigit():
        idx = int(normalized) - 1
        if 0 <= idx < len(colors):
            return colors[idx]
    for color in colors:
        if color.lower() == normalized:
            return color
    return None


def _resolve_mesh_choice(text: str, meshes: list[str]) -> str | None:
    normalized = text.strip().lower().replace(" ", "").replace("×", "x")
    if normalized.startswith("mesh_"):
        candidate = normalized[5:]
        for mesh in meshes:
            if mesh.lower().replace(" ", "").replace("×", "x") == candidate:
                return mesh
    if normalized.isdigit():
        idx = int(normalized) - 1
        if 0 <= idx < len(meshes):
            return meshes[idx]
    for mesh in meshes:
        if mesh.lower().replace(" ", "").replace("×", "x") == normalized:
            return mesh
    return None


def _color_prompt(company) -> str:
    colors = _build_colors(company)
    numbered = "\n".join(f"{idx}) {color}" for idx, color in enumerate(colors, start=1))
    return f"Qual cor da rede você deseja?\n{numbered}"


def _mesh_prompt(company) -> str:
    meshes = _build_mesh_types(company)
    numbered = "\n".join(f"{idx}) {mesh}" for idx, mesh in enumerate(meshes, start=1))
    return f"Qual malha você deseja?\n{numbered}"


def _has_sacada_item(context: dict[str, Any]) -> bool:
    for item in context.get("selected_items") or []:
        desc = str(item.get("descricao") or item.get("tipo") or "").lower()
        if "sacada" in desc:
            return True
    return False


def _send_color_interactive(conversation, db, *, context: dict[str, Any], company) -> dict[str, Any]:
    colors = _build_colors(company)
    if len(colors) <= 3:
        buttons = [
            {"id": f"color_{c.replace(' ', '_')}", "title": c.capitalize()[:20]}
            for c in colors[:3]
        ]
        return _reply_buttons(
            conversation, db,
            text="Qual cor da rede você deseja?",
            next_step="network_color",
            context=context,
            buttons=buttons,
        )
    rows = [
        {"id": f"color_{c.replace(' ', '_')}", "title": c.capitalize()[:24], "description": ""}
        for c in colors[:10]
    ]
    return _reply_list(
        conversation, db,
        header="Cor da rede",
        body="Qual cor da rede você deseja?",
        button_text="Escolher",
        sections=[{"title": "Cores disponíveis", "rows": rows}],
        next_step="network_color",
        context=context,
    )


def _send_mesh_interactive(conversation, db, *, context: dict[str, Any], company) -> dict[str, Any]:
    meshes = _build_mesh_types(company)
    if len(meshes) <= 3:
        buttons = [
            {"id": f"mesh_{m.replace(' ', '_').replace('×', 'x')}", "title": f"Malha {m}"[:20]}
            for m in meshes[:3]
        ]
        return _reply_buttons(
            conversation, db,
            text="Qual malha da rede você deseja?",
            next_step="mesh_type",
            context=context,
            buttons=buttons,
        )
    rows = [
        {"id": f"mesh_{m.replace(' ', '_').replace('×', 'x')}", "title": f"Malha {m}"[:24], "description": ""}
        for m in meshes[:10]
    ]
    return _reply_list(
        conversation, db,
        header="Malha da rede",
        body="Qual malha da rede você deseja?",
        button_text="Escolher",
        sections=[{"title": "Malhas disponíveis", "rows": rows}],
        next_step="mesh_type",
        context=context,
    )


def _format_money_br(value: Any) -> str:
    if value is None:
        return "0,00"
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    quantized = value.quantize(Decimal("0.01"))
    s = f"{quantized:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _build_selected_items_summary(selected_items: list[dict[str, Any]]) -> str:
    lines = []
    for idx, item in enumerate(selected_items, start=1):
        desc = (item.get("descricao") or item.get("tipo") or f"item {idx}").strip()
        width = item.get("width")
        height = item.get("height")
        lines.append(f"{idx}. {desc} — {width} x {height} m")
    return "\n".join(lines)


def _build_quote_confirmation_text(*, client_name: str | None, address: str, selected_items: list[dict[str, Any]], color: str | None, mesh_type: str | None, totals: dict[str, Any], show_measures: bool = True) -> str:
    customer = client_name or "cliente"
    subtotal = _format_money_br(totals.get("subtotal"))
    visit_fee = _format_money_br(totals.get("visit_fee"))
    total = _format_money_br(totals.get("total_value"))

    base = (
        f"Perfeito, {customer}.\n\n"
        f"Confira seu orçamento:\n\n"
        f"Nome: {customer}\n"
        f"Endereço: {address}\n"
        f"Cor: {color or 'não informada'}\n"
        f"Malha: {mesh_type or 'não informada'}\n\n"
    )

    if show_measures and selected_items:
        parts = _build_selected_items_summary(selected_items)
        base += f"Áreas selecionadas:\n{parts}\n\n"

    base += (
        f"Subtotal: R$ {subtotal}\n"
        f"Taxa/visita: R$ {visit_fee}\n"
        f"Total estimado: R$ {total}\n\n"
        f"1) Confirmar orçamento\n"
        f"2) Alterar dados"
    )
    return base


def _get_schedule_cfg(company, db) -> dict[str, Any]:
    from sqlalchemy import select as _select
    from app.db.models import CompanySettings as _CS
    cs = db.scalar(_select(_CS).where(_CS.company_id == company.id))
    extra = (cs.extra_settings or {}) if cs else {}
    cfg = extra.get("schedule") or {}
    return {
        "slot_minutes": int(cfg.get("slot_minutes", 120)),
        "workday_start": cfg.get("workday_start", "08:00"),
        "workday_end": cfg.get("workday_end", "18:00"),
        "allowed_weekdays": list(cfg.get("allowed_weekdays", [0, 1, 2, 3, 4])),
    }


def _parse_date_br(text: str):
    from datetime import date as _date, datetime as _dt
    text = text.strip()
    for sep in ["/", "-", "."]:
        text = text.replace(sep, "/")
    parts = text.split("/")
    try:
        if len(parts) == 3:
            day, month = int(parts[0]), int(parts[1])
            year = int(parts[2]) if len(parts[2]) == 4 else 2000 + int(parts[2])
            return _date(year, month, day)
        if len(parts) == 2:
            day, month = int(parts[0]), int(parts[1])
            today = _dt.today().date()
            year = today.year
            try:
                d = _date(year, month, day)
                if d < today:
                    d = _date(year + 1, month, day)
                return d
            except ValueError:
                return None
    except (ValueError, IndexError):
        return None
    return None


def _compute_slots(target_date, cfg: dict[str, Any]) -> list[dict[str, Any]]:
    from datetime import datetime as _dt, timedelta as _td
    weekday = target_date.weekday()
    allowed = list(cfg.get("allowed_weekdays", [0, 1, 2, 3, 4]))
    if weekday not in allowed:
        return []
    start_h, start_m = map(int, cfg.get("workday_start", "08:00").split(":"))
    end_h, end_m = map(int, cfg.get("workday_end", "18:00").split(":"))
    slot_minutes = int(cfg.get("slot_minutes", 120))
    day_start = _dt(target_date.year, target_date.month, target_date.day, start_h, start_m)
    day_end = _dt(target_date.year, target_date.month, target_date.day, end_h, end_m)
    slots = []
    current = day_start
    while current + _td(minutes=slot_minutes) <= day_end:
        slot_end = current + _td(minutes=slot_minutes)
        slots.append({
            "id": f"slot_{current.strftime('%H%M')}",
            "label": f"{current.strftime('%H:%M')} às {slot_end.strftime('%H:%M')}",
            "start_dt": current.isoformat(),
            "end_dt": slot_end.isoformat(),
        })
        current = slot_end
    return slots


def _compute_available_days(cfg: dict[str, Any], days_ahead: int = 21) -> list[dict[str, Any]]:
    from datetime import date as _date, datetime as _dt, timedelta as _td
    WEEKDAYS_SHORT = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    today = _dt.today().date()
    days: list[dict[str, Any]] = []
    for i in range(1, days_ahead + 1):
        candidate = today + _td(days=i)
        if _compute_slots(candidate, cfg):
            label = f"{WEEKDAYS_SHORT[candidate.weekday()]} {candidate.day:02d}/{candidate.month:02d}"
            days.append({
                "id": f"day_{candidate.strftime('%Y%m%d')}",
                "date": candidate.isoformat(),
                "label": label,
            })
        if len(days) >= 10:
            break
    return days


def _format_date_pt(d) -> str:
    WEEKDAYS_PT = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
                   "sexta-feira", "sábado", "domingo"]
    day_name = WEEKDAYS_PT[d.weekday()]
    return f"{d.day:02d}/{d.month:02d}/{d.year} ({day_name})"


def handle_inbound_message(*, company, conversation, client, inbound_message, db):
    text = _safe_text(inbound_message)
    context = _current_context(conversation)
    current_step = (conversation.bot_step or "start").strip().lower()

    if text.lower() in RESET_WORDS:
        context = {}
        return _reply_text(
            conversation,
            db,
            text="Vamos recomeçar. Qual é o seu nome completo?",
            next_step="customer_name",
            context=context,
        )

    if current_step in {"", "start"}:
        context = {}
        return _reply_text(
            conversation,
            db,
            text="Olá! Vou te ajudar com seu orçamento de rede de proteção. Primeiro, qual é o seu nome completo?",
            next_step="customer_name",
            context=context,
        )

    if current_step == "customer_name":
        if len(text.strip()) < 3:
            return _reply_text(
                conversation,
                db,
                text="Me informe seu nome completo, por favor.",
                next_step="customer_name",
                context=context,
            )

        context["customer_name"] = text.strip()
        try:
            client.name = text.strip()
            db.flush()
        except Exception:
            pass

        return _reply_text(
            conversation,
            db,
            text="Perfeito. Agora me envie o endereço completo do local da instalação.",
            next_step="address_lookup",
            context=context,
        )

    if current_step == "address_lookup":
        context["address"] = text
        catalog = AddressCatalog(db=db, company_id=company.id)
        lookup_result = catalog.lookup_address(text)
        context["address_lookup_found"] = lookup_result["found"]
        context["address_lookup_endereco_id"] = lookup_result["endereco_id"]

        if lookup_result["found"] and ((lookup_result.get("items") or []) or (lookup_result.get("plants") or {})):
            settings_data = _domain_settings(company)
            show_measures = settings_data.get("show_measures_to_customer", True)
            context["show_measures_to_customer"] = show_measures

            plants = lookup_result.get("plants", {}) or {}
            plant_names = list(plants.keys())

            # Multiple plants → ALWAYS ask the client (plant names are always visible,
            # regardless of show_measures_to_customer toggle)
            if len(plant_names) > 1:
                context["address_plants"] = plant_names
                context["selected_items"] = []
                context["selected_item_ids"] = []

                rows = []
                for idx, plant in enumerate(plant_names[:10], start=1):
                    rows.append(
                        {
                            "id": f"pick_plant_{idx}",
                            "title": plant[:24],
                            "description": "",
                        }
                    )

                return _reply_list(
                    conversation,
                    db,
                    header="Escolha a planta",
                    body="Encontrei mais de uma planta para esse endereço.\nQual é a sua planta?",
                    button_text="Ver plantas",
                    sections=[{"title": "Plantas disponíveis", "rows": rows}],
                    next_step="plant_choice",
                    context=context,
                )

            # Single plant (or no plant grouping)
            chosen_plant = plant_names[0] if plant_names else None
            items = _items_from_catalog_lookup(lookup_result, chosen_plant)
            if not items:
                context["selected_items"] = []
                context["selected_item_ids"] = []
                return _reply_text(
                    conversation,
                    db,
                    text=(
                        "Encontrei o endereço, mas ainda não há medidas cadastradas.\n\n"
                        "Me envie as medidas.\n"
                        "Você pode mandar uma por vez:\n"
                        "1 sacada 1,20 x 1,40\n\n"
                        "Ou várias linhas de uma vez:\n"
                        "1 janela sala 1,29 x 1,19\n"
                        "1 sacada 2,00 x 1,30"
                    ),
                    next_step="manual_measurements",
                    context=context,
                )

            all_items = [_normalize_catalog_item(i) for i in items]
            context["address_items_available"] = all_items

            if not show_measures:
                # Auto-select all, skip measure list, go straight to color.
                # Plant name is always shown to the client (rule: plant name always visible).
                context["selected_items"] = all_items
                context["selected_item_ids"] = [i.get("selection_id") for i in all_items]
                plant_prefix = f"Planta: *{chosen_plant}*\n\n" if chosen_plant else ""
                return _reply_text(
                    conversation,
                    db,
                    text=plant_prefix + _color_prompt(company),
                    next_step="network_color",
                    context=context,
                )

            context["selected_items"] = []
            context["selected_item_ids"] = []

            rows = _build_measure_rows(all_items)
            rows.append({"id": "pick_manual", "title": "Informar manualmente", "description": ""})
            rows.append({"id": "pick_by_numbers", "title": "Escolher por números", "description": ""})

            return _reply_list(
                conversation,
                db,
                header="Itens encontrados",
                body="Encontrei medidas salvas para esse endereço. Qual área você quer orçar?",
                button_text="Escolher",
                sections=[{"title": "Medidas", "rows": rows[:10]}],
                next_step="measure_selection",
                context=context,
            )

        context["selected_items"] = []
        context["selected_item_ids"] = []
        return _reply_buttons(
            conversation,
            db,
            text=(
                "Não encontrei esse endereço no nosso cadastro. "
                "Você já tem as medidas dos ambientes que quer orçar?"
            ),
            buttons=[
                {"id": "has_measures_yes", "title": "Sim, tenho as medidas"},
                {"id": "has_measures_no",  "title": "Não tenho"},
            ],
            next_step="ask_has_measures",
            context=context,
        )

    if current_step == "ask_has_measures":
        normalized = text.strip().lower()
        if normalized in {"has_measures_yes", "sim", "s", "yes", "y", "1", "sim, tenho as medidas"}:
            return _reply_text(
                conversation,
                db,
                text=(
                    "Perfeito! Me envie as medidas dos ambientes.\n"
                    "Você pode mandar uma por vez:\n"
                    "1 sacada 1,20 x 1,40\n\n"
                    "Ou várias de uma vez:\n"
                    "1 janela sala 1,29 x 1,19\n"
                    "1 sacada 2,00 x 1,30\n\n"
                    "⚠️ *Importante:* Quando o instalador chegar ao local, ele irá tirar as medidas "
                    "oficiais e pode haver alteração no orçamento."
                ),
                next_step="manual_measurements",
                context=context,
            )
        return _reply_assumed(
            conversation,
            db,
            text=(
                "Tudo bem! Vou encaminhar seu atendimento para um de nossos especialistas "
                "montar o orçamento para você 😊\n\n"
                "Em breve entraremos em contato!"
            ),
            context=context,
        )

    if current_step == "plant_choice":
        plant_names = context.get("address_plants") or []
        show_measures = context.get("show_measures_to_customer", True)
        chosen_plant = _resolve_plant_choice(text, plant_names)
        if not chosen_plant:
            # Re-show the plant list so the client can pick again
            rows = []
            for idx, plant in enumerate(plant_names[:10], start=1):
                rows.append({"id": f"pick_plant_{idx}", "title": plant[:24], "description": ""})
            return _reply_list(
                conversation,
                db,
                header="Escolha a planta",
                body="Não entendi. Escolha uma planta da lista ou digite o número correspondente.",
                button_text="Ver plantas",
                sections=[{"title": "Plantas disponíveis", "rows": rows}],
                next_step="plant_choice",
                context=context,
            )

        catalog = AddressCatalog(db=db, company_id=company.id)
        lookup_result = catalog.lookup_address(context.get("address") or "")
        items = _items_from_catalog_lookup(lookup_result, chosen_plant)
        if not items:
            context["selected_items"] = []
            context["selected_item_ids"] = []
            return _reply_text(
                conversation,
                db,
                text=(
                    "Essa planta não possui medidas cadastradas. Me envie as medidas manualmente.\n\n"
                    "Exemplo:\n1 sacada 1,20 x 1,40"
                ),
                next_step="manual_measurements",
                context=context,
            )

        context["selected_plant"] = chosen_plant
        all_items = [_normalize_catalog_item(i) for i in items]
        context["address_items_available"] = all_items

        if not show_measures:
            # Plant chosen — auto-select all measures of this plant, jump to color.
            # Plant name is always shown to the client (rule: plant name always visible).
            context["selected_items"] = all_items
            context["selected_item_ids"] = [i.get("selection_id") for i in all_items]
            return _reply_text(
                conversation,
                db,
                text=f"Planta: *{chosen_plant}*\n\n" + _color_prompt(company),
                next_step="network_color",
                context=context,
            )

        context["selected_items"] = []
        context["selected_item_ids"] = []

        rows = _build_measure_rows(all_items)
        rows.append({"id": "pick_manual", "title": "Informar manualmente", "description": ""})
        rows.append({"id": "pick_by_numbers", "title": "Escolher por números", "description": ""})

        return _reply_list(
            conversation,
            db,
            header="Itens encontrados",
            body=f"Planta: {chosen_plant}\nQual área você quer orçar?",
            button_text="Escolher",
            sections=[{"title": "Medidas", "rows": rows[:10]}],
            next_step="measure_selection",
            context=context,
        )

    if current_step == "measure_selection":
        items = context.get("address_items_available") or []

        if text == "pick_manual":
            return _reply_text(
                conversation,
                db,
                text=(
                    "Sem problemas. Me envie as medidas manualmente.\n\n"
                    "Você pode mandar uma por vez:\n"
                    "1 sacada 1,20 x 1,40\n\n"
                    "Ou várias linhas de uma vez:\n"
                    "1 janela sala 1,29 x 1,19\n"
                    "1 sacada 2,00 x 1,30"
                ),
                next_step="manual_measurements",
                context=context,
            )

        if text == "pick_by_numbers":
            lines = []
            for idx, item in enumerate(items, start=1):
                lines.append(f"{idx}) {format_measure_choice_title(item)}")

            return _reply_text(
                conversation,
                db,
                text="Digite os números das áreas que deseja selecionar.\nExemplo: 1, 3\n\n" + "\n".join(lines[:20]),
                next_step="measure_selection_numbers",
                context=context,
            )

        item = _resolve_measure_selection(text, items)
        if item:
            _append_selected_item(context, item)
            _rebuild_selected_items(context)
            return _reply_buttons(
                conversation,
                db,
                text="Tem mais alguma área desse endereço que você quer incluir?",
                next_step="measure_selection_add_more",
                context=context,
                buttons=[
                    {"id": "add_more_yes", "title": "Sim"},
                    {"id": "add_more_no", "title": "Não"},
                ],
            )

        return _reply_text(
            conversation,
            db,
            text="Escolha uma área pelas opções enviadas ou digite o número correspondente.",
            next_step="measure_selection",
            context=context,
        )

    if current_step == "measure_selection_numbers":
        raw = text.replace(";", ",")
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        items = context.get("address_items_available") or []

        selected_any = False
        for part in parts:
            item = _resolve_measure_selection(part, items)
            if item:
                _append_selected_item(context, item)
                selected_any = True

        _rebuild_selected_items(context)

        if not selected_any:
            return _reply_text(
                conversation,
                db,
                text="Não consegui aplicar esses números. Tente novamente. Ex: 1, 3",
                next_step="measure_selection_numbers",
                context=context,
            )

        return _reply_buttons(
            conversation,
            db,
            text="Tem mais alguma área desse endereço que você quer incluir?",
            next_step="measure_selection_add_more",
            context=context,
            buttons=[
                {"id": "add_more_yes", "title": "Sim"},
                {"id": "add_more_no", "title": "Não"},
            ],
        )

    if current_step == "measure_selection_add_more":
        _rebuild_selected_items(context)
        yn = _normalize_yes_no(text)
        if yn == "yes":
            rows = _build_measure_rows(context.get("address_items_available") or [])
            rows.append({"id": "pick_manual", "title": "Informar manualmente", "description": ""})
            rows.append({"id": "pick_by_numbers", "title": "Escolher por números", "description": ""})

            return _reply_list(
                conversation,
                db,
                header="Mais áreas",
                body="Escolha mais uma área que deseja incluir.",
                button_text="Escolher",
                sections=[{"title": "Medidas", "rows": rows[:10]}],
                next_step="measure_selection",
                context=context,
            )

        if yn == "no":
            if not (context.get("selected_items") or context.get("selected_item_ids")):
                return _reply_text(
                    conversation,
                    db,
                    text="Não encontrei nenhuma área selecionada. Escolha uma área primeiro.",
                    next_step="measure_selection",
                    context=context,
                )
            _rebuild_selected_items(context)
            if _has_sacada_item(context) and not context.get("blindex_asked"):
                return _reply_buttons(
                    conversation,
                    db,
                    text="Sua sacada possui fechamento em vidro (Blindex)?",
                    next_step="blindex_check",
                    context=context,
                    buttons=[
                        {"id": "blindex_yes", "title": "Sim, tem Blindex"},
                        {"id": "blindex_no", "title": "Não tem"},
                    ],
                )
            return _send_color_interactive(conversation, db, context=context, company=company)

        return _reply_buttons(
            conversation,
            db,
            text="Tem mais alguma área desse endereço que você quer incluir?",
            next_step="measure_selection_add_more",
            context=context,
            buttons=[
                {"id": "add_more_yes", "title": "Sim"},
                {"id": "add_more_no", "title": "Não"},
            ],
        )

    if current_step == "manual_measurements":
        parsed_items = parse_manual_measurements_block(text)
        if not parsed_items:
            return _reply_text(
                conversation,
                db,
                text=(
                    "Não consegui entender as medidas.\n"
                    "Envie no formato:\n"
                    "1 sacada 1,20 x 1,40\n"
                    "ou várias linhas de uma vez."
                ),
                next_step="manual_measurements",
                context=context,
            )

        base_len = len(context.get("selected_item_ids") or [])
        for idx, item in enumerate(parsed_items, start=1):
            item["selection_id"] = f"manual_{base_len + idx}"
            _append_selected_item(context, item)

        _rebuild_selected_items(context)

        if len(parsed_items) == 1 and len((text or "").splitlines()) == 1:
            return _reply_buttons(
                conversation,
                db,
                text="Tem mais alguma medida para incluir?",
                next_step="manual_measurements_add_more",
                context=context,
                buttons=[
                    {"id": "add_more_yes", "title": "Sim"},
                    {"id": "add_more_no", "title": "Não"},
                ],
            )

        _rebuild_selected_items(context)
        if _has_sacada_item(context) and not context.get("blindex_asked"):
            return _reply_buttons(
                conversation,
                db,
                text="Sua sacada possui fechamento em vidro (Blindex)?",
                next_step="blindex_check",
                context=context,
                buttons=[
                    {"id": "blindex_yes", "title": "Sim, tem Blindex"},
                    {"id": "blindex_no", "title": "Não tem"},
                ],
            )
        return _send_color_interactive(conversation, db, context=context, company=company)

    if current_step == "manual_measurements_add_more":
        yn = _normalize_yes_no(text)
        if yn == "yes":
            return _reply_text(
                conversation,
                db,
                text="Pode enviar a próxima medida.",
                next_step="manual_measurements",
                context=context,
            )

        if yn == "no":
            _rebuild_selected_items(context)
            if _has_sacada_item(context) and not context.get("blindex_asked"):
                return _reply_buttons(
                    conversation,
                    db,
                    text="Sua sacada possui fechamento em vidro (Blindex)?",
                    next_step="blindex_check",
                    context=context,
                    buttons=[
                        {"id": "blindex_yes", "title": "Sim, tem Blindex"},
                        {"id": "blindex_no", "title": "Não tem"},
                    ],
                )
            return _send_color_interactive(conversation, db, context=context, company=company)

        return _reply_buttons(
            conversation,
            db,
            text="Tem mais alguma medida para incluir?",
            next_step="manual_measurements_add_more",
            context=context,
            buttons=[
                {"id": "add_more_yes", "title": "Sim"},
                {"id": "add_more_no", "title": "Não"},
            ],
        )

    if current_step == "blindex_check":
        normalized_bl = (text or "").strip().lower()
        yn = _normalize_yes_no(normalized_bl)
        if yn is None:
            if normalized_bl in {"blindex_yes", "blindex"}:
                yn = "yes"
            elif normalized_bl == "blindex_no":
                yn = "no"
        if yn is None:
            return _reply_buttons(
                conversation,
                db,
                text="Sua sacada possui fechamento em vidro (Blindex)?",
                next_step="blindex_check",
                context=context,
                buttons=[
                    {"id": "blindex_yes", "title": "Sim, tem Blindex"},
                    {"id": "blindex_no", "title": "Não tem"},
                ],
            )
        context["blindex"] = (yn == "yes")
        context["blindex_asked"] = True
        return _send_color_interactive(conversation, db, context=context, company=company)

    if current_step == "network_color":
        colors = _build_colors(company)
        chosen_color = _resolve_color_choice(text, colors)
        if not chosen_color:
            return _send_color_interactive(conversation, db, context=context, company=company)

        context["network_color"] = chosen_color.lower().strip()
        return _send_mesh_interactive(conversation, db, context=context, company=company)

    if current_step == "mesh_type":
        meshes = _build_mesh_types(company)
        chosen_mesh = _resolve_mesh_choice(text, meshes)
        if not chosen_mesh:
            return _send_mesh_interactive(conversation, db, context=context, company=company)

        context["mesh_type"] = chosen_mesh.lower().strip().replace(" ", "").replace("×", "x")

        _rebuild_selected_items(context)
        selected_items = context.get("selected_items") or []
        show_measures = context.get("show_measures_to_customer", True)

        if not selected_items:
            if show_measures:
                return _reply_text(
                    conversation,
                    db,
                    text="Não encontrei nenhuma área selecionada. Escolha uma área primeiro.",
                    next_step="measure_selection",
                    context=context,
                )
            return _reply_text(
                conversation,
                db,
                text="Não encontrei medidas para calcular o orçamento. Por favor, informe o endereço novamente.",
                next_step="address_lookup",
                context={},
            )

        rule_result = resolve_address_rule(company, context.get("address") or "")
        color = context.get("network_color")
        mesh_type = context.get("mesh_type")

        quote_items = build_quote_items_from_selection(
            selected_items=selected_items,
            company=company,
            mesh_type=mesh_type or "3x3",
            color=color,
            rule_result=rule_result,
        )
        totals = calculate_quote_totals(
            company=company,
            items=quote_items,
            rule_result=rule_result,
        )
        context["quote_preview"] = {
            "items": quote_items,
            "totals": totals,
        }

        summary = _build_quote_confirmation_text(
            client_name=context.get("customer_name") or getattr(client, "name", None),
            address=context.get("address") or "",
            selected_items=selected_items,
            color=color,
            mesh_type=mesh_type,
            totals=totals,
            show_measures=show_measures,
        )

        return _reply_buttons(
            conversation,
            db,
            text=summary,
            next_step="quote_confirm",
            context=context,
            buttons=[
                {"id": "quote_confirm_yes", "title": "Confirmar"},
                {"id": "quote_confirm_edit", "title": "Alterar"},
            ],
        )

    if current_step == "quote_confirm":
        normalized = (text or "").strip().lower()
        if normalized in {"quote_confirm_yes", "confirmar", "1", "sim"}:
            selected_items = context.get("selected_items") or []
            if not selected_items:
                _rebuild_selected_items(context)
                selected_items = context.get("selected_items") or []

            if not selected_items:
                return _reply_text(
                    conversation,
                    db,
                    text="Perdi as medidas selecionadas. Vamos recomeçar pelo endereço.",
                    next_step="address_lookup",
                    context={},
                )

            address = context.get("address") or ""
            rule_result = resolve_address_rule(company, address)
            if rule_result.blocked:
                return _reply_text(
                    conversation,
                    db,
                    text=rule_result.message or "No momento não atendemos esse endereço.",
                    next_step="blocked",
                    context=context,
                    extra={"rule_result": rule_result.to_dict()},
                )

            color = context.get("network_color")
            mesh_type = context.get("mesh_type")

            if color:
                ok, error = validate_color_for_rule(selected_color=color, rule_result=rule_result)
                if not ok:
                    return _reply_text(
                        conversation,
                        db,
                        text=error or "Cor não permitida para esse endereço.",
                        next_step="network_color",
                        context=context,
                        extra={"rule_result": rule_result.to_dict()},
                    )

            if mesh_type:
                ok, error = validate_mesh_for_rule(selected_mesh=mesh_type, rule_result=rule_result)
                if not ok:
                    return _reply_text(
                        conversation,
                        db,
                        text=error or "Malha não permitida para esse endereço.",
                        next_step="mesh_type",
                        context=context,
                        extra={"rule_result": rule_result.to_dict()},
                    )

            preview = context.get("quote_preview") or {}
            if not preview:
                quote_items = build_quote_items_from_selection(
                    selected_items=selected_items,
                    company=company,
                    mesh_type=mesh_type or "3x3",
                    color=color,
                    rule_result=rule_result,
                )
                totals = calculate_quote_totals(company=company, items=quote_items, rule_result=rule_result)
                preview = {"items": quote_items, "totals": totals}
                context["quote_preview"] = preview

            return _reply_buttons(
                conversation,
                db,
                text="Ótimo! Seu orçamento está confirmado.\n\nDeseja agendar a instalação agora?",
                next_step="schedule_ask",
                context=context,
                buttons=[
                    {"id": "schedule_yes", "title": "Sim, agendar agora"},
                    {"id": "schedule_later", "title": "Prefiro depois"},
                ],
                extra={
                    "rule_result": rule_result.to_dict(),
                    "quote_preview": preview,
                },
            )

        if normalized in {"quote_confirm_edit", "alterar", "2"}:
            show_measures = context.get("show_measures_to_customer", True)
            edit_buttons = [{"id": "edit_address", "title": "Endereço"}]
            if show_measures:
                edit_buttons.append({"id": "edit_items", "title": "Áreas"})
            edit_buttons.append({"id": "edit_color", "title": "Cor"})
            edit_buttons.append({"id": "edit_mesh", "title": "Malha"})
            return _reply_buttons(
                conversation,
                db,
                text="O que você deseja alterar?",
                next_step="quote_edit_choice",
                context=context,
                buttons=edit_buttons,
            )

        return _reply_buttons(
            conversation,
            db,
            text="Confirma o orçamento ou deseja alterar os dados?",
            next_step="quote_confirm",
            context=context,
            buttons=[
                {"id": "quote_confirm_yes", "title": "Confirmar"},
                {"id": "quote_confirm_edit", "title": "Alterar"},
            ],
        )

    if current_step == "quote_edit_choice":
        normalized = (text or "").strip().lower()
        show_measures = context.get("show_measures_to_customer", True)

        if normalized in {"edit_address", "endereço", "endereco", "1"}:
            return _reply_text(
                conversation,
                db,
                text="Tudo bem. Me envie novamente o endereço completo.",
                next_step="address_lookup",
                context={},
            )
        if normalized in {"edit_items", "áreas", "areas", "2"}:
            if not show_measures:
                return _reply_text(
                    conversation,
                    db,
                    text="Não é possível alterar as áreas. Escolha entre alterar o endereço, a cor ou a malha.",
                    next_step="quote_edit_choice",
                    context=context,
                )
            context["selected_items"] = []
            context["selected_item_ids"] = []
            rows = _build_measure_rows(context.get("address_items_available") or [])
            if rows:
                rows.append({"id": "pick_manual", "title": "Informar manualmente", "description": ""})
                rows.append({"id": "pick_by_numbers", "title": "Escolher por números", "description": ""})
                return _reply_list(
                    conversation,
                    db,
                    header="Escolher áreas",
                    body="Selecione novamente as áreas desejadas.",
                    button_text="Escolher",
                    sections=[{"title": "Medidas", "rows": rows[:10]}],
                    next_step="measure_selection",
                    context=context,
                )
            return _reply_text(
                conversation,
                db,
                text="Não encontrei medidas disponíveis. Me envie o endereço novamente.",
                next_step="address_lookup",
                context={},
            )
        if normalized in {"edit_color", "cor", "3"}:
            return _send_color_interactive(conversation, db, context=context, company=company)
        if normalized in {"edit_mesh", "malha", "4"}:
            return _send_mesh_interactive(conversation, db, context=context, company=company)

        edit_buttons = [{"id": "edit_address", "title": "Endereço"}]
        if show_measures:
            edit_buttons.append({"id": "edit_items", "title": "Áreas"})
        edit_buttons.append({"id": "edit_color", "title": "Cor"})
        edit_buttons.append({"id": "edit_mesh", "title": "Malha"})
        return _reply_buttons(
            conversation,
            db,
            text="Escolha o que deseja alterar.",
            next_step="quote_edit_choice",
            context=context,
            buttons=edit_buttons,
        )

    if current_step == "quote_ready":
        return _reply_buttons(
            conversation,
            db,
            text="Seu orçamento foi confirmado! Deseja agendar a instalação?",
            next_step="schedule_ask",
            context=context,
            buttons=[
                {"id": "schedule_yes", "title": "Sim, agendar agora"},
                {"id": "schedule_later", "title": "Prefiro depois"},
            ],
        )

    # ── helper: send the day-choice list ────────────────────────────────────
    def _send_day_list(body_text: str, cfg: dict[str, Any]):
        available_days = _compute_available_days(cfg)
        if not available_days:
            return _reply_text(
                conversation,
                db,
                text=(
                    "No momento não encontramos dias disponíveis para agendamento "
                    "nos próximos dias. Por favor, entre em contato diretamente com nossa equipe."
                ),
                next_step="done",
                context=context,
            )
        context["schedule_available_days"] = available_days
        rows = [{"id": d["id"], "title": d["label"], "description": ""} for d in available_days]
        return _reply_list(
            conversation,
            db,
            header="Dias disponíveis",
            body=body_text,
            button_text="Ver dias",
            sections=[{"title": "Próximos dias disponíveis", "rows": rows}],
            next_step="schedule_day_choice",
            context=context,
        )

    # ── helper: send the slot-choice list ───────────────────────────────────
    def _send_slot_list(chosen_day: dict[str, Any], cfg: dict[str, Any]):
        from datetime import date as _date_cls
        chosen_date = _date_cls.fromisoformat(chosen_day["date"])
        slots = _compute_slots(chosen_date, cfg)
        if not slots:
            return _send_day_list(
                f"Não há horários disponíveis para *{chosen_day['label']}*. Escolha outro dia:",
                cfg,
            )
        context["schedule_date"] = chosen_day["date"]
        context["schedule_day_label"] = chosen_day["label"]
        context["schedule_slots"] = slots
        rows = [{"id": s["id"], "title": s["label"], "description": ""} for s in slots[:10]]
        return _reply_list(
            conversation,
            db,
            header="Horários disponíveis",
            body=f"Ótimo! Agora escolha o horário para *{chosen_day['label']}*:",
            button_text="Ver horários",
            sections=[{"title": "Horários disponíveis", "rows": rows}],
            next_step="schedule_slot_choice",
            context=context,
        )

    # ── helper: create appointment & confirm ────────────────────────────────
    def _confirm_appointment(chosen_slot: dict[str, Any]):
        from datetime import datetime as _dt
        from decimal import Decimal as _Decimal
        from app.repositories.appointments import AppointmentsRepository as _AR
        start_at = _dt.fromisoformat(chosen_slot["start_dt"])
        end_at = _dt.fromisoformat(chosen_slot["end_dt"])
        address_raw = context.get("address_raw") or context.get("address") or ""
        preview = context.get("quote_preview") or {}
        totals = preview.get("totals") or {}
        total_value = None
        if totals and totals.get("total_value"):
            try:
                total_value = _Decimal(str(totals["total_value"]))
            except Exception:
                total_value = None
        quote_id = None
        from sqlalchemy import select as _sel
        from app.db.models import Quote as _Q
        q = db.scalar(
            _sel(_Q)
            .where(_Q.company_id == company.id, _Q.client_id == client.id)
            .order_by(_Q.created_at.desc())
        )
        if q:
            quote_id = q.id
        repo = _AR(db)
        repo.create_appointment(
            company_id=company.id,
            client_id=client.id,
            quote_id=quote_id,
            address_raw=address_raw,
            start_at=start_at,
            end_at=end_at,
            service_type="protection_network",
            event_title=f"Instalação – {client.name or 'Cliente'}",
            valor=total_value,
            notes="Agendado pelo chatbot WhatsApp.",
        )
        db.commit()
        from datetime import date as _d
        date_str = chosen_slot["start_dt"][:10]
        try:
            full_date = _full_weekday_date_pt(_d.fromisoformat(date_str))
        except Exception:
            full_date = context.get("schedule_day_label") or date_str
        address_raw = context.get("address_raw") or context.get("address") or ""
        address_line = f"📍 *{address_raw}*\n" if address_raw.strip() else ""
        return _reply_text(
            conversation,
            db,
            text=(
                f"Perfeito! Seu agendamento ficou confirmado 🎉\n\n"
                f"📅 *{full_date}*\n"
                f"⏰ *{chosen_slot['label']}*\n"
                f"{address_line}"
                f"\nNossa equipe estará no local nesse horário. "
                f"Se precisar alterar alguma informação, é só me avisar 😊"
            ),
            next_step="schedule_confirmed",
            context=context,
        )

    # ── step: schedule_ask ───────────────────────────────────────────────────
    if current_step == "schedule_ask":
        if normalized in SCHEDULE_LATER_WORDS:
            return _reply_text(
                conversation,
                db,
                text="Sem problema! Quando quiser agendar, pode entrar em contato conosco. Até mais!",
                next_step="done",
                context=context,
            )
        cfg = _get_schedule_cfg(company, db)
        return _send_day_list("Perfeito. Escolha um dia para a instalação:", cfg)

    # ── step: schedule_day_choice ────────────────────────────────────────────
    if current_step == "schedule_day_choice":
        available_days: list = context.get("schedule_available_days") or []
        chosen_day = next(
            (d for d in available_days if d["id"] == normalized or d["label"].lower() == text.strip().lower()),
            None,
        )
        if chosen_day is None:
            for d in available_days:
                if normalized in d["id"] or normalized in d["label"].lower():
                    chosen_day = d
                    break
        if chosen_day is None and len(available_days) == 1:
            chosen_day = available_days[0]
        if chosen_day is None:
            cfg = _get_schedule_cfg(company, db)
            return _send_day_list("Por favor, selecione um dos dias disponíveis:", cfg)
        cfg = _get_schedule_cfg(company, db)
        return _send_slot_list(chosen_day, cfg)

    # ── step: schedule_slot_choice (main) ───────────────────────────────────
    if current_step in ("schedule_slot_choice", "schedule_slot"):
        slots: list = context.get("schedule_slots") or []
        chosen_slot = next(
            (s for s in slots if s["id"] == normalized or s["label"].lower() == text.strip().lower()),
            None,
        )
        if chosen_slot is None:
            for s in slots:
                if normalized in s["id"] or normalized in s["label"].lower():
                    chosen_slot = s
                    break
        if chosen_slot is None and len(slots) == 1:
            chosen_slot = slots[0]
        if chosen_slot is None:
            rows = [{"id": s["id"], "title": s["label"], "description": ""} for s in slots[:10]]
            return _reply_list(
                conversation,
                db,
                header="Escolha um horário",
                body="Por favor, selecione um dos horários abaixo:",
                button_text="Ver horários",
                sections=[{"title": "Horários disponíveis", "rows": rows}],
                next_step="schedule_slot_choice",
                context=context,
            )
        return _confirm_appointment(chosen_slot)

    # ── step: schedule_date (backward compat — redirect to day list) ─────────
    if current_step == "schedule_date":
        cfg = _get_schedule_cfg(company, db)
        return _send_day_list("Escolha um dia disponível para a instalação:", cfg)

    # ── step: schedule_confirmed ─────────────────────────────────────────────
    if current_step == "schedule_confirmed":
        return _reply_text(
            conversation,
            db,
            text="Seu agendamento já está registrado. Em caso de dúvidas, fale com nossa equipe. 😊",
            next_step="schedule_confirmed",
            context=context,
        )

    return _reply_text(
        conversation,
        db,
        text="Recebi sua mensagem. Vamos continuar seu atendimento.",
        next_step=current_step,
        context=context,
    )
