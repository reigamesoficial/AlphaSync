from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case as sa_case, func, select
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


@router.get("/financial")
def get_financial_report(
    months: int = Query(default=6, ge=1, le=24),
    company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)

    # Calculate period_start (months ago, first day of that month)
    pm = now.month - months
    py = now.year + (pm - 1) // 12
    pm = ((pm - 1) % 12) + 1
    period_start = now.replace(year=py, month=pm, day=1, hour=0, minute=0, second=0, microsecond=0)

    # Previous month (for comparison)
    lm = now.month - 1 if now.month > 1 else 12
    ly = now.year if now.month > 1 else now.year - 1
    prev_month_start = now.replace(year=ly, month=lm, day=1, hour=0, minute=0, second=0, microsecond=0)

    revenue_statuses = [QuoteStatus.CONFIRMED, QuoteStatus.DONE]

    # Revenue in full period
    revenue_total_row = db.execute(
        select(func.coalesce(func.sum(Quote.total_value), 0))
        .where(
            Quote.company_id == company_id,
            Quote.status.in_(revenue_statuses),
            Quote.created_at >= period_start,
        )
    ).scalar() or 0

    # Revenue last month only
    revenue_last_month_row = db.execute(
        select(func.coalesce(func.sum(Quote.total_value), 0))
        .where(
            Quote.company_id == company_id,
            Quote.status.in_(revenue_statuses),
            Quote.created_at >= prev_month_start,
            Quote.created_at < now,
        )
    ).scalar() or 0

    # Counts
    quotes_confirmed = db.execute(
        select(func.count(Quote.id))
        .where(Quote.company_id == company_id, Quote.status == QuoteStatus.CONFIRMED, Quote.created_at >= period_start)
    ).scalar() or 0

    quotes_done = db.execute(
        select(func.count(Quote.id))
        .where(Quote.company_id == company_id, Quote.status == QuoteStatus.DONE, Quote.created_at >= period_start)
    ).scalar() or 0

    total_quotes_period = db.execute(
        select(func.count(Quote.id))
        .where(Quote.company_id == company_id, Quote.created_at >= period_start)
    ).scalar() or 0

    clients_active = db.execute(
        select(func.count(func.distinct(Quote.client_id)))
        .where(Quote.company_id == company_id, Quote.created_at >= period_start)
    ).scalar() or 0

    conversion_rate = round((quotes_confirmed + quotes_done) / total_quotes_period * 100, 1) if total_quotes_period else 0.0

    # Current month boundaries (for growth comparison)
    cur_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    revenue_current_month = db.execute(
        select(func.coalesce(func.sum(Quote.total_value), 0))
        .where(
            Quote.company_id == company_id,
            Quote.status.in_(revenue_statuses),
            Quote.created_at >= cur_month_start,
        )
    ).scalar() or 0

    # Monthly breakdown — filtered to revenue statuses only
    monthly_rows = db.execute(
        select(
            func.to_char(Quote.created_at, "Mon/YY").label("month"),
            func.date_trunc("month", Quote.created_at).label("month_dt"),
            func.coalesce(func.sum(Quote.total_value), 0).label("revenue"),
            func.count(Quote.id).label("quotes"),
        )
        .where(
            Quote.company_id == company_id,
            Quote.status.in_(revenue_statuses),
            Quote.created_at >= period_start,
        )
        .group_by("month", "month_dt")
        .order_by("month_dt")
    ).all()

    monthly = [{"month": r.month, "revenue": float(r.revenue), "quotes": r.quotes} for r in monthly_rows]

    # Top clients
    top_clients_rows = db.execute(
        select(
            Client.name.label("client_name"),
            func.coalesce(func.sum(Quote.total_value), 0).label("total"),
            func.count(Quote.id).label("quotes_count"),
        )
        .join(Client, Quote.client_id == Client.id)
        .where(
            Quote.company_id == company_id,
            Quote.status.in_(revenue_statuses),
            Quote.created_at >= period_start,
        )
        .group_by(Client.name)
        .order_by(func.sum(Quote.total_value).desc())
        .limit(10)
    ).all()

    top_clients = [
        {"client_name": r.client_name, "total": float(r.total), "quotes_count": r.quotes_count}
        for r in top_clients_rows
    ]

    return {
        "revenue_total": float(revenue_total_row),
        "revenue_current_month": float(revenue_current_month),
        "revenue_prev_month": float(revenue_last_month_row),
        "quotes_confirmed": quotes_confirmed,
        "quotes_done": quotes_done,
        "clients_active": clients_active,
        "conversion_rate": conversion_rate,
        "monthly": monthly,
        "top_clients": top_clients,
    }


@router.get("/crm")
def get_crm_pipeline(
    company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Returns clients with their CRM pipeline stage calculated from client status + best quote status.
    Stage priority logic:
      - DONE quote        → 'won'
      - CONFIRMED quote   → 'quote_sent'
      - DRAFT quote       → 'visit'
      - No quotes + qualified client → 'contacted'
      - No quotes + lead client      → 'lead'
      - inactive client   → 'lost'
      - customer client   → 'won'
    """
    # Subquery: per-client best quote priority and top value
    status_priority = sa_case(
        (Quote.status == QuoteStatus.DONE, 5),
        (Quote.status == QuoteStatus.CONFIRMED, 4),
        (Quote.status == QuoteStatus.DRAFT, 3),
        (Quote.status == QuoteStatus.EXPIRED, 2),
        (Quote.status == QuoteStatus.CANCELLED, 1),
        else_=0,
    )

    quote_sub = (
        select(
            Quote.client_id.label("client_id"),
            func.max(status_priority).label("best_priority"),
            func.max(Quote.total_value).label("top_value"),
        )
        .where(Quote.company_id == company_id)
        .group_by(Quote.client_id)
        .subquery()
    )

    rows = db.execute(
        select(
            Client.id,
            Client.name,
            Client.phone,
            Client.status.label("client_status"),
            quote_sub.c.best_priority,
            quote_sub.c.top_value,
        )
        .outerjoin(quote_sub, quote_sub.c.client_id == Client.id)
        .where(Client.company_id == company_id)
        .order_by(Client.created_at.desc())
        .limit(300)
    ).all()

    def _derive_stage(client_status: str, best_priority: int | None) -> str:
        if client_status == "inactive":
            return "lost"
        if client_status == "customer":
            return "won"
        if best_priority is None:
            return "contacted" if client_status == "qualified" else "lead"
        if best_priority >= 5:
            return "won"
        if best_priority >= 4:
            return "quote_sent"
        if best_priority >= 3:
            return "visit"
        # Only EXPIRED or CANCELLED quotes remain
        return "contacted" if client_status == "qualified" else "lead"

    clients = []
    for r in rows:
        stage = _derive_stage(r.client_status, r.best_priority)
        clients.append({
            "id": r.id,
            "name": r.name,
            "phone": r.phone or "",
            "stage": stage,
            "quote_value": float(r.top_value) if r.top_value else 0.0,
        })

    return {"clients": clients}


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
