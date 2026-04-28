# Case Study: EnterpriseHub — Production Real Estate AI Platform

**Built and shipped a multi-bot lead qualification system for a Rancho Cucamonga real estate team. Production run: 3 months. Stack: FastAPI / PostgreSQL / Redis / Claude / GoHighLevel.**

---

## What Was Built

A real-estate-vertical lead qualification platform that took inbound SMS/web leads, qualified them in seconds via three specialized AI bots (Lead intake, Buyer, Seller), routed each conversation through a 7-stage compliance pipeline, and synced everything back to the GoHighLevel CRM with full audit trails.

The core engineering bets:
- **Three specialized bots** instead of one monolith — domain-specific prompts produced measurably better qualification scores
- **3-tier cache** (in-memory + Redis + Postgres) to keep LLM cost per qualification at roughly one-tenth of the naive baseline
- **Compliance as a pipeline**, not a check — every outbound message passes through ordered stages that can short-circuit before the LLM ever runs
- **A versioned prompt registry** with golden-dataset evals + nightly regression — every prompt change has a reviewable diff and a quality-delta number attached
- **An evaluation harness** with 50 hand-curated test cases, LLM-as-judge across 4 rubrics, and a CI gate that blocks PRs below a 0.85 quality threshold

The system ran in production for ~3 months processing 500+ real leads in English and Spanish before the engagement ended.

---

## The Business Problem

Real estate teams lose ~40% of leads when first response time exceeds the 5-minute SLA. Manual lead qualification takes 30–45 minutes per lead, is inconsistent across staff, and creates compliance exposure under FHA, RESPA, TCPA, CCPA, and California SB-243.

The brokerage I built this for had three concrete asks:
1. Qualify leads automatically before they went cold
2. Enforce compliance without trusting the LLM to know the regulations
3. Give the operator one dashboard for pipeline state instead of switching between CRM, spreadsheets, and separate analytics tools

---

## Architecture Decisions (and the tradeoffs that came with them)

### 3-Tier LLM Cache — L1 in-memory / L2 Redis / L3 Postgres

The naive baseline of one Claude call per lead qualification costs roughly $0.15 in tokens at the model size we used. At a real-estate brokerage's volume that's modest in absolute dollars but compounds with retries, A/B variants, and conversation context windows.

**The tiered approach:**
- L1 in-memory LRU — sub-millisecond, capped at ~1,000 entries, evicts under pressure
- L2 Redis with 15-minute TTL — single-digit ms, scoped to the conversation
- L3 Postgres — persistent across sessions, used for long-tail repeats

**Design-target hit-rate distribution:** L1 60% / L2 20% / L3 8% / miss 12% (88% combined).

**Important honesty caveat:** the 88% number was the *design target* under an expected workload, not a measurement of the running system. The simulation in `benchmarks/bench_cache.py` validates the latency model under that distribution; a live measurement tool reading real hit/miss counters from `LLMObservabilityService` is the correct way to evidence the achieved rate, and it's the next item on the roadmap. I'm flagging this here because the original case study quoted the design target as if it were measured, and that conflation is exactly the sort of thing senior reviewers screen for.

### Cross-Bot Handoff with Confidence Thresholds

The Lead bot uses a Q0-Q4 framework. The Seller bot uses an FRS/PCS scoring rubric. The Buyer bot uses a financial-readiness assessment. Mixing these into a single prompt degraded qualification accuracy by ~15% in testing, so I built a handoff service.

**The handoff layer:**
- Asymmetric thresholds per route (Lead→Buyer/Seller: 0.7, Buyer→Seller: 0.8, Seller→Buyer: 0.6) — empirical, not symmetric
- Circular-prevention window (30 min) — prevents bouncing between bots on ambiguous intent
- Rate limits (3/hr, 10/day per contact) — protects the lead from being talked at
- Dynamic threshold learning kicks in after 10 data points per route

**The lesson:** static confidence thresholds were a defensible starting point. The system improved meaningfully once outcome data fed back into the thresholds, but you need the outcome plumbing built first or you have nothing to learn from.

### 7-Stage Response Pipeline

Every outbound message passes through:

1. Language detection — mirror the customer's language
2. TCPA opt-out detection — short-circuits on STOP / unsubscribe before anything else runs
3. FHA/RESPA compliance check — blocks steering, redlining, and non-compliant content
4. Conversation repair — detects breakdown patterns, escalates to a human
5. AI disclosure (SB-243 California requirement) — appends `[AI-assisted message]` footer
6. Translation if customer language differs from operator language
7. SMS truncation — 320-char limit, sentence-boundary aware

**The lesson:** compliance pipelines must short-circuit. TCPA opt-out runs in stage 2, before any LLM call, because (a) it's required, and (b) generating a response to someone who said STOP is the kind of thing that draws regulatory attention even if the response is benign.

---

## Eval & Prompt Engineering Discipline

This is the part that's harder to see from the README but matters more than the architecture for production reliability:

- **`evals/golden_dataset.json`** — 50 hand-curated test cases covering seller qualification (15), buyer scheduling (10), lead intake (10), edge cases (10), and compliance scenarios (5). Every case has expected output properties (max length, no URLs, no AI disclosure leakage, persona maintained, topic boundary) that a correct response must satisfy.
- **`evals/judge.py`** — LLM-as-judge over 4 rubrics, plus deterministic property checks. Returns a quality score per case.
- **`evals/baseline.json`** — regression baseline. Every PR runs against it; >10% drop fails CI and auto-creates a GitHub issue.
- **`PROMPT_CHANGELOG.md`** — every prompt version is documented with rationale, the dataset run that validated it, and the quality delta.
- **`tests/adversarial/`** — 18 prompt-injection / jailbreak / topic-boundary cases with CI integration.
- **`.github/workflows/nightly-eval.yml`** — 2 a.m. UTC cron that re-runs the golden set against the current main branch, posts a regression report.

This is what "eval-driven AI delivery" actually looks like at the IC level. Most portfolios don't have it.

---

## Honest Production Metrics

| Metric | Value | How it was measured |
|---|---|---|
| Production duration | ~3 months | Real customer traffic |
| Leads processed | 500+ | Counted in CRM |
| Languages supported | EN + ES | Full bilingual flows |
| Bot count | 3 specialized + handoff service | Lead, Buyer, Seller |
| Tests | 8,212 across the test suite | Unit / integration / security / compliance / adversarial |
| Eval golden cases | 50, with regression baseline + nightly cron | `evals/` |
| Prompt versions tracked | 25+ in `PROMPT_CHANGELOG.md` | PostgreSQL `prompt_versions` table |
| Compliance regulations covered | FHA, RESPA, TCPA, CCPA, SB-243 | 7-stage pipeline + adversarial tests |
| ADRs documenting non-obvious tradeoffs | 13 | `docs/adr/` |

**What I am NOT claiming:** specific live throughput numbers (the 150 req/s figure in earlier docs was unbacked by reproducible artifacts; honest k6 load tests are pending). Specific live cache-hit measurements (see honesty caveat above). Specific dollar savings (the $93K → $7.8K figure was a workflow-projection estimate, not a measurement of the bill).

---

## Technical Highlights

- **Agent Mesh Coordinator** — 22 domain agents, weighted routing on cost / success rate / load / latency, emergency shutdown at $100/hr spend threshold (some scaling verbs are scaffolded; documented in ADR rather than dressed up).
- **A/B testing service** — deterministic variant assignment (SHA-256 hash), z-test statistical significance, sample-size calculator. 4 prebuilt experiments.
- **Security baseline** — parameterized SQL throughout, Ed25519 + HMAC webhook signature verification, JWT auth with fail-closed secret loading, Fernet PII encryption, Redis-backed rate limiting.
- **Observability** — structlog structured logging, Prometheus-shaped metrics, OTLP-instrumented (collector wiring is a Wave 1 task).

---

## What I Took Away From Shipping It

1. **Cache hit rates compound, but the design-target distribution is not the measurement.** Build the live counter before you cite the rate.

2. **Compliance pipelines must short-circuit.** Move the cheap, deterministic checks (opt-out, language) ahead of the LLM. Both legally required and significantly cheaper.

3. **Handoff thresholds want to learn.** Static thresholds work until you have outcomes; then they're leaving accuracy on the table. Build the outcome plumbing on day 1 even if you don't use it for a month.

4. **God classes are technical debt that compounds.** The webhook handler grew to 2,700 lines before I decomposed it into domain-specific handlers. The pre-decomposition state was the single biggest blocker to security review and onboarding.

5. **Eval-driven delivery is the senior-tier difference.** Without the golden dataset + LLM-as-judge + CI gate, every prompt change is a coin flip. With it, prompts can be tuned with the same discipline as code.

---

## Stack

FastAPI (async) · PostgreSQL 15 · Redis 7 · Claude API (primary) + Gemini + Perplexity (fallback) · GoHighLevel CRM · Stripe · Streamlit · Docker Compose · GitHub Actions CI · OTLP / Prometheus

---

## What Engagement Like This Looks Like

I build and ship production AI systems for vertical-specific lead qualification, intake, and compliance workflows — particularly in real estate, but the patterns transfer to insurance, mortgage, and home services.

A typical engagement:
- 4–8 weeks build, 2–4 weeks operate-and-tune
- Fixed-price scopes from $1,800 (single qualification bot) up through $4,500+ (full multi-bot system + dashboard)
- Hourly $55–95/hr depending on scope and stack fit

If you're running a brokerage, agency, or vertical-AI shop and have a lead-qualification, intake, or compliance problem that isn't being served by the off-the-shelf chatbots, I'm available — [github.com/ChunkyTortoise/EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub) is the source.

---

*Source repo: [github.com/ChunkyTortoise/EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub) · Live demo: [ct-enterprise-ai.streamlit.app](https://ct-enterprise-ai.streamlit.app)*
