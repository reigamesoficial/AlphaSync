"""Catálogo de serviços — Câmeras de Segurança"""
from __future__ import annotations

SERVICES = [
    {"id": "instalacao_cameras", "label": "Instalação de Câmeras", "description": "Instalação completa de sistema de câmeras"},
    {"id": "manutencao_cameras", "label": "Manutenção do Sistema", "description": "Revisão, limpeza e ajuste de câmeras"},
    {"id": "ampliacao_cameras", "label": "Ampliação do Sistema", "description": "Adição de câmeras ao sistema existente"},
    {"id": "configuracao_remota", "label": "Configuração de Acesso Remoto", "description": "Configuração de visualização via celular/PC"},
    {"id": "troca_dvr_nvr", "label": "Troca de DVR / NVR", "description": "Substituição do gravador do sistema"},
    {"id": "visita_tecnica", "label": "Visita Técnica", "description": "Vistoria e diagnóstico do sistema"},
]

SERVICE_IDS = [s["id"] for s in SERVICES]

PROPERTY_TYPES = ["Residência", "Comércio / Loja", "Empresa / Escritório", "Indústria", "Condomínio", "Estacionamento"]
PROPERTY_IDS = ["residencia", "comercio", "empresa", "industria", "condominio", "estacionamento"]

CAMERA_COUNT_OPTIONS = ["1 a 2 câmeras", "3 a 4 câmeras", "5 a 8 câmeras", "9 a 16 câmeras", "Acima de 16 câmeras"]
CAMERA_COUNT_IDS = ["1_2", "3_4", "5_8", "9_16", "acima_16"]
CAMERA_COUNT_VALUES = {"1_2": 2, "3_4": 4, "5_8": 8, "9_16": 16, "acima_16": 20}

RECORDING_TYPES = ["DVR (câmeras analógicas)", "NVR (câmeras IP)", "Nuvem (cloud)", "Não sei / quero indicação"]
RECORDING_IDS = ["dvr", "nvr", "nuvem", "nao_sei"]
