# Outreach Templates V2

**Author**: Cayman Roden | **Date**: February 2026
**Purpose**: Three segment-specific outreach templates with A/B subject lines, email body, and LinkedIn InMail versions.

---

## Template 1: GHL Agency Owner

### Subject Lines

- **A**: Your GHL setup is leaving money on the table
- **B**: How we cut a GHL agency's AI costs by 89%

### Email Body (180 words)

Hi {{first_name}},

I saw {{company}} is running GoHighLevel for your clients. Nice setup.

Quick question: are your bots handing off leads without losing context? Most GHL agencies I talk to are losing 30-50% of qualified leads during bot-to-bot transitions because the conversation history gets dropped.

I built a system for a real estate operation on GHL that solved this. The results:

- **89% reduction in LLM costs** ($3,600/mo down to $400/mo)
- **Zero context loss** on handoffs between Lead, Buyer, and Seller bots
- **Sub-200ms response times** even with multi-bot orchestration

The whole thing runs on a 3-tier Redis caching layer with intelligent handoff routing. It manages a $50M+ pipeline now.

I'd love to do a **free 15-minute mini-audit** of your GHL automation setup. No pitch, just specifics on where you're leaking leads or overpaying on API calls.

Worth a quick look?

Best,
Cayman Roden
Python/AI Engineer | GHL + AI Specialist
caymanroden@gmail.com | (310) 982-0492

### LinkedIn InMail Version (120 words)

Hi {{first_name}},

I noticed you're running a GHL agency and thought this might be relevant.

I built an AI orchestration layer on top of GoHighLevel for a real estate operation. Three specialized bots (Lead, Buyer, Seller) with intelligent handoffs, 3-tier caching, and tag-based routing. The result: 89% reduction in LLM costs and zero context loss during bot transitions.

Most GHL agencies I've talked to are overpaying on AI API costs by 40-80% and losing leads during handoffs.

I'm offering free 15-minute GHL audits this month -- just a quick look at your automation setup with specific recommendations. No strings.

Interested?

Cayman Roden
Python/AI Engineer
caymanroden@gmail.com

---

## Template 2: PropTech Founder

### Subject Lines

- **A**: Your lead qualification is slower than your competitors'
- **B**: 88% cache hit rate on AI lead scoring -- here's how

### Email Body (175 words)

Hi {{first_name}},

I've been following {{company}}'s work in {{specific_area}}. The PropTech companies winning right now are the ones responding to leads in under 60 seconds with intelligent qualification -- not just auto-replies.

I built an AI-powered lead qualification system for a real estate platform that:

- **Scores leads in real-time** using multi-LLM orchestration (Claude + Gemini)
- **Routes Hot/Warm/Cold leads** automatically via CRM tag automation
- **Qualifies across 10 dimensions** including budget, timeline, pre-approval status, and motivation

The system manages a $50M+ pipeline with 5,100+ automated tests in production. It cut LLM costs by 89% through intelligent caching -- an 88% hit rate means most queries never touch the API.

I'd love to show you how this architecture could work for {{company}}. I've got a 15-minute demo that walks through the qualification flow and CRM integration.

Open to a quick call this week?

Cayman Roden
Python/AI Engineer | RAG & Multi-LLM Orchestration
caymanroden@gmail.com | (310) 982-0492

### LinkedIn InMail Version (115 words)

Hi {{first_name}},

Saw {{company}} is building in PropTech -- great space right now.

Quick thought: the real estate AI companies pulling ahead are the ones with sub-minute lead qualification and intelligent routing. I built a system that does this with multi-LLM orchestration, 3-tier caching (89% cost reduction), and CRM integration that auto-tags leads as Hot/Warm/Cold.

It manages a $50M+ pipeline in production with 5,100+ automated tests.

I've got a 15-minute demo that shows the full qualification flow. Would be happy to walk you through it and discuss how something similar could fit {{company}}'s roadmap.

Worth a look?

Cayman Roden
Python/AI Engineer
caymanroden@gmail.com

---

## Template 3: SaaS CTO

### Subject Lines

- **A**: Your AI pipeline is costing you 40-80% more than it should
- **B**: Fractional AI CTO -- $150/hr vs $250K/yr hire

### Email Body (185 words)

Hi {{first_name}},

I noticed {{company}} is {{hiring_signal_or_product_detail}}. Building production AI systems is a different animal from prototyping -- the gap between "works in Jupyter" and "reliable at scale" is where most teams burn 3-6 months.

I'm a fractional AI CTO who ships production systems, not slide decks. A few proof points:

- **8,500+ automated tests** across 11 production repositories
- **89% LLM cost reduction** via 3-tier Redis caching (88% hit rate)
- **P99 latency: 0.095ms** for multi-agent orchestration
- **3 CRM integrations** (GoHighLevel, HubSpot, Salesforce)

My entry point is a **$2,500 Architecture Audit** -- a scored assessment across six categories (RAG quality, latency benchmarks, LLM cost analysis, security, data quality, CRM integration). You get a 20-30 page report with P50/P95/P99 benchmarks, a migration roadmap, and a 60-minute walkthrough.

Most audits identify $5,000-$15,000/month in savings. The engagement pays for itself in the first month.

Want to do a 30-minute discovery call to see if it's a fit?

Cayman Roden
Python/AI Engineer | Fractional AI CTO
caymanroden@gmail.com | (310) 982-0492

### LinkedIn InMail Version (125 words)

Hi {{first_name}},

I saw {{company}} is building AI products and thought this might resonate.

I'm a fractional AI CTO with 20+ years of engineering experience and 11 production repos with 8,500+ tests. My last project achieved 89% LLM cost reduction and sub-200ms orchestration for a multi-agent AI platform.

Most AI teams I work with are overspending on LLM costs by 40-80% and underinvesting in caching, testing, and observability.

My entry point is a $2,500 Architecture Audit -- a scored assessment with P50/P95/P99 benchmarks and a migration roadmap. Typically identifies $5K-$15K/month in savings.

Happy to do a quick discovery call to see if there's a fit.

Cayman Roden
Python/AI Engineer | Fractional AI CTO
caymanroden@gmail.com

---

## Usage Notes

### Personalization Variables

| Variable | Description |
|----------|-------------|
| `{{first_name}}` | Recipient's first name |
| `{{company}}` | Company name |
| `{{specific_area}}` | Their product focus or market segment |
| `{{hiring_signal_or_product_detail}}` | What triggered outreach (job posting, product launch, etc.) |

### A/B Testing Strategy

- Send variant A to first 5 contacts in each segment, variant B to next 5
- Track open rates and reply rates separately
- After 20 sends, use the winning subject line for remaining outreach
- Rotate between email and LinkedIn for first touch (track which channel converts better)

### Timing

| Segment | Best Send Day | Best Send Time |
|---------|---------------|----------------|
| GHL Agency Owners | Tuesday-Thursday | 9-11 AM recipient's timezone |
| PropTech Founders | Tuesday-Wednesday | 10 AM - 12 PM PT |
| SaaS CTOs | Monday-Wednesday | 8-10 AM PT |
