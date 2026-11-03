# Frontend

The frontend is the repository's single Next.js App Router application. It provides seller-facing workflows and public storefront/customer chat experiences; it is not a separate frontend per feature.

## Architecture and use

The Next.js app renders route-level experiences and shared components. It calls the FastAPI backend through shared URL/API helpers. Authentication context handles the seller session; server-side API authorization and tenant scope remain authoritative. The PWA shell supports install/offline states, but offline mode must not imply that server-side actions were delivered.

Main routes include login, products and photo-assisted product drafts, approvals, posts, orders, owner messages, job traces, and public stores. The API contract is [../contracts/openapi.json](../contracts/openapi.json).

## Stack

Next.js 16.4.3, React 19.3.0, TypeScript, Tailwind CSS 4, ESLint 9, npm. Versions are read from `package.json`; see `docs/12-assumptions-risks-deps.md` for repository-wide verified assumptions.

```powershell
npm run dev
npm run lint
npm run build
```

## Metrics and impact

No production usage, accessibility score, web-vitals, or business-impact metrics are recorded here. The intended value is one consistent interface for seller workflows and customer-facing conversations. Measure real task completion and customer outcomes before claiming impact.
