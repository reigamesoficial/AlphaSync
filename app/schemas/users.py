from pydantic import EmailStr, Field

from app.db.models import UserRole
from app.schemas.common import BaseSchema, IDSchema, TimestampSchema


class UserBase(BaseSchema):
    company_id: int | None = None
    email: EmailStr
    role: UserRole = UserRole.VIEWER
    name: str = Field(min_length=2, max_length=200)
    whatsapp_id: str | None = Field(default=None, max_length=40)
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)


class UserUpdate(BaseSchema):
    email: EmailStr | None = None
    role: UserRole | None = None
    name: str | None = Field(default=None, min_length=2, max_length=200)
    whatsapp_id: str | None = Field(default=None, max_length=40)
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)


class UserPasswordChange(BaseSchema):
    current_password: str = Field(min_length=6, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


class UserResponse(UserBase, IDSchema, TimestampSchema):
    pass


class UserMeResponse(UserResponse):
    pass