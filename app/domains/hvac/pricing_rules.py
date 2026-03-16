"""Regras de precificação — HVAC"""
from __future__ import annotations
from typing import Any

BASE_PRICES: dict[str, float] = {
    "instalacao_ar": 350,
    "manutencao_ar": 200,
    "limpeza_ar": 180,
    "carga_gas": 280,
    "reparo_ar": 250,
}

BTU_MULTIPLIERS = {"ate_9000": 1.0, "12000": 1.1, "18000": 1.2, "24000": 1.35, "30000": 1.5, "36000_mais": 1.8}
VISIT_FEE = 80.0
MINIMUM_VALUE = 150.0


def calculate(context: dict[str, Any], company=None) -> dict[str, Any]:
    service = context.get("service_type", "manutencao_ar")
    btu = context.get("btu", "12000")

    base = BASE_PRICES.get(service, 220.0)
    multiplier = BTU_MULTIPLIERS.get(btu, 1.0)
    service_price = round(base * multiplier, 2)

    items = [
        {"description": f"{service.replace('_', ' ').title()} ({btu} BTU)", "unit_price": service_price, "total_price": service_price, "quantity": 1, "service_type": service, "notes": f"Equipamento: {context.get('equipment_type', 'não informado')}"},
        {"description": "Taxa de visita técnica", "unit_price": VISIT_FEE, "total_price": VISIT_FEE, "quantity": 1, "service_type": "visit_fee"},
    ]

    subtotal = service_price
    total = max(subtotal + VISIT_FEE, MINIMUM_VALUE)
    return {"items": items, "totals": {"subtotal": subtotal, "discount": 0.0, "visit_fee": VISIT_FEE, "total_value": total}}
