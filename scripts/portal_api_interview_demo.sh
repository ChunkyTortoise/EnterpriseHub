#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

BASE_URL="${PORTAL_API_BASE_URL:-http://127.0.0.1:8000}"
API_KEY="${PORTAL_API_DEMO_KEY:-}"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

print_fail() {
  local label="$1"
  local status="$2"
  local body_file="$3"
  echo "[FAIL] ${label} (status=${status})"
  if [[ -f "$body_file" ]]; then
    cat "$body_file"
    echo
  fi
  exit 1
}

request() {
  local method="$1"
  local path="$2"
  local data="${3:-}"
  local output_file="$4"

  local -a curl_args=(
    -sS
    -X "$method"
    -o "$output_file"
    -w "%{http_code}"
    "${BASE_URL}${path}"
  )

  if [[ -n "$API_KEY" ]]; then
    curl_args+=(-H "X-API-Key: ${API_KEY}")
  fi

  if [[ -n "$data" ]]; then
    curl_args+=(-H "content-type: application/json" --data "$data")
  fi

  curl "${curl_args[@]}"
}

assert_json() {
  local body_file="$1"
  local label="$2"
  local py_expr="$3"

  if ! python3 - "$body_file" "$py_expr" <<'PY'
import json
import sys

path, expr = sys.argv[1], sys.argv[2]
with open(path, "r", encoding="utf-8") as fh:
    payload = json.load(fh)
if not eval(expr, {"payload": payload}):  # noqa: S307 - local assertion script only
    raise AssertionError(expr)
PY
  then
    echo "[FAIL] ${label} (json assertion failed)"
    cat "$body_file"
    echo
    exit 1
  fi
}

echo "[STEP] 1/7 reset deterministic state"
reset_body="${TMP_DIR}/reset.json"
reset_status="$(request POST "/system/reset" "" "$reset_body")"
[[ "$reset_status" == "200" ]] || print_fail "reset deterministic state" "$reset_status" "$reset_body"
assert_json "$reset_body" "reset deterministic state" "payload.get('status') == 'success' and 'reset' in payload"
echo "[PASS] 1/7 reset deterministic state"

echo "[STEP] 2/7 fetch deck"
deck_body="${TMP_DIR}/deck.json"
deck_status="$(request GET "/portal/deck?contact_id=lead_001" "" "$deck_body")"
[[ "$deck_status" == "200" ]] || print_fail "fetch deck" "$deck_status" "$deck_body"
assert_json "$deck_body" "fetch deck" "isinstance(payload.get('deck'), list) and len(payload['deck']) >= 1"
echo "[PASS] 2/7 fetch deck"

echo "[STEP] 3/7 valid swipe"
swipe_body="${TMP_DIR}/swipe.json"
swipe_status="$(request POST "/portal/swipe" '{"contact_id":"lead_001","property_id":"prop_001","action":"like"}' "$swipe_body")"
[[ "$swipe_status" == "200" ]] || print_fail "valid swipe" "$swipe_status" "$swipe_body"
assert_json "$swipe_body" "valid swipe" "payload.get('status') == 'success' and payload.get('high_intent') is True"
echo "[PASS] 3/7 valid swipe"

echo "[STEP] 4/7 book tour"
book_body="${TMP_DIR}/book.json"
book_status="$(request POST "/vapi/tools/book-tour" '{"toolCall":{"id":"demo-1","function":{"arguments":{"contact_id":"lead_001","slot_time":"2026-02-15T10:00:00","property_address":"123 Palm Ave"}}}}' "$book_body")"
[[ "$book_status" == "200" ]] || print_fail "book tour" "$book_status" "$book_body"
assert_json "$book_body" "book tour" "isinstance(payload.get('results'), list) and payload['results'][0].get('toolCallId') == 'demo-1'"
echo "[PASS] 4/7 book tour"

echo "[STEP] 5/7 aggregate state"
state_body="${TMP_DIR}/state.json"
state_status="$(request GET "/system/state" "" "$state_body")"
[[ "$state_status" == "200" ]] || print_fail "aggregate state" "$state_status" "$state_body"
assert_json "$state_body" "aggregate state" "payload.get('status') == 'success' and payload.get('state', {}).get('inventory_interactions') == 1"
echo "[PASS] 5/7 aggregate state"

echo "[STEP] 6/7 detailed state"
details_body="${TMP_DIR}/details.json"
details_status="$(request GET "/system/state/details?limit=2" "" "$details_body")"
[[ "$details_status" == "200" ]] || print_fail "detailed state" "$details_status" "$details_body"
assert_json "$details_body" "detailed state" "payload.get('status') == 'success' and payload.get('details', {}).get('appointment', {}).get('booking_count') == 1"
echo "[PASS] 6/7 detailed state"

echo "[STEP] 7/7 invalid swipe returns 422"
invalid_body="${TMP_DIR}/invalid.json"
invalid_status="$(request POST "/portal/swipe" '{"contact_id":"lead_001","property_id":"prop_001","action":"save"}' "$invalid_body")"
[[ "$invalid_status" == "422" ]] || print_fail "invalid swipe returns 422" "$invalid_status" "$invalid_body"
assert_json "$invalid_body" "invalid swipe returns 422" "any(err.get('loc', [None])[-1] == 'action' for err in payload.get('detail', []))"
echo "[PASS] 7/7 invalid swipe returns 422"

echo "[PASS] interview demo flow completed"

