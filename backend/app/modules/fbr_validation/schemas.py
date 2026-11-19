from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass
class FieldEvidence:
    field: str
    value: str
    method: str
    status: str  # EXTRACTED | AMBIGUOUS | MISSING | UNSUPPORTED
    snippet: str | None = None


@dataclass
class LineItemExtracted:
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    hs_code: str | None = None
    value_excluding_tax: Decimal | None = None
    sales_tax_rate: str | None = None
    sales_tax_amount: Decimal | None = None
    extraction_status: str = "EXTRACTED"


@dataclass
class ExtractedInvoice:
    invoice_reference: str | None = None
    fbr_invoice_number: str | None = None
    seller_name: str | None = None
    seller_address: str | None = None
    seller_ntn: str | None = None
    seller_strn: str | None = None
    buyer_name: str | None = None
    buyer_address: str | None = None
    buyer_ntn: str | None = None
    buyer_strn: str | None = None
    issue_date: str | None = None
    due_date: str | None = None
    currency: str = "PKR"
    total_amount: Decimal | None = None
    grand_total: Decimal | None = None
    subtotal: Decimal | None = None
    total_sales_tax: Decimal | None = None
    line_items: list[LineItemExtracted] = field(default_factory=list)
    text_confidence: str = "high"
    raw_text_length: int = 0
    extraction_method: str = "none"


@dataclass
class ValidationIssue:
    field: str
    code: str
    message: str
    source: str  # FBR_DERIVED | RECOVRA_BUSINESS | EXTRACTION
    rule_id: str | None = None
    severity: str = "ERROR"

    def __dict__(self):  # noqa: D105 — legacy API serialization
        return {
            "field": self.field,
            "code": self.code,
            "message": self.message,
            "source": self.source,
            "rule_id": self.rule_id,
            "severity": self.severity,
        }


@dataclass
class ValidationResult:
    status: str
    issues: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)
    normalized: dict[str, Any] = field(default_factory=dict)