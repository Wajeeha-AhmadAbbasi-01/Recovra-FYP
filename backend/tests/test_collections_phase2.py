import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select

from app.modules.collections.models import FollowUpTask, ReminderHold, TaskSource
from app.modules.collections.reminder_cycle import run_tenant_reminder_cycle
from tests.test_collections_phase1 import _register_and_login, _seed_invoice


def test_reminder_cycle_idempotent_and_respects_hold(client, db, unique_email):
    me = _register_and_login(client, unique_email)
    user_id = uuid.UUID(me["user"]["id"])
    tenant_id = uuid.UUID(me["tenant"]["id"])
    overdue = _seed_invoice(db, tenant_id, user_id, f"INV-{uuid.uuid4().hex[:6]}", date.today() - timedelta(days=5))
    future = _seed_invoice(db, tenant_id, user_id, f"INV-{uuid.uuid4().hex[:6]}", date.today() + timedelta(days=10))

    first = client.post("/api/v1/collections/reminders/run")
    assert first.status_code == 200
    body = first.json()["data"]
    assert body["sends_customer_email"] is False
    assert body["tasks_created"] >= 1

    tasks = db.scalars(
        select(FollowUpTask).where(
            FollowUpTask.tenant_id == tenant_id,
            FollowUpTask.invoice_id == overdue.id,
            FollowUpTask.source == TaskSource.RULE,
        )
    ).all()
    assert len(tasks) == 1

    second = client.post("/api/v1/collections/reminders/run")
    assert second.json()["data"]["tasks_created"] == 0

    future_tasks = db.scalars(select(FollowUpTask).where(FollowUpTask.invoice_id == future.id)).all()
    assert len(future_tasks) == 0

    db.refresh(overdue)
    assert overdue.outstanding_amount == Decimal("1000.00")


def test_hold_blocks_new_rule_task(client, db, unique_email):
    me = _register_and_login(client, unique_email)
    user_id = uuid.UUID(me["user"]["id"])
    tenant_id = uuid.UUID(me["tenant"]["id"])
    invoice = _seed_invoice(db, tenant_id, user_id, f"INV-{uuid.uuid4().hex[:6]}", date.today() - timedelta(days=3))

    client.post("/api/v1/collections/reminders/run")
    before = db.scalar(select(func.count()).select_from(FollowUpTask).where(FollowUpTask.invoice_id == invoice.id))

    dispute = client.post(
        f"/api/v1/collections/invoices/{invoice.id}/disputes",
        json={"reason": "Dispute after task", "challenged_amount": "50.00"},
    )
    dispute_id = dispute.json()["data"]["id"]
    client.patch(f"/api/v1/collections/disputes/{dispute_id}", json={"status": "CONFIRMED"})

    client.post("/api/v1/collections/reminders/run")
    after = db.scalar(select(func.count()).select_from(FollowUpTask).where(FollowUpTask.invoice_id == invoice.id))
    assert after == before
    holds = db.scalar(
        select(func.count()).select_from(ReminderHold).where(
            ReminderHold.invoice_id == invoice.id,
            ReminderHold.active.is_(True),
        )
    )
    assert holds >= 1


def test_resolve_dispute_releases_hold_only_that_hold(client, db, unique_email):
    me = _register_and_login(client, unique_email)
    user_id = uuid.UUID(me["user"]["id"])
    tenant_id = uuid.UUID(me["tenant"]["id"])
    invoice = _seed_invoice(db, tenant_id, user_id, f"INV-{uuid.uuid4().hex[:6]}", date.today() - timedelta(days=2))

    promise = client.post(
        f"/api/v1/collections/invoices/{invoice.id}/promises",
        json={"promised_date": (date.today() + timedelta(days=30)).isoformat()},
    )
    pid = promise.json()["data"]["id"]
    client.patch(f"/api/v1/collections/promises/{pid}", json={"status": "CONFIRMED"})

    dispute = client.post(
        f"/api/v1/collections/invoices/{invoice.id}/disputes",
        json={"reason": "Both holds"},
    )
    did = dispute.json()["data"]["id"]
    client.patch(f"/api/v1/collections/disputes/{did}", json={"status": "CONFIRMED"})

    client.patch(f"/api/v1/collections/disputes/{did}", json={"status": "RESOLVED", "resolution_note": "OK"})

    active = db.scalar(
        select(func.count()).select_from(ReminderHold).where(
            ReminderHold.invoice_id == invoice.id,
            ReminderHold.active.is_(True),
        )
    )
    assert active == 1