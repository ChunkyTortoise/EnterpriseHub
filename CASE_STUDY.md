# Case Study: Production Real Estate AI Platform

**89% LLM cost reduction | P95 < 2s | 7-stage compliance pipeline | 7,678 tests**

---

## Business Problem

Real estate teams lose 40% of leads when response time exceeds the 5-minute SLA. Manual lead qualification is slow (45+ minutes per lead), inconsistent, and creates compliance risk under FHA, RESPA, TCPA, and SB-243 regulations. The typical brokerage juggles disconnected tools: CRM, spreadsheets, separate analytics, and no unified view of pipeline health.

EnterpriseHub was built for a Rancho Cucamonga real estate team (Jorge Salas, Acuity Real Estate) to solve three problems simultaneously:
1. Qualify leads instantly via AI before they go cold
2. Enforce regulatory compliance automatically
3. Provide unified BI dashboards for pipeline visibility

---

## Architecture Decisions

### Why 3-Tier LLM Cache (L1/L2/L3)

The most expensive component is LLM inference. Without caching, each lead qualification costs ~$0.15 in Claude API tokens. At scale (500 leads/month), that's $900/year just for qualification.

**Solution**: Three-tier cache with different TTLs and latency profiles:
- **L1**: In-memory LRU (1,000 entries, <1ms, 59% hit rate)
- **L2**: Redis (15-minute TTL, <5ms, 21% hit rate)
- **L3**: PostgreSQL (persistent, <20ms, 8% hit rate)

**Result**: 88% aggregate cache hit rate, 89% token cost reduction ($93K to $7.8K tokens per workflow run).

### Why Cross-Bot Handoff with Confidence Thresholds

Three specialized bots (Lead, Buyer, Seller) handle different qualification flows. Instead of a single monolithic bot, the handoff service routes between them at 0.7 confidence with circular prevention (30-minute window), rate limiting (3/hr, 10/day per contact), and dynamic threshold learning from outcome history.

**Why not a single bot?** Domain-specific prompts produce measurably better qualification scores. The Lead bot uses a Q0-Q4 framework, the Seller bot uses FRS/PCS scoring, and the Buyer bot uses financial readiness assessment. Mixing these in one prompt degraded accuracy by ~15% in testing.

### Why 7-Stage Response Pipeline

Every bot response passes through a compliance pipeline before reaching the customer:

1. **Language detection** (mirror the customer's language)
2. **TCPA opt-out detection** (short-circuit on STOP/unsubscribe)
3. **FHA/RESPA compliance check** (block discriminatory or non-compliant content)
4. **Conversation repair** (detect breakdowns, escalate to human)
5. **AI disclosure** (SB-243 footer: `[AI-assisted message]`)
6. **Translation** (if customer language differs)
7. **SMS truncation** (320-char limit, sentence boundary aware)

This exists because a single compliance violation can trigger regulatory action. The pipeline ensures every outbound message is safe regardless of what the LLM generates.

---

## Production Metrics

| Metric | Value | How Measured |
|--------|-------|--------------|
| Lead qualification P95 | < 2 seconds | Synthetic load benchmark (no live LLM) |
| Cache hit rate | 88% | L1 59% + L2 21% + L3 8% |
| LLM cost reduction | 89% | Token usage: 93K to 7.8K per workflow |
| Test suite | 7,678 tests | Unit + integration + security + compliance |
| Agent fleet | 22 agents | Auto-routed via Agent Mesh Coordinator |
| Compliance coverage | 5 regulations | FHA, RESPA, TCPA, CCPA, SB-243 |

---

## Technical Highlights

- **Agent Mesh Coordinator**: Routes tasks to 22 domain agents based on cost, success rate, load, and latency. Emergency shutdown at $100/hr spend threshold.
- **A/B Testing Service**: Deterministic variant assignment (SHA-256 hash), z-test statistical significance, minimum sample size calculation. 4 pre-built experiments (response tone, follow-up timing, CTA style, greeting).
- **Security**: Parameterized SQL queries (zero f-string SQL), Ed25519 + HMAC webhook signature verification, JWT auth (1hr expiry), Redis-backed rate limiting (100 req/min).
- **Observability**: structlog structured logging, Prometheus-ready metrics, distributed tracing (OTLP), 10 Architecture Decision Records documenting design choices.

---

## Lessons Learned

1. **Cache hit rates compound**: L1 alone gets 59%. Adding L2 (Redis) captures 21% of L1 misses. L3 (PostgreSQL) catches another 8%. The marginal cost of each tier is minimal, but the aggregate 88% hit rate transforms the economics.

2. **Compliance pipelines must short-circuit**: TCPA opt-out detection runs in stage 2, before any AI processing. This prevents the LLM from generating a response to someone who said "STOP" -- both a legal requirement and a cost saving.

3. **Handoff thresholds need learning**: Static confidence thresholds (0.7 for Lead->Buyer/Seller) worked initially, but dynamic threshold adjustment from outcome history improved handoff quality once we had 10+ data points per route.

4. **God classes are technical debt**: The webhook handler grew to 2,700 lines before being decomposed into domain-specific handlers (GHL, Stripe, registry). The decomposition improved testability and made security review practical.

---

## Stack

FastAPI (async) | PostgreSQL 15 | Redis 7 | Claude API (primary) + Gemini + Perplexity (fallback) | GoHighLevel CRM | Stripe | Streamlit | Docker Compose | GitHub Actions CI

---

*Source: [github.com/ChunkyTortoise/EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub)*
