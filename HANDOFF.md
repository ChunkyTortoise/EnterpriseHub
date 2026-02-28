# Jorge Bots — Handoff Guide

## Live Service
- **URL**: https://jorge-realty-ai-xxdf.onrender.com
- **Render Service**: srv-d6d5go15pdvs73fcjjq0
- **Latest Deploy**: sha-20ecaa2 (2026-02-28, status: live)
- **Plan**: Pro

## GHL Webhook Configuration
Set your GHL webhook URL to:
```
https://jorge-realty-ai-xxdf.onrender.com/api/ghl/webhook
```
The HMAC secret must match `GHL_WEBHOOK_SECRET` in your Render environment.

## How to Redeploy
Push to `main` branch → GitHub Actions builds Docker image → Render auto-deploys.
No manual steps needed. Takes ~3–5 minutes.

## Environment Variables
All 65 env vars are configured in the Render dashboard (srv-d6d5go15pdvs73fcjjq0).
Source of truth: `.env.jorge` (keep secure, do not commit).

## Bot Activation Tags (GHL)
| Tag | Bot Activated |
|-----|--------------|
| `Needs Qualifying` | Seller bot + Lead bot |
| `Buyer-Lead` | Buyer bot |
| `AI-Off` | Deactivates all bots |

## Calendar Booking
- Calendar ID: `CrqysY0FVTxatzEczl7h`
- Bot offers slots automatically when seller qualifies as HOT (FRS ≥ 70)
- Contact replies "1", "2", or "3" to book

## Known Limitations (not blockers)
- A/B tone variant **outcome data** resets on redeploy (assignment is stable — same contact always gets same tone)
- If server restarts mid-slot-offer, slots are re-offered on next message

## Agent Documentation
- Architecture: `CLAUDE.md` (repo root)
- Domain context: `.claude/reference/domain-context.md`
- Deployment guide: `ghl_real_estate_ai/agents/DEPLOYMENT_CHECKLIST.md`
- Agent personas: `AGENTS.md`

## Gate 5 — Manual Calendar Test (one-time)
1. SMS from test contact tagged `Needs Qualifying`: "Hi I want to sell my house"
2. Answer 4 seller questions (motivated, 30 days, move-in ready, $650k)
3. After turn 5: bot sends numbered slots ("Reply 1, 2, or 3")
4. Reply "1" → expect "You're all set!" booking confirmation
5. Verify appointment in GHL calendar + custom fields updated
