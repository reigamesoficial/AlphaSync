from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.core.tenancy import get_tenant_company_id
from app.db.connection import get_db
from app.db.models import (
    Client,
    ClientStatus,
    Conversation,
    ConversationStatus,
    Quote,
    QuoteStatus,
    User,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _count_by_enum(db: Session, model: Any, company_id: int, enum_col: Any, enum_cls: type) -> dict[str, int]:
    stmt = (
        select(enum_col, func.count())
        .where(model.company_id == company_id)
        .group_by(enum_col)
    )
    rows = db.execute(stmt).all()
    result = {e.value: 0 for e in enum_cls}
    for val, cnt in rows:
        result[val] = cnt
    return result


@router.get("/summary")
def get_dashboard_summary(
    company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    conv_by_status = _count_by_enum(
        db, Conversation, company_id, Conversation.status, ConversationStatus
    )
    total_conversations = sum(conv_by_status.values())

    client_by_status = _count_by_enum(
        db, Client, company_id, Client.status, ClientStatus
    )
    total_clients = sum(client_by_status.values())

    quote_by_status = _count_by_enum(
        db, Quote, company_id, Quote.status, QuoteStatus
    )
    total_quotes = sum(quote_by_status.values())

    open_convs = (
        conv_by_status.get(ConversationStatus.OPEN, 0)
        + conv_by_status.get(ConversationStatus.ASSUMED, 0)
        + conv_by_status.get(ConversationStatus.BOT, 0)
    )

    return {
        "conversations": {
            "total": total_conversations,
            "open": open_convs,
            "by_status": conv_by_status,
        },
        "clients": {
            "total": total_clients,
            "by_status": client_by_status,
        },
        "quotes": {
            "total": total_quotes,
            "by_status": quote_by_status,
        },
    }
