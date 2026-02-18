# Production Agent Orchestration

**Build multi-agent systems that survive production.** In 4 weeks, go from isolated LLM calls to orchestrated agent pipelines with human approval gates, self-correcting RAG, and eval-driven deployment. You'll ship real code every week.

[**Enroll Now -- $997/seat**](#pricing)

---

## Who This Is For

- **Senior engineers** building LLM-powered features who need to move past single-prompt architectures
- **ML engineers** deploying retrieval-augmented systems who want structured evaluation before shipping
- **Tech leads** responsible for AI reliability who need human-in-the-loop patterns that actually scale
- **Platform engineers** designing internal agent frameworks who want production-tested primitives instead of framework lock-in

This is not an intro to LLMs. You should be comfortable with Python, async patterns, and have built at least one LLM integration.

---

## What You'll Build

Each week produces a working system you can deploy or adapt for your own use case.

| Week | Project | What Ships |
|------|---------|------------|
| 1 | **Research Pipeline** | 3-agent DAG with dependency resolution, retry, graceful degradation, and ASCII monitoring |
| 2 | **Approval-Gated Data Pipeline** | Ingest-transform-export pipeline with webhook-based HITL gates, Slack integration, and audit trails |
| 3 | **Multi-KB Policy Bot** | RAG agent querying multiple knowledge bases with self-correcting retrieval and confidence-based answer validation |
| 4 | **Eval-Driven CI Pipeline** | Benchmark suite comparing agent versions on pass rate and P50/P95/P99 latency, with JSON export for CI |

---

## Full Syllabus

### Week 1: DAG Orchestration Fundamentals

Build a research pipeline from scratch using directed acyclic graphs. No frameworks -- pure Python orchestration you fully understand and control.

**Module 1.1 -- Agent Primitives**
- `BaseAgent` architecture: Pydantic validation, execution timing, cost tracking
- `AgentInput` / `AgentOutput` contracts and upstream result passing
- Building a custom agent in under 20 lines

**Module 1.2 -- DAG Execution Engine**
- Topological sort (Kahn's algorithm) for deterministic execution order
- `AgentNode` dependency declaration and cycle detection
- Result injection: how downstream agents consume upstream outputs

**Module 1.3 -- Failure Handling**
- Retry with exponential backoff (configurable per agent)
- Graceful degradation: optional vs. required agents
- Error propagation and downstream dependency skipping

**Module 1.4 -- Monitoring and Observability**
- ASCII performance tables: agent name, status, duration, tokens, cost
- Gantt chart timeline for execution visualization
- JSON export for external dashboards and alerting

**Lab: Research-Analysis-Report Pipeline**
Build a 3-agent pipeline: `ResearchAgent` gathers data, `AnalysisAgent` processes it, `ReportAgent` synthesizes both outputs. Add retry policies, optional agents, and export metrics to JSON. Run the pipeline with different failure scenarios and observe degradation behavior.

---

### Week 2: Human-in-the-Loop Approval Gates

Production agent systems need human oversight. This week you'll add approval gates that pause pipeline execution at critical decision points -- model deployment, data writes, payment processing.

**Module 2.1 -- HITL Gate Architecture**
- `HITLGate` design: blocking execution until explicit approve/reject
- Auto-approve timeouts as safety nets
- Interactive mode (CLI) vs. non-interactive mode (webhook/API)

**Module 2.2 -- External Integration Patterns**
- `on_request` and `on_resolve` callbacks for Slack, PagerDuty, email
- Thread-safe approval from external systems (webhook handlers, background workers)
- Polling vs. event-driven gate resolution

**Module 2.3 -- Rejection and Pipeline Halting**
- Rejection propagation: blocking downstream agents on gate denial
- Audit trail: who approved, when, how long the gate waited
- Approval rate tracking and gate history

**Module 2.4 -- Production Patterns**
- Multi-gate pipelines with different approval authorities
- Escalation chains: auto-approve after timeout with elevated logging
- Gate metrics: wait time distribution, rejection rates, approver response times

**Lab: Approval-Gated Data Pipeline**
Build an ingest-transform-export pipeline where a `data_quality_review` gate blocks writes to production. Implement three modes: (1) auto-approve after timeout, (2) external webhook approval from a simulated Slack bot running in a background thread, (3) rejection that halts the pipeline. Add approval rate tracking and full audit logging.

---

### Week 3: Agentic RAG

Move beyond naive retrieve-and-generate. This week you'll build a RAG agent that queries multiple knowledge bases, self-corrects on low-confidence retrievals, and validates answers before returning them.

**Module 3.1 -- Knowledge Base Construction**
- `KnowledgeBase` and `Document` primitives
- TF-IDF relevance scoring (zero external dependencies)
- Swapping in OpenAI/Cohere embeddings by overriding `search()`

**Module 3.2 -- Multi-KB Retrieval**
- Querying across multiple knowledge bases in a single pass
- Cross-KB result merging and re-ranking by relevance score
- Source attribution: which KB contributed which result

**Module 3.3 -- Self-Correction Loop**
- Confidence threshold detection
- Query refinement strategies when confidence is below threshold
- Configurable max iterations to prevent infinite loops

**Module 3.4 -- Answer Validation**
- Groundedness checks: does the answer cite retrieved content?
- Confidence blending across multiple sources
- Structured warnings when answer quality is uncertain
- `RAGAgent` subclassing: overriding `synthesize_answer()` for LLM integration

**Lab: Multi-KB Policy Bot**
Build a `PolicyBot` that answers employee questions by querying HR, legal, and engineering knowledge bases simultaneously. Implement self-correction (low confidence triggers query expansion and retry), answer validation (groundedness scoring), and source attribution. Test with adversarial queries that span multiple KBs and queries with no good answer.

---

### Week 4: Eval, Benchmarking, and Production Deployment

You cannot improve what you do not measure. This week you'll build an evaluation framework that gates agent deployment on pass rate and latency, then integrate it into CI.

**Module 4.1 -- Test Case Design**
- `TestCase` structure: input context, judge functions, tags
- Custom judges: exact match, partial credit, LLM-as-judge
- Tag-based filtering for smoke tests, regression suites, edge cases

**Module 4.2 -- Agent Evaluation**
- `AgentEvaluator`: pass rate, average score, failure analysis
- `results_by_tag()` for targeted test slices
- Failure reporting: which cases failed, why, and with what output

**Module 4.3 -- Benchmarking**
- Multi-run benchmarks for latency stability
- P50/P95/P99 latency percentiles
- Error rate tracking across runs

**Module 4.4 -- Agent Comparison and CI Integration**
- `BenchmarkSuite` for head-to-head agent comparison
- Leaderboard generation across multiple agent versions
- JSON export for CI pipelines (fail the build if pass rate drops below threshold)
- Monitoring: alerting on latency regression between deploys

**Lab: Eval-Driven CI Pipeline**
Build a benchmark suite that compares your Week 3 `PolicyBot` against a baseline. Define 15+ test cases across smoke, regression, and edge-case tags. Run 10-iteration benchmarks and generate a leaderboard. Export results to JSON and write a CI gate script that fails if pass rate < 95% or P95 latency exceeds your SLA. Integrate with GitHub Actions.

---

## What's Included

- **8 live sessions** (2 per week, 90 minutes each) -- lecture + live coding, recorded for async viewing
- **4 hands-on labs** with starter code, solution branches, and automated test suites
- **Weekly office hours** (60 minutes) -- bring your own codebase, get direct feedback
- **Private Slack community** -- cohort channel + direct access to instructor
- **Full source code** -- the [multi-agent-starter-kit](https://github.com/ChunkyTortoise/multi-agent-starter-kit) repo (101 tests, MIT license) plus all course extensions
- **Code review** -- submit your lab solutions for written feedback
- **Lifetime access** to all recordings, materials, and future updates to the starter kit

---

## Outcomes

After completing this course, you will be able to:

- Design and implement multi-agent pipelines using DAG orchestration with explicit dependency management, retry policies, and graceful degradation
- Add human-in-the-loop approval gates to any agent workflow, with webhook integration, audit trails, and rejection handling
- Build RAG systems that query multiple knowledge bases, self-correct on low-confidence retrievals, and validate answers before returning them
- Evaluate agent quality systematically using custom test suites, benchmark latency percentiles, and agent-vs-agent comparison
- Gate production deployments on eval results by integrating benchmark reports into CI pipelines
- Operate without framework lock-in -- every component is pure Python with zero heavyweight dependencies

---

## Instructor

**Cayman Roden** builds production AI systems. His portfolio includes 8,500+ automated tests across multiple agent orchestration projects, verified 89% AI cost reduction in production deployments, and orchestration systems handling 4.3M dispatches/sec. He has managed a $50M+ real estate pipeline using multi-agent AI, working daily with Claude, GPT-4, Gemini, FastAPI, PostgreSQL, Redis, and Docker. Based in Palm Springs, CA.

---

## Pricing

| Plan | Price | Details |
|------|-------|---------|
| **Early Bird** | **$697** | First 20 seats only |
| **Standard** | **$997** | Full price per seat |
| **Team (3+)** | **$799/seat** | Same team, same cohort -- contact for invoicing |

All plans include everything listed above. No upsells, no premium tier. 30-day refund policy: if you complete Week 1 labs and the course is not what you expected, full refund.

[**Reserve Your Seat -- $697 Early Bird**](#enroll)

---

## FAQ

**What LLM provider do I need?**
None required. All labs run with mock agents and local logic. When you're ready to add real LLM calls (Claude, GPT-4, Gemini), we show you exactly where to plug them in -- the architecture is provider-agnostic.

**How much time should I expect per week?**
Plan for 6-8 hours: 3 hours of live sessions, 3-5 hours on labs and reading. Labs have stretch goals if you want to go deeper.

**Is this the same content as the open-source starter kit?**
The starter kit is the foundation. The course adds 4 extended labs, live instruction, code review, architecture deep-dives, production deployment patterns, and CI integration that go well beyond the README examples.

**What if I miss a live session?**
All sessions are recorded and posted within 24 hours. Office hours are also recorded. Slack stays active between sessions.

**Do I need to know a specific AI framework (LangChain, CrewAI, etc.)?**
No. This course is framework-independent by design. The orchestration layer is pure Python. If you use a framework at work, you'll learn the primitives underneath it.

**What Python version do I need?**
Python 3.11+. The only external dependency is Pydantic. Everything else is standard library.

---

## Cohort Details

- **Start date**: 4 weeks from enrollment open
- **Cohort cap**: 30 seats
- **Format**: Live + async, fully remote
- **Time zone**: Sessions scheduled for US-friendly hours (Pacific), all recorded

Seats are allocated in order of enrollment. When this cohort fills, the next cohort opens 8 weeks later.

[**Enroll Now -- 30 Seats Available**](#enroll)
