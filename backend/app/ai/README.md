# AI model adapters

This package is the backend boundary for model providers. `interface.py` defines the operations consumed by application code; `mock.py` supports deterministic development and tests; `live.py` makes configured provider calls. Credentials and model configuration belong in server-side environment settings.

## Architecture and use

Callers use the shared interface instead of constructing provider requests directly. Image analysis and other supported modalities are sent through the adapter. Keep deterministic validation, tenant authorization, evidence checks, and action permissions outside the model.

## Stack, metrics, and impact

Python and the repository's configured provider protocol. No live quality, latency, or cost result is implied by adapter availability. Evaluation reports must label mock and live runs separately. The adapter enables provider changes and controlled model use without making model output authoritative.
