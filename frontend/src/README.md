# Secondary source tree

This tree contains application-related source files in addition to the root `frontend/app/` route tree. It includes an `app/`, shared components, a library (including an API client), and design tokens.

## Architecture and use

Because both `frontend/app/` and `frontend/src/app/` exist, avoid adding or changing routes in both places. The root `app/` is the current route tree documented by the frontend README; confirm imports and build behavior before moving or duplicating code here. The generated API client under `lib/api-client/` must not be edited by hand.

## Metrics and impact

No separate runtime metrics are recorded for this tree. Its value depends on how its shared modules are imported by the active app; do not assume files here are active merely because they exist.
