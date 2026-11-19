from decimal import Decimal

from app.modules.fbr_validation.financial import reconcile_line_items
from app.modules.fbr_validation.profiles.v2 import PROFILE_VERSION, validate_extracted_v2
from app.modules.fbr_validation.sample_pdf import build_illustrative_sample_pdf
from app.modules.fbr_validation.schemas import ExtractedInvoice, LineItemExtracted
from app.modules.imports.pdf_extract import extract_invoice_from_pdf


def test_sample_pdf_passes_v2_validation():
    pdf = build_illustrative_sample_pdf()
    extracted, _ = extract_invoice_from_pdf(pdf, max_pages=1)
    result = validate_extracted_v2(extracted)

    assert result.status == "ACCEPTED_LOCAL_CHECK"
    assert result.normalized["profile_version"] == PROFILE_VERSION
    assert len(result.normalized["line_items"]) == 2
    assert extracted.extraction_method in ("legacy_labels", "structured_v2")


def test_sample_pdf_upload_accepted(client, unique_email):
    client.post(
        "/api/v1/auth/register",
        json={
            "business_name": "V2 Co",
            "full_name": "Owner",
            "email": unique_email,
            "password": "securepass123",
        },
    )
    client.post("/api/v1/auth/login", json={"email": unique_email, "password": "securepass123"})

    pdf = build_illustrative_sample_pdf()
    res = client.post(
        "/api/v1/imports/pdf-batch",
        files=[("files", ("sample.pdf", pdf, "application/pdf"))],
    )
    assert res.status_code == 200
    row = res.json()["data"]["results"][0]
    assert row["local_status"] == "ACCEPTED_LOCAL_CHECK"
    assert row["line_item_count"] == 2
    assert row["validation_profile"] == PROFILE_VERSION

    inv = client.get("/api/v1/invoices")
    assert inv.status_code == 200
    data = inv.json()["data"]
    assert len(data) >= 1


def test_financial_reconcile_flags_mismatch():
    invoice = ExtractedInvoice(
        line_items=[
            LineItemExtracted(
                description="X",
                quantity=Decimal("2"),
                unit_price=Decimal("10"),
                line_total=Decimal("30"),
            )
        ],
        grand_total=Decimal("30"),
    )
    issues = reconcile_line_items(invoice)
    assert any(i.code == "LINE_TOTAL_MISMATCH" for i in issues)