from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.tenancy import get_tenant_company_or_404
from app.db.models import User
from app.repositories.companies import CompaniesRepository
from app.schemas.company import CompanyResponse


class CompanyService:
    def __init__(self, db: Session):
        self.db = db
        self.companies_repo = CompaniesRepository(db)

    def get_current_company(
        self,
        *,
        tenant_company_id: int,
        current_user: User,
    ) -> CompanyResponse:
        company = self.companies_repo.get_by_id(tenant_company_id)
        company = get_tenant_company_or_404(
            current_user=current_user,
            company=company,
            tenant_company_id=tenant_company_id,
        )
        return CompanyResponse.model_validate(company)

    def get_company_by_id(
        self,
        *,
        company_id: int,
        tenant_company_id: int,
        current_user: User,
    ) -> CompanyResponse:
        company = self.companies_repo.get_by_id(company_id)
        company = get_tenant_company_or_404(
            current_user=current_user,
            company=company,
            tenant_company_id=tenant_company_id,
        )
        return CompanyResponse.model_validate(company)