from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field
from pydantic.generics import GenericModel


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class IDSchema(BaseSchema):
    id: int


class TimestampSchema(BaseSchema):
    created_at: datetime
    updated_at: datetime


class MessageSchema(BaseSchema):
    message: str


class ErrorSchema(BaseSchema):
    error: str
    code: str


class OkSchema(BaseSchema):
    ok: bool = True


class PaginationParams(BaseSchema):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=50, ge=1, le=200)


T = TypeVar("T")


class PaginatedResponse(GenericModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int