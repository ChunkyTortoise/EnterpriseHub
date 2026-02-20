# Monday Zoom — Remaining Setup (~15 min total)

**Status as of Feb 20, 2026**: ALL 6 workflows created + published. Switching to Render (not Railway).
**Zoom is now: Render deploy → API key → webhook → smoke test.**

---

## Workflow IDs (ALL DONE ✅)

| Workflow | Tag | ID |
|----------|-----|----|
| Jorge — Hot Seller Alert | `Hot-Seller` | `577d56c4-28af-4668-8d84-80f5db234f48` |
| Jorge — Warm Seller Nurture | `Warm-Seller` | `c8334775-e5d8-422f-bb92-62606663c659` |
| Jorge — Hot Buyer Alert | `Hot-Lead` | `2c405e58-5746-4e14-b038-2e3836fa74fd` |
| Jorge — Agent Notification | `Qualified` | `f3fc268b-5f16-4854-af28-200024cb3c8b` |

---

## Pre-Zoom (Cayman does before call, ~20 min)

### 1. Deploy to Render

1. Go to **render.com** → New → Web Service
2. Connect GitHub → select `ChunkyTortoise/EnterpriseHub` → branch `main`
3. Set **Root Directory**: `ghl_real_estate_ai`
4. **Plan**: Starter ($7/mo) — do NOT use free (spins down after 15 min, bots won't respond)
5. Set **Build Command**: `pip install -r requirements.txt`
6. Set **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT --workers 1`
7. Click **Create Web Service**

> Alternatively: `render.yaml` in root already defines everything — Render may auto-detect it.

### 2. Add PostgreSQL + Redis in Render

1. Render Dashboard → **New** → **PostgreSQL** → name: `jorge-realty-db` → Plan: Starter → Create
2. Render Dashboard → **New** → **Redis** → name: `jorge-realty-redis` → Plan: Starter → Create
3. Go to jorge-realty-ai → **Environment** → confirm `DATABASE_URL` and `REDIS_URL` are auto-injected
   (If not, copy Internal Connection String from each service → paste manually)

### 3. Add env vars in Render dashboard

Go to **jorge-realty-ai → Environment → Add Environment Variable** for each:

```
# GHL (all values from .env.jorge)
GHL_API_KEY=eyJhbGci...          (full JWT from GHL)
GHL_LOCATION_ID=3xt4qayAh35BlDLaUv7P
LOCATION_ID=3xt4qayAh35BlDLaUv7P
GHL_WEBHOOK_SECRET=change-me-to-a-32-char-random-secret

# Bot config (already set in render.yaml, but double-check)
JORGE_SELLER_MODE=true
JORGE_BUYER_MODE=true
JORGE_LEAD_MODE=true

# GHL Workflow IDs
HOT_SELLER_WORKFLOW_ID=577d56c4-28af-4668-8d84-80f5db234f48
WARM_SELLER_WORKFLOW_ID=c8334775-e5d8-422f-bb92-62606663c659
HOT_BUYER_WORKFLOW_ID=2c405e58-5746-4e14-b038-2e3836fa74fd
NOTIFY_AGENT_WORKFLOW_ID=f3fc268b-5f16-4854-af28-200024cb3c8b

# Calendar
JORGE_CALENDAR_ID=CrqysY0FVTxatzEczl7h
JORGE_USER_ID=Or4ImSUxUarPJQyawA5W

# Digest email
JORGE_DIGEST_EMAIL=realtorjorgesalas@gmail.com

# JWT (generate a new one)
JWT_SECRET_KEY=<openssl rand -hex 32>

# Custom field IDs (get from .env.jorge — the 22 CUSTOM_FIELD_* values)
CUSTOM_FIELD_SELLER_TEMPERATURE=...
CUSTOM_FIELD_TIMELINE_URGENCY=...
CUSTOM_FIELD_BUYER_TEMPERATURE=...
CUSTOM_FIELD_BUDGET=...
CUSTOM_FIELD_LEAD_SCORE=...
# ... (all remaining from .env.jorge)
```

> **ANTHROPIC_API_KEY** — leave blank for now, Jorge provides on the call.

### 4. Update GHL Webhook URL

GHL → Settings → Integrations → Webhooks → update the webhook URL to:
```
https://jorge-realty-ai.onrender.com/api/webhooks/ghl
```

### 5. Verify the app is live

```bash
curl https://jorge-realty-ai.onrender.com/api/health/live
# Expected: {"status":"ok"}
```

### 6. Verify phone numbers in GHL workflows

GHL → Automation → Workflows → **Jorge — Hot Seller Alert** + **Jorge — Hot Buyer Alert**
→ confirm the "Send SMS" action has Jorge's real mobile number

---

## During Zoom (~10 min)

### Task 1: Add Anthropic API key (~2 min)

1. Jorge goes to **platform.anthropic.com** → API Keys → Create Key → copies it
2. Cayman: Render Dashboard → jorge-realty-ai → **Environment** → Add:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```
3. Render auto-redeploys (~90 sec) — watch deploy log

### Task 2: Smoke Test (~5 min)

1. GHL → Contacts → find or create a test contact (use Jorge's real phone)
2. Add tag **`Needs Qualifying`** → should receive seller bot text within 30 sec
3. Reply → confirm bot responds
4. Add tag **`Hot-Seller`** on same contact → confirm internal GHL notification fires

If all 3 things happen, system is live.

Check logs: Render Dashboard → jorge-realty-ai → **Logs** tab

---

## After the Call (Jorge does separately)

| Item | Where | Why |
|------|-------|-----|
| **A2P 10DLC registration** | GHL → Settings → Phone Numbers → Register | Required for SMS delivery in US — without this, texts may be blocked |
| Phone number verification | Workflows: Hot Seller Alert + Hot Buyer Alert | Confirm "Send SMS" step has Jorge's real number |

---

## Already Done ✅

- All 6 GHL workflows: created + published (Feb 20)
- All 22 GHL custom fields: mapped
- Calendar: `CrqysY0FVTxatzEczl7h` (Zoom Call With Jorge Sales)
- All 3 bots: code-complete, 243 tests passing
- Codebase: delivery audit clean (Feb 20)
- render.yaml: complete with PostgreSQL + Redis + all bot env vars
