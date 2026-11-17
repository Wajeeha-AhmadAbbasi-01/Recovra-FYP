from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.core.responses import ApiResponse, success
from app.db.session import get_db
from app.modules.customers.models import Customer
from app.modules.users.models import User

router = APIRouter(prefix="/api/v1/customers", tags=["customers"])


@router.get("", response_model=ApiResponse[list])
def list_customers(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[list]:
    rows = db.scalars(select(Customer).where(Customer.tenant_id == user.tenant_id).order_by(Customer.business_name)).all()
    return success(
        [
            {
                "id": str(r.id),
                "business_name": r.business_name,
                "buyer_ntn": r.buyer_ntn,
                "address": r.address,
                "contact_email": r.contact_email,
            }
            for r in rows
        ]
    )


@router.get("/{customer_id}", response_model=ApiResponse[dict])
def get_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    customer = db.get(Customer, customer_id)
    if not customer or customer.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return success(
        {
            "id": str(customer.id),
            "business_name": customer.business_name,
            "buyer_ntn": customer.buyer_ntn,
            "address": customer.address,
            "contact_email": customer.contact_email,
        }
    )