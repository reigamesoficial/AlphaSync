"""
Serviço para administração de DomainDefinition.

Responsabilidades:
- Sincronizar domínios builtin do código para o banco na inicialização
- CRUD de DomainDefinition para o painel master
- Fornecer config_json para o onboarding
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import DomainDefinition
from app.repositories.domain_definitions import DomainDefinitionsRepository

logger = logging.getLogger("alphasync.domains")

# Mapeamento estático de ícone e descrição por domínio
_DOMAIN_META: dict[str, dict[str, str]] = {
    "protection_network": {"icon": "🕸️", "description": "Instalação e manutenção de redes de proteção"},
    "hvac":               {"icon": "❄️", "description": "Ar condicionado, refrigeração e climatização"},
    "electrician":        {"icon": "⚡", "description": "Serviços elétricos residenciais e comerciais"},
    "plumbing":           {"icon": "🔧", "description": "Encanamento, vazamentos e instalações hidráulicas"},
    "cleaning":           {"icon": "🧹", "description": "Limpeza residencial, comercial e pós-obra"},
    "glass_installation": {"icon": "🪟", "description": "Box de banheiro, janelas, portas e espelhos de vidro"},
    "pest_control":       {"icon": "🐛", "description": "Dedetização, desratização e controle de pragas"},
    "security_cameras":   {"icon": "📷", "description": "Câmeras de segurança, DVR/NVR e monitoramento"},
}

# Defaults de config_json por domínio (editáveis pelo master)
_DOMAIN_CONFIGS: dict[str, dict[str, Any]] = {
    "protection_network": {
        "bot": {
            "greeting_message": "Olá! Bem-vindo(a) ao serviço de Redes de Proteção! 🕸️ Como posso ajudar?",
            "tone": "profissional",
            "fallback_message": "Não entendi sua mensagem. Pode repetir ou digitar *menu*?",
            "confirm_message": "Perfeito! Vou gerar seu orçamento.",
        },
        "services": ["janela", "sacada", "varanda", "escada", "quadra", "cobertura", "outro"],
        "pricing_defaults": {"minimum_order_value": 150.0, "visit_fee": 0.0, "default_price_per_m2": 45.0},
        "onboarding_defaults": {
            "bot_name": "Assistente", "quote_prefix": "RDP", "currency": "BRL",
            "timezone": "America/Sao_Paulo",
            "extra_settings": {"show_measures_to_customer": True, "pricing_rules": {"minimum_order_value": 150.0, "visit_fee": 0.0}},
        },
        "labels": {"service_type": "Tipo de instalação", "measurement": "Medidas (m²)"},
    },
    "cleaning": {
        "bot": {
            "greeting_message": "Olá! 👋 Bem-vindo(a) ao serviço de *Limpeza*! Qual tipo de limpeza você precisa?",
            "tone": "amigável",
            "fallback_message": "Não entendi. Informe o número da opção ou digite *menu* para reiniciar.",
            "confirm_message": "Ótimo! Confirme os dados do orçamento:",
        },
        "services": ["limpeza_residencial", "limpeza_comercial", "limpeza_pos_obra", "limpeza_pesada", "limpeza_mudanca", "limpeza_estofados"],
        "pricing_defaults": {"minimum_order_value": 120.0, "visit_fee": 0.0},
        "onboarding_defaults": {
            "bot_name": "Limpeza Bot", "quote_prefix": "LIM", "currency": "BRL",
            "timezone": "America/Sao_Paulo", "extra_settings": {},
        },
        "labels": {"service_type": "Tipo de limpeza", "property_type": "Tipo de imóvel", "property_size": "Tamanho"},
    },
    "electrician": {
        "bot": {
            "greeting_message": "Olá! ⚡ Bem-vindo(a) ao serviço de *Eletricista*! Qual serviço você precisa?",
            "tone": "objetivo",
            "fallback_message": "Não entendi. Informe o número da opção ou digite *menu*.",
            "confirm_message": "Perfeito! Confira o resumo abaixo:",
        },
        "services": ["instalacao_eletrica", "troca_tomada", "troca_disjuntor", "instalacao_luminaria", "instalacao_chuveiro", "curto_circuito", "manutencao_eletrica"],
        "pricing_defaults": {"minimum_order_value": 120.0, "visit_fee": 80.0},
        "onboarding_defaults": {
            "bot_name": "Elétrica Bot", "quote_prefix": "ELE", "currency": "BRL",
            "timezone": "America/Sao_Paulo", "extra_settings": {},
        },
        "labels": {"service_type": "Tipo de serviço", "urgency": "Urgência"},
    },
    "hvac": {
        "bot": {
            "greeting_message": "Olá! ❄️ Bem-vindo(a) ao serviço de *Ar Condicionado*! Qual serviço você precisa?",
            "tone": "técnico",
            "fallback_message": "Não entendi. Informe o número da opção ou *menu*.",
            "confirm_message": "Certo! Confira o orçamento:",
        },
        "services": ["instalacao_ar", "manutencao_ar", "limpeza_ar", "carga_gas", "reparo_ar"],
        "pricing_defaults": {"minimum_order_value": 150.0, "visit_fee": 80.0},
        "onboarding_defaults": {
            "bot_name": "HVAC Bot", "quote_prefix": "CLI", "currency": "BRL",
            "timezone": "America/Sao_Paulo", "extra_settings": {},
        },
        "labels": {"service_type": "Serviço", "equipment_type": "Tipo de equipamento", "btu": "Capacidade (BTU)"},
    },
    "pest_control": {
        "bot": {
            "greeting_message": "Olá! 🐛 Bem-vindo(a) ao serviço de *Dedetização*! Qual praga está com problema?",
            "tone": "amigável",
            "fallback_message": "Não entendi. Informe o número ou *menu*.",
            "confirm_message": "Certo! Veja o resumo do orçamento:",
        },
        "services": ["dedetizacao", "desratizacao", "descupinizacao", "controle_baratas", "controle_formigas", "dedetizacao_completa"],
        "pricing_defaults": {"minimum_order_value": 150.0, "visit_fee": 0.0},
        "onboarding_defaults": {
            "bot_name": "Dedetização Bot", "quote_prefix": "DED", "currency": "BRL",
            "timezone": "America/Sao_Paulo", "extra_settings": {},
        },
        "labels": {"pest_type": "Tipo de praga", "property_size": "Tamanho do local", "infestation_level": "Nível de infestação"},
    },
    "plumbing": {
        "bot": {
            "greeting_message": "Olá! 🔧 Bem-vindo(a) ao serviço de *Encanamento*! Qual serviço você precisa?",
            "tone": "objetivo",
            "fallback_message": "Não entendi. Informe o número ou *menu*.",
            "confirm_message": "Perfeito! Confira o orçamento:",
        },
        "services": ["reparo_vazamento", "desentupimento", "troca_torneira", "reparo_descarga", "instalacao_hidraulica", "inspecao_hidraulica"],
        "pricing_defaults": {"minimum_order_value": 120.0, "visit_fee": 80.0},
        "onboarding_defaults": {
            "bot_name": "Hidráulica Bot", "quote_prefix": "HID", "currency": "BRL",
            "timezone": "America/Sao_Paulo", "extra_settings": {},
        },
        "labels": {"service_type": "Tipo de serviço", "urgency": "Urgência", "service_location": "Local"},
    },
    "glass_installation": {
        "bot": {
            "greeting_message": "Olá! 🪟 Bem-vindo(a) à *Vidraçaria*! Qual serviço você precisa?",
            "tone": "amigável",
            "fallback_message": "Não entendi. Informe o número ou *menu*.",
            "confirm_message": "Ótimo! Veja o orçamento estimado:",
        },
        "services": ["box_banheiro", "janela_vidro", "porta_vidro", "espelho_medida", "fechamento_varanda", "divisoria_vidro"],
        "pricing_defaults": {"minimum_order_value": 200.0, "visit_fee": 100.0},
        "onboarding_defaults": {
            "bot_name": "Vidraçaria Bot", "quote_prefix": "VID", "currency": "BRL",
            "timezone": "America/Sao_Paulo", "extra_settings": {},
        },
        "labels": {"service_type": "Tipo de vidro", "glass_type": "Tipo do vidro", "dimensions": "Medidas"},
    },
    "security_cameras": {
        "bot": {
            "greeting_message": "Olá! 📷 Bem-vindo(a) ao serviço de *Câmeras de Segurança*! O que precisa?",
            "tone": "técnico",
            "fallback_message": "Não entendi. Informe o número ou *menu*.",
            "confirm_message": "Perfeito! Veja o orçamento:",
        },
        "services": ["instalacao_cameras", "manutencao_cameras", "ampliacao_cameras", "configuracao_remota", "troca_dvr_nvr", "visita_tecnica"],
        "pricing_defaults": {"minimum_order_value": 200.0, "visit_fee": 100.0},
        "onboarding_defaults": {
            "bot_name": "Câmeras Bot", "quote_prefix": "CAM", "currency": "BRL",
            "timezone": "America/Sao_Paulo", "extra_settings": {},
        },
        "labels": {"service_type": "Tipo de serviço", "camera_count": "Quantidade de câmeras", "recording_type": "Tipo de gravação"},
    },
}


def build_config_for_domain(key: str, domain_label: str) -> dict[str, Any]:
    """Constrói o config_json padrão para um domínio builtin."""
    return _DOMAIN_CONFIGS.get(key, {
        "bot": {
            "greeting_message": f"Olá! Bem-vindo(a) ao serviço de {domain_label}!",
            "tone": "amigável",
            "fallback_message": "Não entendi. Pode repetir ou digitar *menu*?",
            "confirm_message": "Ótimo! Confira o resumo:",
        },
        "services": [],
        "pricing_defaults": {"minimum_order_value": 100.0, "visit_fee": 0.0},
        "onboarding_defaults": {
            "bot_name": "Assistente", "quote_prefix": "SVC", "currency": "BRL",
            "timezone": "America/Sao_Paulo", "extra_settings": {},
        },
        "labels": {},
    })


class DomainDefinitionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DomainDefinitionsRepository(db)

    def sync_builtin_domains(self) -> dict[str, int]:
        """
        Sincroniza os domínios builtin do código para o banco.
        Cria registros faltantes; nunca apaga ou sobrescreve config editada.
        Retorna contadores de criados e pulados.
        """
        from app.domains.registry import DOMAIN_REGISTRY

        created = 0
        skipped = 0

        for key, domain in DOMAIN_REGISTRY.items():
            existing = self.repo.get_by_key(key)
            if existing:
                skipped += 1
                continue

            meta = _DOMAIN_META.get(key, {})
            config = build_config_for_domain(key, domain.label)

            self.repo.create(
                key=key,
                display_name=domain.label,
                description=meta.get("description"),
                icon=meta.get("icon"),
                is_active=True,
                is_builtin=True,
                config_json=config,
            )
            created += 1
            logger.info("DomainDefinition criado: %s", key)

        self.db.commit()
        logger.info("Sync domínios: %d criados, %d já existentes", created, skipped)
        return {"created": created, "skipped": skipped}

    def list_all(self, *, active_only: bool = False) -> list[DomainDefinition]:
        return self.repo.list_all(active_only=active_only)

    def get_by_key(self, key: str) -> DomainDefinition | None:
        return self.repo.get_by_key(key)

    def update(self, key: str, **fields) -> DomainDefinition:
        obj = self.repo.get_by_key(key)
        if not obj:
            raise ValueError(f"Domínio '{key}' não encontrado.")
        return self.repo.update(obj, **fields)

    def get_onboarding_config(self, domain_key: str) -> dict[str, Any]:
        """
        Retorna os defaults de onboarding configurados para o domínio.
        Prioriza config_json do banco; fallback para _DOMAIN_CONFIGS estático.
        """
        obj = self.repo.get_by_key(domain_key)
        if obj and obj.config_json:
            return obj.config_json.get("onboarding_defaults", {})
        return _DOMAIN_CONFIGS.get(domain_key, {}).get("onboarding_defaults", {})
