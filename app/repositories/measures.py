from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import PNAddressCatalog, PNAddressMeasurement, PNAddressPlant
from app.schemas.measures import (
    AddressCreate,
    AddressUpdate,
    ItemCreate,
    ItemUpdate,
    PlantCreate,
    PlantUpdate,
    _normalize_address,
)


class MeasuresRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_addresses(
        self,
        company_id: int,
        *,
        search: str | None = None,
        city: str | None = None,
        state: str | None = None,
    ) -> list[PNAddressCatalog]:
        stmt = (
            select(PNAddressCatalog)
            .where(
                PNAddressCatalog.company_id == company_id,
                PNAddressCatalog.is_active.is_(True),
            )
            .options(
                selectinload(PNAddressCatalog.plants).selectinload(PNAddressPlant.measurements),
                selectinload(PNAddressCatalog.measurements),
            )
            .order_by(PNAddressCatalog.id.desc())
        )
        if search:
            term = f"%{search.strip().lower()}%"
            stmt = stmt.where(PNAddressCatalog.normalized_address.ilike(term))
        if city:
            stmt = stmt.where(PNAddressCatalog.city.ilike(f"%{city.strip()}%"))
        if state:
            stmt = stmt.where(PNAddressCatalog.state.ilike(f"%{state.strip()}%"))
        return list(self.db.scalars(stmt).all())

    def get_address(self, address_id: int, company_id: int) -> PNAddressCatalog | None:
        stmt = (
            select(PNAddressCatalog)
            .where(
                PNAddressCatalog.id == address_id,
                PNAddressCatalog.company_id == company_id,
                PNAddressCatalog.is_active.is_(True),
            )
            .options(
                selectinload(PNAddressCatalog.plants).selectinload(PNAddressPlant.measurements),
                selectinload(PNAddressCatalog.measurements),
            )
        )
        return self.db.scalar(stmt)

    def create_address(self, company_id: int, payload: AddressCreate) -> PNAddressCatalog:
        normalized = _normalize_address(payload.raw_address)
        obj = PNAddressCatalog(
            company_id=company_id,
            raw_address=payload.raw_address.strip(),
            normalized_address=normalized,
            city=payload.city,
            state=payload.state,
            zipcode=payload.zipcode,
            notes=payload.notes,
            is_active=True,
        )
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj

    def update_address(self, obj: PNAddressCatalog, payload: AddressUpdate) -> PNAddressCatalog:
        data = payload.model_dump(exclude_unset=True)
        if "raw_address" in data and data["raw_address"]:
            data["normalized_address"] = _normalize_address(data["raw_address"])
        for k, v in data.items():
            setattr(obj, k, v)
        self.db.flush()
        self.db.refresh(obj)
        return obj

    def soft_delete_address(self, obj: PNAddressCatalog) -> None:
        obj.is_active = False
        self.db.flush()

    def get_plant(self, plant_id: int, company_id: int) -> PNAddressPlant | None:
        stmt = select(PNAddressPlant).where(
            PNAddressPlant.id == plant_id,
            PNAddressPlant.company_id == company_id,
            PNAddressPlant.is_active.is_(True),
        )
        return self.db.scalar(stmt)

    def create_plant(self, company_id: int, payload: PlantCreate) -> PNAddressPlant:
        obj = PNAddressPlant(
            company_id=company_id,
            address_catalog_id=payload.address_catalog_id,
            name=payload.name.strip(),
            sort_order=payload.sort_order,
            is_active=True,
        )
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj

    def update_plant(self, obj: PNAddressPlant, payload: PlantUpdate) -> PNAddressPlant:
        data = payload.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(obj, k, v)
        self.db.flush()
        self.db.refresh(obj)
        return obj

    def soft_delete_plant(self, obj: PNAddressPlant) -> None:
        obj.is_active = False
        self.db.flush()

    def get_item(self, item_id: int, company_id: int) -> PNAddressMeasurement | None:
        stmt = select(PNAddressMeasurement).where(
            PNAddressMeasurement.id == item_id,
            PNAddressMeasurement.company_id == company_id,
            PNAddressMeasurement.is_active.is_(True),
        )
        return self.db.scalar(stmt)

    def create_item(self, company_id: int, payload: ItemCreate) -> PNAddressMeasurement:
        obj = PNAddressMeasurement(
            company_id=company_id,
            address_catalog_id=payload.address_catalog_id,
            plant_id=payload.plant_id,
            label=payload.label.strip(),
            width_m=Decimal(str(payload.width_m)),
            height_m=Decimal(str(payload.height_m)),
            quantity=payload.quantity,
            notes=payload.notes,
            is_active=True,
        )
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj

    def update_item(self, obj: PNAddressMeasurement, payload: ItemUpdate) -> PNAddressMeasurement:
        data = payload.model_dump(exclude_unset=True)
        for k, v in data.items():
            if k in ("width_m", "height_m") and v is not None:
                setattr(obj, k, Decimal(str(v)))
            else:
                setattr(obj, k, v)
        self.db.flush()
        self.db.refresh(obj)
        return obj

    def soft_delete_item(self, obj: PNAddressMeasurement) -> None:
        obj.is_active = False
        self.db.flush()

    def get_stats(self, company_id: int) -> dict[str, int]:
        addr_count = self.db.scalar(
            select(func.count()).select_from(PNAddressCatalog).where(
                PNAddressCatalog.company_id == company_id,
                PNAddressCatalog.is_active.is_(True),
            )
        ) or 0
        plant_count = self.db.scalar(
            select(func.count()).select_from(PNAddressPlant).where(
                PNAddressPlant.company_id == company_id,
                PNAddressPlant.is_active.is_(True),
            )
        ) or 0
        item_count = self.db.scalar(
            select(func.count()).select_from(PNAddressMeasurement).where(
                PNAddressMeasurement.company_id == company_id,
                PNAddressMeasurement.is_active.is_(True),
            )
        ) or 0
        return {
            "total_addresses": int(addr_count),
            "total_plants": int(plant_count),
            "total_items": int(item_count),
        }
