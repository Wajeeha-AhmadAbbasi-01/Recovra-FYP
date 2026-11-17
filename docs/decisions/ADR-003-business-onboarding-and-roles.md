# ADR-003 — Business onboarding, roles, and email

**Status:** Accepted for Module 1 implementation (development)

## Decisions

- Public self-service signup creates tenant + `owner` atomically.
- Signup redirects to login (no auto-login).
- Roles: `owner`, `finance_manager`.
- Globally unique normalized user email (one tenant per user).
- Invitation expiry: 72 hours (configurable).
- Development SMTP: Mailpit on `localhost:1025`, inbox `http://localhost:8025`.
- Production email provider: **TBD** (application fail-closed until configured).
- `.test` addresses allowed only in `development`/`test` environments.