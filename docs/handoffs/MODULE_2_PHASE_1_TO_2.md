# Module 2 — Phase 1 → Phase 2 handoff

**From:** Student 2 (Phase 1)  
**To:** Student 1 (Phase 2)  
**Date:** 2026-11-22  
**Authorization:** Phase 2 is **approved to start**.

## What Phase 1 left you

- **APIs** already live: tasks, promises, disputes, cases, timeline, mock inbox (`backend/app/modules/collections/`, `backend/app/modules/inbox/`).
- **DB** on Supabase at revision `c2a91f0m2p1` (collection tables, inbox tables, audit columns).
- **Policies** table/model exists but scheduling is not wired (`ReminderPolicy`, `m2-phase1-unscheduled`).
- **Holds** table exists; Phase 1 **does not** insert rows on promise/dispute confirm — that is your work.
- **No worker** — plan allows a minimal scheduled job or explicit service entry point; still **no customer email**.

## Phase 2 objectives (plan)

1. **Pure rules** — `services/rules/`: inputs = invoice due/outstanding/status, tenant policy, risk field, active holds, confirmed promise/dispute, clock (`Asia/Karachi`). Outputs = decision, reason, next eligible date, action type. Unit-testable.
2. **Automatic reminder tasks** — idempotent dedupe keys; eligible overdue invoices get staff `RULE` tasks; never send mail.
3. **Scheduler** — use existing infra if any, else approved minimal polling/cron; safe catch-up without duplicates.
4. **Promise lifecycle** — on `CONFIRMED`, create/release holds per policy, set follow-up dates; expire/resume; **never** change `outstanding_amount`.
5. **Dispute lifecycle** — confirmed dispute holds; resolve releases only applicable hold; respect multiple holds.
6. **Tests** — idempotency, multi-hold, timezone boundaries, tenant isolation, no Module 1 balance changes.
7. **Docs** — update `MODULE_2_IMPLEMENTATION.md` feature sections 1, 3–5, 9, 12 with real paths and test results.

## Defaults already assumed (confirm or change with team)

- Timezone `Asia/Karachi`, `grace_days=0` until overridden per tenant.
- Routine reminder eligible day after due date when active, outstanding > 0, due set, no effective hold.
- `GET /collections/reminders/preview` should become a read-only preview (still no send).

## Out of scope for Phase 2

- Next.js UI (Phase 3).
- Live IMAP (Phase 3, Student 2).
- AI/NLP, SMTP, invoice payment settlement.

## Suggested first files to read

- `MODULE_2_IMPLEMENTATION.md` §§4–12  
- `backend/app/modules/collections/service.py` (transitions; extend, do not break Phase 1 contracts)  
- `backend/app/modules/invoices/aging.py`  
- `backend/tests/test_collections_phase1.py` (regression must stay green)

## Phase 2 stop gate

When done: phase report, tests run, ask explicitly:

**“Do you approve Phase 2 and authorize Student 3 (with Student 2 for IMAP) to begin Phase 3?”**

Do not start Phase 3 without that token.