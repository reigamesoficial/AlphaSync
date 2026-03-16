"""Catálogo de produtos e serviços — Limpeza"""
from __future__ import annotations

SERVICES = [
    {"id": "limpeza_residencial", "label": "Limpeza Residencial", "description": "Limpeza completa de casa ou apartamento"},
    {"id": "limpeza_comercial", "label": "Limpeza Comercial", "description": "Limpeza de escritórios, lojas e comércios"},
    {"id": "limpeza_pos_obra", "label": "Limpeza Pós-Obra", "description": "Remoção de entulho, pó de obra e acabamento"},
    {"id": "limpeza_pesada", "label": "Limpeza Pesada", "description": "Limpeza de imóveis sujos ou abandonados"},
    {"id": "limpeza_mudanca", "label": "Limpeza de Mudança", "description": "Limpeza antes ou depois de mudança"},
    {"id": "limpeza_estofados", "label": "Limpeza de Estofados", "description": "Higienização de sofás, cadeiras e colchões"},
]

SERVICE_IDS = [s["id"] for s in SERVICES]
SERVICE_LABELS = {s["id"]: s["label"] for s in SERVICES}

PROPERTY_TYPES = ["Casa", "Apartamento", "Comercial / Escritório", "Outro"]
PROPERTY_TYPE_IDS = ["casa", "apartamento", "comercial", "outro"]

PROPERTY_SIZES = [
    {"id": "ate_50m2", "label": "Até 50 m²"},
    {"id": "51_100m2", "label": "51 a 100 m²"},
    {"id": "101_200m2", "label": "101 a 200 m²"},
    {"id": "acima_200m2", "label": "Acima de 200 m²"},
]
PROPERTY_SIZE_IDS = [s["id"] for s in PROPERTY_SIZES]
PROPERTY_SIZE_LABELS = {s["id"]: s["label"] for s in PROPERTY_SIZES}

EXTRAS = [
    {"id": "extra_janelas", "label": "Limpeza de janelas"},
    {"id": "extra_sacada", "label": "Sacada / varanda"},
    {"id": "extra_area_externa", "label": "Área externa"},
    {"id": "extra_armarios", "label": "Interior de armários"},
    {"id": "extra_fogao", "label": "Limpeza de fogão / forno"},
]
