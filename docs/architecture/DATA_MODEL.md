# Data model

Module 1 tables (`tenants`, `users`, `sessions`, `customers`, `uploads`, `validation_attempts`, `invoices`, `invoice_items`, `audit_events`, team invitations) are the SQLAlchemy models under `backend/app/modules/`. This file records the Module 2 additions only.

Money stays `Numeric(18, 2)`. Collection rows do not copy invoice totals. Outstanding balance remains `invoices.outstanding_amount`.

## Module 2 tables

Defined in `backend/app/modules/collections/models.py` and `backend/app/modules/inbox/models.py`.

| Table | Isolation / idempotency |
|---|---|
| `collection_cases` | Unique `(tenant_id, invoice_id)` |
| `follow_up_tasks` | Unique `(tenant_id, dedupe_key)` |
| `reminder_policies` | Unique `tenant_id`. Stored defaults. Scheduling is not implemented |
| `payment_promises` | Tenant and invoice indexes |
| `disputes` | Tenant and invoice indexes |
| `reminder_holds` | Schema only. Phase 1 writes no rows |
| `mailboxes` | Unique `(tenant_id, provider)`. No credential columns |
| `inbound_messages` | Unique `(tenant_id, mailbox_id, folder, uidvalidity, uid)` |
| `message_invoice_links` | Unique `(tenant_id, message_id, invoice_id)` |

`audit_events` gained nullable `origin` and `correlation_id`.

Migration file: `backend/alembic/versions/c2a91f0m2p1_module2_collections.py`. **Not applied.**
