# Week 4: Production Orchestration (EnterpriseHub)

## Overview

This week is about production hardening. Students add caching, rate limiting, error handling, and CRM integration to an AI orchestration platform. This is where demos become products.

**Repo**: EnterpriseHub
**Lab**: Add caching, rate limiting, and error handling to an AI platform

## Learning Objectives

By the end of this week, students will be able to:
1. Implement L1/L2/L3 caching for LLM calls with intelligent invalidation
2. Build rate-aware API clients that respect external service limits
3. Design multi-strategy output parsing with fallback chains
4. Integrate with external CRM systems handling webhooks and field mapping
5. Measure and report on cache hit rates and cost reduction

## Session A: Concepts + Live Coding (Tuesday)

### Part 1: Production AI Patterns (15 min)

**The 5 pillars of production AI:**
1. **Caching**: Don't call the LLM if you already have the answer
2. **Rate limiting**: Respect your dependencies' limits
3. **Error handling**: Degrade gracefully, never crash silently
4. **Output parsing**: Don't trust raw LLM output
5. **Observability**: Measure everything (covered in Week 5)

**Cost analysis:**
- Uncached: 10K requests/day x $0.03/request = $300/day = $9K/month
- 89% cached: 1.1K LLM calls/day x $0.03 = $33/day = $1K/month
- Savings: $8K/month = $96K/year from a single caching layer

### Part 2: Live Coding — L1/L2/L3 Cache (45 min)

1. **Cache architecture** (10 min)
   - L1: In-memory (dict/LRU, <1ms, per-process, lost on restart)
   - L2: Redis (5ms, shared across instances, TTL-based)
   - L3: PostgreSQL (50ms, persistent, queryable, analytics)
   - Lookup order: L1 → L2 → L3 → LLM call → write back to all levels

2. **Cache key design** (10 min)
   - Key components: model, system prompt hash, user message hash, parameters
   - Collision avoidance: include temperature, max_tokens in key
   - Versioning: prefix keys with model version for cache busting

3. **Implementation** (15 min)
   - Build the cache lookup chain
   - Implement write-through (write to all levels on miss)
   - Add TTL management (L1: 5min, L2: 1hr, L3: 24hr)
   - Cache invalidation strategies

4. **Rate-aware API client** (10 min)
   - Token bucket algorithm for rate limiting
   - Backoff with jitter on 429 responses
   - Queue overflow handling
   - Per-endpoint rate limits (GoHighLevel: 10 req/s)

### Part 3: Lab Introduction (15 min)

- Lab 4 README walkthrough
- Starter code: bare AI orchestrator without caching or rate limiting
- Autograder: cache hit rate > 70% on test workload, no rate limit violations
- Bonus: CRM webhook handler

### Part 4: Q&A (15 min)

## Session B: Lab Review + Deep Dive (Thursday)

### Part 1: Lab Solution Review (20 min)

Common patterns and mistakes:
- Cache key not including all relevant parameters (stale responses)
- Missing TTL on L1 cache (unbounded memory growth)
- Rate limiter that blocks instead of queues (latency spikes)
- Not measuring cache hit rate (can't optimize what you don't measure)

### Part 2: Deep Dive — CRM Integration (40 min)

**GoHighLevel integration patterns:**
- Webhook handling: receive contact updates, opportunity changes
- Field mapping: CRM fields to application models
- Rate limiting: 10 requests/second, queue beyond that
- Error handling: retry on 5xx, skip on 4xx, alert on repeated failures

**Multi-strategy output parsing:**
- Strategy 1: JSON extraction (regex for JSON blocks in text)
- Strategy 2: Structured regex (key: value patterns)
- Strategy 3: Key-value extraction (flexible delimiter matching)
- Strategy 4: Re-prompt (ask the LLM to fix its output)
- Metrics: track which strategy succeeds and how often

**Circuit breaker pattern:**
- When an external service is down, stop calling it
- States: closed (normal) → open (blocking) → half-open (testing)
- Prevents cascading failures across your system
- Implementation with configurable thresholds

### Part 3: Production Case Study (20 min)

EnterpriseHub in production:
- $50M+ pipeline managed through AI orchestration
- 89% cache hit rate across 3 cache levels
- Jorge bots handling lead qualification with handoff protocols
- Agent mesh coordinating 4.3M dispatches/sec
- How monitoring caught a cache invalidation bug before it affected users

### Part 4: Week 5 Preview (10 min)

## Key Takeaways

1. Caching is the highest-ROI optimization for AI systems (89% = 8x cost reduction)
2. Cache keys must include all parameters that affect the response
3. Rate limiting protects you and your dependencies — never skip it
4. Output parsing needs fallbacks — the happy path isn't enough
5. CRM integration is a rate-limited, webhook-driven, eventually-consistent system

## Resources

- EnterpriseHub repository (services/claude_orchestrator.py)
- Redis documentation (caching patterns)
- GoHighLevel API documentation
- "Caching Strategies for AI Systems" (course materials)
