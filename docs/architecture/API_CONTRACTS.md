# API contracts (Module 1)

Base URL: `http://localhost:8000`

Envelope: `{ "data": ..., "error": null|{code,message,details}, "meta": { "request_id" } }`

## Auth

| Method | Path | Auth |
|--------|------|------|
| POST | `/api/v1/auth/register` | Public |
| POST | `/api/v1/auth/login` | Public (sets HttpOnly session cookie) |
| POST | `/api/v1/auth/logout` | Session |
| GET | `/api/v1/auth/me` | Session |

## Team (owner-only where noted)

| POST | `/api/v1/team/invitations` | Owner |
| GET | `/api/v1/team/invitations` | Owner |
| DELETE | `/api/v1/team/invitations/{id}` | Owner |
| POST | `/api/v1/team/invitations/accept` | Public |
| GET | `/api/v1/team/members` | Owner |

## Finance workspace

| GET | `/api/v1/customers` | Session |
| GET | `/api/v1/customers/{id}` | Session |
| GET | `/api/v1/invoices` | Session |
| GET | `/api/v1/invoices/{id}` | Session |
| GET | `/api/v1/invoices/{id}/document` | Session |
| POST | `/api/v1/imports/pdf-batch` | Session (multipart files) |
| GET | `/api/v1/imports/{id}` | Session |
| GET | `/api/v1/imports/{id}/validation` | Session |
| GET | `/api/v1/imports/{id}/document` | Session |
| GET | `/api/v1/imports/sample-invoice.pdf` | Public |
| GET | `/api/v1/dashboard/summary` | Session (+ overdue totals) |
| GET | `/api/v1/dashboard/aging` | Session (+ `bucket_counts`) |
| GET | `/api/v1/dashboard/overdue-invoices` | Session (`?limit=100`) |
| GET | `/api/v1/health` | Public |

## Collections (Module 2, Phase 1)

Session required. Tenant comes from the session user. Both `owner` and `finance_manager` may call these routes. Responses use the same envelope. Promise and dispute bodies include `scheduling_effect: "NOT_IMPLEMENTED"`.

| Method | Path | Notes |
|--------|------|--------|
| GET | `/api/v1/collections/tasks` | `status`, `assignee`, `customer`, `overdue`, `page`, `page_size` |
| POST | `/api/v1/collections/tasks` | Manual staff task. Does not change invoice balance |
| GET | `/api/v1/collections/tasks/{id}` | 404 outside the tenant |
| PATCH | `/api/v1/collections/tasks/{id}` | Assignment and allowed status transitions |
| GET | `/api/v1/collections/cases` | `status`, `customer`, `page`, `page_size` |
| GET | `/api/v1/collections/cases/{id}` | |
| POST | `/api/v1/collections/invoices/{id}/promises` | Staff-selected date. No hold |
| PATCH | `/api/v1/collections/promises/{id}` | Explicit status transition |
| POST | `/api/v1/collections/invoices/{id}/disputes` | Unconfirmed record does not create a hold |
| PATCH | `/api/v1/collections/disputes/{id}` | Explicit status transition |
| GET | `/api/v1/collections/invoices/{id}/timeline` | Audit rows for that invoice |
| GET | `/api/v1/collections/reminders/preview` | **501** not implemented. Sends nothing |

## Inbox (Module 2, Phase 1, mock only)

| Method | Path | Notes |
|--------|------|--------|
| GET | `/api/v1/inbox/mailbox/status` | Health only. No secrets. `live_imap` is `NOT_IMPLEMENTED` |
| POST | `/api/v1/inbox/mailbox/mock-deliver` | `development` and `test` only. No network, no send |
| GET | `/api/v1/inbox/messages` | `link_state` or `unlinked`, `page`, `page_size` |
| GET | `/api/v1/inbox/messages/{id}` | |
| POST | `/api/v1/inbox/messages/{id}/links` | `{ invoice_id, action: confirm\|reject }` |

Session cookie name: `recovra_session` (configurable).