import uuid

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.modules.collections.models import (
    CollectionCase,
    Dispute,
    FollowUpTask,
    PaymentPromise,
    ReminderHold,
)
from app.modules.customers.models import Customer
from app.modules.invoices.models import Invoice, InvoiceLifecycle
from app.modules.users.models import User


def invoice_for_tenant(db: Session, tenant_id: uuid.UUID, invoice_id: uuid.UUID) -> Invoice | None:
    row = db.get(Invoice, invoice_id)
    if row is None or row.tenant_id != tenant_id:
        return None
    return row


def active_member(db: Session, tenant_id: uuid.UUID, user_id: uuid.UUID) -> User | None:
    row = db.get(User, user_id)
    if row is None or row.tenant_id != tenant_id or not row.is_active:
        return None
    return row


def case_for_invoice(db: Session, tenant_id: uuid.UUID, invoice_id: uuid.UUID) -> CollectionCase | None:
    return db.scalar(
        select(CollectionCase).where(
            CollectionCase.tenant_id == tenant_id,
            CollectionCase.invoice_id == invoice_id,
        )
    )


def task_for_tenant(db: Session, tenant_id: uuid.UUID, task_id: uuid.UUID) -> FollowUpTask | None:
    row = db.get(FollowUpTask, task_id)
    if row is None or row.tenant_id != tenant_id:
        return None
    return row


def promises_for_invoice(db: Session, tenant_id: uuid.UUID, invoice_id: uuid.UUID) -> list[PaymentPromise]:
    return list(
        db.scalars(
            select(PaymentPromise)
            .where(PaymentPromise.tenant_id == tenant_id, PaymentPromise.invoice_id == invoice_id)
            .order_by(PaymentPromise.created_at.desc())
        ).all()
    )


def disputes_for_invoice(db: Session, tenant_id: uuid.UUID, invoice_id: uuid.UUID) -> list[Dispute]:
    return list(
        db.scalars(
            select(Dispute)
            .where(Dispute.tenant_id == tenant_id, Dispute.invoice_id == invoice_id)
            .order_by(Dispute.created_at.desc())
        ).all()
    )


def promise_for_tenant(db: Session, tenant_id: uuid.UUID, promise_id: uuid.UUID) -> PaymentPromise | None:
    row = db.get(PaymentPromise, promise_id)
    if row is None or row.tenant_id != tenant_id:
        return None
    return row


def dispute_for_tenant(db: Session, tenant_id: uuid.UUID, dispute_id: uuid.UUID) -> Dispute | None:
    row = db.get(Dispute, dispute_id)
    if row is None or row.tenant_id != tenant_id:
        return None
    return row


def case_for_tenant(db: Session, tenant_id: uuid.UUID, case_id: uuid.UUID) -> CollectionCase | None:
    row = db.get(CollectionCase, case_id)
    if row is None or row.tenant_id != tenant_id:
        return None
    return row


def active_hold_count(db: Session, tenant_id: uuid.UUID, invoice_id: uuid.UUID) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(ReminderHold)
            .where(
                ReminderHold.tenant_id == tenant_id,
                ReminderHold.invoice_id == invoice_id,
                ReminderHold.active.is_(True),
            )
        )
        or 0
    )


def task_query(
    tenant_id: uuid.UUID,
    *,
    status: str | None,
    assignee_id: uuid.UUID | None,
    customer_id: uuid.UUID | None,
    overdue: bool | None,
    today,
) -> Select:
    stmt = (
        select(FollowUpTask)
        .join(Invoice, FollowUpTask.invoice_id == Invoice.id)
        .where(FollowUpTask.tenant_id == tenant_id, Invoice.tenant_id == tenant_id)
    )
    if status:
        stmt = stmt.where(FollowUpTask.status == status)
    if assignee_id:
        stmt = stmt.where(FollowUpTask.assignee_id == assignee_id)
    if customer_id:
        stmt = stmt.where(Invoice.customer_id == customer_id)
    if overdue:
        stmt = stmt.where(
            Invoice.due_date.is_not(None),
            Invoice.due_date < today,
            Invoice.outstanding_amount > 0,
            Invoice.lifecycle_status == InvoiceLifecycle.active,
        )
    return stmt.order_by(FollowUpTask.created_at.desc())


def customer_name(db: Session, customer_id: uuid.UUID) -> str | None:
    customer = db.get(Customer, customer_id)
    return customer.business_name if customer else None
