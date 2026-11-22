# Current state

**Module:** 2 — Collections workflow, reminder scheduling, inbound email  
**Branch:** `module-2.1-ghazia`  
**Active phase:** **3** — frontend + mock/live inbox integration (authorized)  
**Phase 1:** closed and approved (2026-11-22)  
**Phase 2:** closed and approved (2026-11-22)  
**Owner:** Student 3 (UI); Student 2 owns live IMAP backend in Phase 3

## Approved gates

| Gate | Status |
|------|--------|
| Gate 0 | Approved 2026-11-22 |
| Phase 1 | Closed / approved |
| Phase 2 | Closed / approved |
| Phase 3 | **Authorized** — do not implement AI Module or customer email |
| Live IMAP mailbox | Requires separate operator approval before production poll |

## Database

- Team **Supabase** at Alembic **`c2a91f0m2p1`**.

## Working (Phases 1–2)

- Collections CRUD, promises, disputes, timeline, audit.
- Mock inbox ingest and invoice links.
- Rule eligibility, holds, idempotent `POST /api/v1/collections/reminders/run`, `GET .../reminders/preview`.
- Reference: `MODULE_2_IMPLEMENTATION.md`.

## Not yet (Phase 3)

- Collections Overview, Tasks, Promise/Dispute UI, Timeline, Inbox pages.
- Live IMAP adapter (mock remains default).
- Formal `ACCEPT MODULE 2` after Phase 3 complete.

## Next

Student 3: wire UI to existing APIs. Student 2: IMAP when mailbox approved. Stop at Phase 3 gate.

## Handoffs

- [MODULE_2_PHASE_1_TO_2.md](MODULE_2_PHASE_1_TO_2.md) (historical)
- Phase 2 report: [../phases/MODULE_2_PHASE_2_REPORT.md](../phases/MODULE_2_PHASE_2_REPORT.md)