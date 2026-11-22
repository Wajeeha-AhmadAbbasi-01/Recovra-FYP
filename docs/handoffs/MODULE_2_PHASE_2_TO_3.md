# Module 2 — Phase 2 → Phase 3 handoff

**From:** Student 1 (Phase 2)  
**To:** Student 3 (UI) + Student 2 (IMAP)  
**Date:** 2026-11-22  
**Authorization:** Phase 3 approved to start.

## APIs ready for UI

| Route | Use in UI |
|-------|-----------|
| `GET/POST/PATCH /collections/tasks` | Task queue and detail |
| `POST/PATCH .../promises`, `.../disputes` | Record / confirm dialogs |
| `GET .../timeline` | Invoice activity |
| `GET /reminders/preview` | Scheduling panel (read-only) |
| `POST /reminders/run` | Admin “run cycle” (optional button) |
| `GET/POST /inbox/*` | Inbox list, mock deliver in dev |

Envelope: `{ data, error, meta }`. Session cookie auth (same as Module 1).

## Copy / labels

- Never label as “email sent” or “customer reminded.”
- Distinguish **staff task** vs **customer message**.

## Phase 3 deliverables

1. Nav + pages in `frontend/` matching `docs/design/UI_SYSTEM.md`.
2. `frontend/lib/api.ts` extensions for collections/inbox.
3. Student 2: live IMAP behind `IMAP_ENABLED` + approved credentials only.
4. E2E demo per Module 2 plan; no Module 1 regression.

## Stop gate

Ask: **“Do you approve the completed Module 2?”** before AI work.