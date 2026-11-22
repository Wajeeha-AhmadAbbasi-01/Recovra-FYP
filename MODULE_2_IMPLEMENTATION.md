# Module 2 — Implemented Features and Technical Reference

## 0. Status / scope / branch / last verified date

- Branch: `module-2.1-ghazia`
- Date: 2026-11-22
- Phase: **1 closed and approved (2026-11-22).** Phase 2 **authorized** (Student 1). Phase 3 not started.
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

**NOT IMPLEMENTED.** Approved default, not executed: a routine task would be due the first `Asia/Karachi` day after `due_date` when the invoice is active, outstanding is greater than zero, due date is set, and no effective hold exists. Phase 1 does not run that rule.

### Actual files and functions/classes

| Concern | Actual location | Function/class or endpoint | What it does |
|---|---|---|---|
| Frontend | NOT IMPLEMENTED | | |
| API | `backend/app/modules/collections/router.py` | `reminder_preview` | Returns 501 |
| Rules/services | NOT IMPLEMENTED | | |
| Model/migration | `ReminderPolicy`, `FollowUpTask.dedupe_key` | stored only | Policy row is not inserted by an API |
| Tests | `test_promise_and_dispute_do_not_change_balance_or_holds` | preview status 501 | |

### Trigger/cadence and idempotency

No scheduler. Dedupe unique key exists for a later worker. Staff tasks use `staff:<uuid>` and are not reminder cycles.

### Data flow / state transitions

None for automatic tasks.

### Status / known limitations

`BLOCKED` on Phase 2. No email is sent.

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

Staff record a date they chose. The API does not parse phrases such as “Friday”. Confirming a promise does not create a hold in Phase 1. Invoice balance is unchanged. **Proposal rule deferred:** hold routine reminders until follow-up date.

### Actual files and functions/classes

| Concern | Actual location | Function/class or endpoint | What it does |
|---|---|---|---|
| Frontend | NOT IMPLEMENTED | | |
| API | `router.post_promise`, `router.patch_promise` | | |
| Rules/services | `service.record_promise`, `service.transition_promise` | Persist and transition | |
| Model/migration | `PaymentPromise` | | |
| Tests | `test_promise_and_dispute_do_not_change_balance_or_holds` | Amount over outstanding is 422; hold count stays 0 | |

### Trigger/cadence and idempotency

Manual. No automatic promise from email.

### Data flow / state transitions

`RECORDED` on create. Confirm sets `confirmed_by`. Response field `scheduling_effect` is `NOT_IMPLEMENTED`.

### Status / known limitations

Hold, expiry job, and follow-up task generation are Phase 2.

## 8. Feature 4: Dispute management

### Purpose and exact business rule

Staff record a reason and optional challenged amount. Confirm does not pause reminders in Phase 1. Resolve stores `resolved_by` and optional `resolution_note`. Rows are not deleted.

### Actual files and functions/classes

| Concern | Actual location | Function/class or endpoint | What it does |
|---|---|---|---|
| Frontend | NOT IMPLEMENTED | | |
| API | `router.post_dispute`, `router.patch_dispute` | | |
| Rules/services | `service.record_dispute`, `service.transition_dispute` | | |
| Model/migration | `Dispute`, `ReminderHold` | Hold table unused | |
| Tests | same promise/dispute test | Confirmed dispute, zero holds, balance unchanged | |

### Status / known limitations

Multi-hold precedence is Phase 2.

## 9. Feature 5: Rule-based reminder scheduling

### Purpose and exact business rule

**NOT IMPLEMENTED.** Stored policy defaults, not applied: `enabled=false`, `grace_days=0`, timezone `Asia/Karachi`, risk `STANDARD`, version `m2-phase1-unscheduled`. No weekend or holiday rule.

### Actual files and functions/classes

| Concern | Actual location | Function/class or endpoint | What it does |
|---|---|---|---|
| Frontend | NOT IMPLEMENTED | | |
| API | `reminder_preview` | HTTP 501 | |
| Rules/services | NOT IMPLEMENTED | | |
| Model/migration | `ReminderPolicy` | defaults only | |
| Tests | preview assertion | 501 | |

### Status / known limitations

`NOT IMPLEMENTED`.

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

| State | Phase 1 behavior |
|---|---|
| Invoice overdue / unpaid | Unchanged by Module 2 |
| Task completed | Task only |
| Promise confirmed | Status only. No hold |
| Dispute confirmed | Status only. No hold |
| Two holds | Table exists. No writer |
| Suggested mail link | Not financial truth |
| Claimed payment | Not a status. Staff may create `PAYMENT_VERIFICATION` manually. Balance unchanged |

## 13. End-to-end local runbook

Backend and frontend launch commands are in `README.md`. This phase adds no new process.

```powershell
cd backend
python -m pytest tests/test_collections_phase1.py -q
```

Env name only: `IMAP_ENABLED=false`. Do not set mailbox passwords in git.

`alembic upgrade` is operator-only and was not run.

## 14. Testing matrix

| Command | Date | Result |
|---|---|---|
| `python -m pytest tests/test_collections_phase1.py -q` | 2026-11-22 | **5 passed** |
| Manual Swagger Phase 1 checklist | 2026-11-22 | **10/10 passed** (team) |

Full backend `tests/` suite: **NOT RUN** at Phase 1 close (run before Phase 2 handoff if policy requires).

## 15. Security, permissions, tenant isolation and data protection

- Tenant id is taken from the session user.
- Missing cross-tenant invoice, task, message, or assignee is 404.
- Mock mailbox stores no credentials.
- HTML is reduced to text before storage.
- SMTP invitation mail in `backend/app/modules/team/email.py` is unchanged and is not used for collections.
- Module 2 has no send path.

## 16. Phase handoffs and explicit approvals

- Gate 0: approved 2026-11-22.
- Phase 1: **closed and approved** 2026-11-22 (automated + Swagger manual).
- Phase 2: **authorized** for Student 1.

**Handoff:** `docs/handoffs/MODULE_2_PHASE_1_TO_2.md`. Implement rules engine, scheduler, holds; stop at Phase 2 gate before Phase 3.

## 17. Future AI integration contract (not yet implemented)

Inbound text and promise notes are stored for staff. Nothing classifies Urdu, Roman Urdu, or English. A later module may suggest a date or a dispute. It must not confirm a promise, open a dispute, or set an invoice paid.

## 18. Known limitations and next steps

- No automatic tasks, holds, or scheduler.
- Preview is 501.
- Timeline filter is in application memory.
- Frontend has no collections or inbox routes.
- Postgres revision is unapplied.
- `ACCEPT MODULE 1` is still unrecorded in `docs/handoffs/CURRENT_STATE.md`.
