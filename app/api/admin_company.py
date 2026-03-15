from fastapi import APIRouter, Depends

from app.core.security import require_company_admin_or_master

router = APIRouter(prefix="/admin/company", tags=["Admin Company"])


@router.get("/health")
def admin_company_health(_=Depends(require_company_admin_or_master)):
    return {"ok": True, "scope": "company_admin"}