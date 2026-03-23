# Reddit Post: LLM Cost Optimization with 3-Tier Caching

**Topic**: LLM Cost Optimization
**Subreddit**: r/MachineLearning (or r/Python for broader reach)
**Format**: Technical discussion post with data
**Flair**: [Project] or [Discussion]

---

## Title

I cut our LLM API costs by 89% ($12K -> $1.3K/month) with a 3-tier caching strategy. Here are the architecture details and production metrics.

## Body

**tl;dr**: We built a 3-tier cache (in-memory / Redis / Postgres+pgvector) for our AI-powered lead qualification system. 88% cache hit rate, 89% cost reduction, 97% latency improvement. Full code is open source.

---

**Context**: We run a real estate platform with 3 specialized chatbots (Lead, Buyer, Seller) that qualify prospects via SMS. Each conversation turn triggers 4 API calls to Claude: scoring, intent classification, response generation, memory retrieval. ~7,500 tokens per interaction, 4,000-6,000 interactions/day, $12K/month.

**The key insight**: We instrumented 10,000 queries and found that 90% of memory lookups reference the last 10-100 messages. Most users ask sequential questions ("what did you just say?"), not semantic queries ("what have we discussed over 3 weeks?").

**Architecture**:

```
Query -> L1 (in-process, <1ms, 74% hit)
      -> L2 (Redis, <5ms, 14% hit)
      -> L3 (Postgres+pgvector, <50ms, 12%)
```

- **L1**: OrderedDict with LRU eviction, last 10 messages per user, 5-min TTL. Per-worker-process.
- **L2**: Redis with structured keys (`score:{contact_id}:{hash}`, `intent:{contact_id}:{hash}`), 15-min TTL. Shared across workers.
- **L3**: pgvector semantic search with cosine similarity > 0.92 threshold. Catches "What's my home worth?" matching to "Can you give me a home valuation?" -- different hashes, same scoring outcome.

**Design decisions**:
- Streaming and tool-use requests bypass cache entirely (results depend on external state)
- Cache invalidation on contact state change (Cold -> Warm -> Hot)
- TTLs set by data volatility: market context = 60 min, lead scoring = 15 min, intent = 5 min
- L1/L2 backfill on L3 hits to prevent repeat deep lookups

**30-day production results**:

| Metric | Before | After |
|--------|--------|-------|
| Monthly cost | $12,000 | $1,300 |
| Cost/lead | $24 | $2.60 |
| P95 latency | 180ms | 4.8ms |
| Cache hit rate | 0% | 88% |
| Lead conversion | 4.2% | 4.5% |

The conversion improvement (+7%) was unexpected. Sub-200ms SMS response times feel instant; at 1.2s there's a perceptible delay.

**Lessons learned**:
1. Start with L2 (Redis), not L1. Redis delivered 80% of the value because it's shared across workers.
2. Cache scoring components individually (FRS, PCS, intent), not full responses. This let us recompose results and pushed hit rate from 75% -> 89%.
3. Cache invalidation took 3x longer than building the cache. Stale scores caused a lead miscategorization in week 2.

**What we'd do differently**: Adaptive TTLs from day 1. Conversation velocity should drive TTL length -- fast-moving conversations need shorter TTLs.

**Code**: [github.com/ChunkyTortoise/EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub) (MIT license)

Run locally: `docker compose up -d && python benchmarks/memory_performance.py`

Happy to answer questions about the implementation, scaling considerations, or how the semantic caching layer works in practice.
