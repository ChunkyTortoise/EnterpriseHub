# Client Showcase Runbook (EnterpriseHub)

Date: February 10, 2026
Repo: `/Users/cave/Documents/New project/enterprisehub`

## 1. Startup Commands

```bash
cd /Users/cave/Documents/New\ project/enterprisehub

# Streamlit showcase
python3 -m streamlit run streamlit_cloud/app.py --server.headless=true --server.port=8765

# Enterprise UI (new terminal)
cd enterprise-ui
npm install
npm run dev
```

Expected URLs:
- Streamlit showcase: `http://localhost:8765`
- Enterprise UI: `http://localhost:3000`

## 2. Recommended Demo Flow (10 Minutes)

1. Minute 0-2: Streamlit `Client Showcase` tab
   - Pick scenario.
   - Anchor pain point and SLA gap.
2. Minute 2-5: Streamlit KPI cards
   - Revenue uplift, conversion lift, extra closings, payback period.
3. Minute 5-7: Enterprise UI `/agents`
   - Show agent status + recent handoffs.
4. Minute 7-8: Enterprise UI `/journeys`
   - Show journey throughput and progression.
5. Minute 8-9: Enterprise UI `/concierge`
   - Send one message and read generated recommendation.
6. Minute 9-10: Enterprise UI `/properties`
   - Show analysis queue and valuation context.

## 3. Fallback Path (Backend Unavailable)

- `enterprise-ui` API clients automatically switch to embedded demo fallback data if endpoint calls fail or payload shape is invalid.
- Demo fallback still supports all showcase routes: `/`, `/agents`, `/journeys`, `/concierge`, `/properties`.
- Keep `NEXT_PUBLIC_ENTERPRISE_API_BASE_URL` set to expected backend URL; fallback engages without extra toggles.

## 4. Troubleshooting Quick Reference

1. Port conflict (`3000` or `8765` in use)
   ```bash
   lsof -i :3000
   lsof -i :8765
   ```

2. Missing Node dependencies in `enterprise-ui`
   ```bash
   cd /Users/cave/Documents/New\ project/enterprisehub/enterprise-ui
   rm -rf node_modules package-lock.json
   npm install
   ```

3. Streamlit import/runtime failure
   ```bash
   cd /Users/cave/Documents/New\ project/enterprisehub
   python3 -m py_compile streamlit_cloud/app.py
   ```

4. API unavailable or 5xx errors
   - Continue the demo; `enterprise-ui` route pages should display seeded fallback data.

5. Frontend build/lint failure
   ```bash
   cd /Users/cave/Documents/New\ project/enterprisehub/enterprise-ui
   npm run lint
   npm run build
   npm run test
   ```

## 5. Smoke Verification Checklist

```bash
cd /Users/cave/Documents/New\ project/enterprisehub
ruff check streamlit_cloud/app.py
python3 -m py_compile streamlit_cloud/app.py
pytest -q tests/test_app_structure.py

cd enterprise-ui
npm run lint
npm run test
npm run build
```
