
from __future__ import annotations

from decimal import Decimal
from typing import Any

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


def _save_state(conversation, db, *, next_step: str, context: dict[str, Any]) -> None:
    conversation.bot_step = next_step
    conversation.bot_context = context
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
    colors = settings.get("available_colors") or ["branca", "preta", "areia", "cinza"]
    return [str(c).strip().lower() for c in colors if str(c).strip()]


def _build_mesh_types(company) -> list[str]:
    settings = _domain_settings(company)
    meshes = settings.get("available_mesh_types") or ["3x3", "5x5", "10x10"]
    return [str(m).strip().lower().replace("×", "x") for m in meshes if str(m).strip()]


def _resolve_plant_choice(text: str, plant_names: list[str]) -> str | None:
    if not plant_names:
        return None

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
    return f"Perfeito. Qual cor da rede você deseja?\n{numbered}"


def _mesh_prompt(company) -> str:
    meshes = _build_mesh_types(company)
    numbered = "\n".join(f"{idx}) {mesh}" for idx, mesh in enumerate(meshes, start=1))
    return f"Qual malha você deseja?\n{numbered}"


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


def _build_quote_confirmation_text(*, client_name: str | None, address: str, selected_items: list[dict[str, Any]], color: str | None, mesh_type: str | None, totals: dict[str, Any]) -> str:
    customer = client_name or "cliente"
    parts = _build_selected_items_summary(selected_items)
    subtotal = _format_money_br(totals.get("subtotal"))
    visit_fee = _format_money_br(totals.get("visit_fee"))
    total = _format_money_br(totals.get("total_value"))

    return (
        f"Perfeito, {customer}.\n\n"
        f"Confira seu orçamento:\n\n"
        f"Nome: {customer}\n"
        f"Endereço: {address}\n"
        f"Cor: {color or 'não informada'}\n"
        f"Malha: {mesh_type or 'não informada'}\n\n"
        f"Áreas selecionadas:\n{parts}\n\n"
        f"Subtotal: R$ {subtotal}\n"
        f"Taxa/visita: R$ {visit_fee}\n"
        f"Total estimado: R$ {total}\n\n"
        f"1) Confirmar orçamento\n"
        f"2) Alterar dados"
    )


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
            plants = lookup_result.get("plants", {}) or {}
            plant_names = list(plants.keys())

            if len(plant_names) > 1:
                context["address_plants"] = plant_names
                context["selected_items"] = []
                context["selected_item_ids"] = []

                rows = []
                for idx, plant in enumerate(plant_names[:10], start=1):
                    rows.append(
                        {
                            "id": f"planta_{plant}",
                            "title": f"{idx}) {plant}"[:24],
                            "description": "",
                        }
                    )

                return _reply_list(
                    conversation,
                    db,
                    header="Escolha a planta",
                    body="Esse endereço possui mais de uma planta. Qual opção é a sua?",
                    button_text="Ver opções",
                    sections=[{"title": "Plantas", "rows": rows}],
                    next_step="plant_choice",
                    context=context,
                )

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

            context["address_items_available"] = items
            context["selected_items"] = []
            context["selected_item_ids"] = []

            rows = _build_measure_rows(items)
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
        return _reply_text(
            conversation,
            db,
            text=(
                "Não encontrei medidas salvas para esse endereço.\n\n"
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

    if current_step == "plant_choice":
        plant_names = context.get("address_plants") or []
        chosen_plant = _resolve_plant_choice(text, plant_names)
        if not chosen_plant:
            return _reply_text(
                conversation,
                db,
                text="Escolha uma planta pelas opções da lista ou digitando o número correspondente.",
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
        context["address_items_available"] = items
        context["selected_items"] = []
        context["selected_item_ids"] = []

        rows = _build_measure_rows(items)
        rows.append({"id": "pick_manual", "title": "Informar manualmente", "description": ""})
        rows.append({"id": "pick_by_numbers", "title": "Escolher por números", "description": ""})

        return _reply_list(
            conversation,
            db,
            header="Itens encontrados",
            body=f"Encontrei medidas salvas para a planta {chosen_plant}. Qual área você quer orçar?",
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
            return _reply_text(
                conversation,
                db,
                text=_color_prompt(company),
                next_step="network_color",
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

        return _reply_text(
            conversation,
            db,
            text=_color_prompt(company),
            next_step="network_color",
            context=context,
        )

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
            return _reply_text(
                conversation,
                db,
                text=_color_prompt(company),
                next_step="network_color",
                context=context,
            )

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

    if current_step == "network_color":
        colors = _build_colors(company)
        chosen_color = _resolve_color_choice(text, colors)
        if not chosen_color:
            return _reply_text(
                conversation,
                db,
                text="Não reconheci essa cor.\n" + _color_prompt(company),
                next_step="network_color",
                context=context,
            )

        context["network_color"] = chosen_color.lower().strip()
        return _reply_text(
            conversation,
            db,
            text=_mesh_prompt(company),
            next_step="mesh_type",
            context=context,
        )

    if current_step == "mesh_type":
        meshes = _build_mesh_types(company)
        chosen_mesh = _resolve_mesh_choice(text, meshes)
        if not chosen_mesh:
            return _reply_text(
                conversation,
                db,
                text="Não reconheci essa malha.\n" + _mesh_prompt(company),
                next_step="mesh_type",
                context=context,
            )

        context["mesh_type"] = chosen_mesh.lower().strip().replace(" ", "").replace("×", "x")

        _rebuild_selected_items(context)
        selected_items = context.get("selected_items") or []
        if not selected_items:
            return _reply_text(
                conversation,
                db,
                text="Não encontrei nenhuma área selecionada. Escolha uma área primeiro.",
                next_step="measure_selection",
                context=context,
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

            return _reply_text(
                conversation,
                db,
                text="Perfeito. Seu orçamento foi confirmado e vou seguir com o próximo passo do atendimento.",
                next_step="quote_ready",
                context=context,
                extra={
                    "rule_result": rule_result.to_dict(),
                    "quote_preview": preview,
                },
            )

        if normalized in {"quote_confirm_edit", "alterar", "2"}:
            return _reply_buttons(
                conversation,
                db,
                text="O que você deseja alterar?",
                next_step="quote_edit_choice",
                context=context,
                buttons=[
                    {"id": "edit_address", "title": "Endereço"},
                    {"id": "edit_items", "title": "Áreas"},
                    {"id": "edit_color", "title": "Cor"},
                    {"id": "edit_mesh", "title": "Malha"},
                ],
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
        if normalized in {"edit_address", "endereço", "endereco", "1"}:
            return _reply_text(
                conversation,
                db,
                text="Tudo bem. Me envie novamente o endereço completo.",
                next_step="address_lookup",
                context={},
            )
        if normalized in {"edit_items", "áreas", "areas", "2"}:
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
            return _reply_text(
                conversation,
                db,
                text=_color_prompt(company),
                next_step="network_color",
                context=context,
            )
        if normalized in {"edit_mesh", "malha", "4"}:
            return _reply_text(
                conversation,
                db,
                text=_mesh_prompt(company),
                next_step="mesh_type",
                context=context,
            )

        return _reply_buttons(
            conversation,
            db,
            text="Escolha o que deseja alterar.",
            next_step="quote_edit_choice",
            context=context,
            buttons=[
                {"id": "edit_address", "title": "Endereço"},
                {"id": "edit_items", "title": "Áreas"},
                {"id": "edit_color", "title": "Cor"},
                {"id": "edit_mesh", "title": "Malha"},
            ],
        )

    return _reply_text(
        conversation,
        db,
        text="Recebi sua mensagem. Vamos continuar seu atendimento.",
        next_step=current_step,
        context=context,
    )
