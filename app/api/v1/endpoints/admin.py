from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.security import hash_password, require_master_admin
from app.db.connection import get_db
from app.db.models import Appointment, Company, CompanyStatus, Conversation, Quote, User, UserRole
from app.repositories.companies import CompaniesRepository
from app.repositories.users import UsersRepository
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate
from app.schemas.users import UserCreate, UserResponse

router = APIRouter(prefix="/admin", tags=["Admin (Master)"])


@router.get("/companies", response_model=list[CompanyResponse])
def list_all_companies(
    search: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> list[CompanyResponse]:
    repo = CompaniesRepository(db)
    return repo.list_companies(search=search, is_active=is_active, limit=limit, offset=offset)


@router.post("/companies", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(
    payload: CompanyCreate,
    _: User = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> CompanyResponse:
    repo = CompaniesRepository(db)
    existing = repo.get_by_slug(payload.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma empresa com esse slug.",
        )
    data = payload.model_dump()
    obj = Company(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.patch("/companies/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: int,
    payload: CompanyUpdate,
    _: User = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> CompanyResponse:
    repo = CompaniesRepository(db)
    obj = repo.get_by_id(company_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada.")
    updates = payload.model_dump(exclude_unset=True)
    for key, val in updates.items():
        setattr(obj, key, val)
    db.commit()
    db.refresh(obj)
    return obj


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
        stmt = stmt.where(
            or_(User.name.ilike(term), User.email.ilike(term))
        )

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
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um usuário com esse e-mail.",
        )
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
