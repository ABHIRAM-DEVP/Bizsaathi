# Backend evaluation runner

This package contains backend-side evaluation execution. The canonical synthetic cases, threshold configuration, and reports are in the repository-level [evals/](../../../evals/README.md) directory.

## Use and architecture

The runner evaluates the implemented workflow against the configured cases and records results for comparison. Keep mock and live runs distinguishable; mock evaluation verifies deterministic plumbing, not live model quality. Do not tune thresholds merely to make a run pass.

## Metrics and impact

See [evals/thresholds.yaml](../../../evals/thresholds.yaml). Current absolute safety targets are zero cross-tenant leaks and zero duplicate side effects; unauthorized-action blocking is 1.0. Other listed quality, latency, and cost metrics remain `TODO` until a baseline is collected.
