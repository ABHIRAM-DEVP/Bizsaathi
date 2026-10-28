# apps/web (the ONE Next.js app: web and PWA)

- Run here: `pnpm lint`, `pnpm typecheck`, `pnpm test --run`, `pnpm build`, `pnpm e2e`
- Server components by default; `use client` only for interaction. API calls only via the generated client in src/lib/api-client.
- Every data view: loading, empty, error, offline, permission-denied, success. Mark AI-suggested values visibly different from confirmed values.
- PWA is explicit work: manifest, icons, service worker, install prompt, update flow. Cache the app shell and static assets only. Never cache tenant data, auth responses or API JSON indiscriminately. Show clear connectivity state; server-backed actions say they need a connection.
- Approval screens show before/after diff, evidence, warnings and the side effect, bound to a proposal version.
- Never put secrets in NEXT_PUBLIC_*. The browser never talks to Meta directly.
- Mobile-first, keyboard reachable, labelled inputs, no color-only signals. No new UI library without an ADR.
