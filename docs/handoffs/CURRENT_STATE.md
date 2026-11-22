# Current state

**Module:** 2 — Collections workflow, reminder scheduling, inbound email  
**Branch:** `module-2.1-ghazia`  
**Active phase:** **2** — rules engine, scheduler, holds (Student 1)  
**Phase 1:** closed and approved (2026-11-22)

## Approved gates

| Gate | Status |
|------|--------|
| Gate 0 (Module 2 architecture) | Approved 2026-11-22 |
| Phase 1 implementation + tests + Swagger manual pass | **Approved / closed** 2026-11-22 |
| Phase 2 work (Student 1) | **Authorized** — do not start Phase 3 or live IMAP yet |
| Live IMAP / customer email | Not authorized (Phase 3 + separate mailbox approval) |

## Database

- Alembic head **`c2a91f0m2p1`** applied on team **Supabase** Postgres (2026-11-22).
- Other clones must run `alembic upgrade head` against their own `DATABASE_URL`.

## What works (Phase 1 baseline)

- `/api/v1/collections/*` — tasks, cases, promises, disputes, timeline (session, tenant-scoped).
- `/api/v1/inbox/*` — mock deliver, messages, link decisions; no send.
- Module 1 dashboard, invoices, imports unchanged in scope.
- Reference: `MODULE_2_IMPLEMENTATION.md`, `docs/phases/MODULE_2_PHASE_1_REPORT.md`.

## Next (Phase 2 only)

Student 1: eligibility/rules service, idempotent scheduler job, promise/dispute hold + follow-up dates, tests, update `MODULE_2_IMPLEMENTATION.md`. Stop at Phase 2 gate before UI or live IMAP.

## Handoff doc

`docs/handoffs/MODULE_2_PHASE_1_TO_2.md`