from __future__ import annotations

from copy import deepcopy
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.security import (
    get_current_active_user,
    hash_password,
    require_company_admin_or_master,
    require_roles,
)
from app.core.tenancy import get_tenant_company_id
from app.db.connection import get_db
from app.db.models import User, UserRole
from app.schemas.company import CompanySettingsResponse, CompanySettingsUpdate
from app.schemas.measures import PNSettingsResponse, PNSettingsUpdate
from app.schemas.users import UserResponse
from app.services.settings_service import SettingsService
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(prefix="/company", tags=["Company"])


# ── schemas inline para gestão de usuários da empresa ──────────────────────

_ALLOWED_COMPANY_ROLES: set[UserRole] = {
    UserRole.COMPANY_ADMIN,
    UserRole.SELLER,
    UserRole.INSTALLER,
    UserRole.VIEWER,
}


class CompanyUserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    role: UserRole = UserRole.SELLER
    is_active: bool = True
    whatsapp_id: str | None = Field(default=None, max_length=40)


class CompanyUserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    email: EmailStr | None = None
    role: UserRole | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)
    whatsapp_id: str | None = Field(default=None, max_length=40)


class CompanyUserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    per_page: int

    model_config = {"from_attributes": True}


def _require_company_only(
    current_user: User = Depends(require_roles(UserRole.COMPANY_ADMIN)),
) -> User:
    return current_user


def _validate_role_for_company(role: UserRole) -> None:
    if role == UserRole.MASTER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não é permitido criar ou promover usuários para master_admin.",
        )
    if role not in _ALLOWED_COMPANY_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Role '{role}' inválida para empresa.",
        )


# ── settings endpoints ──────────────────────────────────────────────────────


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


def _extract_pn_settings(effective: dict[str, Any]) -> PNSettingsResponse:
    pricing = effective.get("pricing_rules") or {}
    return PNSettingsResponse(
        show_measures_to_customer=bool(effective.get("show_measures_to_customer", True)),
        default_price_per_m2=float(pricing.get("default_price_per_m2", 45.0)),
        minimum_order_value=float(pricing.get("minimum_order_value", 150.0)),
        visit_fee=float(pricing.get("visit_fee", 0.0)),
        available_colors=list(effective.get("network_colors") or ["branca", "preta", "areia", "cinza"]),
        available_mesh_types=list(effective.get("mesh_types") or ["3x3", "5x5"]),
        mesh_prices=dict(effective.get("mesh_prices") or {}),
    )


@router.get("/settings/protection-network", response_model=PNSettingsResponse)
def get_pn_settings(
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PNSettingsResponse:
    service = SettingsService(db)
    effective = service.get_effective_extra_settings(
        tenant_company_id=tenant_company_id,
        current_user=current_user,
    )
    return _extract_pn_settings(effective)


@router.patch("/settings/protection-network", response_model=PNSettingsResponse)
def update_pn_settings(
    payload: PNSettingsUpdate,
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(require_company_admin_or_master),
    db: Session = Depends(get_db),
) -> PNSettingsResponse:
    service = SettingsService(db)

    data = payload.model_dump(exclude_unset=True)
    extra_patch: dict[str, Any] = {}

    if "show_measures_to_customer" in data:
        extra_patch["show_measures_to_customer"] = data["show_measures_to_customer"]
    if "available_colors" in data:
        extra_patch["network_colors"] = data["available_colors"]
    if "available_mesh_types" in data:
        extra_patch["mesh_types"] = data["available_mesh_types"]
    if "mesh_prices" in data:
        extra_patch["mesh_prices"] = data["mesh_prices"]

    pricing_patch: dict[str, Any] = {}
    for key in ("default_price_per_m2", "minimum_order_value", "visit_fee"):
        if key in data:
            pricing_patch[key] = data[key]
    if pricing_patch:
        extra_patch["pricing_rules"] = pricing_patch

    settings_update = CompanySettingsUpdate(extra_settings=extra_patch)
    service.upsert_company_settings(
        tenant_company_id=tenant_company_id,
        current_user=current_user,
        payload=settings_update,
    )

    effective = service.get_effective_extra_settings(
        tenant_company_id=tenant_company_id,
        current_user=current_user,
    )
    return _extract_pn_settings(effective)


# ── gestão de usuários da empresa (company_admin only) ─────────────────────


@router.get("/users", response_model=CompanyUserListResponse)
def list_company_users(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    role: UserRole | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    current_user: User = Depends(_require_company_only),
    tenant_company_id: int = Depends(get_tenant_company_id),
    db: Session = Depends(get_db),
) -> CompanyUserListResponse:
    q = select(User).where(User.company_id == tenant_company_id)

    if role is not None:
        q = q.where(User.role == role)
    if is_active is not None:
        q = q.where(User.is_active == is_active)
    if search:
        pattern = f"%{search}%"
        q = q.where(or_(User.name.ilike(pattern), User.email.ilike(pattern)))

    total: int = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    users = db.scalars(q.order_by(User.name).offset((page - 1) * per_page).limit(per_page)).all()

    return CompanyUserListResponse(
        items=list(users),
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/users/{user_id}", response_model=UserResponse)
def get_company_user(
    user_id: int,
    current_user: User = Depends(_require_company_only),
    tenant_company_id: int = Depends(get_tenant_company_id),
    db: Session = Depends(get_db),
) -> User:
    u = db.get(User, user_id)
    if not u or u.company_id != tenant_company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    return u


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_company_user(
    payload: CompanyUserCreate,
    current_user: User = Depends(_require_company_only),
    tenant_company_id: int = Depends(get_tenant_company_id),
    db: Session = Depends(get_db),
) -> User:
    _validate_role_for_company(payload.role)

    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já está em uso.",
        )

    new_user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        company_id=tenant_company_id,
        is_active=payload.is_active,
        whatsapp_id=payload.whatsapp_id,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_company_user(
    user_id: int,
    payload: CompanyUserUpdate,
    current_user: User = Depends(_require_company_only),
    tenant_company_id: int = Depends(get_tenant_company_id),
    db: Session = Depends(get_db),
) -> User:
    u = db.get(User, user_id)
    if not u or u.company_id != tenant_company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    updates = payload.model_dump(exclude_unset=True)

    if "role" in updates:
        _validate_role_for_company(updates["role"])

    if "email" in updates and updates["email"] != u.email:
        clash = db.scalar(select(User).where(User.email == updates["email"], User.id != u.id))
        if clash:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail já está em uso.")

    if "password" in updates:
        u.password_hash = hash_password(updates.pop("password"))

    for k, v in updates.items():
        setattr(u, k, v)

    db.commit()
    db.refresh(u)
    return u
