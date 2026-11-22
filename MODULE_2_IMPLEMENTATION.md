# Module 2 — Implemented Features and Technical Reference

## 0. Status / scope / branch / last verified date

- Branch: `module-2.1-ghazia`
- Date: 2026-11-22
- Phase: **3 in progress (2026-11-22).** Frontend wired to collections/inbox APIs; live IMAP still not implemented.
- Migration `c2a91f0m2p1`: **applied** on team Supabase via `alembic upgrade head` (2026-11-22).
- Live IMAP: **not implemented.** No customer email is sent.
- Phase 1 verification: automated **5 passed**; manual Swagger checklist **10/10** (see phase report).

## 1. Module 1 dependencies and compatibility contract

Collections read existing invoices. They do not rewrite invoice, customer, import, or FBR validation code.

| Fact | Source |
|---|---|
| Invoice id, tenant, customer, reference, due date, outstanding, lifecycle | `backend/app/modules/invoices/models.py` |
| Eligible receivables are `lifecycle_status=active` rows created only after `ACCEPTED_LOCAL_CHECK` | `backend/app/modules/imports/service.py` |
| Outstanding is the balance. There is no payment table | `Invoice.outstanding_amount` |
| Calendar day for overdue filters | `today_karachi()` in `backend/app/modules/invoices/aging.py` (`Asia/Karachi`) |
| Session user supplies tenant. Roles `owner` and `finance_manager` | `get_current_user` |

A task, promise, dispute, or message link must not change outstanding or lifecycle.

## 2. Architecture: frontend → API → services → database → jobs/IMAP

Frontend collections and inbox pages: **NOT IMPLEMENTED.**

```text
Session cookie
  -> /api/v1/collections/*   router.py -> service.py -> repository.py -> PostgreSQL/SQLite
  -> /api/v1/inbox/*         router.py -> service.py (mock adapter) -> inbound tables
  -> audit_events via log_event
```

No worker, Celery, Redis, or IMAP socket exists. `IMAP_ENABLED` defaults false (`backend/app/core/config.py`).

## 3. Database tables and migrations (actual names, commands, approvals)

Models: `backend/app/modules/collections/models.py`, `backend/app/modules/inbox/models.py`.  
Audit columns `origin`, `correlation_id`: `backend/app/modules/audit/models.py`.

Revision file: `backend/alembic/versions/c2a91f0m2p1_module2_collections.py`  
Revises: `b313838edb42`.

**Applied (team Supabase, 2026-11-22):** `alembic upgrade head` → revision `c2a91f0m2p1`.

Other environments: run the same from `backend/` with `DATABASE_URL` set (e.g. load from root `.env`). Rollback: `alembic downgrade b313838edb42` only with explicit team approval.

SQLite tests build tables with `Base.metadata.create_all` in `backend/tests/conftest.py`. They do not apply Alembic.

## 4. API inventory (method, path, request/response, roles)

Prefix `/api/v1`. Envelope `{data, error, meta}`. Auth: session. Role: any active workspace member (`owner` or `finance_manager`).

| Method | Path | Behavior |
|---|---|---|
| GET | `/collections/tasks` | Filters `status`, `assignee`, `customer`, `overdue`, `page`, `page_size` |
| POST | `/collections/tasks` | Creates `STAFF` task. Body: `invoice_id`, `task_type`, `reason`, optional `due_at`, `priority`, `assignee_id` |
| GET | `/collections/tasks/{id}` | 404 if missing or other tenant |
| PATCH | `/collections/tasks/{id}` | Status, assignee, `clear_assignee`, `due_at`, `priority` |
| GET | `/collections/cases` | Filters `status`, `customer`, pagination |
| GET | `/collections/cases/{id}` | |
| POST | `/collections/invoices/{id}/promises` | `promised_date` required. Optional `amount`, `follow_up_date`, `note` |
| PATCH | `/collections/promises/{id}` | `status` transition |
| POST | `/collections/invoices/{id}/disputes` | `reason`, optional `challenged_amount` |
| PATCH | `/collections/disputes/{id}` | `status`, optional `resolution_note` |
| GET | `/collections/invoices/{id}/timeline` | Paginated audit items |
| GET | `/collections/reminders/preview` | HTTP 501 |
| GET | `/inbox/mailbox/status` | `live_imap=NOT_IMPLEMENTED`, `sends_mail=false` |
| POST | `/inbox/mailbox/mock-deliver` | Dev/test only. Body `{messages: [...]}` |
| GET | `/inbox/messages` | `link_state`, `unlinked`, pagination |
| GET | `/inbox/messages/{id}` | |
| POST | `/inbox/messages/{id}/links` | `{invoice_id, action: confirm\|reject}` |

Task transitions (`service.TASK_TRANSITIONS`): `OPEN` → in progress, on hold, completed, cancelled. `IN_PROGRESS` and `ON_HOLD` → the other of those two, or completed, or cancelled. `COMPLETED` and `CANCELLED` are terminal.

Promise: `RECORDED` → `CONFIRMED` or `CANCELLED`. `CONFIRMED` → `FULFILLED`, `CANCELLED`, or `EXPIRED`.  
Dispute: `OPEN` → `CONFIRMED` or `CANCELLED`. `CONFIRMED` → `RESOLVED`.

## 5. Feature 1: Automatic reminder task creation

### Purpose and exact business rule

### Purpose and exact business rule

First eligible Karachi day = `due_date + grace_days + 1`. Creates a **staff** `RULE` task of type `REMINDER` when invoice is `active`, `outstanding_amount > 0`, due date set, policy enabled, no **active** `reminder_hold`. Does **not** send customer email.

### Actual files and functions/classes

| Concern | Actual location | Function/class or endpoint | What it does |
|---|---|---|---|
| Frontend | NOT IMPLEMENTED | | |
| API | `collections/router.py` | `run_reminders`, `reminder_preview` | Run cycle / preview |
| Rules | `collections/rules/eligibility.py` | `evaluate_routine_reminder`, `routine_reminder_dedupe_key` | Pure eligibility |
| Scheduler | `collections/reminder_cycle.py` | `run_tenant_reminder_cycle`, `create_routine_task_if_eligible` | Idempotent task insert |
| Policy | `collections/policy.py` | `ensure_reminder_policy` | `m2-phase2-v1` |
| Tests | `test_collections_phase2.py`, `test_collections_rules.py` | idempotency, hold skip | |

### Trigger/cadence and idempotency

`POST /api/v1/collections/reminders/run` per tenant session. Dedupe key `rule:{policy_version}:routine:{invoice_id}:{due_date}`. Repeat run → `tasks_created: 0`.

### Status / known limitations

No background worker. Operator cron may call run endpoint. No email is sent.

## 6. Feature 2: Follow-up task management

### Purpose and exact business rule

Staff create and update tasks. Completing a task closes the task only. **Implementation assumption:** both workspace roles may assign any active member of the same tenant. Cross-tenant assignee returns 404.

### Actual files and functions/classes

| Concern | Actual location | Function/class or endpoint | What it does |
|---|---|---|---|
| Frontend | NOT IMPLEMENTED | | |
| API | `collections/router.py` | `list_tasks`, `post_task`, `get_task`, `patch_task` | HTTP only |
| Rules/services | `collections/service.py` | `create_task`, `update_task`, `TASK_TRANSITIONS` | Guards and audit |
| Model/migration | `FollowUpTask`, `CollectionCase` | | Case is created on first staff action for that invoice |
| Tests | `test_collections_phase1.py` | `test_task_assignment_transition_and_balance`, `test_cross_tenant_invoice_task_hidden` | |

### Trigger/cadence and idempotency

Manual POST only. Each staff task gets a new dedupe key.

### Data flow / state transitions

See section 4. `COMPLETED` sets `completed_at` and `completed_by`.

### API, DB tables, tests and edge cases

`overdue=true` filters the linked invoice (due before Karachi today, outstanding > 0, active). It does not change the invoice. Impossible transitions return 409.

### Status / known limitations

Backend list/detail/patch works. UI is Phase 3.

## 7. Feature 3: Payment promise recording

### Purpose and exact business rule

Staff record a date they chose; no NLP. **CONFIRMED** creates `CONFIRMED_PROMISE` hold and sets `follow_up_date` to `promised_date` if missing. Invoice balance unchanged. Expired promises on cycle run → `EXPIRED` + hold released.

### Actual files and functions/classes

| Concern | Actual location | Function/class or endpoint | What it does |
|---|---|---|---|
| Holds | `collections/holds.py` | `on_promise_confirmed`, `on_promise_terminal` | Active hold rows |
| Service | `collections/service.py` | `transition_promise` | Wires holds |
| Present | `collections/present.py` | `scheduling_effect_for_invoice` | `hold_active` / `routine_may_apply` |
| Tests | `test_collections_phase1.py`, `test_collections_phase2.py` | active holds, multi-hold | |

### Status / known limitations

Does not mark invoice paid. UI deferred to Phase 3.

## 8. Feature 4: Dispute management

### Purpose and exact business rule

**CONFIRMED** creates `CONFIRMED_DISPUTE` hold (preview **SKIP** / `active_reminder_hold`). **RESOLVED** or **CANCELLED** releases that hold only. Other active holds remain.

### Actual files and functions/classes

| Concern | Actual location | Function/class or endpoint | What it does |
|---|---|---|---|
| Holds | `collections/holds.py` | `on_dispute_confirmed`, `on_dispute_resolved_or_cancelled` | |
| Tests | `test_collections_phase2.py` | `test_hold_blocks_new_rule_task`, multi-hold | |

## 9. Feature 5: Rule-based reminder scheduling

### Purpose and exact business rule

Policy defaults: `enabled=true`, `grace_days=0`, `Asia/Karachi`, `STANDARD` risk, version `m2-phase2-v1`. Preview lists per-invoice `decision`, `reason`, `would_create_task`, `sends_customer_email: false`.

### Actual files and functions/classes

| Concern | Actual location | Function/class or endpoint | What it does |
|---|---|---|---|
| API | `router.reminder_preview` | GET preview | |
| Rules | `rules/eligibility.py` | `evaluate_routine_reminder` | |
| Cycle | `reminder_cycle.py` | `preview_tenant_reminders` | |

### Status / known limitations

No weekend/holiday rules. Risk does not change cadence yet.

## 10. Feature 6: Follow-up history and audit log

### Purpose and exact business rule

Phase 1 writes an audit row for task create/update, promise record/transition, dispute record/transition, mock ingest, and link confirm/reject. Actor is the staff user. Origin is `staff`. Rejected HTTP calls do not write a success event because the handler raises before commit.

### Actual files and functions/classes

| Concern | Actual location | Function/class or endpoint | What it does |
|---|---|---|---|
| Frontend | NOT IMPLEMENTED | | |
| API | `router.get_timeline` | | |
| Rules/services | `service._audit`, `inbox.service` `log_event` calls | | |
| Model/migration | `AuditEvent.origin`, `correlation_id` | `audit/service.py` `log_event` | |
| Tests | timeline assertion | `promise_recorded`, `dispute_recorded` | |

### Status / known limitations

Timeline loads tenant audit rows and filters `summary.invoice_id` in Python. No delete API for audit rows. Message ingest summary stores mailbox id and UID, not the body.

## 11. Feature 7: Inbound IMAP email integration

### Purpose and exact business rule

Mock ingest only. Identity is `(tenant, mailbox, folder, uidvalidity, uid)`. RFC Message-ID is stored and is not the unique key. Matching on invoice reference creates `SUGGESTED` links and does not confirm them. Multiple references can suggest multiple invoices. Staff confirm or reject. Reading or linking mail does not change balances.

### Actual files and functions/classes

| Concern | Actual location | Function/class or endpoint | What it does |
|---|---|---|---|
| Frontend | NOT IMPLEMENTED | | |
| API | `inbox/router.py` | `mailbox_status`, `mock_deliver`, `list_messages`, `get_message`, `post_link` | |
| Rules/services | `inbox/service.py` | `ingest_mock`, `decide_link`, `get_or_create_mock_mailbox` | No network |
| Sanitize | `inbox/sanitize.py` | `sanitize_body` | Strips tags, caps length |
| Model/migration | `Mailbox`, `InboundMessage`, `MessageInvoiceLink` | | No secret columns |
| Tests | `test_mock_inbox_dedupe_suggestion_and_tenant_isolation`, `test_sanitize_strips_markup` | | |

### Secure setup and deduplication

`POST /inbox/mailbox/mock-deliver` returns 404 outside `development` and `test`. Status payload has no password. Repeated UID returns `created: false`. Live polling is **NOT IMPLEMENTED**.

## 12. Business-state and priority rules

| State | Behavior (after Phase 2) |
|---|---|
| Invoice overdue / unpaid | Unchanged by Module 2 |
| RULE task created | Staff reminder only; no email |
| Task completed | Task only |
| Promise confirmed | Active promise hold; routine RULE tasks skipped |
| Dispute confirmed | Active dispute hold; preview SKIP `active_reminder_hold` |
| Resolve dispute | Release dispute hold; promise hold may remain |
| Suggested mail link | Not financial truth |
| Claimed payment | Does not change `outstanding_amount` |

## 13. End-to-end local runbook

Backend and frontend launch commands are in `README.md`. This phase adds no new process.

```powershell
cd backend
python -m pytest tests/test_collections_rules.py tests/test_collections_phase1.py tests/test_collections_phase2.py -q
```

Env name only: `IMAP_ENABLED=false`. Do not set mailbox passwords in git.

`alembic upgrade` is operator-only and was not run.

## 14. Testing matrix

| Command | Date | Result |
|---|---|---|
| `python -m pytest tests/test_collections_phase1.py -q` | 2026-11-22 | **5 passed** |
| `python -m pytest tests/test_collections_rules.py tests/test_collections_phase1.py tests/test_collections_phase2.py -q` | 2026-11-22 | **11 passed** |
| Manual Swagger Phase 1 checklist | 2026-11-22 | **10/10 passed** |
| Manual Swagger Phase 2 checks | 2026-11-22 | **Passed** (hold preview, idempotent run, no send) |

Full backend `tests/` suite: **NOT RUN** (Module 1 regression separate).

## 15. Security, permissions, tenant isolation and data protection

- Tenant id is taken from the session user.
- Missing cross-tenant invoice, task, message, or assignee is 404.
- Mock mailbox stores no credentials.
- HTML is reduced to text before storage.
- SMTP invitation mail in `backend/app/modules/team/email.py` is unchanged and is not used for collections.
- Module 2 has no send path.

## 16. Phase handoffs and explicit approvals

- Gate 0: approved 2026-11-22.
- Phase 1: **closed and approved** 2026-11-22.
- Phase 2: **closed and approved** 2026-11-22.
- Phase 3: **authorized** 2026-11-22.

**Handoff:** `docs/handoffs/MODULE_2_PHASE_2_TO_3.md`. UI + IMAP; stop at Module 2 acceptance gate.

## 17. Future AI integration contract (not yet implemented)

Inbound text and promise notes are stored for staff. Nothing classifies Urdu, Roman Urdu, or English. A later module may suggest a date or a dispute. It must not confirm a promise, open a dispute, or set an invoice paid.

## 18. Known limitations and next steps

- Collections/inbox UI: initial slice (`frontend/app/(dashboard)/collections`, `inbox`, invoice collections card); polish + confirm flows remain.
- No live IMAP.
- No Celery worker (manual/cron `POST /reminders/run`).
- Timeline filter is in application memory.
- **Next:** Phase 3 UI and optional live IMAP (`docs/handoffs/MODULE_2_PHASE_2_TO_3.md`).
