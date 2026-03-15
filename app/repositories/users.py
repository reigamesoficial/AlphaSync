from __future__ import annotations

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.db.models import User, UserRole
from app.repositories.base import TenantRepository


class UsersRepository(TenantRepository[User]):
    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(func.lower(User.email) == email.lower())
        return self.db.scalar(stmt)

    def get_by_email_and_company(self, email: str, company_id: int) -> User | None:
        stmt = select(User).where(
            func.lower(User.email) == email.lower(),
            User.company_id == company_id,
        )
        return self.db.scalar(stmt)

    def list_company_users(
        self,
        company_id: int,
        *,
        search: str | None = None,
        role: UserRole | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[User]:
        stmt: Select[tuple[User]] = select(User).where(User.company_id == company_id)

        if search:
            search_term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    User.name.ilike(search_term),
                    User.email.ilike(search_term),
                )
            )

        if role is not None:
            stmt = stmt.where(User.role == role)

        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)

        stmt = stmt.order_by(User.name.asc()).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())

    def create_user(
        self,
        *,
        company_id: int | None,
        email: str,
        password_hash: str,
        role: UserRole,
        name: str,
        whatsapp_id: str | None = None,
        is_active: bool = True,
    ) -> User:
        user = User(
            company_id=company_id,
            email=email.strip().lower(),
            password_hash=password_hash,
            role=role,
            name=name.strip(),
            whatsapp_id=whatsapp_id,
            is_active=is_active,
        )
        return self.add(user)

    def update_user(
        self,
        user: User,
        *,
        email: str | None = None,
        password_hash: str | None = None,
        role: UserRole | None = None,
        name: str | None = None,
        whatsapp_id: str | None = None,
        is_active: bool | None = None,
    ) -> User:
        if email is not None:
            user.email = email.strip().lower()
        if password_hash is not None:
            user.password_hash = password_hash
        if role is not None:
            user.role = role
        if name is not None:
            user.name = name.strip()
        if whatsapp_id is not None:
            user.whatsapp_id = whatsapp_id
        if is_active is not None:
            user.is_active = is_active

        self.db.flush()
        self.db.refresh(user)
        return user

    def count_company_users(self, company_id: int) -> int:
        stmt = select(func.count()).select_from(User).where(User.company_id == company_id)
        return int(self.db.scalar(stmt) or 0)