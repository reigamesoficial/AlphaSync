from fastapi import APIRouter, Depends

from app.core.security import require_master_admin

router = APIRouter(prefix="/admin/master", tags=["Admin Master"])


@router.get("/health")
def admin_master_health(_=Depends(require_master_admin)):
    return {"ok": True, "scope": "master_admin"}