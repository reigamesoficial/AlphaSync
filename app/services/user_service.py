from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.tenancy import assert_company_match
from app.db.models import User
from app.repositories.users import UsersRepository
from app.schemas.users import UserMeResponse, UserResponse


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.users_repo = UsersRepository(db)

    def get_me(self, current_user: User) -> UserMeResponse:
        return UserMeResponse.model_validate(current_user)

    def get_by_id_for_tenant(
        self,
        *,
        user_id: int,
        tenant_company_id: int,
        current_user: User,
    ) -> UserResponse:
        user = self.users_repo.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado.",
            )

        if user.company_id is not None:
            assert_company_match(user.company_id, tenant_company_id, current_user)

        return UserResponse.model_validate(user)