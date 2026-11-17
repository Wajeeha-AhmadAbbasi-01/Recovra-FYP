from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass
class ExtractedInvoice:
    invoice_reference: str | None = None
    seller_name: str | None = None
    seller_ntn: str | None = None
    buyer_name: str | None = None
    buyer_ntn: str | None = None
    issue_date: str | None = None
    due_date: str | None = None
    currency: str = "PKR"
    total_amount: Decimal | None = None
    line_items: list[dict[str, Any]] = field(default_factory=list)
    text_confidence: str = "high"
    raw_text_length: int = 0


@dataclass
class ValidationIssue:
    field: str
    code: str
    message: str
    source: str  # FBR_DERIVED | RECOVRA_BUSINESS


@dataclass
class ValidationResult:
    status: str
    issues: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)
    normalized: dict[str, Any] = field(default_factory=dict)