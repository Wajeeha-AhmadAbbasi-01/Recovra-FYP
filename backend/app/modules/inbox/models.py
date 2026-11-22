import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _enum(enum_cls: type[enum.Enum]) -> Enum:
    return Enum(enum_cls, native_enum=False, length=32)


class LinkState(str, enum.Enum):
    SUGGESTED = "SUGGESTED"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"


class IngestionState(str, enum.Enum):
    STORED = "STORED"


class Mailbox(Base):
    __tablename__ = "mailboxes"
    __table_args__ = (UniqueConstraint("tenant_id", "provider", name="uq_mailboxes_tenant_provider"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False, default="Finance inbox (mock)")
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="mock")
    folder: Mapped[str] = mapped_column(String(128), nullable=False, default="INBOX")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InboundMessage(Base):
    __tablename__ = "inbound_messages"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "mailbox_id",
            "folder",
            "uidvalidity",
            "uid",
            name="uq_inbound_messages_uid",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    mailbox_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("mailboxes.id"), nullable=False)
    folder: Mapped[str] = mapped_column(String(128), nullable=False)
    uidvalidity: Mapped[int] = mapped_column(Integer, nullable=False)
    uid: Mapped[int] = mapped_column(Integer, nullable=False)
    rfc_message_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    sender: Mapped[str] = mapped_column(String(320), nullable=False)
    recipient: Mapped[str] = mapped_column(String(320), nullable=False)
    subject: Mapped[str] = mapped_column(String(998), nullable=False, default="")
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sanitized_body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content_type: Mapped[str] = mapped_column(String(128), nullable=False, default="text/plain")
    ingestion_state: Mapped[IngestionState] = mapped_column(_enum(IngestionState), nullable=False, default=IngestionState.STORED)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MessageInvoiceLink(Base):
    __tablename__ = "message_invoice_links"
    __table_args__ = (UniqueConstraint("tenant_id", "message_id", "invoice_id", name="uq_message_invoice_link"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("inbound_messages.id"), nullable=False, index=True)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    link_state: Mapped[LinkState] = mapped_column(_enum(LinkState), nullable=False, default=LinkState.SUGGESTED)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
