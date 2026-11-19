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

Session cookie name: `recovra_session` (configurable).