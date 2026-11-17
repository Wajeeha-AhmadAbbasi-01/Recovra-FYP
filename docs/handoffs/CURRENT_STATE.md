# Current state

**Module:** 1 — Invoice intake, auth, dashboard  
**Status:** Implementation baseline in `Recovra-FYP/`  
**Phases:** 0–3 code present; formal G1/G2/G3 human tokens still required per team process.

## Working

- Backend API (FastAPI): auth, team invitations, PDF batch import, local validation, invoices, customers, dashboard
- Frontend (Next.js): landing, signup/login, workspace UI, editorial SaaS tokens
- Fixtures under `fixtures/`
- Backend tests: `cd backend && python -m pytest tests -q` (SQLite in-memory)

## Local run

See [README.md](../../README.md). Docker optional (Postgres + Mailpit).

## Next

- Team verification on Postgres + Mailpit demo path
- Record `APPROVE PHASE 1/2` and `ACCEPT MODULE 1` in phase reports when ready