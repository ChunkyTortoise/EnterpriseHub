# Jorge Bots Deployment Package

Production-focused lead and seller bot package for GoHighLevel workflows.

## Scope
This README is for `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package` only.

## Included Components
- `jorge_fastapi_lead_bot.py`: lead analysis API, webhook intake, telemetry endpoints.
- `jorge_webhook_server.py`: secondary webhook server.
- `jorge_lead_bot.py`: lead bot orchestration.
- `jorge_seller_bot.py`: seller bot orchestration.
- `jorge_engines.py` and `jorge_engines_optimized.py`: qualification engines.
- `ghl_client.py`: GoHighLevel API client.
- `conversation_manager.py`: file-backed context persistence.
- `jorge_claude_intelligence.py`: hybrid pattern + Claude lead analysis.
- `jorge_kpi_dashboard.py`: Streamlit dashboard.

## Prerequisites
- Python 3.10+
- pip
- Optional: virtualenv

## Required Environment Variables
Create `.env` in this directory:

```env
GHL_ACCESS_TOKEN=your_ghl_access_token
CLAUDE_API_KEY=your_claude_api_key
GHL_LOCATION_ID=your_ghl_location_id

# Optional but recommended
GHL_WEBHOOK_SECRET=your_webhook_secret
GHL_WEBHOOK_IDEMPOTENCY_TTL_SECONDS=86400
TESTING_MODE=false
DEBUG_MODE=false
```

## Verified Startup Path
1. Create environment and install dependencies.
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the lead API.
```bash
uvicorn jorge_fastapi_lead_bot:app --host 0.0.0.0 --port 8001 --reload
```

3. Run the dashboard (optional).
```bash
streamlit run jorge_kpi_dashboard.py --server.port 8501
```

4. Run tests.
```bash
pytest -c pytest.ini
python3 test_standalone.py
```

## API Endpoints
- `GET /health`: dependency and runtime health.
- `GET /performance`: operational performance summary.
- `GET /metrics`: machine-readable runtime metrics.
- `POST /analyze-lead`: lead scoring and response recommendation.
- `POST /webhook/ghl`: signed GHL webhook intake with idempotency.

## Workstream G Flags (Growth Rollout)
All growth behavior is default-off and canary compatible.

```env
FF_GROWTH_LEAD_SOURCE_ATTRIBUTION_ENABLED=false
FF_GROWTH_ADAPTIVE_FOLLOWUP_TIMING_ENABLED=false
FF_GROWTH_AB_RESPONSE_STYLE_TESTING_ENABLED=false
FF_GROWTH_SLA_HANDOFF_THRESHOLDS_ENABLED=false
FF_GROWTH_CANARY_MODE_ENABLED=false
FF_GROWTH_CANARY_SOURCE=
FF_GROWTH_LEAD_SOURCE_WRITEBACK_ENABLED=false
FF_GROWTH_CONVERSION_FEEDBACK_WRITEBACK_ENABLED=false
```

Implemented in this package:
- Feature 1: lead-source attribution + conversion feedback metadata.
- Feature 2: adaptive follow-up timing.
- Feature 3: deterministic A/B response style assignment (`contact_id + lead_source` bucketing).
- Feature 4: SLA-based handoff recommendation + optional `Needs-Handoff-SLA` tagging path.

## Troubleshooting
### 403 on `/webhook/ghl` (signature failures)
- Confirm `GHL_WEBHOOK_SECRET` matches the signing secret configured in GHL.
- Confirm the webhook includes `X-GHL-Signature`.
- If debugging locally, set `TESTING_MODE=true` to avoid production fail-closed behavior.

### GHL auth/operation failures
- Verify `GHL_ACCESS_TOKEN` is valid and not expired.
- Verify token scopes allow contacts, tags, and messaging updates.
- Check API logs for `ghl_request` entries and status codes.

### Missing environment variable errors
- Ensure required vars are present in `.env`.
- Confirm your shell session loads `.env` in this directory.
- For local test-only runs, set `TESTING_MODE=true`.

## Known Limitations (v1.1)
- Storage is file-backed (`data/`) and not distributed-safe across multiple replicas.
- Webhook idempotency store is local-file based; use shared storage for multi-instance deployments.
- `/metrics` is JSON output for this phase, not Prometheus exposition format.

## Rollout and Backout
Rollout:
1. Deploy with all `FF_GROWTH_*` flags set to `false`.
2. Enable `FF_GROWTH_CANARY_MODE_ENABLED=true` and set one `FF_GROWTH_CANARY_SOURCE`.
3. Enable one feature at a time:
   - `FF_GROWTH_AB_RESPONSE_STYLE_TESTING_ENABLED`
   - `FF_GROWTH_SLA_HANDOFF_THRESHOLDS_ENABLED`
4. Observe `/metrics` growth counters for at least 24h before broader rollout.

Backout:
1. Disable the specific feature flag first (immediate behavior rollback).
2. Disable writeback toggles second if operational propagation must stop.
3. Keep telemetry enabled for postmortem and recovery analysis.

## Operational Notes
- Webhook idempotency file: `data/webhook_idempotency.json`
- Conversation context files: `data/conversations/*.json`
- Package test configuration: `pytest.ini`
