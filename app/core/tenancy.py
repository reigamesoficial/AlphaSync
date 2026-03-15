from __future__ import annotations

from typing import Any, Type

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Query

from app.core.security import get_current_active_user, get_current_company_id
from app.db.models import Company, User, UserRole


# ============================================================
# TENANT ID EXTRACTION
# ============================================================


def get_tenant_company_id(
    company_id: int | None = Depends(get_current_company_id),
) -> int:
    """
    Obtém o company_id do token JWT.
    Usado para todas as operações dentro de um tenant.
    """
    if company_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário não pertence a nenhuma empresa.",
        )

    return company_id


# ============================================================
# USER VALIDATION
# ============================================================


def ensure_user_belongs_to_tenant(
    current_user: User = Depends(get_current_active_user),
    tenant_company_id: int = Depends(get_tenant_company_id),
) -> User:
    """
    Garante que o usuário pertence ao tenant correto.
    Master Admin pode acessar qualquer empresa.
    """
    if current_user.role == UserRole.MASTER_ADMIN:
        return current_user

    if current_user.company_id != tenant_company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso cruzado entre empresas não permitido.",
        )

    return current_user


# ============================================================
# RESOURCE VALIDATION
# ============================================================


def assert_company_match(
    resource_company_id: int | None,
    tenant_company_id: int,
    current_user: User,
) -> None:
    """
    Garante que o recurso pertence ao tenant.
    """
    if current_user.role == UserRole.MASTER_ADMIN:
        return

    if resource_company_id is None or resource_company_id != tenant_company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este recurso não pertence à empresa do usuário.",
        )


def assert_same_tenant(resource: Any, tenant_company_id: int) -> None:
    """
    Valida se um objeto possui company_id correto.
    """
    if not hasattr(resource, "company_id"):
        raise ValueError("O recurso informado não possui company_id.")

    if resource.company_id != tenant_company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recurso fora do tenant do usuário.",
        )


# ============================================================
# QUERY HELPERS
# ============================================================


def apply_tenant_scope(
    query: Query,
    model: Type[Any],
    company_id: int,
) -> Query:
    """
    Aplica filtro automático por tenant nas queries.
    """
    if not hasattr(model, "company_id"):
        raise ValueError(f"Model {model.__name__} não possui campo company_id.")

    return query.filter(model.company_id == company_id)


def tenant_filter(
    model: Type[Any],
    company_id: int,
):
    """
    Retorna expressão SQL para filtro por tenant.
    """
    if not hasattr(model, "company_id"):
        raise ValueError(f"Model {model.__name__} não possui campo company_id.")

    return model.company_id == company_id


# ============================================================
# COMPANY RESOLUTION
# ============================================================


def get_tenant_company_or_404(
    current_user: User,
    company: Company | None,
    tenant_company_id: int,
) -> Company:
    """
    Valida se empresa existe e pertence ao tenant.
    """
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada.",
        )

    assert_company_match(company.id, tenant_company_id, current_user)

    return company


# ============================================================
# WEBHOOK TENANCY (WHATSAPP)
# ============================================================


def tenant_payload() -> dict:
    """
    Documentação interna de como resolvemos tenants.
    """
    return {
        "strategy": "jwt_company_id",
        "frontend_sends_company_id": False,
        "webhook_strategy": "resolve_by_whatsapp_phone_number_id",
    }