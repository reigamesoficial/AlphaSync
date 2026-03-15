from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from app.db.models import Company, ServiceDomain
from app.domains.base import BaseDomain
from app.domains.registry import DOMAIN_REGISTRY


class DomainEngine:
    """
    Resolve e entrega o domínio correto para cada empresa.

    Uso esperado:
        domain = domain_engine.resolve(company.service_domain)

    ou:

        domain = domain_engine.resolve_for_company(company)
    """

    def __init__(self, registry: dict[str, BaseDomain] | None = None) -> None:
        self.registry = registry or DOMAIN_REGISTRY

    # ============================================================
    # RESOLUTION
    # ============================================================

    def normalize_key(self, domain_key: str | ServiceDomain) -> str:
        if isinstance(domain_key, ServiceDomain):
            return domain_key.value

        normalized = str(domain_key).strip()

        # aceita "PROTECTION_NETWORK"
        if normalized in ServiceDomain.__members__:
            return ServiceDomain[normalized].value

        # aceita "protection_network"
        lowered = normalized.lower()
        for member in ServiceDomain:
            if member.value == lowered:
                return member.value

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Domínio de serviço inválido: '{domain_key}'.",
        )

    def resolve(self, domain_key: str | ServiceDomain) -> BaseDomain:
        normalized_key = self.normalize_key(domain_key)
        domain = self.registry.get(normalized_key)

        if domain is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Domínio '{normalized_key}' não está registrado no sistema.",
            )

        return domain

    def resolve_for_company(self, company: Company) -> BaseDomain:
        if not company.service_domain:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A empresa não possui service_domain configurado.",
            )

        return self.resolve(company.service_domain)

    # ============================================================
    # SETTINGS
    # ============================================================

    def get_default_settings(self, domain_key: str | ServiceDomain) -> dict[str, Any]:
        domain = self.resolve(domain_key)
        return domain.get_default_settings()

    def get_default_settings_for_company(self, company: Company) -> dict[str, Any]:
        domain = self.resolve_for_company(company)
        return domain.get_default_settings()

    # ============================================================
    # COMPONENTES
    # ============================================================

    def get_chatbot_flow(self, domain_key: str | ServiceDomain) -> Any:
        domain = self.resolve(domain_key)
        return domain.ensure_component(domain.get_chatbot_flow(), "chatbot_flow")

    def get_chatbot_flow_for_company(self, company: Company) -> Any:
        domain = self.resolve_for_company(company)
        return domain.ensure_component(domain.get_chatbot_flow(), "chatbot_flow")

    def get_pricing_service(self, domain_key: str | ServiceDomain) -> Any:
        domain = self.resolve(domain_key)
        return domain.ensure_component(domain.get_pricing_service(), "pricing_service")

    def get_pricing_service_for_company(self, company: Company) -> Any:
        domain = self.resolve_for_company(company)
        return domain.ensure_component(domain.get_pricing_service(), "pricing_service")

    def get_job_rules_service(self, domain_key: str | ServiceDomain) -> Any:
        domain = self.resolve(domain_key)
        return domain.ensure_component(domain.get_job_rules_service(), "job_rules_service")

    def get_job_rules_service_for_company(self, company: Company) -> Any:
        domain = self.resolve_for_company(company)
        return domain.ensure_component(domain.get_job_rules_service(), "job_rules_service")

    def get_pdf_builder(self, domain_key: str | ServiceDomain) -> Any:
        domain = self.resolve(domain_key)
        return domain.ensure_component(domain.get_pdf_builder(), "pdf_builder")

    def get_pdf_builder_for_company(self, company: Company) -> Any:
        domain = self.resolve_for_company(company)
        return domain.ensure_component(domain.get_pdf_builder(), "pdf_builder")

    def get_scheduling_service(self, domain_key: str | ServiceDomain) -> Any:
        domain = self.resolve(domain_key)
        return domain.ensure_component(domain.get_scheduling_service(), "scheduling_service")

    def get_scheduling_service_for_company(self, company: Company) -> Any:
        domain = self.resolve_for_company(company)
        return domain.ensure_component(domain.get_scheduling_service(), "scheduling_service")

    # ============================================================
    # INTROSPECTION
    # ============================================================

    def list_domains(self) -> list[dict[str, Any]]:
        return [domain.describe() for domain in self.registry.values()]

    def is_registered(self, domain_key: str | ServiceDomain) -> bool:
        try:
            normalized_key = self.normalize_key(domain_key)
        except HTTPException:
            return False
        return normalized_key in self.registry


domain_engine = DomainEngine()