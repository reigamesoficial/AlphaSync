from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    def __init__(self, db: Session, model: type[ModelT]):
        self.db = db
        self.model = model

    def get_by_id(self, obj_id: int) -> ModelT | None:
        stmt = select(self.model).where(self.model.id == obj_id)
        return self.db.scalar(stmt)

    def add(self, instance: ModelT) -> ModelT:
        self.db.add(instance)
        self.db.flush()
        self.db.refresh(instance)
        return instance

    def delete(self, instance: ModelT) -> None:
        self.db.delete(instance)
        self.db.flush()

    def count(self, stmt: Select[Any]) -> int:
        subquery = stmt.order_by(None).subquery()
        count_stmt = select(func.count()).select_from(subquery)
        return int(self.db.scalar(count_stmt) or 0)


class TenantRepository(BaseRepository[ModelT]):
    def get_by_id_and_company(self, obj_id: int, company_id: int) -> ModelT | None:
        stmt = select(self.model).where(
            self.model.id == obj_id,
            self.model.company_id == company_id,
        )
        return self.db.scalar(stmt)

    def list_by_company(
        self,
        company_id: int,
        *,
        limit: int = 50,
        offset: int = 0,
        order_by: Any | None = None,
    ) -> list[ModelT]:
        stmt = select(self.model).where(self.model.company_id == company_id)

        if order_by is not None:
            stmt = stmt.order_by(order_by)

        stmt = stmt.offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())