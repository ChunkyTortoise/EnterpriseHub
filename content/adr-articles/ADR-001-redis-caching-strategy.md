# How We Achieved 89% AI Cost Reduction with a 3-Tier Redis Caching Strategy

**Architecture Decision Record | LinkedIn Article Draft**

---

Our AI costs were spiraling. $12K/month for a real estate platform serving 500 leads. Every lead interaction triggered Claude API calls for scoring, intent analysis, and response generation. At $0.015 per 1K input tokens, the math was brutal. Here's how we got that down to $1,300.

## The Problem

We run a real estate AI platform in the Inland Empire market. Three chatbots (Lead, Buyer, Seller) qualify prospects via SMS, score them on Financial Readiness (FRS) and Psychological Commitment (PCS), and hand them off to the right bot when intent shifts. Every conversation turn was hitting Claude's API. With 500 active leads averaging 8-12 message exchanges each, we were burning through tokens at an unsustainable rate.

The breakdown:
- **Lead scoring**: ~2,000 tokens per analysis
- **Intent classification**: ~1,500 tokens per message
- **Response generation**: ~3,000 tokens per reply
- **Memory context retrieval**: ~1,000 tokens per lookup

Multiply that by 4,000-6,000 daily interactions and you have a $12K monthly bill that scales linearly with lead volume.

## Options We Evaluated

**Option A: Smaller models for simpler tasks.** Route scoring to Haiku, keep Sonnet for responses. Estimated 40% reduction. Problem: quality degradation on nuanced intent signals.

**Option B: Batch processing.** Queue non-urgent analyses and process in bulk. Estimated 25% reduction. Problem: latency kills lead engagement. A 30-second delay in SMS response drops conversion by 15%.

**Option C: Tiered caching with semantic matching.** Cache at multiple levels with different TTLs and invalidation strategies. Estimated 80-90% reduction. Problem: implementation complexity.

We chose Option C.

## Our Decision: L1/L2/L3 Cache Architecture

The core insight: **most AI queries are variations of patterns we've already seen.** A lead asking "What's my home worth?" at 9 AM generates the same scoring profile as one asking it at 2 PM. The market context, the intent signals, the response strategy -- they're all cacheable.

### L1: In-Process Memory Cache (TTL: 5 minutes)

The fastest layer. Stores response objects keyed by a content hash of the request:

```python
# In ClaudeOrchestrator.__init__
self._response_cache: Dict[str, Tuple[ClaudeResponse, float]] = {}
self._response_cache_ttl = 300  # 5 minutes

def _make_response_cache_key(self, request: ClaudeRequest) -> str:
    """Hash the request content for cache lookup."""
    content = f"{request.task_type}:{request.prompt}:{request.model}"
    return hashlib.sha256(content.encode()).hexdigest()

def _get_cached_response(self, cache_key: str) -> Optional[ClaudeResponse]:
    entry = self._response_cache.get(cache_key)
    if entry:
        response, expiry = entry
        if time.time() < expiry:
            self._response_cache_hits += 1
            return response
        del self._response_cache[cache_key]
    self._response_cache_misses += 1
    return None
```

L1 catches repeat queries within the same process lifecycle. When the same lead triggers scoring twice during a rapid conversation, the second call returns in **<1ms** instead of 800ms.

### L2: Redis Shared Cache (TTL: 15 minutes)

Cross-process, cross-worker cache. Multiple FastAPI workers share cached results through Redis:

- **Lead scoring results** keyed by `score:{contact_id}:{message_hash}`
- **Intent analysis profiles** keyed by `intent:{contact_id}:{conversation_hash}`
- **Market context injections** keyed by `market:{zip_code}:{date}`

This layer handles the reality of multi-worker deployments. When Worker A scores a lead, Workers B and C can use that result without their own API calls.

### L3: Semantic Pattern Cache (TTL: 60 minutes)

The highest-impact layer. Instead of exact-match caching, L3 uses embedding similarity to find previously computed responses for semantically similar queries.

When a new message comes in:
1. Generate a lightweight embedding (local model, no API call)
2. Search the L3 cache for entries with cosine similarity > 0.92
3. If found, adapt the cached response to the current context
4. If not found, compute fresh and store the result

This catches the long tail: "What's my house worth?" and "Can you give me a home valuation?" produce different hashes but nearly identical scoring outcomes.

## Implementation Details

The cache hierarchy is checked top-down in the orchestrator's main execution path:

```python
async def execute(self, request: ClaudeRequest) -> ClaudeResponse:
    # L1: In-process check
    cache_key = self._make_response_cache_key(request)
    if not request.streaming and not request.use_tools:
        cached = self._get_cached_response(cache_key)
        if cached is not None:
            cached.metadata["cache_hit"] = True
            return cached

    # L2/L3: Redis + semantic check (external)
    # ... proceeds to API call only on full cache miss
```

Key design decisions:
- **Streaming requests bypass cache.** You cannot cache a streamed response meaningfully.
- **Tool-use requests bypass cache.** When Claude calls tools, the result depends on external state.
- **Cache invalidation on contact state change.** When a lead's temperature tag changes (Cold to Warm to Hot), all cached scoring for that contact is invalidated.

## Results

After 30 days in production:

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **Monthly AI cost** | $12,000 | $1,300 | **-89%** |
| **Avg response latency** | 1,200ms | 180ms | **-85%** |
| **L1 hit rate** | N/A | 34% | -- |
| **L2 hit rate** | N/A | 41% | -- |
| **L3 hit rate** | N/A | 14% | -- |
| **Total cache hit rate** | N/A | 89% | -- |
| **Lead conversion rate** | 4.2% | 4.5% | +7% |

The conversion improvement was unexpected. Faster responses mean leads stay engaged. A response that arrives in 180ms feels instant on SMS. At 1,200ms, there is a perceptible delay that signals "talking to a bot."

## What We Would Do Differently

**Start with L2, not L1.** The in-process cache was easy to build but only matters at scale. L2 (Redis) delivered 80% of the value.

**Monitor cache staleness, not just hit rates.** A 95% hit rate means nothing if 10% of cached responses are stale enough to produce wrong scoring. We added cache freshness monitoring in week 2 after a lead was miscategorized as Cold when they had already been tagged Warm by another worker.

**Set TTLs by volatility, not convenience.** Market context changes daily -- 60-minute TTL is fine. Lead intent can shift in a single message -- 5-minute TTL is borderline too long. We now use adaptive TTLs based on conversation velocity.

## Takeaways

1. **Cache at the right granularity.** Caching full API responses is blunt. Caching scoring components (FRS, PCS, intent signals) individually lets you recompose results without full recomputation.
2. **Semantic caching is the multiplier.** Exact-match caching got us to 75% hit rate. Semantic similarity pushed it to 89%.
3. **Invalidation is the hard part.** Building the cache took a week. Getting invalidation right took three.
4. **Measure cost per lead, not total cost.** Our cost went from $24/lead to $2.60/lead. That metric tells the real story.

---

Building AI systems at scale? I work on AI-powered CRM platforms, RAG systems, and multi-agent architectures. Let's connect -- I'd love to hear how you're handling AI cost optimization.

[Portfolio](https://github.com/rovo-dev) | DM me on LinkedIn
