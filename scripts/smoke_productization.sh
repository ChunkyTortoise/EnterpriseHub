#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"

echo "== Intake Diagnose =="
curl -sS -X POST "${BASE_URL}/api/v2/intake/diagnose" \
  -H "Content-Type: application/json" \
  -d '{
    "engagement_id":"smoke-eng-1",
    "vertical_profile":"real_estate",
    "client_name":"Smoke Client",
    "goals":["improve response sla","increase qualified leads"],
    "context":{"channels":["sms"],"event_volume_14d":40}
  }' | jq .

echo "== Workflow Bootstrap =="
curl -sS -X POST "${BASE_URL}/api/v2/workflows/bootstrap" \
  -H "Content-Type: application/json" \
  -d '{"engagement_id":"smoke-eng-1"}' | jq .

echo "== Generate Proof Pack =="
curl -sS -X POST "${BASE_URL}/api/v2/reports/proof-pack" \
  -H "Content-Type: application/json" \
  -d '{
    "engagement_id":"smoke-eng-1",
    "event_count":20,
    "baseline_kpis":{"response_sla_seconds":300,"qualified_leads":10,"attributed_revenue":10000},
    "current_kpis":{"response_sla_seconds":120,"qualified_leads":15,"attributed_revenue":17000}
  }' | jq .

echo "== Fetch Proof Pack =="
curl -sS "${BASE_URL}/api/v2/reports/smoke-eng-1" | jq .
