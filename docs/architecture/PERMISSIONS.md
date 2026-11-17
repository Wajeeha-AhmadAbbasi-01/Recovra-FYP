# Permission matrix (Module 1)

| Operation | owner | finance_manager |
|-----------|:-----:|:---------------:|
| Register business | n/a (public) | n/a |
| Login / logout / me | yes | yes |
| Dashboard, invoices, customers, imports | yes | yes |
| Invite finance manager | yes | no |
| List/revoke invitations | yes | no |
| List team members | yes | no |

Enforcement: FastAPI dependencies + `require_owner()` on team routes. UI hiding is not security.