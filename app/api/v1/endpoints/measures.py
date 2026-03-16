from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    get_current_active_user,
    require_admin_seller_or_master,
    require_company_admin_or_master,
)
from app.core.tenancy import get_tenant_company_id
from app.db.connection import get_db
from app.db.models import User
from app.repositories.measures import MeasuresRepository
from app.schemas.measures import (
    AddressCreate,
    AddressResponse,
    AddressUpdate,
    AddressWithHierarchy,
    ItemCreate,
    ItemResponse,
    ItemUpdate,
    MeasureStats,
    PlantCreate,
    PlantResponse,
    PlantUpdate,
    PlantWithItems,
)

router = APIRouter(prefix="/measures", tags=["Measures"])


def _build_hierarchy(catalog) -> AddressWithHierarchy:
    active_plants = [p for p in (catalog.plants or []) if p.is_active]
    active_plant_ids = {p.id for p in active_plants}

    plants_out: list[PlantWithItems] = []
    for plant in active_plants:
        plant_items = [
            ItemResponse.model_validate(m)
            for m in (plant.measurements or [])
            if m.is_active
        ]
        plants_out.append(
            PlantWithItems(
                plant=PlantResponse.model_validate(plant),
                items=plant_items,
            )
        )

    direct_items = [
        ItemResponse.model_validate(m)
        for m in (catalog.measurements or [])
        if m.is_active and m.plant_id not in active_plant_ids
    ]

    return AddressWithHierarchy(
        address=AddressResponse.model_validate(catalog),
        plants=plants_out,
        direct_items=direct_items,
    )


@router.get("/stats", response_model=MeasureStats)
def get_stats(
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> MeasureStats:
    repo = MeasuresRepository(db)
    data = repo.get_stats(tenant_company_id)
    return MeasureStats(**data)


@router.get("/addresses", response_model=list[AddressWithHierarchy])
def list_addresses(
    search: str | None = Query(default=None),
    city: str | None = Query(default=None),
    state: str | None = Query(default=None),
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[AddressWithHierarchy]:
    repo = MeasuresRepository(db)
    catalogs = repo.list_addresses(tenant_company_id, search=search, city=city, state=state)
    return [_build_hierarchy(c) for c in catalogs]


@router.post("/addresses", response_model=AddressWithHierarchy, status_code=status.HTTP_201_CREATED)
def create_address(
    payload: AddressCreate,
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(require_admin_seller_or_master),
    db: Session = Depends(get_db),
) -> AddressWithHierarchy:
    repo = MeasuresRepository(db)
    try:
        obj = repo.create_address(tenant_company_id, payload)
        db.commit()
        fresh = repo.get_address(obj.id, tenant_company_id)
        return _build_hierarchy(fresh)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um endereço com esse endereço normalizado para esta empresa.",
        )


@router.patch("/addresses/{address_id}", response_model=AddressWithHierarchy)
def update_address(
    address_id: int,
    payload: AddressUpdate,
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(require_admin_seller_or_master),
    db: Session = Depends(get_db),
) -> AddressWithHierarchy:
    repo = MeasuresRepository(db)
    obj = repo.get_address(address_id, tenant_company_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endereço não encontrado.")
    try:
        updated = repo.update_address(obj, payload)
        db.commit()
        fresh = repo.get_address(updated.id, tenant_company_id)
        return _build_hierarchy(fresh)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um endereço com esse endereço normalizado para esta empresa.",
        )


@router.delete("/addresses/{address_id}")
def delete_address(
    address_id: int,
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(require_company_admin_or_master),
    db: Session = Depends(get_db),
) -> Response:
    repo = MeasuresRepository(db)
    obj = repo.get_address(address_id, tenant_company_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endereço não encontrado.")
    repo.soft_delete_address(obj)
    db.commit()
    return Response(status_code=204)


@router.post("/plants", response_model=PlantResponse, status_code=status.HTTP_201_CREATED)
def create_plant(
    payload: PlantCreate,
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(require_admin_seller_or_master),
    db: Session = Depends(get_db),
) -> PlantResponse:
    repo = MeasuresRepository(db)
    catalog = repo.get_address(payload.address_catalog_id, tenant_company_id)
    if not catalog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endereço não encontrado.")
    try:
        obj = repo.create_plant(tenant_company_id, payload)
        db.commit()
        return PlantResponse.model_validate(obj)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma planta com esse nome neste endereço.",
        )


@router.patch("/plants/{plant_id}", response_model=PlantResponse)
def update_plant(
    plant_id: int,
    payload: PlantUpdate,
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(require_admin_seller_or_master),
    db: Session = Depends(get_db),
) -> PlantResponse:
    repo = MeasuresRepository(db)
    obj = repo.get_plant(plant_id, tenant_company_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planta não encontrada.")
    updated = repo.update_plant(obj, payload)
    db.commit()
    return PlantResponse.model_validate(updated)


@router.delete("/plants/{plant_id}")
def delete_plant(
    plant_id: int,
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(require_company_admin_or_master),
    db: Session = Depends(get_db),
) -> Response:
    repo = MeasuresRepository(db)
    obj = repo.get_plant(plant_id, tenant_company_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planta não encontrada.")
    repo.soft_delete_plant(obj)
    db.commit()
    return Response(status_code=204)


@router.post("/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    payload: ItemCreate,
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(require_admin_seller_or_master),
    db: Session = Depends(get_db),
) -> ItemResponse:
    repo = MeasuresRepository(db)
    catalog = repo.get_address(payload.address_catalog_id, tenant_company_id)
    if not catalog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endereço não encontrado.")
    if payload.plant_id:
        plant = repo.get_plant(payload.plant_id, tenant_company_id)
        if not plant or plant.address_catalog_id != payload.address_catalog_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planta não encontrada.")
    obj = repo.create_item(tenant_company_id, payload)
    db.commit()
    return ItemResponse.model_validate(obj)


@router.patch("/items/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int,
    payload: ItemUpdate,
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(require_admin_seller_or_master),
    db: Session = Depends(get_db),
) -> ItemResponse:
    repo = MeasuresRepository(db)
    obj = repo.get_item(item_id, tenant_company_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medida não encontrada.")
    updated = repo.update_item(obj, payload)
    db.commit()
    return ItemResponse.model_validate(updated)


@router.delete("/items/{item_id}")
def delete_item(
    item_id: int,
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(require_company_admin_or_master),
    db: Session = Depends(get_db),
) -> Response:
    repo = MeasuresRepository(db)
    obj = repo.get_item(item_id, tenant_company_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medida não encontrada.")
    repo.soft_delete_item(obj)
    db.commit()
    return Response(status_code=204)
