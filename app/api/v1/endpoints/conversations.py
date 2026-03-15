from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.core.tenancy import get_tenant_company_id
from app.db.connection import get_db
from app.db.models import ConversationMessage, ConversationStatus, User
from app.repositories.conversations import ConversationsRepository
from app.schemas.common import PaginatedResponse
from app.schemas.conversation import ConversationMessageResponse, ConversationResponse

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get("", response_model=PaginatedResponse[ConversationResponse])
def list_conversations(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    status: ConversationStatus | None = Query(default=None),
    search: str | None = Query(default=None, description="Busca por telefone ou assunto"),
    assigned_to_id: int | None = Query(default=None),
    company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo = ConversationsRepository(db)
    offset = (page - 1) * per_page
    items = repo.list_company_conversations(
        company_id,
        status=status,
        assigned_to_id=assigned_to_id,
        search=search,
        limit=per_page,
        offset=offset,
    )
    total = repo.count_company_conversations(company_id, status=status, search=search)
    return PaginatedResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: int,
    company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo = ConversationsRepository(db)
    conv = repo.get_full_by_id_and_company(conversation_id, company_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversa não encontrada.")
    return conv


@router.get("/{conversation_id}/messages", response_model=list[ConversationMessageResponse])
def list_conversation_messages(
    conversation_id: int,
    company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo = ConversationsRepository(db)
    conv = repo.get_by_id_and_company(conversation_id, company_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversa não encontrada.")

    stmt = (
        select(ConversationMessage)
        .where(
            ConversationMessage.conversation_id == conversation_id,
            ConversationMessage.company_id == company_id,
        )
        .order_by(ConversationMessage.created_at.asc())
    )
    return list(db.scalars(stmt).all())
