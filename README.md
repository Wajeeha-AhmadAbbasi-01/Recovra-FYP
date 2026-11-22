# Recovra (Module 1) — Recovra-FYP

Multi-tenant receivables workspace: business signup, PDF invoice intake, **local FBR-oriented format checks** (not official FBR verification), customers, invoices, aging dashboard.

## Prerequisites

- Python 3.11+
- Node.js 20+
- Optional: Docker Desktop for PostgreSQL + Mailpit (`compose.yaml`)

## Quick start (development)

```powershell
cd Recovra-FYP
copy .env.example .env

# Backend
cd backend
python -m pip install -e ".[dev]"
cd ..
python scripts/bootstrap_db.py
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
$env:NEXT_PUBLIC_API_BASE_URL="http://localhost:8000"
npm run dev
```

Open `http://localhost:3000` — register, sign in, upload PDFs from `fixtures/` (generate with `python scripts/generate_fixture_pdfs.py`).

### Mailpit (invitations)

```powershell
cd Recovra-FYP
docker compose up -d mailpit
```

SMTP `localhost:1025`, web UI `http://localhost:8025`.

### PostgreSQL (recommended for team demo)

Set `DATABASE_URL` in `.env` to Postgres, run `docker compose up -d postgres`, then `cd backend; alembic upgrade head` or `python ../scripts/bootstrap_db.py`.

## Tests

```powershell
cd backend
python -m pytest tests -q
```

Integration tests use in-memory SQLite unless `DATABASE_URL` is set.

## Module 2 (collections + inbox)

Backend: tasks, promises, disputes, timeline, rule-based reminder cycle (staff tasks only), mock inbox ingest. **No customer email.** Invoice balances are unchanged by collections actions. Live IMAP remains opt-in (`IMAP_ENABLED=false` by default).

Frontend (Phase 3): **Collections** (`/collections`, `/collections/tasks/[id]`), **Inbox** (`/inbox`, `/inbox/[id]`), promise/dispute + timeline on **invoice detail**.

Migration `c2a91f0m2p1` on team Supabase — run `alembic upgrade head` from `backend/` when your DB is behind.

```powershell
cd backend
python -m pytest tests/test_collections_rules.py tests/test_collections_phase1.py tests/test_collections_phase2.py -q
```

See `MODULE_2_IMPLEMENTATION.md` and `docs/handoffs/CURRENT_STATE.md`.

## Compliance note

UI and API labels describe **local format checks**. They do not certify FBR registration, payment, or tax compliance.