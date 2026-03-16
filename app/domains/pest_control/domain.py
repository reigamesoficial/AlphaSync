from __future__ import annotations

from importlib import import_module

from app.domains.base import BaseDomain, DomainCapabilities


def _safe_import(module_path: str):
    try:
        return import_module(module_path)
    except ModuleNotFoundError:
        return None


class PestControlDomain(BaseDomain):
    key = "pest_control"
    label = "Controle de Pragas"
    capabilities = DomainCapabilities(
        has_chatbot_flow=True,
        has_pricing=True,
        has_job_rules=False,
        has_pdf_builder=False,
        has_scheduling=True,
    )

    def get_chatbot_flow(self):
        return _safe_import("app.domains.pest_control.chatbot_flow")

    def get_pricing_service(self):
        return _safe_import("app.domains.pest_control.pricing_rules")

    def get_default_settings(self) -> dict:
        return {
            "domain_meta": {
                "key": self.key,
                "label": self.label,
            },
            "catalog": {
                "services": [
                    "baratas",
                    "formigas",
                    "cupins",
                    "roedores",
                    "mosquitos",
                    "aranhas",
                    "escorpioes",
                ]
            },
            "bot": {
                "enabled": True,
                "ask_pest_type": True,
                "ask_property_type": True,
                "ask_property_size": True,
                "ask_address_details": True,
                "ask_urgency": True,
            },
            "fields": {
                "required": [
                    "pest_type",
                    "property_type",
                    "address",
                ],
                "optional": [
                    "property_size",
                    "urgency",
                ],
            },
            "options": {
                "property_types": ["casa", "apartamento", "comercio", "industria"],
                "urgency_levels": ["normal", "urgente"],
            },
            "quote_defaults": {
                "validity_days": 5,
            },
            "scheduling": {
                "default_duration_minutes": 120,
                "allow_weekend_booking": True,
            },
        }


domain = PestControlDomain()