from fastapi import APIRouter

router = APIRouter(prefix="/bot", tags=["Bot"])


@router.get("/health")
def bot_health():
    return {"ok": True, "scope": "bot"}