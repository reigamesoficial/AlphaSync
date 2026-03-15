from __future__ import annotations

from importlib import import_module
from typing import Iterable

from app.db.models import ServiceDomain
from app.domains.base import BaseDomain


DOMAIN_MODULES: dict[str, str] = {
    ServiceDomain.PROTECTION_NETWORK.value: "app.domains.protection_network.domain",
    ServiceDomain.HVAC.value: "app.domains.hvac.domain",
    ServiceDomain.ELECTRICIAN.value: "app.domains.electrician.domain",
    ServiceDomain.PLUMBING.value: "app.domains.plumbing.domain",
    ServiceDomain.CLEANING.value: "app.domains.cleaning.domain",
    ServiceDomain.GLASS_INSTALLATION.value: "app.domains.glass_installation.domain",
    ServiceDomain.PEST_CONTROL.value: "app.domains.pest_control.domain",
    ServiceDomain.SECURITY_CAMERAS.value: "app.domains.security_cameras.domain",
}


def _load_domain(module_path: str) -> BaseDomain:
    module = import_module(module_path)

    if not hasattr(module, "domain"):
        raise RuntimeError(
            f"O módulo '{module_path}' precisa expor uma variável 'domain'."
        )

    domain = getattr(module, "domain")

    if not isinstance(domain, BaseDomain):
        raise RuntimeError(
            f"O objeto 'domain' em '{module_path}' precisa herdar BaseDomain."
        )

    return domain


def build_domain_registry() -> dict[str, BaseDomain]:
    registry: dict[str, BaseDomain] = {}

    for domain_key, module_path in DOMAIN_MODULES.items():
        domain = _load_domain(module_path)

        if domain.key != domain_key:
            raise RuntimeError(
                f"Inconsistência no domínio '{module_path}': "
                f"esperado key='{domain_key}', recebido key='{domain.key}'."
            )

        if domain.key in registry:
            raise RuntimeError(f"Domínio duplicado registrado: '{domain.key}'.")

        registry[domain.key] = domain

    return registry


DOMAIN_REGISTRY: dict[str, BaseDomain] = build_domain_registry()


def get_registered_domains() -> dict[str, BaseDomain]:
    return DOMAIN_REGISTRY.copy()


def get_registered_domain_keys() -> list[str]:
    return sorted(DOMAIN_REGISTRY.keys())


def iter_registered_domains() -> Iterable[BaseDomain]:
    return DOMAIN_REGISTRY.values()