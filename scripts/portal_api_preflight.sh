#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${PORTAL_API_BASE_URL:-http://127.0.0.1:8000}"

run_check() {
  local label="$1"
  shift
  echo "[STEP] ${label}"
  if "$@"; then
    echo "[PASS] ${label}"
  else
    echo "[FAIL] ${label}"
    exit 1
  fi
}

check_cmd() {
  command -v "$1" >/dev/null 2>&1
}

check_health() {
  local body_file
  body_file="$(mktemp)"
  local status_code
  status_code="$(curl -sS -o "$body_file" -w "%{http_code}" "${BASE_URL}/health")"
  rm -f "$body_file"
  [[ "$status_code" == "200" ]]
}

run_check "python3 is available" check_cmd python3
run_check "curl is available" check_cmd curl
run_check "ruff is available" check_cmd ruff
run_check "pytest is available" check_cmd pytest
run_check "portal openapi snapshot exists" test -f portal_api/tests/openapi_snapshot.json
run_check "validate script is executable" test -x scripts/portal_api_validate.sh
run_check "demo script is executable" test -x scripts/portal_api_interview_demo.sh
run_check "api health responds 200 (${BASE_URL}/health)" check_health

echo "[PASS] preflight checks completed"
