# Monday Zoom — Remaining Setup (~10 min total)

**Status as of Feb 20, 2026**: ALL 6 workflows created + published. All 4 workflow IDs in Railway.
**Zoom is now just: GitHub connect → API key → smoke test.**

---

## Workflows — ALL DONE ✅

| Workflow | Name | Tag | ID |
|----------|------|-----|----|
| 0 | Jorge — Seller Bot Trigger | `Needs Qualifying` | (no ID needed) |
| 00 | Jorge — Buyer Bot Trigger | `Buyer-Lead` | (no ID needed) |
| 1 | Jorge — Hot Seller Alert | `Hot-Seller` | `577d56c4-28af-4668-8d84-80f5db234f48` |
| 2 | Jorge — Warm Seller Nurture | `Warm-Seller` | `c8334775-e5d8-422f-bb92-62606663c659` |
| 3 | Jorge — Hot Buyer Alert | `Hot-Lead` | `2c405e58-5746-4e14-b038-2e3836fa74fd` |
| 4 | Jorge — Agent Notification | `Qualified` | `f3fc268b-5f16-4854-af28-200024cb3c8b` |

All 4 IDs set in Railway `sparkling-light` via CLI ✅

---

## Pre-Zoom (Cayman does before call)

- [ ] **Connect GitHub repo**: Railway dashboard → sparkling-light → Settings → Source → GitHub → ChunkyTortoise/EnterpriseHub → Deploy
  - This is the only blocker. Once connected, app auto-deploys and Railway sets DATABASE_URL + REDIS_URL.
- [ ] Confirm app is live: `curl https://sparkling-light.up.railway.app/health` → should return `{"status":"ok"}`
- [ ] **Verify phone numbers** in GHL: Automation → Workflows → Jorge — Hot Seller Alert + Jorge — Hot Buyer Alert → confirm "Send SMS" step has Jorge's real phone number

---

## Zoom: Two tasks (~10 min)

### Task 1: Jorge provides Anthropic API key (~2 min)

1. Jorge goes to **platform.anthropic.com** → API Keys → Create Key → copy
2. Cayman runs: `railway variables set ANTHROPIC_API_KEY=<paste key>`
3. Railway auto-redeploys (takes ~60 sec)

### Task 2: Smoke Test (~5 min)

1. GHL → Contacts → find or create a test contact (use Jorge's real phone)
2. Add tag `Needs Qualifying` → should receive seller bot text within 30 sec
3. Reply → confirm bot responds
4. Add tag `Hot-Seller` → confirm internal notification fires + Jorge's phone gets SMS
5. Check Railway logs: `railway logs` — no errors

---

## Also Needed (Jorge does separately, not Zoom)

| Item | Where | Why |
|------|-------|-----|
| **A2P 10DLC registration** | GHL → Settings → Phone Numbers → Register | Required for SMS delivery in US — without this, texts may not deliver |
| Phone number verification | In Workflow 1 + 3 (Hot Seller / Hot Buyer Alert) | Make sure "Send SMS" step has your real number — update if wrong |

---

## Already Done ✅

- All 22 GHL custom fields: mapped in `.env.jorge`
- Calendar: `CrqysY0FVTxatzEczl7h` (Zoom Call With Jorge Sales)
- Railway `sparkling-light`: 69 env vars set (65 + 4 workflow IDs), Postgres + Redis added
- All 6 GHL workflows: created + published (Feb 20)
- All 4 workflow IDs: set in Railway (Feb 20)
- All 3 bots: code-complete, tests passing
