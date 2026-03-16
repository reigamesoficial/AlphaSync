from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.security import (
    get_current_active_user,
    require_admin_seller_or_master,
    require_company_admin_or_master,
)
from app.core.tenancy import get_tenant_company_id
from app.db.connection import get_db
from app.db.models import Appointment, AppointmentStatus, User, UserRole
from app.repositories.appointments import AppointmentsRepository
from app.schemas.appointment import AppointmentCreate, AppointmentResponse, AppointmentUpdate

router = APIRouter(prefix="/appointments", tags=["Appointments"])


class AppointmentStatusUpdate:
    from pydantic import BaseModel as _Base

    class Body(_Base):
        status: AppointmentStatus
        reschedule_reason: str | None = None


from pydantic import BaseModel


class StatusBody(BaseModel):
    status: AppointmentStatus
    reschedule_reason: str | None = None


@router.get("", response_model=list[AppointmentResponse])
def list_appointments(
    assigned_installer_id: int | None = Query(default=None),
    client_id: int | None = Query(default=None),
    status: AppointmentStatus | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[AppointmentResponse]:
    repo = AppointmentsRepository(db)
    items = repo.list_company_appointments(
        tenant_company_id,
        assigned_installer_id=assigned_installer_id,
        client_id=client_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [AppointmentResponse.model_validate(a) for a in items]


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: int,
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AppointmentResponse:
    repo = AppointmentsRepository(db)
    obj = repo.get_full_by_id_and_company(appointment_id, tenant_company_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agendamento não encontrado.")
    return AppointmentResponse.model_validate(obj)


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(
    payload: AppointmentCreate,
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(require_admin_seller_or_master),
    db: Session = Depends(get_db),
) -> AppointmentResponse:
    repo = AppointmentsRepository(db)
    data = payload.model_dump()
    data["company_id"] = tenant_company_id
    obj = Appointment(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    fresh = repo.get_full_by_id_and_company(obj.id, tenant_company_id)
    return AppointmentResponse.model_validate(fresh)


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
    appointment_id: int,
    payload: AppointmentUpdate,
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(require_company_admin_or_master),
    db: Session = Depends(get_db),
) -> AppointmentResponse:
    repo = AppointmentsRepository(db)
    obj = repo.get_full_by_id_and_company(appointment_id, tenant_company_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agendamento não encontrado.")
    updates = payload.model_dump(exclude_unset=True)
    for key, val in updates.items():
        setattr(obj, key, val)
    db.commit()
    fresh = repo.get_full_by_id_and_company(obj.id, tenant_company_id)
    return AppointmentResponse.model_validate(fresh)


@router.patch("/{appointment_id}/status", response_model=AppointmentResponse)
def update_appointment_status(
    appointment_id: int,
    body: StatusBody,
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(require_admin_seller_or_master),
    db: Session = Depends(get_db),
) -> AppointmentResponse:
    repo = AppointmentsRepository(db)
    obj = repo.get_full_by_id_and_company(appointment_id, tenant_company_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agendamento não encontrado.")
    obj.status = body.status
    if body.reschedule_reason is not None:
        obj.reschedule_reason = body.reschedule_reason
    db.commit()
    fresh = repo.get_full_by_id_and_company(obj.id, tenant_company_id)
    return AppointmentResponse.model_validate(fresh)


@router.delete("/{appointment_id}")
def delete_appointment(
    appointment_id: int,
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(require_company_admin_or_master),
    db: Session = Depends(get_db),
) -> Response:
    repo = AppointmentsRepository(db)
    obj = repo.get_full_by_id_and_company(appointment_id, tenant_company_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agendamento não encontrado.")
    db.delete(obj)
    db.commit()
    return Response(status_code=204)
