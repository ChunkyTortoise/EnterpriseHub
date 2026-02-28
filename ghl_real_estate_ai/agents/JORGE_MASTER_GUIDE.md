# Jorge Realty AI — Master System Guide
**Prepared by:** Cayman Roden · **Date:** February 2026 · **System:** jorge-realty-ai-xxdf.onrender.com
**Status:** 3 active bots · 24/7 · ~$15/month AI cost · 484/484 tests passing

---

## Part 1 — The Big Picture

### What the System Does

When a lead texts Jorge's number, an AI bot handles the entire first conversation — qualifying them, scoring their motivation, and booking appointments with the hot ones. Jorge only gets notified about leads worth his time.

1. **Lead texts Jorge's number** via SMS
2. **Bot responds automatically** — asks qualifying questions in Jorge's voice
3. **Bot scores the lead** — HOT, Warm, or Cold based on answers
4. **HOT leads** → bot offers calendar slots → appointment booked automatically
5. **Jorge gets notified** — "HOT SELLER, call ASAP" — only the ones worth calling

### The Three Bots

| Bot | Trigger | What It Does |
|-----|---------|-------------|
| **Lead Bot** | Any new inbound message | First contact — introduces itself, figures out if they're a buyer or seller, and routes to the right bot |
| **Seller Bot** | `Needs Qualifying` tag | Asks 4 key questions: motivation, timeline, property condition, and price expectation. Classifies as HOT, Warm, or Cold. Books calendar if HOT |
| **Buyer Bot** | `Buyer-Lead` tag | Asks about budget, pre-approval status, property preferences, and timeline. Notifies Jorge when a buyer is pre-approved and ready |

### The 3 Websites Involved

| Site | Purpose | URL |
|------|---------|-----|
| **GoHighLevel (GHL)** | The CRM — contacts, conversations, tags, workflows, calendar | app.gohighlevel.com |
| **Bot API (Render)** | Where the bot code lives and runs — the "brain" of the system | jorge-realty-ai-xxdf.onrender.com |
| **Lyrio Dashboard** | Live monitoring — lead counts, bot activity, cost tracker, AI chat | lyrio-jorge.streamlit.app |

### Account Ownership

Your system runs across 5 platforms. You already own two. To be fully independent, the remaining three need to transfer to your accounts.

| Platform | What It Holds | Current Owner | Your Action |
|----------|--------------|---------------|-------------|
| GoHighLevel | CRM, contacts, workflows, calendar | ✅ You | Nothing needed |
| Render | Live bot server — runs 24/7 | ✅ You | Nothing needed |
| GitHub | Bot source code | Developer account | Ask developer to transfer repo to your GitHub account |
| Docker Hub | Packaged bot app — what Render deploys | Developer account | Ask developer to rebuild image under your Docker Hub account |
| Streamlit | Lyrio dashboard | Developer account | Ask developer to redeploy dashboard under your Streamlit account |

> Until GitHub, Docker Hub, and Streamlit are under your name, you can't redeploy the bots or update the dashboard without the developer. Creating the 3 accounts takes 10 minutes. The transfer takes about 1–2 hours of developer time.

---

## Part 2 — GoHighLevel Walkthrough

### 2.1 Contacts

Every lead is a **Contact**. Each has: name, phone, email, **tags**, and **custom fields**. Tags control which bot runs. Custom fields store what the bot learned.

- **Where to find:** Contacts tab → search by name or phone
- **To edit manually:** Click contact → edit fields, add/remove tags

### 2.2 Conversations

- All SMS back-and-forth lives here — every bot message and every reply
- **Where to find:** Conversations tab (left sidebar)
- **To stop the bot:** Add tag `AI-Off` or `Stop-Bot` → stops immediately

### 2.3 Tags — The On/Off Switches

Tags control which bot runs and what happens next. Full reference in [Section 10](#section-10--complete-tag-reference).

**Tags you add manually to start or stop a bot:**

| Tag | What It Does |
|-----|-------------|
| `Needs Qualifying` | Activates the Lead/Seller bot |
| `Seller-Lead` | Also activates the Seller bot (same effect as Needs Qualifying) |
| `Buyer-Lead` | Activates the Buyer bot |
| `AI-Off` | Turns off ALL bots for this contact immediately |
| `Stop-Bot` | Same as AI-Off |

**Tags the bot applies automatically:**

| Tag | When It's Applied |
|-----|-----------------|
| `Hot-Seller` | Seller answers all 4 questions with quality responses → triggers HOT workflow |
| `Warm-Seller` | Seller gives partial answers → triggers nurture drip |
| `Cold-Seller` | Seller unresponsive or too vague → long-term follow-up |
| `Hot-Lead` | Lead score ≥ 80 → priority workflow + agent notification |
| `Warm-Lead` | Lead score 40–79 → nurture sequence |
| `Cold-Lead` | Lead score < 40 → educational content, periodic check-in |
| `Seller-Qualified` | Seller bot finished — won't restart on next message |
| `Qualified` | Qualification complete (any bot) — deactivates further bot processing |
| `TCPA-Opt-Out` | Lead replied STOP/unsubscribe — bot never texts them again |
| `Compliance-Alert` | Bot detected an FHA/RESPA violation attempt — blocked and flagged |
| `Human-Escalation-Needed` | Bot exhausted all automated repair strategies — needs Jorge |

### 2.5 Workflows (Automation) — Quick Summary

| # | Workflow | What It Does |
|---|---------|-------------|
| 1 | Hot Seller | Answers all 4 Qs → SMS + email to Jorge: "HOT SELLER, call ASAP" |
| 2 | Warm Seller | Partial qualification → nurture drip over days/weeks |
| 3 | Hot Buyer | Pre-approved, budget captured → notifies Jorge to schedule showing |
| 4 | Warm Buyer | Partial buyer qualification → nurture sequence |
| 5 | Manual Scheduling Fallback | Calendar booking fails → asks for morning/afternoon preference |

### 2.6 Calendar

- "Zoom Call With Jorge Sales" is what the bot books into — **Calendars tab**
- Set Jorge's available hours here — bot only offers slots within those hours
- Calendar ID: `CrqysY0FVTxatzEczl7h`

### 2.8 Webhook

```
https://jorge-realty-ai-xxdf.onrender.com/api/ghl/webhook
Events: Inbound Message · Contact Tag Added
```

---

## Part 3 — How the Bot Works

### 3.1 The Full Message Flow

1. Lead texts Jorge's number
2. GHL receives it → fires webhook to the bot URL
3. Bot receives contact ID, message text, and current tags
4. Bot routes to the right bot based on tags
5. Claude AI generates a response in Jorge's voice
6. Response passes 5 quality checks: language, opt-out, Fair Housing, AI disclosure, SMS length
7. Bot sends reply through GHL → lead gets the SMS
8. Bot updates contact's custom fields in GHL
9. If HOT → triggers Hot Seller/Buyer workflow → Jorge notified

### 3.2 The 4 Seller Questions

| # | Topic | Example Prompt |
|---|-------|---------------|
| 1 | Motivation | "What's making you consider selling?" |
| 2 | Timeline | "When are you looking to make a move?" |
| 3 | Property Condition | "What condition is the house in?" |
| 4 | Price Expectation | "What number would you need to walk away happy?" |

| Classification | Criteria | What Happens Next |
|---------------|----------|------------------|
| 🔴 **HOT** | All 4 answered meaningfully | Bot offers calendar → books appointment → notifies Jorge |
| 🟡 **WARM** | Partial answers | Nurture drip (follow-up texts over days/weeks) |
| 🔵 **COLD** | Unresponsive or vague | Long-term follow-up sequence |

### 3.4 Safety Features

| Feature | How It Works |
|---------|-------------|
| **TCPA Compliance** | Lead texts STOP → bot stops immediately, `TCPA-Opt-Out` tag applied, never texts again |
| **Fair Housing Compliance** | Bot won't say anything violating FHA or RESPA |
| **AI Disclosure (CA SB 243)** | Every message includes `[AI-assisted message]` footer |
| **Duplicate + Lock Protection** | Second webhook ignored; per-contact lock prevents simultaneous responses |

---

## Part 4 — Render Hosting

| Service | Status | URL |
|---------|--------|-----|
| jorge-realty-ai-xxdf | ● ACTIVE · sha-20ecaa2 | jorge-realty-ai-xxdf.onrender.com |
| jorge-realty-ai | ● Older — not in use | jorge-realty-ai.onrender.com |

### 4.1 Key Environment Variables

| Variable | What It Controls |
|----------|-----------------|
| `GHL_API_KEY` | Jorge's GHL access key |
| `ANTHROPIC_API_KEY` | Claude AI key — uses credits (top up at console.anthropic.com) |
| `HOT_SELLER_WORKFLOW_ID` | Which GHL workflow fires for hot sellers |
| `JORGE_CALENDAR_ID` | Which calendar the bot books into |
| `JORGE_SELLER_MODE` | `true` / `false` — toggle seller bot on/off without code changes |

> **Most common issue:** Anthropic API credits ran out. Fix: top up at console.anthropic.com — takes 2 minutes.

---

## Part 5 — Lyrio Dashboard

**URL:** lyrio-jorge.streamlit.app

| Page | What It Shows |
|------|-------------|
| **Concierge Chat** | Ask Claude AI: "How many hot leads this week?" — uses your real data |
| **Bot Command Center** | Live activity, lead counts by temperature, conversation reset |
| **Cost & ROI Tracker** | AI API cost vs. deal value generated from bot-qualified leads |
| **Lead Activity Feed** | Recent conversations and qualification events in real time |

**Reset a conversation:** Lyrio → Bot Command Center → enter contact ID → Reset Conversation. Clears all memory; next message starts fresh.

---

## Part 6 — How to Make Changes

### Self-Service (No Developer)

**In GHL:**
- Edit workflow steps and message text
- Add/remove tags from contacts
- Modify calendar availability
- Create new custom fields
- Edit pipeline stages

**Via Render Env Vars:**
- Toggle bots: `JORGE_SELLER_MODE=false`
- Switch to 10-question mode: `JORGE_SIMPLE_MODE=false`
- Adjust thresholds: `HOT_SELLER_THRESHOLD`
- Swap workflow ID to update hot-lead trigger

### Requires Developer

- Change bot questions or phrasing
- Adjust what counts as "hot"
- Add new bot logic or a new bot type
- Integrate a third-party service
- Logic changes / new integrations / qualification thresholds

### Emergency Kill Switch

| Scope | How |
|-------|-----|
| **One contact** | Add tag `AI-Off` in GHL → that person's bot stops instantly |
| **System-wide** | Set `JORGE_SELLER_MODE=false` + `JORGE_BUYER_MODE=false` + `JORGE_LEAD_MODE=false` in Render → all bots pause, no messages processed until flipped back to `true` |

---

## Part 7 — Common Q&A

**How does the bot know when to stop texting?**
After 30 days of no response (sequence ends), when lead replies STOP, when classified HOT and appointment booked, or when `AI-Off` / `Seller-Qualified` tag added.

**Can the bot handle Spanish?**
Yes — detects the lead's language automatically and responds in kind. No setup required.

**What if the bot says something wrong?**
Add `AI-Off` to that contact immediately. Can delete/edit the message in GHL Conversations. Report for a code fix — ~1 business day.

**How do I know who's a hot lead right now?**
GHL → Contacts → filter by `Hot-Seller` or `Hot-Lead` tag. Or check Lyrio Dashboard → Bot Command Center.

**Can I change what the bot says?**
Phrasing changes require a developer. Tone is tuned to Jorge's voice ("Let me be straight with you..."). Major changes ~1 day to test and deploy.

**What does the bot cost to run?**
~$0.03 per response. At 100 active leads/month = $3–15/month AI costs + ~$7/month Render hosting. Under $25/month total.

**What's A2P 10DLC?**
Carrier registration requirement for business SMS. Without it, texts get blocked. Already registered and active as of February 2026.

**What if the bot doesn't respond?**
Check Render → Logs tab. Most common cause: Anthropic API credits ran out → top up at console.anthropic.com in 2 minutes.

---

## Part 8 — Live Demo Script

1. Open GHL → Contacts → find a test contact (or create one)
2. Add tag `Needs Qualifying` to the contact
3. Send inbound SMS: *"Hi I'm thinking about selling my house"*
4. Watch Render Logs — see **"webhook received"** within 1 second
5. Wait 3–5 seconds → bot reply appears in GHL Conversations
6. Answer the 4 questions naturally through the conversation
7. After 4 answers → `Hot-Seller` tag appears on the contact automatically
8. Calendar slot options appear in the SMS conversation
9. Reply "1" → confirm appointment in GHL Calendars tab

---

## Part 9 — Delivery Status

### System Gates

| Gate | What Was Tested | Result |
|------|----------------|--------|
| Gate 1 — Deploy | Health endpoint, server live | ✅ PASSED · sha-20ecaa2 |
| Gate 2 — Unit Tests | Full automated test suite | ✅ PASSED · 484/484 |
| Gate 3 — Smoke Test | Live webhook, HMAC verified | ✅ PASSED · 4/4 |
| Gate 4 — Full Live Eval | 18 phases, real HTTP calls to production | ✅ PASSED · 478/478 |
| Gate 5 — Phone Test | Real SMS → HOT → calendar booked | ⏳ Jorge performs this (below) |

**Gate 4 confirmed on your live system:** Prompt injection blocked · Fair Housing compliance active · STOP/opt-out handled · Calendar slot offer working · Cross-contact isolation verified · SQL injection rejected · Spanish input handled · 478 of 478 checks green.

### Gate 5 — Manual Phone Test Script

One test remaining: send a real SMS through your GHL number to confirm the full calendar booking loop end-to-end. Takes about 5 minutes.

| Step | Send This | Expected Response |
|------|-----------|------------------|
| 1 | `Hi I want to sell my house` | Bot asks for property address |
| 2 | [any address] | "Would 30–45 days work for you?" |
| 3 | `Yes, relocating for work` | Q3: property condition |
| 4 | `Move-in ready` | Q4: price expectation |
| 5 | `$650,000` | 🔴 HOT — numbered calendar slots appear |
| 6 | `1` | "You're all set!" — appointment booked in GHL Calendars |

**Verify after step 6:** GHL → Calendars → "Zoom Call With Jorge Sales" → new appointment appears. GHL → Contacts → test contact → tags include `Hot-Seller` and `Seller-Qualified`. You should also receive the SMS/email via your Hot Seller workflow.

### Current Live Configuration

| | |
|-|-|
| **URL** | jorge-realty-ai-xxdf.onrender.com |
| **Deploy** | sha-20ecaa2 |
| **Plan** | Render Pro (always on) |
| **Health** | /api/health/live → 200 OK |
| **Calendar ID** | CrqysY0FVTxatzEczl7h |
| **Calendar behavior** | Bot offers 3 real slots when seller goes HOT. Contact replies 1, 2, or 3 to book. Appointment appears in GHL Calendars tab |

> **Known limitation (not a blocker):** If the server restarts while waiting for a contact to pick a slot, the slots are re-offered on the next message. This is cosmetic only — the bot recovers automatically.

---

## Workflow Directory

### Jorge Bots Folder

| Workflow | What It Does |
|----------|-------------|
| **Jorge AI Bot - Inbound Message Handler** | Entry point for all inbound SMS. Validates GHL webhook signature, identifies contact, routes message to the correct active bot (seller/buyer/lead), returns AI response |
| **Jorge — Bot Activation** | Fires when `Needs Qualifying`, `Seller-Lead`, or `Buyer-Lead` tag is added. Calls the tag-webhook to activate the appropriate bot (seller or buyer) on that contact. Consolidated from the former Seller Bot Trigger + Buyer Bot Trigger (Feb 2026) |
| **Jorge — Hot Seller Alert** | Fires when a seller reaches HOT temperature. Notifies Jorge via SMS/email, enrolls in the hot seller handoff sequence |
| **Jorge — Warm Seller Nurture** | Fires on Warm-Seller classification. Enrolls contact in the warm nurture drip — periodic check-ins to keep engagement without pushing |
| **Jorge — Hot Buyer Alert** | Fires when a buyer hits HOT score. Triggers immediate agent notification with lead details and recommended next step |
| **Jorge — Warm Buyer Nurture** | Fires on Warm-Buyer classification. Enrolls in nurture sequence — property match updates, market education, drip SMS |
| **Jorge — Agent Notification** | Sends Jorge a structured SMS with lead summary when any bot classifies a contact as hot or ready for human handoff |
| **Jorge — Manual Scheduling Fallback** | Fires when Jorge's bot offers calendar slots but the contact doesn't pick one via keyword. Sends Jorge a manual follow-up alert to schedule directly |
| **AI Bot - Jorge Qualification** | Fires when the `Needs Qualifying` tag is added via cold call form or signal snipe. Launches the Jorge AI qualification flow on the contact |

---

### Supporting Workflows (used by Jorge bots)

| Workflow | What It Does |
|----------|-------------|
| **1. Bot Change** | Handles mid-conversation bot switches — saves context, removes old bot tag, adds new one |
| **2. AI OFF/ON Tag Added** | Monitors `AI-Off` / `AI-On` tags — updates the "AI Assistant Is" custom field so bots check status before responding |
| **3. AI Tag Removal** | Cleans up old AI state tags when a new bot activates |
| **5. Process Message — Which Bot?** | Secondary webhook entry point — reads contact tags to determine which bot should handle a message |
| **New Inbound Lead** | Fires on new contact creation — applies `Needs Qualifying`, creates opportunity, routes to appropriate activation |
| **"For Seller" Disposition Changed** | Fires when seller disposition field changes — triggers appropriate Status– campaign |
| **Retail Buyer Disposition Changed** | Fires when buyer disposition changes — routes to appropriate STG stage workflow |
| **Seller Dispo + Assign User** | Assigns Jorge as owner on seller contacts and logs disposition change |
| **#1 Inbound Lead Force Call** | Fires on inbound lead tags — triggers forced call task to Jorge for immediate outreach |

---

## Section 10 — Complete Tag Reference

This is the full list of every tag the bot system uses. Use this to know which tags are safe to add, remove, or rename in GHL.

### Tags You Control (Safe to Add/Remove Manually)

| Tag | Add To... | Effect |
|-----|-----------|--------|
| `Needs Qualifying` | Any contact | Starts the Lead or Seller bot |
| `Seller-Lead` | Any contact | Same as Needs Qualifying — starts Seller bot |
| `Buyer-Lead` | Any contact | Starts the Buyer bot |
| `AI-Off` | Any contact | **Immediately stops all bots** for that contact. Bot will not respond until removed. |
| `Stop-Bot` | Any contact | Same as AI-Off |

> **Tip:** To pause the bot on one contact, add `AI-Off`. To restart it, remove `AI-Off`. The bot picks up fresh on the next message.

---

### Tags the Bots Apply Automatically (Do Not Remove Without Reason)

Removing these mid-conversation can cause the bot to re-run a completed flow or lose context.

| Tag | Applied By | When | Triggers |
|-----|-----------|------|----------|
| `Hot-Seller` | Seller bot | All 4 questions answered with quality responses | Hot Seller workflow (Jorge notified, calendar offered) |
| `Warm-Seller` | Seller bot | Partial qualification (good signal, not complete) | Warm Seller nurture drip |
| `Cold-Seller` | Seller bot | Unresponsive or vague answers | Long-term follow-up sequence |
| `Seller-Qualified` | Seller bot | Qualification flow finished | Prevents bot from restarting |
| `Hot-Lead` | Lead bot | Lead score ≥ 80 | Priority workflow + agent notification |
| `Warm-Lead` | Lead bot | Lead score 40–79 | Nurture sequence + follow-up reminder |
| `Cold-Lead` | Lead bot | Lead score < 40 | Educational content + periodic check-in |
| `Qualified` | Any bot | Qualification complete | Deactivates all further bot processing |
| `TCPA-Opt-Out` | Response pipeline | Lead sent STOP, unsubscribe, or opt-out phrase | Bot permanently silenced for this contact |
| `Compliance-Alert` | Response pipeline | Message blocked for FHA/RESPA violation | Flags contact for review — bot response was replaced with safe fallback |
| `Human-Escalation-Needed` | Conversation repair | Bot tried multiple repair strategies and failed | Flags for Jorge to step in manually |

---

### What You Can Safely Edit in GHL

| Action | Safe? | Notes |
|--------|-------|-------|
| Add `AI-Off` or `Stop-Bot` | ✅ Yes | Standard kill switch — use any time |
| Remove `AI-Off` or `Stop-Bot` | ✅ Yes | Restarts bot on next message |
| Add `Needs Qualifying` or `Buyer-Lead` | ✅ Yes | Manually activates the appropriate bot |
| Remove `Hot-Seller` / `Warm-Seller` / `Cold-Seller` | ⚠️ Careful | Bot won't re-apply unless it re-qualifies. Only remove if you want to reset the classification. |
| Remove `Seller-Qualified` or `Qualified` | ⚠️ Careful | Bot will restart the qualification flow on next message |
| Remove `TCPA-Opt-Out` | ❌ No | This is a legal compliance record. Only remove if you have confirmed re-consent from the contact. |
| Rename any tag | ❌ No | Tag names are hardcoded in the bot — renaming breaks routing. Contact developer to change. |

---

## Reference Documents

| File | Contents |
|------|---------|
| `HANDOFF.md` | Repo root · quick-reference for GHL config, bot tags, and Gate 5 test script |
| `AGENTS.md` | Agent personas and tone details |
| `DEPLOYMENT_CHECKLIST.md` | Full env var reference and deploy steps |
| `CLAUDE.md` | Full system architecture |
| `JORGE_PRODUCTION_IDS.md` | All production GHL IDs — workflows, custom fields, calendar |
