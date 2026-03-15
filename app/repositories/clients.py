from __future__ import annotations

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.db.models import Client, ClientLeadSource, ClientStatus
from app.repositories.base import TenantRepository


class ClientsRepository(TenantRepository[Client]):
    def __init__(self, db: Session):
        super().__init__(db, Client)

    def get_by_phone(self, *, company_id: int, phone: str) -> Client | None:
        stmt = select(Client).where(
            Client.company_id == company_id,
            Client.phone == phone,
        )
        return self.db.scalar(stmt)

    def get_by_whatsapp_id(self, *, company_id: int, whatsapp_id: str) -> Client | None:
        stmt = select(Client).where(
            Client.company_id == company_id,
            Client.whatsapp_id == whatsapp_id,
        )
        return self.db.scalar(stmt)

    def list_company_clients(
        self,
        company_id: int,
        *,
        search: str | None = None,
        status: ClientStatus | None = None,
        lead_source: ClientLeadSource | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Client]:
        stmt: Select[tuple[Client]] = select(Client).where(Client.company_id == company_id)

        if search:
            search_term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Client.name.ilike(search_term),
                    Client.phone.ilike(search_term),
                    Client.email.ilike(search_term),
                )
            )

        if status is not None:
            stmt = stmt.where(Client.status == status)

        if lead_source is not None:
            stmt = stmt.where(Client.lead_source == lead_source)

        stmt = stmt.order_by(Client.created_at.desc()).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())

    def create_client(
        self,
        *,
        company_id: int,
        name: str,
        phone: str,
        whatsapp_id: str | None = None,
        email: str | None = None,
        address: str | None = None,
        lead_source: ClientLeadSource = ClientLeadSource.WHATSAPP,
        status: ClientStatus = ClientStatus.LEAD,
        notes: str | None = None,
    ) -> Client:
        client = Client(
            company_id=company_id,
            name=name.strip(),
            phone=phone,
            whatsapp_id=whatsapp_id,
            email=email,
            address=address,
            lead_source=lead_source,
            status=status,
            notes=notes,
        )
        return self.add(client)

    def update_client(
        self,
        client: Client,
        *,
        name: str | None = None,
        phone: str | None = None,
        whatsapp_id: str | None = None,
        email: str | None = None,
        address: str | None = None,
        lead_source: ClientLeadSource | None = None,
        status: ClientStatus | None = None,
        notes: str | None = None,
    ) -> Client:
        if name is not None:
            client.name = name.strip()
        if phone is not None:
            client.phone = phone
        if whatsapp_id is not None:
            client.whatsapp_id = whatsapp_id
        if email is not None:
            client.email = email
        if address is not None:
            client.address = address
        if lead_source is not None:
            client.lead_source = lead_source
        if status is not None:
            client.status = status
        if notes is not None:
            client.notes = notes

        self.db.flush()
        self.db.refresh(client)
        return client

    def count_company_clients(self, company_id: int) -> int:
        stmt = select(func.count()).select_from(Client).where(Client.company_id == company_id)
        return int(self.db.scalar(stmt) or 0)