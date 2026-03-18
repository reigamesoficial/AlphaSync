from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.security import require_installer
from app.core.tenancy import get_tenant_company_id
from app.db.connection import get_db
from app.db.models import AppointmentStatus, Company, CompanySettings, User, Warranty
from app.repositories.appointments import AppointmentsRepository
from app.schemas.appointment import AppointmentResponse, InstallerAppointmentResponse
from app.schemas.warranty import WarrantyResponse
from app.services import warranty_service
from pydantic import BaseModel

router = APIRouter(prefix="/installer", tags=["Installer"])


class InstallerStatusBody(BaseModel):
    status: AppointmentStatus
    reschedule_reason: str | None = None


def _to_installer_response(appt: any) -> InstallerAppointmentResponse:  # type: ignore[valid-type]
    data = AppointmentResponse.model_validate(appt).model_dump()
    client = appt.client
    warranty = appt.warranty
    data["client_name"] = client.name if client else None
    data["client_phone"] = client.phone if client else None
    data["client_address"] = client.address if client else None
    data["has_warranty"] = warranty is not None
    data["warranty_id"] = warranty.id if warranty else None
    return InstallerAppointmentResponse(**data)


@router.get("/appointments", response_model=list[InstallerAppointmentResponse])
def list_my_appointments(
    status: AppointmentStatus | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(require_installer),
    db: Session = Depends(get_db),
) -> list[InstallerAppointmentResponse]:
    repo = AppointmentsRepository(db)
    items = repo.list_company_appointments(
        tenant_company_id,
        assigned_installer_id=current_user.id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [_to_installer_response(a) for a in items]


@router.get("/appointments/{appointment_id}", response_model=InstallerAppointmentResponse)
def get_my_appointment(
    appointment_id: int,
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(require_installer),
    db: Session = Depends(get_db),
) -> InstallerAppointmentResponse:
    repo = AppointmentsRepository(db)
    obj = repo.get_full_by_id_and_company(appointment_id, tenant_company_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Atendimento não encontrado.")
    if obj.assigned_installer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem acesso a este atendimento.",
        )
    return _to_installer_response(obj)


@router.patch("/appointments/{appointment_id}/status", response_model=InstallerAppointmentResponse)
def update_my_appointment_status(
    appointment_id: int,
    body: InstallerStatusBody,
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(require_installer),
    db: Session = Depends(get_db),
) -> InstallerAppointmentResponse:
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
    return _to_installer_response(fresh)


# ─── Warranty endpoints ────────────────────────────────────────────────────────

@router.post("/appointments/{appointment_id}/warranty", response_model=WarrantyResponse, status_code=status.HTTP_201_CREATED)
def create_warranty(
    appointment_id: int,
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(require_installer),
    db: Session = Depends(get_db),
) -> WarrantyResponse:
    """Gera (ou retorna existente) a garantia para um atendimento concluído."""
    repo = AppointmentsRepository(db)
    obj = repo.get_full_by_id_and_company(appointment_id, tenant_company_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Atendimento não encontrado.")
    if obj.assigned_installer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Você não tem acesso a este atendimento.")
    if obj.status != AppointmentStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="O atendimento precisa estar concluído para gerar a garantia.")

    try:
        w = warranty_service.get_or_create_warranty(db, obj, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return _warranty_to_response(w)


@router.get("/appointments/{appointment_id}/warranty", response_model=WarrantyResponse)
def get_warranty(
    appointment_id: int,
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(require_installer),
    db: Session = Depends(get_db),
) -> WarrantyResponse:
    """Retorna a garantia existente de um atendimento."""
    repo = AppointmentsRepository(db)
    obj = repo.get_full_by_id_and_company(appointment_id, tenant_company_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Atendimento não encontrado.")
    if obj.assigned_installer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Você não tem acesso a este atendimento.")

    w = db.query(Warranty).filter(Warranty.appointment_id == appointment_id).first()
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Garantia não encontrada para este atendimento.")

    return _warranty_to_response(w)


@router.get("/appointments/{appointment_id}/warranty/pdf")
def download_warranty_pdf(
    appointment_id: int,
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(require_installer),
    db: Session = Depends(get_db),
) -> Response:
    """Gera e retorna o PDF da garantia como download."""
    repo = AppointmentsRepository(db)
    obj = repo.get_full_by_id_and_company(appointment_id, tenant_company_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Atendimento não encontrado.")
    if obj.assigned_installer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Você não tem acesso a este atendimento.")

    w = db.query(Warranty).filter(Warranty.appointment_id == appointment_id).first()
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gere a garantia primeiro.")

    cs = db.query(CompanySettings).filter(CompanySettings.company_id == tenant_company_id).first()
    brand_name = (cs.extra_settings or {}).get("brand_name") if cs else None
    company = db.query(Company).filter(Company.id == tenant_company_id).first()
    brand = brand_name or (company.name if company else "AlphaSync")

    pdf_buf = warranty_service.generate_warranty_pdf(w, brand_name=brand)
    filename = f"garantia-{w.id:06d}.pdf"
    return Response(
        content=pdf_buf.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _warranty_to_response(w: Warranty) -> WarrantyResponse:
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
