---
title: "Building an AI Lead Qualification System on GoHighLevel: Architecture and 6-Month Results"
published: false
tags: python, ai, crm, automation
cover_image:
canonical_url:
---

# Building an AI Lead Qualification System on GoHighLevel: Architecture and 6-Month Results

I've been running an AI-powered lead qualification system on top of GoHighLevel for a real estate brokerage for 6 months. Three specialized chatbots, full CRM integration, compliance pipeline, and a 3-tier caching strategy that cut LLM costs by 89%.

This is the technical deep-dive: architecture decisions, integration patterns, compliance requirements, and the production numbers.

---

## The Problem

The brokerage manages a $50M+ pipeline in the Inland Empire market (Rancho Cucamonga, CA). 200+ inbound leads per month from Zillow, Realtor.com, and direct campaigns.

**Speed-to-lead was the bottleneck.** Initial contact took 15-45 minutes. Industry research shows responding within 5 minutes increases conversion by 400%. Every minute past that erodes close rates.

The existing GHL setup had basic automation -- drip sequences, tag-based workflows -- but no intelligent qualification. Every lead got the same generic follow-up regardless of intent.

What they needed:
- Instant response (<60 seconds) to every inbound lead
- Automatic routing based on buyer vs. seller intent
- Temperature scoring so human agents prioritize hot leads
- Everything synced back to GHL so existing workflows still work

## Architecture Decision: Enhance, Don't Replace

The most important decision: **we didn't replace GoHighLevel.** We built an orchestration layer that sits between GHL and LLM providers.

```
Inbound Lead (GHL Webhook)
    |
    v
FastAPI Orchestration Layer
    |
    v
Bot Selection (tag-based routing)
    |
    +--> Lead Bot (tag: "Needs Qualifying")
    +--> Buyer Bot (tag: "Buyer-Lead")
    +--> Seller Bot (tag: "Seller-Lead")
    |
    v
LLM Processing (Claude/Gemini via 3-tier cache)
    |
    v
Response Pipeline (compliance checks)
    |
    v
GHL Contact API (update fields, apply tags, trigger workflows)
```

This means:
- Existing GHL automations continue working
- CRM data stays in GHL (single source of truth)
- AI layer can be upgraded independently
- If the AI layer goes down, GHL still functions

### GHL Integration Points

1. **Contact API**: Read/write custom fields (FRS score, PCS score, temperature, timeline, budget)
2. **Webhook triggers**: Inbound messages activate bot processing
3. **Tag management**: Apply temperature tags (Hot-Lead, Warm-Lead, Cold-Lead), status tags (Qualified, AI-Off)
4. **Workflow triggers**: Hot leads trigger priority notification workflows
5. **Calendar API**: Book appointments directly from bot conversations

Rate limiting: 10 requests/second to the GHL API with exponential backoff.

## The Three Bots

### Lead Bot

Entry point for all new leads. Runs a 10-question qualification flow via SMS:
- What type of property are you looking for?
- What's your timeline?
- Are you pre-approved?
- What's your budget range?

Scores each response on two axes:
- **Financial Readiness Score (FRS)**: Objective qualification (income, pre-approval, budget)
- **Psychological Commitment Score (PCS)**: Subjective engagement (urgency, specificity, responsiveness)

When combined scores exceed thresholds, applies temperature tags and triggers appropriate workflows.

### Buyer Bot

Activated when Lead Bot identifies buyer intent. Deeper qualification:
- Pre-approval status and budget verification
- Property preference extraction (bedrooms, neighborhoods, must-haves)
- Affordability analysis
- Property matching against available listings

### Seller Bot

Activated for seller intent. Assesses:
- Motivation level and timeline urgency
- Property condition self-assessment
- Price expectations vs. market data
- Decision-maker identification (are they the sole owner?)

### Handoff System

When intent shifts mid-conversation (buyer mentions selling), the handoff service:
1. Scores intent confidence (threshold: 0.7)
2. Checks safety gates (rate limit, circular prevention, target health)
3. Packages context (all extracted data, scores, conversation summary)
4. Routes to target bot with full context
5. Target bot continues without re-asking questions

## Compliance Pipeline

Every outbound message passes through a 5-stage pipeline:

```python
# Default pipeline stages (in order):
1. LanguageMirrorProcessor    # Detect language, respond in kind
2. TCPAOptOutProcessor        # Detect STOP/unsubscribe, short-circuit
3. ComplianceCheckProcessor   # FHA/RESPA enforcement
4. AIDisclosureProcessor      # SB 243 "[AI-assisted message]" footer
5. SMSTruncationProcessor     # 320-char SMS limit
```

**TCPA**: Any opt-out phrase (STOP, unsubscribe, cancel, opt out) immediately halts all bot communication, applies AI-Off tag, and sends acknowledgment.

**Fair Housing (FHA)**: The compliance middleware scans generated responses for discriminatory language, steering phrases, or protected class references. Violations are replaced with safe fallback text and flagged.

**SB 243**: California law requiring AI disclosure. Every message includes a language-aware footer: `[AI-assisted message]`.

**SMS Truncation**: Messages exceeding 320 characters are truncated at sentence boundaries. Never mid-sentence.

## 3-Tier Caching for Cost Control

LLM API calls were the biggest cost center. The caching strategy:

- **L1 (in-process)**: Last 10 messages per user. <1ms. 74% hit rate.
- **L2 (Redis)**: Last 100 messages, shared across workers. <5ms. 14% hit rate.
- **L3 (Postgres+pgvector)**: Semantic search for long-tail queries. <50ms.

Total cache hit rate: 88%. Monthly LLM cost: $3,600 -> $400 (-89%).

## 6-Month Production Results

| Metric | Before | After |
|--------|--------|-------|
| Speed-to-lead | 15-45 minutes | <60 seconds |
| Monthly LLM cost | $3,600 | $400 |
| Orchestration overhead | N/A | <200ms (P99: 0.095ms) |
| Context loss on handoffs | Frequent | 0% |
| Automated tests | 0 | 5,100+ |
| Pipeline managed | N/A | $50M+ |
| Compliance violations | Not tracked | 0 |

The speed-to-lead improvement had the largest business impact. Leads that receive a response within 60 seconds convert at significantly higher rates than those waiting 15+ minutes.

## Key Takeaways

1. **Enhance the CRM, don't replace it.** Building on top of GHL meant zero workflow disruption and kept the CRM team happy.

2. **Compliance is not optional.** TCPA, FHA, CCPA, SB 243 -- these aren't nice-to-haves. A single violation can cost more than the entire system.

3. **Cache before you optimize prompts.** 89% of our cost reduction came from caching, not prompt engineering.

4. **Tag-based routing is simple and powerful.** GHL's tag system provided a natural abstraction for bot activation and workflow triggers.

5. **Test at the integration boundary.** The GHL API has quirks (rate limiting, field format requirements, webhook timing). Integration tests caught issues unit tests missed.

## Try It

Full source code: [github.com/ChunkyTortoise/EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub)

If you're building AI on GHL, I'm happy to discuss architecture approaches. The GHL API has patterns that work well with AI orchestration and patterns that will bite you.

---

*Building CRM integrations with AI? Connect on [LinkedIn](https://linkedin.com/in/caymanroden) or check my [other projects](https://github.com/ChunkyTortoise).*
