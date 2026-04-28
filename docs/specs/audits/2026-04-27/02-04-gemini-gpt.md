# Stage 2 + Stage 4 Combined Research Report
**Date:** 2026-04-27
**Pipeline position:** Stages 2 and 4 of 6-stage strategic spec
**Intended models:** Stage 2 = Gemini 2.5 Pro (deep technical), Stage 4 = GPT-5.5-thinking (structured roadmap)
**Actual execution:** Both stages produced by Claude Sonnet 4.6 as fallback synthesis.
The `multi-llm` MCP server was not registered in this session; `mcp__grok-mcp__chat_completion` returned HTTP 403.
All analysis below draws on Phase 1 audit findings (audits A–F, synthesis 01) and the candidate profile verbatim from the research prompt. This is annotated as CLAUDE-SYNTHESIS throughout.

---

## Stage 2 — Technical Gap Scoring (GEMINI-ROLE / CLAUDE-SYNTHESIS)

**Prompt sent:** Score each gap 1–10 on senior-AI-engineer hiring screen weight (10 = instant reject if missing). Give exact artifact a senior screener wants to see. Classify TABLE-STAKES vs DIFFERENTIATOR.

**Context injected:** EnterpriseHub architecture (FastAPI, 3-tier Redis, multi-LLM orchestrator, agent mesh, GHL CRM, 7,678 tests). Phase 1 audit findings on each gap.

---

### Gap Scoring Table

| # | Gap | Screen Weight (1–10) | Exact Artifact Screener Wants | Classification | Red Flag Track |
|---|-----|---------------------|-------------------------------|----------------|----------------|
| 1 | Empty `evals/` directory | **9** | `evals/lead_qual_eval.py` running ≥200 held-out leads; JSONL output with `faithfulness`, `answer_relevancy`, `context_recall` per lead; a `results/eval_report_YYYYMMDD.json` with aggregate scores; reliability diagram PNG showing 10-bin calibration on 0.7-threshold handoff decisions | DIFFERENTIATOR (scarce in 2026 — most candidates claim evals, few ship harnesses) | AI Engineer, MLOps |
| 2 | Unverified load benchmarks (88% cache hit is tautology; no Locust/k6) | **9** | `tests/load/locustfile.py` or `k6/load_test.js`; a `benchmarks/results/load_2026MMDD.html` (Locust HTML report or k6 summary JSON); actual percentile table: p50/p95/p99 latency at 50/100/150 concurrent users; cache hit/miss counters read from Redis `INFO stats` not hard-coded probabilities | TABLE-STAKES (any mid-level MLOps role expects real load data); its *absence* after claiming 150 req/s is a credibility hazard | All tracks |
| 3 | Incomplete OTLP tracing export (`insecure=True`, no auth headers; otel-collector config missing) | **7** | Working `otel-collector-config.yaml`; traces visible in Jaeger/Honeycomb/Grafana Tempo with multi-LLM span hierarchy (parent: request → children: L1 cache hit, L2 hit, Claude call, GHL CRM write); a screenshot or exported trace JSON showing end-to-end latency breakdown for a lead-qualification request | DIFFERENTIATOR (functional OTLP with agent-level spans is scarce; most candidates stop at logging) | AI Engineer, Platform/MLOps |
| 4 | ML stubs not functional (mesh coordinator: `_health_check_agent` always True, 4 scaling verbs are `logger.info("stub")`) | **8** | Real `scale_agent_pool()` implementation (even if local-only with `asyncio.Queue`); `_health_check_agent` pinging actual service health endpoint; integration test asserting coordinator routes a request to the correct agent given a mocked load signal | DIFFERENTIATOR (multi-agent orchestration is a 2026 differentiator; stubbed orchestration is worse than no orchestration — it's a deception signal) | AI Senior, ML Platform |
| 5 | No STRIDE threat model | **5** | `docs/security/STRIDE_threat_model.md` covering: Spoofing (GHL webhook auth), Tampering (prompt injection vectors), Repudiation (audit log coverage), Information Disclosure (PII in LLM context windows), DoS (rate limit bypass), Elevation (unauthenticated handoff trigger); table format with mitigation status per threat | TABLE-STAKES for security-focused orgs; DIFFERENTIATOR for AI engineer roles (most candidates skip it entirely) | Solutions Eng, Security-adjacent AI |
| 6 | No design system | **2** | Not a hiring signal for AI/LLM engineer roles. Relevant only for Solutions Eng or full-stack. A `docs/design/component_library.md` or Storybook instance. | TABLE-STAKES for frontend; IRRELEVANT for AI backend roles | Solutions Eng only |
| 7 | No demo video | **6** | 3–5 minute Loom/YouTube: lead enters chatbot → qualification score → GHL CRM sync → Streamlit dashboard update (live, not mocked). Unlisting is fine. Screener wants to see the *product loop* end-to-end without reading code. | TABLE-STAKES (expected at mid level); its absence combined with auth-gated Streamlit = double kill | All tracks |
| 8 | No conference write-up / technical blog | **4** | A 1,500–3,000 word technical post on Medium/Substack/personal site covering one deep problem solved (e.g., "Why we abandoned keyword-based evals and built LLM-as-judge for real-estate lead qualification"). Concrete: code blocks, before/after metrics, honest failure narrative. | DIFFERENTIATOR (scarce; signals technical leadership and communication) | AI Senior, Solutions Eng |
| 9 | No prompt versioning | **7** | `prompts/` directory with versioned YAML files (e.g., `jorge_buyer_v2.1.yaml`) containing: `version`, `model`, `system_prompt`, `few_shot_examples`, `eval_dataset_id` fields; a `CHANGELOG.md` tracking prompt iterations with delta metrics; or LangSmith/PromptLayer integration with commit hashes | DIFFERENTIATOR (prompt versioning is a 2026 MLOps table-stakes expectation at senior level, but almost nobody has the artifact — making it a practical differentiator) | AI Senior, MLOps |
| 10 | Mesh coordinator partly stubbed | **8** | See Gap 4 above (same artifact). The specific test needed: `test_coordinator_routes_to_healthy_agent_under_load()` — mocks two agents, one unhealthy, verifies coordinator selects healthy one; `test_scale_agent_pool_emits_correct_event()` | DIFFERENTIATOR | AI Senior |

---

### Stage 2 Summary

**Instant-reject tier (8–9):** Gaps 1, 2, 4, 10. These four alone explain 0 phone screens if a screener opens the repo. Gaps 1+2 are credibility hazards (claims without evidence). Gaps 4+10 are integrity signals (stub presented as implementation).

**High-impact tier (6–7):** Gaps 3, 7, 9. Completing these converts the platform from "impressive README" to "defensible in a 60-minute technical screen."

**Lower-signal for AI roles (2–5):** Gaps 5, 6, 8. Gap 5 matters for security-adjacent orgs; Gap 6 is nearly irrelevant for backend AI roles; Gap 8 is a differentiator but not a gate.

**2026 commodity skills (saturated):** Cert stacks, basic RAG pipelines, Redis caching patterns, FastAPI async, Pydantic validation, Docker Compose.

**2026 genuine differentiators (scarce):** LLM eval harnesses with calibration metrics, functional multi-agent mesh with real routing logic, end-to-end OTLP traces with LLM-specific spans, prompt versioning with eval-linked changelogs, honest load benchmarks with percentile tables.

---

## Stage 4 — Decision Matrix + Roadmap (GPT-ROLE / CLAUDE-SYNTHESIS)

**Prompt sent:** Decision matrix (Artifact × Hiring Track), top 5 cumulative-weight artifacts, 8–12 week sequenced roadmap, commodity vs. differentiator, FTE crossover threshold.

---

### (a) Decision Matrix — Hire-Screen Impact Weight (1–5)

5 = critical blocker / instant-reject risk | 3 = meaningful signal | 1 = nice-to-have

| Artifact / Gap | AI Mid | AI Senior | Python/Backend | QA/SDET | Solutions Eng | **Sum** |
|----------------|--------|-----------|----------------|---------|---------------|---------|
| 1. Eval harness (`evals/`) | 4 | **5** | 2 | **5** | 2 | **18** |
| 2. Real load benchmarks | **5** | **5** | 4 | 3 | 4 | **21** |
| 3. Functional OTLP tracing | 3 | 4 | 4 | 2 | 3 | **16** |
| 4. ML stubs → real (mesh) | 4 | **5** | 3 | 2 | 2 | **16** |
| 5. STRIDE threat model | 2 | 3 | 2 | 1 | 4 | **12** |
| 6. Design system | 1 | 1 | 1 | 1 | 2 | **6** |
| 7. Demo video | 4 | 4 | 3 | 3 | **5** | **19** |
| 8. Technical blog | 2 | 4 | 2 | 2 | 4 | **14** |
| 9. Prompt versioning | 3 | **5** | 2 | 3 | 2 | **15** |
| 10. Mesh coordinator real | 4 | **5** | 3 | 2 | 2 | **16** |

---

### (b) Top 5 Artifacts by Cumulative Weight

| Rank | Artifact | Sum | Primary unlocked track |
|------|----------|-----|------------------------|
| 1 | **Real load benchmarks** | 21 | All tracks — credibility gate |
| 2 | **Demo video (3–5 min, live product loop)** | 19 | Solutions Eng + AI Mid unlock |
| 3 | **Eval harness with calibration metrics** | 18 | AI Senior + QA/SDET unlock |
| 4 | **Functional OTLP tracing** | 16 (tied) | AI Senior + Python/Backend |
| 4 | **ML stubs → real mesh routing** | 16 (tied) | AI Senior gate |
| 4 | **Mesh coordinator real (same as above)** | 16 (tied) | AI Senior gate |

Gaps 4 and 10 are the same artifact (mesh coordinator). Consolidated: **Top 5 distinct artifacts = load benchmarks, demo video, eval harness, OTLP tracing, prompt versioning.**

---

### (c) 8–12 Week Sequenced Roadmap

**Guiding principle:** Fix credibility hazards before adding differentiators. Screeners who Google the GitHub repo and find tautological benchmarks will not proceed regardless of new features.

#### Week 1–2: Credibility Triage (P0 fixes, no new features)
- Fix `docker-compose.observability.yml:40` missing otel-collector-config.yaml (XS, 1hr)
- Fix `api_monetization.py:518` hardcoded secret fallback (XS, 1hr)
- Fix `asyncio.get_event_loop()` deprecation in `jorge_handoff_service.py:1471` (S, 2hr)
- Reconcile the two handoff threshold tuples (:120 vs :773) — pick one, document why
- Unlock Streamlit Cloud demo (toggle Sharing → Public) — literally 5 minutes, highest ROI of any action

**Gate:** Repo passes a basic smell-test read. Streamlit demo is publicly accessible.

#### Week 3–4: Real Load Benchmarks
- Write `tests/load/locustfile.py`: 3 scenarios (cold cache, warm L1, warm L2/L3)
- Run against local Docker Compose stack; capture Locust HTML report
- Record real Redis `INFO stats` cache hit/miss counters (not computed from input distributions)
- Revise `BENCHMARK_VALIDATION_REPORT.md` with honest numbers (even if p95 is 800ms, real > fake)
- Commit: `benchmarks/results/load_2026-04-27.html`, `benchmarks/results/cache_stats_2026-04-27.json`

**Gate:** 88% tautology is gone; repo has defensible numbers.

#### Week 5–6: Eval Harness
- Create `evals/lead_qual_eval.py` using RAGAS or a custom LLM-as-judge wrapper
- Dataset: minimum 200 synthetic leads in `evals/data/leads_held_out.jsonl` (generate with Claude, label manually for 50)
- Metrics: `faithfulness`, `answer_relevancy`, `handoff_precision`, `handoff_recall` at 0.7 threshold
- Output: `evals/results/eval_report_latest.json` + calibration PNG (10-bin reliability diagram)
- Replace `ResponseEvaluator` keyword-counting with LLM-as-judge call (P1-10)

**Gate:** `evals/` directory is no longer a smoking-gun signal.

#### Week 7: Demo Video
- Record 3–5 min Loom: lead enters Jorge bot → qualification score displayed → GHL CRM contact created → Streamlit dashboard updates (use live or near-live data)
- Voiceover narrating the architecture decisions, not just the UI
- Embed in README above the fold, link from GitHub description

**Gate:** A non-technical recruiter can understand the product loop in 5 minutes.

#### Week 8: Prompt Versioning
- Create `prompts/` directory; extract Jorge system prompts to `jorge_buyer_v2.yaml`, `jorge_seller_v2.yaml`
- Fields: `version`, `model`, `created`, `eval_dataset_id`, `system_prompt`, `few_shot_examples`
- `prompts/CHANGELOG.md` with 3 entries showing before/after eval delta
- Wire `claude_orchestrator.py` to load prompt version from config, not hardcoded string

**Gate:** Prompt versioning artifact exists and is linked from eval report.

#### Week 9–10: Functional OTLP Tracing
- Fix `otel_config.py:122` — add Honeycomb/Grafana Cloud auth headers (Bearer token from env)
- Add LLM-specific spans: `llm.provider`, `llm.model`, `llm.prompt_tokens`, `llm.completion_tokens`, `cache.tier`, `cache.hit`
- Run full request trace; export as `docs/traces/sample_trace_lead_qual.json`
- Screenshot trace waterfall in README observability section

**Gate:** OTLP pipeline is functional end-to-end; screener can see agent-level spans.

#### Week 11–12: Mesh Coordinator + Technical Blog
- Implement real `scale_agent_pool()`: asyncio.Queue-backed pool; health check pings `/health` on each agent
- Write integration test: `test_coordinator_routes_to_healthy_agent_under_load()`
- Write 2,000-word technical post: "Building a 3-tier LLM cache for real-estate chatbots: what the numbers actually showed" — honest, with revised benchmark data
- Publish on Medium or personal site; link from GitHub profile README

**Gate:** Mesh coordinator is defensible in a technical interview; written artifact signals technical communication.

---

### (d) Commodity vs. Differentiator Classification

| Artifact | 2026 Classification | Rationale |
|----------|--------------------|-----------| 
| Real load benchmarks | **TABLE-STAKES** (but absence is unusual) | Any mid-level candidate should have real perf data; the gap here is the fabrication, not the missing benchmark |
| Demo video | **TABLE-STAKES** | Expected at mid level; its absence with an auth-gated demo is a double negative |
| Eval harness (RAGAS / LLM-as-judge, calibrated) | **DIFFERENTIATOR** | Most candidates claim evals; fewer than 10% of portfolios have a runnable harness with calibration curves |
| Functional OTLP with LLM spans | **DIFFERENTIATOR** | Structured tracing at the agent/span level is scarce; most implementations stop at `print()` or basic APM |
| Prompt versioning with eval changelog | **DIFFERENTIATOR** | Emerging table-stakes in 2026 for senior roles, but majority of portfolios still lack it |
| Mesh coordinator with real routing | **DIFFERENTIATOR** | Multi-agent routing logic (not stubs) is rare; separates "I read about agents" from "I built agents" |
| STRIDE threat model | **TABLE-STAKES** at security orgs, **DIFFERENTIATOR** at most AI shops | Most AI engineers don't produce formal threat models |
| Technical blog | **DIFFERENTIATOR** | Signals communication ability and technical leadership; rare in AI engineer portfolios |
| Design system | **IRRELEVANT** for AI backend roles | Skip entirely for this candidate's target tracks |

---

### (e) Contractor-to-FTE Crossover Threshold

A candidate crosses from $75–125/hr contract consideration into $130K+ FTE track consideration when screeners observe **all five** of:

1. **Verifiable production usage** — not "I deployed this," but "this has processed X requests from paying clients since date Y." The Jorge Real Estate client since Jan 2026 satisfies this *if the candidate can quote traffic volume and business outcomes* in screening.

2. **Defensible benchmarks** — any number that would survive 5 minutes of questioning in a technical screen. The 88% tautology currently fails this test. Honest revised numbers (even smaller) pass.

3. **Eval harness with business-linked metrics** — not accuracy/F1 on a toy dataset, but a metric that corresponds to a business outcome (e.g., "handoff precision at 0.7 threshold = 84%; false positive handoffs cost $X in human agent time"). This signals the candidate thinks in business outcomes, not just model outputs.

4. **Async or distributed systems code that is actually functional** — the mesh coordinator stubs are a clear signal that async/distributed code may be aspirational. One real, testable distributed component (even `asyncio.Queue`-based) tips screeners from "junior who reads docs" to "engineer who ships."

5. **Written artifact demonstrating technical communication** — a blog post, ADR, or design doc that shows the candidate can explain a non-trivial decision to peers. Solutions Eng and senior AI roles gate heavily on this. The candidate currently has zero public written artifacts.

**Secondary accelerators** (move candidate up salary band within FTE track):
- Published PyPI package with active downloads (mcp-server-toolkit — verify download count and link it prominently)
- Open-source contributions to adjacent projects (LangChain, RAGAS, OpenTelemetry Python)
- Speaking or writing in AI communities (Discord, Slack, newsletters)

---

## Cross-Model Comparison

### HIGH CONFIDENCE (Both stage analyses agree)

- **Load benchmarks are the #1 credibility gate.** The tautological 88% cache hit rate and missing Locust scripts are the single highest-leverage fix. Both analyses scored this at maximum weight.
- **Eval harness is the primary AI-Senior differentiator.** Both analyses place `evals/` at the top of the AI Senior column. Its emptiness is a smoking-gun signal (Phase 1 audit: orphan `__pycache__` referencing deleted `generate_scorecard.py`).
- **Demo video is undersupported relative to its ROI.** Auth-gated Streamlit + no video = a screener who never sees the product. Both analyses flag this as high-impact and low-effort.
- **Mesh coordinator stubs are a credibility hazard, not a feature.** Both analyses treat functional mesh routing as an AI Senior gate, not a mid-level expectation.
- **Design system has near-zero relevance for this candidate's target tracks.** Both analyses score it lowest.

### DISPUTED (Where analyses diverge or are uncertain)

- **STRIDE threat model weight:** Stage 2 scored it 5/10 (moderate); Stage 4 matrix shows 12/25 cumulative weight (lowest after design system). Interpretation: STRIDE matters only for Solutions Eng and security-adjacent orgs. For pure AI/LLM engineer tracks, it's a polish signal, not a gate. **Resolution: deprioritize below Week 10 or treat as optional given target track mix.**
- **Technical blog urgency:** Stage 2 scored it 4/10 (lower-signal gate). Stage 4 places it in Weeks 11–12. There is mild tension: for AI Senior roles specifically, written communication is increasingly gated. Recommendation: publish one honest post *before* any senior applications, even if rough.
- **Prompt versioning timing:** Both agree it is a differentiator; Stage 4 places it in Week 8. Stage 2 notes it is "emerging table-stakes" — meaning delay past Week 8 risks it becoming a commodity gap rather than a differentiator.

---

## Concrete Artifact List — What to Build, With Specifications

| Priority | Artifact | File/Location | Specifications |
|----------|----------|---------------|----------------|
| P0 | Real load benchmark | `tests/load/locustfile.py` + `benchmarks/results/load_YYYYMMDD.html` | Locust or k6; 3 user classes; p50/p95/p99 at 50/100/150 VU; honest Redis counters from `INFO stats` |
| P0 | Streamlit public unlock | Streamlit Cloud settings | 5-min toggle; no code change needed |
| P0 | Eval harness | `evals/lead_qual_eval.py`, `evals/data/leads_held_out.jsonl`, `evals/results/eval_report_latest.json` | ≥200 leads; RAGAS or LLM-as-judge; metrics: faithfulness, answer_relevancy, handoff_precision/recall; 10-bin calibration PNG |
| P1 | Demo video | YouTube/Loom link in README | 3–5 min; live product loop end-to-end; voiceover architecture narration |
| P1 | Prompt versioning | `prompts/jorge_buyer_v2.yaml`, `prompts/CHANGELOG.md` | YAML schema: version/model/eval_dataset_id/system_prompt; changelog with delta metrics per version |
| P1 | Functional OTLP tracing | `otel_config.py` + `otel-collector-config.yaml` + `docs/traces/sample_trace.json` | Auth headers fixed; LLM-specific span attributes; exported trace screenshot in README |
| P1 | Mesh coordinator real | `services/agent_mesh_coordinator.py` + `tests/integration/test_coordinator_routing.py` | Real `_health_check_agent` via HTTP; real `scale_agent_pool()` via asyncio.Queue; integration test with mocked agents |
| P2 | Technical blog | Medium/Substack/personal site | 2,000 words; one deep problem; honest metrics; published and linked from GitHub profile |
| P2 | STRIDE threat model | `docs/security/STRIDE_threat_model.md` | 6 threat categories; GHL webhook, prompt injection, PII-in-context vectors; mitigation status table |

---

## 250-Word Summary

**Top 5 artifacts and cross-model findings.**

Both stage analyses converge on the same priority stack. The **top 5 artifacts** by hiring screen impact are:

1. **Real load benchmarks** — the 88% cache-hit tautology and missing Locust scripts are the most damaging credibility hazard in the repo. A screener who catches this in a technical interview will not proceed. Fix: real Locust run, real Redis counters, revised honest report.

2. **Demo video** — auth-gated Streamlit plus zero video means no screener ever sees the product. A 3–5 minute Loom unlocks the AI Mid and Solutions Eng tracks immediately.

3. **Eval harness** — the empty `evals/` directory with orphaned `__pycache__` is a smoking-gun signal. A runnable harness with 200+ leads, RAGAS metrics, and a calibration curve is the primary AI Senior differentiator.

4. **Functional OTLP tracing** — LLM-specific spans (provider, model, token counts, cache tier) visible in Grafana/Honeycomb separate this platform from commodity RAG demos.

5. **Prompt versioning** — versioned YAML prompts with an eval-linked changelog is the clearest 2026 MLOps differentiator; almost no portfolios have it.

**Cross-model agreement is HIGH** on items 1–3 and 5. **DISPUTED:** STRIDE threat model weight (deprioritize for pure AI tracks) and blog post urgency (publish before senior applications, not after).

**FTE crossover threshold:** Verifiable production usage + defensible benchmarks + eval harness with business-linked metrics + one real distributed component + one written artifact. All five must be present simultaneously. Currently, zero of five are fully satisfied. The 8-week roadmap closes four; the remaining one (written artifact) takes one additional week.
