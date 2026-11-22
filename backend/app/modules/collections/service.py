import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.audit.models import AuditEvent
from app.modules.audit.service import log_event
from app.modules.collections import repository as repo
from app.modules.collections.models import (
    CollectionCase,
    Dispute,
    DisputeStatus,
    FollowUpTask,
    PaymentPromise,
    PromiseStatus,
    TaskSource,
    TaskStatus,
)
from app.modules.collections.schemas import DisputeCreate, DisputePatch, PromiseCreate, PromisePatch, TaskCreate, TaskPatch
from app.modules.invoices.aging import today_karachi
from app.modules.invoices.models import Invoice
from app.modules.users.models import User

TASK_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.OPEN: {TaskStatus.IN_PROGRESS, TaskStatus.ON_HOLD, TaskStatus.COMPLETED, TaskStatus.CANCELLED},
    TaskStatus.IN_PROGRESS: {TaskStatus.ON_HOLD, TaskStatus.COMPLETED, TaskStatus.CANCELLED},
    TaskStatus.ON_HOLD: {TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED, TaskStatus.CANCELLED},
    TaskStatus.COMPLETED: set(),
    TaskStatus.CANCELLED: set(),
}

PROMISE_TRANSITIONS: dict[PromiseStatus, set[PromiseStatus]] = {
    PromiseStatus.RECORDED: {PromiseStatus.CONFIRMED, PromiseStatus.CANCELLED},
    PromiseStatus.CONFIRMED: {PromiseStatus.FULFILLED, PromiseStatus.CANCELLED, PromiseStatus.EXPIRED},
    PromiseStatus.FULFILLED: set(),
    PromiseStatus.CANCELLED: set(),
    PromiseStatus.EXPIRED: set(),
}

DISPUTE_TRANSITIONS: dict[DisputeStatus, set[DisputeStatus]] = {
    DisputeStatus.OPEN: {DisputeStatus.CONFIRMED, DisputeStatus.CANCELLED},
    DisputeStatus.CONFIRMED: {DisputeStatus.RESOLVED},
    DisputeStatus.RESOLVED: set(),
    DisputeStatus.CANCELLED: set(),
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _reject(code: int, message: str) -> None:
    raise HTTPException(status_code=code, detail=message)


def _require_invoice(db: Session, user: User, invoice_id: uuid.UUID) -> Invoice:
    invoice = repo.invoice_for_tenant(db, user.tenant_id, invoice_id)
    if invoice is None:
        _reject(status.HTTP_404_NOT_FOUND, "Invoice not found")
    return invoice


def _ensure_case(db: Session, user: User, invoice: Invoice) -> CollectionCase:
    existing = repo.case_for_invoice(db, user.tenant_id, invoice.id)
    if existing:
        return existing
    case = CollectionCase(tenant_id=user.tenant_id, invoice_id=invoice.id, created_by=user.id)
    db.add(case)
    db.flush()
    return case


def _check_amount(amount: Decimal | None, outstanding: Decimal) -> None:
    if amount is None:
        return
    if amount > outstanding:
        _reject(status.HTTP_422_UNPROCESSABLE_ENTITY, "Amount cannot exceed the invoice outstanding balance")


def _audit(
    db: Session,
    user: User,
    *,
    entity_type: str,
    entity_id: uuid.UUID,
    action: str,
    invoice_id: uuid.UUID,
    correlation_id: str,
    before: dict | None = None,
    after: dict | None = None,
) -> None:
    log_event(
        db,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        entity_type=entity_type,
        entity_id=str(entity_id),
        action=action,
        origin="staff",
        correlation_id=correlation_id,
        summary={"invoice_id": str(invoice_id), "before": before, "after": after},
    )


def create_task(db: Session, user: User, payload: TaskCreate, correlation_id: str) -> FollowUpTask:
    invoice = _require_invoice(db, user, payload.invoice_id)
    if payload.assignee_id and repo.active_member(db, user.tenant_id, payload.assignee_id) is None:
        _reject(status.HTTP_404_NOT_FOUND, "Assignee not found in this workspace")
    case = _ensure_case(db, user, invoice)
    task = FollowUpTask(
        tenant_id=user.tenant_id,
        case_id=case.id,
        invoice_id=invoice.id,
        task_type=payload.task_type,
        status=TaskStatus.OPEN,
        assignee_id=payload.assignee_id,
        due_at=payload.due_at,
        priority=payload.priority,
        source=TaskSource.STAFF,
        reason=payload.reason.strip(),
        dedupe_key=f"staff:{uuid.uuid4()}",
        policy_version=None,
    )
    db.add(task)
    db.flush()
    _audit(
        db,
        user,
        entity_type="follow_up_task",
        entity_id=task.id,
        action="task_created",
        invoice_id=invoice.id,
        correlation_id=correlation_id,
        after={"status": task.status.value, "source": task.source.value},
    )
    return task


def update_task(db: Session, user: User, task_id: uuid.UUID, payload: TaskPatch, correlation_id: str) -> FollowUpTask:
    task = repo.task_for_tenant(db, user.tenant_id, task_id)
    if task is None:
        _reject(status.HTTP_404_NOT_FOUND, "Task not found")
    invoice = _require_invoice(db, user, task.invoice_id)
    before = {"status": task.status.value, "assignee_id": str(task.assignee_id) if task.assignee_id else None}
    if payload.assignee_id and payload.clear_assignee:
        _reject(status.HTTP_422_UNPROCESSABLE_ENTITY, "Choose assignment or clear it, not both")
    if payload.assignee_id is not None:
        if repo.active_member(db, user.tenant_id, payload.assignee_id) is None:
            _reject(status.HTTP_404_NOT_FOUND, "Assignee not found in this workspace")
        task.assignee_id = payload.assignee_id
    if payload.clear_assignee:
        task.assignee_id = None
    if payload.due_at is not None:
        task.due_at = payload.due_at
    if payload.priority is not None:
        task.priority = payload.priority
    if payload.status is not None and payload.status != task.status:
        allowed = TASK_TRANSITIONS[task.status]
        if payload.status not in allowed:
            _reject(status.HTTP_409_CONFLICT, f"Cannot change task from {task.status.value} to {payload.status.value}")
        task.status = payload.status
        if payload.status == TaskStatus.COMPLETED:
            task.completed_at = _utcnow()
            task.completed_by = user.id
    _audit(
        db,
        user,
        entity_type="follow_up_task",
        entity_id=task.id,
        action="task_updated",
        invoice_id=invoice.id,
        correlation_id=correlation_id,
        before=before,
        after={"status": task.status.value, "assignee_id": str(task.assignee_id) if task.assignee_id else None},
    )
    return task


def list_tasks(db: Session, user: User, *, status_filter, assignee_id, customer_id, overdue, page: int, page_size: int):
    stmt = repo.task_query(
        user.tenant_id,
        status=status_filter,
        assignee_id=assignee_id,
        customer_id=customer_id,
        overdue=overdue,
        today=today_karachi(),
    )
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
    return rows, int(total)


def record_promise(db: Session, user: User, invoice_id: uuid.UUID, payload: PromiseCreate, correlation_id: str) -> PaymentPromise:
    invoice = _require_invoice(db, user, invoice_id)
    _check_amount(payload.amount, invoice.outstanding_amount)
    case = _ensure_case(db, user, invoice)
    promise = PaymentPromise(
        tenant_id=user.tenant_id,
        invoice_id=invoice.id,
        case_id=case.id,
        amount=payload.amount,
        promised_date=payload.promised_date,
        follow_up_date=payload.follow_up_date,
        status=PromiseStatus.RECORDED,
        note=payload.note,
        recorded_by=user.id,
    )
    db.add(promise)
    db.flush()
    _audit(
        db,
        user,
        entity_type="payment_promise",
        entity_id=promise.id,
        action="promise_recorded",
        invoice_id=invoice.id,
        correlation_id=correlation_id,
        after={"status": promise.status.value, "promised_date": promise.promised_date.isoformat()},
    )
    return promise


def transition_promise(db: Session, user: User, promise_id: uuid.UUID, payload: PromisePatch, correlation_id: str) -> PaymentPromise:
    promise = repo.promise_for_tenant(db, user.tenant_id, promise_id)
    if promise is None:
        _reject(status.HTTP_404_NOT_FOUND, "Promise not found")
    if payload.status == promise.status:
        return promise
    if payload.status not in PROMISE_TRANSITIONS[promise.status]:
        _reject(status.HTTP_409_CONFLICT, f"Cannot change promise from {promise.status.value} to {payload.status.value}")
    before = promise.status.value
    promise.status = payload.status
    if payload.status == PromiseStatus.CONFIRMED:
        promise.confirmed_by = user.id
    _audit(
        db,
        user,
        entity_type="payment_promise",
        entity_id=promise.id,
        action="promise_transition",
        invoice_id=promise.invoice_id,
        correlation_id=correlation_id,
        before={"status": before},
        after={"status": promise.status.value},
    )
    return promise


def record_dispute(db: Session, user: User, invoice_id: uuid.UUID, payload: DisputeCreate, correlation_id: str) -> Dispute:
    invoice = _require_invoice(db, user, invoice_id)
    _check_amount(payload.challenged_amount, invoice.outstanding_amount)
    case = _ensure_case(db, user, invoice)
    dispute = Dispute(
        tenant_id=user.tenant_id,
        invoice_id=invoice.id,
        case_id=case.id,
        challenged_amount=payload.challenged_amount,
        reason=payload.reason.strip(),
        status=DisputeStatus.OPEN,
        recorded_by=user.id,
    )
    db.add(dispute)
    db.flush()
    _audit(
        db,
        user,
        entity_type="dispute",
        entity_id=dispute.id,
        action="dispute_recorded",
        invoice_id=invoice.id,
        correlation_id=correlation_id,
        after={"status": dispute.status.value},
    )
    return dispute


def transition_dispute(db: Session, user: User, dispute_id: uuid.UUID, payload: DisputePatch, correlation_id: str) -> Dispute:
    dispute = repo.dispute_for_tenant(db, user.tenant_id, dispute_id)
    if dispute is None:
        _reject(status.HTTP_404_NOT_FOUND, "Dispute not found")
    if payload.status == dispute.status:
        return dispute
    if payload.status not in DISPUTE_TRANSITIONS[dispute.status]:
        _reject(status.HTTP_409_CONFLICT, f"Cannot change dispute from {dispute.status.value} to {payload.status.value}")
    before = dispute.status.value
    dispute.status = payload.status
    if payload.status == DisputeStatus.CONFIRMED:
        dispute.confirmed_by = user.id
    if payload.status == DisputeStatus.RESOLVED:
        dispute.resolved_by = user.id
        dispute.resolution_note = payload.resolution_note
    _audit(
        db,
        user,
        entity_type="dispute",
        entity_id=dispute.id,
        action="dispute_transition",
        invoice_id=dispute.invoice_id,
        correlation_id=correlation_id,
        before={"status": before},
        after={"status": dispute.status.value},
    )
    return dispute


def timeline(db: Session, user: User, invoice_id: uuid.UUID, page: int, page_size: int) -> tuple[list[AuditEvent], int]:
    if repo.invoice_for_tenant(db, user.tenant_id, invoice_id) is None:
        _reject(status.HTTP_404_NOT_FOUND, "Invoice not found")
    invoice_key = str(invoice_id)
    rows = db.scalars(
        select(AuditEvent).where(AuditEvent.tenant_id == user.tenant_id).order_by(AuditEvent.created_at.desc())
    ).all()
    matched = [row for row in rows if (row.summary or {}).get("invoice_id") == invoice_key]
    start = (page - 1) * page_size
    return matched[start : start + page_size], len(matched)
