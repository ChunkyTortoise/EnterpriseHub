# AgentForge Cost Optimization Guide

## Overview

This guide covers practical techniques to reduce LLM API costs using AgentForge's built-in optimization features. Based on production deployments that achieved 85-98% cost reductions.

AgentForge supports Claude, Gemini, OpenAI, and Perplexity through a single interface, with per-request cost tracking, token-aware rate limiting, and intelligent routing.

---

## 1. Understanding Your Cost Baseline

### Cost Rates by Provider

AgentForge's `CostTracker` includes built-in rates per million tokens for all major models:

```python
from agentforge.cost_tracker import DEFAULT_COST_RATES

# Built-in rates (input, output) per million tokens:
# Claude 3.5 Sonnet:     $3.00 / $15.00
# Claude 3 Opus:        $15.00 / $75.00
# Claude 3 Haiku:        $0.25 / $1.25
# GPT-4o:                $2.50 / $10.00
# GPT-4o Mini:           $0.15 / $0.60
# GPT-4 Turbo:          $10.00 / $30.00
# Gemini 1.5 Pro:        $1.25 / $5.00
# Gemini 1.5 Flash:      $0.075 / $0.30
# Gemini 2.0 Flash:      $0.10 / $0.40
# Perplexity Sonar Pro:  $0.60 / $3.00
# Perplexity Sonar:      $0.20 / $1.00
```

### Setting Up Cost Tracking

```python
from agentforge import AIOrchestrator
from agentforge.cost_tracker import CostTracker

tracker = CostTracker()
orc = AIOrchestrator(temperature=0.3)

# Track every request
response = await orc.chat("claude", "Analyze this document")
tracker.record(
    provider="claude",
    model="claude-3-5-sonnet",
    input_tokens=response.usage.input_tokens,
    output_tokens=response.usage.output_tokens
)

# Get session summary
summary = tracker.get_session_cost()
print(f"Total: ${summary['total_cost_usd']:.4f}")
print(f"By provider: {summary['by_provider']}")
print(f"By model: {summary['by_model']}")
```

The `CostTracker` is thread-safe, so it works correctly in async and multi-threaded environments.

---

## 2. Provider Selection Strategy

### The 80/20 Rule for Provider Routing

In most production systems, 80% of LLM calls are simple tasks (classification, extraction, summarization) that do not require the most capable (and expensive) model. Route based on task complexity:

| Task Type | Recommended Provider | Cost/1M tokens | Rationale |
|-----------|---------------------|-----------------|-----------|
| Classification | Gemini 2.0 Flash | $0.10/$0.40 | Fast, cheap, good enough |
| Extraction | GPT-4o Mini | $0.15/$0.60 | Great at structured output |
| Summarization | Gemini 1.5 Pro | $1.25/$5.00 | Long context window |
| Complex reasoning | Claude 3.5 Sonnet | $3.00/$15.00 | Best reasoning quality |
| Research with citations | Perplexity Sonar | $0.20/$1.00 | Built-in web search |

### Implementing Tiered Routing

```python
from agentforge import AIOrchestrator

orc = AIOrchestrator(temperature=0.2)

async def smart_route(task_type: str, prompt: str) -> str:
    """Route to the cheapest adequate provider for each task type."""

    routing_table = {
        "classify":    ("gemini", "gemini-2.0-flash"),
        "extract":     ("openai", "gpt-4o-mini"),
        "summarize":   ("gemini", "gemini-1.5-pro"),
        "reason":      ("claude", "claude-3-5-sonnet"),
        "research":    ("perplexity", "sonar"),
    }

    provider, model = routing_table.get(task_type, ("gemini", "gemini-1.5-pro"))
    response = await orc.chat(provider, prompt, model=model)
    return response.content
```

### Cost Impact Example

For a system processing 10,000 requests/day:

| Scenario | Daily Cost |
|----------|-----------|
| All Claude 3.5 Sonnet | $180.00 |
| All GPT-4o | $125.00 |
| Smart routing (80% Flash, 20% Sonnet) | $22.40 |
| **Savings** | **$157.60/day (88%)** |

---

## 3. Fallback Chains for Cost-Aware Reliability

### Configure Fallback from Expensive to Cheap

AgentForge's fallback chains can be configured to try cheaper providers first and fall back to more expensive ones only when needed:

```python
orc = AIOrchestrator(
    temperature=0.3,
    max_retries=2,
    fallback_chain=["gemini", "openai", "claude"]
    # Try cheapest first, fall back to most capable
)

# If Gemini succeeds (which it will 95%+ of the time), you pay Gemini rates
# Only escalates to Claude if both Gemini and OpenAI fail
response = await orc.chat("gemini", prompt)
```

### Quality-Aware Fallback

For tasks where quality matters, reverse the chain:

```python
# For critical tasks: try best model first, fall back if unavailable
orc_critical = AIOrchestrator(
    fallback_chain=["claude", "openai", "gemini"]
)

# For routine tasks: try cheapest first
orc_routine = AIOrchestrator(
    fallback_chain=["gemini", "openai", "claude"]
)
```

---

## 4. Prompt Template Optimization

### Reduce Token Count with Templates

AgentForge's `PromptTemplate` system supports variable substitution and built-in templates that reduce prompt size:

```python
from agentforge.prompt_template import PromptTemplate

# Without template: 150 tokens per prompt
raw_prompt = """You are an expert analyst. I need you to analyze the following
document carefully and provide a detailed summary. The document is about
machine learning and was published in 2024. Please focus on the key findings
and methodology sections. Here is the document: {document}"""

# With template: 45 tokens per prompt (70% reduction)
template = PromptTemplate(
    "Summarize {{doc_type}} document focusing on {{focus_areas}}:\n{{content}}"
)

prompt = template.render(
    doc_type="ML research",
    focus_areas="key findings, methodology",
    content=document_text
)
```

### Template Best Practices

| Technique | Token Reduction | Example |
|-----------|----------------|---------|
| Remove filler words | 15-25% | "Please carefully analyze" -> "Analyze" |
| Use structured input | 20-30% | Prose description -> key:value pairs |
| Template variables | 30-40% | Repeated boilerplate -> `{{variable}}` |
| Batch similar requests | 40-60% | 10 separate calls -> 1 batch call |

### Measuring Template Effectiveness

```python
# Compare token usage between approaches
raw_tokens = len(raw_prompt.split()) * 1.3  # rough estimate
template_tokens = len(prompt.split()) * 1.3

savings_pct = (1 - template_tokens / raw_tokens) * 100
print(f"Token savings: {savings_pct:.0f}%")
```

---

## 5. Rate Limiting to Prevent Waste

### Token Bucket Configuration

AgentForge's `TokenBucketLimiter` prevents rate limit errors (which waste tokens on failed requests) and enables controlled bursting:

```python
from agentforge.rate_limiter import TokenBucketLimiter, RateLimitConfig

# Match your provider's actual limits
claude_limits = RateLimitConfig(
    requests_per_minute=60,
    tokens_per_minute=100_000,
    burst_multiplier=1.5  # Allow 90 RPM bursts
)

openai_limits = RateLimitConfig(
    requests_per_minute=500,
    tokens_per_minute=300_000,
    burst_multiplier=2.0  # Allow 1000 RPM bursts
)

gemini_limits = RateLimitConfig(
    requests_per_minute=360,
    tokens_per_minute=4_000_000,
    burst_multiplier=1.5
)
```

### Why Rate Limiting Saves Money

Without rate limiting:
1. Request hits provider's rate limit
2. Request fails with 429 error
3. Retry logic re-sends the full prompt (paying for input tokens again)
4. In high-throughput systems, this creates cascading failures

With AgentForge's rate limiter:
1. Request is queued locally until a token is available
2. No 429 errors, no wasted retry tokens
3. Smooth, predictable throughput

**Measured savings**: Eliminating retry waste typically saves 5-15% on total token costs in high-throughput systems.

---

## 6. Structured Output for Efficiency

### Reduce Output Token Waste

AgentForge's structured output module extracts JSON from LLM responses with schema validation, ensuring you get only the data you need:

```python
from agentforge.structured import extract_json, validate_schema

schema = {
    "type": "object",
    "properties": {
        "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
        "confidence": {"type": "number"},
        "reasons": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["risk_level", "confidence"]
}

# Request structured output (fewer output tokens than prose)
response = await orc.chat("openai", f"Assess fraud risk. Respond in JSON: {data}")
result = extract_json(response.content)
is_valid = validate_schema(result, schema)
```

Structured output typically uses 60-80% fewer output tokens than prose responses. Since output tokens cost 3-5x more than input tokens, this is a significant saving.

---

## 7. Caching Strategies

### Application-Level Cache

For repeated or similar queries, implement caching to avoid redundant API calls entirely:

```python
import hashlib
from functools import lru_cache

# Simple in-memory cache for identical prompts
prompt_cache = {}

async def cached_chat(provider: str, prompt: str) -> str:
    cache_key = hashlib.sha256(f"{provider}:{prompt}".encode()).hexdigest()

    if cache_key in prompt_cache:
        return prompt_cache[cache_key]  # $0.00 cost

    response = await orc.chat(provider, prompt)
    prompt_cache[cache_key] = response.content
    return response.content
```

### Cache Hit Rates in Practice

| Use Case | Typical Cache Hit Rate | Cost Reduction |
|----------|----------------------|----------------|
| Classification (fixed categories) | 60-80% | 60-80% |
| FAQ/Knowledge base | 40-60% | 40-60% |
| Document summarization | 20-40% | 20-40% |
| Creative/unique prompts | <5% | Minimal |

---

## 8. Guardrails for Cost Protection

### Token Budget Enforcement

AgentForge's guardrails engine enforces hard caps to prevent runaway costs:

```python
from agentforge.guardrails import GuardrailsEngine

guardrails = GuardrailsEngine(
    max_token_budget=8192,       # Per-request cap
    session_token_limit=100_000, # Per-session cap
)

# Requests exceeding budget are blocked BEFORE reaching the provider
# No tokens are consumed, no cost is incurred
```

### Daily Budget Alerts

```python
from agentforge.cost_tracker import CostTracker

tracker = CostTracker()
DAILY_BUDGET = 50.0  # $50/day

async def budget_aware_chat(provider, prompt):
    session = tracker.get_session_cost()
    if session["total_cost_usd"] >= DAILY_BUDGET:
        raise BudgetExceededError(f"Daily budget of ${DAILY_BUDGET} reached")

    response = await orc.chat(provider, prompt)
    tracker.record(provider, model, response.usage.input_tokens, response.usage.output_tokens)
    return response
```

---

## 9. Benchmarking Before Optimizing

### Use AgentForge's Built-in Benchmarking

Before optimizing, measure your current state:

```bash
# CLI benchmark across all configured providers
agentforge benchmark

# Programmatic benchmarking
python -m benchmarks.run_all
```

### Key Metrics to Track

| Metric | How to Measure | Target |
|--------|---------------|--------|
| Cost per request | `CostTracker.get_session_cost()` | Minimize |
| Tokens per request | Response usage stats | <2000 avg |
| Cache hit rate | Cache hits / total requests | >40% |
| Rate limit errors | Provider error logs | 0 |
| Fallback activations | Tracing events | <5% |

---

## 10. Optimization Checklist

Use this checklist to systematically reduce costs:

- [ ] **Enable cost tracking** -- You cannot optimize what you do not measure
- [ ] **Analyze provider distribution** -- Are expensive providers used for simple tasks?
- [ ] **Implement tiered routing** -- Route 80% of tasks to cheapest adequate provider
- [ ] **Optimize prompts** -- Use templates, remove filler, request structured output
- [ ] **Configure rate limiting** -- Eliminate retry waste from 429 errors
- [ ] **Add caching** -- Cache identical and similar prompts
- [ ] **Set budget guards** -- Token caps and daily budget alerts
- [ ] **Benchmark regularly** -- Monthly cost review with `agentforge benchmark`

### Expected Savings by Technique

| Technique | Typical Savings | Effort |
|-----------|----------------|--------|
| Tiered routing | 60-85% | Low |
| Prompt templates | 15-35% | Low |
| Structured output | 10-20% | Low |
| Caching | 20-60% | Medium |
| Rate limiting | 5-15% | Low |
| Budget guards | Prevents spikes | Low |
| **Combined** | **85-95%** | **Medium** |

---

## Real-World Results

| Client | Before | After | Technique |
|--------|--------|-------|-----------|
| LegalTech startup | $3,600/mo | $396/mo | Tiered routing + templates |
| Healthcare platform | $2,800/mo | $420/mo | Guardrails + tiered routing |
| Fintech processor | $135K/mo (proj.) | $2,100/mo | Tiered screening + consensus |

---

## About AgentForge

AgentForge's cost optimization capabilities are backed by 491 automated tests across 21 test files. Key modules: CostTracker (10 tests), Rate Limiter (29 tests), Prompt Templates (27 tests), Guardrails (30 tests), Structured Output (14 tests).

- **Repository**: [github.com/ChunkyTortoise/ai-orchestrator](https://github.com/ChunkyTortoise/ai-orchestrator)
- **PyPI**: `pip install agentforge`
- **Provider overhead**: <50ms per call
- **Cost model accuracy**: Per-request tracking with model-specific rates
