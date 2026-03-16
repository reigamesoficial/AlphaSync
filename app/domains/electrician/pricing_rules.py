"""Regras de precificação — Eletricista"""
from __future__ import annotations
from typing import Any

BASE_PRICES: dict[str, float] = {
    "instalacao_eletrica": 350,
    "troca_tomada": 120,
    "troca_disjuntor": 150,
    "instalacao_luminaria": 180,
    "instalacao_chuveiro": 200,
    "curto_circuito": 280,
    "manutencao_eletrica": 250,
}

URGENCY_SURCHARGE = {"normal": 0, "urgente": 80, "emergencia": 150}
VISIT_FEE = 80.0
MINIMUM_VALUE = 120.0


def calculate(context: dict[str, Any], company=None) -> dict[str, Any]:
    service = context.get("service_type", "manutencao_eletrica")
    urgency = context.get("urgency", "normal")

    base = BASE_PRICES.get(service, 200.0)
    surcharge = URGENCY_SURCHARGE.get(urgency, 0)
    subtotal = base + surcharge

    items = [
        {"description": f"Serviço: {service.replace('_', ' ').title()}", "unit_price": base, "total_price": base, "quantity": 1, "service_type": service, "notes": ""},
    ]
    if surcharge > 0:
        items.append({"description": f"Adicional de urgência ({urgency})", "unit_price": surcharge, "total_price": surcharge, "quantity": 1, "service_type": "surcharge"})
    if VISIT_FEE > 0:
        items.append({"description": "Taxa de visita técnica", "unit_price": VISIT_FEE, "total_price": VISIT_FEE, "quantity": 1, "service_type": "visit_fee"})

    total = max(subtotal + VISIT_FEE, MINIMUM_VALUE)
    return {"items": items, "totals": {"subtotal": subtotal, "discount": 0.0, "visit_fee": VISIT_FEE, "total_value": total}}
