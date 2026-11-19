from datetime import datetime
from decimal import Decimal

from app.modules.fbr_validation.financial import reconcile_line_items
from app.modules.fbr_validation.schemas import ExtractedInvoice, ValidationIssue, ValidationResult
from app.modules.imports.models import ValidationStatus

PROFILE_VERSION = "registered_b2b_goods_v2"

REQUIRED_FIELDS = [
    ("invoice_reference", "FBR-INV-REF", "INV-REF-REQUIRED", "Invoice reference is required."),
    ("seller_name", "FBR-SELLER-NAME", "SELLER_NAME_REQUIRED", "Supplier name is required."),
    ("seller_ntn", "FBR-SELLER-ID", "SELLER_NTN_REQUIRED", "Supplier NTN is required (not interchangeable with STRN)."),
    ("buyer_name", "FBR-BUYER", "BUYER_NAME_REQUIRED", "Buyer name is required."),
    ("issue_date", "FBR-DATE", "ISSUE_DATE_REQUIRED", "Invoice date is required."),
    ("total_amount", "FBR-TOTAL", "TOTAL_REQUIRED", "Invoice total is required."),
]


def validate_extracted_v2(extracted: ExtractedInvoice) -> ValidationResult:
    issues: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []

    if extracted.text_confidence == "low" or extracted.raw_text_length < 40:
        return ValidationResult(
            status=ValidationStatus.NEEDS_MANUAL_REVIEW.value,
            issues=[
                ValidationIssue(
                    field="document",
                    code="LOW_TEXT_CONFIDENCE",
                    message="Could not reliably extract text from PDF (scanned/image-only PDFs are not supported).",
                    source="EXTRACTION",
                    rule_id="RECOVRA-EXTRACT-TEXT",
                )
            ],
        )

    for attr, rule_id, code, message in REQUIRED_FIELDS:
        if not getattr(extracted, attr, None):
            issues.append(
                ValidationIssue(
                    field=attr,
                    code=code,
                    message=message,
                    source="FBR_DERIVED",
                    rule_id=rule_id,
                )
            )

    if not extracted.due_date:
        issues.append(
            ValidationIssue(
                field="due_date",
                code="DUE_DATE_REQUIRED",
                message="Due date is required for Recovra aging.",
                source="RECOVRA_BUSINESS",
                rule_id="RECOVRA-DUE",
            )
        )

    issue_date = _parse_date(extracted.issue_date, "issue_date", issues)
    due_date = _parse_date(extracted.due_date, "due_date", issues)

    total = extracted.total_amount or extracted.grand_total
    if total is not None and total <= Decimal("0"):
        issues.append(
            ValidationIssue(
                field="total_amount",
                code="TOTAL_INVALID",
                message="Total amount must be positive.",
                source="FBR_DERIVED",
                rule_id="FBR-TOTAL",
            )
        )

    # V2: when structured extraction is used, require at least one line item.
    if extracted.extraction_method == "structured_v2" and not extracted.line_items:
        issues.append(
            ValidationIssue(
                field="line_items",
                code="LINE_ITEMS_MISSING",
                message="Itemized invoice lines could not be extracted.",
                source="EXTRACTION",
                rule_id="RECOVRA-LINE-ITEMS",
            )
        )

    if extracted.line_items:
        issues.extend(reconcile_line_items(extracted))

    if extracted.seller_strn and not extracted.seller_ntn:
        warnings.append(
            ValidationIssue(
                field="seller_ntn",
                code="STRN_WITHOUT_NTN",
                message="STRN present but seller NTN missing — verify registration identifiers.",
                source="FBR_DERIVED",
                rule_id="FBR-SELLER-ID",
                severity="WARNING",
            )
        )

    if issues:
        return ValidationResult(
            status=ValidationStatus.REJECTED_LOCAL_CHECK.value,
            issues=issues,
            warnings=warnings,
            normalized=_normalized(extracted, issue_date, due_date),
        )

    warnings.append(
        ValidationIssue(
            field="compliance",
            code="LOCAL_CHECK_ONLY",
            message="Passed local validation only; this is not official FBR verification.",
            source="RECOVRA_BUSINESS",
            rule_id="RECOVRA-DISCLAIMER",
            severity="WARNING",
        )
    )

    return ValidationResult(
        status=ValidationStatus.ACCEPTED_LOCAL_CHECK.value,
        issues=[],
        warnings=warnings,
        normalized=_normalized(extracted, issue_date, due_date),
    )


def _parse_date(raw: str | None, field: str, issues: list[ValidationIssue]):
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        issues.append(
            ValidationIssue(
                field=field,
                code=f"{field.upper()}_INVALID",
                message="Date must be YYYY-MM-DD.",
                source="FBR_DERIVED" if field == "issue_date" else "RECOVRA_BUSINESS",
                rule_id="FBR-DATE" if field == "issue_date" else "RECOVRA-DUE",
            )
        )
        return None


def _normalized(extracted: ExtractedInvoice, issue_date, due_date) -> dict:
    total = extracted.total_amount or extracted.grand_total
    return {
        "invoice_reference": extracted.invoice_reference,
        "fbr_invoice_number": extracted.fbr_invoice_number,
        "seller_name": extracted.seller_name,
        "seller_ntn": extracted.seller_ntn,
        "seller_strn": extracted.seller_strn,
        "buyer_name": extracted.buyer_name,
        "buyer_ntn": extracted.buyer_ntn,
        "issue_date": issue_date.isoformat() if issue_date else extracted.issue_date,
        "due_date": due_date.isoformat() if due_date else extracted.due_date,
        "currency": extracted.currency or "PKR",
        "total_amount": str(total) if total is not None else None,
        "profile_version": PROFILE_VERSION,
        "extraction_method": extracted.extraction_method,
        "line_items": [
            {
                "description": li.description,
                "quantity": str(li.quantity),
                "unit_price": str(li.unit_price),
                "line_total": str(li.line_total),
                "hs_code": li.hs_code,
            }
            for li in extracted.line_items
        ],
    }