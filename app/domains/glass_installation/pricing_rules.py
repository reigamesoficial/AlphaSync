"""Regras de precificação — Glass Installation"""
from __future__ import annotations
from typing import Any

GLASS_PRICE_M2 = {"temperado": 180, "laminado": 220, "jateado": 200, "cristal": 160, "espelhado": 190}
FINISH_PRICES = {"aluminio": 0, "aluminio_preto": 50, "inox": 80, "box_click": 40, "embutido": 120}

SERVICE_MINIMUMS = {
    "box_banheiro": 350, "janela_vidro": 280, "porta_vidro": 500,
    "espelho_medida": 200, "fechamento_varanda": 800, "divisoria_vidro": 600,
}
VISIT_FEE = 100.0
MINIMUM_VALUE = 200.0


def calculate(context: dict[str, Any], company=None) -> dict[str, Any]:
    service = context.get("service_type", "box_banheiro")
    glass = context.get("glass_type", "temperado")
    finish = context.get("finish_type", "aluminio")

    try:
        dims = context.get("dimensions", "1.5x2.0")
        parts = str(dims).replace("x", ",").replace("X", ",").replace(" ", "").split(",")
        width = float(parts[0])
        height = float(parts[1]) if len(parts) > 1 else 2.0
        area = round(width * height, 2)
    except Exception:
        area = 2.0

    price_m2 = GLASS_PRICE_M2.get(glass, 180)
    glass_price = round(area * price_m2, 2)
    finish_price = FINISH_PRICES.get(finish, 0)
    minimum = SERVICE_MINIMUMS.get(service, 300)

    subtotal = max(glass_price + finish_price, minimum)

    items = [
        {"description": f"Vidro {glass.replace('_', ' ').title()} ({area} m²)", "unit_price": price_m2, "total_price": glass_price, "quantity": area, "service_type": service, "notes": f"Medidas: {context.get('dimensions', 'não informado')}"},
        {"description": "Taxa de visita / instalação", "unit_price": VISIT_FEE, "total_price": VISIT_FEE, "quantity": 1, "service_type": "visit_fee"},
    ]
    if finish_price > 0:
        items.insert(1, {"description": f"Acabamento: {finish.replace('_', ' ').title()}", "unit_price": finish_price, "total_price": finish_price, "quantity": 1, "service_type": "extra"})

    total = subtotal + VISIT_FEE
    return {"items": items, "totals": {"subtotal": subtotal, "discount": 0.0, "visit_fee": VISIT_FEE, "total_value": total}}
