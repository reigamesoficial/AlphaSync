"""Regras de precificação — Pest Control"""
from __future__ import annotations
from typing import Any

BASE_PRICES: dict[str, dict[str, float]] = {
    "dedetizacao":        {"ate_100m2": 200, "101_300m2": 320, "301_600m2": 480, "acima_600m2": 700},
    "desratizacao":       {"ate_100m2": 280, "101_300m2": 420, "301_600m2": 600, "acima_600m2": 900},
    "descupinizacao":     {"ate_100m2": 350, "101_300m2": 550, "301_600m2": 800, "acima_600m2": 1200},
    "controle_baratas":   {"ate_100m2": 180, "101_300m2": 280, "301_600m2": 420, "acima_600m2": 600},
    "controle_formigas":  {"ate_100m2": 160, "101_300m2": 260, "301_600m2": 380, "acima_600m2": 550},
    "dedetizacao_completa": {"ate_100m2": 450, "101_300m2": 700, "301_600m2": 1000, "acima_600m2": 1500},
}

INFESTATION_MULTIPLIERS = {"leve": 1.0, "moderada": 1.3, "severa": 1.6}
RESTAURANT_SURCHARGE = 80.0
MINIMUM_VALUE = 150.0
VISIT_FEE = 0.0

SERVICE_FOR_PEST = {
    "baratas": "controle_baratas", "ratos": "desratizacao", "cupins": "descupinizacao",
    "formigas": "controle_formigas", "mosquitos": "dedetizacao", "percevejos": "dedetizacao",
    "pombos": "dedetizacao", "multiplas": "dedetizacao_completa",
}


def calculate(context: dict[str, Any], company=None) -> dict[str, Any]:
    pest = context.get("pest_type", "baratas")
    service = context.get("service_type") or SERVICE_FOR_PEST.get(pest, "dedetizacao")
    size = context.get("property_size", "ate_100m2")
    infestation = context.get("infestation_level", "leve")
    prop_type = context.get("property_type", "residencia")

    sizes = BASE_PRICES.get(service, BASE_PRICES["dedetizacao"])
    base = sizes.get(size, 200.0)
    multiplier = INFESTATION_MULTIPLIERS.get(infestation, 1.0)
    service_price = round(base * multiplier, 2)
    surcharge = RESTAURANT_SURCHARGE if prop_type == "restaurante" else 0.0

    items = [{"description": f"{service.replace('_', ' ').title()} — {pest.replace('_', ' ').title()}", "unit_price": service_price, "total_price": service_price, "quantity": 1, "service_type": service, "notes": f"Área: {size} | Infestação: {infestation}"}]
    if surcharge:
        items.append({"description": "Adicional estabelecimento alimentício", "unit_price": surcharge, "total_price": surcharge, "quantity": 1, "service_type": "surcharge"})

    total = max(service_price + surcharge, MINIMUM_VALUE)
    return {"items": items, "totals": {"subtotal": service_price + surcharge, "discount": 0.0, "visit_fee": 0.0, "total_value": total}}
