from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models import Appointment, Client


class AddressesRepository:
    def __init__(self, db: Session):
        self.db = db

    def search_client_addresses(
        self,
        *,
        company_id: int,
        query: str,
        limit: int = 20,
    ) -> list[str]:
        search_term = f"%{query.strip()}%"

        stmt = (
            select(Client.address)
            .where(
                Client.company_id == company_id,
                Client.address.is_not(None),
                Client.address.ilike(search_term),
            )
            .distinct()
            .order_by(Client.address.asc())
            .limit(limit)
        )

        return [addr for addr in self.db.scalars(stmt).all() if addr]

    def search_appointment_addresses(
        self,
        *,
        company_id: int,
        query: str,
        limit: int = 20,
    ) -> list[str]:
        search_term = f"%{query.strip()}%"

        stmt = (
            select(Appointment.address_raw)
            .where(
                Appointment.company_id == company_id,
                Appointment.address_raw.is_not(None),
                Appointment.address_raw.ilike(search_term),
            )
            .distinct()
            .order_by(Appointment.address_raw.asc())
            .limit(limit)
        )

        return [addr for addr in self.db.scalars(stmt).all() if addr]

    def search_all_addresses(
        self,
        *,
        company_id: int,
        query: str,
        limit: int = 20,
    ) -> list[str]:
        client_addresses = self.search_client_addresses(
            company_id=company_id,
            query=query,
            limit=limit,
        )
        appointment_addresses = self.search_appointment_addresses(
            company_id=company_id,
            query=query,
            limit=limit,
        )

        merged = []
        seen = set()

        for address in client_addresses + appointment_addresses:
            normalized = address.strip().lower()
            if normalized not in seen:
                seen.add(normalized)
                merged.append(address)

        return merged[:limit]