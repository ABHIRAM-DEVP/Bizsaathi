---
paths:
  - "frontend/**/*.{ts,tsx,css,json}"
  - "frontend/public/**"
---

# Web and PWA rules
- One Next.js codebase serves browser and installed PWA. Do not fork routes, components or config for "mobile app" vs "web".
- Server components by default; client components small and only for interaction, forms and browser APIs.
- API access only through the generated client; types come from contracts/openapi.json. Public store chat uses /public/* endpoints with opaque session ids.
- PWA checklist (verify against current Next.js and web.dev docs): web app manifest with icons, service worker registered only in production build, install prompt handling, update-available flow, offline fallback page.
- Caching: app shell and static assets only. Never cache authenticated JSON, tenant data or approval payloads indiscriminately. Offline UI states the truth: reading cached shell works, server-backed actions need a connection, queued actions (if any) show sync state.
- Distinguish AI suggestion vs confirmed fact visually (label plus shape, not color alone) in every product, content and answer view.
- Approval UI: show diff, evidence, warnings, side effect; submit with proposal version. Disable approve when the proposal has changed.
- SSE or polling for job progress with a visible stalled/failed state.
- Accessibility: labelled inputs, focus order, keyboard operation, sufficient contrast, reduced-motion respect.
- Test with Testing Library (roles/labels) and Playwright at mobile and desktop viewport.
