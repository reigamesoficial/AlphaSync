from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db.models import (
    Client,
    ClientLeadSource,
    ClientStatus,
    Company,
    Conversation,
    ConversationChannel,
    ConversationStatus,
    MessageDirection,
    MessageType,
    Quote,
    QuoteItem,
    QuoteItemStatus,
    QuoteStatus,
)
from app.domains.engine import domain_engine
from app.repositories.clients import ClientsRepository
from app.repositories.company_settings import CompanySettingsRepository
from app.repositories.conversations import (
    ChatbotSessionsRepository,
    ConversationMessagesRepository,
    ConversationsRepository,
)
from app.repositories.quotes import QuoteItemsRepository, QuotesRepository
from app.services.whatsapp_service import WhatsAppService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_decimal(value: Any, default: str = "0.00") -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal(default)


class ConversationService:
    def __init__(self, db: Session):
        self.db = db
        self.clients_repo = ClientsRepository(db)
        self.conversations_repo = ConversationsRepository(db)
        self.messages_repo = ConversationMessagesRepository(db)
        self.sessions_repo = ChatbotSessionsRepository(db)
        self.settings_repo = CompanySettingsRepository(db)
        self.quotes_repo = QuotesRepository(db)
        self.quote_items_repo = QuoteItemsRepository(db)
        self.whatsapp_service = WhatsAppService()

    def _next_quote_code(self, *, company: Company) -> str:
        prefix = "RP"
        settings = getattr(company, "settings", None)
        if settings and getattr(settings, "quote_prefix", None):
            prefix = (settings.quote_prefix or "").strip() or prefix

        current_year = utc_now().year
        stmt = (
            self.db.query(Quote.code)
            .filter(
                Quote.company_id == company.id,
                Quote.code.isnot(None),
                Quote.code.like(f"{prefix}-{current_year}-%"),
            )
            .order_by(Quote.id.desc())
        )
        last_code = stmt.first()
        next_number = 1

        if last_code and last_code[0]:
            parts = str(last_code[0]).split("-")
            if parts and parts[-1].isdigit():
                next_number = int(parts[-1]) + 1

        return f"{prefix}-{current_year}-{next_number:04d}"

    def _sync_conversation_session(
        self,
        *,
        company_id: int,
        conversation: Conversation,
        phone: str,
        sender_key: str | None = None,
    ):
        return self.ensure_chatbot_session(
            company_id=company_id,
            conversation_id=conversation.id,
            phone=phone,
            sender_key=sender_key,
            step=conversation.bot_step,
            state=conversation.bot_step or "start",
            payload_json=conversation.bot_context or {},
        )

    def _normalize_dimension_to_cm(self, value: Any) -> Decimal | None:
        if value is None:
            return None
        dec = _to_decimal(value)
        # values coming from protection_network pricing are in meters;
        # convert to cm when they look like metric dimensions.
        if dec <= Decimal("20"):
            return dec * Decimal("100")
        return dec

    def _normalize_phone(self, phone: str | None) -> str:
        if not phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Telefone inválido.",
            )

        normalized = "".join(ch for ch in phone if ch.isdigit())
        if not normalized:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Telefone inválido.",
            )

        return normalized


    def _merge_bot_context(
        self,
        *,
        current_context: dict[str, Any] | None,
        incoming_context: dict[str, Any] | None,
    ) -> dict[str, Any]:
        base = dict(current_context or {})
        incoming = dict(incoming_context or {})

        if not incoming:
            return base

        protected_list_keys = [
            "selected_items",
            "selected_item_ids",
            "address_items_available",
            "manual_measurements",
            "quote_items_preview",
        ]

        for key in protected_list_keys:
            current_value = base.get(key)
            incoming_value = incoming.get(key)

            if isinstance(current_value, list) and current_value:
                if incoming_value is None:
                    incoming[key] = current_value
                elif isinstance(incoming_value, list) and not incoming_value:
                    incoming[key] = current_value

        protected_scalar_keys = [
            "address",
            "address_lookup_found",
            "address_lookup_endereco_id",
            "chosen_plant",
            "network_color",
            "mesh_type",
            "quote_id",
            "quote_code",
            "quote_status",
        ]

        for key in protected_scalar_keys:
            current_value = base.get(key)
            incoming_value = incoming.get(key)

            if current_value not in (None, "", {}, []):
                if incoming_value is None:
                    incoming[key] = current_value
                elif isinstance(incoming_value, str) and not incoming_value.strip():
                    incoming[key] = current_value

        base.update(incoming)
        return base

    def get_or_create_client(
        self,
        *,
        company_id: int,
        phone: str,
        contact_name: str | None = None,
        whatsapp_id: str | None = None,
    ) -> Client:
        normalized_phone = self._normalize_phone(phone)

        client = None
        if whatsapp_id:
            client = self.clients_repo.get_by_whatsapp_id(
                company_id=company_id,
                whatsapp_id=whatsapp_id,
            )

        if client is None:
            client = self.clients_repo.get_by_phone(
                company_id=company_id,
                phone=normalized_phone,
            )

        if client:
            update_data: dict[str, Any] = {}
            if contact_name and client.name != contact_name:
                update_data["name"] = contact_name
            if whatsapp_id and client.whatsapp_id != whatsapp_id:
                update_data["whatsapp_id"] = whatsapp_id

            if update_data:
                client = self.clients_repo.update_client(client, **update_data)

            return client

        return self.clients_repo.create_client(
            company_id=company_id,
            name=contact_name or normalized_phone,
            phone=normalized_phone,
            whatsapp_id=whatsapp_id,
            lead_source=ClientLeadSource.WHATSAPP,
            status=ClientStatus.LEAD,
        )

    def get_or_create_conversation(
        self,
        *,
        company_id: int,
        client_id: int,
        phone: str,
        external_id: str | None = None,
        subject: str | None = None,
    ) -> Conversation:
        normalized_phone = self._normalize_phone(phone)

        conversation = self.conversations_repo.get_open_by_phone(
            company_id=company_id,
            phone=normalized_phone,
            channel=ConversationChannel.WHATSAPP,
        )

        if conversation:
            return self.conversations_repo.update_conversation(
                conversation,
                client_id=client_id,
                last_message_at=utc_now(),
                subject=subject,
            )

        now = utc_now()
        return self.conversations_repo.create_conversation(
            company_id=company_id,
            client_id=client_id,
            assigned_to_id=None,
            channel=ConversationChannel.WHATSAPP,
            status=ConversationStatus.BOT,
            external_id=external_id,
            phone=normalized_phone,
            subject=subject,
            bot_step="start",
            bot_context={},
            first_message_at=now,
            last_message_at=now,
        )

    def append_inbound_message(
        self,
        *,
        company_id: int,
        conversation_id: int,
        content: str | None,
        sender_name: str | None = None,
        whatsapp_msg_id: str | None = None,
        media_url: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ):
        if whatsapp_msg_id:
            existing = self.messages_repo.get_by_whatsapp_msg_id(
                company_id=company_id,
                whatsapp_msg_id=whatsapp_msg_id,
            )
            if existing:
                return existing

        return self.messages_repo.create_message(
            company_id=company_id,
            conversation_id=conversation_id,
            direction=MessageDirection.INBOUND,
            type=MessageType.TEXT if not media_url else MessageType.IMAGE,
            sender_name=sender_name,
            content=content,
            media_url=media_url,
            whatsapp_msg_id=whatsapp_msg_id,
            metadata_json=metadata_json,
        )

    def append_outbound_message(
        self,
        *,
        company_id: int,
        conversation_id: int,
        content: str | None,
        metadata_json: dict[str, Any] | None = None,
        whatsapp_msg_id: str | None = None,
    ):
        return self.messages_repo.create_message(
            company_id=company_id,
            conversation_id=conversation_id,
            direction=MessageDirection.OUTBOUND,
            type=MessageType.TEXT,
            sender_name="bot",
            content=content,
            whatsapp_msg_id=whatsapp_msg_id,
            metadata_json=metadata_json,
        )

    def ensure_chatbot_session(
        self,
        *,
        company_id: int,
        conversation_id: int,
        phone: str,
        sender_key: str | None = None,
        step: str | None = None,
        state: str | None = None,
        payload_json: dict[str, Any] | None = None,
    ):
        normalized_phone = self._normalize_phone(phone)

        session = self.sessions_repo.get_active_by_phone(
            company_id=company_id,
            phone=normalized_phone,
        )

        effective_step = step or "start"
        effective_state = state or effective_step
        effective_payload = payload_json or {}

        if session:
            return self.sessions_repo.update_session(
                session,
                conversation_id=conversation_id,
                sender_key=sender_key,
                step=effective_step,
                state=effective_state,
                payload_json=effective_payload,
                last_interaction_at=utc_now(),
            )

        return self.sessions_repo.create_session(
            company_id=company_id,
            conversation_id=conversation_id,
            phone=normalized_phone,
            sender_key=sender_key,
            state=effective_state,
            step=effective_step,
            payload_json=effective_payload,
            last_interaction_at=utc_now(),
        )

    def _maybe_humanize_response(
        self,
        *,
        company: Company,
        conversation: Conversation,
        domain_result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Humaniza o texto do bot usando IA se estiver habilitado para esta empresa.
        Retorna o domain_result original se a IA estiver desabilitada ou falhar.
        """
        try:
            settings_obj = getattr(company, "settings", None)
            extra = (settings_obj.extra_settings or {}) if settings_obj else {}
            if not extra.get("ai_humanize_enabled", False):
                return domain_result

            from app.services.ai_assistant_service import humanize_bot_response

            bot_name = settings_obj.bot_name if settings_obj else None
            company_ctx = {
                "company_name": company.name,
                "bot_name": bot_name or "Assistente",
                "service_domain": str(
                    company.service_domain.value
                    if hasattr(company.service_domain, "value")
                    else company.service_domain
                ),
                "tone": str(extra.get("ai_tone", "amigável e profissional")),
            }

            current_step = conversation.bot_step or ""
            original_text = domain_result.get("text") or ""
            humanized = humanize_bot_response(
                original_text,
                company_ctx=company_ctx,
                current_step=current_step,
            )

            if humanized and humanized != original_text:
                result = dict(domain_result)
                result["text"] = humanized
                result["_ai_humanized"] = True
                return result

        except Exception as exc:
            import logging
            logging.getLogger("alphasync.ai").warning("Humanize step failed: %s", exc)

        return domain_result

    def _call_domain_chatbot(
        self,
        *,
        company: Company,
        conversation: Conversation,
        client: Client,
        inbound_message: dict[str, Any],
        chatbot_component: Any,
    ) -> dict[str, Any] | None:
        """Invoke the domain-specific chatbot component."""
        if hasattr(chatbot_component, "handle_inbound_message"):
            return chatbot_component.handle_inbound_message(
                company=company,
                conversation=conversation,
                client=client,
                inbound_message=inbound_message,
                db=self.db,
            )
        if hasattr(chatbot_component, "handle_message"):
            return chatbot_component.handle_message(
                company=company,
                conversation=conversation,
                client=client,
                inbound_message=inbound_message,
                db=self.db,
            )
        return None

    def _execute_domain_flow(
        self,
        *,
        company: Company,
        conversation: Conversation,
        client: Client,
        inbound_message: dict[str, Any],
    ) -> dict[str, Any] | None:
        from app.domains._shared.flow_helpers import RESET_WORDS, current_context, json_safe
        from app.domains._shared import global_menu

        step = conversation.bot_step or "start"
        txt = (
            inbound_message.get("message_text")
            or inbound_message.get("interactive_reply_title")
            or inbound_message.get("interactive_reply_id")
            or ""
        ).strip().lower()

        # ── GLOBAL RESET: any reset-word clears global_menu_done and returns to start ──
        if txt in RESET_WORDS:
            ctx = current_context(conversation)
            ctx.pop("global_menu_done", None)
            ctx.pop("global_intent", None)
            conversation.bot_step = "start"
            conversation.bot_context = json_safe(ctx)
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(conversation, "bot_context")
            self.db.flush()
            step = "start"

        ctx = current_context(conversation)

        # ── SHOW GLOBAL MENU when step is 'start' and no menu_done flag ──────────────
        if step == "start" and not ctx.get("global_menu_done"):
            return global_menu.show_main_menu(
                conversation, self.db, client=client, ctx=ctx
            )

        # ── HANDLE ALL GLOBAL STEPS ───────────────────────────────────────────────────
        if global_menu.is_global_step(step):
            try:
                chatbot_component = domain_engine.get_chatbot_flow_for_company(company)
            except Exception:
                chatbot_component = None

            def _domain_caller() -> dict[str, Any] | None:
                if chatbot_component is None:
                    return None
                empty_msg = dict(inbound_message)
                empty_msg["message_text"] = ""
                empty_msg["interactive_reply_id"] = None
                empty_msg["interactive_reply_title"] = None
                return self._call_domain_chatbot(
                    company=company,
                    conversation=conversation,
                    client=client,
                    inbound_message=empty_msg,
                    chatbot_component=chatbot_component,
                )

            result = global_menu.handle_global_step(
                company=company,
                conversation=conversation,
                client=client,
                inbound_message=inbound_message,
                db=self.db,
                current_step=step,
                domain_caller=_domain_caller,
            )
            if result is not None:
                return result
            # None means "delegate to domain" (opt_quote path after greeting returned)

        # ── DOMAIN-SPECIFIC FLOW ──────────────────────────────────────────────────────
        try:
            chatbot_component = domain_engine.get_chatbot_flow_for_company(company)
        except Exception:
            return None

        if chatbot_component is None:
            return None

        return self._call_domain_chatbot(
            company=company,
            conversation=conversation,
            client=client,
            inbound_message=inbound_message,
            chatbot_component=chatbot_component,
        )

    def _persist_quote_preview(
        self,
        *,
        company: Company,
        client: Client,
        conversation: Conversation,
        quote_preview: dict[str, Any],
    ) -> Quote | None:
        items_preview = quote_preview.get("items") or []
        totals = quote_preview.get("totals") or {}

        if not items_preview:
            return None

        context = dict(conversation.bot_context or {})
        existing_quote_id = context.get("quote_id")

        quote: Quote | None = None
        if existing_quote_id:
            quote = self.quotes_repo.get_by_id_and_company(existing_quote_id, company.id)

        title = f"Orçamento - {client.name}"
        description = f"Orçamento gerado automaticamente via WhatsApp para {conversation.subject or conversation.phone}"
        quote_code = quote.code if quote and quote.code else self._next_quote_code(company=company)

        if quote is None:
            quote = self.quotes_repo.create_quote(
                company_id=company.id,
                client_id=client.id,
                conversation_id=conversation.id,
                seller_id=conversation.assigned_to_id,
                code=quote_code,
                service_type="protection_network",
                title=title,
                description=description,
                subtotal=_to_decimal(totals.get("subtotal")),
                discount=_to_decimal(totals.get("discount")),
                total_value=_to_decimal(totals.get("total_value")),
                status=QuoteStatus.DRAFT,
                valid_until=None,
                notes="Gerado automaticamente pelo fluxo do bot.",
                pdf_url=None,
                domain_data={
                    "generated_by": "chatbot",
                    "conversation_id": conversation.id,
                    "bot_step": conversation.bot_step,
                },
            )
        else:
            self.db.execute(
                delete(QuoteItem).where(
                    QuoteItem.company_id == company.id,
                    QuoteItem.quote_id == quote.id,
                )
            )
            self.db.flush()

            quote = self.quotes_repo.update_quote(
                quote,
                client_id=client.id,
                conversation_id=conversation.id,
                seller_id=conversation.assigned_to_id,
                code=quote_code,
                service_type="protection_network",
                title=title,
                description=description,
                subtotal=_to_decimal(totals.get("subtotal")),
                discount=_to_decimal(totals.get("discount")),
                total_value=_to_decimal(totals.get("total_value")),
                status=QuoteStatus.DRAFT,
                notes="Atualizado automaticamente pelo fluxo do bot.",
                domain_data={
                    "generated_by": "chatbot",
                    "conversation_id": conversation.id,
                    "bot_step": conversation.bot_step,
                },
            )

        for item_data in items_preview:
            self.quote_items_repo.create_item(
                company_id=company.id,
                quote_id=quote.id,
                description=item_data.get("description") or "Rede de proteção",
                service_type=item_data.get("service_type"),
                width_cm=self._normalize_dimension_to_cm(
                    item_data.get("width_cm", item_data.get("width"))
                ),
                height_cm=self._normalize_dimension_to_cm(
                    item_data.get("height_cm", item_data.get("height"))
                ),
                quantity=int(item_data.get("quantity") or 1),
                unit_price=_to_decimal(item_data.get("unit_price")),
                total_price=_to_decimal(item_data.get("total_price")),
                status=QuoteItemStatus.PENDING,
                notes=item_data.get("notes"),
                domain_data=item_data.get("domain_data") or {},
            )

        context["quote_id"] = quote.id
        context["quote_code"] = quote.code
        context["quote_status"] = "draft"
        conversation.bot_context = context
        self.db.flush()

        return quote

    def _send_domain_response(
        self,
        *,
        company: Company,
        phone_number_id: str,
        to_phone: str,
        conversation: Conversation,
        domain_result: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not domain_result:
            return None

        action = domain_result.get("action")
        settings_obj = self.settings_repo.get_by_company_id(company.id)
        access_token = settings_obj.whatsapp_access_token if settings_obj else None

        if not access_token:
            fallback_text = domain_result.get("text") or ""
            self.append_outbound_message(
                company_id=company.id,
                conversation_id=conversation.id,
                content=fallback_text,
                metadata_json={
                    "delivery": "not_sent",
                    "reason": "missing_whatsapp_access_token",
                    "action": action,
                    "domain_result": domain_result,
                },
            )
            return {
                "sent": False,
                "reason": "missing_whatsapp_access_token",
                "action": action,
                "text": fallback_text,
            }

        try:
            if action == "reply_text":
                text = (domain_result.get("text") or "").strip()
                send_result = self.whatsapp_service.send_text(
                    access_token=access_token,
                    phone_number_id=phone_number_id,
                    to=to_phone,
                    body=text,
                )

            elif action == "reply_buttons":
                text = (domain_result.get("text") or "").strip()
                send_result = self.whatsapp_service.send_buttons(
                    access_token=access_token,
                    phone_number_id=phone_number_id,
                    to=to_phone,
                    body=text,
                    buttons=domain_result.get("buttons") or [],
                )

            elif action == "reply_list":
                send_result = self.whatsapp_service.send_list_message(
                    access_token=access_token,
                    phone_number_id=phone_number_id,
                    to=to_phone,
                    header=domain_result.get("header") or "Opções",
                    body=domain_result.get("text") or "",
                    button_text=domain_result.get("button_text") or "Escolher",
                    sections=domain_result.get("sections") or [],
                )

            elif action == "assumed":
                text = (domain_result.get("text") or "").strip()
                if text:
                    send_result = self.whatsapp_service.send_text(
                        access_token=access_token,
                        phone_number_id=phone_number_id,
                        to=to_phone,
                        body=text,
                    )
                else:
                    send_result = {"messages": []}

            else:
                return {
                    "sent": False,
                    "reason": "unsupported_action",
                    "action": action,
                }

            whatsapp_message_id = None
            messages = send_result.get("messages") or []
            if messages:
                whatsapp_message_id = messages[0].get("id")

            self.append_outbound_message(
                company_id=company.id,
                conversation_id=conversation.id,
                content=domain_result.get("text"),
                whatsapp_msg_id=whatsapp_message_id,
                metadata_json={
                    "delivery": "sent",
                    "provider_response": send_result,
                    "action": action,
                },
            )

            return {
                "sent": True,
                "action": action,
                "provider_response": send_result,
            }

        except Exception as exc:
            self.append_outbound_message(
                company_id=company.id,
                conversation_id=conversation.id,
                content=domain_result.get("text"),
                metadata_json={
                    "delivery": "failed",
                    "error": str(exc),
                    "action": action,
                },
            )
            return {
                "sent": False,
                "reason": "provider_error",
                "error": str(exc),
                "action": action,
            }

    def handle_inbound_whatsapp_message(
        self,
        *,
        company: Company,
        phone_number_id: str,
        from_phone: str,
        contact_name: str | None,
        message_text: str | None,
        whatsapp_message_id: str | None,
        whatsapp_contact_id: str | None = None,
        interactive_reply_id: str | None = None,
        interactive_reply_title: str | None = None,
        media_url: str | None = None,
        raw_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        client = self.get_or_create_client(
            company_id=company.id,
            phone=from_phone,
            contact_name=contact_name,
            whatsapp_id=whatsapp_contact_id,
        )

        conversation = self.get_or_create_conversation(
            company_id=company.id,
            client_id=client.id,
            phone=from_phone,
            external_id=whatsapp_contact_id or from_phone,
            subject=f"WhatsApp {from_phone}",
        )

        message = self.append_inbound_message(
            company_id=company.id,
            conversation_id=conversation.id,
            content=message_text or interactive_reply_title or interactive_reply_id,
            sender_name=contact_name,
            whatsapp_msg_id=whatsapp_message_id,
            media_url=media_url,
            metadata_json=raw_payload,
        )

        self._sync_conversation_session(
            company_id=company.id,
            conversation=conversation,
            phone=from_phone,
            sender_key=whatsapp_contact_id or from_phone,
        )

        previous_context = dict(conversation.bot_context or {})
        previous_step = conversation.bot_step

        domain_result = self._execute_domain_flow(
            company=company,
            conversation=conversation,
            client=client,
            inbound_message={
                "phone_number_id": phone_number_id,
                "from_phone": from_phone,
                "contact_name": contact_name,
                "message_text": message_text,
                "interactive_reply_id": interactive_reply_id,
                "interactive_reply_title": interactive_reply_title,
                "whatsapp_message_id": whatsapp_message_id,
                "whatsapp_contact_id": whatsapp_contact_id,
                "media_url": media_url,
                "raw_payload": raw_payload,
            },
        )

        if domain_result:
            domain_next_step = domain_result.get("next_step")
            domain_context = domain_result.get("context")

            merged_context = self._merge_bot_context(
                current_context=previous_context,
                incoming_context=conversation.bot_context or domain_context or {},
            )

            if domain_next_step:
                conversation.bot_step = domain_next_step
            elif previous_step:
                conversation.bot_step = previous_step

            conversation.bot_context = merged_context

            if isinstance(domain_context, dict):
                domain_result["context"] = merged_context

        self.conversations_repo.update_conversation(
            conversation,
            last_message_at=utc_now(),
            bot_step=conversation.bot_step,
            bot_context=conversation.bot_context or {},
        )

        self._sync_conversation_session(
            company_id=company.id,
            conversation=conversation,
            phone=from_phone,
            sender_key=whatsapp_contact_id or from_phone,
        )

        persisted_quote_id = None
        if domain_result and conversation.bot_step == "quote_ready":
            quote_preview = domain_result.get("quote_preview") or {}
            quote = self._persist_quote_preview(
                company=company,
                client=client,
                conversation=conversation,
                quote_preview=quote_preview,
            )
            if quote:
                persisted_quote_id = quote.id

        # ── Humanização via IA (opcional, degradação graciosa) ─────────────────
        if domain_result and domain_result.get("text"):
            domain_result = self._maybe_humanize_response(
                company=company,
                conversation=conversation,
                domain_result=domain_result,
            )

        outbound_result = self._send_domain_response(
            company=company,
            phone_number_id=phone_number_id,
            to_phone=self._normalize_phone(from_phone),
            conversation=conversation,
            domain_result=domain_result,
        )

        return {
            "company_id": company.id,
            "service_domain": str(
                company.service_domain.value
                if hasattr(company.service_domain, "value")
                else company.service_domain
            ),
            "client_id": client.id,
            "conversation_id": conversation.id,
            "message_id": message.id,
            "domain_result": domain_result,
            "outbound_result": outbound_result,
            "quote_id": persisted_quote_id,
        }
