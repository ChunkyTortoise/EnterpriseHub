# AI Services Proposal for Jorge Salas
**Prepared by Cayman Roden | February 2026**
*Based on your existing GHL stack + comprehensive market research*

---

Everything below builds directly on what's already live. No rebuilding from scratch — these are targeted additions that extend what's working.

---

## Immediate Builds (< 1 week each)

### 1. Post-Closing Review Request Workflow
**What it is**: Automated 3-touch sequence in GHL (SMS → email → SMS) that triggers when a deal closes and asks clients to leave Google and Zillow reviews.
**What I build**: GHL workflow + message templates in English and Spanish. Connects to your existing pipeline.
**Tools needed**: None — already on GHL.
**My fee**: ~2 hours (included in retainer or $150 one-time)
**Expected outcome**: Review velocity moves from ~1-2/month to 4-6/month. 50 Google reviews = top-3 local search ranking for "realtor Rancho Cucamonga."

---

### 2. Spanish Language Bot Variations
**What it is**: Spanish-language versions of your existing SMS seller, buyer, and lead qualification bots — same BANT logic, same GHL workflows, different language.
**What I build**: Duplicate all three bot flows with Spanish messaging. Add language-detection logic (simple keyword trigger) so incoming messages in Spanish auto-route to the Spanish bot.
**Tools needed**: None — already on GHL. Claude API calls continue to work in Spanish natively.
**My fee**: ~4 hours ($300-400 one-time)
**Expected outcome**: Capture the ~35% Spanish-speaking homeowner market in Rancho Cucamonga that your English bots currently under-serve.

---

## Month 1 Builds (1-2 weeks each)

### 3. AI Voice Receptionist Setup (Goodcall)
**What it is**: An AI phone agent that answers your business line 24/7 — qualifies inbound buyers by price/timeline/pre-approval, answers property FAQs, texts property links, and schedules showings. Pushes all data into GHL automatically.
**What I build**: Configure Goodcall with bilingual call scripts (EN/ES). Set up GHL webhook to create contacts + tag inbound calls. Forward your main number.
**Tools needed**: Goodcall ($59/mo, unlimited minutes) + Zapier/webhook to GHL
**My fee**: ~6 hours ($450-500 one-time)
**Expected outcome**: You capture 40%+ of buyer calls that currently go to voicemail (evenings, weekends, when you're in showings). Goodcall replaces a $2,500-4,000/mo human receptionist.
**CA Legal**: Call must open with AI disclosure ("Hi, I'm an AI assistant for Jorge Salas..."). Two-party recording consent required — I'll build this into the script.

---

### 4. WhatsApp Bilingual Bot (WATI Integration)
**What it is**: A WhatsApp Business chatbot that handles property inquiries, sends listing photos/videos, qualifies buyers, and books showings — in English and Spanish. Syncs to GHL.
**What I build**: WATI account setup + bilingual conversation flows (property inquiry → criteria capture → match delivery → showing schedule). Zapier bridge to create/update GHL contacts. Rich media templates (property images, floor plans, virtual tour links sent directly in WhatsApp).
**Tools needed**: WATI ($49/mo)
**My fee**: ~8 hours ($600-700 one-time)
**Expected outcome**: WhatsApp is the dominant channel for Hispanic homeowners in SoCal. 95-98% open rate vs. ~20% for email. Opens a new inbound channel that your competitors aren't using.
**CA Legal**: Opt-in required before first message. SB 1001 AI disclosure at start of each conversation — built into the flow.

---

### 5. Automated Market Report Pipeline (Make.com)
**What it is**: A weekly automated workflow that pulls Inland Empire market data, runs it through AI for narrative + analysis, formats it as a branded email, and sends via GHL to your sphere — without you touching it.
**What I build**: Make.com scenario that fetches MLS/market data (RPR API or data source), sends to Claude for analysis + narrative generation, formats branded email template, queues in GHL for weekly delivery to a segmented list. Optional: also generate an AI podcast episode (NotebookLM or ElevenLabs) from the same data.
**Tools needed**: Make.com (~$16/mo), existing GHL, Claude API (existing)
**My fee**: ~8-10 hours ($700-800 one-time)
**Expected outcome**: Consistent weekly market authority content delivered to your sphere — zero ongoing effort from you. Positions you as the go-to market expert in Rancho Cucamonga. Drives referrals and repeat business.

---

## Month 2-3 Builds (2-4 weeks each)

### 6. Investor Deal Matching System (GHL Custom Workflow)
**What it is**: A system inside GHL that captures investor buyer criteria (price range, property type, preferred returns, deal type), then auto-matches and delivers off-market deals to matched investors when new opportunities are identified.
**What I build**: (a) Investor buyer intake form → GHL custom fields. (b) Off-market deal entry workflow with PropLab-style analysis fields (ARV, repair estimate, margin). (c) Auto-match logic: when a deal is added, query against investor profiles and trigger deal sheet delivery (SMS + email) to matched buyers. (d) Deal sheet template (professional PDF-style email).
**Tools needed**: DealCheck ($14/mo for analysis), GHL (existing)
**My fee**: ~12-15 hours ($900-1,200 one-time)
**Expected outcome**: Scalable wholesale/investor pipeline. When you find an off-market deal, it goes to the right investors automatically. Turns a manual 30-60 min matching process into a 5-minute workflow.

---

### 7. HeyGen Bilingual Video System + Content Templates
**What it is**: Set Jorge up with an AI avatar video workflow — create his digital avatar, build 5-6 reusable video templates (listing walkthrough, market update, buyer guide, seller guide, investor pitch), record in English once and auto-dub to Spanish.
**What I build**: HeyGen account + avatar creation session with Jorge. 5 template scripts (EN) ready for teleprompter recording. Bilingual dubbing workflow. Integration with Opus Clip for repurposing long videos into Reels/Shorts. Standard process doc so Jorge can produce new videos in < 30 min.
**Tools needed**: HeyGen Creator ($29/mo), Opus Clip ($15/mo)
**My fee**: ~6-8 hours ($500-600 one-time, includes recording session)
**Expected outcome**: Properties with video get 403% more inquiries. Bilingual avatar videos create the "bilingual AI-powered Rancho Cucamonga REALTOR" brand positioning before any competitor does.

---

### 8. Predictive Seller Alert → GHL Integration (Likely.AI or SmartZip)
**What it is**: Connect a predictive seller analytics platform to your GHL — when a homeowner in your farm area shows "likely to sell" signals, they automatically get tagged in GHL and entered into a targeted follow-up sequence.
**What I build**: Likely.AI or SmartZip account setup + Zapier/webhook bridge → GHL. When a contact hits a seller score threshold, auto-tag ("Predicted Seller"), enroll in a targeted 30-day sequence (market update → equity report → "thinking about selling?" text). Alert notification to Jorge when a past client or SOI contact triggers.
**Tools needed**: Likely.AI (~$150/mo) or SmartZip ($599/mo if going premium)
**My fee**: ~8 hours ($600-700 one-time)
**Expected outcome**: Reach likely sellers 6-12 months before they list — before Zillow, before other agents. 72-82% accuracy. One additional listing from predictive targeting covers the annual tool cost.

---

## Strategic / Revenue-Generating

### 9. White-Label Bot Resale to Inland Empire Agents
**What it is**: Package your live GHL bot stack (SMS qualification, BANT scoring, Spanish bots, follow-up sequences, compliance pipeline) as a productized SaaS that other IE agents buy monthly. You become the "bilingual AI bot provider for Inland Empire realtors" — a recurring revenue stream independent of your transaction volume.
**What I build**: GHL SaaS Pro account setup ($497/mo replaces your current GHL plan). Snapshot of your full bot configuration (white-labeled, no GHL branding). Branded onboarding portal. Pricing tiers + Stripe recurring billing setup. Onboarding documentation Jorge can hand to new clients. I handle new client sub-account setup (1-2 hrs per client).
**Tools needed**: GHL SaaS Pro ($497/mo — replaces existing GHL cost)
**My fee**: ~20-25 hours for initial build ($1,800-2,200 one-time) + ongoing: $100-150/client onboarded
**Revenue model**:
| Clients | Revenue | Net after GHL |
|---------|---------|--------------|
| 5 clients @ $199/mo | $995/mo | ~$498/mo |
| 10 clients @ $199/mo | $1,990/mo | ~$1,493/mo |
| 20 clients @ $199/mo | $3,980/mo | ~$3,483/mo |
**Expected outcome**: $2,000-5,000/mo recurring at 10-25 clients. Builds long-term business value independent of market conditions. Your "built by a working Rancho Cucamonga agent" credibility is the pitch no tech company can replicate.
**CA Legal**: No real estate license needed to sell SaaS. A2P 10DLC registration required per sub-account — I handle this during client onboarding.

---

## Summary Table

| # | Service | My Fee (est.) | Tool Cost | Priority | Effort |
|---|---------|--------------|-----------|----------|--------|
| 1 | Review Request Workflow | $150 | $0 | This week | 2 hrs |
| 2 | Spanish Bot Variations | $300-400 | $0 | This week | 4 hrs |
| 3 | Goodcall Voice Receptionist | $450-500 | $59/mo | Month 1 | 6 hrs |
| 4 | WhatsApp Bilingual Bot | $600-700 | $49/mo | Month 1 | 8 hrs |
| 5 | Market Report Pipeline | $700-800 | ~$16/mo | Month 1 | 10 hrs |
| 6 | Investor Deal Matching | $900-1,200 | $14/mo | Month 2 | 15 hrs |
| 7 | HeyGen Video System | $500-600 | $44/mo | Month 2 | 8 hrs |
| 8 | Predictive Seller → GHL | $600-700 | ~$150/mo | Month 2-3 | 8 hrs |
| 9 | White-Label Bot Resale | $1,800-2,200 | $497/mo* | Month 3 | 25 hrs |

*GHL SaaS Pro replaces your existing GHL subscription. Net tool cost increase is ~$200-300/mo until first 3 clients cover it.

**You don't need all of these.** The highest-ROI starting point is **#1 + #2 + #3** — three builds totaling ~$900 in dev fees and $59/mo in new tool costs, all delivering measurable results within 30 days.

---

## What I'm NOT building (Jorge self-configures)

These tools are genuinely easy to set up yourself — no dev needed:
- **RPR AI CMA** (free with NAR membership) — log in and run your first AI CMA today
- **ListingAI** (free tier) — generate EN+ES descriptions for next listing
- **AI HomeDesign** ($19/mo) — virtual staging at $0.24/photo
- **Homebot** ($25/mo) — upload past client database, automated from there
- **DealCheck** ($14/mo) — investor deal analysis for client presentations
- **tl;dv** (free) — call recording + AI summaries
- **Glide** (free) — CA transaction management + e-sign

These 7 tools cost ~$58-72/mo combined and take an afternoon to set up. I'm happy to walk you through any of them on a quick call.

---

*All pricing estimates in USD. Dev fees are project-based, not hourly. CA legal compliance built into every deliverable.*
