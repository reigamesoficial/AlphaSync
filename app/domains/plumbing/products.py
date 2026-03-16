"""Catálogo de serviços — Encanamento / Plumbing"""
from __future__ import annotations

SERVICES = [
    {"id": "reparo_vazamento", "label": "Reparo de Vazamento", "description": "Localização e reparo de vazamentos"},
    {"id": "desentupimento", "label": "Desentupimento", "description": "Desentupimento de pias, ralos e esgoto"},
    {"id": "troca_torneira", "label": "Troca de Torneira / Vaso", "description": "Substituição de torneiras, registros e vasos"},
    {"id": "reparo_descarga", "label": "Reparo de Descarga / Caixa", "description": "Reparo ou troca de válvula e caixa acoplada"},
    {"id": "instalacao_hidraulica", "label": "Instalação Hidráulica", "description": "Instalação de novos pontos hidráulicos"},
    {"id": "inspecao_hidraulica", "label": "Inspeção Hidráulica", "description": "Vistoria completa da instalação"},
]

SERVICE_IDS = [s["id"] for s in SERVICES]

URGENCY_OPTIONS = ["Normal (1-3 dias)", "Urgente (hoje ou amanhã)", "Emergência (agora)"]
URGENCY_IDS = ["normal", "urgente", "emergencia"]

LOCATIONS = ["Cozinha", "Banheiro", "Área de serviço", "Externo / jardim", "Caixa d'água / cisterna", "Múltiplos locais"]
LOCATION_IDS = ["cozinha", "banheiro", "area_servico", "externo", "caixa_dagua", "multiplos"]
