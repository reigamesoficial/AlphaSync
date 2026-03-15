from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from app.domains.protection_network.job_rules import ProtectionNetworkJobRuleResult

TWOPLACES = Decimal("0.01")


def _to_decimal(value: Any, default: str = "0.00") -> Decimal:
    if value is None:
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal(default)


def _money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def normalize_mesh(mesh_type: str | None) -> str:
    if not mesh_type:
        return "3x3"
    value = mesh_type.strip().lower().replace(" ", "").replace("×", "x")
    return value


def normalize_color(color: str | None) -> str | None:
    if not color:
        return None
    return color.strip().lower()


def get_effective_settings(company) -> dict[str, Any]:
    extra = {}
    if getattr(company, "settings", None) and getattr(company.settings, "extra_settings", None):
        extra = company.settings.extra_settings or {}

    pricing_rules = extra.get("pricing_rules") or {}

    return {
        "minimum_order_value": _to_decimal(pricing_rules.get("minimum_order_value", 150.0)),
        "visit_fee": _to_decimal(pricing_rules.get("visit_fee", 0.0)),
        "mesh_price_overrides": pricing_rules.get("mesh_price_overrides") or {
            "3x3": 50.0,
            "5x5": 40.0,
            "10x10": 35.0,
        },
        "color_price_overrides": pricing_rules.get("color_price_overrides") or {},
    }


def get_effective_price_per_m2(
    *,
    company,
    mesh_type: str,
    color: str | None,
    rule_result: ProtectionNetworkJobRuleResult | None = None,
) -> Decimal:
    config = get_effective_settings(company)

    if rule_result and rule_result.price_per_m2_override is not None:
        return _money(_to_decimal(rule_result.price_per_m2_override))

    mesh = normalize_mesh(mesh_type)
    color_norm = normalize_color(color)

    mesh_prices = config["mesh_price_overrides"] or {}
    color_overrides = config["color_price_overrides"] or {}

    base_price = _to_decimal(mesh_prices.get(mesh, 50.0))
    if color_norm and color_norm in color_overrides:
        base_price += _to_decimal(color_overrides[color_norm])

    return _money(base_price)


def calculate_area(width: Any, height: Any) -> Decimal:
    return _money(_to_decimal(width) * _to_decimal(height))


def build_quote_item(
    *,
    item: dict[str, Any],
    company,
    mesh_type: str,
    color: str | None,
    rule_result: ProtectionNetworkJobRuleResult | None = None,
) -> dict[str, Any]:
    width = _to_decimal(item.get("width"))
    height = _to_decimal(item.get("height"))
    area = calculate_area(width, height)
    unit_price = get_effective_price_per_m2(
        company=company,
        mesh_type=mesh_type,
        color=color,
        rule_result=rule_result,
    )
    total_price = _money(area * unit_price)

    descricao_base = (item.get("descricao") or "").strip()
    tipo = (item.get("tipo") or "item").strip().lower()
    description = f"Rede de proteção - {tipo} {descricao_base}".strip()

    return {
        "description": description,
        "service_type": "protection_network",
        "width_cm": width,
        "height_cm": height,
        "quantity": 1,
        "unit_price": unit_price,
        "total_price": total_price,
        "status": "PENDING",
        "notes": (
            f"Malha {normalize_mesh(mesh_type)} | "
            f"Cor {color or 'não informada'} | "
            f"Área {area} m²"
        ),
        "domain_data": {
            "source": item.get("source"),
            "legacy_id": item.get("legacy_id"),
            "tipo": tipo,
            "descricao": descricao_base,
            "mesh_type": normalize_mesh(mesh_type),
            "color": color,
            "area_m2": str(area),
            "price_per_m2": str(unit_price),
        },
    }


def build_quote_items_from_selection(
    *,
    selected_items: list[dict[str, Any]],
    company,
    mesh_type: str,
    color: str | None,
    rule_result: ProtectionNetworkJobRuleResult | None = None,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in selected_items:
        items.append(
            build_quote_item(
                item=item,
                company=company,
                mesh_type=mesh_type,
                color=color,
                rule_result=rule_result,
            )
        )
    return items


def calculate_quote_totals(
    *,
    company,
    items: list[dict[str, Any]],
    rule_result: ProtectionNetworkJobRuleResult | None = None,
) -> dict[str, Decimal]:
    config = get_effective_settings(company)

    subtotal = _money(sum((_to_decimal(item.get("total_price")) for item in items), Decimal("0.00")))

    visit_fee = config["visit_fee"]
    if rule_result and rule_result.visit_fee_override is not None:
        visit_fee = _to_decimal(rule_result.visit_fee_override)

    minimum_order_value = config["minimum_order_value"]
    if rule_result and rule_result.minimum_order_value_override is not None:
        minimum_order_value = _to_decimal(rule_result.minimum_order_value_override)

    total = _money(subtotal + visit_fee)
    if total < minimum_order_value:
        total = minimum_order_value

    return {
        "subtotal": subtotal,
        "discount": Decimal("0.00"),
        "visit_fee": _money(visit_fee),
        "minimum_order_value": _money(minimum_order_value),
        "total_value": _money(total),
    }