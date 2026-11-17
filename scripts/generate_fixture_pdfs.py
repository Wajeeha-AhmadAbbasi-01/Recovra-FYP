"""Generate Module 1 PDF fixtures (text-based, label format). Run from Recovra-FYP root."""

from pathlib import Path

from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1] / "fixtures"
ROOT.mkdir(parents=True, exist_ok=True)


def write_pdf(path: Path, lines: list[str]) -> None:
    c = canvas.Canvas(str(path))
    y = 800
    for line in lines:
        c.drawString(50, y, line)
        y -= 20
    c.showPage()
    c.save()


def main() -> None:
    valid = [
        "INVOICE_REF: INV-2026-0001",
        "SELLER_NAME: Demo Supplier Pvt Ltd",
        "SELLER_NTN: 1111111-1",
        "BUYER_NAME: Demo Buyer Co",
        "BUYER_NTN: 2222222-2",
        "ISSUE_DATE: 2026-01-10",
        "DUE_DATE: 2026-02-10",
        "CURRENCY: PKR",
        "TOTAL_AMOUNT: 50000.00",
    ]
    write_pdf(ROOT / "valid_local_invoice.pdf", valid)

    missing = valid.copy()
    missing = [ln for ln in missing if not ln.startswith("SELLER_NTN:")]
    write_pdf(ROOT / "missing_required_field.pdf", missing)

    write_pdf(ROOT / "duplicate_invoice.pdf", valid)

    unreadable = ["---"]
    write_pdf(ROOT / "scanned_or_unreadable.pdf", unreadable)

    print(f"Wrote fixtures to {ROOT}")


if __name__ == "__main__":
    main()