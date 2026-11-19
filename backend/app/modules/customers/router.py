from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.core.responses import ApiResponse, success
from app.db.session import get_db
from app.modules.customers.models import Customer
from app.modules.invoices.aging import days_overdue, today_karachi
from app.modules.invoices.models import Invoice, InvoiceLifecycle
from app.modules.users.models import User

router = APIRouter(prefix="/api/v1/customers", tags=["customers"])


def _customer_invoice_stats(db: Session, tenant_id: UUID, customer_id: UUID) -> dict:
    today = today_karachi()
    rows = list(
        db.scalars(
            select(Invoice).where(
                Invoice.tenant_id == tenant_id,
                Invoice.customer_id == customer_id,
                Invoice.lifecycle_status == InvoiceLifecycle.active,
            )
        ).all()
    )
    outstanding = sum((r.outstanding_amount for r in rows), Decimal("0"))
    overdue_count = sum(
        1 for r in rows if r.due_date and days_overdue(r.due_date, today) > 0 and r.outstanding_amount > 0
    )
    return {
        "invoice_count": len(rows),
        "outstanding_total": str(outstanding),
        "overdue_count": overdue_count,
    }


@router.get("", response_model=ApiResponse[list])
def list_customers(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[list]:
    rows = db.scalars(
        select(Customer).where(Customer.tenant_id == user.tenant_id).order_by(Customer.business_name)
    ).all()
    payload = []
    for r in rows:
        stats = _customer_invoice_stats(db, user.tenant_id, r.id)
        payload.append(
            {
                "id": str(r.id),
                "business_name": r.business_name,
                "buyer_ntn": r.buyer_ntn,
                "address": r.address,
                "contact_email": r.contact_email,
                **stats,
            }
        )
    return success(payload)


@router.get("/{customer_id}", response_model=ApiResponse[dict])
def get_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    customer = db.get(Customer, customer_id)
    if not customer or customer.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    today = today_karachi()
    invoices = list(
        db.scalars(
            select(Invoice)
            .where(
                Invoice.tenant_id == user.tenant_id,
                Invoice.customer_id == customer_id,
                Invoice.lifecycle_status == InvoiceLifecycle.active,
            )
            .order_by(Invoice.due_date.desc().nullslast())
        ).all()
    )
    stats = _customer_invoice_stats(db, user.tenant_id, customer_id)
    invoice_rows = []
    for inv in invoices:
        due = inv.due_date
        overdue_days = days_overdue(due, today) if due else 0
        if due and overdue_days > 0:
            status_label = "Overdue"
        elif due:
            status_label = "Not yet due"
        else:
            status_label = "Due date not set"
        invoice_rows.append(
            {
                "id": str(inv.id),
                "invoice_reference": inv.invoice_reference,
                "issue_date": inv.issue_date.isoformat(),
                "due_date": due.isoformat() if due else None,
                "total_amount": str(inv.total_amount),
                "outstanding_amount": str(inv.outstanding_amount),
                "days_overdue": overdue_days if due else None,
                "status": status_label,
            }
        )

    return success(
        {
            "id": str(customer.id),
            "business_name": customer.business_name,
            "buyer_ntn": customer.buyer_ntn,
            "address": customer.address,
            "contact_email": customer.contact_email,
            "summary": stats,
            "invoices": invoice_rows,
        }
    )