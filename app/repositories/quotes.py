from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Quote, QuoteItem, QuoteItemStatus, QuoteStatus
from app.repositories.base import TenantRepository


class QuotesRepository(TenantRepository[Quote]):
    def __init__(self, db: Session):
        super().__init__(db, Quote)

    def get_full_by_id_and_company(self, quote_id: int, company_id: int) -> Quote | None:
        stmt = (
            select(Quote)
            .where(
                Quote.id == quote_id,
                Quote.company_id == company_id,
            )
            .options(
                selectinload(Quote.items),
                selectinload(Quote.client),
                selectinload(Quote.seller),
                selectinload(Quote.conversation),
            )
        )
        return self.db.scalar(stmt)

    def get_by_code(self, *, company_id: int, code: str) -> Quote | None:
        stmt = select(Quote).where(
            Quote.company_id == company_id,
            Quote.code == code,
        )
        return self.db.scalar(stmt)

    def list_company_quotes(
        self,
        company_id: int,
        *,
        client_id: int | None = None,
        seller_id: int | None = None,
        status: QuoteStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Quote]:
        stmt: Select[tuple[Quote]] = (
            select(Quote)
            .where(Quote.company_id == company_id)
            .options(
                selectinload(Quote.client),
                selectinload(Quote.seller),
            )
        )

        if client_id is not None:
            stmt = stmt.where(Quote.client_id == client_id)

        if seller_id is not None:
            stmt = stmt.where(Quote.seller_id == seller_id)

        if status is not None:
            stmt = stmt.where(Quote.status == status)

        stmt = stmt.order_by(Quote.created_at.desc()).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())

    def create_quote(
        self,
        *,
        company_id: int,
        client_id: int,
        conversation_id: int | None = None,
        seller_id: int | None = None,
        code: str | None = None,
        service_type: str = "protection_network",
        title: str | None = None,
        description: str | None = None,
        subtotal: Decimal = Decimal("0.00"),
        discount: Decimal = Decimal("0.00"),
        total_value: Decimal = Decimal("0.00"),
        status: QuoteStatus = QuoteStatus.DRAFT,
        valid_until: date | None = None,
        notes: str | None = None,
        pdf_url: str | None = None,
        domain_data: dict[str, Any] | None = None,
    ) -> Quote:
        quote = Quote(
            company_id=company_id,
            client_id=client_id,
            conversation_id=conversation_id,
            seller_id=seller_id,
            code=code,
            service_type=service_type,
            title=title,
            description=description,
            subtotal=subtotal,
            discount=discount,
            total_value=total_value,
            status=status,
            valid_until=valid_until,
            notes=notes,
            pdf_url=pdf_url,
            domain_data=domain_data,
        )
        return self.add(quote)

    def update_quote(
        self,
        quote: Quote,
        *,
        client_id: int | None = None,
        conversation_id: int | None = None,
        seller_id: int | None = None,
        code: str | None = None,
        service_type: str | None = None,
        title: str | None = None,
        description: str | None = None,
        subtotal: Decimal | None = None,
        discount: Decimal | None = None,
        total_value: Decimal | None = None,
        status: QuoteStatus | None = None,
        valid_until: date | None = None,
        notes: str | None = None,
        pdf_url: str | None = None,
        domain_data: dict[str, Any] | None = None,
    ) -> Quote:
        if client_id is not None:
            quote.client_id = client_id
        if conversation_id is not None:
            quote.conversation_id = conversation_id
        if seller_id is not None:
            quote.seller_id = seller_id
        if code is not None:
            quote.code = code
        if service_type is not None:
            quote.service_type = service_type
        if title is not None:
            quote.title = title
        if description is not None:
            quote.description = description
        if subtotal is not None:
            quote.subtotal = subtotal
        if discount is not None:
            quote.discount = discount
        if total_value is not None:
            quote.total_value = total_value
        if status is not None:
            quote.status = status
        if valid_until is not None:
            quote.valid_until = valid_until
        if notes is not None:
            quote.notes = notes
        if pdf_url is not None:
            quote.pdf_url = pdf_url
        if domain_data is not None:
            quote.domain_data = domain_data

        self.db.flush()
        self.db.refresh(quote)
        return quote

    def count_company_quotes(
        self,
        company_id: int,
        *,
        status: QuoteStatus | None = None,
        client_id: int | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(Quote).where(Quote.company_id == company_id)
        if status is not None:
            stmt = stmt.where(Quote.status == status)
        if client_id is not None:
            stmt = stmt.where(Quote.client_id == client_id)
        return int(self.db.scalar(stmt) or 0)


class QuoteItemsRepository(TenantRepository[QuoteItem]):
    def __init__(self, db: Session):
        super().__init__(db, QuoteItem)

    def list_by_quote(
        self,
        *,
        company_id: int,
        quote_id: int,
    ) -> list[QuoteItem]:
        stmt = (
            select(QuoteItem)
            .where(
                QuoteItem.company_id == company_id,
                QuoteItem.quote_id == quote_id,
            )
            .order_by(QuoteItem.id.asc())
        )
        return list(self.db.scalars(stmt).all())

    def create_item(
        self,
        *,
        company_id: int,
        quote_id: int,
        description: str,
        service_type: str | None = None,
        width_cm: Decimal | None = None,
        height_cm: Decimal | None = None,
        quantity: int = 1,
        unit_price: Decimal = Decimal("0.00"),
        total_price: Decimal = Decimal("0.00"),
        status: QuoteItemStatus = QuoteItemStatus.PENDING,
        notes: str | None = None,
        domain_data: dict[str, Any] | None = None,
    ) -> QuoteItem:
        item = QuoteItem(
            company_id=company_id,
            quote_id=quote_id,
            description=description,
            service_type=service_type,
            width_cm=width_cm,
            height_cm=height_cm,
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price,
            status=status,
            notes=notes,
            domain_data=domain_data,
        )
        return self.add(item)

    def update_item(
        self,
        item: QuoteItem,
        *,
        description: str | None = None,
        service_type: str | None = None,
        width_cm: Decimal | None = None,
        height_cm: Decimal | None = None,
        quantity: int | None = None,
        unit_price: Decimal | None = None,
        total_price: Decimal | None = None,
        status: QuoteItemStatus | None = None,
        notes: str | None = None,
        domain_data: dict[str, Any] | None = None,
    ) -> QuoteItem:
        if description is not None:
            item.description = description
        if service_type is not None:
            item.service_type = service_type
        if width_cm is not None:
            item.width_cm = width_cm
        if height_cm is not None:
            item.height_cm = height_cm
        if quantity is not None:
            item.quantity = quantity
        if unit_price is not None:
            item.unit_price = unit_price
        if total_price is not None:
            item.total_price = total_price
        if status is not None:
            item.status = status
        if notes is not None:
            item.notes = notes
        if domain_data is not None:
            item.domain_data = domain_data

        self.db.flush()
        self.db.refresh(item)
        return item