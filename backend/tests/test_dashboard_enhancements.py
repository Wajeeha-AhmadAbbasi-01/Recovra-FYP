import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.modules.customers.models import Customer
from app.modules.imports.models import Upload, UploadStatus, ValidationAttempt, ValidationStatus
from app.modules.invoices.aging import today_karachi
from app.modules.invoices.models import Invoice, InvoiceItem, InvoiceLifecycle


def _seed_invoice(
    db: Session, tenant_id, customer_id, upload_id, validation_attempt_id, ref: str, due: date, amount: str
):
    inv = Invoice(
        tenant_id=tenant_id,
        customer_id=customer_id,
        upload_id=upload_id,
        validation_attempt_id=validation_attempt_id,
        invoice_reference=ref,
        seller_identity="seller|123",
        issue_date=due - timedelta(days=30),
        due_date=due,
        total_amount=Decimal(amount),
        outstanding_amount=Decimal(amount),
        lifecycle_status=InvoiceLifecycle.active,
    )
    db.add(inv)
    db.flush()
    db.add(
        InvoiceItem(
            invoice=inv,
            description="line",
            quantity=Decimal("1"),
            unit_price=Decimal(amount),
            line_total=Decimal(amount),
        )
    )
    return inv


def test_dashboard_summary_and_overdue(client, db: Session, unique_email):
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "business_name": "Dash Co",
            "full_name": "Owner",
            "email": unique_email,
            "password": "securepass123",
        },
    )
    assert reg.status_code == 201
    login = client.post("/api/v1/auth/login", json={"email": unique_email, "password": "securepass123"})
    assert login.status_code == 200

    me = client.get("/api/v1/auth/me").json()["data"]
    tenant_id = uuid.UUID(me["tenant"]["id"])
    user_id = uuid.UUID(me["user"]["id"])

    customer = Customer(tenant_id=tenant_id, business_name="Buyer A")
    db.add(customer)
    db.flush()

    def _placeholder_ids() -> tuple[uuid.UUID, uuid.UUID]:
        upload_id = uuid.uuid4()
        upload = Upload(
            id=upload_id,
            tenant_id=tenant_id,
            uploader_user_id=user_id,
            original_filename="t.pdf",
            storage_key=f"key-{upload_id.hex}",
            sha256=f"{upload_id.hex}",
            mime_type="application/pdf",
            size_bytes=1,
            status=UploadStatus.completed,
        )
        db.add(upload)
        db.flush()
        attempt = ValidationAttempt(
            tenant_id=tenant_id,
            upload_id=upload_id,
            profile_version="test",
            extracted_candidate={},
            local_status=ValidationStatus.ACCEPTED_LOCAL_CHECK,
            errors=[],
            warnings=[],
            evidence={},
        )
        db.add(attempt)
        db.flush()
        return upload_id, attempt.id

    today = today_karachi()
    up1, att1 = _placeholder_ids()
    up2, att2 = _placeholder_ids()
    _seed_invoice(db, tenant_id, customer.id, up1, att1, "INV-1", today + timedelta(days=5), "1000.00")
    _seed_invoice(db, tenant_id, customer.id, up2, att2, "INV-2", today - timedelta(days=10), "500.00")
    db.commit()

    summary = client.get("/api/v1/dashboard/summary").json()["data"]
    assert summary["invoice_count"] == 2
    assert summary["overdue_invoice_count"] == 1
    assert Decimal(summary["total_outstanding"]) == Decimal("1500.00")
    assert Decimal(summary["overdue_amount"]) == Decimal("500.00")

    aging = client.get("/api/v1/dashboard/aging").json()["data"]
    assert "bucket_counts" in aging
    assert sum(aging["bucket_counts"].values()) == 2

    overdue = client.get("/api/v1/dashboard/overdue-invoices").json()["data"]
    assert len(overdue) == 1
    assert overdue[0]["invoice_reference"] == "INV-2"
    assert overdue[0]["customer_name"] == "Buyer A"