from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.core.responses import ApiResponse, success
from app.db.session import get_db
from app.modules.customers.models import Customer
from app.modules.invoices.aging import (
    bucket_invoice_counts,
    bucket_outstanding,
    days_overdue,
    today_karachi,
)
from app.modules.invoices.models import Invoice, InvoiceLifecycle
from app.modules.users.models import User

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

_OVERDUE_STATUS = "Overdue"


def _active_invoices(db: Session, tenant_id: UUID) -> list[Invoice]:
    return list(
        db.scalars(
            select(Invoice).where(
                Invoice.tenant_id == tenant_id,
                Invoice.lifecycle_status == InvoiceLifecycle.active,
            )
        ).all()
    )


@router.get("/summary", response_model=ApiResponse[dict])
def summary(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    today = today_karachi()
    rows = _active_invoices(db, user.tenant_id)
    outstanding = sum((r.outstanding_amount for r in rows), Decimal("0"))
    overdue_rows = [r for r in rows if r.due_date and days_overdue(r.due_date, today) > 0]
    overdue_amount = sum((r.outstanding_amount for r in overdue_rows), Decimal("0"))
    return success(
        {
            "as_of_date": today.isoformat(),
            "invoice_count": len(rows),
            "total_outstanding": str(outstanding),
            "overdue_invoice_count": len(overdue_rows),
            "overdue_amount": str(overdue_amount),
            "currency": "PKR",
            "disclaimer": "Totals from locally accepted invoices only; not FBR verified.",
        }
    )


@router.get("/aging", response_model=ApiResponse[dict])
def aging(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    rows = _active_invoices(db, user.tenant_id)
    pairs = [(r.due_date, r.outstanding_amount) for r in rows if r.due_date is not None]
    due_dates = [r.due_date for r in rows if r.due_date is not None]
    buckets = bucket_outstanding(pairs)
    counts = bucket_invoice_counts(due_dates)
    return success(
        {
            "as_of_date": today_karachi().isoformat(),
            "buckets": {k: str(v) for k, v in buckets.items()},
            "bucket_counts": counts,
            "disclaimer": "Aging uses Asia/Karachi business calendar.",
        }
    )


@router.get("/overdue-invoices", response_model=ApiResponse[list])
def overdue_invoices(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = Query(default=100, ge=1, le=500),
) -> ApiResponse[list]:
    today = today_karachi()
    rows = _active_invoices(db, user.tenant_id)
    overdue = [r for r in rows if r.due_date and days_overdue(r.due_date, today) > 0]
    overdue.sort(key=lambda r: days_overdue(r.due_date, today), reverse=True)
    if not overdue:
        return success([])

    payload = []
    slice_rows = overdue[:limit]
    customer_ids = {r.customer_id for r in slice_rows}
    customers = {
        c.id: c
        for c in db.scalars(
            select(Customer).where(Customer.id.in_(customer_ids), Customer.tenant_id == user.tenant_id)
        )
    }
    for inv in slice_rows:
        customer = customers.get(inv.customer_id)
        overdue_days = days_overdue(inv.due_date, today)
        payload.append(
            {
                "id": str(inv.id),
                "invoice_reference": inv.invoice_reference,
                "customer_id": str(inv.customer_id),
                "customer_name": customer.business_name if customer else "Unknown customer",
                "due_date": inv.due_date.isoformat(),
                "days_overdue": overdue_days,
                "outstanding_amount": str(inv.outstanding_amount),
                "currency": inv.currency,
                "status": _OVERDUE_STATUS,
            }
        )
    return success(payload)