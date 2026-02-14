# How I Built a Production AI Lead Qualification System on GoHighLevel

**Platform**: GHL Facebook Group / r/gohighlevel
**Tone**: Educational, technical, honest about trade-offs
**Length**: ~1,500 words (long-form community post)

---

## Post Content

**Title**: How I Built a Production AI Lead Qualification System on GoHighLevel

I've been working on an AI-powered lead qualification system that runs entirely on top of GoHighLevel for a real estate brokerage in the Inland Empire (Rancho Cucamonga, CA). After 6 months in production, I wanted to share the architecture, what worked, what didn't, and the actual numbers.

This is NOT a pitch. I just think more people in the GHL community should be building this kind of thing, and I want to save you the mistakes I made.

---

### The Problem

The brokerage was handling ~200 inbound leads/month across buyers, sellers, and general inquiries. Their bottleneck wasn't generating leads -- it was qualifying them fast enough. Speed-to-lead was measured in hours, not minutes. By the time a human agent followed up, half the leads had gone cold.

They needed:
- Instant response to every inbound lead (< 60 seconds)
- Automatic routing to the right conversation (buyer vs. seller vs. general)
- Temperature scoring so agents focus on hot leads first
- All of it synced back to GHL so existing workflows still work

---

### The Architecture

Here's how the system is structured:

```
Inbound Lead (GHL Webhook)
         |
         v
   FastAPI Orchestrator
         |
    +-----------+-----------+
    |           |           |
    v           v           v
 Lead Bot   Buyer Bot   Seller Bot
 (Qualify)  (Financial) (Property)
    |           |           |
    +-----+-----+-----+----+
          |           |
          v           v
   Intent Decoder   Handoff Service
   (GHL-Enhanced)   (Tag-Based Routing)
          |           |
          v           v
   GHL Contact API   GHL Tags + Workflows
   (Temperature Tags) (Activation Routing)
```

Each bot is a specialized AI agent backed by Claude. The Lead Bot handles initial qualification. When it detects buyer intent ("I want to buy", "budget is $X", "pre-approved"), it hands off to the Buyer Bot. Same for seller intent ("sell my home", "what's my home worth", "CMA").

**The key insight**: handoffs are done entirely through GHL tags. The Lead Bot removes its own activation tag ("Needs Qualifying") and adds the target bot's tag ("Buyer-Lead"). The next inbound message routes to the correct bot via GHL's existing tag-based workflow triggers. No custom routing infrastructure needed -- GHL handles it natively.

---

### The Intent Detection System

We built intent decoders that combine two signal sources:

**1. Pattern matching** on the current message:
- Buyer patterns: budget mentions, pre-approval references, "find me a home"
- Seller patterns: CMA requests, "home value", "list my property"
- Each pattern match adds 0.3 to the confidence score (capped at 1.0)

**2. GHL contact data enrichment**:
- Tag history (has "Pre-Approved" tag? Boost buyer score)
- Lead age (newer leads get urgency boost)
- Engagement recency (active in last 48h? Higher priority)
- Pipeline stage (already in buyer pipeline? Skip re-qualification)

The GHL-enhanced decoder consistently outperforms the standalone version because it has context the conversation alone can't provide.

---

### Handoff Safeguards (The Hard Lessons)

Early on, we hit a nasty bug: the buyer bot would detect seller intent, hand off to the seller bot, which would detect buyer intent, and hand back. Infinite loop. The contact got 15 handoffs in 20 minutes before we caught it.

Here's what we built to prevent it:

**Circular prevention**: Same source-to-target handoff blocked within a 30-minute window. If Lead Bot already sent a contact to Buyer Bot, it can't do it again for 30 minutes.

**Rate limiting**: Max 3 handoffs per hour, 10 per day, per contact. Hard cap. No exceptions.

**Conflict resolution**: Contact-level locking prevents two bots from trying to hand off the same contact simultaneously. Lock expires after 30 seconds if something crashes.

**Pattern learning**: After collecting 10+ handoff outcomes for a route (e.g., lead-to-buyer), the system adjusts its confidence threshold. If 80%+ of lead-to-buyer handoffs succeed, the threshold drops from 0.7 to 0.65 (easier to trigger). If less than 50% succeed, it rises to 0.8 (harder to trigger). The system literally learns which handoffs work.

---

### Temperature Scoring + GHL Tag Publishing

Every lead gets a temperature score based on qualification signals:

| Score | Tag | What Happens in GHL |
|-------|-----|-------------------|
| 80+ | Hot-Lead | Priority workflow fires, agent gets notified immediately |
| 40-79 | Warm-Lead | Nurture sequence starts, follow-up reminder in 24h |
| < 40 | Cold-Lead | Educational drip campaign, check-in at 7 days |

These tags drive GHL workflows directly. The human agents never need to check a separate dashboard -- their existing GHL pipeline view shows lead temperature via tags.

---

### The Numbers (After 6 Months)

| Metric | Before | After |
|--------|--------|-------|
| Speed to first response | 2-4 hours | < 60 seconds |
| Lead qualification rate | ~30% (manual) | ~75% (automated) |
| AI response latency (P95) | N/A | < 200ms |
| Cache hit rate | N/A | 88% |
| LLM cost per lead | N/A | ~$0.003 (with caching) |
| Monthly LLM spend | N/A | 89% below initial projections |

The 88% cache hit rate is the real cost saver. We use a 3-tier cache: L1 (in-process memory, ~1ms), L2 (Redis, ~5ms), L3 (PostgreSQL for long-term patterns). Most qualification questions are variations of the same themes, so cached responses handle the majority of traffic.

---

### What Didn't Work

**Over-engineering the qualification flow**. We initially had a 10-question qualification sequence. Leads dropped off by question 4. We cut it to 3-4 contextual questions and saw completion rates jump.

**Ignoring GHL's native capabilities**. We tried building custom routing before realizing GHL's tag-based workflows already do most of what we needed. The lesson: work WITH the platform, not around it.

**Generic AI responses**. Early versions used generic real estate prompts. Performance improved dramatically when we injected local market context (Rancho Cucamonga median prices, school districts, commute times) into the system prompts.

---

### Tech Stack

- **Backend**: FastAPI (async Python) -- handles GHL webhooks, orchestrates bots
- **AI**: Claude API (Sonnet for standard queries, Opus for complex analysis)
- **Database**: PostgreSQL (lead data, handoff history) + Redis (caching)
- **CRM**: GoHighLevel (contacts, tags, workflows, pipelines)
- **Monitoring**: Custom alerting with P50/P95/P99 latency tracking, SLA compliance
- **Testing**: 8,500+ automated tests, CI/CD via GitHub Actions

---

### What I'd Do Differently

1. **Start with GHL tags as the routing mechanism from day one**. We wasted 3 weeks building custom routing before realizing tags + workflows handle 90% of it.

2. **Build the handoff safeguards BEFORE going live**. The circular handoff bug was embarrassing and avoidable.

3. **Instrument everything from the start**. We added monitoring late. Having P95 latency data from day one would have caught performance regressions earlier.

4. **Use enriched handoff context sooner**. When a lead hands off from the Lead Bot to the Buyer Bot, passing the qualification score, temperature, and conversation summary means the Buyer Bot doesn't re-ask questions. This cut the buyer qualification flow from 8 turns to 3.

---

### Ask Me Anything

Happy to go deeper on any part of this -- the intent detection patterns, the caching strategy, the GHL integration specifics, whatever. If you're building something similar, I'd genuinely like to hear about your approach too.

---

**Formatting Notes for Posting**:
- GHL Facebook Group: Post as-is, use the built-in formatting. Add the architecture diagram as a comment image (render the mermaid separately).
- Reddit: Use markdown formatting. Flair as "Case Study" or "Discussion" if available.
- Remove the meta-section headers ("Post Content", "Formatting Notes") before posting.
