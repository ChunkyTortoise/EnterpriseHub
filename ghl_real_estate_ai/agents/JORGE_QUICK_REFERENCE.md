# Jorge Realty AI — Quick Reference Card
**Service**: jorge-realty-ai-xxdf.onrender.com · **Dashboard**: lyrio-jorge.streamlit.app

---

## Kill Switch — Stop ALL Bots Instantly

**In GHL → Contact record → Tags → Add tag:**

| Tag to Add | Effect |
|-----------|--------|
| `AI-Off` | All bots stop immediately |
| `Stop-Bot` | All bots stop immediately |

**To re-enable:** Remove the tag, add `Needs Qualifying` or `Buyer-Lead`

---

## Tag Cheat Sheet

### Tags YOU Control (add/remove manually)

| Tag | What It Does |
|-----|-------------|
| `Needs Qualifying` | Starts seller or lead bot |
| `Seller-Lead` | Same as Needs Qualifying — starts seller bot |
| `Buyer-Lead` | Starts buyer bot |
| `AI-Off` | Stops all bots |
| `Stop-Bot` | Stops all bots |

### Tags the Bot Applies Automatically (do not delete)

| Tag | Applied When |
|-----|-------------|
| `Hot-Seller` | Seller scored HOT (all 4 questions answered well) |
| `Warm-Seller` | Seller partially qualified |
| `Cold-Seller` | Seller unresponsive or not motivated |
| `Hot-Lead` | Lead score ≥ 80 |
| `Warm-Lead` | Lead score 40–79 |
| `Cold-Lead` | Lead score < 40 |
| `Seller-Qualified` | Seller bot finished |
| `Qualified` | Any bot finished |
| `TCPA-Opt-Out` | Contact replied STOP / unsubscribe |
| `Compliance-Alert` | Message blocked — fair housing concern |
| `Human-Escalation-Needed` | Bot couldn't continue — needs human |

---

## What Each Bot Does

| Bot | Activated By | Questions Asked |
|-----|-------------|----------------|
| **Lead Bot** | Any new inbound message | Figures out buyer vs. seller, routes to right bot |
| **Seller Bot** | `Needs Qualifying` tag | Motivation · Timeline · Property condition · Price expectation |
| **Buyer Bot** | `Buyer-Lead` tag | Budget · Pre-approval · Property preferences · Timeline |

---

## HOT Lead Criteria

**Seller HOT** = all 4 questions answered + strong motivation + timeline ≤ 6 months
→ Bot offers calendar slots automatically

**Buyer HOT** (score ≥ 75) = pre-approved + budget $500K+ + wants to buy within 90 days

---

## Costs (Monthly Estimates)

| Item | Cost |
|------|------|
| Render hosting | ~$7/month |
| Claude AI (per lead) | ~$0.01–0.05 |
| Typical month (100 leads) | ~$8–12 total |
| Dashboard (Streamlit Cloud) | Free |

---

## Monthly Maintenance Checklist

- [ ] Lyrio dashboard → check bot response counts
- [ ] GHL → Conversations → scan for `Human-Escalation-Needed` contacts
- [ ] GHL → Contacts → filter `TCPA-Opt-Out` → confirm opted-out list is current
- [ ] Check Render dashboard — service should show "Live" (green)
- [ ] Review 1–2 HOT lead conversations for quality
- [ ] If calendar booking stopped working → check GHL calendar has open slots

---

## Service URLs

| Service | URL |
|---------|-----|
| Render (hosting) | dashboard.render.com → jorge-realty-ai |
| GHL CRM | app.gohighlevel.com |
| Lyrio Dashboard | lyrio-jorge.streamlit.app |
| Inbound webhook | jorge-realty-ai-xxdf.onrender.com/api/ghl/webhook |
| Tag webhook | jorge-realty-ai-xxdf.onrender.com/api/ghl/tag-webhook |

---

## When Something Looks Wrong

| Symptom | First Check |
|---------|------------|
| Bot not responding | Render → Events → Is service Live? |
| Bot responding to wrong contacts | GHL → Contact → check tags |
| Calendar not booking | GHL → Calendars → check available slots exist |
| `Human-Escalation-Needed` on many contacts | Call Cayman — may need bot tuning |
| Contact wants human now | Add `AI-Off` tag, respond manually |
| Bots stopped responding | Check Anthropic credits at console.anthropic.com — top up if < $10 |

---

*Prepared by Cayman Roden · February 2026 · For full system details see JORGE_MASTER_GUIDE.pdf*
