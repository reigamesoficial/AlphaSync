from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.connection import get_db
from app.db.models import User, UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/auth/login"
)


class TokenType:
    ACCESS = "access"
    REFRESH = "refresh"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def _build_token_payload(
    *,
    user_id: int,
    company_id: int | None,
    role: UserRole,
    token_type: str,
    expires_delta: timedelta,
) -> tuple[dict, datetime]:
    expires_at = utc_now() + expires_delta

    payload = {
        "sub": str(user_id),
        "company_id": company_id,
        "role": role.value,
        "type": token_type,
        "exp": expires_at,
    }
    return payload, expires_at


def create_access_token(
    *,
    user_id: int,
    company_id: int | None,
    role: UserRole,
) -> tuple[str, datetime]:
    payload, expires_at = _build_token_payload(
        user_id=user_id,
        company_id=company_id,
        role=role,
        token_type=TokenType.ACCESS,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_at


def create_refresh_token(
    *,
    user_id: int,
    company_id: int | None,
    role: UserRole,
) -> tuple[str, datetime]:
    payload, expires_at = _build_token_payload(
        user_id=user_id,
        company_id=company_id,
        role=role,
        token_type=TokenType.REFRESH,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_at


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_token_payload(token: str = Depends(oauth2_scheme)) -> dict:
    return decode_token(token)


def _coerce_user_role(role_value: str | None) -> UserRole:
    if not role_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sem role.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return UserRole(role_value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Role inválida no token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def _coerce_user_id(sub_value: str | None) -> int:
    if not sub_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sem usuário.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return int(sub_value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identificador de usuário inválido no token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def _extract_token_type(payload: dict) -> str:
    token_type = payload.get("type")
    if token_type not in {TokenType.ACCESS, TokenType.REFRESH}:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tipo de token inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_type


def _extract_company_id(payload: dict) -> int | None:
    company_id = payload.get("company_id")
    if company_id is None:
        return None
    try:
        return int(company_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Company ID inválido no token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_user(
    payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db),
) -> User:
    token_type = _extract_token_type(payload)
    if token_type != TokenType.ACCESS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="É necessário um access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = _coerce_user_id(payload.get("sub"))
    user = db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo.",
        )
    return current_user


def get_current_role(
    payload: dict = Depends(get_token_payload),
) -> UserRole:
    return _coerce_user_role(payload.get("role"))


def get_current_company_id(
    payload: dict = Depends(get_token_payload),
) -> int | None:
    token_type = _extract_token_type(payload)
    if token_type != TokenType.ACCESS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="É necessário um access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _extract_company_id(payload)


def require_roles(*allowed_roles: UserRole) -> Callable:
    allowed_set = set(allowed_roles)

    def dependency(
        current_user: User = Depends(get_current_active_user),
        payload: dict = Depends(get_token_payload),
    ) -> User:
        token_role = _coerce_user_role(payload.get("role"))

        if current_user.role != token_role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inconsistência entre token e usuário.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if token_role not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para acessar este recurso.",
            )

        return current_user

    return dependency


def require_master_admin(
    current_user: User = Depends(require_roles(UserRole.MASTER_ADMIN)),
) -> User:
    return current_user


def require_company_admin_or_master(
    current_user: User = Depends(
        require_roles(UserRole.MASTER_ADMIN, UserRole.COMPANY_ADMIN)
    ),
) -> User:
    return current_user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    if not user.is_active:
        return None

    return user


def build_login_response(user: User) -> dict:
    access_token, access_expires_at = create_access_token(
        user_id=user.id,
        company_id=user.company_id,
        role=user.role,
    )
    refresh_token, _ = create_refresh_token(
        user_id=user.id,
        company_id=user.company_id,
        role=user.role,
    )

    return {
        "token": access_token,
        "refresh_token": refresh_token,
        "expires_at": access_expires_at,
        "user": {
            "id": user.id,
            "company_id": user.company_id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
        },
    }


def build_refresh_response_from_token(refresh_token: str) -> dict:
    payload = decode_token(refresh_token)

    token_type = _extract_token_type(payload)
    if token_type != TokenType.REFRESH:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = _coerce_user_id(payload.get("sub"))
    company_id = _extract_company_id(payload)
    role = _coerce_user_role(payload.get("role"))

    token, expires_at = create_access_token(
        user_id=user_id,
        company_id=company_id,
        role=role,
    )

    return {
        "token": token,
        "expires_at": expires_at,
    }