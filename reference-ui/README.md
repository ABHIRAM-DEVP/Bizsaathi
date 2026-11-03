# 3 · Approval queue (mobile) — design reference

This is a design mockup created in a visual design tool, exported as a
standalone page. Treat it as a REFERENCE MOCKUP, not production code:
the markup and inline styles carry the design's precise values — colors,
font sizes, spacing, radii, shadows, layout — which an implementation
should replicate faithfully in its own components and styling system
rather than copy wholesale.

## Contents

- `Approvals.dc.html` — the artboard (a Design Component: an `<x-dc>`
  template + a small logic class). The values to replicate live in its
  inline `style="…"` attributes and the `<helmet><style>` block.
- `support.js`, `vendor/react*.js` — the runtime that renders the
  component in a browser; not part of the design.

## Viewing

Serve the folder (e.g. `python3 -m http.server`) and open `Approvals.dc.html`;
some browsers block the scripts over file://.

## Architecture, stack, and impact

These are static HTML design references rendered with the included design-tool support runtime. They do not call the BizSaathi API, persist data, or implement production authorization, approvals, or customer workflows. Use them to inspect visual values and inform a separate production implementation; do not copy their vendor runtime into the application.

There are no functional, performance, accessibility, or business-impact metrics for this mockup folder. The value is visual guidance only.
