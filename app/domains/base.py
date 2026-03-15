from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DomainCapabilities:
    has_chatbot_flow: bool = True
    has_pricing: bool = False
    has_job_rules: bool = False
    has_pdf_builder: bool = False
    has_scheduling: bool = False


class BaseDomain(ABC):
    """
    Contrato base de qualquer domínio do AlphaSync.

    Cada nicho deve expor um objeto `domain` em:
        app/domains/<nicho>/domain.py

    Esse objeto deve herdar BaseDomain.
    """

    key: str
    label: str
    capabilities: DomainCapabilities = DomainCapabilities()

    def __init__(self) -> None:
        self._validate_identity()

    def _validate_identity(self) -> None:
        if not getattr(self, "key", None):
            raise ValueError(f"{self.__class__.__name__} precisa definir 'key'.")
        if not getattr(self, "label", None):
            raise ValueError(f"{self.__class__.__name__} precisa definir 'label'.")

    # ============================================================
    # COMPONENTES DO DOMÍNIO
    # ============================================================

    def get_chatbot_flow(self) -> Any | None:
        """
        Retorna a classe/objeto responsável pelo fluxo conversacional do nicho.
        """
        return None

    def get_pricing_service(self) -> Any | None:
        """
        Retorna a classe/objeto responsável pela precificação do nicho.
        """
        return None

    def get_job_rules_service(self) -> Any | None:
        """
        Retorna a classe/objeto responsável por regras específicas do nicho.
        """
        return None

    def get_pdf_builder(self) -> Any | None:
        """
        Retorna a classe/objeto responsável por geração de PDF do nicho.
        """
        return None

    def get_scheduling_service(self) -> Any | None:
        """
        Retorna a classe/objeto responsável por lógica extra de agenda do nicho.
        """
        return None

    # ============================================================
    # DEFAULT SETTINGS
    # ============================================================

    def get_default_settings(self) -> dict[str, Any]:
        """
        Configurações padrão do nicho para popular `company_settings.extra_settings`
        quando a empresa for criada pelo master admin.
        """
        return {}

    # ============================================================
    # HELPERS
    # ============================================================

    def describe(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "capabilities": {
                "has_chatbot_flow": self.capabilities.has_chatbot_flow,
                "has_pricing": self.capabilities.has_pricing,
                "has_job_rules": self.capabilities.has_job_rules,
                "has_pdf_builder": self.capabilities.has_pdf_builder,
                "has_scheduling": self.capabilities.has_scheduling,
            },
        }

    def ensure_component(self, component: Any | None, component_name: str) -> Any:
        if component is None:
            raise NotImplementedError(
                f"O domínio '{self.key}' não implementa o componente '{component_name}'."
            )
        return component