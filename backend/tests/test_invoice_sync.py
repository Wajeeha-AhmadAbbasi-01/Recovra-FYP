"""Invoice import ↔ dashboard / listing synchronization."""

from decimal import Decimal

from app.modules.fbr_validation.sample_pdf import build_illustrative_sample_pdf


def _register_login(client, unique_email: str) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "business_name": "Sync Co",
            "full_name": "Owner",
            "email": unique_email,
            "password": "securepass123",
        },
    )
    client.post("/api/v1/auth/login", json={"email": unique_email, "password": "securepass123"})


def test_accept_creates_one_invoice_and_dashboard_counts(client, unique_email):
    _register_login(client, unique_email)
    pdf = build_illustrative_sample_pdf()
    res = client.post(
        "/api/v1/imports/pdf-batch",
        files=[("files", ("a.pdf", pdf, "application/pdf"))],
    )
    assert res.status_code == 200
    row = res.json()["data"]["results"][0]
    assert row["local_status"] == "ACCEPTED_LOCAL_CHECK"
    assert row["invoice_id"]

    dash = client.get("/api/v1/dashboard/summary").json()["data"]
    assert dash["invoice_count"] == 1
    assert Decimal(dash["total_outstanding"]) > 0

    inv_list = client.get("/api/v1/invoices").json()["data"]
    assert len(inv_list) == 1

    customers = client.get("/api/v1/customers").json()["data"]
    assert len(customers) == 1
    assert customers[0]["invoice_count"] == 1


def test_reupload_same_pdf_after_accept_is_duplicate_with_invoice_id(client, unique_email):
    _register_login(client, unique_email)
    pdf = build_illustrative_sample_pdf()
    first = client.post(
        "/api/v1/imports/pdf-batch",
        files=[("files", ("inv.pdf", pdf, "application/pdf"))],
    ).json()["data"]["results"][0]
    invoice_id = first["invoice_id"]
    assert first["local_status"] == "ACCEPTED_LOCAL_CHECK"

    second = client.post(
        "/api/v1/imports/pdf-batch",
        files=[("files", ("inv-again.pdf", pdf, "application/pdf"))],
    ).json()["data"]["results"][0]
    assert second["local_status"] == "DUPLICATE"
    assert second["duplicate_kind"] == "file"
    assert second["invoice_id"] == invoice_id

    dash = client.get("/api/v1/dashboard/summary").json()["data"]
    assert dash["invoice_count"] == 1


def test_reupload_same_bytes_after_reject_allows_retry(client, unique_email):
    _register_login(client, unique_email)
    # Minimal PDF without required labels — should fail validation or need review
    junk = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 200 200]/Parent 2 0 R/Contents 4 0 R>>endobj\n4 0 obj<</Length 20>>stream\nBT /F1 12 Tf ET\nendstream\nendobj\nxref\n0 5\ntrailer<</Size 5/Root 1 0 R>>\nstartxref\n0\n%%EOF"
    r1 = client.post(
        "/api/v1/imports/pdf-batch",
        files=[("files", ("bad.pdf", junk, "application/pdf"))],
    ).json()["data"]["results"][0]
    assert r1["local_status"] in ("REJECTED_LOCAL_CHECK", "NEEDS_MANUAL_REVIEW", "REJECTED_UNSUPPORTED")

    r2 = client.post(
        "/api/v1/imports/pdf-batch",
        files=[("files", ("bad2.pdf", junk, "application/pdf"))],
    ).json()["data"]["results"][0]
    assert r2["local_status"] != "DUPLICATE" or r2.get("duplicate_kind") != "file"

    dash = client.get("/api/v1/dashboard/summary").json()["data"]
    assert dash["invoice_count"] == 0


def test_rejected_does_not_affect_dashboard(client, unique_email):
    _register_login(client, unique_email)
    junk = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 200 200]/Parent 2 0 R/Contents 4 0 R>>endobj\n4 0 obj<</Length 44>>stream\nBT (hello world test content layer) Tj ET\nendstream\nendobj\nxref\n0 5\ntrailer<</Size 5/Root 1 0 R>>\nstartxref\n0\n%%EOF"
    client.post(
        "/api/v1/imports/pdf-batch",
        files=[("files", ("noreq.pdf", junk, "application/pdf"))],
    )
    dash = client.get("/api/v1/dashboard/summary").json()["data"]
    assert dash["invoice_count"] == 0
    assert Decimal(dash["total_outstanding"]) == 0