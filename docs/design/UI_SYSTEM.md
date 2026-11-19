# UI system — editorial SaaS (Module 1)

## Principles

- Warm neutral canvas, charcoal accent — not navy/gold banking dashboards.
- Generous whitespace, serif display headings, sans body.
- Public marketing vs authenticated workspace share one token set.
- Validation labels always say **local format check**, never “FBR verified”.

## Tokens

Defined in `frontend/app/globals.css` and `tailwind.config.ts`:

- `canvas` `#f6f3ee`, `surface` `#fffcf8`, `ink` `#1f1c1a`, `accent` `#2f3a36`
- Status colors map to validation enums via `StatusBadge`.

## Shared components

- `Button`, `Input`, `Card`, `StatusBadge`, `PageHeader`, `WorkspaceShell`
- `SummaryCard`, `EmptyState`, `ErrorState`, `LoadingSkeleton`, `CurrencyDisplay`, `DateDisplay`

Format helpers: `frontend/lib/format.ts` (PKR, Karachi dates, aging labels).

## Routes

Public: `/`, `/signup`, `/login`, `/invite/[token]`  
Workspace: `/dashboard`, `/imports`, `/invoices`, `/customers`, `/team` (owner)