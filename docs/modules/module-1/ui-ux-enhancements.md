# Module 1 — UI/UX enhancements

## Scope

Frontend polish for dashboard, imports, customers, and invoices. Read-only API extensions; **no schema migrations**.

## Screens enhanced

| Route | Changes |
|-------|---------|
| `/dashboard` | Summary cards, human aging labels, overdue invoice table |
| `/imports` | Drag-drop queue, batch summary, richer results, sample download CTA |
| `/customers` | Directory table with aggregates |
| `/customers/[id]` | Customer detail + invoice list (new page) |
| `/invoices` | Search, formatting, customer column, status wording |
| `/invoices/[id]` | PKR/dates, customer link, loading/error |

## New shared components

`SummaryCard`, `EmptyState`, `ErrorState`, `LoadingSkeleton`, `CurrencyDisplay`, `DateDisplay` under `frontend/components/ui/`.

Utilities: `frontend/lib/format.ts`, `frontend/lib/labels.ts`.

## API changes (backward compatible)

| Endpoint | Change |
|----------|--------|
| `GET /api/v1/dashboard/summary` | + `overdue_amount`, `overdue_invoice_count` |
| `GET /api/v1/dashboard/aging` | + `bucket_counts` (existing `buckets` unchanged) |
| `GET /api/v1/dashboard/overdue-invoices` | **New** — overdue rows with customer name |
| `GET /api/v1/customers` | + `invoice_count`, `outstanding_total`, `overdue_count` |
| `GET /api/v1/customers/{id}` | + `summary`, `invoices[]` |
| `GET /api/v1/invoices` | + `customer_name` |
| `POST /api/v1/imports/pdf-batch` | Accepted rows may include `invoice_reference`, `buyer_name` |

Aging keys remain `CURRENT`, `1_30`, … — UI maps to plain-language labels.

## Data integrity

- Overdue = `due_date` before Asia/Karachi today with `days_overdue > 0`.
- No payment status; outstanding amounts from DB only.
- FBR disclaimer preserved on imports and invoice views.

## Tests run

```powershell
cd backend
python -m pytest tests/test_dashboard_enhancements.py tests/test_auth.py -q
```

`npm run lint` — not run (project has no ESLint config; Next prompted interactively).

## Limitations

- Customer list aggregates use per-customer queries (acceptable for SME scale).
- No STRN/phone fields in schema; UI shows buyer NTN and contact email when stored.
- Import rejected rows may omit `invoice_reference` / `buyer_name` if extraction failed early.