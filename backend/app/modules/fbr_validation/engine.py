from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.modules.fbr_validation.schemas import ExtractedInvoice, ValidationIssue, ValidationResult
from app.modules.imports.models import ValidationStatus

KARACHI = ZoneInfo("Asia/Karachi")
PROFILE_VERSION = "registered_b2b_goods_v1"


def validate_extracted(extracted: ExtractedInvoice) -> ValidationResult:
    issues: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []

    if extracted.text_confidence == "low" or extracted.raw_text_length < 40:
        return ValidationResult(
            status=ValidationStatus.NEEDS_MANUAL_REVIEW.value,
            issues=[
                ValidationIssue(
                    field="document",
                    code="LOW_TEXT_CONFIDENCE",
                    message="Could not reliably extract text from PDF",
                    source="FBR_DERIVED",
                )
            ],
        )

    required_fbr = [
        ("invoice_reference", "INVOICE_REF_REQUIRED", "Invoice reference is required", "invoice_reference"),
        ("seller_name", "SELLER_NAME_REQUIRED", "Supplier name is required", "seller_name"),
        ("seller_ntn", "SELLER_NTN_REQUIRED", "Supplier NTN/STRN is required", "seller_ntn"),
        ("buyer_name", "BUYER_NAME_REQUIRED", "Buyer name is required", "buyer_name"),
        ("issue_date", "ISSUE_DATE_REQUIRED", "Invoice date is required", "issue_date"),
        ("total_amount", "TOTAL_REQUIRED", "Invoice total is required", "total_amount"),
    ]
    for attr, code, message, field in required_fbr:
        if not getattr(extracted, attr):
            issues.append(ValidationIssue(field=field, code=code, message=message, source="FBR_DERIVED"))

    if not extracted.due_date:
        issues.append(
            ValidationIssue(
                field="due_date",
                code="DUE_DATE_REQUIRED",
                message="Due date is required for Recovra aging (business rule)",
                source="RECOVRA_BUSINESS",
            )
        )

    if extracted.total_amount is not None and extracted.total_amount <= Decimal("0"):
        issues.append(
            ValidationIssue(
                field="total_amount",
                code="TOTAL_INVALID",
                message="Total amount must be positive",
                source="FBR_DERIVED",
            )
        )

    # Parse dates when present
    issue_date = None
    due_date = None
    if extracted.issue_date:
        try:
            issue_date = datetime.strptime(extracted.issue_date, "%Y-%m-%d").date()
        except ValueError:
            issues.append(
                ValidationIssue(
                    field="issue_date",
                    code="ISSUE_DATE_INVALID",
                    message="Issue date must be YYYY-MM-DD",
                    source="FBR_DERIVED",
                )
            )
    if extracted.due_date:
        try:
            due_date = datetime.strptime(extracted.due_date, "%Y-%m-%d").date()
        except ValueError:
            issues.append(
                ValidationIssue(
                    field="due_date",
                    code="DUE_DATE_INVALID",
                    message="Due date must be YYYY-MM-DD",
                    source="RECOVRA_BUSINESS",
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
            message="This is a local format check only; not FBR verified",
            source="RECOVRA_BUSINESS",
        )
    )

    return ValidationResult(
        status=ValidationStatus.ACCEPTED_LOCAL_CHECK.value,
        issues=[],
        warnings=warnings,
        normalized=_normalized(extracted, issue_date, due_date),
    )


def _normalized(extracted: ExtractedInvoice, issue_date, due_date) -> dict:
    return {
        "invoice_reference": extracted.invoice_reference,
        "seller_name": extracted.seller_name,
        "seller_ntn": extracted.seller_ntn,
        "buyer_name": extracted.buyer_name,
        "buyer_ntn": extracted.buyer_ntn,
        "issue_date": issue_date.isoformat() if issue_date else extracted.issue_date,
        "due_date": due_date.isoformat() if due_date else extracted.due_date,
        "currency": extracted.currency or "PKR",
        "total_amount": str(extracted.total_amount) if extracted.total_amount is not None else None,
        "profile_version": PROFILE_VERSION,
    }