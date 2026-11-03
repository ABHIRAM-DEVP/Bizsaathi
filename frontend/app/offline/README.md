# Offline route

> [Back to BizSaathi overview](../../../README.md)

This route communicates the app's offline or disconnected state.

## Architecture and use

Offline UI must accurately distinguish cached display from server-confirmed changes. Do not present an action as delivered or persisted when it has only been stored in the browser.

## Metrics and impact

No offline availability or recovery metrics are recorded. The route provides user feedback during connectivity loss; it is not itself an offline synchronization guarantee.
