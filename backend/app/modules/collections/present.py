from sqlalchemy.orm import Session

from app.modules.collections.models import CollectionCase, Dispute, FollowUpTask, PaymentPromise
from app.modules.collections.repository import customer_name
from app.modules.invoices.models import Invoice


def _iso(value) -> str | None:
    return value.isoformat() if value is not None else None


def task_payload(db: Session, task: FollowUpTask, invoice: Invoice) -> dict:
    return {
        "id": str(task.id),
        "case_id": str(task.case_id),
        "invoice_id": str(task.invoice_id),
        "invoice_reference": invoice.invoice_reference,
        "customer_id": str(invoice.customer_id),
        "customer_name": customer_name(db, invoice.customer_id),
        "outstanding_amount": str(invoice.outstanding_amount),
        "invoice_due_date": _iso(invoice.due_date),
        "invoice_lifecycle": invoice.lifecycle_status.value,
        "task_type": task.task_type.value,
        "status": task.status.value,
        "assignee_id": str(task.assignee_id) if task.assignee_id else None,
        "due_at": _iso(task.due_at),
        "priority": task.priority.value,
        "source": task.source.value,
        "reason": task.reason,
        "dedupe_key": task.dedupe_key,
        "policy_version": task.policy_version,
        "created_at": _iso(task.created_at),
        "completed_at": _iso(task.completed_at),
        "completed_by": str(task.completed_by) if task.completed_by else None,
    }


def case_payload(case: CollectionCase, invoice: Invoice) -> dict:
    return {
        "id": str(case.id),
        "invoice_id": str(case.invoice_id),
        "invoice_reference": invoice.invoice_reference,
        "state": case.state.value,
        "outstanding_amount": str(invoice.outstanding_amount),
        "created_at": _iso(case.created_at),
    }


def scheduling_effect_for_invoice(db: Session, tenant_id, invoice_id) -> str:
    from uuid import UUID

    from app.modules.collections.repository import active_hold_count

    iid = invoice_id if isinstance(invoice_id, UUID) else UUID(str(invoice_id))
    return "hold_active" if active_hold_count(db, tenant_id, iid) > 0 else "routine_may_apply"


def promise_payload(db: Session, promise: PaymentPromise) -> dict:
    return {
        "id": str(promise.id),
        "invoice_id": str(promise.invoice_id),
        "case_id": str(promise.case_id),
        "amount": str(promise.amount) if promise.amount is not None else None,
        "promised_date": promise.promised_date.isoformat(),
        "follow_up_date": _iso(promise.follow_up_date),
        "status": promise.status.value,
        "note": promise.note,
        "recorded_by": str(promise.recorded_by),
        "confirmed_by": str(promise.confirmed_by) if promise.confirmed_by else None,
        "scheduling_effect": scheduling_effect_for_invoice(db, promise.tenant_id, promise.invoice_id),
    }


def dispute_payload(db: Session, dispute: Dispute) -> dict:
    return {
        "id": str(dispute.id),
        "invoice_id": str(dispute.invoice_id),
        "case_id": str(dispute.case_id),
        "challenged_amount": str(dispute.challenged_amount) if dispute.challenged_amount is not None else None,
        "reason": dispute.reason,
        "status": dispute.status.value,
        "resolution_note": dispute.resolution_note,
        "recorded_by": str(dispute.recorded_by),
        "confirmed_by": str(dispute.confirmed_by) if dispute.confirmed_by else None,
        "resolved_by": str(dispute.resolved_by) if dispute.resolved_by else None,
        "scheduling_effect": scheduling_effect_for_invoice(db, dispute.tenant_id, dispute.invoice_id),
    }
