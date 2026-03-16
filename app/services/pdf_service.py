from __future__ import annotations

from decimal import Decimal
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

_DARK = colors.HexColor("#1e293b")
_BRAND = colors.HexColor("#6366f1")
_LIGHT_BG = colors.HexColor("#f8fafc")
_BORDER = colors.HexColor("#e2e8f0")
_MUTED = colors.HexColor("#64748b")
_GREEN = colors.HexColor("#16a34a")
_RED = colors.HexColor("#dc2626")
_WHITE = colors.white


def _money(value: Any) -> str:
    try:
        v = Decimal(str(value))
        formatted = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatted}"
    except Exception:
        return "R$ 0,00"


def _dim_m(value_cm: Any) -> str:
    try:
        return f"{Decimal(str(value_cm)) / 100:.2f}".replace(".", ",")
    except Exception:
        return "—"


def _area_m2(width_cm: Any, height_cm: Any, qty: int) -> str:
    try:
        w = Decimal(str(width_cm)) / 100
        h = Decimal(str(height_cm)) / 100
        area = w * h * qty
        return f"{area:.2f}".replace(".", ",")
    except Exception:
        return "—"


def generate_quote_pdf(
    *,
    quote: Any,
    company_name: str,
    brand_name: str | None = None,
    quote_prefix: str = "ORC",
) -> bytes:
    buffer = BytesIO()
    page_w, page_h = A4
    avail_w = page_w - 4 * cm

    display_name = brand_name or company_name or "Empresa"
    quote_code = getattr(quote, "code", None) or f"{quote_prefix}-{quote.id:04d}"

    from datetime import datetime, timezone

    issued_raw = getattr(quote, "created_at", None)
    if issued_raw is None:
        issued_raw = datetime.now(timezone.utc)
    issued_str = issued_raw.strftime("%d/%m/%Y") if hasattr(issued_raw, "strftime") else str(issued_raw)[:10]

    valid_until = getattr(quote, "valid_until", None)
    valid_str = valid_until.strftime("%d/%m/%Y") if valid_until and hasattr(valid_until, "strftime") else None

    client = getattr(quote, "client", None)
    client_name = client.name if client else "—"
    client_phone = getattr(client, "phone", None) or ""

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Orçamento {quote_code}",
        author=display_name,
    )

    base = getSampleStyleSheet()["Normal"]

    def ps(name: str, **kw) -> ParagraphStyle:
        return ParagraphStyle(name, parent=base, **kw)

    s_company = ps("co", fontSize=18, textColor=_BRAND, fontName="Helvetica-Bold", spaceAfter=2)
    s_sub = ps("sub", fontSize=9, textColor=_MUTED, fontName="Helvetica")
    s_section = ps("sec", fontSize=7, textColor=_MUTED, fontName="Helvetica-Bold", spaceAfter=3)
    s_title = ps("ttl", fontSize=11, textColor=_DARK, fontName="Helvetica-Bold", spaceAfter=2)
    s_body = ps("bod", fontSize=9, textColor=_DARK, fontName="Helvetica", leading=14)
    s_muted = ps("mut", fontSize=8, textColor=_MUTED, fontName="Helvetica", leading=11)
    s_right = ps("ri", fontSize=9, textColor=_DARK, fontName="Helvetica", alignment=TA_RIGHT)
    s_right_lg = ps("ri_lg", fontSize=13, textColor=_BRAND, fontName="Helvetica-Bold", alignment=TA_RIGHT)
    s_right_bold = ps("ri_b", fontSize=11, textColor=_DARK, fontName="Helvetica-Bold", alignment=TA_RIGHT)
    s_right_green = ps("ri_g", fontSize=11, textColor=_GREEN, fontName="Helvetica-Bold", alignment=TA_RIGHT)
    s_right_red = ps("ri_r", fontSize=9, textColor=_RED, fontName="Helvetica", alignment=TA_RIGHT)
    s_center = ps("ctr", fontSize=8, textColor=_MUTED, fontName="Helvetica", alignment=TA_CENTER)
    s_th = ps("th", fontSize=8, textColor=_WHITE, fontName="Helvetica-Bold", alignment=TA_LEFT)
    s_th_r = ps("thr", fontSize=8, textColor=_WHITE, fontName="Helvetica-Bold", alignment=TA_RIGHT)
    s_td = ps("td", fontSize=8, textColor=_DARK, fontName="Helvetica", leading=11)
    s_td_r = ps("tdr", fontSize=8, textColor=_DARK, fontName="Helvetica", alignment=TA_RIGHT)
    s_td_muted = ps("tdm", fontSize=7, textColor=_MUTED, fontName="Helvetica", leading=10)

    story = []
    col_half = avail_w / 2

    header_rows: list[list] = [
        [Paragraph(display_name, s_company), Paragraph("ORÇAMENTO", s_right_lg)],
        [Paragraph("Serviços de instalação", s_sub), Paragraph(f"<b>N° {quote_code}</b>", s_right)],
        [Paragraph("", s_sub), Paragraph(f"Emitido em: {issued_str}", s_right)],
    ]
    if valid_str:
        header_rows.append([Paragraph("", s_sub), Paragraph(f"Válido até: {valid_str}", s_right)])

    header_tbl = Table(header_rows, colWidths=[col_half, col_half])
    header_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 3 * mm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=_BRAND, spaceAfter=4 * mm))

    story.append(Paragraph("DADOS DO CLIENTE", s_section))

    label_w = 2.5 * cm
    info_w = avail_w - label_w

    info_rows: list[list] = [[Paragraph("Nome", s_muted), Paragraph(client_name, s_title)]]
    if client_phone:
        info_rows.append([Paragraph("Telefone", s_muted), Paragraph(client_phone, s_body)])
    quote_title = str(getattr(quote, "title", None) or "")
    if quote_title:
        info_rows.append([Paragraph("Serviço", s_muted), Paragraph(quote_title, s_body)])

    info_tbl = Table(info_rows, colWidths=[label_w, info_w - 0.3 * cm])
    info_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
        ("LEFTPADDING", (1, 0), (1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))

    client_box = Table([[info_tbl]], colWidths=[avail_w])
    client_box.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, _BORDER),
        ("BACKGROUND", (0, 0), (-1, -1), _LIGHT_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(client_box)
    story.append(Spacer(1, 5 * mm))

    items = list(getattr(quote, "items", []) or [])
    if items:
        story.append(Paragraph("ITENS DO ORÇAMENTO", s_section))

        cw = [avail_w * r for r in (0.38, 0.13, 0.07, 0.12, 0.14, 0.16)]

        tbl_data: list[list] = [[
            Paragraph("Descrição", s_th),
            Paragraph("Dim. (m)", s_th),
            Paragraph("Qtd", s_th_r),
            Paragraph("Área m²", s_th_r),
            Paragraph("Preço/m²", s_th_r),
            Paragraph("Total", s_th_r),
        ]]

        for it in items:
            desc = str(getattr(it, "description", "") or "—")
            qty = int(getattr(it, "quantity", 1) or 1)
            w_cm = getattr(it, "width_cm", None)
            h_cm = getattr(it, "height_cm", None)
            unit_p = getattr(it, "unit_price", Decimal("0.00"))
            total_p = getattr(it, "total_price", Decimal("0.00"))
            it_notes = str(getattr(it, "notes", None) or "")

            dim_str = f"{_dim_m(w_cm)} × {_dim_m(h_cm)}" if w_cm and h_cm else "—"
            area_str = _area_m2(w_cm, h_cm, qty) if w_cm and h_cm else "—"

            desc_cell: list = [Paragraph(desc[:70], s_td)]
            if it_notes:
                desc_cell.append(Paragraph(it_notes[:90], s_td_muted))

            tbl_data.append([
                desc_cell,
                Paragraph(dim_str, s_td),
                Paragraph(str(qty), s_td_r),
                Paragraph(area_str, s_td_r),
                Paragraph(_money(unit_p), s_td_r),
                Paragraph(_money(total_p), s_td_r),
            ])

        items_tbl = Table(tbl_data, colWidths=cw)
        items_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), _WHITE),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("TOPPADDING", (0, 1), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_WHITE, _LIGHT_BG]),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, _BRAND),
            ("LINEBELOW", (0, -1), (-1, -1), 1, _BORDER),
            ("LINEAFTER", (0, 0), (-2, -1), 0.3, _BORDER),
            ("BOX", (0, 0), (-1, -1), 0.5, _BORDER),
        ]))
        story.append(items_tbl)
        story.append(Spacer(1, 4 * mm))

    subtotal = Decimal(str(getattr(quote, "subtotal", "0.00") or "0.00"))
    discount = Decimal(str(getattr(quote, "discount", "0.00") or "0.00"))
    total_value = Decimal(str(getattr(quote, "total_value", "0.00") or "0.00"))

    fin_lw = avail_w * 0.22
    fin_vw = avail_w * 0.18
    spacer_w = avail_w - fin_lw - fin_vw

    fin_rows: list[list] = [
        [Paragraph("Subtotal", s_right), Paragraph(_money(subtotal), s_right)],
    ]
    if discount > 0:
        fin_rows.append([Paragraph("Desconto", s_right), Paragraph(f"- {_money(discount)}", s_right_red)])
    fin_rows.append([
        Paragraph("<b>TOTAL</b>", s_right_bold),
        Paragraph(f"<b>{_money(total_value)}</b>", s_right_green),
    ])

    fin_tbl = Table(fin_rows, colWidths=[fin_lw, fin_vw])
    fin_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("LINEABOVE", (0, -1), (-1, -1), 0.8, _BORDER),
        ("BACKGROUND", (0, -1), (-1, -1), _LIGHT_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, _BORDER),
    ]))

    fin_outer = Table([[Paragraph("", s_body), fin_tbl]], colWidths=[spacer_w, fin_lw + fin_vw])
    fin_outer.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(fin_outer)

    notes = str(getattr(quote, "notes", None) or "")
    if notes:
        story.append(Spacer(1, 5 * mm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=_BORDER, spaceAfter=3 * mm))
        story.append(Paragraph("OBSERVAÇÕES", s_section))
        story.append(Paragraph(notes, s_body))

    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_BORDER, spaceAfter=3 * mm))
    story.append(Paragraph(f"Documento gerado em {issued_str} · {display_name}", s_center))

    doc.build(story)
    return buffer.getvalue()
