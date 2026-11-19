from decimal import Decimal

from app.modules.fbr_validation.schemas import ExtractedInvoice, ValidationIssue

MONEY_TOLERANCE = Decimal("0.05")


def reconcile_line_items(invoice: ExtractedInvoice) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not invoice.line_items:
        return issues

    running = Decimal("0")
    for idx, item in enumerate(invoice.line_items, start=1):
        expected = (item.quantity * item.unit_price).quantize(Decimal("0.01"))
        if abs(expected - item.line_total) > MONEY_TOLERANCE:
            issues.append(
                ValidationIssue(
                    field=f"line_items[{idx}]",
                    code="LINE_TOTAL_MISMATCH",
                    message=f"Line {idx}: quantity × unit price does not match line total within tolerance.",
                    source="RECOVRA_BUSINESS",
                    rule_id="RECOVRA-LINE-MATH",
                    severity="ERROR",
                )
            )
        running += item.line_total

    grand = invoice.grand_total or invoice.total_amount
    if grand is not None and abs(running - grand) > MONEY_TOLERANCE:
        issues.append(
            ValidationIssue(
                field="grand_total",
                code="GRAND_TOTAL_MISMATCH",
                message="Sum of line totals does not match invoice grand total within tolerance.",
                source="RECOVRA_BUSINESS",
                rule_id="RECOVRA-GRAND-TOTAL",
                severity="ERROR",
            )
        )
    return issues