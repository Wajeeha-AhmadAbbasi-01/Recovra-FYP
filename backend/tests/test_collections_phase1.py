import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select

from app.modules.collections.models import ReminderHold
from app.modules.customers.models import Customer
from app.modules.imports.models import Upload, UploadStatus, ValidationAttempt, ValidationStatus
from app.modules.inbox.models import InboundMessage
from app.modules.inbox.sanitize import sanitize_body
from app.modules.invoices.models import Invoice, InvoiceLifecycle
from app.modules.users.models import User


def _register_and_login(client, email: str, business: str = "Collections Co"):
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "business_name": business,
            "full_name": "Owner",
            "email": email,
            "password": "securepass123",
        },
    )
    assert reg.status_code == 201
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "securepass123"})
    assert login.status_code == 200
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    return me.json()["data"]


def _seed_invoice(db, tenant_id, user_id, reference: str, due: date, outstanding: str = "1000.00") -> Invoice:
    customer = Customer(tenant_id=tenant_id, business_name=f"Buyer {reference}")
    db.add(customer)
    db.flush()
    upload = Upload(
        tenant_id=tenant_id,
        uploader_user_id=user_id,
        original_filename=f"{reference}.pdf",
        storage_key=f"test/{uuid.uuid4()}",
        sha256=uuid.uuid4().hex + uuid.uuid4().hex,
        mime_type="application/pdf",
        size_bytes=100,
        status=UploadStatus.completed,
    )
    db.add(upload)
    db.flush()
    attempt = ValidationAttempt(
        tenant_id=tenant_id,
        upload_id=upload.id,
        local_status=ValidationStatus.ACCEPTED_LOCAL_CHECK,
    )
    db.add(attempt)
    db.flush()
    invoice = Invoice(
        tenant_id=tenant_id,
        customer_id=customer.id,
        upload_id=upload.id,
        validation_attempt_id=attempt.id,
        invoice_reference=reference,
        seller_identity="Seller",
        issue_date=due - timedelta(days=10),
        due_date=due,
        currency="PKR",
        total_amount=Decimal(outstanding),
        outstanding_amount=Decimal(outstanding),
        lifecycle_status=InvoiceLifecycle.active,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def test_sanitize_strips_markup():
    text = sanitize_body("<script>alert(1)</script><p>Pay Friday</p>")
    assert "script" not in text.lower()
    assert "Pay Friday" in text


def test_task_assignment_transition_and_balance(client, db, unique_email):
    me = _register_and_login(client, unique_email)
    user_id = uuid.UUID(me["user"]["id"])
    tenant_id = uuid.UUID(me["tenant"]["id"])
    invoice = _seed_invoice(db, tenant_id, user_id, f"INV-{uuid.uuid4().hex[:6]}", date.today() - timedelta(days=3))
    before = invoice.outstanding_amount

    created = client.post(
        "/api/v1/collections/tasks",
        json={"invoice_id": str(invoice.id), "task_type": "FOLLOW_UP", "reason": "Call the buyer"},
    )
    assert created.status_code == 201
    body = created.json()["data"]
    assert body["status"] == "OPEN"
    assert body["source"] == "STAFF"
    assert body["outstanding_amount"] == "1000.00"
    task_id = body["id"]

    other = f"other-{uuid.uuid4().hex[:8]}@recovra.test"
    client.cookies.clear()
    other_me = _register_and_login(client, other, "Other Co")
    client.cookies.clear()
    client.post("/api/v1/auth/login", json={"email": unique_email, "password": "securepass123"})

    denied = client.patch(
        f"/api/v1/collections/tasks/{task_id}",
        json={"assignee_id": other_me["user"]["id"]},
    )
    assert denied.status_code == 404

    assigned = client.patch(
        f"/api/v1/collections/tasks/{task_id}",
        json={"assignee_id": me["user"]["id"], "status": "COMPLETED"},
    )
    assert assigned.status_code == 200
    assert assigned.json()["data"]["status"] == "COMPLETED"

    illegal = client.patch(f"/api/v1/collections/tasks/{task_id}", json={"status": "OPEN"})
    assert illegal.status_code == 409

    db.refresh(invoice)
    assert invoice.outstanding_amount == before
    assert invoice.lifecycle_status == InvoiceLifecycle.active

    missing = client.get(f"/api/v1/collections/tasks/{uuid.uuid4()}")
    assert missing.status_code == 404
    anon = client
    anon.cookies.clear()
    assert anon.get("/api/v1/collections/tasks").status_code == 401


def test_promise_and_dispute_do_not_change_balance_or_holds(client, db, unique_email):
    me = _register_and_login(client, unique_email)
    user_id = uuid.UUID(me["user"]["id"])
    tenant_id = uuid.UUID(me["tenant"]["id"])
    invoice = _seed_invoice(db, tenant_id, user_id, f"INV-{uuid.uuid4().hex[:6]}", date.today() - timedelta(days=1))

    promise = client.post(
        f"/api/v1/collections/invoices/{invoice.id}/promises",
        json={"promised_date": "2026-12-01", "amount": "250.00", "note": "Staff selected date"},
    )
    assert promise.status_code == 201
    assert promise.json()["data"]["status"] == "RECORDED"
    assert promise.json()["data"]["scheduling_effect"] == "routine_may_apply"
    promise_id = promise.json()["data"]["id"]

    confirmed = client.patch(f"/api/v1/collections/promises/{promise_id}", json={"status": "CONFIRMED"})
    assert confirmed.status_code == 200
    assert confirmed.json()["data"]["status"] == "CONFIRMED"

    too_far = client.post(
        f"/api/v1/collections/invoices/{invoice.id}/promises",
        json={"promised_date": "2026-12-02", "amount": "99999.00"},
    )
    assert too_far.status_code == 422

    dispute = client.post(
        f"/api/v1/collections/invoices/{invoice.id}/disputes",
        json={"reason": "Buyer challenged a line", "challenged_amount": "100.00"},
    )
    assert dispute.status_code == 201
    dispute_id = dispute.json()["data"]["id"]
    assert client.patch(f"/api/v1/collections/disputes/{dispute_id}", json={"status": "CONFIRMED"}).status_code == 200

    active_holds = db.scalar(
        select(func.count()).select_from(ReminderHold).where(
            ReminderHold.invoice_id == invoice.id,
            ReminderHold.active.is_(True),
        )
    )
    assert active_holds == 2
    db.refresh(invoice)
    assert invoice.outstanding_amount == Decimal("1000.00")

    timeline = client.get(f"/api/v1/collections/invoices/{invoice.id}/timeline")
    assert timeline.status_code == 200
    actions = {item["action"] for item in timeline.json()["data"]["items"]}
    assert "promise_recorded" in actions
    assert "dispute_recorded" in actions

    preview = client.get("/api/v1/collections/reminders/preview")
    assert preview.status_code == 200
    assert preview.json()["data"]["sends_customer_email"] is False


def test_mock_inbox_dedupe_suggestion_and_tenant_isolation(client, db, unique_email):
    me = _register_and_login(client, unique_email)
    user_id = uuid.UUID(me["user"]["id"])
    tenant_id = uuid.UUID(me["tenant"]["id"])
    ref_a = f"INV-A-{uuid.uuid4().hex[:4]}"
    ref_b = f"INV-B-{uuid.uuid4().hex[:4]}"
    invoice_a = _seed_invoice(db, tenant_id, user_id, ref_a, date.today() - timedelta(days=2))
    _seed_invoice(db, tenant_id, user_id, ref_b, date.today() + timedelta(days=5))

    payload = {
        "messages": [
            {
                "uidvalidity": 7,
                "uid": 3,
                "sender": "buyer@example.com",
                "recipient": "finance@example.com",
                "subject": "About invoices",
                "body": "<b>Please check</b> <script>nope()</script>",
                "invoice_references": [ref_a, ref_b],
            }
        ]
    }
    first = client.post("/api/v1/inbox/mailbox/mock-deliver", json=payload)
    assert first.status_code == 200
    assert first.json()["data"]["results"][0]["created"] is True
    second = client.post("/api/v1/inbox/mailbox/mock-deliver", json=payload)
    assert second.json()["data"]["results"][0]["created"] is False

    stored = db.scalar(select(func.count()).select_from(InboundMessage).where(InboundMessage.tenant_id == tenant_id))
    assert stored == 1

    listing = client.get("/api/v1/inbox/messages")
    assert listing.status_code == 200
    item = listing.json()["data"]["items"][0]
    assert "script" not in item["body_text"].lower()
    assert "Please check" in item["body_text"]
    assert {link["link_state"] for link in item["links"]} == {"SUGGESTED"}
    assert len(item["links"]) == 2

    confirmed = client.post(
        f"/api/v1/inbox/messages/{item['id']}/links",
        json={"invoice_id": str(invoice_a.id), "action": "confirm"},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["data"]["link_state"] == "CONFIRMED"
    again = client.post(
        f"/api/v1/inbox/messages/{item['id']}/links",
        json={"invoice_id": str(invoice_a.id), "action": "confirm"},
    )
    assert again.status_code == 200

    db.refresh(invoice_a)
    assert invoice_a.outstanding_amount == Decimal("1000.00")

    status_body = client.get("/api/v1/inbox/mailbox/status").json()["data"]
    assert status_body["live_imap"] == "NOT_IMPLEMENTED"
    assert status_body["sends_mail"] is False
    assert "password" not in status_body

    other = f"inbox-{uuid.uuid4().hex[:8]}@recovra.test"
    client.cookies.clear()
    _register_and_login(client, other, "Inbox Other")
    hidden = client.get(f"/api/v1/inbox/messages/{item['id']}")
    assert hidden.status_code == 404
    assert client.get("/api/v1/inbox/messages").json()["data"]["total"] == 0


def test_cross_tenant_invoice_task_hidden(client, db, unique_email):
    me = _register_and_login(client, unique_email)
    invoice = _seed_invoice(
        db,
        uuid.UUID(me["tenant"]["id"]),
        uuid.UUID(me["user"]["id"]),
        f"INV-{uuid.uuid4().hex[:6]}",
        date.today(),
    )
    other = f"hide-{uuid.uuid4().hex[:8]}@recovra.test"
    client.cookies.clear()
    _register_and_login(client, other, "Hidden Co")
    denied = client.post(
        "/api/v1/collections/tasks",
        json={"invoice_id": str(invoice.id), "task_type": "DOCUMENT_REQUEST", "reason": "Need the bill"},
    )
    assert denied.status_code == 404
    user = db.get(User, uuid.UUID(me["user"]["id"]))
    assert user is not None
