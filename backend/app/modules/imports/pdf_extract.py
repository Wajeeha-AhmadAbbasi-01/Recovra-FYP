import re
from decimal import Decimal, InvalidOperation
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.modules.fbr_validation.schemas import ExtractedInvoice


LABEL_PATTERN = re.compile(r"^([A-Z_]+):\s*(.+)$", re.MULTILINE)


def extract_invoice_from_pdf(data: bytes, *, max_pages: int) -> tuple[ExtractedInvoice, dict]:
    evidence: dict = {"pages": [], "labels": {}}
    try:
        reader = PdfReader(BytesIO(data))
    except PdfReadError as exc:
        raise ValueError("corrupted_or_encrypted") from exc

    if reader.is_encrypted:
        raise ValueError("encrypted")

    page_count = len(reader.pages)
    if page_count > max_pages:
        raise ValueError("too_many_pages")
    if page_count > 1:
        raise ValueError("multiple_invoices_unsupported")

    texts: list[str] = []
    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        texts.append(text)
        evidence["pages"].append({"index": idx, "chars": len(text)})

    full_text = "\n".join(texts).strip()
    invoice = ExtractedInvoice(raw_text_length=len(full_text))

    if len(full_text) < 40:
        invoice.text_confidence = "low"
        return invoice, evidence

    for match in LABEL_PATTERN.finditer(full_text):
        key = match.group(1).strip()
        value = match.group(2).strip()
        evidence["labels"][key] = value
        _assign_field(invoice, key, value)

    if not evidence["labels"]:
        invoice.text_confidence = "low"

    return invoice, evidence


def _assign_field(invoice: ExtractedInvoice, key: str, value: str) -> None:
    mapping = {
        "INVOICE_REF": "invoice_reference",
        "SELLER_NAME": "seller_name",
        "SELLER_NTN": "seller_ntn",
        "BUYER_NAME": "buyer_name",
        "BUYER_NTN": "buyer_ntn",
        "ISSUE_DATE": "issue_date",
        "DUE_DATE": "due_date",
        "CURRENCY": "currency",
        "TOTAL_AMOUNT": "total_amount",
    }
    attr = mapping.get(key)
    if not attr:
        return
    if attr == "total_amount":
        try:
            invoice.total_amount = Decimal(value.replace(",", ""))
        except InvalidOperation:
            invoice.total_amount = None
    else:
        setattr(invoice, attr, value)