# Module 2 Phase 2 report

**Owner:** Student 1  
**Date opened:** 2026-11-22  
**Status:** **CLOSED — APPROVED**  
**Approval recorded:** 2026-11-22 (automated, manual Swagger, team sign-off)

## Scope delivered

- Pure reminder eligibility (`rules/eligibility.py`): `Asia/Karachi` calendar day, `grace_days`, active holds, policy enablement.
- Tenant policy bootstrap (`policy.py`): `m2-phase2-v1`, `enabled=true`, `grace_days=0` on first use.
- Routine **staff** `RULE` `REMINDER` tasks via `reminder_cycle.py` (no customer email).
- Holds: confirm promise/dispute → active `reminder_holds`; release on resolve/cancel/fulfill/expire; multi-hold respected.
- APIs: `GET /api/v1/collections/reminders/preview`, `POST /api/v1/collections/reminders/run`.
- Promise/dispute transitions wired in `service.py` with `holds.py`.
- `scheduling_effect` on promise/dispute responses reflects active holds.

## Automated tests

| Command | Date | Result |
|---------|------|--------|
| `python -m pytest tests/test_collections_rules.py tests/test_collections_phase1.py tests/test_collections_phase2.py -q` | 2026-11-22 | **11 passed** |

## Manual verification (Swagger)

Confirmed by team on 2026-11-22:

- Preview shows **SKIP** with reason **`active_reminder_hold`** when dispute is confirmed.
- **`POST /reminders/run`** is idempotent (`tasks_created: 0` on repeat run).
- No emails sent (`sends_customer_email: false` on preview/run).

## Risks / limitations

- No Celery/Redis: operators trigger cycle via `POST /reminders/run` or external cron with session auth.
- `risk_level` stored on policy only; no per-invoice cadence variants yet.
- UI and live IMAP remain Phase 3.

## Phase 2 gate

**Closed.** Phase 3 (frontend + live IMAP with Student 2) is **authorized to start** per team approval 2026-11-22.

## Not in Phase 2

Next.js collections/inbox pages, production IMAP mailbox, outbound mail, AI modules.