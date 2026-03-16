"""Repositório para DomainDefinition."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DomainDefinition
from app.repositories.base import BaseRepository


class DomainDefinitionsRepository(BaseRepository[DomainDefinition]):
    def __init__(self, db: Session):
        super().__init__(db, DomainDefinition)

    def get_by_key(self, key: str) -> DomainDefinition | None:
        return self.db.scalar(select(DomainDefinition).where(DomainDefinition.key == key))

    def list_all(self, *, active_only: bool = False) -> list[DomainDefinition]:
        stmt = select(DomainDefinition).order_by(DomainDefinition.display_name)
        if active_only:
            stmt = stmt.where(DomainDefinition.is_active.is_(True))
        return list(self.db.scalars(stmt).all())

    def create(
        self,
        *,
        key: str,
        display_name: str,
        description: str | None = None,
        icon: str | None = None,
        is_active: bool = True,
        is_builtin: bool = True,
        config_json: dict | None = None,
    ) -> DomainDefinition:
        obj = DomainDefinition(
            key=key,
            display_name=display_name,
            description=description,
            icon=icon,
            is_active=is_active,
            is_builtin=is_builtin,
            config_json=config_json or {},
        )
        return self.add(obj)

    def update(self, obj: DomainDefinition, **fields) -> DomainDefinition:
        for k, v in fields.items():
            if v is not None or k in ("description", "icon"):
                setattr(obj, k, v)
        self.db.flush()
        self.db.refresh(obj)
        return obj
