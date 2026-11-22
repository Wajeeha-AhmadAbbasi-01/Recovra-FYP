# Module 2 — Collections workflow (Phase 1)

**Owner this phase:** Student 2 (backend / security)  
**Scope now:** tenant-scoped HTTP contracts, state-transition guards, audit rows, mock inbound mail.  
**Deferred:** reminder rule engine, holds that change scheduling, workers, live IMAP, frontend.

## What works

- Manual follow-up tasks for an invoice in the same tenant. Assignee must be an active member of that tenant.
- Task statuses: `OPEN`, `IN_PROGRESS`, `ON_HOLD`, `COMPLETED`, `CANCELLED`. Terminal states reject further status changes.
- Completing a task does not change `invoices.outstanding_amount` or `lifecycle_status`.
- Staff can record a payment promise or dispute with an explicit calendar date and optional amount. Amount cannot exceed outstanding. Confirming either record does **not** create a `reminder_holds` row.
- Invoice timeline reads `audit_events` for that tenant and invoice.
- Mock mailbox ingest stores one row per `(tenant, mailbox, folder, UIDVALIDITY, UID)`. Body text is tag-stripped. Invoice links start as `SUGGESTED` until staff confirm or reject.
- `GET /api/v1/collections/reminders/preview` returns HTTP 501. No message is sent.

## Dependencies

Module 1 invoice, customer, user, tenant, and session models. Existing `log_event`. No Celery, Redis, or IMAP library.

## Config

`IMAP_ENABLED` defaults to false. Mock deliver is available only when `APP_ENV` is `development` or `test`.

## Tests

`backend/tests/test_collections_phase1.py`

## Limits

No automatic reminder tasks. No email sending. No live mailbox. Frontend routes are unchanged. Postgres migration is not applied.
