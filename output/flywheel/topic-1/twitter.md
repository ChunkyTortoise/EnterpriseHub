# Twitter/X Thread: LLM Cost Optimization with 3-Tier Caching

**Topic**: LLM Cost Optimization
**Format**: 7-tweet thread
**CTA**: GitHub repo link

---

## Tweet 1 (Hook)

Our AI agent was burning $12K/month on Claude API calls.

500 active leads. 3 bots. 6,000 daily interactions.

We cut it to $1,300/month with a 3-tier caching strategy.

Here's the full breakdown:

[thread]

---

## Tweet 2 (Problem)

The problem: every conversation turn hit the API.

- Lead scoring: 2,000 tokens
- Intent classification: 1,500 tokens
- Response generation: 3,000 tokens
- Memory retrieval: 1,000 tokens

= 7,500 tokens per interaction
= $12K/month at Claude pricing

---

## Tweet 3 (Insight)

We logged 10,000 queries over 7 days.

The data:
- 74% referenced the last 10 messages
- 14% referenced the last 100 messages
- Only 12% needed full semantic search

90% of queries were "what did I just say?" not "what have we discussed over 3 weeks?"

---

## Tweet 4 (Solution)

So we built a 3-tier cache:

L1 (RAM): Last 10 messages. <1ms. 74% hit rate.
L2 (Redis): Last 100 messages. <5ms. 14% hit rate.
L3 (Postgres+pgvector): Full history. <50ms. 12% hit rate.

88% of queries never touch the LLM.

---

## Tweet 5 (Results)

30-day production results:

Cost: $12K -> $1,300 (-89%)
Cost/lead: $24 -> $2.60
P95 latency: 180ms -> 4.8ms
Conversion: +7%

The conversion boost was unexpected -- sub-200ms SMS responses feel instant. 1.2s feels like a bot.

---

## Tweet 6 (Lessons)

3 hard-won lessons:

1. Start with Redis (L2), not in-memory. L2 gave 80% of the value.

2. Monitor cache FRESHNESS, not just hit rates. Stale cache = wrong scores.

3. Set TTLs by data volatility. Market context = 60 min. Lead intent = 5 min.

---

## Tweet 7 (CTA)

Before you fine-tune a model or build RAG -- check if it's a caching problem.

Full architecture + production code:
github.com/ChunkyTortoise/EnterpriseHub

Open source. MIT license. Questions? Reply or DM.
