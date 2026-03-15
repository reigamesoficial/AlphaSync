from __future__ import annotations

from copy import deepcopy
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user, require_company_admin_or_master
from app.core.tenancy import get_tenant_company_id
from app.db.connection import get_db
from app.db.models import User
from app.schemas.company import CompanySettingsResponse, CompanySettingsUpdate
from app.schemas.measures import PNSettingsResponse, PNSettingsUpdate
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/company", tags=["Company"])


@router.get("/settings", response_model=CompanySettingsResponse)
def get_company_settings(
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = SettingsService(db)
    return service.get_company_settings(
        tenant_company_id=tenant_company_id,
        current_user=current_user,
    )


@router.patch("/settings", response_model=CompanySettingsResponse)
def update_company_settings(
    payload: CompanySettingsUpdate,
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(require_company_admin_or_master),
    db: Session = Depends(get_db),
):
    service = SettingsService(db)
    return service.upsert_company_settings(
        tenant_company_id=tenant_company_id,
        current_user=current_user,
        payload=payload,
    )


def _extract_pn_settings(effective: dict[str, Any]) -> PNSettingsResponse:
    pricing = effective.get("pricing_rules") or {}
    return PNSettingsResponse(
        show_measures_to_customer=bool(effective.get("show_measures_to_customer", True)),
        default_price_per_m2=float(pricing.get("default_price_per_m2", 45.0)),
        minimum_order_value=float(pricing.get("minimum_order_value", 150.0)),
        visit_fee=float(pricing.get("visit_fee", 0.0)),
        available_colors=list(effective.get("network_colors") or ["branca", "preta", "areia", "cinza"]),
        available_mesh_types=list(effective.get("mesh_types") or ["3x3", "5x5"]),
        mesh_prices=dict(effective.get("mesh_prices") or {}),
    )


@router.get("/settings/protection-network", response_model=PNSettingsResponse)
def get_pn_settings(
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PNSettingsResponse:
    service = SettingsService(db)
    effective = service.get_effective_extra_settings(
        tenant_company_id=tenant_company_id,
        current_user=current_user,
    )
    return _extract_pn_settings(effective)


@router.patch("/settings/protection-network", response_model=PNSettingsResponse)
def update_pn_settings(
    payload: PNSettingsUpdate,
    tenant_company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(require_company_admin_or_master),
    db: Session = Depends(get_db),
) -> PNSettingsResponse:
    service = SettingsService(db)

    data = payload.model_dump(exclude_unset=True)
    extra_patch: dict[str, Any] = {}

    if "show_measures_to_customer" in data:
        extra_patch["show_measures_to_customer"] = data["show_measures_to_customer"]
    if "available_colors" in data:
        extra_patch["network_colors"] = data["available_colors"]
    if "available_mesh_types" in data:
        extra_patch["mesh_types"] = data["available_mesh_types"]
    if "mesh_prices" in data:
        extra_patch["mesh_prices"] = data["mesh_prices"]

    pricing_patch: dict[str, Any] = {}
    for key in ("default_price_per_m2", "minimum_order_value", "visit_fee"):
        if key in data:
            pricing_patch[key] = data[key]
    if pricing_patch:
        extra_patch["pricing_rules"] = pricing_patch

    settings_update = CompanySettingsUpdate(extra_settings=extra_patch)
    service.upsert_company_settings(
        tenant_company_id=tenant_company_id,
        current_user=current_user,
        payload=settings_update,
    )

    effective = service.get_effective_extra_settings(
        tenant_company_id=tenant_company_id,
        current_user=current_user,
    )
    return _extract_pn_settings(effective)
