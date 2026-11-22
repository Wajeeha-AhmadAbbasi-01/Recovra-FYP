# Module 2 — Phase 3 report

**Date:** 2026-11-22  
**Status:** **Phase 3 UI complete** (mock inbox only). Live IMAP not implemented. Module 2 acceptance gate: team E2E + formal approval.

## Delivered

| Area | Routes / files |
|------|----------------|
| API client | `frontend/lib/api.ts` — collections + inbox + promise/dispute lists |
| Nav | `workspace-shell.tsx` — Collections, Inbox |
| Collections hub | `/collections` — tasks, preview, run cycle, **manual FOLLOW_UP task** |
| Task detail | `/collections/tasks/[id]` — view + patch status |
| Inbox list | `/inbox` — status, mock deliver (dev), message list |
| Inbox detail | `/inbox/[id]` — SUGGESTED links, **per-link Confirm → CONFIRMED**, manual link |
| Invoice collections | `/invoices/[id]` — record promise/dispute, **list + Confirm/Resolve**, timeline |
| List APIs | `GET /api/v1/collections/invoices/{id}/promises`, `GET .../disputes` |

## UI behavior (acceptance)

1. **Invoice:** Existing promises show **Confirm** (`PATCH` → `CONFIRMED`) and **Resolve** (`PATCH` → `FULFILLED` when confirmed). Disputes: **Confirm** → `CONFIRMED`, **Resolve** → `RESOLVED` (optional note).
2. **Collections:** **Create manual task** posts `FOLLOW_UP` via `POST /api/v1/collections/tasks`.
3. **Inbox:** Suggested links show status badge; **Confirm link** calls `POST .../links` with `action: confirm` and displays **SUGGESTED → CONFIRMED**.

## Not in Phase 3

- Live IMAP adapter (`IMAP_ENABLED` remains off unless separately approved).
- Outbound customer email (by design).
- Automated browser E2E tests.

## Manual end-to-end test checklist

Prerequisites: API on `:8000`, frontend dev server, logged-in user, at least one **active** overdue invoice in Module 1.

| # | Step | Expected |
|---|------|----------|
| 1 | **Collections** → Run reminder cycle | `tasks_created` ≥ 0; no email sent |
| 2 | **Create manual task** with invoice UUID + reason | New `FOLLOW_UP` task; opens task detail |
| 3 | Task detail → set status **COMPLETED** | Saves without error |
| 4 | Invoice detail → record promise → **Confirm** | Status `CONFIRMED`; timeline event |
| 5 | Same invoice → promise **Resolve** | Status `FULFILLED` |
| 6 | Record dispute → **Confirm** → **Resolve** | Hold semantics in reminder preview `SKIP` while confirmed |
| 7 | **Inbox** → mock deliver (or fixture with `invoice_references`) | Message shows **SUGGESTED** link |
| 8 | Message detail → **Confirm link** on suggested row | Banner: `SUGGESTED → CONFIRMED`; badge updates |
| 9 | **Collections** → reminder preview | Confirmed dispute/hold rows show skip where applicable |
| 10 | Regression: login, imports, invoices list | Module 1 unchanged |

## Gate

After the checklist passes, approve **Module 2** per `RECOVRA_CURSOR_AGENT_PROMPT.md`. Live IMAP is a separate follow-up, not required for Phase 3 UI sign-off.