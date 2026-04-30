#!/usr/bin/env bash
# Run all three k6 load test scripts and capture results.
#
# Requires: k6 installed (https://k6.io/docs/get-started/installation/)
# Requires: app running at BASE_URL (default: http://localhost:8000)
#
# Usage:
#   ./benchmarks/run_k6.sh                         # localhost:8000
#   BASE_URL=https://staging.example.com ./benchmarks/run_k6.sh
#   TARGET_RPS=75 ./benchmarks/run_k6.sh           # half-rate sustained test

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
TARGET_RPS="${TARGET_RPS:-150}"
RESULTS_DIR="benchmarks/results/2026-W17"
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)

echo "=== EnterpriseHub k6 Load Tests ==="
echo "  BASE_URL   : $BASE_URL"
echo "  TARGET_RPS : $TARGET_RPS (sustained test)"
echo "  Results    : $RESULTS_DIR/"
echo ""

if ! command -v k6 &>/dev/null; then
  echo "ERROR: k6 not found. Install from https://k6.io/docs/get-started/installation/"
  exit 1
fi

# Verify app is reachable
if ! curl -sf "$BASE_URL/health" >/dev/null 2>&1 && \
   ! curl -sf "$BASE_URL/api/health" >/dev/null 2>&1; then
  echo "WARN: Could not reach $BASE_URL/health — ensure the app is running before tests."
fi

mkdir -p "$RESULTS_DIR"

run_test() {
  local name="$1"
  local script="$2"
  local out="$RESULTS_DIR/${name}_${TIMESTAMP}.json"
  echo "--- Running: $name ---"
  k6 run "$script" \
    --out "json=${out}" \
    -e "BASE_URL=$BASE_URL" \
    -e "TARGET_RPS=$TARGET_RPS" \
    --summary-export "$RESULTS_DIR/${name}_summary_${TIMESTAMP}.json"
  echo "    Results: $out"
  echo ""
}

run_test "qualification_load" "benchmarks/k6/qualification_load.js"
run_test "burst"              "benchmarks/k6/burst.js"
run_test "sustained"          "benchmarks/k6/sustained.js"

echo "=== All tests complete. Results in $RESULTS_DIR/ ==="
echo "Commit results with: git add $RESULTS_DIR && git commit -m 'bench: k6 results $TIMESTAMP'"
