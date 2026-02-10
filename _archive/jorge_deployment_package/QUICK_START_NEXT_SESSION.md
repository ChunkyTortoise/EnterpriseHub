# Quick Start (Verified)

Use this to resume work quickly in this package.

## Current Status
- Phase 1 (A-C): complete.
- Phase 2 (D-F): complete.
- Phase 3 (Workstream G): complete (Features 1-4 behind flags/canary).

## 1) Open Project
```bash
cd /Users/cave/Documents/New\ project/enterprisehub/jorge_deployment_package
```

## 2) Activate Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3) Configure Environment
Create `.env` with at least:
```env
GHL_ACCESS_TOKEN=your_ghl_access_token
CLAUDE_API_KEY=your_claude_api_key
GHL_LOCATION_ID=your_ghl_location_id
GHL_WEBHOOK_SECRET=your_webhook_secret
```

## 4) Run Core Service
```bash
uvicorn jorge_fastapi_lead_bot:app --host 0.0.0.0 --port 8001 --reload
```

## 5) Optional Local Interfaces
- Dashboard (optional):
```bash
streamlit run jorge_kpi_dashboard.py --server.port 8501
```
- Secondary webhook server (optional):
```bash
uvicorn jorge_webhook_server:app --host 0.0.0.0 --port 8000 --reload
```

## 6) Validate
```bash
pytest -c pytest.ini
python3 test_standalone.py
```

## 7) Useful Endpoints
- `http://localhost:8001/health`
- `http://localhost:8001/performance`
- `http://localhost:8001/metrics`
- `http://localhost:8001/docs`

## 8) Growth Rollout Toggle Reference
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
