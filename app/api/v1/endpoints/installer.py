from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import require_installer
from app.core.tenancy import get_tenant_company_id
from app.db.connection import get_db
from app.db.models import AppointmentStatus, User
from app.repositories.appointments import AppointmentsRepository
from app.schemas.appointment import AppointmentResponse
from pydantic import BaseModel

router = APIRouter(prefix="/installer", tags=["Installer"])


class InstallerStatusBody(BaseModel):
    status: AppointmentStatus
    reschedule_reason: str | None = None


@router.get("/appointments", response_model=list[AppointmentResponse])
def list_my_appointments(
    status: AppointmentStatus | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(require_installer),
    db: Session = Depends(get_db),
) -> list[AppointmentResponse]:
    repo = AppointmentsRepository(db)
    items = repo.list_company_appointments(
        tenant_company_id,
        assigned_installer_id=current_user.id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [AppointmentResponse.model_validate(a) for a in items]


@router.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
def get_my_appointment(
    appointment_id: int,
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(require_installer),
    db: Session = Depends(get_db),
) -> AppointmentResponse:
    repo = AppointmentsRepository(db)
    obj = repo.get_full_by_id_and_company(appointment_id, tenant_company_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Atendimento não encontrado.")
    if obj.assigned_installer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem acesso a este atendimento.",
        )
    return AppointmentResponse.model_validate(obj)


@router.patch("/appointments/{appointment_id}/status", response_model=AppointmentResponse)
def update_my_appointment_status(
    appointment_id: int,
    body: InstallerStatusBody,
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(require_installer),
    db: Session = Depends(get_db),
) -> AppointmentResponse:
    repo = AppointmentsRepository(db)
    obj = repo.get_full_by_id_and_company(appointment_id, tenant_company_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Atendimento não encontrado.")
    if obj.assigned_installer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem acesso a este atendimento.",
        )
    obj.status = body.status
    if body.reschedule_reason is not None:
        obj.reschedule_reason = body.reschedule_reason
    db.commit()
    fresh = repo.get_full_by_id_and_company(obj.id, tenant_company_id)
    return AppointmentResponse.model_validate(fresh)
