"""Regras de precificação — Câmeras de Segurança"""
from __future__ import annotations
from typing import Any

CAMERA_BASE_PRICE = 180.0
DVR_NVR_PRICES = {"dvr": 0, "nvr": 80, "nuvem": 50, "nao_sei": 0}
CAMERA_COUNT_VALUES = {"1_2": 2, "3_4": 4, "5_8": 8, "9_16": 16, "acima_16": 20}
SERVICE_BASE = {"instalacao_cameras": 0, "manutencao_cameras": 250, "ampliacao_cameras": 0, "configuracao_remota": 180, "troca_dvr_nvr": 350, "visita_tecnica": 120}
VISIT_FEE = 100.0
MINIMUM_VALUE = 200.0


def calculate(context: dict[str, Any], company=None) -> dict[str, Any]:
    service = context.get("service_type", "instalacao_cameras")
    cam_key = context.get("camera_count", "3_4")
    recording = context.get("recording_type", "dvr")

    cam_qty = CAMERA_COUNT_VALUES.get(cam_key, 4)
    service_base = SERVICE_BASE.get(service, 0)

    if service in ("instalacao_cameras", "ampliacao_cameras"):
        cam_price = cam_qty * CAMERA_BASE_PRICE
        dvr_price = DVR_NVR_PRICES.get(recording, 0)
        subtotal = cam_price + dvr_price + VISIT_FEE
        items = [
            {"description": f"Câmeras ({cam_qty} unidades)", "unit_price": CAMERA_BASE_PRICE, "total_price": cam_price, "quantity": cam_qty, "service_type": service},
            {"description": "Taxa de visita / instalação", "unit_price": VISIT_FEE, "total_price": VISIT_FEE, "quantity": 1, "service_type": "visit_fee"},
        ]
        if dvr_price > 0:
            items.insert(1, {"description": f"Config. {recording.upper()}", "unit_price": dvr_price, "total_price": dvr_price, "quantity": 1, "service_type": "extra"})
    else:
        subtotal = service_base + VISIT_FEE
        items = [
            {"description": f"Serviço: {service.replace('_', ' ').title()}", "unit_price": service_base, "total_price": service_base, "quantity": 1, "service_type": service},
            {"description": "Taxa de visita técnica", "unit_price": VISIT_FEE, "total_price": VISIT_FEE, "quantity": 1, "service_type": "visit_fee"},
        ]

    total = max(subtotal, MINIMUM_VALUE)
    return {"items": items, "totals": {"subtotal": subtotal - VISIT_FEE, "discount": 0.0, "visit_fee": VISIT_FEE, "total_value": total}}
