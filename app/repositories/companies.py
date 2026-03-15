from __future__ import annotations

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.db.models import Company, CompanyStatus, ServiceDomain
from app.repositories.base import BaseRepository


class CompaniesRepository(BaseRepository[Company]):
    def __init__(self, db: Session):
        super().__init__(db, Company)

    def get_by_slug(self, slug: str) -> Company | None:
        stmt = select(Company).where(func.lower(Company.slug) == slug.lower())
        return self.db.scalar(stmt)

    def get_by_whatsapp_phone_number_id(self, phone_number_id: str) -> Company | None:
        stmt = select(Company).where(Company.whatsapp_phone_number_id == phone_number_id)
        return self.db.scalar(stmt)

    def list_companies(
        self,
        *,
        search: str | None = None,
        status: CompanyStatus | None = None,
        service_domain: ServiceDomain | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Company]:
        stmt: Select[tuple[Company]] = select(Company)

        if search:
            search_term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Company.name.ilike(search_term),
                    Company.slug.ilike(search_term),
                    Company.support_email.ilike(search_term),
                )
            )

        if status is not None:
            stmt = stmt.where(Company.status == status)

        if service_domain is not None:
            stmt = stmt.where(Company.service_domain == service_domain)

        if is_active is not None:
            stmt = stmt.where(Company.is_active == is_active)

        stmt = stmt.order_by(Company.created_at.desc()).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())

    def create_company(
        self,
        *,
        slug: str,
        name: str,
        status: CompanyStatus = CompanyStatus.ACTIVE,
        service_domain: ServiceDomain = ServiceDomain.PROTECTION_NETWORK,
        plan_name: str | None = None,
        whatsapp_phone_number_id: str | None = None,
        whatsapp_business_account_id: str | None = None,
        support_email: str | None = None,
        support_phone: str | None = None,
        is_active: bool = True,
    ) -> Company:
        company = Company(
            slug=slug.strip().lower(),
            name=name.strip(),
            status=status,
            service_domain=service_domain,
            plan_name=plan_name,
            whatsapp_phone_number_id=whatsapp_phone_number_id,
            whatsapp_business_account_id=whatsapp_business_account_id,
            support_email=support_email.lower() if support_email else None,
            support_phone=support_phone,
            is_active=is_active,
        )
        return self.add(company)

    def update_company(
        self,
        company: Company,
        *,
        slug: str | None = None,
        name: str | None = None,
        status: CompanyStatus | None = None,
        service_domain: ServiceDomain | None = None,
        plan_name: str | None = None,
        whatsapp_phone_number_id: str | None = None,
        whatsapp_business_account_id: str | None = None,
        support_email: str | None = None,
        support_phone: str | None = None,
        is_active: bool | None = None,
    ) -> Company:
        if slug is not None:
            company.slug = slug.strip().lower()
        if name is not None:
            company.name = name.strip()
        if status is not None:
            company.status = status
        if service_domain is not None:
            company.service_domain = service_domain
        if plan_name is not None:
            company.plan_name = plan_name
        if whatsapp_phone_number_id is not None:
            company.whatsapp_phone_number_id = whatsapp_phone_number_id
        if whatsapp_business_account_id is not None:
            company.whatsapp_business_account_id = whatsapp_business_account_id
        if support_email is not None:
            company.support_email = support_email.lower()
        if support_phone is not None:
            company.support_phone = support_phone
        if is_active is not None:
            company.is_active = is_active

        self.db.flush()
        self.db.refresh(company)
        return company