# Approval routes

This route group presents owner review and approval experiences for proposed work. Approval is the human control boundary before consequential execution.

## Architecture and use

The UI displays proposals returned by the backend and submits owner decisions through the API. The backend must enforce authorization and bind approval to the exact proposal version; hiding or disabling a button is not a security control.

## Metrics and impact

No approval completion or false-approval metrics are recorded here. Evaluation threshold `false_approval_rate` is still `TODO`. The intended value is making proposed changes reviewable before they affect confirmed business data.
