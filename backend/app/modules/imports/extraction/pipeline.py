from app.modules.fbr_validation.schemas import ExtractedInvoice
from app.modules.imports.extraction.field_scanner import scan_fields
from app.modules.imports.extraction.legacy_labels import apply_legacy_labels
from app.modules.imports.extraction.reader import read_pdf_text
from app.modules.imports.extraction.table_parser import parse_line_items


def extract_invoice_from_pdf(data: bytes, *, max_pages: int) -> tuple[ExtractedInvoice, dict]:
    text, evidence = read_pdf_text(data, max_pages=max_pages)
    invoice = ExtractedInvoice(raw_text_length=len(text))
    evidence["field_evidence"] = []

    if len(text) < 40:
        invoice.text_confidence = "low"
        invoice.extraction_method = "none"
        return invoice, evidence

    legacy_count = apply_legacy_labels(invoice, text, evidence)
    field_evidence = scan_fields(invoice, text)
    evidence["field_evidence"] = [fe.__dict__ for fe in field_evidence]

    line_items = parse_line_items(text)
    invoice.line_items = line_items

    if legacy_count >= 5:
        invoice.extraction_method = "legacy_labels"
    elif line_items:
        invoice.extraction_method = "structured_v2"
    elif field_evidence:
        invoice.extraction_method = "field_scan"
    else:
        invoice.extraction_method = "none"
        invoice.text_confidence = "low"

    if invoice.grand_total is not None and invoice.total_amount is None:
        invoice.total_amount = invoice.grand_total

    return invoice, evidence