# frontend

- Run here: `npm run lint`, `npm run build`, `npm run dev`
- Layout: app/, public/, src/components, src/lib/api-client
- ONE Next.js App Router app for web and PWA. Never fork code for mobile vs desktop.
- Generated API client in src/lib/api-client is read-only (generated from contracts/openapi.json).
- Never store secrets or API keys in NEXT_PUBLIC_ variables.
