from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.core.tenancy import get_tenant_company_id
from app.db.connection import get_db
from app.db.models import QuoteStatus, User
from app.repositories.quotes import QuoteItemsRepository, QuotesRepository
from app.schemas.common import PaginatedResponse
from app.schemas.quote import QuoteCreate, QuoteResponse, QuoteUpdate

router = APIRouter(prefix="/quotes", tags=["Quotes"])


@router.get("", response_model=PaginatedResponse[QuoteResponse])
def list_quotes(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    status: QuoteStatus | None = Query(default=None),
    client_id: int | None = Query(default=None),
    seller_id: int | None = Query(default=None),
    company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo = QuotesRepository(db)
    offset = (page - 1) * per_page
    items = repo.list_company_quotes(
        company_id,
        status=status,
        client_id=client_id,
        seller_id=seller_id,
        limit=per_page,
        offset=offset,
    )
    total = repo.count_company_quotes(company_id, status=status, client_id=client_id)
    return PaginatedResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/{quote_id}", response_model=QuoteResponse)
def get_quote(
    quote_id: int,
    company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo = QuotesRepository(db)
    quote = repo.get_full_by_id_and_company(quote_id, company_id)
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orçamento não encontrado.")
    return quote


@router.post("", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
def create_quote(
    payload: QuoteCreate,
    company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo = QuotesRepository(db)
    items_repo = QuoteItemsRepository(db)

    quote = repo.create_quote(
        company_id=company_id,
        client_id=payload.client_id,
        conversation_id=payload.conversation_id,
        seller_id=payload.seller_id or current_user.id,
        code=payload.code,
        service_type=payload.service_type,
        title=payload.title,
        description=payload.description,
        subtotal=payload.subtotal,
        discount=payload.discount,
        total_value=payload.total_value,
        status=payload.status,
        valid_until=payload.valid_until,
        notes=payload.notes,
        pdf_url=payload.pdf_url,
        domain_data=payload.domain_data,
    )

    for item in payload.items:
        items_repo.create_item(
            company_id=company_id,
            quote_id=quote.id,
            description=item.description,
            service_type=item.service_type,
            width_cm=item.width_cm,
            height_cm=item.height_cm,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.total_price,
            status=item.status,
            notes=item.notes,
            domain_data=item.domain_data,
        )

    db.commit()
    return repo.get_full_by_id_and_company(quote.id, company_id)


@router.patch("/{quote_id}", response_model=QuoteResponse)
def update_quote(
    quote_id: int,
    payload: QuoteUpdate,
    company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo = QuotesRepository(db)
    quote = repo.get_by_id_and_company(quote_id, company_id)
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orçamento não encontrado.")

    update_data = payload.model_dump(exclude_unset=True)
    repo.update_quote(quote, **update_data)
    db.commit()
    return repo.get_full_by_id_and_company(quote_id, company_id)
