# Week 5: Observability + Testing (Insight Engine)

## Overview

This week covers instrumentation, monitoring, and testing for AI systems. Students build a Streamlit dashboard for real-time observability and write 50+ tests for non-deterministic AI behavior.

**Repo**: Insight Engine
**Lab**: Instrument an AI system with monitoring, build a dashboard, write 50+ tests

## Learning Objectives

By the end of this week, students will be able to:
1. Instrument AI systems with structured logging and performance metrics
2. Build latency tracking with P50/P95/P99 percentile calculations
3. Implement anomaly detection for business metrics and KPIs
4. Design and build a Streamlit monitoring dashboard
5. Write comprehensive tests for non-deterministic AI behavior

## Session A: Concepts + Live Coding (Tuesday)

### Part 1: Observability for AI Systems (15 min)

**Three pillars of observability:**
1. **Logs**: Structured JSON logs with request IDs, token counts, cache status
2. **Metrics**: Latency histograms, throughput counters, error rates, cache hit ratios
3. **Traces**: Request lifecycle tracking across services

**AI-specific observability:**
- Token usage per request (input + output)
- Cost per request (model pricing x tokens)
- Cache hit/miss ratios per cache level
- Output parsing strategy success rates
- Agent tool selection patterns

### Part 2: Live Coding — Monitoring Dashboard (45 min)

1. **Structured logging** (10 min)
   - JSON log format with standard fields
   - Log levels: DEBUG (dev), INFO (production), WARNING (degraded), ERROR (failures)
   - Context propagation: request ID across all log entries
   - Sensitive data redaction (PII, API keys)

2. **Performance tracking** (15 min)
   - Rolling window latency calculation
   - P50/P95/P99 percentile computation
   - SLA compliance tracking (P95 < target)
   - Alerting thresholds and cooldown periods

3. **Streamlit dashboard** (15 min)
   - Layout: sidebar for filters, main area for metrics
   - Real-time charts: latency over time, cache hit rate, error rate
   - KPI cards: current P95, cache hit %, cost/request, throughput
   - Anomaly highlighting: red indicators when metrics breach thresholds

4. **Anomaly detection** (5 min)
   - Z-score based: flag values > 2 standard deviations from rolling mean
   - Threshold based: absolute limits on metrics
   - Trend detection: is the metric getting worse over time?

### Part 3: Lab Introduction (15 min)

- Lab 5 README walkthrough
- Starter code: AI system without observability
- Autograder: structured logs present, dashboard renders, 50+ tests passing
- Test categories: unit, integration, behavior

### Part 4: Q&A (15 min)

## Session B: Lab Review + Deep Dive (Thursday)

### Part 1: Lab Solution Review (20 min)

Common patterns and mistakes:
- Logging too much (performance overhead, storage costs)
- Not logging enough (can't debug production issues)
- Tests that depend on exact LLM output instead of behavioral properties
- Dashboard that only shows current values without history

### Part 2: Deep Dive — Testing AI Systems (40 min)

**The testing pyramid for AI:**

```
         /  E2E  \          Few: Full pipeline tests
        /----------\
       / Integration \       Some: Service boundary tests
      /----------------\
     /    Unit Tests     \   Many: Pure function tests
    /______________________\
```

**What to test in AI systems:**

| Test Type | What It Verifies | Example |
|-----------|-----------------|---------|
| Output format | Response matches expected schema | Agent returns valid JSON with required fields |
| Behavioral | System makes correct decisions | Agent hands off at confidence > 0.7 |
| Boundary | Edge cases handled correctly | Empty input, max-length input, special characters |
| Integration | Services communicate correctly | Cache read/write, API rate limiting |
| Regression | Fixed bugs stay fixed | Previously-failing inputs produce correct output |
| Performance | Meets latency/throughput SLAs | P95 < 500ms under load |

**Testing non-determinism:**
- Seed random generators where possible
- Mock LLM calls for deterministic unit tests
- Use statistical assertions for integration tests (>80% correct over 10 runs)
- Property-based testing: "response always contains required fields"

**Test patterns for AI:**
- Mock the LLM response, test the surrounding logic
- Snapshot testing: detect unexpected output format changes
- Behavior-driven: given X input, the system should Y (not "returns exactly Z")
- Parameterized tests: one test function, many input/output pairs

### Part 3: Case Study (20 min)

EnterpriseHub's 8,500+ test strategy:
- Test distribution: 60% unit, 30% integration, 10% e2e
- Jorge bot tests: handoff confidence, scoring accuracy, response safety
- Performance tests: P50/P95/P99 under simulated load
- How monitoring caught a regression before it reached production

### Part 4: Week 6 Preview (10 min)

## Key Takeaways

1. Observability is not optional — you cannot run AI in production without it
2. Structured logging with request IDs is the foundation of debugging
3. P95 latency matters more than average latency for user experience
4. Test AI behavior, not exact output — mock the LLM, test the logic
5. 50+ tests is a starting point, not a ceiling

## Resources

- Insight Engine repository
- Streamlit documentation
- "Testing AI Systems" (course materials)
- EnterpriseHub test suite (examples of production AI tests)
