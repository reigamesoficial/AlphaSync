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
    CompanyStatus,
    Conversation,
    Quote,
    User,
    UserRole,
)
from app.repositories.companies import CompaniesRepository
from app.repositories.company_settings import CompanySettingsRepository
from app.repositories.users import UsersRepository
from app.schemas.common import PaginatedResponse
from app.schemas.company import (
    BootstrapAdminPayload,
    CompanyCreateFull,
    CompanyDetailResponse,
    CompanyListItem,
    CompanyResponse,
    CompanySettingsResponse,
    CompanyUpdate,
    AdminUserSummary,
)
from app.schemas.users import UserCreate, UserResponse
from app.services.onboarding_service import OnboardingService

router = APIRouter(prefix="/admin", tags=["Admin (Master)"])


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
    users_repo = UsersRepository(db)

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


@router.get("/companies", response_model=PaginatedResponse[CompanyListItem])
def list_all_companies(
    search: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    service_domain: str | None = Query(default=None),
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


@router.get("/users", response_model=list[UserResponse])
def list_all_users(
    company_id: int | None = Query(default=None),
    role: UserRole | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> list[UserResponse]:
    stmt = select(User)
    if company_id is not None:
        stmt = stmt.where(User.company_id == company_id)
    if role is not None:
        stmt = stmt.where(User.role == role)
    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(or_(User.name.ilike(term), User.email.ilike(term)))
    stmt = stmt.order_by(User.name.asc()).offset(offset).limit(limit)
    return list(db.scalars(stmt).all())


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    _: User = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> UserResponse:
    repo = UsersRepository(db)
    existing = repo.get_by_email(payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe um usuário com esse e-mail.")
    obj = repo.create_user(
        company_id=payload.company_id,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        name=payload.name,
        whatsapp_id=payload.whatsapp_id,
        is_active=payload.is_active,
    )
    db.commit()
    db.refresh(obj)
    return obj


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
