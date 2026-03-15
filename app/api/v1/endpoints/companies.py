from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import (
    get_current_active_user,
    require_company_admin_or_master,
)
from app.core.tenancy import get_tenant_company_id
from app.db.connection import get_db
from app.db.models import User
from app.schemas.company import CompanyResponse, CompanySettingsResponse, CompanySettingsUpdate
from app.services.company_service import CompanyService
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get("/me", response_model=CompanyResponse)
def get_my_company(
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = CompanyService(db)
    return service.get_current_company(
        tenant_company_id=tenant_company_id,
        current_user=current_user,
    )


@router.get("/me/settings", response_model=CompanySettingsResponse)
def get_settings(
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = SettingsService(db)
    return service.get_company_settings(
        tenant_company_id=tenant_company_id,
        current_user=current_user,
    )


@router.put("/me/settings", response_model=CompanySettingsResponse)
def update_settings(
    payload: CompanySettingsUpdate,
    tenant_company_id: int = Depends(get_tenant_company_id),
    _: User = Depends(require_company_admin_or_master),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = SettingsService(db)
    return service.upsert_company_settings(
        tenant_company_id=tenant_company_id,
        current_user=current_user,
        payload=payload,
    )