from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

DISCLAIMER = (
    "Illustrative structure based on documented fields; not an official FBR-issued invoice, "
    "not an FBR template, and not proof of compliance."
)


def build_illustrative_sample_pdf() -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 800, "Recovra — Illustrative invoice layout (non-official)")
    c.setFont("Helvetica", 10)
    c.drawString(50, 780, DISCLAIMER)
    c.drawString(50, 740, "INVOICE_REF: EXAMPLE-001")
    c.drawString(50, 720, "SELLER_NAME: Example Supplier (Pvt) Ltd")
    c.drawString(50, 700, "SELLER_NTN: 1234567-8")
    c.drawString(50, 680, "BUYER_NAME: Example Buyer Co")
    c.drawString(50, 660, "BUYER_NTN: 7654321-0")
    c.drawString(50, 640, "ISSUE_DATE: 2026-01-15")
    c.drawString(50, 620, "DUE_DATE: 2026-02-15")
    c.drawString(50, 600, "CURRENCY: PKR")
    c.drawString(50, 580, "TOTAL_AMOUNT: 118000.00")
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()