"""Catálogo de serviços — Dedetização / Pest Control"""
from __future__ import annotations

SERVICES = [
    {"id": "dedetizacao", "label": "Dedetização Geral", "description": "Controle de insetos voadores e rasteiros"},
    {"id": "desratizacao", "label": "Desratização", "description": "Controle e eliminação de ratos e camundongos"},
    {"id": "descupinizacao", "label": "Descupinização", "description": "Tratamento e eliminação de cupins"},
    {"id": "controle_baratas", "label": "Controle de Baratas", "description": "Tratamento específico para baratas"},
    {"id": "controle_formigas", "label": "Controle de Formigas", "description": "Tratamento específico para formigas"},
    {"id": "dedetizacao_completa", "label": "Dedetização Completa (Pacote)", "description": "Controle completo de múltiplas pragas"},
]

SERVICE_IDS = [s["id"] for s in SERVICES]

PEST_TYPES = ["Baratas", "Ratos / Camundongos", "Cupins", "Formigas", "Mosquitos / Dengue", "Percevejos", "Pombos", "Múltiplas pragas"]
PEST_IDS = ["baratas", "ratos", "cupins", "formigas", "mosquitos", "percevejos", "pombos", "multiplas"]

PROPERTY_TYPES = ["Residência", "Comércio / Loja", "Restaurante / Alimentação", "Indústria / Armazém", "Condomínio"]
PROPERTY_IDS = ["residencia", "comercio", "restaurante", "industria", "condominio"]

SIZE_OPTIONS = ["Até 100 m²", "101 a 300 m²", "301 a 600 m²", "Acima de 600 m²"]
SIZE_IDS = ["ate_100m2", "101_300m2", "301_600m2", "acima_600m2"]

INFESTATION_LEVELS = ["Leve (poucos insetos)", "Moderada (frequente)", "Severa (alta presença)"]
INFESTATION_IDS = ["leve", "moderada", "severa"]
INFESTATION_MULTIPLIERS = {"leve": 1.0, "moderada": 1.3, "severa": 1.6}
