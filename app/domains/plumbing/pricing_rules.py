"""Regras de precificação — Plumbing"""
from __future__ import annotations
from typing import Any

BASE_PRICES: dict[str, float] = {
    "reparo_vazamento": 200,
    "desentupimento": 220,
    "troca_torneira": 180,
    "reparo_descarga": 160,
    "instalacao_hidraulica": 400,
    "inspecao_hidraulica": 150,
}

URGENCY_SURCHARGE = {"normal": 0, "urgente": 80, "emergencia": 150}
VISIT_FEE = 80.0
MINIMUM_VALUE = 120.0


def calculate(context: dict[str, Any], company=None) -> dict[str, Any]:
    service = context.get("service_type", "reparo_vazamento")
    urgency = context.get("urgency", "normal")

    base = BASE_PRICES.get(service, 200.0)
    surcharge = URGENCY_SURCHARGE.get(urgency, 0)

    items = [
        {"description": f"Serviço: {service.replace('_', ' ').title()}", "unit_price": base, "total_price": base, "quantity": 1, "service_type": service, "notes": f"Local: {context.get('service_location', 'não informado')}"},
        {"description": "Taxa de visita técnica", "unit_price": VISIT_FEE, "total_price": VISIT_FEE, "quantity": 1, "service_type": "visit_fee"},
    ]
    if surcharge > 0:
        items.append({"description": f"Adicional urgência ({urgency})", "unit_price": surcharge, "total_price": surcharge, "quantity": 1, "service_type": "surcharge"})

    total = max(base + surcharge + VISIT_FEE, MINIMUM_VALUE)
    return {"items": items, "totals": {"subtotal": base + surcharge, "discount": 0.0, "visit_fee": VISIT_FEE, "total_value": total}}
