# Invoice data synchronization (Module 1)

## Root cause

Import batch results used a single `DUPLICATE` status for two different situations:

1. **Same PDF file (SHA-256)** — blocked even when the first attempt **never created an invoice** (rejected or needs review).
2. **Same invoice identity** (seller + reference) — correct duplicate protection, but responses omitted `invoice_id`, so the UI could not link to the existing record.

Users re-uploading the same file after a failed check saw **“Already imported”** while Dashboard / Invoices / Customers stayed empty.

## Affected components

| Layer | Component |
|-------|-----------|
| Backend | `backend/app/modules/imports/service.py` — SHA duplicate gate, duplicate API payload |
| Frontend | `frontend/app/(dashboard)/imports/page.tsx` — duplicate copy, invoice link, post-accept hint |
| APIs | Unchanged contracts; added optional `duplicate_kind` on batch `results[]` |

## Fix

- **SHA duplicate**: Return duplicate **only** when a prior upload with the same hash has an **active invoice**. Otherwise allow re-validation (new upload row).
- **Invoice identity duplicate**: Return `invoice_id` of the existing invoice; `duplicate_kind: "invoice"`, issue code `DUPLICATE_INVOICE`.
- **File duplicate**: `duplicate_kind: "file"`, issue code `DUPLICATE_FILE`, `invoice_id` set when known.
- **UI**: “View existing invoice” for duplicates; guidance to open Dashboard / Invoices after accept.

## Data flow

```
PDF batch → validate → ACCEPTED? → create Customer (match by name) + Invoice + Items → commit
                     → DUPLICATE (identity)? → no new invoice; response links existing id
Prior same SHA → has active invoice? → DUPLICATE (file) with invoice_id
              → no invoice → process again
Dashboard / Invoices / Customers → query by tenant_id (dashboard: active invoices only)
```

## Tests

`backend/tests/test_invoice_sync.py`:

- Accept increases dashboard and listing counts.
- Re-upload after accept: duplicate, one invoice, `invoice_id` on second result.
- Re-upload after failed extraction/validation: not treated as successful-import duplicate.
- Rejected uploads do not affect dashboard totals.

Run: `cd backend && python -m pytest tests/test_invoice_sync.py -q`

## Known limitations

- Customer match remains **exact `business_name`** per tenant (no fuzzy merge).
- Imports page does not auto-refresh other routes; navigate to Dashboard or Invoices after accept.
- Invoice list includes all lifecycle rows; dashboard uses **active** only.