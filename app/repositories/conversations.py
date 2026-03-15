from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import (
    ChatbotSession,
    Conversation,
    ConversationChannel,
    ConversationMessage,
    ConversationStatus,
    MessageDirection,
    MessageType,
    SessionStatus,
)
from app.repositories.base import TenantRepository


class ConversationsRepository(TenantRepository[Conversation]):
    def __init__(self, db: Session):
        super().__init__(db, Conversation)

    def get_full_by_id_and_company(self, conversation_id: int, company_id: int) -> Conversation | None:
        stmt = (
            select(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.company_id == company_id,
            )
            .options(
                selectinload(Conversation.messages),
                selectinload(Conversation.chatbot_sessions),
                selectinload(Conversation.client),
                selectinload(Conversation.assigned_user),
            )
        )
        return self.db.scalar(stmt)

    def get_by_external_id(
        self,
        *,
        company_id: int,
        channel: ConversationChannel,
        external_id: str,
    ) -> Conversation | None:
        stmt = select(Conversation).where(
            Conversation.company_id == company_id,
            Conversation.channel == channel,
            Conversation.external_id == external_id,
        )
        return self.db.scalar(stmt)

    def get_open_by_phone(
        self,
        *,
        company_id: int,
        phone: str,
        channel: ConversationChannel = ConversationChannel.WHATSAPP,
    ) -> Conversation | None:
        stmt = (
            select(Conversation)
            .where(
                Conversation.company_id == company_id,
                Conversation.phone == phone,
                Conversation.channel == channel,
                Conversation.status.in_(
                    [
                        ConversationStatus.OPEN,
                        ConversationStatus.ASSUMED,
                        ConversationStatus.BOT,
                    ]
                ),
            )
            .order_by(Conversation.updated_at.desc())
        )
        return self.db.scalar(stmt)

    def list_company_conversations(
        self,
        company_id: int,
        *,
        status: ConversationStatus | None = None,
        assigned_to_id: int | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Conversation]:
        stmt: Select[tuple[Conversation]] = (
            select(Conversation)
            .where(Conversation.company_id == company_id)
            .options(
                selectinload(Conversation.client),
                selectinload(Conversation.assigned_user),
            )
        )

        if status is not None:
            stmt = stmt.where(Conversation.status == status)

        if assigned_to_id is not None:
            stmt = stmt.where(Conversation.assigned_to_id == assigned_to_id)

        if search:
            search_term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Conversation.phone.ilike(search_term),
                    Conversation.subject.ilike(search_term),
                )
            )

        stmt = stmt.order_by(
            Conversation.last_message_at.desc().nullslast(),
            Conversation.updated_at.desc(),
        ).offset(offset).limit(limit)

        return list(self.db.scalars(stmt).all())

    def create_conversation(
        self,
        *,
        company_id: int,
        client_id: int | None,
        assigned_to_id: int | None,
        channel: ConversationChannel,
        status: ConversationStatus,
        external_id: str | None,
        phone: str,
        subject: str | None = None,
        bot_step: str | None = None,
        bot_context: dict[str, Any] | None = None,
        first_message_at: datetime | None = None,
        last_message_at: datetime | None = None,
    ) -> Conversation:
        conversation = Conversation(
            company_id=company_id,
            client_id=client_id,
            assigned_to_id=assigned_to_id,
            channel=channel,
            status=status,
            external_id=external_id,
            phone=phone,
            subject=subject,
            bot_step=bot_step,
            bot_context=bot_context,
            first_message_at=first_message_at,
            last_message_at=last_message_at,
        )
        return self.add(conversation)

    def update_conversation(
        self,
        conversation: Conversation,
        *,
        client_id: int | None = None,
        assigned_to_id: int | None = None,
        status: ConversationStatus | None = None,
        subject: str | None = None,
        bot_step: str | None = None,
        bot_context: dict[str, Any] | None = None,
        last_message_at: datetime | None = None,
    ) -> Conversation:
        if client_id is not None:
            conversation.client_id = client_id
        if assigned_to_id is not None:
            conversation.assigned_to_id = assigned_to_id
        if status is not None:
            conversation.status = status
        if subject is not None:
            conversation.subject = subject
        if bot_step is not None:
            conversation.bot_step = bot_step
        if bot_context is not None:
            conversation.bot_context = bot_context
        if last_message_at is not None:
            conversation.last_message_at = last_message_at

        self.db.flush()
        self.db.refresh(conversation)
        return conversation

    def count_company_conversations(
        self,
        company_id: int,
        *,
        status: ConversationStatus | None = None,
        search: str | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(Conversation).where(
            Conversation.company_id == company_id
        )
        if status is not None:
            stmt = stmt.where(Conversation.status == status)
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(Conversation.phone.ilike(term), Conversation.subject.ilike(term))
            )
        return int(self.db.scalar(stmt) or 0)


class ConversationMessagesRepository(TenantRepository[ConversationMessage]):
    def __init__(self, db: Session):
        super().__init__(db, ConversationMessage)

    def list_by_conversation(
        self,
        *,
        company_id: int,
        conversation_id: int,
        limit: int = 200,
        offset: int = 0,
    ) -> list[ConversationMessage]:
        stmt = (
            select(ConversationMessage)
            .where(
                ConversationMessage.company_id == company_id,
                ConversationMessage.conversation_id == conversation_id,
            )
            .order_by(ConversationMessage.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_whatsapp_msg_id(
        self,
        *,
        company_id: int,
        whatsapp_msg_id: str,
    ) -> ConversationMessage | None:
        stmt = select(ConversationMessage).where(
            ConversationMessage.company_id == company_id,
            ConversationMessage.whatsapp_msg_id == whatsapp_msg_id,
        )
        return self.db.scalar(stmt)

    def create_message(
        self,
        *,
        company_id: int,
        conversation_id: int,
        direction: MessageDirection,
        type: MessageType = MessageType.TEXT,
        sender_name: str | None = None,
        content: str | None = None,
        media_url: str | None = None,
        whatsapp_msg_id: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> ConversationMessage:
        message = ConversationMessage(
            company_id=company_id,
            conversation_id=conversation_id,
            direction=direction,
            type=type,
            sender_name=sender_name,
            content=content,
            media_url=media_url,
            whatsapp_msg_id=whatsapp_msg_id,
            metadata_json=metadata_json,
        )
        return self.add(message)


class ChatbotSessionsRepository(TenantRepository[ChatbotSession]):
    def __init__(self, db: Session):
        super().__init__(db, ChatbotSession)

    def get_active_by_phone(
        self,
        *,
        company_id: int,
        phone: str,
    ) -> ChatbotSession | None:
        stmt = (
            select(ChatbotSession)
            .where(
                ChatbotSession.company_id == company_id,
                ChatbotSession.phone == phone,
                ChatbotSession.status == SessionStatus.ACTIVE,
            )
            .order_by(ChatbotSession.updated_at.desc())
        )
        return self.db.scalar(stmt)

    def create_session(
        self,
        *,
        company_id: int,
        conversation_id: int | None,
        phone: str,
        sender_key: str | None = None,
        state: str = "start",
        step: str | None = None,
        payload_json: dict[str, Any] | None = None,
        status: SessionStatus = SessionStatus.ACTIVE,
        expires_at: datetime | None = None,
        last_interaction_at: datetime | None = None,
    ) -> ChatbotSession:
        session = ChatbotSession(
            company_id=company_id,
            conversation_id=conversation_id,
            phone=phone,
            sender_key=sender_key,
            state=state,
            step=step,
            payload_json=payload_json or {},
            status=status,
            expires_at=expires_at,
            last_interaction_at=last_interaction_at or datetime.utcnow(),
        )
        return self.add(session)

    def update_session(
        self,
        session: ChatbotSession,
        *,
        conversation_id: int | None = None,
        sender_key: str | None = None,
        state: str | None = None,
        step: str | None = None,
        payload_json: dict[str, Any] | None = None,
        status: SessionStatus | None = None,
        expires_at: datetime | None = None,
        last_interaction_at: datetime | None = None,
    ) -> ChatbotSession:
        if conversation_id is not None:
            session.conversation_id = conversation_id
        if sender_key is not None:
            session.sender_key = sender_key
        if state is not None:
            session.state = state
        if step is not None:
            session.step = step
        if payload_json is not None:
            session.payload_json = payload_json
        if status is not None:
            session.status = status
        if expires_at is not None:
            session.expires_at = expires_at
        if last_interaction_at is not None:
            session.last_interaction_at = last_interaction_at

        self.db.flush()
        self.db.refresh(session)
        return session