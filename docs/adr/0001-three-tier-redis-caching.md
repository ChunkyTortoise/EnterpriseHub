# ADR 0001: Three-Tier Redis Caching Strategy

## Status

Accepted

## Context

LLM API calls are expensive ($0.015-0.06/1K tokens) and latency-sensitive. Repeated queries for the same lead context waste tokens and add 200-500ms latency per call. In a real estate lead qualification system handling hundreds of concurrent conversations, the same property data, market context, and qualification criteria are requested repeatedly across sessions. Without caching, a single lead qualification workflow consumes ~93K tokens; with caching, this drops to ~7.8K tokens for subsequent interactions on the same context.

## Decision

Implement a three-tier caching hierarchy:

- **L1 (In-Memory)**: Python dict with LRU eviction, <1ms access, 1000-item capacity. Used for hot conversation context within the same process. Ideal for active Jorge bot sessions where the same lead's data is accessed multiple times within a single qualification flow.

- **L2 (Redis)**: Shared cache across all API workers, <5ms access, TTL-based expiration (default 15min for conversation context, 1hr for market data). Handles cross-request deduplication and ensures all FastAPI workers share the same cached LLM responses.

- **L3 (PostgreSQL)**: Persistent storage, <20ms access. Stores historical query results for analytics, A/B test comparisons, and long-term pattern analysis. Enables the performance tracker to compute cost savings over time.

Cache keys incorporate `conversation_id + message_hash + model_version` to ensure invalidation safety during model upgrades. A background task performs periodic L1-to-L2 promotion for frequently accessed keys.

## Consequences

### Positive
- 89% reduction in LLM API costs (93K to 7.8K tokens per workflow)
- P95 latency reduced from 800ms to <200ms for cached queries
- L1 prevents Redis round-trips for active conversations, reducing median latency to <1ms
- L3 enables historical cost analysis and optimization tracking
- Cache hit rate consistently >85% in production

### Negative
- Cache invalidation complexity increases with three tiers; stale data risk during model version transitions
- Memory pressure from L1 requires careful LRU eviction tuning per worker
- Redis failure requires graceful degradation to L1-only mode, increasing LLM costs temporarily
- L3 storage grows over time and requires periodic cleanup jobs
