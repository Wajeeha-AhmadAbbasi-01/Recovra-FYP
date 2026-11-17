from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.core.responses import ApiResponse, success
from app.db.session import get_db
from app.modules.invoices.aging import aging_bucket, days_overdue, today_karachi
from app.modules.customers.models import Customer
from app.modules.invoices.models import Invoice
from app.modules.users.models import User

router = APIRouter(prefix="/api/v1/invoices", tags=["invoices"])


@router.get("", response_model=ApiResponse[list])
def list_invoices(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    q: str | None = None,
) -> ApiResponse[list]:
    stmt = select(Invoice).where(Invoice.tenant_id == user.tenant_id).order_by(Invoice.imported_at.desc())
    rows = db.scalars(stmt).all()
    today = today_karachi()
    payload = []
    for inv in rows:
        if q and q.lower() not in inv.invoice_reference.lower():
            continue
        due = inv.due_date
        payload.append(
            {
                "id": str(inv.id),
                "invoice_reference": inv.invoice_reference,
                "customer_id": str(inv.customer_id),
                "issue_date": inv.issue_date.isoformat(),
                "due_date": due.isoformat() if due else None,
                "currency": inv.currency,
                "total_amount": str(inv.total_amount),
                "outstanding_amount": str(inv.outstanding_amount),
                "days_overdue": days_overdue(due, today) if due else None,
                "aging_bucket": aging_bucket(due, today) if due else None,
                "local_check_note": "Local format check only; not FBR verified",
            }
        )
    return success(payload)


@router.get("/{invoice_id}", response_model=ApiResponse[dict])
def get_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    inv = db.get(Invoice, invoice_id)
    if not inv or inv.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    customer = db.get(Customer, inv.customer_id) if inv.customer_id else None
    today = today_karachi()
    due = inv.due_date
    return success(
        {
            "id": str(inv.id),
            "invoice_reference": inv.invoice_reference,
            "claimed_fbr_identifier": inv.claimed_fbr_identifier,
            "customer": {"id": str(customer.id), "business_name": customer.business_name} if customer else None,
            "upload_id": str(inv.upload_id),
            "issue_date": inv.issue_date.isoformat(),
            "due_date": due.isoformat() if due else None,
            "currency": inv.currency,
            "total_amount": str(inv.total_amount),
            "outstanding_amount": str(inv.outstanding_amount),
            "days_overdue": days_overdue(due, today) if due else None,
            "aging_bucket": aging_bucket(due, today) if due else None,
            "local_check_note": "Local format check only; not FBR verified",
        }
    )


@router.get("/{invoice_id}/document")
def invoice_document_redirect(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    inv = db.get(Invoice, invoice_id)
    if not inv or inv.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url=f"/api/v1/imports/{inv.upload_id}/document", status_code=status.HTTP_307_TEMPORARY_REDIRECT)