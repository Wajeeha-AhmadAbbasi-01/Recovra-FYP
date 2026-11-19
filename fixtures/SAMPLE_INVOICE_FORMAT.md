# Sample invoices that pass Recovra local checks

Use these **text-based PDFs** in **Imports**. They are illustrative only — not official FBR documents.

| File | Invoice ref | Buyer | Expected |
|------|-------------|-------|----------|
| `recovra_sample_accepted_001.pdf` | RECOVRA-SAMPLE-2026-001 | Fictitious Buyer Company | Accept; 2 line items |
| `recovra_sample_accepted_002.pdf` | RECOVRA-SAMPLE-2026-002 | Second Buyer Trading Co | Accept; 1 line item, **second customer** |

**Also in the app:** Imports → **Download Sample Invoice Format** (same layout as `001`).

## Required for accept (`registered_b2b_goods_v2`)

### Option A — Machine-readable block (recommended)

One line per field (keys must match):

```
INVOICE_REF: <unique ref>
SELLER_NAME: ...
SELLER_NTN: ...
BUYER_NAME: ...
ISSUE_DATE: YYYY-MM-DD
DUE_DATE: YYYY-MM-DD
CURRENCY: PKR
TOTAL_AMOUNT: 12345.67
LINE_ITEM: Description|qty|unit_price|line_total|hs_code_optional
```

Rules:

- Text must be selectable (not a scan).
- One invoice per PDF; single page preferred.
- `qty × unit_price` must match `line_total` within **PKR 0.05**; line totals must sum to **TOTAL_AMOUNT**.
- If `LINE_ITEM:` lines are present, at least one line is required.

### Option B — Labeled fields + visible labels

Same fields with prefixes such as `Seller NTN:`, `Buyer:`, `Issue Date:`, `Grand Total:` (see field scanner patterns in the codebase).

## After upload

- **Status:** Passed Local Validation  
- **Saved:** Yes  
- **View invoice** link present  
- Dashboard / Invoices / Customers update (hard-refresh if needed)

Duplicate uploads of the same file or same seller + reference return **Already imported** without doubling counts.