#!/bin/bash
# Stop hook: the agent may not stop while `just check-fast` fails.
# Needs jq and just. Uses the fast check so every stop stays cheap.
INPUT=$(cat)

# Loop guard: if we already blocked once this turn, let Claude stop.
if [ "$(echo "$INPUT" | jq -r '.stop_hook_active')" = "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

# Skip in repos without a justfile or without just installed.
command -v just >/dev/null 2>&1 || exit 0
[ -f justfile ] || exit 0

# Skip when nothing changed (pure Q&A turns).
if git rev-parse --git-dir >/dev/null 2>&1 && [ -z "$(git status --porcelain)" ]; then
  exit 0
fi

OUT=$(timeout 300 just check-fast 2>&1)
CODE=$?
if [ $CODE -ne 0 ]; then
  TAIL=$(echo "$OUT" | tail -n 40)
  REASON="just check-fast FAILED (exit $CODE). You are not done. Fix the failures below, then report. Output tail:
$TAIL"
  jq -n --arg r "$REASON" '{decision: "block", reason: $r}'
  exit 0
fi
exit 0
