from __future__ import annotations

from importlib import import_module

from app.domains.base import BaseDomain, DomainCapabilities


def _safe_import(module_path: str):
    try:
        return import_module(module_path)
    except ModuleNotFoundError:
        return None


class CleaningDomain(BaseDomain):
    key = "cleaning"
    label = "Limpeza"
    capabilities = DomainCapabilities(
        has_chatbot_flow=True,
        has_pricing=True,
        has_job_rules=False,
        has_pdf_builder=False,
        has_scheduling=True,
    )

    def get_chatbot_flow(self):
        return _safe_import("app.domains.cleaning.chatbot_flow")

    def get_pricing_service(self):
        return _safe_import("app.domains.cleaning.pricing_rules")

    def get_default_settings(self) -> dict:
        return {
            "domain_meta": {
                "key": self.key,
                "label": self.label,
            },
            "catalog": {
                "services": [
                    "limpeza_residencial",
                    "limpeza_comercial",
                    "limpeza_pos_obra",
                    "limpeza_pesada",
                    "limpeza_fina",
                ]
            },
            "bot": {
                "enabled": True,
                "ask_service_type": True,
                "ask_property_type": True,
                "ask_property_size": True,
                "ask_rooms_count": True,
                "ask_address_details": True,
                "ask_preferred_date": True,
                "ask_notes": True,
            },
            "fields": {
                "required": [
                    "service_type",
                    "property_type",
                    "property_size",
                    "address",
                ],
                "optional": [
                    "rooms_count",
                    "notes",
                ],
            },
            "options": {
                "property_types": [
                    "casa",
                    "apartamento",
                    "comercial",
                    "escritorio",
                ],
                "property_sizes": [
                    "ate_50m2",
                    "51_100m2",
                    "101_200m2",
                    "200m2_ou_mais",
                ],
            },
            "pricing_rules": {
                "visit_fee": 0.0,
                "minimum_order_value": 120.0,
            },
            "quote_defaults": {
                "validity_days": 7,
            },
            "scheduling": {
                "default_duration_minutes": 180,
                "allow_weekend_booking": True,
            },
        }


domain = CleaningDomain()