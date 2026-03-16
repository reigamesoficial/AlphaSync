"""Catálogo de serviços — Eletricista"""
from __future__ import annotations

SERVICES = [
    {"id": "instalacao_eletrica", "label": "Instalação Elétrica", "description": "Instalação de circuitos e quadros elétricos"},
    {"id": "troca_tomada", "label": "Troca de Tomada / Interruptor", "description": "Substituição de tomadas e interruptores"},
    {"id": "troca_disjuntor", "label": "Troca de Disjuntor", "description": "Substituição de disjuntores no quadro"},
    {"id": "instalacao_luminaria", "label": "Instalação de Luminária", "description": "Instalação de luminárias, spots e lustres"},
    {"id": "instalacao_chuveiro", "label": "Instalação de Chuveiro Elétrico", "description": "Instalação ou troca de chuveiro"},
    {"id": "curto_circuito", "label": "Curto Circuito / Falha Elétrica", "description": "Diagnóstico e reparo de curto circuito"},
    {"id": "manutencao_eletrica", "label": "Manutenção Elétrica Geral", "description": "Manutenção preventiva e corretiva"},
]

SERVICE_IDS = [s["id"] for s in SERVICES]
SERVICE_LABELS = {s["id"]: s["label"] for s in SERVICES}

URGENCY_OPTIONS = ["Normal (1-3 dias)", "Urgente (hoje ou amanhã)", "Emergência (agora)"]
URGENCY_IDS = ["normal", "urgente", "emergencia"]
URGENCY_PRICES = {"normal": 0, "urgente": 80, "emergencia": 150}
