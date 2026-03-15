from __future__ import annotations

from importlib import import_module

from app.domains.base import BaseDomain, DomainCapabilities


def _safe_import(module_path: str):
    try:
        return import_module(module_path)
    except ModuleNotFoundError:
        return None


class ElectricianDomain(BaseDomain):
    key = "electrician"
    label = "Eletricista"
    capabilities = DomainCapabilities(
        has_chatbot_flow=True,
        has_pricing=True,
        has_job_rules=False,
        has_pdf_builder=False,
        has_scheduling=True,
    )

    def get_chatbot_flow(self):
        return _safe_import("app.domains.electrician.chatbot_flow")

    def get_pricing_service(self):
        return _safe_import("app.domains.electrician.pricing")

    def get_default_settings(self) -> dict:
        return {
            "domain_meta": {
                "key": self.key,
                "label": self.label,
            },
            "catalog": {
                "services": [
                    "troca_tomada",
                    "troca_interruptor",
                    "troca_disjuntor",
                    "instalacao_luminaria",
                    "quadro_eletrico",
                    "manutencao_geral",
                    "visita_tecnica",
                ]
            },
            "bot": {
                "enabled": True,
                "ask_service_type": True,
                "ask_voltage": True,
                "ask_urgency": True,
                "ask_address_details": True,
                "ask_photos": True,
                "ask_notes": True,
            },
            "fields": {
                "required": [
                    "service_type",
                    "address",
                ],
                "optional": [
                    "voltage",
                    "urgency",
                    "photos",
                    "notes",
                ],
            },
            "options": {
                "voltages": ["110v", "127v", "220v", "nao_sei"],
                "urgency_levels": ["normal", "urgente", "emergencial"],
            },
            "pricing_rules": {
                "visit_fee": 80.0,
                "minimum_order_value": 150.0,
                "emergency_multiplier": 1.5,
            },
            "quote_defaults": {
                "validity_days": 7,
            },
            "scheduling": {
                "default_duration_minutes": 90,
                "allow_weekend_booking": True,
            },
        }


domain = ElectricianDomain()