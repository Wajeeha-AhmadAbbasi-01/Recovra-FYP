from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

DISCLAIMER_TITLE = "SAMPLE — FOR FORMAT GUIDANCE ONLY — NOT AN OFFICIAL FBR INVOICE"
DISCLAIMER_BODY = (
    "Illustrative sales-tax invoice layout using fictitious parties. "
    "Not FBR-issued. Local format checks only — not official FBR verification."
)


def build_illustrative_sample_pdf() -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    y = h - 25 * mm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(20 * mm, y, "SALES TAX INVOICE")
    y -= 6 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(20 * mm, y, DISCLAIMER_TITLE)
    y -= 5 * mm
    c.setFont("Helvetica", 8)
    c.drawString(20 * mm, y, DISCLAIMER_BODY)
    y -= 10 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "Seller")
    y -= 5 * mm
    c.setFont("Helvetica", 9)
    for line in (
        "Seller: Fictitious Supplier (Pvt) Ltd",
        "Seller NTN: 1234567-8",
        "Seller STRN: 12-34-5678-901-23",
        "123 Sample Industrial Estate, Karachi",
    ):
        c.drawString(20 * mm, y, line)
        y -= 4.5 * mm

    y -= 4 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "Buyer")
    y -= 5 * mm
    c.setFont("Helvetica", 9)
    for line in (
        "Buyer: Fictitious Buyer Company",
        "Buyer NTN: 7654321-0",
        "45 Commerce Road, Lahore",
    ):
        c.drawString(20 * mm, y, line)
        y -= 4.5 * mm

    y -= 6 * mm
    c.setFont("Helvetica", 9)
    for line in (
        "Invoice No: RECOVRA-SAMPLE-2026-001",
        "Issue Date: 2026-01-15",
        "Due Date: 2026-02-15",
        "Currency: PKR",
    ):
        c.drawString(20 * mm, y, line)
        y -= 4.5 * mm

    y -= 6 * mm
    c.setFont("Helvetica-Bold", 9)
    headers = ("Description", "Qty", "Unit Price", "Line Total")
    xs = [20 * mm, 95 * mm, 115 * mm, 145 * mm]
    for x, label in zip(xs, headers, strict=True):
        c.drawString(x, y, label)
    y -= 4 * mm
    c.setFont("Helvetica", 9)
    rows = [
        ("Industrial Widget A", "2", "11800.00", "23600.00"),
        ("Service Charge B", "1", "94400.00", "94400.00"),
    ]
    for desc, qty, unit, total in rows:
        c.drawString(xs[0], y, desc)
        c.drawRightString(xs[1] + 12 * mm, y, qty)
        c.drawRightString(xs[2] + 18 * mm, y, unit)
        c.drawRightString(xs[3] + 18 * mm, y, total)
        y -= 5 * mm

    y -= 4 * mm
    c.drawString(20 * mm, y, "Subtotal (excl. tax): 100000.00")
    y -= 4.5 * mm
    c.drawString(20 * mm, y, "Total Sales Tax: 20360.00")
    y -= 4.5 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "Grand Total: 118000.00")
    y -= 8 * mm
    c.setFont("Helvetica", 8)
    c.drawString(20 * mm, y, "QR PLACEHOLDER — ILLUSTRATIVE ONLY — NOT VERIFIABLE")

    machine_lines = [
        "INVOICE_REF: RECOVRA-SAMPLE-2026-001",
        "SELLER_NAME: Fictitious Supplier (Pvt) Ltd",
        "SELLER_NTN: 1234567-8",
        "BUYER_NAME: Fictitious Buyer Company",
        "BUYER_NTN: 7654321-0",
        "ISSUE_DATE: 2026-01-15",
        "DUE_DATE: 2026-02-15",
        "CURRENCY: PKR",
        "TOTAL_AMOUNT: 118000.00",
        "LINE_ITEM: Industrial Widget A|2|11800.00|23600.00|8471.30",
        "LINE_ITEM: Service Charge B|1|94400.00|94400.00|",
    ]
    y = 70 * mm
    c.setFont("Helvetica", 7)
    c.drawString(20 * mm, y, "Machine-readable extract block (for Recovra local checks):")
    y -= 4 * mm
    for line in machine_lines:
        c.drawString(20 * mm, y, line)
        y -= 3.5 * mm

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()