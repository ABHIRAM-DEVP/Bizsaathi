---
name: new-page
description: Add a Next.js App Router page for the single web/PWA app with generated API client, all UI states, AI-vs-confirmed labelling and tests. Use when adding or changing a web route.
argument-hint: "[route - purpose]"
disable-model-invocation: true
---

# New page: $ARGUMENTS

Prerequisite: task file and the route's section in docs/03-ui.md.

1. Read .claude/rules/web-pwa.md, apps/web/CLAUDE.md and the nearest existing page.
2. Component tests first (Testing Library, by role/label): loading, empty, error, offline, permission-denied, success, plus the main interaction. Show them fail.
3. Server component fetching through src/lib/api-client; small client component for interaction only. AI suggestions look different from confirmed facts (label + shape).
4. If the page offers an action that changes data or sends content: use the approval pattern (diff, evidence, warnings, proposal version).
5. `just check-fast`, then `just check` (includes `pnpm build`). For visuals or PWA behavior, run it at mobile and desktop width and describe what you actually saw, or write NOT VERIFIED.
6. Report with the AGENTS.md final report format.
