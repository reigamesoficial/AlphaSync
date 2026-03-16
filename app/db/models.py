from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.connection import Base


# ============================================================
# ENUMS
# ============================================================


class UserRole(str, PyEnum):
    MASTER_ADMIN = "master_admin"
    COMPANY_ADMIN = "company_admin"
    SELLER = "seller"
    INSTALLER = "installer"
    VIEWER = "viewer"


class CompanyStatus(str, PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class ServiceDomain(str, PyEnum):
    PROTECTION_NETWORK = "protection_network"
    HVAC = "hvac"
    ELECTRICIAN = "electrician"
    PLUMBING = "plumbing"
    CLEANING = "cleaning"
    GLASS_INSTALLATION = "glass_installation"
    PEST_CONTROL = "pest_control"
    SECURITY_CAMERAS = "security_cameras"


class ConversationChannel(str, PyEnum):
    WHATSAPP = "whatsapp"
    WEBCHAT = "webchat"
    INSTAGRAM = "instagram"


class ConversationStatus(str, PyEnum):
    OPEN = "open"
    ASSUMED = "assumed"
    BOT = "bot"
    CLOSED = "closed"
    ARCHIVED = "archived"


class MessageDirection(str, PyEnum):
    INBOUND = "in"
    OUTBOUND = "out"


class MessageType(str, PyEnum):
    TEXT = "text"
    BUTTON = "button"
    LIST = "list"
    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    TEMPLATE = "template"
    SYSTEM = "system"


class ClientLeadSource(str, PyEnum):
    WHATSAPP = "whatsapp"
    MANUAL = "manual"
    IMPORT = "import"


class ClientStatus(str, PyEnum):
    LEAD = "lead"
    QUALIFIED = "qualified"
    CUSTOMER = "customer"
    INACTIVE = "inactive"


class QuoteStatus(str, PyEnum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    DONE = "done"
    EXPIRED = "expired"


class QuoteItemStatus(str, PyEnum):
    PENDING = "pending"
    DONE = "done"
    REMOVED = "removed"


class AppointmentStatus(str, PyEnum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    DONE = "done"
    RESCHEDULED = "rescheduled"


class ReminderStatus(str, PyEnum):
    PENDING = "pending"
    SENT = "sent"
    CONFIRMED = "confirmed"
    DECLINED = "declined"


class SessionStatus(str, PyEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"
    ABANDONED = "abandoned"


# ============================================================
# MIXINS
# ============================================================


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ============================================================
# MODELS
# ============================================================


class Company(TimestampMixin, Base):
    __tablename__ = "companies"
    __table_args__ = (
        Index("ix_companies_status", "status"),
        Index("ix_companies_is_active", "is_active"),
        Index("ix_companies_service_domain", "service_domain"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    slug: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    status: Mapped[CompanyStatus] = mapped_column(
        Enum(CompanyStatus, name="company_status_enum"),
        default=CompanyStatus.ACTIVE,
        nullable=False,
    )
    service_domain: Mapped[ServiceDomain] = mapped_column(
        Enum(ServiceDomain, name="service_domain_enum"),
        default=ServiceDomain.PROTECTION_NETWORK,
        nullable=False,
    )
    plan_name: Mapped[str | None] = mapped_column(String(50), nullable=True)

    whatsapp_phone_number_id: Mapped[str | None] = mapped_column(
        String(40),
        unique=True,
        nullable=True,
        index=True,
    )
    whatsapp_business_account_id: Mapped[str | None] = mapped_column(String(80), nullable=True)

    support_email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    support_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    settings: Mapped["CompanySettings | None"] = relationship(
        "CompanySettings",
        back_populates="company",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="company",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    clients: Mapped[list["Client"]] = relationship(
        "Client",
        back_populates="company",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="company",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    conversation_messages: Mapped[list["ConversationMessage"]] = relationship(
        "ConversationMessage",
        back_populates="company",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    quotes: Mapped[list["Quote"]] = relationship(
        "Quote",
        back_populates="company",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    quote_items: Mapped[list["QuoteItem"]] = relationship(
        "QuoteItem",
        back_populates="company",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment",
        back_populates="company",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    chatbot_sessions: Mapped[list["ChatbotSession"]] = relationship(
        "ChatbotSession",
        back_populates="company",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    pn_address_catalogs: Mapped[list["PNAddressCatalog"]] = relationship(
        "PNAddressCatalog",
        back_populates="company",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    pn_address_plants: Mapped[list["PNAddressPlant"]] = relationship(
        "PNAddressPlant",
        back_populates="company",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    pn_address_measurements: Mapped[list["PNAddressMeasurement"]] = relationship(
        "PNAddressMeasurement",
        back_populates="company",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    pn_address_job_rules: Mapped[list["PNAddressJobRule"]] = relationship(
        "PNAddressJobRule",
        back_populates="company",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class CompanySettings(TimestampMixin, Base):
    __tablename__ = "company_settings"
    __table_args__ = (
        UniqueConstraint("company_id", name="uq_company_settings_company_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    brand_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    primary_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    secondary_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)

    bot_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    quote_prefix: Mapped[str | None] = mapped_column(String(20), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="BRL", nullable=False)
    timezone: Mapped[str] = mapped_column(String(80), default="America/Sao_Paulo", nullable=False)

    whatsapp_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    whatsapp_verify_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    calendar_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    calendar_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    extra_settings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    company: Mapped["Company"] = relationship("Company", back_populates="settings")


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("company_id", "email", name="uq_users_company_email"),
        Index("ix_users_company_role", "company_id", "role"),
        Index("ix_users_company_active", "company_id", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    email: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum"),
        nullable=False,
        default=UserRole.VIEWER,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    whatsapp_id: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    company: Mapped["Company | None"] = relationship("Company", back_populates="users")

    assigned_conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="assigned_user",
        foreign_keys="Conversation.assigned_to_id",
    )
    created_quotes: Mapped[list["Quote"]] = relationship(
        "Quote",
        back_populates="seller",
        foreign_keys="Quote.seller_id",
    )
    assigned_appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment",
        back_populates="assigned_installer",
        foreign_keys="Appointment.assigned_installer_id",
    )


class Client(TimestampMixin, Base):
    __tablename__ = "clients"
    __table_args__ = (
        UniqueConstraint("company_id", "phone", name="uq_clients_company_phone"),
        Index("ix_clients_company_name", "company_id", "name"),
        Index("ix_clients_company_status", "company_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    whatsapp_id: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    lead_source: Mapped[ClientLeadSource] = mapped_column(
        Enum(ClientLeadSource, name="client_lead_source_enum"),
        default=ClientLeadSource.WHATSAPP,
        nullable=False,
    )
    status: Mapped[ClientStatus] = mapped_column(
        Enum(ClientStatus, name="client_status_enum"),
        default=ClientStatus.LEAD,
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    company: Mapped["Company"] = relationship("Company", back_populates="clients")
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="client",
        passive_deletes=True,
    )
    quotes: Mapped[list["Quote"]] = relationship(
        "Quote",
        back_populates="client",
        passive_deletes=True,
    )
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment",
        back_populates="client",
        passive_deletes=True,
    )


class Conversation(TimestampMixin, Base):
    __tablename__ = "conversations"
    __table_args__ = (
        Index("ix_conversations_company_status", "company_id", "status"),
        Index("ix_conversations_company_phone", "company_id", "phone"),
        Index("ix_conversations_company_last_message", "company_id", "last_message_at"),
        UniqueConstraint(
            "company_id",
            "channel",
            "external_id",
            name="uq_conversations_company_channel_external",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    client_id: Mapped[int | None] = mapped_column(
        ForeignKey("clients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assigned_to_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    channel: Mapped[ConversationChannel] = mapped_column(
        Enum(ConversationChannel, name="conversation_channel_enum"),
        default=ConversationChannel.WHATSAPP,
        nullable=False,
    )
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus, name="conversation_status_enum"),
        default=ConversationStatus.OPEN,
        nullable=False,
    )

    external_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    subject: Mapped[str | None] = mapped_column(String(200), nullable=True)

    bot_step: Mapped[str | None] = mapped_column(String(80), nullable=True)
    bot_context: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    first_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    company: Mapped["Company"] = relationship("Company", back_populates="conversations")
    client: Mapped["Client | None"] = relationship("Client", back_populates="conversations")
    assigned_user: Mapped["User | None"] = relationship(
        "User",
        back_populates="assigned_conversations",
        foreign_keys=[assigned_to_id],
    )

    messages: Mapped[list["ConversationMessage"]] = relationship(
        "ConversationMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ConversationMessage.created_at",
    )
    chatbot_sessions: Mapped[list["ChatbotSession"]] = relationship(
        "ChatbotSession",
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ChatbotSession.created_at",
    )
    quotes: Mapped[list["Quote"]] = relationship(
        "Quote",
        back_populates="conversation",
        passive_deletes=True,
    )


class ConversationMessage(TimestampMixin, Base):
    __tablename__ = "conversation_messages"
    __table_args__ = (
        Index("ix_conversation_messages_company_created", "company_id", "created_at"),
        Index("ix_conversation_messages_conversation_created", "conversation_id", "created_at"),
        UniqueConstraint(
            "company_id",
            "whatsapp_msg_id",
            name="uq_conversation_messages_company_whatsapp_msg_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    direction: Mapped[MessageDirection] = mapped_column(
        Enum(MessageDirection, name="message_direction_enum"),
        nullable=False,
    )
    type: Mapped[MessageType] = mapped_column(
        Enum(MessageType, name="message_type_enum"),
        default=MessageType.TEXT,
        nullable=False,
    )

    sender_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    whatsapp_msg_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    company: Mapped["Company"] = relationship("Company", back_populates="conversation_messages")
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")


class ChatbotSession(TimestampMixin, Base):
    __tablename__ = "chatbot_sessions"
    __table_args__ = (
        Index("ix_chatbot_sessions_company_status", "company_id", "status"),
        Index("ix_chatbot_sessions_company_phone", "company_id", "phone"),
        Index("ix_chatbot_sessions_company_expires", "company_id", "expires_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[int | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    phone: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    sender_key: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)

    state: Mapped[str] = mapped_column(String(100), nullable=False, default="start")
    step: Mapped[str | None] = mapped_column(String(100), nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="session_status_enum"),
        default=SessionStatus.ACTIVE,
        nullable=False,
    )

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_interaction_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    company: Mapped["Company"] = relationship("Company", back_populates="chatbot_sessions")
    conversation: Mapped["Conversation | None"] = relationship("Conversation", back_populates="chatbot_sessions")


class Quote(TimestampMixin, Base):
    __tablename__ = "quotes"
    __table_args__ = (
        Index("ix_quotes_company_status", "company_id", "status"),
        Index("ix_quotes_company_client", "company_id", "client_id"),
        Index("ix_quotes_company_created", "company_id", "created_at"),
        UniqueConstraint("company_id", "code", name="uq_quotes_company_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[int | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    seller_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    code: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    service_type: Mapped[str] = mapped_column(String(60), nullable=False, default="protection_network")
    title: Mapped[str | None] = mapped_column(String(150), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    discount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)

    status: Mapped[QuoteStatus] = mapped_column(
        Enum(QuoteStatus, name="quote_status_enum"),
        default=QuoteStatus.DRAFT,
        nullable=False,
    )
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    domain_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    company: Mapped["Company"] = relationship("Company", back_populates="quotes")
    client: Mapped["Client"] = relationship("Client", back_populates="quotes")
    conversation: Mapped["Conversation | None"] = relationship("Conversation", back_populates="quotes")
    seller: Mapped["User | None"] = relationship(
        "User",
        back_populates="created_quotes",
        foreign_keys=[seller_id],
    )
    items: Mapped[list["QuoteItem"]] = relationship(
        "QuoteItem",
        back_populates="quote",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="QuoteItem.id",
    )
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment",
        back_populates="quote",
        passive_deletes=True,
    )


class QuoteItem(TimestampMixin, Base):
    __tablename__ = "quote_items"
    __table_args__ = (
        Index("ix_quote_items_company_quote", "company_id", "quote_id"),
        Index("ix_quote_items_company_status", "company_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    quote_id: Mapped[int] = mapped_column(
        ForeignKey("quotes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(Text, nullable=False)
    service_type: Mapped[str | None] = mapped_column(String(60), nullable=True)

    width_cm: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    height_cm: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)

    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)

    status: Mapped[QuoteItemStatus] = mapped_column(
        Enum(QuoteItemStatus, name="quote_item_status_enum"),
        default=QuoteItemStatus.PENDING,
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    domain_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    company: Mapped["Company"] = relationship("Company", back_populates="quote_items")
    quote: Mapped["Quote"] = relationship("Quote", back_populates="items")


class PNAddressCatalog(TimestampMixin, Base):
    __tablename__ = "pn_address_catalog"
    __table_args__ = (
        Index("ix_pn_address_catalog_company_id", "company_id"),
        Index("ix_pn_address_catalog_normalized_address", "normalized_address"),
        UniqueConstraint(
            "company_id",
            "normalized_address",
            name="uq_pn_address_catalog_company_normalized_address",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    raw_address: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_address: Mapped[str] = mapped_column(String(500), nullable=False)
    zipcode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[str | None] = mapped_column(String(60), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    company: Mapped["Company"] = relationship("Company", back_populates="pn_address_catalogs")
    plants: Mapped[list["PNAddressPlant"]] = relationship(
        "PNAddressPlant",
        back_populates="address_catalog",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="PNAddressPlant.sort_order",
    )
    measurements: Mapped[list["PNAddressMeasurement"]] = relationship(
        "PNAddressMeasurement",
        back_populates="address_catalog",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="PNAddressMeasurement.id",
    )
    job_rules: Mapped[list["PNAddressJobRule"]] = relationship(
        "PNAddressJobRule",
        back_populates="address_catalog",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="PNAddressJobRule.id",
    )


class PNAddressPlant(TimestampMixin, Base):
    __tablename__ = "pn_address_plants"
    __table_args__ = (
        Index("ix_pn_address_plants_company_id", "company_id"),
        Index("ix_pn_address_plants_address_catalog_id", "address_catalog_id"),
        UniqueConstraint("address_catalog_id", "name", name="uq_pn_address_plants_address_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    address_catalog_id: Mapped[int] = mapped_column(
        ForeignKey("pn_address_catalog.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    company: Mapped["Company"] = relationship("Company", back_populates="pn_address_plants")
    address_catalog: Mapped["PNAddressCatalog"] = relationship("PNAddressCatalog", back_populates="plants")
    measurements: Mapped[list["PNAddressMeasurement"]] = relationship(
        "PNAddressMeasurement",
        back_populates="plant",
        passive_deletes=True,
        order_by="PNAddressMeasurement.id",
    )
    job_rules: Mapped[list["PNAddressJobRule"]] = relationship(
        "PNAddressJobRule",
        back_populates="plant",
        passive_deletes=True,
        order_by="PNAddressJobRule.id",
    )


class PNAddressMeasurement(TimestampMixin, Base):
    __tablename__ = "pn_address_measurements"
    __table_args__ = (
        Index("ix_pn_address_measurements_company_id", "company_id"),
        Index("ix_pn_address_measurements_address_catalog_id", "address_catalog_id"),
        Index("ix_pn_address_measurements_plant_id", "plant_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    address_catalog_id: Mapped[int] = mapped_column(
        ForeignKey("pn_address_catalog.id", ondelete="CASCADE"),
        nullable=False,
    )
    plant_id: Mapped[int | None] = mapped_column(
        ForeignKey("pn_address_plants.id", ondelete="CASCADE"),
        nullable=True,
    )
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    width_m: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    height_m: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    company: Mapped["Company"] = relationship("Company", back_populates="pn_address_measurements")
    address_catalog: Mapped["PNAddressCatalog"] = relationship("PNAddressCatalog", back_populates="measurements")
    plant: Mapped["PNAddressPlant | None"] = relationship("PNAddressPlant", back_populates="measurements")


class PNAddressJobRule(TimestampMixin, Base):
    __tablename__ = "pn_address_job_rules"
    __table_args__ = (
        Index("ix_pn_address_job_rules_company_id", "company_id"),
        Index("ix_pn_address_job_rules_address_catalog_id", "address_catalog_id"),
        Index("ix_pn_address_job_rules_plant_id", "plant_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    address_catalog_id: Mapped[int] = mapped_column(
        ForeignKey("pn_address_catalog.id", ondelete="CASCADE"),
        nullable=False,
    )
    plant_id: Mapped[int | None] = mapped_column(
        ForeignKey("pn_address_plants.id", ondelete="CASCADE"),
        nullable=True,
    )
    rule_type: Mapped[str] = mapped_column(String(100), nullable=False)
    rule_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    company: Mapped["Company"] = relationship("Company", back_populates="pn_address_job_rules")
    address_catalog: Mapped["PNAddressCatalog"] = relationship("PNAddressCatalog", back_populates="job_rules")
    plant: Mapped["PNAddressPlant | None"] = relationship("PNAddressPlant", back_populates="job_rules")


class Appointment(TimestampMixin, Base):
    __tablename__ = "appointments"
    __table_args__ = (
        Index("ix_appointments_company_status", "company_id", "status"),
        Index("ix_appointments_company_start", "company_id", "start_at"),
        Index("ix_appointments_company_reminder", "company_id", "reminder_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quote_id: Mapped[int | None] = mapped_column(
        ForeignKey("quotes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assigned_installer_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    parent_appointment_id: Mapped[int | None] = mapped_column(
        ForeignKey("appointments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    address_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    service_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    event_title: Mapped[str | None] = mapped_column(String(200), nullable=True)

    calendar_event_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    installers: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    valor: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, name="appointment_status_enum"),
        default=AppointmentStatus.SCHEDULED,
        nullable=False,
    )
    reminder_status: Mapped[ReminderStatus] = mapped_column(
        Enum(ReminderStatus, name="reminder_status_enum"),
        default=ReminderStatus.PENDING,
        nullable=False,
    )

    reminder_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reschedule_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    finish_installer: Mapped[str | None] = mapped_column(Text, nullable=True)
    finish_payment: Mapped[str | None] = mapped_column(Text, nullable=True)
    finish_card_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    finish_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    company: Mapped["Company"] = relationship("Company", back_populates="appointments")
    client: Mapped["Client"] = relationship("Client", back_populates="appointments")
    quote: Mapped["Quote | None"] = relationship("Quote", back_populates="appointments")
    assigned_installer: Mapped["User | None"] = relationship(
        "User",
        back_populates="assigned_appointments",
        foreign_keys=[assigned_installer_id],
    )
    parent_appointment: Mapped["Appointment | None"] = relationship(
        "Appointment",
        remote_side=[id],
        foreign_keys=[parent_appointment_id],
    )

class PlatformSettings(TimestampMixin, Base):
    """Singleton table (always id=1) for global SaaS platform configuration."""

    __tablename__ = "platform_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    platform_name: Mapped[str] = mapped_column(String(100), default="AlphaSync", nullable=False)
    default_company_plan: Mapped[str | None] = mapped_column(String(50), nullable=True)
    default_service_domain: Mapped[str] = mapped_column(
        String(50), default="protection_network", nullable=False
    )
    allow_self_signup: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    support_email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    support_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    public_app_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    extra_flags: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class DomainDefinition(TimestampMixin, Base):
    """
    Entidade administrável para cada domínio de serviço da plataforma.

    - is_builtin=True  → domínio com motor em código (chatbot_flow.py, pricing_rules.py etc.)
    - is_builtin=False → domínio customizado criado pelo master via painel (futuro)
    - config_json      → configurações editáveis pelo master (textos, defaults, pricing simples)
    """

    __tablename__ = "domain_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
