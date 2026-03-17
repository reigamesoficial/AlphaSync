from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.security import hash_password, require_master_admin
from app.db.connection import get_db
from app.db.models import (
    Appointment,
    Company,
    CompanySettings,
    Conversation,
    PlatformSettings,
    Quote,
    User,
    UserRole,
)
from app.repositories.companies import CompaniesRepository
from app.repositories.company_settings import CompanySettingsRepository
from app.repositories.users import UsersRepository
from app.schemas.common import PaginatedResponse
from app.schemas.company import (
    AdminUserSummary,
    BootstrapAdminPayload,
    CompanyCreateFull,
    CompanyDetailResponse,
    CompanyListItem,
    CompanyResponse,
    CompanySettingsResponse,
    CompanyUpdate,
)
from app.schemas.platform_settings import PlatformSettingsResponse, PlatformSettingsUpdate
from app.schemas.users import AdminUserResponse, AdminUserUpdate, UserCreate, UserResponse
from app.services.onboarding_service import OnboardingService

router = APIRouter(prefix="/admin", tags=["Admin (Master)"])


# ============================================================
# HELPERS — companies
# ============================================================

def _count_users(db: Session, company_ids: list[int]) -> dict[int, int]:
    if not company_ids:
        return {}
    rows = db.execute(
        select(User.company_id, func.count(User.id))
        .where(User.company_id.in_(company_ids))
        .group_by(User.company_id)
    ).all()
    return {cid: cnt for cid, cnt in rows}


def _has_settings_set(db: Session, company_ids: list[int]) -> set[int]:
    if not company_ids:
        return set()
    return set(
        db.scalars(
            select(CompanySettings.company_id).where(
                CompanySettings.company_id.in_(company_ids)
            )
        ).all()
    )


def _has_admin_set(db: Session, company_ids: list[int]) -> set[int]:
    if not company_ids:
        return set()
    return set(
        db.scalars(
            select(User.company_id)
            .where(
                User.company_id.in_(company_ids),
                User.role == UserRole.COMPANY_ADMIN,
            )
            .distinct()
        ).all()
    )


def _build_list_item(
    c: Company,
    user_count: int,
    has_settings: bool,
    has_admin: bool,
) -> CompanyListItem:
    base = CompanyResponse.model_validate(c)
    return CompanyListItem.model_validate({
        **base.model_dump(),
        "user_count": user_count,
        "has_settings": has_settings,
        "has_admin": has_admin,
    })


def _build_detail(
    db: Session,
    c: Company,
    user_count: int,
    has_settings: bool,
    has_admin: bool,
) -> CompanyDetailResponse:
    settings_repo = CompanySettingsRepository(db)
    raw_settings = settings_repo.get_by_company_id(c.id)
    settings_resp = CompanySettingsResponse.model_validate(raw_settings) if raw_settings else None

    admin_users_raw = list(
        db.scalars(
            select(User)
            .where(User.company_id == c.id, User.role == UserRole.COMPANY_ADMIN)
            .order_by(User.name)
        ).all()
    )
    admin_users = [AdminUserSummary.model_validate(u) for u in admin_users_raw]

    base = CompanyResponse.model_validate(c)
    return CompanyDetailResponse.model_validate({
        **base.model_dump(),
        "user_count": user_count,
        "has_settings": has_settings,
        "has_admin": has_admin,
        "settings": settings_resp.model_dump() if settings_resp else None,
        "admin_users": [u.model_dump() for u in admin_users],
    })


# ============================================================
# HELPERS — users
# ============================================================

def _fetch_admin_user(db: Session, user_id: int) -> AdminUserResponse:
    row = db.execute(
        select(User, Company.name.label("cn"), Company.slug.label("cs"))
        .outerjoin(Company, User.company_id == Company.id)
        .where(User.id == user_id)
    ).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    u, cn, cs = row
    return AdminUserResponse.model_validate({
        **UserResponse.model_validate(u).model_dump(),
        "company_name": cn,
        "company_slug": cs,
    })


# ============================================================
# PLATFORM SETTINGS
# ============================================================

@router.get("/settings", response_model=PlatformSettingsResponse)
def get_platform_settings(
    _: User = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> PlatformSettingsResponse:
    s = db.scalar(select(PlatformSettings))
    if not s:
        s = PlatformSettings(id=1)
        db.add(s)
        db.commit()
        db.refresh(s)
    return PlatformSettingsResponse.model_validate(s)


@router.patch("/settings", response_model=PlatformSettingsResponse)
def update_platform_settings(
    payload: PlatformSettingsUpdate,
    _: User = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> PlatformSettingsResponse:
    s = db.scalar(select(PlatformSettings))
    if not s:
        s = PlatformSettings(id=1)
        db.add(s)
        db.flush()

    updates = payload.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(s, k, v)

    db.commit()
    db.refresh(s)
    return PlatformSettingsResponse.model_validate(s)


# ============================================================
# COMPANIES
# ============================================================

@router.get("/companies", response_model=PaginatedResponse[CompanyListItem])
def list_all_companies(
    search: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    _: User = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> PaginatedResponse[CompanyListItem]:
    repo = CompaniesRepository(db)
    offset = (page - 1) * per_page
    companies = repo.list_companies(
        search=search,
        is_active=is_active,
        limit=per_page,
        offset=offset,
    )

    count_conditions = []
    if is_active is not None:
        count_conditions.append(Company.is_active == is_active)
    if search:
        count_conditions.append(
            Company.name.ilike(f"%{search}%") | Company.slug.ilike(f"%{search}%")
        )
    total = db.scalar(
        select(func.count()).select_from(Company).where(*count_conditions)
    ) or 0

    cids = [c.id for c in companies]
    user_counts = _count_users(db, cids)
    settings_set = _has_settings_set(db, cids)
    admin_set = _has_admin_set(db, cids)

    items = [
        _build_list_item(
            c,
            user_counts.get(c.id, 0),
            c.id in settings_set,
            c.id in admin_set,
        )
        for c in companies
    ]
    return PaginatedResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/companies/{company_id}", response_model=CompanyDetailResponse)
def get_company(
    company_id: int,
    _: User = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> CompanyDetailResponse:
    repo = CompaniesRepository(db)
    c = repo.get_by_id(company_id)
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada.")

    cids = [c.id]
    user_count = _count_users(db, cids).get(c.id, 0)
    has_settings = bool(_has_settings_set(db, cids))
    has_admin = bool(_has_admin_set(db, cids))
    return _build_detail(db, c, user_count, has_settings, has_admin)


@router.post("/companies", response_model=CompanyDetailResponse, status_code=status.HTTP_201_CREATED)
def create_company(
    payload: CompanyCreateFull,
    _: User = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> CompanyDetailResponse:
    service = OnboardingService(db)
    try:
        company, settings, admin = service.bootstrap_company(
            name=payload.name,
            slug=payload.slug,
            service_domain=payload.service_domain,
            plan_name=payload.plan_name,
            whatsapp_phone_number_id=payload.whatsapp_phone_number_id,
            support_email=str(payload.support_email) if payload.support_email else None,
            admin_name=payload.admin_name,
            admin_email=str(payload.admin_email),
            admin_password=payload.admin_password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    db.commit()
    db.refresh(company)
    return _build_detail(db, company, 1, True, True)


@router.patch("/companies/{company_id}", response_model=CompanyDetailResponse)
def update_company(
    company_id: int,
    payload: CompanyUpdate,
    _: User = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> CompanyDetailResponse:
    repo = CompaniesRepository(db)
    c = repo.get_by_id(company_id)
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada.")

    updates = payload.model_dump(exclude_unset=True)
    for key, val in updates.items():
        setattr(c, key, val)
    db.commit()
    db.refresh(c)

    cids = [c.id]
    user_count = _count_users(db, cids).get(c.id, 0)
    has_settings = bool(_has_settings_set(db, cids))
    has_admin = bool(_has_admin_set(db, cids))
    return _build_detail(db, c, user_count, has_settings, has_admin)


@router.post("/companies/{company_id}/bootstrap-admin", response_model=CompanyDetailResponse)
def bootstrap_admin(
    company_id: int,
    payload: BootstrapAdminPayload,
    _: User = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> CompanyDetailResponse:
    repo = CompaniesRepository(db)
    c = repo.get_by_id(company_id)
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada.")

    service = OnboardingService(db)
    try:
        service.create_admin_for_company(
            company=c,
            admin_name=payload.admin_name,
            admin_email=str(payload.admin_email),
            admin_password=payload.admin_password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    db.commit()

    cids = [c.id]
    user_count = _count_users(db, cids).get(c.id, 0)
    has_settings = bool(_has_settings_set(db, cids))
    has_admin = bool(_has_admin_set(db, cids))
    return _build_detail(db, c, user_count, has_settings, has_admin)


# ============================================================
# USERS
# ============================================================

@router.get("/users", response_model=PaginatedResponse[AdminUserResponse])
def list_all_users(
    company_id: int | None = Query(default=None),
    role: UserRole | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    _: User = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> PaginatedResponse[AdminUserResponse]:
    base_stmt = (
        select(User, Company.name.label("cn"), Company.slug.label("cs"))
        .outerjoin(Company, User.company_id == Company.id)
    )
    conditions = []
    if company_id is not None:
        if company_id == 0:
            conditions.append(User.company_id.is_(None))
        else:
            conditions.append(User.company_id == company_id)
    if role is not None:
        conditions.append(User.role == role)
    if is_active is not None:
        conditions.append(User.is_active == is_active)
    if search:
        term = f"%{search.strip()}%"
        conditions.append(or_(User.name.ilike(term), User.email.ilike(term)))

    if conditions:
        base_stmt = base_stmt.where(*conditions)

    total = db.scalar(
        select(func.count())
        .select_from(User)
        .where(*conditions)
    ) or 0

    rows = db.execute(
        base_stmt.order_by(User.name.asc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    ).all()

    items = [
        AdminUserResponse.model_validate({
            **UserResponse.model_validate(u).model_dump(),
            "company_name": cn,
            "company_slug": cs,
        })
        for u, cn, cs in rows
    ]
    return PaginatedResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/users/{user_id}", response_model=AdminUserResponse)
def get_user(
    user_id: int,
    _: User = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> AdminUserResponse:
    return _fetch_admin_user(db, user_id)


@router.post("/users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    _: User = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> AdminUserResponse:
    users_repo = UsersRepository(db)
    existing = users_repo.get_by_email(str(payload.email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe um usuário com esse e-mail.")

    if payload.role != UserRole.MASTER_ADMIN and payload.company_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="company_id é obrigatório para roles que não sejam master_admin.",
        )
    if payload.role == UserRole.MASTER_ADMIN and payload.company_id is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="master_admin não pode pertencer a uma empresa.",
        )

    obj = users_repo.create_user(
        company_id=payload.company_id,
        email=str(payload.email),
        password_hash=hash_password(payload.password),
        role=payload.role,
        name=payload.name,
        whatsapp_id=payload.whatsapp_id,
        is_active=payload.is_active,
    )
    db.commit()
    db.refresh(obj)
    return _fetch_admin_user(db, obj.id)


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    _: User = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> AdminUserResponse:
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    updates = payload.model_dump(exclude_unset=True)

    if "role" in updates:
        if updates["role"] == UserRole.MASTER_ADMIN:
            updates["company_id"] = None
        elif updates["role"] != UserRole.MASTER_ADMIN and updates.get("company_id") is None and u.company_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="company_id é obrigatório para roles que não sejam master_admin.",
            )

    if "email" in updates:
        existing = db.scalar(
            select(User).where(
                func.lower(User.email) == str(updates["email"]).lower(),
                User.id != user_id,
            )
        )
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail já em uso por outro usuário.")

    for k, v in updates.items():
        if k == "password":
            u.password_hash = hash_password(v)
        else:
            setattr(u, k, v)

    db.commit()
    db.refresh(u)
    return _fetch_admin_user(db, u.id)


# ============================================================
# METRICS
# ============================================================

@router.get("/metrics")
def get_global_metrics(
    _: User = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> dict:
    total_companies = db.scalar(select(func.count()).select_from(Company)) or 0
    active_companies = db.scalar(
        select(func.count()).select_from(Company).where(Company.is_active.is_(True))
    ) or 0
    total_users = db.scalar(select(func.count()).select_from(User)) or 0
    total_conversations = db.scalar(select(func.count()).select_from(Conversation)) or 0
    total_quotes = db.scalar(select(func.count()).select_from(Quote)) or 0
    total_appointments = db.scalar(select(func.count()).select_from(Appointment)) or 0

    return {
        "companies": {"total": total_companies, "active": active_companies},
        "users": {"total": total_users},
        "conversations": {"total": total_conversations},
        "quotes": {"total": total_quotes},
        "appointments": {"total": total_appointments},
    }


# ============================================================
# REMINDERS
# ============================================================

@router.post("/reminders/send-pending", tags=["Admin"])
def trigger_send_pending_reminders(
    _: User = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> dict:
    """
    Dispara manualmente o envio de lembretes pendentes de agendamento.
    Útil para testes e reprocessamento em caso de falha do scheduler.
    Acesso: apenas MASTER_ADMIN.
    """
    from app.services.reminder_service import send_pending_reminders
    stats = send_pending_reminders(db)
    return {
        "ok": True,
        "stats": stats,
        "message": (
            f"Lembretes processados: {stats['sent']} enviados, "
            f"{stats['failed']} com falha, {stats['skipped']} sem credenciais."
        ),
    }
