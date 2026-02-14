# AgentBridge Interview Showcase

A runnable showcase asset for your interviews: multilingual message handling, deterministic task routing, tenant isolation, cross-bot handoff guardrails, and live metrics.

## What This Demonstrates

- Multi-tenant safety with cross-tenant access blocking
- Deterministic routing to `calendar`, `email`, `research`, `reminder`, `general`
- Multilingual detection for English, Spanish, French, Hebrew
- Cross-bot handoff with circular-loop prevention
- Approval workflow for high-risk send/schedule actions
- Cache hit-rate and latency metrics with cost-savings estimate
- One-command local startup with Docker Compose

## Quick Start

```bash
cd interview_showcase
docker compose up --build
```

Open:
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- UI: [http://localhost:8501](http://localhost:8501)

## Demo Flow

### Scenario A (Kialash Focus)

1. In UI sidebar, keep tenant `tenant-alpha`.
2. Click `Run Kialash Scenario`.
3. Show:
- language detection (`es` from Spanish input)
- handoff events in `Events`
- circular prevention event on reverse handoff
- metrics in `Metrics` tab

### Scenario B (Chase Focus)

1. Click `Run Chase Scenario`.
2. Show deterministic routing for email/calendar/reminder actions.
3. Send a scheduling/email action and show it enters the approval queue.
4. Approve it in the `Approvals` tab and show auditable decision history.
5. Show cache hits on repeated requests and cost savings in metrics.

### Safety Proof

Use `Simulate Cross-Tenant Block` in `Live Demo` and show blocked request.

## API Endpoints

- `GET /health`
- `POST /v1/demo/message`
- `POST /v1/demo/scenario/{kialash|chase}`
- `GET /v1/events?tenant_id=...`
- `GET /v1/approvals?tenant_id=...&status=pending`
- `POST /v1/approvals/{approval_id}/decision`
- `GET /v1/metrics`

## Local Dev and Tests

```bash
cd interview_showcase
python -m venv .venv
source .venv/bin/activate
pip install -r api/requirements.txt -r ui/requirements.txt -r tests/requirements.txt
pytest -q tests
uvicorn main:app --app-dir api --reload --port 8000
streamlit run ui/app.py
```

## Project Structure

```text
interview_showcase/
  api/
    main.py
    requirements.txt
    Dockerfile
  ui/
    app.py
    requirements.txt
    Dockerfile
  tests/
    test_api.py
    requirements.txt
  docker-compose.yml
  README.md
```

## Notes

- Redis is used for cache if available; API falls back to in-memory cache automatically.
- This asset is intentionally local-first and deterministic for reliable interview demos.
- The UI includes a `Presenter Script` tab with exact narration prompts for both interviews.
