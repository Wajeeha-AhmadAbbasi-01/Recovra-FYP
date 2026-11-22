# Module 2 Phase 1 report

**Owner:** Student 2  
**Date opened:** 2026-11-22  
**Status:** **CLOSED — APPROVED**  
**Approval recorded:** 2026-11-22 (team: Phase 1 complete after automated and manual verification)

## Scope delivered

- Tenant-scoped collections APIs: tasks, cases, promises, disputes, invoice timeline.
- Mock inbound inbox (ingest, list, link confirm/reject). No SMTP, no live IMAP.
- `GET /api/v1/collections/reminders/preview` returns HTTP 501 by design.
- Confirmed promise/dispute does **not** create `reminder_holds` in Phase 1 (delegated to Phase 2).
- Bugfix during verification: missing `sqlalchemy.func` import in `collections/service.py` `list_tasks`.

## Files (primary)

- `backend/app/modules/collections/`
- `backend/app/modules/inbox/`
- `backend/app/modules/audit/` (`origin`, `correlation_id`)
- `backend/alembic/versions/c2a91f0m2p1_module2_collections.py`
- `backend/tests/test_collections_phase1.py`
- `MODULE_2_IMPLEMENTATION.md`

## Migration

- Revision: `c2a91f0m2p1` (revises `b313838edb42`).
- **Applied** to team Supabase/Postgres (`DATABASE_URL` in root `.env`) via `alembic upgrade head` on 2026-11-22.
- Adds Module 2 tables and `audit_events.origin` / `correlation_id`.

## Automated tests

| Command | Date | Result |
|---------|------|--------|
| `python -m pytest tests/test_collections_phase1.py -q` (from `backend/`) | 2026-11-22 | **5 passed** |

## Manual verification (Swagger)

Completed successfully against running API (`/docs`). All checklist items passed:

1. Login / session for protected routes  
2. Task create, assign, complete (invoice balance unchanged)  
3. Promise record and confirm (`scheduling_effect` NOT_IMPLEMENTED)  
4. Dispute record and confirm  
5. Invoice timeline events  
6. Reminder preview → 501  
7. Mock inbox deliver  
8. Mock inbox dedupe on repeat deliver  
9. Message link confirm  
10. Mailbox status (`live_imap` NOT_IMPLEMENTED, `sends_mail` false)

## Risks / limitations carried to Phase 2

- No automatic reminder tasks, scheduler, or holds side effects.
- No collections/inbox UI (Phase 3).
- Other environments must run the same Alembic revision before using collections APIs.

## Phase 1 gate

**Closed.** Phase 2 (rules engine, scheduler, holds) is **authorized for Student 1** per team approval on 2026-11-22.

## Not in Phase 1 (unchanged)

Reminder scheduling, holds on confirm, live IMAP, frontend, outbound email.