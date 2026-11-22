from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.modules.collections.rules.eligibility import ReminderDecision, evaluate_routine_reminder


def test_not_eligible_before_grace():
    inv = uuid4()
    result = evaluate_routine_reminder(
        due_date=date(2026, 1, 10),
        outstanding=Decimal("100"),
        lifecycle_active=True,
        grace_days=0,
        as_of=date(2026, 1, 10),
        has_active_hold=False,
        policy_enabled=True,
        policy_version="t",
        invoice_id=inv,
    )
    assert result.decision == ReminderDecision.SKIP
    assert result.reason == "not_yet_eligible"


def test_eligible_overdue_no_hold():
    inv = uuid4()
    result = evaluate_routine_reminder(
        due_date=date(2026, 1, 10),
        outstanding=Decimal("100"),
        lifecycle_active=True,
        grace_days=0,
        as_of=date(2026, 1, 11),
        has_active_hold=False,
        policy_enabled=True,
        policy_version="v1",
        invoice_id=inv,
    )
    assert result.decision == ReminderDecision.CREATE_ROUTINE_TASK
    assert result.dedupe_key and "v1" in result.dedupe_key


def test_skip_on_hold():
    inv = uuid4()
    result = evaluate_routine_reminder(
        due_date=date(2026, 1, 1),
        outstanding=Decimal("50"),
        lifecycle_active=True,
        grace_days=0,
        as_of=date(2026, 1, 20),
        has_active_hold=True,
        policy_enabled=True,
        policy_version="v1",
        invoice_id=inv,
    )
    assert result.decision == ReminderDecision.SKIP
    assert result.reason == "active_reminder_hold"