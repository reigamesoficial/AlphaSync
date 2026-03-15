from datetime import datetime
from typing import Any

from pydantic import Field

from app.db.models import (
    ConversationChannel,
    ConversationStatus,
    MessageDirection,
    MessageType,
    SessionStatus,
)
from app.schemas.common import BaseSchema, IDSchema, TimestampSchema


class ConversationBase(BaseSchema):
    client_id: int | None = None
    assigned_to_id: int | None = None
    channel: ConversationChannel = ConversationChannel.WHATSAPP
    status: ConversationStatus = ConversationStatus.OPEN
    external_id: str | None = Field(default=None, max_length=120)
    phone: str = Field(min_length=8, max_length=30)
    subject: str | None = Field(default=None, max_length=200)
    bot_step: str | None = Field(default=None, max_length=80)
    bot_context: dict[str, Any] | None = None
    first_message_at: datetime | None = None
    last_message_at: datetime | None = None


class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(BaseSchema):
    client_id: int | None = None
    assigned_to_id: int | None = None
    channel: ConversationChannel | None = None
    status: ConversationStatus | None = None
    external_id: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, min_length=8, max_length=30)
    subject: str | None = Field(default=None, max_length=200)
    bot_step: str | None = Field(default=None, max_length=80)
    bot_context: dict[str, Any] | None = None
    first_message_at: datetime | None = None
    last_message_at: datetime | None = None


class ConversationResponse(ConversationBase, IDSchema, TimestampSchema):
    company_id: int


class ConversationMessageBase(BaseSchema):
    conversation_id: int
    direction: MessageDirection
    type: MessageType = MessageType.TEXT
    sender_name: str | None = Field(default=None, max_length=150)
    content: str | None = None
    media_url: str | None = None
    whatsapp_msg_id: str | None = Field(default=None, max_length=100)
    metadata_json: dict[str, Any] | None = None


class ConversationMessageCreate(ConversationMessageBase):
    pass


class ConversationMessageResponse(ConversationMessageBase, IDSchema, TimestampSchema):
    company_id: int


class ChatbotSessionBase(BaseSchema):
    conversation_id: int | None = None
    phone: str = Field(min_length=8, max_length=30)
    sender_key: str | None = Field(default=None, max_length=120)
    state: str = Field(default="start", max_length=100)
    step: str | None = Field(default=None, max_length=100)
    payload_json: dict[str, Any] = Field(default_factory=dict)
    status: SessionStatus = SessionStatus.ACTIVE
    expires_at: datetime | None = None
    last_interaction_at: datetime | None = None


class ChatbotSessionCreate(ChatbotSessionBase):
    pass


class ChatbotSessionUpdate(BaseSchema):
    conversation_id: int | None = None
    phone: str | None = Field(default=None, min_length=8, max_length=30)
    sender_key: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=100)
    step: str | None = Field(default=None, max_length=100)
    payload_json: dict[str, Any] | None = None
    status: SessionStatus | None = None
    expires_at: datetime | None = None
    last_interaction_at: datetime | None = None


class ChatbotSessionResponse(ChatbotSessionBase, IDSchema, TimestampSchema):
    company_id: int