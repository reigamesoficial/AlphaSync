from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    get_current_active_user,
    require_admin_seller_or_master,
    require_company_admin_or_master,
)
from app.core.tenancy import get_tenant_company_id
from app.db.connection import get_db
from app.db.models import Appointment, AppointmentStatus, CompanySettings, User, UserRole, Warranty
from app.repositories.appointments import AppointmentsRepository
from app.schemas.appointment import AppointmentCreate, AppointmentResponse, AppointmentUpdate
from app.schemas.warranty import WarrantyResponse

router = APIRouter(prefix="/appointments", tags=["Appointments"])


class StatusBody(BaseModel):
    status: AppointmentStatus
    reschedule_reason: str | None = None


class SlotResponse(BaseModel):
    start_at: str
    end_at: str
    available: bool


def _get_schedule_config(db: Session, company_id: int) -> dict:
    """Return schedule config from company extra_settings with sensible defaults."""
    cs = db.scalar(select(CompanySettings).where(CompanySettings.company_id == company_id))
    extra = (cs.extra_settings or {}) if cs else {}
    cfg = extra.get("schedule") or {}
    return {
        "slot_minutes": int(cfg.get("slot_minutes", 120)),
        "workday_start": cfg.get("workday_start", "08:00"),
        "workday_end": cfg.get("workday_end", "18:00"),
        "allowed_weekdays": list(cfg.get("allowed_weekdays", [0, 1, 2, 3, 4])),
    }


def _validate_appointment_times(
    start_at: datetime,
    end_at: datetime,
    repo: AppointmentsRepository,
    company_id: int,
    installer_id: int | None,
    exclude_id: int | None = None,
) -> None:
    """Raise HTTPException for past dates or installer conflicts."""
    now = datetime.now(timezone.utc)
    start_cmp = start_at if start_at.tzinfo is not None else start_at.replace(tzinfo=timezone.utc)
    if start_cmp < now:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Não é possível agendar em uma data/hora passada.",
        )
    if end_at <= start_at:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A data de término deve ser posterior ao início.",
        )
    if installer_id is not None:
        conflict = repo.has_installer_conflict(
            company_id=company_id,
            installer_id=installer_id,
            start_at=start_at,
            end_at=end_at,
            exclude_appointment_id=exclude_id,
        )
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="O instalador já possui um agendamento neste horário.",
            )


@router.get("/slots", response_model=list[SlotResponse])
def get_available_slots(
    date_str: str = Query(alias="date", description="Data no formato YYYY-MM-DD"),
    installer_id: int | None = Query(default=None),
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[SlotResponse]:
    """Return all time slots for a given date with availability info."""
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Data inválida. Use o formato YYYY-MM-DD.")

    cfg = _get_schedule_config(db, tenant_company_id)

    if installer_id is not None:
        cs = db.scalar(select(CompanySettings).where(CompanySettings.company_id == tenant_company_id))
        extra = (cs.extra_settings or {}) if cs else {}
        installer_schedules = extra.get("installer_schedules") or {}
        inst_cfg = installer_schedules.get(str(installer_id)) or {}
        if inst_cfg:
            cfg["workday_start"] = inst_cfg.get("work_start", cfg["workday_start"])
            cfg["workday_end"] = inst_cfg.get("work_end", cfg["workday_end"])
            cfg["allowed_weekdays"] = inst_cfg.get("allowed_weekdays", cfg["allowed_weekdays"])

    weekday = target_date.weekday()
    if weekday not in cfg["allowed_weekdays"]:
        return []

    start_h, start_m = map(int, cfg["workday_start"].split(":"))
    end_h, end_m = map(int, cfg["workday_end"].split(":"))
    slot_minutes = cfg["slot_minutes"]

    day_start = datetime(target_date.year, target_date.month, target_date.day, start_h, start_m)
    day_end = datetime(target_date.year, target_date.month, target_date.day, end_h, end_m)

    repo = AppointmentsRepository(db)
    slots: list[SlotResponse] = []
    current = day_start

    while current + timedelta(minutes=slot_minutes) <= day_end:
        slot_end = current + timedelta(minutes=slot_minutes)
        available = True

        if installer_id is not None:
            available = not repo.has_installer_conflict(
                company_id=tenant_company_id,
                installer_id=installer_id,
                start_at=current,
                end_at=slot_end,
            )

        slots.append(SlotResponse(
            start_at=current.isoformat(),
            end_at=slot_end.isoformat(),
            available=available,
        ))
        current = slot_end

    return slots


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

    start_at: datetime = data["start_at"]
    end_at: datetime = data["end_at"]
    installer_id: int | None = data.get("assigned_installer_id")

    _validate_appointment_times(start_at, end_at, repo, tenant_company_id, installer_id)

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

    new_start = updates.get("start_at", obj.start_at)
    new_end = updates.get("end_at", obj.end_at)
    new_installer_id = updates.get("assigned_installer_id", obj.assigned_installer_id)

    if "start_at" in updates or "end_at" in updates or "assigned_installer_id" in updates:
        _validate_appointment_times(
            new_start, new_end, repo, tenant_company_id, new_installer_id, exclude_id=appointment_id
        )

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


# ─── Admin warranty read endpoint ──────────────────────────────────────────────

@router.get("/{appointment_id}/warranty", response_model=WarrantyResponse)
def get_appointment_warranty(
    appointment_id: int,
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> WarrantyResponse:
    """Retorna a garantia de um atendimento (acessível por admin e instalador da empresa)."""
    repo = AppointmentsRepository(db)
    obj = repo.get_full_by_id_and_company(appointment_id, tenant_company_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agendamento não encontrado.")
    w = db.query(Warranty).filter(Warranty.appointment_id == appointment_id, Warranty.company_id == tenant_company_id).first()
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Garantia não encontrada para este atendimento.")
    return WarrantyResponse(
        id=w.id,
        created_at=w.created_at,
        updated_at=w.updated_at,
        company_id=w.company_id,
        appointment_id=w.appointment_id,
        client_id=w.client_id,
        client_name=w.client_name,
        client_phone=w.client_phone,
        address_raw=w.address_raw,
        service_description=w.service_description,
        warranty_period=w.warranty_period,
        warranty_covers=w.warranty_covers,
        additional_notes=w.additional_notes,
        signature=w.signature,
        sent_at=w.sent_at,
        sent_by_user_id=w.sent_by_user_id,
    )
