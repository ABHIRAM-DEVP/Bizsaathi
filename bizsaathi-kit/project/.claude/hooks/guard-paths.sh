#!/bin/bash
# PreToolUse hook for Edit|Write. Needs jq. Exit 2 = block (stderr shown to Claude).
INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // empty')
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
[ -z "$FILE" ] && exit 0

case "$FILE" in
  */apps/web/src/lib/api-client/*)
    echo "Blocked: generated API client. Change the API, run just export-openapi and regenerate." >&2; exit 2 ;;
  */pnpm-lock.yaml|*/uv.lock|*/package-lock.json)
    echo "Blocked: lockfiles are changed by the package manager, not by hand." >&2; exit 2 ;;
  */.env|*/.env.*)
    case "$FILE" in *.example) ;; *)
      echo "Blocked: do not read or write .env files. Document variables in .env.example." >&2; exit 2 ;;
    esac ;;
  */alembic/versions/*|*/migrations/versions/*)
    if [ "$TOOL" = "Edit" ]; then
      echo "Blocked: do not edit an existing migration. Add a new one with just new-migration." >&2; exit 2
    fi ;;
  */evals/dataset/cases.jsonl)
    : ;; # allowed; heldout discipline is enforced by rules and review
esac

# Block secrets or secret-looking public env vars in written content.
CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // .tool_input.new_string // empty')
if [ -n "$CONTENT" ]; then
  if echo "$CONTENT" | grep -Eq 'NEXT_PUBLIC_[A-Z0-9_]*(KEY|SECRET|TOKEN|PASSWORD)'; then
    echo "Blocked: secret-like name in a NEXT_PUBLIC_ variable. Public variables are shipped to browsers." >&2; exit 2
  fi
  if echo "$CONTENT" | grep -Eq '(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)'; then
    echo "Blocked: content looks like a real secret. Use environment variables." >&2; exit 2
  fi
fi
exit 0
