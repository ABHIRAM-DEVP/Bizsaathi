# Frontend context

> [Back to BizSaathi overview](../../../README.md)

`AuthContext.tsx` provides shared seller authentication/session state to frontend routes.

## Architecture and use

Use it to coordinate client navigation and session-aware UI. It is not an authorization boundary: protected API routes must validate the session and enforce business/tenant scope on the server.

## Metrics and impact

No session success or retention metrics are recorded here. Shared session state helps provide a consistent login experience while backend checks protect data.
