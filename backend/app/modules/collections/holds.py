import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.audit.service import log_event
from app.modules.collections.models import Dispute, HoldReason, PaymentPromise, PromiseStatus, ReminderHold


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def active_holds(db: Session, tenant_id: uuid.UUID, invoice_id: uuid.UUID) -> list[ReminderHold]:
    return list(
        db.scalars(
            select(ReminderHold).where(
                ReminderHold.tenant_id == tenant_id,
                ReminderHold.invoice_id == invoice_id,
                ReminderHold.active.is_(True),
            )
        ).all()
    )


def has_active_hold(db: Session, tenant_id: uuid.UUID, invoice_id: uuid.UUID) -> bool:
    return len(active_holds(db, tenant_id, invoice_id)) > 0


def _upsert_hold(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    invoice_id: uuid.UUID,
    hold_reason: HoldReason,
    source_id: uuid.UUID,
    created_by: uuid.UUID | None,
    correlation_id: str,
) -> ReminderHold:
    existing = db.scalar(
        select(ReminderHold).where(
            ReminderHold.tenant_id == tenant_id,
            ReminderHold.invoice_id == invoice_id,
            ReminderHold.hold_reason == hold_reason,
            ReminderHold.source_id == source_id,
            ReminderHold.active.is_(True),
        )
    )
    if existing:
        return existing
    hold = ReminderHold(
        tenant_id=tenant_id,
        invoice_id=invoice_id,
        hold_reason=hold_reason,
        active=True,
        source_id=source_id,
        created_by=created_by,
    )
    db.add(hold)
    db.flush()
    log_event(
        db,
        tenant_id=tenant_id,
        actor_user_id=created_by,
        entity_type="reminder_hold",
        entity_id=str(hold.id),
        action="hold_activated",
        origin="staff",
        correlation_id=correlation_id,
        summary={"invoice_id": str(invoice_id), "hold_reason": hold_reason.value, "source_id": str(source_id)},
    )
    return hold


def release_hold(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    invoice_id: uuid.UUID,
    hold_reason: HoldReason,
    source_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
    correlation_id: str,
) -> bool:
    hold = db.scalar(
        select(ReminderHold).where(
            ReminderHold.tenant_id == tenant_id,
            ReminderHold.invoice_id == invoice_id,
            ReminderHold.hold_reason == hold_reason,
            ReminderHold.source_id == source_id,
            ReminderHold.active.is_(True),
        )
    )
    if hold is None:
        return False
    hold.active = False
    hold.released_at = _utcnow()
    db.flush()
    log_event(
        db,
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        entity_type="reminder_hold",
        entity_id=str(hold.id),
        action="hold_released",
        origin="staff",
        correlation_id=correlation_id,
        summary={"invoice_id": str(invoice_id), "hold_reason": hold_reason.value},
    )
    return True


def on_promise_confirmed(
    db: Session,
    user_id: uuid.UUID,
    promise: PaymentPromise,
    correlation_id: str,
) -> None:
    if promise.follow_up_date is None:
        promise.follow_up_date = promise.promised_date
    _upsert_hold(
        db,
        tenant_id=promise.tenant_id,
        invoice_id=promise.invoice_id,
        hold_reason=HoldReason.CONFIRMED_PROMISE,
        source_id=promise.id,
        created_by=user_id,
        correlation_id=correlation_id,
    )


def on_promise_terminal(
    db: Session,
    user_id: uuid.UUID | None,
    promise: PaymentPromise,
    correlation_id: str,
) -> None:
    release_hold(
        db,
        tenant_id=promise.tenant_id,
        invoice_id=promise.invoice_id,
        hold_reason=HoldReason.CONFIRMED_PROMISE,
        source_id=promise.id,
        actor_user_id=user_id,
        correlation_id=correlation_id,
    )


def on_dispute_confirmed(
    db: Session,
    user_id: uuid.UUID,
    dispute: Dispute,
    correlation_id: str,
) -> None:
    _upsert_hold(
        db,
        tenant_id=dispute.tenant_id,
        invoice_id=dispute.invoice_id,
        hold_reason=HoldReason.CONFIRMED_DISPUTE,
        source_id=dispute.id,
        created_by=user_id,
        correlation_id=correlation_id,
    )


def on_dispute_resolved_or_cancelled(
    db: Session,
    user_id: uuid.UUID | None,
    dispute: Dispute,
    correlation_id: str,
) -> None:
    release_hold(
        db,
        tenant_id=dispute.tenant_id,
        invoice_id=dispute.invoice_id,
        hold_reason=HoldReason.CONFIRMED_DISPUTE,
        source_id=dispute.id,
        actor_user_id=user_id,
        correlation_id=correlation_id,
    )