"""Regras de precificação — Limpeza"""
from __future__ import annotations
from typing import Any

BASE_PRICES: dict[str, dict[str, float]] = {
    "limpeza_residencial": {"ate_50m2": 180, "51_100m2": 280, "101_200m2": 380, "acima_200m2": 520},
    "limpeza_comercial":   {"ate_50m2": 220, "51_100m2": 320, "101_200m2": 450, "acima_200m2": 620},
    "limpeza_pos_obra":    {"ate_50m2": 350, "51_100m2": 500, "101_200m2": 700, "acima_200m2": 950},
    "limpeza_pesada":      {"ate_50m2": 400, "51_100m2": 580, "101_200m2": 800, "acima_200m2": 1100},
    "limpeza_mudanca":     {"ate_50m2": 200, "51_100m2": 300, "101_200m2": 420, "acima_200m2": 580},
    "limpeza_estofados":   {"ate_50m2": 150, "51_100m2": 150, "101_200m2": 150, "acima_200m2": 150},
}

EXTRA_PRICES: dict[str, float] = {
    "extra_janelas": 80,
    "extra_sacada": 60,
    "extra_area_externa": 90,
    "extra_armarios": 50,
    "extra_fogao": 40,
}

MINIMUM_VALUE = 120.0
VISIT_FEE = 0.0


def calculate(context: dict[str, Any], company=None) -> dict[str, Any]:
    service = context.get("service_type", "limpeza_residencial")
    size = context.get("property_size", "ate_50m2")
    extras = context.get("selected_extras") or []

    prices_by_size = BASE_PRICES.get(service, BASE_PRICES["limpeza_residencial"])
    base = prices_by_size.get(size, 200.0)

    extra_total = sum(EXTRA_PRICES.get(e, 0) for e in extras)
    subtotal = base + extra_total

    items = [{"description": f"Serviço: {service.replace('_', ' ').title()}", "unit_price": base, "total_price": base, "quantity": 1, "service_type": service, "notes": f"Tamanho: {size}"}]
    for e in extras:
        if e in EXTRA_PRICES:
            items.append({"description": f"Extra: {e.replace('_', ' ').replace('extra ', '').title()}", "unit_price": EXTRA_PRICES[e], "total_price": EXTRA_PRICES[e], "quantity": 1, "service_type": "extra"})

    total = max(subtotal + VISIT_FEE, MINIMUM_VALUE)
    return {"items": items, "totals": {"subtotal": subtotal, "discount": 0.0, "visit_fee": VISIT_FEE, "total_value": total}}
