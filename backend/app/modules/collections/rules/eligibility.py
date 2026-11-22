"""Pure reminder eligibility. No database I/O."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from enum import Enum


class ReminderDecision(str, Enum):
    SKIP = "SKIP"
    CREATE_ROUTINE_TASK = "CREATE_ROUTINE_TASK"


@dataclass(frozen=True)
class EligibilityResult:
    decision: ReminderDecision
    reason: str
    next_eligible_date: date | None
    dedupe_key: str | None


def first_eligible_reminder_date(due_date: date, grace_days: int) -> date:
    """First Karachi calendar day a routine staff reminder may be created (not email)."""
    return due_date + timedelta(days=grace_days + 1)


def routine_reminder_dedupe_key(policy_version: str, invoice_id: uuid.UUID, due_date: date) -> str:
    return f"rule:{policy_version}:routine:{invoice_id}:{due_date.isoformat()}"


def evaluate_routine_reminder(
    *,
    due_date: date | None,
    outstanding: Decimal,
    lifecycle_active: bool,
    grace_days: int,
    as_of: date,
    has_active_hold: bool,
    policy_enabled: bool,
    policy_version: str,
    invoice_id: uuid.UUID,
) -> EligibilityResult:
    if not policy_enabled:
        return EligibilityResult(ReminderDecision.SKIP, "policy_disabled", None, None)
    if not lifecycle_active:
        return EligibilityResult(ReminderDecision.SKIP, "invoice_not_active", None, None)
    if outstanding <= 0:
        return EligibilityResult(ReminderDecision.SKIP, "no_outstanding_balance", None, None)
    if due_date is None:
        return EligibilityResult(ReminderDecision.SKIP, "missing_due_date", None, None)
    if has_active_hold:
        return EligibilityResult(
            ReminderDecision.SKIP,
            "active_reminder_hold",
            None,
            None,
        )

    first_eligible = first_eligible_reminder_date(due_date, grace_days)
    if as_of < first_eligible:
        return EligibilityResult(
            ReminderDecision.SKIP,
            "not_yet_eligible",
            first_eligible,
            None,
        )

    dedupe = routine_reminder_dedupe_key(policy_version, invoice_id, due_date)
    return EligibilityResult(
        ReminderDecision.CREATE_ROUTINE_TASK,
        "overdue_routine_reminder",
        first_eligible,
        dedupe,
    )