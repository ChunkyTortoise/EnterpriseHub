# Jorge Salas — AI Opportunity Roadmap 2026
**Rancho Cucamonga, CA | Bilingual (EN/ES) | Solo Residential Agent**
*Research date: February 2026 | Prepared by: Cayman Roden*

---

## What's Already Built (Excluded from Recommendations)

The following are live and operational — not recommended again below:
- SMS qualification bots (seller / buyer / lead) on GHL via Render
- BANT scoring engine → Hot/Warm/Cold tagging → GHL workflow triggers
- Property matching engine (price/bed/bath/neighborhood + must-have scoring)
- Automated follow-up sequences (2-3 day cadence × 30 days → 14-day long-term)
- Calendar booking (slot offering + GHL appointment creation)
- SB 1001 / TCPA compliance pipeline (AI disclosure, opt-out handling)
- AI cost tracker + 7am digest email
- Admin dashboard (Streamlit, 8 pages)
- GHL tag-based workflow orchestration (6 workflows live)

---

## Priority Action Matrix

```
EFFORT vs. IMPACT GRID

HIGH IMPACT
    │
    │  [D] Homebot          [A] RPR AI CMA
    │  [D] GHL Review        [A] ListingAI
    │      Workflow          [A] AI HomeDesign
    │  [D] NotebookLM        [B] HeyGen
    │  [D] DealCheck         [B] Goodcall
    │                        [B] KCM Pro
    │  [C] WATI WhatsApp     [C] Predis.ai
    │  [C] PropStream        [C] tl;dv + Motion
    │  [C] Likely.AI         [C] Opus Clip
    │                        [C] Glide
    │
    │  [D] White-Label       [D] REDX
    │      Bot Resale        [D] FlyFin
    │
LOW IMPACT
    └──────────────────────────────────────
      LOW EFFORT              HIGH EFFORT
      (Self-config,           (Dev required,
       <1 week)                1-4 weeks)

[A] = Quick Win (this week)
[B] = Quick Win (next week)
[C] = 1-2 week build
[D] = Strategic investment
```

---

## TOP 5 QUICK WINS — Buildable This Week (<1 week each)

### QW-1: RPR AI CMA + Free Branded Market Reports
**Tool**: NAR RPR (narrpr.com) — **FREE** (NAR member benefit)
**What**: AI-scored comparable selection, pricing strategy options (below/at/above market),
neighborhood reports, school data, demographics — all branded with Jorge's info.
**Impact**: Replaces or supplements $35-49/mo Cloud CMA subscription. Generates polished
client-facing reports in minutes. Homebeat equivalent (automated monthly market updates
to sphere) available via RPR.
**Action**: Log in at narrpr.com with NAR credentials. Enable AI CMA. Run first report
on a current listing. Set up Homebeat market update emails for top 50 SOI contacts.
**Time**: 2 hours to set up, zero ongoing effort.

---

### QW-2: ListingAI for Dual-Language Listing Descriptions
**Tool**: ListingAI (listingai.co) — **Free / $14/mo Pro**
**What**: Generate MLS descriptions + social copy in English AND Spanish from property
data. Built-in Fair Housing compliance scanner that auto-flags violations. 50+ languages.
**Impact**: Saves 30-60 min per listing. Competitive edge in the 35% Hispanic Rancho
Cucamonga market — most IE agents publish English-only listings.
**Action**: Sign up free. Test with Jorge's next listing. Produce EN + ES versions.
Add Fair Housing scanner to standard listing prep workflow.
**Time**: 30 minutes to set up.
**CA Legal**: Complies with CA AI Transparency Act (SB 942) — disclose AI-generated copy.

---

### QW-3: AI HomeDesign for Virtual Staging
**Tool**: AI HomeDesign (aihomedesign.com) — **$19/mo annual** (was $49/mo monthly)
**What**: Virtual staging, furniture removal, room redesign in 30 seconds at $0.24/photo.
30 photos under $8 total vs. $300-500 for traditional virtual staging.
**Impact**: Staged homes sell for 1-5% more and 73% faster (NAR). At Jorge's average
price point ($500K), 1% improvement = $5,000 per listing.
**Action**: Sign up annual plan ($19/mo). Stage next 5 listings. Pair each staged
photo with original (AB 723 requires this — label as "virtually staged").
**Time**: 1 hour to set up. 15 min per listing thereafter.
**CA Legal**: AB 723 (eff. Jan 1, 2026) — MUST label AI-staged photos and show original.

---

### QW-4: Homebot for SOI Passive Nurturing
**Tool**: Homebot (homebot.ai) — **$25/mo**
**What**: Automated monthly home value digest emails to past clients. 89% accuracy
predicting which clients will sell in the next 9 months. Jorge gets notified when a
past client's equity or market conditions trigger a "thinking about selling?" moment.
**Impact**: One referral or repeat transaction from a past client = $7,500-15,000 commission.
$25/mo pays for itself with a single converted lead every ~3 years. Most agents report
recovering multiple past clients in the first 6 months.
**Action**: Import Jorge's full past client database (all addresses). Enable monthly
automated sends. Review "likely to sell" alerts weekly.
**Time**: 2 hours to set up. Zero ongoing effort.

---

### QW-5: GHL Review Request Workflow
**Tool**: GoHighLevel (already deployed) — **$0 incremental**
**What**: Automated post-closing SMS + email sequence asking for Google and Zillow reviews.
Triggers when deal status moves to "Closed" in GHL pipeline. Sends 3-touch sequence:
Day 1 (SMS), Day 3 (email), Day 7 (SMS follow-up).
**Impact**: Most agents get 1-2 reviews/month passively. Automating the ask pushes
to 4-6/month. 50 reviews on Google = top-3 local search position for "realtor
Rancho Cucamonga." Review velocity compounds — each review improves SEO, which
brings more leads.
**Action**: Build a 3-step post-closing review request workflow in GHL. Cayman builds
this in < 2 hours. Test with Jorge's next 3 closings.
**Time**: 2 hours dev. $0 marginal cost.

---

## TOP 5 STRATEGIC INVESTMENTS — Worth 1-4 Weeks of Development

### SI-1: HeyGen Bilingual Avatar Video System
**Tool**: HeyGen Creator (heygen.com) — **$29/mo**
**What**: Create a digital avatar of Jorge that presents listings, market updates,
and neighborhood tours in both English AND Spanish — without Jorge needing to be
on camera. Feb 2026 update: unlimited Spanish audio dubbing on all paid plans.
Record once in English → AI dubs to Spanish automatically.
**Use cases**:
- 60-second listing walkthrough videos (EN + ES)
- Weekly Rancho Cucamonga market update videos
- "Why buy in the Inland Empire" investor pitch video
- First-time buyer guide video series (bilingual)
**Impact**: Properties with video get 403% more inquiries. Bilingual video content
reaches the underserved ~35% Hispanic homeowner market in the IE.
**Action**: Create avatar ($29/mo plan). Produce 5 template video scripts
(listing, market update, buyer guide, seller guide, investor pitch).
Record English versions → auto-dub to Spanish. Publish to GHL contact nurture sequences.
**Time**: 1 week to produce initial video library. 30 min/video thereafter.
**Pair with**: Opus Clip ($15/mo) to repurpose long videos into Instagram/TikTok Reels.

---

### SI-2: Goodcall Voice AI Receptionist
**Tool**: Goodcall (goodcall.com) — **$59/mo** (unlimited minutes)
**What**: AI phone receptionist that answers inbound calls 24/7 — qualifies buyers
by price range/timeline, answers property FAQs, texts property links, and schedules
showings. Automatically updates GHL CRM.
**Why this matters**: 40%+ of buyer calls come in evenings and weekends. Jorge misses
these. Goodcall captures them, qualifies them, and feeds hot leads directly into
Jorge's GHL workflows.
**Impact**: Goodcall replaces a $2,500-4,000/mo human receptionist. At $59/mo,
the ROI is 40-65x. Even capturing 2 additional qualified leads/month from after-hours
calls pays for the tool.
**Setup**: Configure bilingual call flow (EN/ES). Connect to GHL via Zapier/webhook.
Define qualification questions. Forward Jorge's main business line.
**Time**: 3-5 days to configure, test, and forward calls. Cayman assists with GHL integration.
**CA Legal**: SB 1001 — call must open with AI disclosure. CA Penal Code 632 — must inform
caller that call may be recorded (two-party consent).

---

### SI-3: KCM Pro + Predis.ai Content Engine
**Tools**: Keeping Current Matters Pro ($59.95/mo) + Predis.ai Starter ($29/mo) = **$89/mo**
**What**:
- **KCM Pro**: Done-for-you, research-backed market content (daily blog posts, buyer/seller
  guides, infographics, social graphics). RealTalk video tool generates scripts +
  teleprompter for on-camera content. Saves 5-8 hrs/week on research and writing.
- **Predis.ai**: AI content generator — type a prompt ("Rancho Cucamonga first-time
  buyer tips in Spanish") → get complete post: image + caption + hashtags + video.
  Bilingual support. Competitor analysis. Ready-to-schedule output.
**Combined workflow**:
1. KCM provides market data and research-backed insights
2. Predis.ai generates bilingual social posts from those insights
3. Later.com ($25/mo optional) schedules across Instagram/Facebook/YouTube
**Impact**: Consistent social presence without Jorge spending 10+ hrs/week on content.
Hyperlocal bilingual content = dominant voice in the Rancho Cucamonga Hispanic homeowner
market online.
**Time**: 1 week to set up editorial calendar and templates. 2 hrs/week thereafter.

---

### SI-4: WATI WhatsApp Integration (Bilingual)
**Tool**: WATI (wati.io) — **$49/mo**
**What**: WhatsApp Business API integration with AI chatbot flows, rich media support
(property photos, PDFs, virtual tour links, documents). Bilingual EN/ES conversations.
**Why this matters**: WhatsApp is the dominant messaging platform for Hispanic/Latino
communities in Southern California. Jorge's leads from the Hispanic market overwhelmingly
prefer WhatsApp over SMS. Sending property images, disclosures, and updates via WhatsApp
meets them where they already communicate.
**What to build**:
- Property inquiry bot in Spanish (sends photos, schedules showings, collects buyer criteria)
- Post-qualification property match delivery (send top 3 matches as WhatsApp messages with images)
- Offer update notifications via WhatsApp (faster than email for transaction-phase clients)
- Connect to GHL via Zapier for bidirectional CRM sync
**Time**: 1-2 weeks to build flows and connect to GHL. Cayman builds the integration.
**CA Legal**: Must get WhatsApp opt-in. SB 1001 disclosure at first automated interaction.

---

### SI-5: White-Label Bot Resale to IE Agents
**Platform**: GoHighLevel SaaS Pro — **$497/mo** (revenue generator, not a cost)
**What**: Package Jorge's live GHL SMS bot stack as a resellable SaaS product for other
Inland Empire agents. Cayman builds a "snapshot" (GHL's white-label export) of Jorge's
entire bot configuration. Jorge sells it to other IE agents for $197-249/mo per sub-account.
**Economics**:
- GHL SaaS Pro: $497/mo
- 5 clients @ $199/mo: $995/mo → net $498/mo profit
- 10 clients @ $199/mo: $1,990/mo → net $1,493/mo profit
- 20 clients @ $199/mo: $3,980/mo → net $3,483/mo profit
- 40 clients @ $199/mo: $7,960/mo → net $7,463/mo profit
**Pricing tiers**:
- Basic ($199/mo): English SMS bots + BANT scoring + follow-up sequences
- Premium ($299/mo): Adds Spanish bots + investor qualification + compliance pipeline
- Setup fee: $500 one-time (covers sub-account config, workflow clone, 1hr training)
**Why Jorge wins**: He's a practicing agent using these bots in the field — not a
tech company selling to agents. Real testimonials, real case studies, local credibility.
**Cayman's role**: Build GHL snapshot, white-label branding, onboarding materials,
support documentation. Ongoing: client onboarding (1-2 hrs per client).
**Timeline**: 2-3 weeks to build snapshot + materials. 1 week to recruit first 3 pilot clients.
**CA Legal**: No restrictions on SaaS resale. A2P 10DLC registration needed per sub-account.

---

## All 9 Domains — Complete Tool Reference

### Domain 1: Listing & Marketing Intelligence

| Tool | Cost | Use Case | Priority |
|------|------|----------|----------|
| ListingAI | Free/$14 | EN+ES descriptions + Fair Housing scan | **QW-2** |
| AI HomeDesign | $19/mo | Virtual staging at $0.24/photo | **QW-3** |
| HeyGen Creator | $29/mo | Bilingual avatar listing videos | **SI-1** |
| Saleswise | $39/mo | All-in-one: CMA + descriptions + staging | Optional |
| BoxBrownie | $24/image | Premium hero shots (pay-per-use) | Optional |
| AutoReel | Free | Quick listing Reels (2/mo free tier) | Free add-on |

**CA Legal — AB 723 (eff. Jan 1, 2026)**: Every AI-staged or digitally altered photo
MUST be labeled "virtually staged" or "digitally altered" AND the unaltered original must
immediately precede/follow it or be accessible via link. Basic edits (exposure, cropping,
white balance) are excluded. Violation = DRE discipline + civil/criminal liability.

---

### Domain 2: Market Analysis & CMA

| Tool | Cost | Use Case | Priority |
|------|------|----------|----------|
| RPR AI CMA | FREE | AI-scored comps, pricing strategy, neighborhood reports | **QW-1** |
| Saleswise | $39/mo | 30-second CMA from live MLS data | Optional |
| Cloud CMA + Homebeat | $49/mo | Premium branded presentations + auto sphere updates | Optional |
| HouseCanary | $69/mo | Institutional-grade AVM + CanaryAI predictions | Optional |
| PropStream | $199/mo | Off-market deal identification + pre-foreclosure | Domain 6 |

**Recommendation**: RPR (free) covers 95% of Jorge's CMA needs. Only add Cloud CMA ($49/mo)
if he wants premium presentation design for luxury or competitive listings.

---

### Domain 3: Lead Generation & Prospecting

| Tool | Cost | Use Case | Priority |
|------|------|----------|----------|
| Homebot | $25/mo | SOI nurturing + "likely to sell" alerts | **QW-4** |
| REDX | ~$120/mo | Expired listings + FSBO with verified phone numbers | Strategic |
| Likely.AI | ~$150/mo | 90-day seller predictions from existing contacts | Strategic |
| PropStream Pro | $199/mo | Off-market, pre-foreclosure, absentee, probate | Strategic |
| USLeadList | ~$100-150/mo | Exclusive probate leads, San Bernardino County | Optional |
| SmartZip | $599/mo | Geographic farming prediction (premium) | Skip for now |
| Offrs | $399/mo | Geographic farming prediction (mid-tier) | Skip for now |

**Hispanic Market Strategy**: No dedicated AI tool exists for this niche. Jorge's bilingual
ability is the competitive moat — AI handles lead identification at scale, Jorge handles
the bilingual relationship. Use PropStream/BatchLeads filtered by Rancho Cucamonga ZIP codes
with high Hispanic homeownership, then route to bilingual follow-up sequences in GHL.

---

### Domain 4: Client Experience & Communication

| Tool | Cost | Use Case | Priority |
|------|------|----------|----------|
| Goodcall | $59/mo | AI phone receptionist, 24/7 inbound qualification | **SI-2** |
| WATI | $49/mo | WhatsApp bilingual chatbot + rich media | **SI-4** |
| Glide | FREE | CA-specific transaction management + e-sign | This week |
| SkySlope | $25-60/mo | AI Smart Scan for document processing | Optional |
| Claude/ChatGPT | $0-20/mo | Private contract pre-review (agent use only, not legal advice) | Existing |
| DeepL Pro | $8.74/mo | Batch translation for marketing materials | Optional |

**CA Legal — Voice AI (SB 1001 + CA Penal Code 632)**:
- Voice AI MUST disclose it's AI at the start of every call
- Two-party consent required for call recording in California
- Callers must be informed the call may be recorded before it begins

**CA Legal — WhatsApp (CCPA + SB 1001)**:
- Must obtain explicit opt-in before sending WhatsApp messages
- First automated message must identify as AI/bot
- Must provide opt-out mechanism

---

### Domain 5: Content & Social Media Automation

| Tool | Cost | Use Case | Priority |
|------|------|----------|----------|
| KCM Pro | $59.95/mo | Daily research-backed content + video scripts | **SI-3** |
| Predis.ai Starter | $29/mo | AI social post generation (EN/ES) from prompts | **SI-3** |
| Opus Clip Starter | $15/mo | Repurpose listing videos into Reels/Shorts | This month |
| NotebookLM | FREE | Weekly market podcast from MLS/market data | This week |
| HeyGen Creator | $29/mo | Bilingual avatar videos (shares with Domain 1) | **SI-1** |
| Later Starter | $25/mo | Visual scheduling for Instagram/Facebook | Optional |
| Parkbench | $99-199/mo | Hyperlocal Rancho Cucamonga community site | Optional |
| Beehiiv Scale | $43/mo | Newsletter with monetization | Long-term |

**GHL Review Workflow (Domain 5E — built in-house)**:
Skip Birdeye ($299/mo), Podium ($250/mo) — GHL already handles automated review requests.
Build a 3-step post-closing review workflow in GHL (covered under QW-5). Cost: $0.

---

### Domain 6: Investor & Wholesale Pipeline

| Tool | Cost | Use Case | Priority |
|------|------|----------|----------|
| DealCheck Plus | $10-14/mo | Cap rate, COC, ROI, IRR analysis + PDF reports | This week |
| PropStream Essentials | $199/mo | Investor data, wholesale valuations, motivated sellers | Month 2 |
| DealMachine Starter | $99/mo | Driving-for-dollars + Alma AI deal analysis | Month 2 |
| Mashvisor Lite | $24.99/mo | Short-term rental / Airbnb analysis | Optional |
| REsimpli Basic | $99/mo | Investor CRM (only if separating from GHL) | Skip — GHL covers this |

**Key Insight**: DealCheck at $10-14/mo instantly gives Jorge professional deal analysis
capabilities for investor clients. At this price point it's practically free and provides
PDF deal packages that impress investor buyers.

---

### Domain 7: Transaction & Operations Efficiency

| Tool | Cost | Use Case | Priority |
|------|------|----------|----------|
| Glide | FREE | CA transaction management + e-sign | This week |
| FlyFin | $192/yr ($16/mo) | AI tax prep + real CPA filing included | This month |
| Keeper Tax | $20/mo | Year-round deduction tracking | Optional |
| DocuSign RE | $45/mo | E-sign with AI signer experience | If brokerage doesn't provide |
| SkySlope | $25-60/mo | AI Smart Scan for document processing | Optional |

**CA Legal — AI Contract Review**:
Real estate agents in California CANNOT provide legal advice or opinions on contract terms.
Using AI to review a contract is permissible for the agent's own awareness only. Never
advise clients on legal implications — always refer to an attorney for anything beyond
standard C.A.R. form completion. Claude/ChatGPT for private pre-review: OK.
Presenting AI analysis as legal advice to clients: NOT OK (unauthorized practice of law).

---

### Domain 8: Coaching & Personal Performance

| Tool | Cost | Use Case | Priority |
|------|------|----------|----------|
| tl;dv Free → Pro | $0-18/mo | Call recording, AI summaries, Spanish support | This week |
| Motion | $19-29/mo | AI daily schedule optimization | This week |
| GHL pipeline analytics | $0 | Conversion by lead source (already deployed) | Already live |
| Follow Up Boss | $69/mo | Advanced lead source attribution (only if GHL insufficient) | Skip |

**tl;dv Key Differentiator**: Supports 30+ languages including Spanish. Jorge can
record and analyze his Spanish-language client calls for coaching insights — no other
tool at this price point does this.

---

### Domain 9: Long-Term Business Building

| Tool | Cost | Use Case | Priority |
|------|------|----------|----------|
| Homebot | $25/mo | Past client re-engagement (shared with Domain 3) | **QW-4** |
| GHL White-Label SaaS | $497/mo | Resell bot stack to IE agents | **SI-5** |
| BombBomb Essentials | $39/mo | Video email for sphere differentiation | Optional |
| ReferralExchange | $95/mo + $495 setup | Agent-to-agent out-of-area referrals | Low priority |

**ISA Hiring Threshold**: Jorge is NOT at the ISA threshold yet. Hire a part-time
virtual ISA ($1,500-2,000/mo, MyOutDesk) when: (a) consistently 50+ new leads/month,
(b) bot-qualified warm leads going cold because Jorge can't personally follow up fast
enough, AND (c) GCI exceeds $250K/yr. Until then, bots handle top-of-funnel; Jorge
handles all warm/hot lead conversations.

---

## California Legal Compliance — Master Reference

| Law | Requirement | Action Required |
|-----|------------|-----------------|
| **AB 723** (eff. Jan 1, 2026) | Disclose AI-altered images; show original paired with altered | Label every AI-staged photo; show before/after pair in MLS |
| **SB 942** (eff. Jan 1, 2026) | Disclose AI-generated content | Watermark or note on AI-written listings, market analyses |
| **SB 1001** (Bot Disclosure) | Bots must disclose they are AI in online interactions | All GHL bots, Goodcall, WATI must open with AI disclosure |
| **CCPA + ADMT** (eff. Oct 1, 2025; compliance by Jan 1, 2027) | Pre-use notice for automated housing decisions; opt-out rights | Add opt-out to lead qualification workflows; update privacy policy |
| **CA Penal Code 632** | Two-party consent for call recording | Voice AI must announce recording before call begins |
| **TCPA + DNC** | No robocalls without consent; check DNC registry | All AI dialing tools must verify consent + DNC status |
| **Fair Housing + FEHA** | No AI-based discrimination by protected class | AI targeting must be geographic only, never demographic |
| **CA DRE Fiduciary Duty** | Agent must supervise AI; cannot delegate licensed activities | Review all AI-generated client advice before sending |
| **UPL (Unauthorized Practice of Law)** | Agents cannot give legal advice | AI contract review = private agent tool only, not client advice |

---

## Recommended Monthly Budget Tiers

### Tier 1 — Foundation ($50-100/mo incremental)
*Start immediately. Zero dev time required.*
| Tool | Cost |
|------|------|
| RPR AI CMA | $0 |
| ListingAI | $0-14 |
| AI HomeDesign | $19 |
| Homebot | $25 |
| GHL Review Workflow | $0 |
| tl;dv | $0 |
| NotebookLM | $0 |
| DealCheck Plus | $14 |
| Glide | $0 |
| **Total** | **$58-72/mo** |

### Tier 2 — Growth ($200-300/mo incremental)
*Add Month 2. ~1 week of dev/setup time.*
| Tool | Cost |
|------|------|
| HeyGen Creator | $29 |
| Goodcall | $59 |
| Predis.ai Starter | $29 |
| Opus Clip Starter | $15 |
| KCM Pro | $59.95 |
| Motion | $19-29 |
| FlyFin | $16 |
| **Total** | **$227-237/mo** |

### Tier 3 — Full Stack ($450-600/mo incremental)
*Add Month 3+. 2-3 weeks of dev/setup time.*
| Tool | Cost |
|------|------|
| WATI WhatsApp | $49 |
| PropStream Essentials | $199 |
| DealMachine Starter | $99 |
| REDX (Expired + FSBO) | $120 |
| Likely.AI | ~$150 |
| **Total** | **$617/mo** |

### Revenue Generator (Self-Funding After 3-5 Clients)
| Tool | Cost |
|------|------|
| GHL SaaS Pro (white-label) | $497/mo |
| Revenue at 10 clients × $199/mo | $1,990/mo |
| **Net profit** | **$1,493/mo** |

**Total all-in (Tier 1+2+3 + SaaS)**: ~$1,400/mo
**One additional closed transaction per quarter** covers the entire annual stack cost.

---

## The Bilingual Advantage — Jorge's Structural Edge

Rancho Cucamonga (San Bernardino County) has a ~35% Hispanic population. The homeownership
gap between white and Hispanic households in California is 30+ percentage points — a massive
underserved market. First-generation Hispanic homebuyers overwhelmingly prefer working with
bilingual agents.

**What no competitor tool can replicate**: Jorge's native bilingual ability + community
credibility. AI amplifies this:
- HeyGen: scales his bilingual video presence × unlimited
- WATI: WhatsApp (preferred by Hispanic clients) with Spanish bot flows
- ListingAI: Dual EN/ES MLS descriptions for every listing
- GHL bots: Already bilingual-capable — just need Spanish workflow variations

**Market opportunity**: Jorge can claim the "bilingual AI-powered Rancho Cucamonga REALTOR"
positioning before any competitor does. This is a 2026 window.

---

## Next Steps Checklist

**This Week (Zero Cost)**
- [ ] Log in to RPR (narrpr.com) — run first AI CMA on next listing
- [ ] Sign up for ListingAI free — generate EN + ES versions of next listing description
- [ ] Set up tl;dv free — record next client call
- [ ] Set up NotebookLM free — generate first "Rancho Cucamonga Market Update" podcast episode
- [ ] Sign up for Glide free — move one pending transaction onto platform
- [ ] Schedule Cayman to build GHL post-closing review request workflow (2 hrs)

**This Month ($72/mo total)**
- [ ] AI HomeDesign annual plan ($19/mo) — stage next listing
- [ ] Homebot ($25/mo) — import full past client database
- [ ] DealCheck Plus ($14/mo) — set up investor client deal templates

**Month 2 ($237/mo additional)**
- [ ] HeyGen Creator ($29/mo) — create avatar, record first bilingual listing video
- [ ] Goodcall ($59/mo) — configure AI receptionist, forward business line
- [ ] KCM Pro ($59.95/mo) — set up content calendar
- [ ] Predis.ai Starter ($29/mo) — generate first week of bilingual social posts
- [ ] Opus Clip Starter ($15/mo) — repurpose first listing video into 5 Reels
- [ ] Motion ($19-29/mo) — connect Google Calendar, let AI schedule for 1 week
- [ ] FlyFin ($16/mo) — connect bank accounts for 2025 tax year catch-up

**Month 3 (Strategic)**
- [ ] WATI WhatsApp setup + Cayman builds bilingual bot flows + GHL integration
- [ ] PropStream Essentials ($199/mo) — first investor lead list for Rancho Cucamonga
- [ ] DealMachine Starter ($99/mo) — first driving-for-dollars session in target neighborhood
- [ ] White-label SaaS pitch to 3 IE agents in Jorge's network (Cayman builds GHL snapshot)
