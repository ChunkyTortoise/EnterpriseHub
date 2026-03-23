# LinkedIn Post: LLM Cost Optimization with 3-Tier Caching

**Topic**: LLM Cost Optimization
**Format**: LinkedIn post (300-500 words)
**CTA**: Engagement question + GitHub link

---

Our AI agent was burning $12K/month on API calls. 500 active leads, 3 bots, 4,000-6,000 daily interactions.

Every conversation turn hit Claude's API: scoring, intent analysis, response generation, memory retrieval. That's 7,500+ tokens per interaction.

We evaluated three approaches:

A) Route simpler tasks to cheaper models. ~40% savings. Problem: quality degradation on nuanced intent signals.

B) Batch processing. ~25% savings. Problem: 30-second SMS delays drop conversion by 15%.

C) 3-tier caching with semantic matching. 80-90% estimated savings.

We built option C. Here's the architecture:

L1 (In-Process): Last 10 messages per user. <1ms retrieval. 74% hit rate.
L2 (Redis): Last 100 messages. Shared across workers. <5ms retrieval. 14% hit rate.
L3 (Postgres + pgvector): Full history. Semantic search. <50ms retrieval. 12% hit rate.

The key insight: 90% of agent memory lookups reference recent messages. "What did I just say?" not "What have we discussed over 3 weeks?"

That means TTL-based caches handle the vast majority of queries without touching the LLM or database.

Results after 30 days in production:

- Monthly cost: $12,000 -> $1,300 (89% reduction)
- Cost per lead: $24 -> $2.60
- P95 latency: 180ms -> 4.8ms
- Cache hit rate: 88%
- Lead conversion: +7% (faster responses keep leads engaged)

The unexpected win: conversion improved because sub-200ms response times feel instant on SMS. At 1.2 seconds, there's a perceptible delay that signals "talking to a bot."

Three lessons from building this:

1. Start with Redis (L2), not in-memory (L1). L2 delivered 80% of the value.

2. Monitor cache freshness, not just hit rates. A 95% hit rate is worthless if 10% of cached responses are stale.

3. Set TTLs by data volatility. Market context = 60 min. Lead intent = 5 min (can shift in one message).

Before building complex RAG systems or fine-tuning models, check if your problem is actually a caching problem.

Full architecture + code: github.com/ChunkyTortoise/EnterpriseHub

What's your biggest LLM cost driver? Token volume? Provider pricing? Something else?

#AIEngineering #LLMOps #CostOptimization #MachineLearning #Python #Redis
