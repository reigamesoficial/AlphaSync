from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.connection import get_db
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    return service.login(payload)


@router.post("/refresh", response_model=RefreshResponse)
def refresh(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    return service.refresh(payload.token)