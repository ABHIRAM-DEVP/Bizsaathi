# Demo accounts (development and test only)

The Next.js demo defaults to the synthetic Demo Store owner in `ENV=dev` or `ENV=test`; no login or password is required. The API accepts the following optional identity selector only for judging negative paths:

| Header | Tenant | Role | Intended judge path |
|---|---|---|---|
| `X-Demo-Account: demo-owner` | Demo Store | owner | Create, approve and edit catalogue/post work |
| `X-Demo-Account: demo-operator` | Demo Store | operator | Read catalogue, approvals, audit and trace; writes return 403 |
| `X-Demo-Account: demo-tenant-b-owner` | Tenant B | owner | Demonstrate tenant-isolation 404s |

These are fixed synthetic IDs, not passwords, and are deliberately rejected outside dev/test. They do not authenticate a production user. Customer/order demo data is deferred to Phase 4 because no customer or order schema exists yet.
