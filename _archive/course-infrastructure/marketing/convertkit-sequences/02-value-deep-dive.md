# Email 2: Value Deep-Dive

**Trigger**: 7 days after social proof email (D-14 before enrollment)
**From**: Cave <cave@productionai.dev>

---

**Subject**: Free lesson: Why 90% of AI demos fail in production

**Preview text**: The 5 things that break when you ship an AI system for real.

---

Hey {first_name},

I promised you a preview of the course. Here it is — a condensed version of what I teach in Week 4: Production Hardening.

**Why 90% of AI demos fail in production:**

**1. No caching strategy**

Every LLM call costs money and takes time. Without caching, your costs scale linearly with usage and your latency is unpredictable.

In EnterpriseHub, we use a 3-tier cache (L1: in-memory, L2: Redis, L3: PostgreSQL) that achieves an 89% hit rate. That means 89% of requests never touch the LLM at all.

In the course, you'll implement this exact caching layer and measure the cost reduction.

**2. No structured output handling**

LLMs return strings. Your application needs structured data. The gap between "it usually returns valid JSON" and "it always returns valid JSON" is where production systems live.

You'll build a multi-strategy parser that tries JSON extraction first, falls back to regex patterns, then to key-value extraction, and finally to a re-prompting strategy. The same system that handles 4.3M dispatches/sec in production.

**3. No error budget**

"It works most of the time" is not a production standard. You'll define SLAs (P50 < 100ms, P95 < 500ms, P99 < 2s), build a performance tracker to measure them, and set up alerting when you breach them.

**4. No rate limiting at the integration boundary**

Your system talks to external APIs (LLMs, CRMs, databases). Each has rate limits. You'll implement rate-aware clients that respect these limits, queue overflow, and degrade gracefully under load.

**5. No observability**

If you can't measure it, you can't improve it. You'll instrument your AI system with structured logging, latency histograms, cache hit counters, and anomaly detection — then visualize it all in a Streamlit dashboard.

**This is one week of six.** Each week goes this deep into a different aspect of production AI.

Enrollment opens in 2 weeks. Beta pricing ($797 instead of $1,297) is reserved for the first 20 students.

If this resonated with you, reply with "I'm in" and I'll make sure you get first access when enrollment opens.

Cave

P.S. — Want to see these patterns in actual code? The repos are open-source. But knowing which patterns to apply and how they fit together — that's what the course teaches.

---

**CTA Button**: "Reply: I'm in" (no link, encourages reply for engagement)
**ConvertKit automation**: If subscriber replies, add tag "high-intent"
**Tags to add**: None
**Tags to remove**: None
