from fastapi import APIRouter

router = APIRouter(prefix="/panel", tags=["Panel"])


@router.get("/health")
def panel_health():
    return {"ok": True, "scope": "panel"}