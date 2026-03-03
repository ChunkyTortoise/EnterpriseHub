# Weekly Proof-Pack Operations Runbook

## Purpose
Operational sequence to generate, validate, and persist weekly pilot reporting artifacts for revenue-v2 delivery.

## Standard Weekly Run (Friday)
1. Generate KPI aggregates:
   - `python3 scripts/generate_weekly_pilot_kpis.py`
2. Render executive proof-pack markdown:
   - `python3 scripts/generate_weekly_executive_proof_pack.py --tenant-id <tenant_id>`
3. Persist reporting data to DB (safe in non-DB environments):
   - `python3 scripts/persist_revenue_pilot_data.py --allow-db-unavailable`

## One-Command Option
- `make pilot-proof-pack-sync`

## Validation Gates
1. `python3 scripts/ci/compile_check.py`
2. `python3 scripts/ci/no_mock_in_prod.py`
3. `python3 scripts/ci/revenue_ops_qa.py`

## Failure Handling
- Input schema/data errors:
  - script exits with `INPUT_ERROR` (exit code 2)
  - fix source files in `reports/outcome_events.jsonl` or `reports/weekly_pilot_kpis.csv`
- DB unavailable:
  - use `--allow-db-unavailable` to continue artifact pipeline
  - API proof-pack route will use file fallback with `meta.source=live_provider`
- Requested week missing in API route:
  - returns `weekly_proof_pack_unavailable` (`retryable=false`)
  - optionally retry with `allow_latest_fallback=true`

## Expected Artifacts
- `reports/weekly_pilot_kpis.csv`
- `reports/weekly_executive_proof_pack.md`

## Post-Run Spot Checks
1. Call `GET /api/v2/reports/weekly-proof-pack?tenant_id=<tenant_id>`
2. Confirm envelope shape and headers:
   - `data/meta/error`
   - `X-Response-Source`, `X-Data-Freshness`, `X-Correlation-Id`
