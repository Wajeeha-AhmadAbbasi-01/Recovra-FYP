# Test results (latest local run)

| Suite | Command | Result |
|-------|---------|--------|
| Backend integration | `cd backend && python -m pytest tests -q` | 4 passed (SQLite in-memory) |
| Frontend build | `cd frontend && npm run build` | Passed (Next.js 15.5) |
| E2E | Manual demo script in README | Pending team run |

Environment: Windows, Python 3.11, no Docker on CI machine used for this record.