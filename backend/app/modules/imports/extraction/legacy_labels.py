import re
from decimal import Decimal, InvalidOperation

from app.modules.fbr_validation.schemas import ExtractedInvoice

LABEL_PATTERN = re.compile(r"^([A-Z_]+):\s*(.+)$", re.MULTILINE)

FIELD_MAP = {
    "INVOICE_REF": "invoice_reference",
    "FBR_INVOICE_NUMBER": "fbr_invoice_number",
    "SELLER_NAME": "seller_name",
    "SELLER_NTN": "seller_ntn",
    "SELLER_STRN": "seller_strn",
    "BUYER_NAME": "buyer_name",
    "BUYER_NTN": "buyer_ntn",
    "ISSUE_DATE": "issue_date",
    "DUE_DATE": "due_date",
    "CURRENCY": "currency",
    "TOTAL_AMOUNT": "total_amount",
    "GRAND_TOTAL": "grand_total",
}


def apply_legacy_labels(invoice: ExtractedInvoice, text: str, evidence: dict) -> int:
    labels: dict[str, str] = {}
    count = 0
    for match in LABEL_PATTERN.finditer(text):
        key = match.group(1).strip()
        value = match.group(2).strip()
        labels[key] = value
        attr = FIELD_MAP.get(key)
        if not attr:
            continue
        if attr in ("total_amount", "grand_total"):
            try:
                amt = Decimal(value.replace(",", ""))
                invoice.total_amount = amt
                invoice.grand_total = amt
            except InvalidOperation:
                pass
        else:
            setattr(invoice, attr, value)
        count += 1
    evidence.setdefault("labels", {}).update(labels)
    return count