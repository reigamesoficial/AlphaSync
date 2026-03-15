from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user, require_company_admin_or_master
from app.core.tenancy import get_tenant_company_id
from app.db.connection import get_db
from app.db.models import User
from app.schemas.company import CompanySettingsResponse, CompanySettingsUpdate
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/company", tags=["Company"])


@router.get("/settings", response_model=CompanySettingsResponse)
def get_company_settings(
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = SettingsService(db)
    return service.get_company_settings(
        tenant_company_id=tenant_company_id,
        current_user=current_user,
    )


@router.patch("/settings", response_model=CompanySettingsResponse)
def update_company_settings(
    payload: CompanySettingsUpdate,
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(require_company_admin_or_master),
    db: Session = Depends(get_db),
):
    service = SettingsService(db)
    return service.upsert_company_settings(
        tenant_company_id=tenant_company_id,
        current_user=current_user,
        payload=payload,
    )
