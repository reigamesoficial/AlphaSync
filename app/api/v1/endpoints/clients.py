from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.core.tenancy import get_tenant_company_id
from app.db.connection import get_db
from app.db.models import ClientLeadSource, ClientStatus, User
from app.repositories.clients import ClientsRepository
from app.schemas.client import ClientCreate, ClientResponse, ClientUpdate
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("", response_model=PaginatedResponse[ClientResponse])
def list_clients(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    search: str | None = Query(default=None, description="Busca por nome, telefone ou e-mail"),
    status: ClientStatus | None = Query(default=None),
    lead_source: ClientLeadSource | None = Query(default=None),
    company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo = ClientsRepository(db)
    offset = (page - 1) * per_page
    items = repo.list_company_clients(
        company_id,
        search=search,
        status=status,
        lead_source=lead_source,
        limit=per_page,
        offset=offset,
    )
    total = repo.count_company_clients_filtered(
        company_id,
        search=search,
        status=status,
        lead_source=lead_source,
    )
    return PaginatedResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(
    client_id: int,
    company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo = ClientsRepository(db)
    client = repo.get_by_id_and_company(client_id, company_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado.")
    return client


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(
    payload: ClientCreate,
    company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo = ClientsRepository(db)
    existing = repo.get_by_phone(company_id=company_id, phone=payload.phone)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Telefone já cadastrado para esta empresa.",
        )
    client = repo.create_client(
        company_id=company_id,
        name=payload.name,
        phone=payload.phone,
        whatsapp_id=payload.whatsapp_id,
        email=payload.email,
        address=payload.address,
        lead_source=payload.lead_source,
        status=payload.status,
        notes=payload.notes,
    )
    db.commit()
    db.refresh(client)
    return client


@router.patch("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int,
    payload: ClientUpdate,
    company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo = ClientsRepository(db)
    client = repo.get_by_id_and_company(client_id, company_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado.")

    update_data = payload.model_dump(exclude_unset=True)

    if "phone" in update_data and update_data["phone"] != client.phone:
        conflict = repo.get_by_phone(company_id=company_id, phone=update_data["phone"])
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Telefone já cadastrado para outro cliente.",
            )

    client = repo.update_client(client, **update_data)
    db.commit()
    db.refresh(client)
    return client
