#!/usr/bin/env bash
# Emoji API smoke test. Edit the CHECKS list at the bottom for your endpoints.
# Usage: API_URL=http://localhost:8000 bash scripts/api_smoke.sh
# Needs: curl. jq is optional (used only for JSON field checks).

API_URL="${API_URL:-http://localhost:8000}"
TOKEN="${TOKEN:-}"
PASS=0; FAIL=0; FAILED=()

# check "<label>" <METHOD> <path> <expected_status> [json_body] [grep_pattern_in_response]
check() {
  local label="$1" method="$2" path="$3" want="$4" body="${5:-}" pattern="${6:-}"
  local args=(-s -o /tmp/smoke_body.$$ -w '%{http_code} %{time_total}' -X "$method" "$API_URL$path" -H 'Content-Type: application/json')
  [ -n "$TOKEN" ] && args+=(-H "Authorization: Bearer $TOKEN")
  [ -n "$body" ] && args+=(-d "$body")
  local out code secs
  out=$(curl "${args[@]}" 2>/dev/null) || out="000 0"
  code="${out%% *}"; secs="${out##* }"
  local ms; ms=$(awk -v s="$secs" 'BEGIN{printf "%d", s*1000}')
  local ok=1
  [ "$code" = "$want" ] || ok=0
  if [ $ok -eq 1 ] && [ -n "$pattern" ]; then
    grep -q -- "$pattern" /tmp/smoke_body.$$ || ok=0
  fi
  if [ $ok -eq 1 ]; then
    printf '✅ %-38s %s %-22s %s (%sms)\n' "$label" "$method" "$path" "$code" "$ms"
    PASS=$((PASS+1))
  else
    printf '❌ %-38s %s %-22s got %s, want %s (%sms)\n' "$label" "$method" "$path" "$code" "$want" "$ms"
    [ -s /tmp/smoke_body.$$ ] && printf '   ↳ body: %s\n' "$(head -c 300 /tmp/smoke_body.$$)"
    FAIL=$((FAIL+1)); FAILED+=("$label")
  fi
}

echo "🚀 Smoke testing $API_URL"
echo "----------------------------------------------------------------"

# ---- EDIT BELOW: add one line per endpoint behavior ----
check "health responds"            GET  /health        200
check "unknown route returns 404"  GET  /does-not-exist 404
# check "create item (valid)"      POST /items 201 '{"name":"demo"}' '"id"'
# check "create item (invalid)"    POST /items 422 '{}'
# ---- EDIT ABOVE ----

rm -f /tmp/smoke_body.$$
echo "----------------------------------------------------------------"
if [ $FAIL -eq 0 ]; then
  echo "🎉 All $PASS checks passed"
  exit 0
else
  echo "💥 $FAIL failed, $PASS passed"
  for f in "${FAILED[@]}"; do echo "   ❌ $f"; done
  exit 1
fi
