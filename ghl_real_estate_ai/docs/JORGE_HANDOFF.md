# Jorge Bot — Client Handoff Summary

> One-page status brief for client presentation / Zoom follow-up.
> Updated: March 2026

---

## What Is Live

| Item | Status | Detail |
|------|--------|--------|
| **Bot server** | ✅ Live | `https://jorge-realty-ai-xxdf.onrender.com` (Render web service) |
| **Seller Bot** | ✅ Complete | 4-question qualification → hot/warm/cold routing → agent handoff |
| **Buyer Bot** | ✅ Complete | Financial readiness → property preferences → appointment booking |
| **Lead Bot** | ✅ Complete | Temperature scoring → multi-day follow-up sequences → cross-bot handoff |
| **GHL Webhook** | ✅ Active | Inbound message → bot dispatch → tag/field updates in real time |
| **Compliance pipeline** | ✅ Active | TCPA opt-out, FHA/Fair Housing, CA SB 243 AI disclosure, SMS 320-char cap |
| **Test coverage** | ✅ Green | 205+ passing tests; zero regressions since Feb 2026 release |

---

## What You (the Client) Still Need to Do

### 1. A2P 10DLC Registration — CRITICAL for SMS delivery

Without this, carriers block all outbound SMS. Fines up to $10,000/violation.

**Steps:**
1. Log into GHL → **Settings → Phone Numbers → A2P Registration**
2. Register your **brand** (business name + EIN)
3. Register your **campaign** — use case: *"Real estate lead qualification"*
   - Sample messages must include opt-out language: *"Reply STOP to opt out"*
4. Wait for TCR approval (1–5 business days)
5. Confirm status shows **Active** before enabling live traffic

**Resource:** [GHL A2P Guide](https://support.gohighlevel.com/support/solutions/articles/48000985491) | [TCR Portal](https://csp.campaignregistry.com/)

---

### 2. Anthropic API Credits Top-Up

Jorge uses Claude (via Anthropic API) for every AI response.

- **Check usage:** [console.anthropic.com](https://console.anthropic.com) → Usage & Billing
- **Add credits:** Billing → Add Credits (prepaid) or set a monthly spending limit
- **Recommended buffer:** Keep at least $20–$50 of credits; a busy lead day can use $3–$8

If credits run out, the bot falls back to a canned "I'll have a team member follow up" message — no crash, but no AI responses.

---

## How to Verify It Is Working

### Quick smoke test (curl)
```bash
# 1. Health check
curl https://jorge-realty-ai-xxdf.onrender.com/health
# Expected: {"status":"healthy","version":"..."}

# 2. Seller bot test (no GHL account needed)
curl -X POST https://jorge-realty-ai-xxdf.onrender.com/test/seller \
  -H "Content-Type: application/json" \
  -d '{"message":"Hi I want to sell my house","contact_id":"test-1","reset":true}'
# Expected: JSON with "message" (bot reply) and "response_type":"address_capture"
```

### GHL webhook verification
1. In GHL, go to **Settings → Webhooks**
2. Confirm the webhook URL is set: `https://jorge-realty-ai-xxdf.onrender.com/webhook/ghl`
3. Send a test lead message to a contact tagged **"Needs Qualifying"**
4. Verify the bot replies within 5–10 seconds and the GHL contact's custom fields update

### What a healthy conversation looks like
| Turn | Bot asks | Seller answers |
|------|----------|----------------|
| T1 | "What's the property address?" | "123 Main St, Rancho Cucamonga" |
| T2 | "Why are you looking to sell?" | "Relocating for work" |
| T3 | "Could you work with a 30–45 day close?" | "Yes that works" |
| T4 | "What condition is the property in?" | "Move-in ready" |
| T5 | "What price are you hoping for?" | "$580k" |
| T6 | Bot: HOT → routes to agent, books call | — |

---

## Key Contacts

| Role | Name | Contact |
|------|------|---------|
| Developer / On-call | Cayman Roden | cayman@example.com |
| GHL Account Admin | — | (your GHL login) |
| Anthropic billing | — | console.anthropic.com |
| Render dashboard | — | dashboard.render.com |

---

## Quick Reference — Bot Tags

| GHL Tag | Meaning |
|---------|---------|
| `Needs Qualifying` | Activates Seller/Lead bot |
| `Buyer-Lead` | Activates Buyer bot |
| `Hot-Seller` / `Warm-Seller` / `Cold-Seller` | Seller temperature result |
| `AI-Off` | Bot deactivated (TCPA opt-out or manual stop) |
| `Seller-Qualified` | Seller flow complete — hand off to human |
| `TCPA-Opt-Out` | User sent STOP — no further AI messages |

---

*Full documentation: `ghl_real_estate_ai/docs/` · Deployment checklist: `JORGE_BOT_DEPLOYMENT_CHECKLIST.md` · On-call runbook: `JORGE_BOT_ON_CALL_RUNBOOK.md`*
