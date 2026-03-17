from __future__ import annotations

from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.core.tenancy import get_tenant_company_id
from app.db.connection import get_db
from app.db.models import (
    Company,
    ConversationMessage,
    ConversationStatus,
    Quote,
    QuoteItem,
    QuoteStatus,
    User,
    UserRole,
)
from app.repositories.conversations import ConversationsRepository
from app.schemas.common import PaginatedResponse
from app.schemas.conversation import ConversationMessageResponse, ConversationResponse

router = APIRouter(prefix="/conversations", tags=["Conversations"])


class GenerateQuoteItemM2(BaseModel):
    description: str = Field(min_length=1, max_length=200)
    width_m: float = Field(gt=0)
    height_m: float = Field(gt=0)
    quantity: int = Field(default=1, ge=1)
    duration_minutes: int | None = Field(default=None, ge=1)


class GenerateQuoteRequestM2(BaseModel):
    mode: Literal["m2"]
    items: list[GenerateQuoteItemM2] = Field(min_length=1)
    color: str | None = None
    mesh: str = "3x3"
    notes: str | None = None


class GenerateQuoteRequestManual(BaseModel):
    mode: Literal["manual"]
    description: str = Field(min_length=1, max_length=500)
    value: float = Field(gt=0)
    duration_minutes: int | None = Field(default=None, ge=1)
    notes: str | None = None


class GenerateQuoteResponse(BaseModel):
    quote_id: int
    total_value: float
    items_count: int


class ReturnToBotResponse(BaseModel):
    ok: bool
    message: str


@router.get("", response_model=PaginatedResponse[ConversationResponse])
def list_conversations(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    status: ConversationStatus | None = Query(default=None),
    search: str | None = Query(default=None, description="Busca por telefone ou assunto"),
    assigned_to_id: int | None = Query(default=None),
    company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo = ConversationsRepository(db)
    offset = (page - 1) * per_page
    items = repo.list_company_conversations(
        company_id,
        status=status,
        assigned_to_id=assigned_to_id,
        search=search,
        limit=per_page,
        offset=offset,
    )
    total = repo.count_company_conversations(company_id, status=status, search=search)
    return PaginatedResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: int,
    company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo = ConversationsRepository(db)
    conv = repo.get_full_by_id_and_company(conversation_id, company_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversa não encontrada.")
    return conv


@router.get("/{conversation_id}/messages", response_model=list[ConversationMessageResponse])
def list_conversation_messages(
    conversation_id: int,
    company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo = ConversationsRepository(db)
    conv = repo.get_by_id_and_company(conversation_id, company_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversa não encontrada.")

    stmt = (
        select(ConversationMessage)
        .where(
            ConversationMessage.conversation_id == conversation_id,
            ConversationMessage.company_id == company_id,
        )
        .order_by(ConversationMessage.created_at.asc())
    )
    return list(db.scalars(stmt).all())


@router.post("/trigger-24h-check", tags=["Conversations"])
def trigger_24h_window_check(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Dispara a verificação da janela de 24h do WhatsApp para todas as empresas.
    Envia mensagens de reengajamento para conversas prestes a perder a janela.

    Acesso: company_admin ou master_admin.
    Ideal para chamar via cron a cada 30 minutos.
    """
    if current_user.role not in (UserRole.MASTER_ADMIN, UserRole.COMPANY_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado.",
        )

    from app.services.whatsapp_window_service import check_and_nudge_expiring_windows

    stats = check_and_nudge_expiring_windows(db)
    return {
        "ok": True,
        "stats": stats,
        "message": f"Verificação concluída. {stats.get('nudged', 0)} nudges enviados.",
    }


@router.post("/{conversation_id}/generate-quote", response_model=GenerateQuoteResponse, tags=["Conversations"])
def generate_quote_from_conversation(
    conversation_id: int,
    body: GenerateQuoteRequestM2 | GenerateQuoteRequestManual,
    company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> GenerateQuoteResponse:
    if current_user.role not in (UserRole.MASTER_ADMIN, UserRole.COMPANY_ADMIN, UserRole.SELLER):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")

    repo = ConversationsRepository(db)
    conv = repo.get_full_by_id_and_company(conversation_id, company_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversa não encontrada.")

    company = db.scalar(select(Company).where(Company.id == company_id))
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada.")

    from app.domains.protection_network.pricing import (
        get_effective_price_per_m2,
        get_effective_settings,
        normalize_mesh,
        _money,
        _to_decimal,
    )

    if body.mode == "m2":
        mesh = normalize_mesh(body.mesh)
        color = body.color
        price_per_m2 = get_effective_price_per_m2(company=company, mesh_type=mesh, color=color)

        quote_items_data: list[dict] = []
        subtotal = Decimal("0.00")
        for it in body.items:
            width = _to_decimal(it.width_m)
            height = _to_decimal(it.height_m)
            area = _money(width * height * it.quantity)
            total_price = _money(area * price_per_m2)
            subtotal += total_price
            quote_items_data.append({
                "description": it.description,
                "width_cm": width,
                "height_cm": height,
                "quantity": it.quantity,
                "duration_minutes": it.duration_minutes,
                "unit_price": price_per_m2,
                "total_price": total_price,
                "service_type": "protection_network",
                "notes": f"Malha {mesh} | Cor {color or 'padrão'} | Área {area} m²",
                "domain_data": {
                    "mesh_type": mesh,
                    "color": color,
                    "area_m2": str(area),
                    "price_per_m2": str(price_per_m2),
                    "source": "seller_panel",
                },
            })

        cfg = get_effective_settings(company)
        visit_fee = _money(_to_decimal(cfg["visit_fee"]))
        min_order = _money(_to_decimal(cfg["minimum_order_value"]))
        total_value = _money(subtotal + visit_fee)
        if total_value < min_order:
            total_value = min_order

    else:
        total_value = _money(Decimal(str(body.value)))
        subtotal = total_value
        visit_fee = Decimal("0.00")
        quote_items_data = [{
            "description": body.description,
            "width_cm": None,
            "height_cm": None,
            "quantity": 1,
            "duration_minutes": body.duration_minutes,
            "unit_price": total_value,
            "total_price": total_value,
            "service_type": "protection_network",
            "notes": body.notes or "",
            "domain_data": {"source": "seller_panel", "mode": "manual"},
        }]

    quote = Quote(
        company_id=company_id,
        client_id=conv.client_id,
        conversation_id=conversation_id,
        seller_id=current_user.id,
        service_type="protection_network",
        title=f"Orçamento – {conv.client.name if conv.client else 'Cliente'}",
        description=getattr(body, "notes", None),
        subtotal=subtotal,
        discount=Decimal("0.00"),
        total_value=total_value,
        status=QuoteStatus.DRAFT,
        notes=getattr(body, "notes", None),
    )
    db.add(quote)
    db.flush()

    for item_data in quote_items_data:
        qi = QuoteItem(
            quote_id=quote.id,
            company_id=company_id,
            description=item_data["description"],
            service_type=item_data["service_type"],
            width_cm=item_data["width_cm"],
            height_cm=item_data["height_cm"],
            quantity=item_data["quantity"],
            duration_minutes=item_data.get("duration_minutes"),
            unit_price=item_data["unit_price"],
            total_price=item_data["total_price"],
            notes=item_data["notes"],
            domain_data=item_data["domain_data"],
        )
        db.add(qi)

    db.commit()
    db.refresh(quote)

    return GenerateQuoteResponse(
        quote_id=quote.id,
        total_value=float(total_value),
        items_count=len(quote_items_data),
    )


@router.post("/{conversation_id}/return-to-bot", response_model=ReturnToBotResponse, tags=["Conversations"])
def return_conversation_to_bot(
    conversation_id: int,
    company_id: int = Depends(get_tenant_company_id),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ReturnToBotResponse:
    """
    Retorna uma conversa em atendimento humano (ASSUMED) de volta ao bot.
    Define status=BOT e bot_step=schedule_ask, depois envia uma mensagem
    ao cliente via WhatsApp notificando que o orçamento está pronto.
    """
    if current_user.role not in (UserRole.MASTER_ADMIN, UserRole.COMPANY_ADMIN, UserRole.SELLER):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")

    repo = ConversationsRepository(db)
    conv = repo.get_full_by_id_and_company(conversation_id, company_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversa não encontrada.")

    company = db.scalar(select(Company).where(Company.id == company_id))
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada.")

    from app.db.models import ConversationStatus as _CS, Conversation as _Conv
    conv_obj = db.scalar(
        select(_Conv).where(_Conv.id == conversation_id, _Conv.company_id == company_id)
    )
    if not conv_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversa não encontrada.")

    conv_obj.status = _CS.BOT
    conv_obj.bot_step = "schedule_ask"
    db.add(conv_obj)

    sent_wa = False
    try:
        access_token = company.settings.whatsapp_access_token if company.settings else None
        phone_id = company.whatsapp_phone_number_id
        if access_token and phone_id and conv_obj.phone:
            from app.services.whatsapp_service import WhatsAppService
            WhatsAppService().send_text(
                access_token=access_token,
                phone_number_id=phone_id,
                to=conv_obj.phone,
                body=(
                    "Olá! Seu orçamento já está pronto 😊\n\n"
                    "Deseja agendar a instalação agora? Responda *Sim* para continuar."
                ),
            )
            sent_wa = True
    except Exception:
        pass

    db.commit()

    msg = "Conversa retornada ao bot com sucesso."
    if sent_wa:
        msg += " Cliente notificado via WhatsApp."
    return ReturnToBotResponse(ok=True, message=msg)
