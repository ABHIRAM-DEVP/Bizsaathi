# Repository scripts

This folder contains local verification and utility scripts: `runner.py`, secret scanning, evaluation dataset validation, documentation consistency, safety checks, and API smoke testing.

## Use

The cross-platform runner provides repository check recipes:

```powershell
python scripts/runner.py guards
python scripts/runner.py check-fast
python scripts/runner.py check
```

Individual scripts may have shell-specific requirements; for example, the secret scan uses Bash. Read the script and its documented prerequisites before invoking it. Scripts should report real command results and must not expose secrets.

## Metrics and impact

The runner reports command outcomes; no historical aggregate pass-rate metric is stored here. These tools automate repeatable checks for repository safety, contract/document consistency, tests, and build health.
