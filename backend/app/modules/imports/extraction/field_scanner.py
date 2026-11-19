import re
from decimal import Decimal, InvalidOperation

from app.modules.fbr_validation.schemas import ExtractedInvoice, FieldEvidence

# Order matters for invoice reference — more specific patterns first.
FIELD_PATTERNS: list[tuple[str, str, re.Pattern[str]]] = [
    ("invoice_reference", "invoice_number", re.compile(r"(?im)^(?:invoice\s*(?:number|no\.?|#|ref(?:erence)?))\s*[:.\-]\s*(.+)$")),
    ("seller_name", "seller_block", re.compile(r"(?im)^seller(?:\s*\/\s*supplier)?\s*[:.\-]\s*(.+)$")),
    ("seller_ntn", "seller_ntn", re.compile(r"(?im)^(?:seller\s*)?ntn\s*[:.\-]\s*([\d\-]+)$")),
    ("seller_strn", "seller_strn", re.compile(r"(?im)^(?:seller\s*)?strn\s*[:.\-]\s*([\d\-]+)$")),
    ("buyer_name", "buyer_block", re.compile(r"(?im)^buyer\s*[:.\-]\s*(.+)$")),
    ("buyer_ntn", "buyer_ntn", re.compile(r"(?im)^buyer\s*ntn\s*[:.\-]\s*([\d\-]+)$")),
    ("issue_date", "issue_date", re.compile(r"(?im)^(?:issue\s*date|invoice\s*date|date\s*of\s*issue)\s*[:.\-]\s*(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})$")),
    ("due_date", "due_date", re.compile(r"(?im)^(?:due\s*date|payment\s*due)\s*[:.\-]\s*(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})$")),
    ("grand_total", "grand_total", re.compile(r"(?im)^(?:grand\s*total|total\s*payable|amount\s*due)\s*[:.\-]?\s*(?:pkr\s*)?([\d,]+\.\d{2})$")),
    ("fbr_invoice_number", "fbr_id", re.compile(r"(?im)^(?:fbr\s*invoice\s*(?:no\.?|number|#))\s*[:.\-]\s*(.+)$")),
]


def _normalize_date(raw: str) -> str:
    raw = raw.strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", raw):
        return raw
    m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", raw)
    if m:
        d, mo, y = m.groups()
        return f"{y}-{mo}-{d}"
    return raw


def scan_fields(invoice: ExtractedInvoice, text: str) -> list[FieldEvidence]:
    found: list[FieldEvidence] = []
    for attr, method, pattern in FIELD_PATTERNS:
        if getattr(invoice, attr, None):
            continue
        match = pattern.search(text)
        if not match:
            continue
        raw = match.group(1).strip()
        if attr in ("issue_date", "due_date"):
            value = _normalize_date(raw)
        elif attr == "grand_total":
            try:
                value = str(Decimal(raw.replace(",", "")))
                invoice.grand_total = Decimal(raw.replace(",", ""))
                if invoice.total_amount is None:
                    invoice.total_amount = invoice.grand_total
            except InvalidOperation:
                continue
        else:
            value = raw
        setattr(invoice, attr, value)
        found.append(
            FieldEvidence(
                field=attr,
                value=value,
                method=method,
                status="EXTRACTED",
                snippet=match.group(0)[:120],
            )
        )
    return found