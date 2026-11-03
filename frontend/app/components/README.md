# Shared frontend components

This folder contains reusable UI components such as the seller shell, connection status, workflow stepper, and draft review.

## Architecture and use

Use shared components for consistent navigation and workflow feedback. Components should expose honest loading, offline, failure, draft, and delivery states and should not imply that a backend action succeeded without a successful response.

## Metrics and impact

No component-level usage or accessibility metrics are recorded. Shared components reduce duplicated interaction patterns and help keep status communication consistent.
