from __future__ import annotations

import logging
from io import BytesIO
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session

from app.db.models import Appointment, AppointmentStatus, CompanySettings, User, Warranty

logger = logging.getLogger("alphasync.warranty")

_DARK = colors.HexColor("#1e293b")
_BRAND = colors.HexColor("#6366f1")
_GREEN = colors.HexColor("#16a34a")
_LIGHT_BG = colors.HexColor("#f8fafc")
_BORDER = colors.HexColor("#e2e8f0")
_MUTED = colors.HexColor("#64748b")
_WHITE = colors.white

_DEFAULT_CONFIG: dict[str, str] = {
    "service_description": "Serviço de instalação profissional realizado conforme especificações acordadas.",
    "warranty_period": "12 meses",
    "warranty_covers": "Defeitos de instalação e falhas de fixação originadas do serviço prestado.",
    "additional_notes": "",
    "signature": "",
}


def _get_warranty_config(db: Session, company_id: int) -> dict[str, str]:
    cs = db.query(CompanySettings).filter(CompanySettings.company_id == company_id).first()
    extra: dict[str, Any] = cs.extra_settings if cs else {}
    cfg = extra.get("warranty", {})
    result = dict(_DEFAULT_CONFIG)
    for k in _DEFAULT_CONFIG:
        if cfg.get(k):
            result[k] = cfg[k]
    return result


def get_or_create_warranty(
    db: Session,
    appointment: Appointment,
    current_user: User,
) -> Warranty:
    """Return existing warranty or create a new one using company config defaults."""
    existing = db.query(Warranty).filter(Warranty.appointment_id == appointment.id).first()
    if existing:
        return existing

    if appointment.status != AppointmentStatus.COMPLETED:
        raise ValueError("Só é possível gerar garantia para atendimentos concluídos.")

    cfg = _get_warranty_config(db, appointment.company_id)
    client = appointment.client

    w = Warranty(
        company_id=appointment.company_id,
        appointment_id=appointment.id,
        client_id=appointment.client_id,
        client_name=client.name,
        client_phone=client.phone,
        address_raw=appointment.address_raw or client.address,
        service_description=cfg["service_description"],
        warranty_period=cfg["warranty_period"],
        warranty_covers=cfg["warranty_covers"],
        additional_notes=cfg["additional_notes"] or None,
        signature=cfg["signature"] or None,
        sent_by_user_id=current_user.id,
    )
    db.add(w)
    db.commit()
    db.refresh(w)
    logger.info("Warranty created: id=%s appointment=%s company=%s", w.id, appointment.id, appointment.company_id)
    return w


def generate_warranty_pdf(warranty: Warranty, brand_name: str = "AlphaSync") -> BytesIO:
    """Generate a professional PDF warranty document."""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    def S(name: str, **kw: Any) -> ParagraphStyle:
        base = styles["Normal"]
        return ParagraphStyle(name, parent=base, **kw)

    title_style = S("title", fontSize=20, textColor=_DARK, alignment=TA_CENTER, fontName="Helvetica-Bold", spaceAfter=4)
    subtitle_style = S("subtitle", fontSize=11, textColor=_MUTED, alignment=TA_CENTER, spaceAfter=4)
    section_header_style = S("sec", fontSize=10, textColor=_BRAND, fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=4)
    body_style = S("body", fontSize=10, textColor=_DARK, leading=16, spaceAfter=4)
    label_style = S("label", fontSize=9, textColor=_MUTED, fontName="Helvetica-Bold", spaceAfter=2)
    value_style = S("value", fontSize=10, textColor=_DARK, leading=14, spaceAfter=6)
    footer_style = S("footer", fontSize=9, textColor=_MUTED, alignment=TA_CENTER)

    content = []

    # ── Header ──────────────────────────────────────────────────────
    content.append(Paragraph(brand_name, title_style))
    content.append(Paragraph("CERTIFICADO DE GARANTIA", subtitle_style))
    content.append(Spacer(1, 0.3 * cm))
    content.append(HRFlowable(width="100%", thickness=2, color=_BRAND))
    content.append(Spacer(1, 0.5 * cm))

    # ── Client info ──────────────────────────────────────────────────
    content.append(Paragraph("DADOS DO CLIENTE", section_header_style))
    client_data = [
        ["Cliente:", warranty.client_name, "Telefone:", warranty.client_phone],
        ["Endereço:", warranty.address_raw or "—", "", ""],
    ]
    t = Table(client_data, colWidths=[3 * cm, 8 * cm, 2.5 * cm, 4 * cm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), _MUTED),
        ("TEXTCOLOR", (2, 0), (2, -1), _MUTED),
        ("TEXTCOLOR", (1, 0), (1, -1), _DARK),
        ("TEXTCOLOR", (3, 0), (3, -1), _DARK),
        ("SPAN", (1, 1), (3, 1)),
        ("BACKGROUND", (0, 0), (-1, -1), _LIGHT_BG),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [_LIGHT_BG, _WHITE]),
        ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    content.append(t)
    content.append(Spacer(1, 0.5 * cm))

    # ── Warranty details ─────────────────────────────────────────────
    content.append(Paragraph("DETALHES DA GARANTIA", section_header_style))

    content.append(Paragraph("Serviço realizado:", label_style))
    content.append(Paragraph(warranty.service_description, body_style))
    content.append(Spacer(1, 0.2 * cm))

    content.append(Paragraph("Prazo de garantia:", label_style))

    period_tbl = Table([[Paragraph(warranty.warranty_period, S("period", fontSize=14, textColor=_GREEN, fontName="Helvetica-Bold", alignment=TA_CENTER))]], colWidths=["100%"])
    period_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
        ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#bbf7d0")),
        ("PADDING", (0, 0), (-1, -1), 10),
    ]))
    content.append(period_tbl)
    content.append(Spacer(1, 0.3 * cm))

    content.append(Paragraph("O que a garantia cobre:", label_style))
    content.append(Paragraph(warranty.warranty_covers, body_style))

    if warranty.additional_notes:
        content.append(Spacer(1, 0.2 * cm))
        content.append(Paragraph("Observações adicionais:", label_style))
        content.append(Paragraph(warranty.additional_notes, body_style))

    content.append(Spacer(1, 0.5 * cm))
    content.append(HRFlowable(width="100%", thickness=0.5, color=_BORDER))
    content.append(Spacer(1, 0.3 * cm))

    # ── Issue date ───────────────────────────────────────────────────
    issued = (warranty.created_at or datetime.utcnow()).strftime("%d/%m/%Y")
    issue_data = [
        [
            Paragraph("Data de emissão:", label_style),
            Paragraph(issued, value_style),
            Paragraph("Nº da Garantia:", label_style),
            Paragraph(f"GAR-{warranty.id:06d}", value_style),
        ]
    ]
    it = Table(issue_data, colWidths=[3.5 * cm, 5 * cm, 3.5 * cm, 5 * cm])
    it.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    content.append(it)

    # ── Signature ────────────────────────────────────────────────────
    if warranty.signature:
        content.append(Spacer(1, 1.5 * cm))
        content.append(HRFlowable(width="40%", thickness=0.5, color=_BORDER, hAlign="CENTER"))
        content.append(Spacer(1, 0.2 * cm))
        content.append(Paragraph(warranty.signature, S("sig", fontSize=9, textColor=_MUTED, alignment=TA_CENTER)))

    # ── Footer ───────────────────────────────────────────────────────
    content.append(Spacer(1, 0.8 * cm))
    content.append(HRFlowable(width="100%", thickness=0.5, color=_BORDER))
    content.append(Spacer(1, 0.2 * cm))
    content.append(Paragraph(
        f"Documento emitido por {brand_name} · GAR-{warranty.id:06d} · {issued}",
        footer_style,
    ))

    doc.build(content)
    buf.seek(0)
    return buf
