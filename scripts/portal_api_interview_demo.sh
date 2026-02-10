#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

BASE_URL="${PORTAL_API_BASE_URL:-http://127.0.0.1:8000}"
API_KEY="${PORTAL_API_DEMO_KEY:-}"
AUTO_START="${PORTAL_API_AUTO_START:-1}"

TMP_DIR="$(mktemp -d)"
SERVER_PID=""
SERVER_LOG=""

cleanup() {
  if [[ -n "$SERVER_PID" ]]; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" >/dev/null 2>&1 || true
  fi
  if [[ -n "$SERVER_LOG" && -f "$SERVER_LOG" ]]; then
    rm -f "$SERVER_LOG"
  fi
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

is_local_base_url() {
  case "$BASE_URL" in
    http://127.0.0.1|http://127.0.0.1:*|http://localhost|http://localhost:*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

health_ready() {
  local status_code
  status_code="$(curl -sS -o /dev/null -w "%{http_code}" "${BASE_URL}/health" 2>/dev/null || true)"
  [[ "$status_code" == "200" ]]
}

wait_for_health() {
  local attempts="${1:-40}"
  for idx in $(seq 1 "$attempts"); do
    if health_ready; then
      return 0
    fi
    sleep 0.25
    if [[ "$idx" -eq "$attempts" ]]; then
      return 1
    fi
  done
}

start_local_server_if_needed() {
  if health_ready; then
    return 0
  fi

  if ! is_local_base_url; then
    echo "[FAIL] ${BASE_URL}/health is not reachable and auto-start is only supported for localhost URLs"
    exit 1
  fi

  if [[ "$AUTO_START" != "1" ]]; then
    echo "[FAIL] ${BASE_URL}/health is not reachable and PORTAL_API_AUTO_START is disabled"
    exit 1
  fi

  if ! command -v python3 >/dev/null 2>&1; then
    echo "[FAIL] python3 is required to auto-start local API server"
    exit 1
  fi

  local port
  port="$(echo "$BASE_URL" | sed -E 's#^https?://[^:/]+:([0-9]+).*$#\1#')"
  if [[ ! "$port" =~ ^[0-9]+$ ]]; then
    port="8000"
  fi

  SERVER_LOG="$(mktemp)"
  echo "[STEP] api health unavailable; auto-starting local server on port ${port}"
  python3 -m uvicorn main:app --host 127.0.0.1 --port "$port" >"$SERVER_LOG" 2>&1 &
  SERVER_PID="$!"

  if wait_for_health 60; then
    echo "[PASS] local server started (${BASE_URL})"
    return 0
  fi

  echo "[FAIL] local server failed to become healthy (${BASE_URL}/health)"
  cat "$SERVER_LOG"
  exit 1
}

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

request_with_headers() {
  local method="$1"
  local path="$2"
  local data="${3:-}"
  local output_file="$4"
  shift 4

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

  if [[ "$#" -gt 0 ]]; then
    local header
    for header in "$@"; do
      curl_args+=(-H "$header")
    done
  fi

  if [[ -n "$data" ]]; then
    curl_args+=(-H "content-type: application/json" --data "$data")
  fi

  curl "${curl_args[@]}"
}

request() {
  request_with_headers "$1" "$2" "${3:-}" "$4"
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

if ! command -v curl >/dev/null 2>&1; then
  echo "[FAIL] curl is required"
  exit 1
fi

start_local_server_if_needed

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

echo "[STEP] 8/10 tenant isolation proof"
tenant_reset_body="${TMP_DIR}/tenant_reset.json"
tenant_reset_status="$(request POST "/system/reset" "" "$tenant_reset_body")"
[[ "$tenant_reset_status" == "200" ]] || print_fail "tenant isolation reset" "$tenant_reset_status" "$tenant_reset_body"

tenant_swipe_body="${TMP_DIR}/tenant_swipe.json"
tenant_swipe_status="$(request_with_headers POST "/portal/swipe" '{"contact_id":"lead_001","property_id":"prop_001","action":"like","location_id":"tenant_payload"}' "$tenant_swipe_body" "X-Tenant-ID: tenant_a")"
[[ "$tenant_swipe_status" == "200" ]] || print_fail "tenant_a swipe" "$tenant_swipe_status" "$tenant_swipe_body"
assert_json "$tenant_swipe_body" "tenant_a swipe" "payload.get('status') == 'success' and payload.get('high_intent') is True"

tenant_b_deck_body="${TMP_DIR}/tenant_b_deck.json"
tenant_b_deck_status="$(request_with_headers GET "/portal/deck?contact_id=lead_001" "" "$tenant_b_deck_body" "X-Tenant-ID: tenant_b")"
[[ "$tenant_b_deck_status" == "200" ]] || print_fail "tenant_b deck after tenant_a swipe" "$tenant_b_deck_status" "$tenant_b_deck_body"
assert_json "$tenant_b_deck_body" "tenant_b deck after tenant_a swipe" "any(card.get('id') == 'prop_001' for card in payload.get('deck', []))"

tenant_a_state_body="${TMP_DIR}/tenant_a_state.json"
tenant_a_state_status="$(request_with_headers GET "/system/state" "" "$tenant_a_state_body" "X-Tenant-ID: tenant_a")"
[[ "$tenant_a_state_status" == "200" ]] || print_fail "tenant_a state" "$tenant_a_state_status" "$tenant_a_state_body"
assert_json "$tenant_a_state_body" "tenant_a state" "payload.get('state', {}).get('inventory_interactions') == 1 and payload.get('state', {}).get('ghl_actions') == 3"

tenant_b_state_body="${TMP_DIR}/tenant_b_state.json"
tenant_b_state_status="$(request_with_headers GET "/system/state" "" "$tenant_b_state_body" "X-Tenant-ID: tenant_b")"
[[ "$tenant_b_state_status" == "200" ]] || print_fail "tenant_b state" "$tenant_b_state_status" "$tenant_b_state_body"
assert_json "$tenant_b_state_body" "tenant_b state" "payload.get('state', {}).get('inventory_interactions') == 0 and payload.get('state', {}).get('ghl_actions') == 0"
echo "[PASS] tenant_a and tenant_b are fully isolated"

echo "[STEP] 9/10 performance validation"
perf_output="${TMP_DIR}/performance.txt"
perf_cmd=(
  python3
  scripts/portal_api_latency_sanity.py
  --base-url "$BASE_URL"
  --runs "${PORTAL_API_PERF_RUNS:-10}"
  --timeout "${PORTAL_API_PERF_TIMEOUT:-5}"
  --tenant-id "${PORTAL_API_PERF_TENANT_ID:-tenant_perf}"
)
if [[ -n "$API_KEY" ]]; then
  perf_cmd+=(--api-key "$API_KEY")
fi

if "${perf_cmd[@]}" >"$perf_output" 2>&1; then
  cat "$perf_output"
  echo "[PASS] p95 thresholds met"
else
  echo "[FAIL] p95 thresholds not met"
  cat "$perf_output"
  exit 1
fi

echo "[STEP] 10/10 multi-language detection"
lang_en_body="${TMP_DIR}/lang_en.json"
lang_en_status="$(request POST "/language/detect" '{"text":"I would like to schedule a property viewing tomorrow morning."}' "$lang_en_body")"
[[ "$lang_en_status" == "200" ]] || print_fail "language detect en" "$lang_en_status" "$lang_en_body"
assert_json "$lang_en_body" "language detect en" "payload.get('language') == 'en' and float(payload.get('confidence', 0.0)) >= 0.70"

lang_es_body="${TMP_DIR}/lang_es.json"
lang_es_status="$(request POST "/language/detect" '{"text":"Quiero programar una visita a la propiedad ma\u00f1ana por la ma\u00f1ana."}' "$lang_es_body")"
[[ "$lang_es_status" == "200" ]] || print_fail "language detect es" "$lang_es_status" "$lang_es_body"
assert_json "$lang_es_body" "language detect es" "payload.get('language') == 'es' and float(payload.get('confidence', 0.0)) >= 0.70"

lang_he_body="${TMP_DIR}/lang_he.json"
lang_he_status="$(request POST "/language/detect" '{"text":"\u05d0\u05e0\u05d9 \u05de\u05e2\u05d5\u05e0\u05d9\u05d9\u05df \u05dc\u05e7\u05d1\u05d5\u05e2 \u05e1\u05d9\u05d5\u05e8 \u05d1\u05d3\u05d9\u05e8\u05d4"}' "$lang_he_body")"
[[ "$lang_he_status" == "200" ]] || print_fail "language detect he" "$lang_he_status" "$lang_he_body"
assert_json "$lang_he_body" "language detect he" "payload.get('language') == 'he' and float(payload.get('confidence', 0.0)) >= 0.90"
echo "[PASS] multilingual readiness verified (en/es/he)"

echo "[PASS] interview demo flow completed (10/10)"
