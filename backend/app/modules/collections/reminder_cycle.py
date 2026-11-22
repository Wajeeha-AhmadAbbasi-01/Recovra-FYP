"""Idempotent routine reminder task generation. Does not send customer email."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.audit.service import log_event
from app.modules.collections import holds
from app.modules.collections.models import (
    CollectionCase,
    FollowUpTask,
    PaymentPromise,
    PromiseStatus,
    TaskSource,
    TaskStatus,
    TaskType,
)
from app.modules.collections.policy import ensure_reminder_policy
from app.modules.collections.rules.eligibility import (
    EligibilityResult,
    ReminderDecision,
    evaluate_routine_reminder,
)
from app.modules.collections.repository import case_for_invoice
from app.modules.invoices.aging import today_karachi
from app.modules.invoices.models import Invoice, InvoiceLifecycle


@dataclass
class CycleResult:
    evaluated: int
    created: int
    skipped: int
    expired_promises: int
    as_of: date
    policy_version: str


def _ensure_case(db: Session, tenant_id: uuid.UUID, invoice_id: uuid.UUID) -> CollectionCase:
    existing = case_for_invoice(db, tenant_id, invoice_id)
    if existing:
        return existing
    case = CollectionCase(tenant_id=tenant_id, invoice_id=invoice_id, created_by=None)
    db.add(case)
    db.flush()
    return case


def expire_confirmed_promises(db: Session, tenant_id: uuid.UUID, as_of: date) -> int:
    rows = db.scalars(
        select(PaymentPromise).where(
            PaymentPromise.tenant_id == tenant_id,
            PaymentPromise.status == PromiseStatus.CONFIRMED,
            PaymentPromise.promised_date < as_of,
        )
    ).all()
    count = 0
    for promise in rows:
        promise.status = PromiseStatus.EXPIRED
        holds.on_promise_terminal(db, None, promise, f"expire-{promise.id}")
        count += 1
    return count


def evaluate_invoice(
    db: Session,
    invoice: Invoice,
    *,
    as_of: date | None = None,
) -> EligibilityResult:
    policy = ensure_reminder_policy(db, invoice.tenant_id)
    ref = as_of or today_karachi()
    return evaluate_routine_reminder(
        due_date=invoice.due_date,
        outstanding=invoice.outstanding_amount,
        lifecycle_active=invoice.lifecycle_status == InvoiceLifecycle.active,
        grace_days=policy.grace_days,
        as_of=ref,
        has_active_hold=holds.has_active_hold(db, invoice.tenant_id, invoice.id),
        policy_enabled=policy.enabled,
        policy_version=policy.policy_version,
        invoice_id=invoice.id,
    )


def _task_exists(db: Session, tenant_id: uuid.UUID, dedupe_key: str) -> bool:
    return (
        db.scalar(
            select(FollowUpTask.id).where(
                FollowUpTask.tenant_id == tenant_id,
                FollowUpTask.dedupe_key == dedupe_key,
            )
        )
        is not None
    )


def create_routine_task_if_eligible(
    db: Session,
    invoice: Invoice,
    *,
    as_of: date | None = None,
    correlation_id: str | None = None,
) -> FollowUpTask | None:
    result = evaluate_invoice(db, invoice, as_of=as_of)
    if result.decision != ReminderDecision.CREATE_ROUTINE_TASK or not result.dedupe_key:
        return None
    if _task_exists(db, invoice.tenant_id, result.dedupe_key):
        return None
    case = _ensure_case(db, invoice.tenant_id, invoice.id)
    policy = ensure_reminder_policy(db, invoice.tenant_id)
    task = FollowUpTask(
        tenant_id=invoice.tenant_id,
        case_id=case.id,
        invoice_id=invoice.id,
        task_type=TaskType.REMINDER,
        status=TaskStatus.OPEN,
        assignee_id=None,
        due_at=None,
        source=TaskSource.RULE,
        reason=result.reason,
        dedupe_key=result.dedupe_key,
        policy_version=policy.policy_version,
    )
    db.add(task)
    db.flush()
    cid = correlation_id or str(uuid.uuid4())
    log_event(
        db,
        tenant_id=invoice.tenant_id,
        actor_user_id=None,
        entity_type="follow_up_task",
        entity_id=str(task.id),
        action="task_created",
        origin="SYSTEM",
        correlation_id=cid,
        summary={"invoice_id": str(invoice.id), "source": "RULE", "reason": result.reason},
    )
    return task


def run_tenant_reminder_cycle(
    db: Session,
    tenant_id: uuid.UUID,
    *,
    as_of: date | None = None,
    correlation_id: str | None = None,
) -> CycleResult:
    ref = as_of or today_karachi()
    policy = ensure_reminder_policy(db, tenant_id)
    expired = expire_confirmed_promises(db, tenant_id, ref)
    invoices = db.scalars(
        select(Invoice).where(
            Invoice.tenant_id == tenant_id,
            Invoice.lifecycle_status == InvoiceLifecycle.active,
            Invoice.outstanding_amount > 0,
        )
    ).all()
    created = 0
    skipped = 0
    cid = correlation_id or str(uuid.uuid4())
    for invoice in invoices:
        task = create_routine_task_if_eligible(db, invoice, as_of=ref, correlation_id=cid)
        if task:
            created += 1
        else:
            skipped += 1
    return CycleResult(
        evaluated=len(invoices),
        created=created,
        skipped=skipped,
        expired_promises=expired,
        as_of=ref,
        policy_version=policy.policy_version,
    )


def preview_tenant_reminders(db: Session, tenant_id: uuid.UUID, *, as_of: date | None = None) -> list[dict]:
    ref = as_of or today_karachi()
    policy = ensure_reminder_policy(db, tenant_id)
    rows = db.scalars(
        select(Invoice).where(
            Invoice.tenant_id == tenant_id,
            Invoice.lifecycle_status == InvoiceLifecycle.active,
        )
    ).all()
    items = []
    for inv in rows:
        ev = evaluate_invoice(db, inv, as_of=ref)
        items.append(
            {
                "invoice_id": str(inv.id),
                "invoice_reference": inv.invoice_reference,
                "due_date": inv.due_date.isoformat() if inv.due_date else None,
                "outstanding_amount": str(inv.outstanding_amount),
                "decision": ev.decision.value,
                "reason": ev.reason,
                "next_eligible_date": ev.next_eligible_date.isoformat() if ev.next_eligible_date else None,
                "would_create_task": ev.decision == ReminderDecision.CREATE_ROUTINE_TASK
                and ev.dedupe_key
                and not _task_exists(db, tenant_id, ev.dedupe_key),
                "sends_customer_email": False,
                "policy_version": policy.policy_version,
            }
        )
    return items