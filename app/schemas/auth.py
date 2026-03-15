from datetime import datetime

from pydantic import EmailStr, Field

from app.db.models import UserRole
from app.schemas.common import BaseSchema


class LoginRequest(BaseSchema):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class RefreshTokenRequest(BaseSchema):
    token: str


class LogoutRequest(BaseSchema):
    token: str | None = None


class AuthUserSchema(BaseSchema):
    id: int
    company_id: int | None = None
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool


class LoginResponse(BaseSchema):
    token: str
    refresh_token: str
    expires_at: datetime
    user: AuthUserSchema


class RefreshResponse(BaseSchema):
    token: str
    expires_at: datetime


class TokenPayload(BaseSchema):
    sub: int
    company_id: int | None = None
    role: UserRole
    exp: int
    type: str