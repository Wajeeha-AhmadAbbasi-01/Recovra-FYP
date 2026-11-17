from datetime import date
from decimal import Decimal
from zoneinfo import ZoneInfo

KARACHI = ZoneInfo("Asia/Karachi")

BUCKETS = ("CURRENT", "1_30", "31_60", "61_90", "91_PLUS")


def today_karachi() -> date:
    from datetime import datetime

    return datetime.now(KARACHI).date()


def days_overdue(due_date: date, as_of: date | None = None) -> int:
    ref = as_of or today_karachi()
    return max(0, (ref - due_date).days)


def aging_bucket(due_date: date, as_of: date | None = None) -> str:
    ref = as_of or today_karachi()
    if due_date >= ref:
        return "CURRENT"
    overdue = days_overdue(due_date, ref)
    if overdue <= 30:
        return "1_30"
    if overdue <= 60:
        return "31_60"
    if overdue <= 90:
        return "61_90"
    return "91_PLUS"


def bucket_outstanding(rows: list[tuple[date | None, Decimal]]) -> dict[str, Decimal]:
    totals = {b: Decimal("0") for b in BUCKETS}
    for due_date, amount in rows:
        if due_date is None:
            continue
        bucket = aging_bucket(due_date)
        totals[bucket] += amount
    return totals