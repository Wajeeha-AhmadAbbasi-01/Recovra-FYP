# Invoice ingestion V2

## Scope

- Text-based PDF only (no OCR), single page, one invoice per file.
- Local validation profile: `registered_b2b_goods_v2`.
- Extraction: legacy label blocks and/or `LINE_ITEM:` machine-readable lines plus field scanning.
- Financial checks: line `quantity × unit_price` vs `line_total`, and sum of lines vs grand/total (tolerance PKR 0.05).

## API batch result fields (per file)

| Field | Description |
|-------|-------------|
| `seller_name`, `buyer_name` | Extracted parties |
| `issue_date`, `due_date` | ISO dates when present |
| `invoice_total` | Normalized total |
| `line_item_count` | Parsed line items |
| `validation_profile` | e.g. `registered_b2b_goods_v2` |
| `extraction_method` | `legacy_labels`, `structured_v2`, `field_scan`, or `none` |
| `local_status_label` | Human-readable status |
| `issues[]` / `warnings[]` | `field`, `code`, `message`, `source`, `rule_id`, `severity` |

## Persistence (accepted only)

- Multiple `InvoiceItem` rows from extracted lines (with optional `hs_code`).
- `Invoice.claimed_fbr_identifier` when `FBR_INVOICE_NUMBER` / equivalent is extracted.

## Disclaimer

Passed local checks are **not** official FBR verification. See `FBR_RULE_REGISTER.md` for rule citations.