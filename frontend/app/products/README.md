# Product routes

This route group supports product catalog browsing and product creation/editing, including photo-assisted draft workflows.

## Architecture and use

Product facts are persisted and confirmed through backend APIs. Photo analysis creates candidate fields; a seller must review and confirm them. The browser uploads media and observes the job status rather than treating an AI proposal as a database fact.

## Metrics and impact

`field_extraction_accuracy` remains `TODO` in the evaluation thresholds; no live accuracy or time-saved figure is claimed. The intended impact is faster catalog entry with human verification of uncertain fields.
