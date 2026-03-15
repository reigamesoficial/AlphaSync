from __future__ import annotations

from importlib import import_module

from app.domains.base import BaseDomain, DomainCapabilities


def _safe_import(module_path: str):
    try:
        return import_module(module_path)
    except ModuleNotFoundError:
        return None


class GlassInstallationDomain(BaseDomain):
    key = "glass_installation"
    label = "Vidraçaria"
    capabilities = DomainCapabilities(
        has_chatbot_flow=True,
        has_pricing=False,
        has_job_rules=False,
        has_pdf_builder=False,
        has_scheduling=True,
    )

    def get_chatbot_flow(self):
        return _safe_import("app.domains.glass_installation.chatbot_flow")

    def get_default_settings(self) -> dict:
        return {
            "domain_meta": {
                "key": self.key,
                "label": self.label,
            },
            "catalog": {
                "services": [
                    "box_banheiro",
                    "espelho",
                    "janela_vidro",
                    "porta_vidro",
                    "fechamento_sacada",
                    "guarda_corpo",
                ]
            },
            "bot": {
                "enabled": True,
                "ask_service_type": True,
                "ask_measurements": True,
                "ask_glass_type": True,
                "ask_finish_type": True,
                "ask_address_details": True,
                "ask_photos": True,
            },
            "fields": {
                "required": [
                    "service_type",
                    "measurements",
                    "address",
                ],
                "optional": [
                    "glass_type",
                    "finish_type",
                    "photos",
                ],
            },
            "options": {
                "glass_types": [
                    "temperado",
                    "laminado",
                    "comum",
                    "espelho",
                ],
                "finish_types": [
                    "preto",
                    "branco",
                    "inox",
                    "dourado",
                ],
            },
            "quote_defaults": {
                "validity_days": 10,
            },
            "scheduling": {
                "default_duration_minutes": 120,
                "allow_weekend_booking": False,
            },
        }


domain = GlassInstallationDomain()