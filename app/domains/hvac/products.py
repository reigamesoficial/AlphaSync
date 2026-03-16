"""Catálogo de serviços — Ar Condicionado (HVAC)"""
from __future__ import annotations

SERVICES = [
    {"id": "instalacao_ar", "label": "Instalação de Ar Condicionado", "description": "Instalação de novos equipamentos"},
    {"id": "manutencao_ar", "label": "Manutenção Preventiva", "description": "Revisão completa do equipamento"},
    {"id": "limpeza_ar", "label": "Limpeza / Higienização", "description": "Higienização completa de filtros e serpentinas"},
    {"id": "carga_gas", "label": "Carga de Gás", "description": "Reposição de gás refrigerante"},
    {"id": "reparo_ar", "label": "Reparo / Defeito", "description": "Diagnóstico e reparo de defeitos"},
]

SERVICE_IDS = [s["id"] for s in SERVICES]

EQUIPMENT_TYPES = ["Split", "Split Inverter", "Janeleiro", "Portátil", "Cassete / Central"]
EQUIPMENT_IDS = ["split", "split_inverter", "janeleiro", "portatil", "cassete"]

BTU_OPTIONS = ["Até 9.000 BTU", "12.000 BTU", "18.000 BTU", "24.000 BTU", "30.000 BTU", "36.000 BTU ou mais"]
BTU_IDS = ["ate_9000", "12000", "18000", "24000", "30000", "36000_mais"]
BTU_MULTIPLIERS = {"ate_9000": 1.0, "12000": 1.1, "18000": 1.2, "24000": 1.35, "30000": 1.5, "36000_mais": 1.8}
