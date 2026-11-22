import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _enum(enum_cls: type[enum.Enum]) -> Enum:
    return Enum(enum_cls, native_enum=False, length=32)


class CaseState(str, enum.Enum):
    OPEN = "OPEN"


class TaskType(str, enum.Enum):
    REMINDER = "REMINDER"
    FOLLOW_UP = "FOLLOW_UP"
    DOCUMENT_REQUEST = "DOCUMENT_REQUEST"
    PAYMENT_VERIFICATION = "PAYMENT_VERIFICATION"
    DISPUTE_RESOLUTION = "DISPUTE_RESOLUTION"


class TaskStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TaskSource(str, enum.Enum):
    RULE = "RULE"
    STAFF = "STAFF"


class TaskPriority(str, enum.Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"


class PromiseStatus(str, enum.Enum):
    RECORDED = "RECORDED"
    CONFIRMED = "CONFIRMED"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class DisputeStatus(str, enum.Enum):
    OPEN = "OPEN"
    CONFIRMED = "CONFIRMED"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"


class HoldReason(str, enum.Enum):
    CONFIRMED_PROMISE = "CONFIRMED_PROMISE"
    CONFIRMED_DISPUTE = "CONFIRMED_DISPUTE"


class RiskLevel(str, enum.Enum):
    STANDARD = "STANDARD"


class CollectionCase(Base):
    __tablename__ = "collection_cases"
    __table_args__ = (UniqueConstraint("tenant_id", "invoice_id", name="uq_collection_cases_tenant_invoice"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    state: Mapped[CaseState] = mapped_column(_enum(CaseState), nullable=False, default=CaseState.OPEN)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class FollowUpTask(Base):
    __tablename__ = "follow_up_tasks"
    __table_args__ = (UniqueConstraint("tenant_id", "dedupe_key", name="uq_follow_up_tasks_tenant_dedupe"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("collection_cases.id"), nullable=False)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False, index=True)
    task_type: Mapped[TaskType] = mapped_column(_enum(TaskType), nullable=False)
    status: Mapped[TaskStatus] = mapped_column(_enum(TaskStatus), nullable=False, default=TaskStatus.OPEN)
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    priority: Mapped[TaskPriority] = mapped_column(_enum(TaskPriority), nullable=False, default=TaskPriority.NORMAL)
    source: Mapped[TaskSource] = mapped_column(_enum(TaskSource), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(255), nullable=False)
    policy_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)


class ReminderPolicy(Base):
    """Stored defaults only. Scheduling behavior is Phase 2."""

    __tablename__ = "reminder_policies"
    __table_args__ = (UniqueConstraint("tenant_id", name="uq_reminder_policies_tenant"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    grace_days: Mapped[int] = mapped_column(nullable=False, default=0)
    timezone_name: Mapped[str] = mapped_column(String(64), nullable=False, default="Asia/Karachi")
    risk_level: Mapped[RiskLevel] = mapped_column(_enum(RiskLevel), nullable=False, default=RiskLevel.STANDARD)
    policy_version: Mapped[str] = mapped_column(String(64), nullable=False, default="m2-phase1-unscheduled")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PaymentPromise(Base):
    __tablename__ = "payment_promises"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False, index=True)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("collection_cases.id"), nullable=False)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    promised_date: Mapped[date] = mapped_column(Date, nullable=False)
    follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[PromiseStatus] = mapped_column(_enum(PromiseStatus), nullable=False, default=PromiseStatus.RECORDED)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Dispute(Base):
    __tablename__ = "disputes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False, index=True)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("collection_cases.id"), nullable=False)
    challenged_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[DisputeStatus] = mapped_column(_enum(DisputeStatus), nullable=False, default=DisputeStatus.OPEN)
    recorded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ReminderHold(Base):
    """Schema only in Phase 1. No API inserts holds until Phase 2."""

    __tablename__ = "reminder_holds"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False, index=True)
    hold_reason: Mapped[HoldReason] = mapped_column(_enum(HoldReason), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
