from pathlib import Path

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


def test_valid_pdf_creates_invoice(client, unique_email):
    client.post(
        "/api/v1/auth/register",
        json={
            "business_name": "PDF Co",
            "full_name": "Owner",
            "email": unique_email,
            "password": "securepass123",
        },
    )
    client.post("/api/v1/auth/login", json={"email": unique_email, "password": "securepass123"})

    pdf = FIXTURES / "valid_local_invoice.pdf"
    if not pdf.exists():
        return

    with pdf.open("rb") as fh:
        res = client.post(
            "/api/v1/imports/pdf-batch",
            files=[("files", (pdf.name, fh, "application/pdf"))],
        )
    assert res.status_code == 200
    results = res.json()["data"]["results"]
    assert results[0]["local_status"] == "ACCEPTED_LOCAL_CHECK"

    inv = client.get("/api/v1/invoices")
    assert inv.status_code == 200
    assert len(inv.json()["data"]) >= 1