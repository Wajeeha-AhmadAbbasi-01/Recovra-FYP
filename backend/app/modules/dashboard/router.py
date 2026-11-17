from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.core.responses import ApiResponse, success
from app.db.session import get_db
from app.modules.invoices.aging import bucket_outstanding, today_karachi
from app.modules.invoices.models import Invoice, InvoiceLifecycle
from app.modules.users.models import User

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=ApiResponse[dict])
def summary(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    rows = db.scalars(
        select(Invoice).where(
            Invoice.tenant_id == user.tenant_id,
            Invoice.lifecycle_status == InvoiceLifecycle.active,
        )
    ).all()
    outstanding = sum((r.outstanding_amount for r in rows), Decimal("0"))
    return success(
        {
            "as_of_date": today_karachi().isoformat(),
            "invoice_count": len(rows),
            "total_outstanding": str(outstanding),
            "currency": "PKR",
            "disclaimer": "Totals from locally accepted invoices only; not FBR verified.",
        }
    )


@router.get("/aging", response_model=ApiResponse[dict])
def aging(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    rows = db.scalars(
        select(Invoice).where(
            Invoice.tenant_id == user.tenant_id,
            Invoice.lifecycle_status == InvoiceLifecycle.active,
        )
    ).all()
    pairs = [(r.due_date, r.outstanding_amount) for r in rows if r.due_date is not None]
    buckets = bucket_outstanding(pairs)
    return success(
        {
            "as_of_date": today_karachi().isoformat(),
            "buckets": {k: str(v) for k, v in buckets.items()},
            "disclaimer": "Aging uses Asia/Karachi business calendar.",
        }
    )