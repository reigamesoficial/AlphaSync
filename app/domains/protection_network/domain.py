from __future__ import annotations

from importlib import import_module

from app.domains.base import BaseDomain, DomainCapabilities


def _safe_import(module_path: str):
    try:
        return import_module(module_path)
    except ModuleNotFoundError:
        return None


class ProtectionNetworkDomain(BaseDomain):
    key = "protection_network"
    label = "Redes de Proteção"
    capabilities = DomainCapabilities(
        has_chatbot_flow=True,
        has_pricing=True,
        has_job_rules=True,
        has_pdf_builder=False,
        has_scheduling=True,
    )

    def get_chatbot_flow(self):
        return _safe_import("app.domains.protection_network.chatbot_flow")

    def get_pricing_service(self):
        return _safe_import("app.domains.protection_network.pricing")

    def get_job_rules_service(self):
        return _safe_import("app.domains.protection_network.job_rules")

    def get_default_settings(self) -> dict:
        return {
            "domain_meta": {
                "key": self.key,
                "label": self.label,
            },
            "catalog": {
                "services": [
                    "janela",
                    "sacada",
                    "varanda",
                    "escada",
                    "quadra",
                    "cobertura",
                    "outro",
                ]
            },
            "network_colors": [
                "branca",
                "preta",
                "areia",
                "cinza",
            ],
            "mesh_types": [
                "3x3",
                "5x5",
            ],
            "default_mesh": "3x3",
            "bot": {
                "enabled": True,
                "ask_installation_type": True,
                "ask_measurements": True,
                "ask_color": True,
                "ask_mesh": True,
                "ask_address_details": True,
                "ask_photos": True,
            },
            "fields": {
                "required": [
                    "installation_type",
                    "measurements",
                    "address",
                ],
                "optional": [
                    "network_color",
                    "mesh_type",
                    "photos",
                ],
            },
            "pricing_rules": {
                "default_price_per_m2": 45.0,
                "minimum_order_value": 150.0,
                "visit_fee": 0.0,
            },
            "job_rules": {
                "allowed_regions": [],
                "special_addresses": [],
            },
            "quote_defaults": {
                "validity_days": 7,
            },
            "scheduling": {
                "default_duration_minutes": 120,
                "allow_weekend_booking": True,
            },
        }


domain = ProtectionNetworkDomain()