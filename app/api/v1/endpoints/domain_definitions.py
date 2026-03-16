"""
Endpoints de administração para DomainDefinition.

Todos protegidos por require_master_admin.

Routes:
  GET  /admin/domains            — lista todos
  GET  /admin/domains/{key}      — detalhe de um
  PUT  /admin/domains/{key}      — edita (display_name, description, icon, is_active, config_json)
  POST /admin/domains/sync       — re-sincroniza domínios builtin do código
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import require_master_admin
from app.db.connection import get_db
from app.db.models import User
from app.schemas.domain_definitions import (
    DomainDefinitionListItem,
    DomainDefinitionResponse,
    DomainDefinitionUpdate,
    DomainSyncResult,
)
from app.services.domain_definition_service import DomainDefinitionService

router = APIRouter(prefix="/admin/domains", tags=["Admin — Domínios"])


@router.get("", response_model=list[DomainDefinitionListItem])
def list_domains(
    db: Session = Depends(get_db),
    _: User = Depends(require_master_admin),
):
    """Lista todos os domínios cadastrados no banco."""
    svc = DomainDefinitionService(db)
    return svc.list_all()


@router.post("/sync", response_model=DomainSyncResult)
def sync_builtin_domains(
    db: Session = Depends(get_db),
    _: User = Depends(require_master_admin),
):
    """
    Re-sincroniza os domínios builtin do código para o banco.
    Cria registros faltantes; não sobrescreve configurações já editadas.
    """
    svc = DomainDefinitionService(db)
    result = svc.sync_builtin_domains()
    domains = svc.list_all()
    return DomainSyncResult(
        synced=len(domains),
        created=result["created"],
        skipped=result["skipped"],
        keys=[d.key for d in domains],
    )


@router.get("/{key}", response_model=DomainDefinitionResponse)
def get_domain(
    key: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_master_admin),
):
    """Retorna o detalhe completo de um domínio pelo key."""
    svc = DomainDefinitionService(db)
    obj = svc.get_by_key(key)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Domínio '{key}' não encontrado.")
    return obj


@router.put("/{key}", response_model=DomainDefinitionResponse)
def update_domain(
    key: str,
    payload: DomainDefinitionUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_master_admin),
):
    """Atualiza dados editáveis de um domínio."""
    svc = DomainDefinitionService(db)
    obj = svc.get_by_key(key)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Domínio '{key}' não encontrado.")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return obj

    updated = svc.update(key, **update_data)
    db.commit()
    return updated
