from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    authenticate_user,
    build_login_response,
    build_refresh_response_from_token,
)
from app.schemas.auth import LoginRequest, LoginResponse, RefreshResponse


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def login(self, payload: LoginRequest) -> LoginResponse:
        user = authenticate_user(
            self.db,
            email=payload.email,
            password=payload.password,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha inválidos.",
            )

        return LoginResponse(**build_login_response(user))

    def refresh(self, refresh_token: str) -> RefreshResponse:
        data = build_refresh_response_from_token(refresh_token)
        return RefreshResponse(**data)