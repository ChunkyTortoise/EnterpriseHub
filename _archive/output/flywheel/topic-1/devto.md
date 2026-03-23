---
title: "How We Cut LLM Costs by 89% Without Sacrificing Quality: A 3-Tier Caching Architecture"
published: false
tags: python, ai, llm, optimization, redis
cover_image:
canonical_url:
---

# How We Cut LLM Costs by 89% Without Sacrificing Quality: A 3-Tier Caching Architecture

Our AI platform was hemorrhaging money. $12,000/month in Claude API calls for a real estate lead qualification system serving 500 active leads. Three specialized chatbots -- Lead, Buyer, Seller -- each consuming tokens for scoring, intent analysis, and response generation on every single conversation turn.

After implementing a 3-tier caching strategy, we dropped to $1,300/month. Same features. Same quality. Better conversion rates.

This is the technical breakdown of how we built it, what went wrong, and the metrics after 30 days in production.

---

## The Problem: Linear Cost Scaling

Our system has three chatbots that qualify real estate prospects via SMS. Each conversation turn triggers multiple API calls:

| Operation | Tokens per Call | Frequency |
|-----------|----------------|-----------|
| Lead scoring (FRS/PCS) | ~2,000 | Every message |
| Intent classification | ~1,500 | Every message |
| Response generation | ~3,000 | Every message |
| Memory context retrieval | ~1,000 | Every message |

With 500 active leads averaging 8-12 message exchanges, that's 4,000-6,000 daily interactions at ~7,500 tokens each. At $0.015/1K input tokens: **$12,000/month**.

The cost scaled linearly with lead volume. Double the leads, double the bill.

## The Insight: Memory Access Patterns

Before optimizing, we instrumented the system to log every memory access for 7 days (10,000 queries):

```python
memory_access_patterns = {
    "last_10_messages": 7420,     # 74.2%
    "last_100_messages": 1410,    # 14.1%
    "full_history_search": 1170   # 11.7%
}
```

**Key finding**: 90% of queries reference recent messages. Most users ask "What did you just say?" or "Earlier you mentioned..." -- not "What have we discussed over the past 3 weeks?"

This meant a TTL-based cache could intercept the vast majority of queries before they hit the LLM.

## The Architecture: L1 / L2 / L3

```
User Query
     |
     v
[L1: In-Process Cache]  -- 74% hit rate, <1ms
     | (miss)
     v
[L2: Redis Cache]        -- 14% hit rate, <5ms
     | (miss)
     v
[L3: Postgres + pgvector] -- 12% of queries, <50ms
```

### L1: In-Process Memory (TTL: 5 minutes)

The fastest layer. Each FastAPI worker keeps the last 10 messages per user in an `OrderedDict` with LRU eviction:

```python
class InProcessCache:
    def __init__(self, max_size: int = 1000):
        self._cache = OrderedDict()
        self._max_size = max_size

    def get(self, user_id: str) -> list[dict] | None:
        if user_id in self._cache:
            self._cache.move_to_end(user_id)
            return self._cache[user_id]
        return None

    def set(self, user_id: str, messages: list[dict]):
        if len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)
        self._cache[user_id] = messages[-10:]
        self._cache.move_to_end(user_id)
```

L1 catches repeat queries within the same process -- when a lead triggers scoring twice during a rapid conversation, the second call returns in <1ms.

### L2: Redis Shared Cache (TTL: 15 minutes)

Cross-process, cross-worker cache. Multiple FastAPI workers share cached results:

```python
class RedisCache:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=True)

    async def get(self, user_id: str) -> list[dict] | None:
        cached = await self.redis.get(f"messages:{user_id}")
        return json.loads(cached) if cached else None

    async def set(self, user_id: str, messages: list[dict]):
        await self.redis.setex(
            f"messages:{user_id}",
            900,  # 15 minutes
            json.dumps(messages[-100:])
        )
```

Cache keys are structured by purpose: `score:{contact_id}:{message_hash}`, `intent:{contact_id}:{conversation_hash}`, `market:{zip_code}:{date}`.

### L3: Semantic Pattern Cache (TTL: 60 minutes)

The highest-impact layer. Instead of exact-match caching, L3 uses embedding similarity to find previously computed responses for semantically similar queries:

```python
async def semantic_search(self, user_id: str, query: str, limit: int = 10):
    query_embedding = await self.embed_text(query)
    results = await self.db.fetch("""
        SELECT content, role, timestamp, metadata
        FROM messages
        WHERE user_id = $1
        ORDER BY embedding <-> $2::vector
        LIMIT $3
    """, user_id, query_embedding, limit)
    return [dict(r) for r in results]
```

This catches the long tail: "What's my home worth?" and "Can you give me a home valuation?" produce different hashes but nearly identical scoring outcomes.

### Unified Interface

```python
class AgentMemory:
    def __init__(self):
        self.l1 = InProcessCache()
        self.l2 = RedisCache()
        self.l3 = PostgresCache(DATABASE_URL)

    async def get_context(self, user_id: str, query: str, limit: int = 10):
        # L1: In-process check
        messages = self.l1.get(user_id)
        if messages and len(messages) >= limit:
            return messages[-limit:]

        # L2: Redis check
        messages = await self.l2.get(user_id)
        if messages:
            self.l1.set(user_id, messages)  # Backfill L1
            return messages[-limit:]

        # L3: Semantic search fallback
        messages = await self.l3.semantic_search(user_id, query, limit)
        await self.l2.set(user_id, messages)  # Backfill L2
        self.l1.set(user_id, messages)         # Backfill L1
        return messages
```

## Design Decisions

**Streaming requests bypass cache.** You cannot cache a streamed response meaningfully.

**Tool-use requests bypass cache.** When Claude calls external tools, the result depends on external state that may have changed.

**Cache invalidation on state change.** When a lead's temperature tag changes (Cold -> Warm -> Hot), all cached scoring for that contact is invalidated immediately.

**TTLs by data volatility, not convenience:**
- Market context: 60-minute TTL (changes daily at most)
- Lead scoring: 15-minute TTL (changes with new messages)
- Lead intent: 5-minute TTL (can shift in a single message)

## Results: 30 Days in Production

### Cost

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Monthly AI cost | $12,000 | $1,300 | **-89%** |
| Cost per lead | $24.00 | $2.60 | **-89%** |

### Performance

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| P50 latency | 120ms | 2ms | **-98%** |
| P95 latency | 180ms | 4.8ms | **-97%** |
| P99 latency | 320ms | 48ms | **-85%** |

### Cache Hit Rates

| Tier | Hit Rate | Avg Latency |
|------|----------|-------------|
| L1 (in-process) | 74.2% | 0.8ms |
| L2 (Redis) | 14.1% | 4.2ms |
| L3 (Postgres) | 11.7% | 48.3ms |
| **Total** | **88.3%** | -- |

### Unexpected Win: Conversion

Lead conversion improved by 7% (4.2% -> 4.5%). Faster responses keep leads engaged. A response that arrives in <200ms feels instant on SMS. At 1.2 seconds, there's a perceptible delay that signals "talking to a bot."

## Three Hard-Won Lessons

### 1. Start with Redis (L2), not in-memory (L1)

L1 was easy to build but only matters at scale. L2 (Redis) delivered 80% of the cost savings because it's shared across workers. If you can only build one tier, build L2.

### 2. Monitor cache freshness, not just hit rates

A 95% hit rate means nothing if 10% of cached responses are stale. We discovered this in week 2 when a lead was miscategorized as Cold after they had been tagged Warm by another worker. Added freshness monitoring and adaptive TTLs based on conversation velocity.

### 3. Cache at the right granularity

Caching full API responses is blunt. Caching scoring components individually (FRS, PCS, intent signals) lets you recompose results without full recomputation. This pushed our effective hit rate from 75% to 89%.

## When You Don't Need This

- **<100 queries/day**: Just send full history. Simplicity beats optimization.
- **Short conversations (<20 messages)**: Context window overhead is negligible.
- **Generous budget**: If you're spending $10K+/month and that's fine, don't add complexity.

This architecture makes sense when you have 1,000+ conversations/day, long conversations (100+ messages), and you're cost-sensitive.

## Try It

Full source code, Docker Compose setup, and benchmark scripts:
[github.com/ChunkyTortoise/EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub)

```bash
git clone https://github.com/ChunkyTortoise/EnterpriseHub.git
cd EnterpriseHub
docker compose up -d
python benchmarks/memory_performance.py
```

---

*Building AI systems at scale? I work on production agent architectures, RAG pipelines, and CRM integrations. Connect on [LinkedIn](https://linkedin.com/in/caymanroden) or check out [my other projects](https://github.com/ChunkyTortoise).*
