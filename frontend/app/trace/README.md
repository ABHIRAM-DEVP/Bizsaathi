# Job trace routes

This route group displays the progress or result of asynchronous jobs using their job identifiers.

## Architecture and use

The page reads backend job status/events and should present explicit not-found, pending, failed, and completed states. A stale or unknown job ID must not be presented as a successful result.

## Metrics and impact

No job latency or completion-rate metrics are recorded here. The route makes asynchronous processing observable to the seller.
