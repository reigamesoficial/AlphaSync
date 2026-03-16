from __future__ import annotations

from importlib import import_module

from app.domains.base import BaseDomain, DomainCapabilities


def _safe_import(module_path: str):
    try:
        return import_module(module_path)
    except ModuleNotFoundError:
        return None


class HVACDomain(BaseDomain):
    key = "hvac"
    label = "Ar-condicionado"
    capabilities = DomainCapabilities(
        has_chatbot_flow=True,
        has_pricing=True,
        has_job_rules=False,
        has_pdf_builder=False,
        has_scheduling=True,
    )

    def get_chatbot_flow(self):
        return _safe_import("app.domains.hvac.chatbot_flow")

    def get_pricing_service(self):
        return _safe_import("app.domains.hvac.pricing_rules")

    def get_default_settings(self) -> dict:
        return {
            "domain_meta": {
                "key": self.key,
                "label": self.label,
            },
            "catalog": {
                "services": [
                    "instalacao",
                    "manutencao",
                    "higienizacao",
                    "recarga_gas",
                    "visita_tecnica",
                ]
            },
            "bot": {
                "enabled": True,
                "ask_service_type": True,
                "ask_equipment_type": True,
                "ask_btus": True,
                "ask_installation_height": True,
                "ask_address_details": True,
                "ask_photos": True,
            },
            "fields": {
                "required": [
                    "service_type",
                    "equipment_type",
                    "address",
                ],
                "optional": [
                    "btus",
                    "installation_height",
                    "photos",
                ],
            },
            "options": {
                "equipment_types": [
                    "split",
                    "janela",
                    "piso_teto",
                    "cassete",
                ],
                "btus": [
                    "9000",
                    "12000",
                    "18000",
                    "24000",
                    "30000+",
                ],
            },
            "pricing_rules": {
                "visit_fee": 90.0,
                "minimum_order_value": 180.0,
            },
            "quote_defaults": {
                "validity_days": 7,
            },
            "scheduling": {
                "default_duration_minutes": 120,
                "allow_weekend_booking": True,
            },
        }


domain = HVACDomain()