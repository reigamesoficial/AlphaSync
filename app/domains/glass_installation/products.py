"""Catálogo de serviços — Vidraçaria / Glass Installation"""
from __future__ import annotations

SERVICES = [
    {"id": "box_banheiro", "label": "Box de Banheiro", "description": "Box de vidro temperado para banheiro"},
    {"id": "janela_vidro", "label": "Janela de Vidro", "description": "Instalação de janelas de vidro"},
    {"id": "porta_vidro", "label": "Porta de Vidro", "description": "Porta de vidro temperado ou laminado"},
    {"id": "espelho_medida", "label": "Espelho Sob Medida", "description": "Espelho cortado e instalado sob medida"},
    {"id": "fechamento_varanda", "label": "Fechamento de Varanda", "description": "Envidraçamento de varandas e sacadas"},
    {"id": "divisoria_vidro", "label": "Divisória de Vidro", "description": "Divisórias em vidro para escritórios"},
]

SERVICE_IDS = [s["id"] for s in SERVICES]

GLASS_TYPES = ["Temperado (segurança)", "Laminado (anti-estilhaço)", "Jateado (privacidade)", "Cristal (transparente)", "Espelhado"]
GLASS_IDS = ["temperado", "laminado", "jateado", "cristal", "espelhado"]
GLASS_PRICE_M2 = {"temperado": 180, "laminado": 220, "jateado": 200, "cristal": 160, "espelhado": 190}

FINISH_TYPES = ["Alumínio Natural", "Alumínio Preto", "Inox Escovado", "Box Click", "Embutido / Sem perfil"]
FINISH_IDS = ["aluminio", "aluminio_preto", "inox", "box_click", "embutido"]
FINISH_PRICES = {"aluminio": 0, "aluminio_preto": 50, "inox": 80, "box_click": 40, "embutido": 120}
