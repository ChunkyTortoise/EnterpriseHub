---
title: "Building Production Multi-Agent Systems: Lessons from 8,500 Tests"
published: true
description: "Real patterns and hard lessons from deploying AI agents managing a $50M+ real estate pipeline — testing strategies, cache layers, and coordination patterns that actually work."
tags: ai, python, testing, architecture
---

# Building Production Multi-Agent Systems: Lessons from 8,500 Tests

I've spent the last year building EnterpriseHub — a multi-agent AI system that manages lead qualification, buyer consultations, and seller CMAs for a real estate operation handling a $50M+ pipeline. It's live at [ct-enterprise-ai.streamlit.app](https://ct-enterprise-ai.streamlit.app).

The system has 8,500+ tests across 11 repositories. Every repo has CI passing. This isn't a demo — it's production code processing real leads.

Here's what I learned building multi-agent systems that don't fall apart under load.

## The Core Problem: Agents Are Expensive and Slow

LLM API calls cost money and take time. When you're orchestrating multiple agents (Lead Bot → Buyer Bot handoffs, intent analysis, CRM sync), those costs compound fast.

**Early architecture (broken):**
```python
async def process_conversation(message: str, contact_id: str):
    # Every call = fresh API request
    intent = await claude_client.analyze_intent(message)
    response = await claude_client.generate_response(intent, message)
    await ghl_client.update_contact(contact_id, response)
    return response
```

**Cost per conversation:** ~$0.15 (20K tokens @ $15/1M)
**Latency:** 2-4 seconds
**Problem:** Identical conversations re-analyzed every time

## Solution 1: Three-Tier Caching (89% Cost Reduction)

I implemented L1/L2/L3 caching inspired by CPU cache hierarchies:

```python
class ClaudeOrchestrator:
    def __init__(self):
        self.l1_cache = {}  # In-memory, <100 items
        self.l2_cache = Redis(ttl=3600)  # 1 hour
        self.l3_cache = Redis(ttl=86400)  # 24 hours

    async def get_cached_or_call(
        self,
        cache_key: str,
        api_call: Callable,
        tier: int = 2
    ) -> dict:
        # L1: In-memory (fastest)
        if cache_key in self.l1_cache:
            return self.l1_cache[cache_key]

        # L2: Redis short-term (fast)
        if tier >= 2:
            cached = await self.l2_cache.get(cache_key)
            if cached:
                self.l1_cache[cache_key] = cached  # Promote
                return cached

        # L3: Redis long-term (fallback)
        if tier >= 3:
            cached = await self.l3_cache.get(cache_key)
            if cached:
                await self.l2_cache.set(cache_key, cached)
                return cached

        # Cache miss: API call
        result = await api_call()
        await self._populate_caches(cache_key, result, tier)
        return result
```

**Results:**
- 88% cache hit rate in production
- Average latency: 45ms (cached) vs 2,300ms (uncached)
- Cost per conversation: $0.02 (down from $0.15)

**Key insight:** Intent analysis patterns repeat. "I want to buy a house" has the same intent as "looking to purchase property". Cache the analysis, not the raw message.

## Solution 2: Async-First Architecture

Multi-agent systems have natural parallelism. Don't block.

**Bad (sequential):**
```python
async def handle_handoff(message: str, contact_id: str):
    intent = await analyze_intent(message)  # 800ms
    ghl_data = await fetch_ghl_contact(contact_id)  # 300ms
    response = await generate_response(intent, ghl_data)  # 1200ms
    return response  # Total: 2300ms
```

**Good (parallel):**
```python
async def handle_handoff(message: str, contact_id: str):
    # Launch both I/O operations simultaneously
    intent_task = asyncio.create_task(analyze_intent(message))
    ghl_task = asyncio.create_task(fetch_ghl_contact(contact_id))

    # Wait for both to complete
    intent, ghl_data = await asyncio.gather(intent_task, ghl_task)

    # Now use results
    response = await generate_response(intent, ghl_data)
    return response  # Total: 1200ms (shaved 1100ms)
```

**FastAPI makes this natural:**
```python
@app.post("/chat")
async def chat_endpoint(message: str, contact_id: str):
    # FastAPI handles async natively
    return await orchestrator.process_conversation(message, contact_id)
```

## Solution 3: Test Multi-Agent Coordination, Not Just Units

Unit tests are necessary but insufficient. Agent handoffs have edge cases that only appear in integration.

**Handoff scenario that broke in production:**
```python
# Lead Bot thinks user wants to buy
# Buyer Bot gets confused by seller-focused history
# System loops between bots infinitely
```

**Integration test that caught it:**
```python
@pytest.mark.asyncio
async def test_circular_handoff_prevention():
    """Lead Bot → Buyer Bot → Lead Bot should block"""
    contact_id = "test_123"

    # Simulate Lead Bot handoff to Buyer
    result1 = await handoff_service.evaluate_handoff(
        source_bot="lead",
        target_bot="buyer",
        contact_id=contact_id,
        confidence=0.85
    )
    assert result1.should_handoff is True

    # Attempt immediate handoff back to Lead (should block)
    result2 = await handoff_service.evaluate_handoff(
        source_bot="buyer",
        target_bot="lead",
        contact_id=contact_id,
        confidence=0.75
    )
    assert result2.should_handoff is False
    assert "circular" in result2.block_reason.lower()
```

**Real implementation:**
```python
class JorgeHandoffService:
    async def evaluate_handoff(
        self,
        source_bot: str,
        target_bot: str,
        contact_id: str,
        confidence: float
    ) -> HandoffDecision:
        # Check circular handoff within 30min window
        recent = await self._get_recent_handoffs(contact_id, minutes=30)
        if any(h.source == target_bot and h.target == source_bot
               for h in recent):
            return HandoffDecision(
                should_handoff=False,
                block_reason="Circular handoff detected"
            )

        # Rate limiting: 3/hour, 10/day
        if len(recent) >= 3:
            return HandoffDecision(
                should_handoff=False,
                block_reason="Rate limit exceeded"
            )

        # Confidence threshold
        if confidence < 0.7:
            return HandoffDecision(should_handoff=False)

        return HandoffDecision(should_handoff=True)
```

## Solution 4: Observability for Black-Box Failures

LLMs hallucinate. Agents make weird decisions. You need forensics.

**Structured logging:**
```python
import structlog

logger = structlog.get_logger()

async def process_conversation(message: str, contact_id: str):
    logger.info(
        "conversation.started",
        contact_id=contact_id,
        message_length=len(message),
        cache_enabled=True
    )

    try:
        result = await orchestrator.handle_message(message, contact_id)
        logger.info(
            "conversation.completed",
            contact_id=contact_id,
            response_length=len(result.response),
            cache_hit=result.from_cache,
            latency_ms=result.latency
        )
        return result
    except Exception as e:
        logger.error(
            "conversation.failed",
            contact_id=contact_id,
            error=str(e),
            exc_info=True
        )
        raise
```

## What I'd Do Differently

**1. Start with rate limits from day one.** We hit OpenAI's tier limits in production because I didn't anticipate conversation volume.

**2. Version your prompts.** When you update agent instructions, you break existing tests. Store prompts in DB with version IDs.

**3. Test with realistic data volumes.** 100 test conversations ≠ 10,000 real users. Use load testing tools like Locust.

**4. Build admin dashboards early.** I wasted hours debugging via logs. A Streamlit dashboard showing cache hit rates and latency percentiles would've saved days.

## The Stack

- **FastAPI** (async web framework)
- **PostgreSQL + Alembic** (schema migrations)
- **Redis** (L2/L3 caching)
- **Claude AI** (LLM orchestration)
- **LangGraph** (agent workflows)
- **Docker Compose** (local dev consistency)

All 11 repos have CI/CD via GitHub Actions. Every PR blocks on tests passing.

## Live Demo

EnterpriseHub dashboard: [ct-enterprise-ai.streamlit.app](https://ct-enterprise-ai.streamlit.app)

See cache hit rates, agent performance metrics, and lead analytics in real-time.

## Key Takeaways

1. **Cache aggressively** — 89% cost reduction is possible with smart cache keys
2. **Async everything** — Don't block on I/O in multi-agent systems
3. **Test coordination, not just units** — Handoff bugs only appear in integration tests
4. **Observability > debugging** — Structured logs and metrics beat print statements
5. **Production ≠ prototype** — Rate limits, versioning, and load testing matter

Building production AI isn't about the newest model. It's about boring infrastructure that scales.
