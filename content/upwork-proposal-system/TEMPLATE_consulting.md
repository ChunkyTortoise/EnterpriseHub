# AI Consulting / Architecture Review Proposal Template

**Target Jobs**: AI consulting, architecture review, technical advisory, LLM strategy, code review, performance audit, feasibility analysis

**Avg Win Rate**: 10-15% (lower volume but higher rates)

**Typical Budget**: $100-150/hr OR $2K-$10K fixed for multi-day engagements

---

## Template

Hi [CLIENT NAME],

[HOOK — Reference their specific challenge, architecture concern, or strategic question. Examples below.]

I provide technical consulting and architecture reviews for AI systems, with a focus on [LLM orchestration / RAG pipelines / multi-agent systems / performance optimization]. Here's my relevant background:

[BULLET 1 — Choose most relevant from proof points library]

[BULLET 2 — Secondary domain expertise]

[OPTIONAL BULLET 3 — Specific tool/framework if mentioned]

For this kind of engagement, I typically work in phases: [Phase 1: Discovery and analysis] → [Phase 2: Recommendations document] → [Phase 3: Implementation support (optional)]. Deliverables include architecture diagrams, technical spec, and risk assessment.

[CTA — Choose from library based on engagement type]

— Cayman Roden

---

## Hook Examples (Pick One, Customize)

### 1. Architecture Review / Design
> "Designing a multi-agent system that balances cost, latency, and quality is exactly the kind of trade-off analysis I specialize in. I've architected systems that reduced token costs by 89% while maintaining <200ms orchestration overhead."

**When to use**: Posts asking for architecture design, system design review, or "how should we build this?"

### 2. Performance Audit
> "Your concern about [slow response times / high API costs / low cache hit rates] is a common pain point. I've audited production AI systems and identified bottlenecks that teams missed — often the fix is in caching strategy or prompt optimization, not model choice."

**When to use**: Posts mentioning performance problems, cost overruns, or "our system is too slow."

### 3. RAG Quality Issues
> "RAG systems returning irrelevant results usually fail at retrieval, not generation. I've debugged dozens of RAG pipelines and typically find the issue is chunking strategy, embedding model mismatch, or lack of hybrid retrieval (BM25 + dense)."

**When to use**: Posts about RAG accuracy, "our Q&A system gives wrong answers," or retrieval quality.

### 4. LLM Strategy / Vendor Selection
> "Choosing between Claude, GPT-4, and Gemini depends on your use case — conversational quality vs. function calling vs. cost. I've built provider-agnostic orchestration layers and can help you evaluate which fits your requirements and budget."

**When to use**: Posts asking "which LLM should we use?" or mentioning vendor evaluation.

### 5. Code Review / Technical Debt
> "Reviewing an existing AI codebase for technical debt, security issues, or scalability bottlenecks is something I do regularly. I provide actionable recommendations ranked by impact and effort — not just 'rewrite everything.'"

**When to use**: Posts asking for code review, audit, or "is our current approach sound?"

---

## Proof Point Selection (Choose 2-3)

Rank these based on job post emphasis. Lead with the most relevant.

### Multi-System Architecture
> **Production AI platform** — Architected EnterpriseHub: 3-bot multi-agent system, LLM orchestration across 4 providers, 3-tier caching (89% cost reduction), CRM integration, BI dashboards. 5,100+ tests, deployed in production managing $50M+ real estate pipeline. ([EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub))

**When to emphasize**: All consulting jobs. Shows breadth of experience and production scale.

### RAG Expertise
> **RAG pipeline design** — Built document Q&A systems with hybrid retrieval (BM25 + dense), query expansion, cross-encoder re-ranking, and answer quality evaluation. Improved accuracy from 72% to 91% on domain benchmarks. ([docqa-engine](https://github.com/ChunkyTortoise/docqa-engine))

**When to emphasize**: RAG-specific consulting, Q&A system reviews, retrieval optimization.

### Multi-Agent Systems
> **Multi-agent orchestration** — Designed 3-bot conversation system with intent-based routing, cross-bot handoff, circular prevention, and A/B testing on response strategies. Handles 10 conversations/sec with <100ms routing overhead. ([jorge_real_estate_bots](https://github.com/ChunkyTortoise/jorge_real_estate_bots))

**When to emphasize**: Multi-agent consulting, conversation design, or bot architecture reviews.

### Performance Optimization
> **LLM cost and latency optimization** — Reduced token costs by 89% and P95 latency from 1.2s to <300ms via 3-tier caching, prompt optimization, and async orchestration. Saved $12K/month in API costs. ([EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub))

**When to emphasize**: Performance audits, cost reduction, or "our system is too expensive."

### Integration Architecture
> **CRM and third-party integrations** — Designed integration layer for GoHighLevel, HubSpot, Salesforce with OAuth 2.0, webhook resilience, rate limiting, and real-time sync. Handles 5K API calls/day with 99.2% uptime. ([EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub))

**When to emphasize**: Integration reviews, API design, or "how do we connect our system to [tool]?"

### Testing + Quality Engineering
> **Test engineering and quality standards** — Established testing frameworks across 11 repos (8,500+ tests total, 80%+ coverage). Includes benchmarking suites, CI/CD pipelines, and quality gates for production readiness. ([Portfolio](https://github.com/ChunkyTortoise))

**When to emphasize**: Code quality audits, test strategy, or "how do we improve our testing?"

---

## Engagement Phases (Customize)

**Standard 3-phase approach**:
> "For this kind of engagement, I typically work in phases: Phase 1 (Discovery and analysis) → Phase 2 (Recommendations document with architecture diagrams) → Phase 3 (Implementation support, optional). Deliverables include Mermaid diagrams, technical spec, and risk assessment."

**Alternative phrasing for specific jobs**:

### Architecture Design
> "For architecture design, I start with requirements gathering (1-2 calls), then provide a technical spec with system diagrams, data flow, tech stack recommendations, and cost estimates. Timeline: 1 week for spec, 2 weeks for review and iteration."

### Performance Audit
> "For performance audits, I profile your system (tracing, logging analysis, load testing), identify bottlenecks, and provide a prioritized fix list with expected impact. Timeline: 3-5 days for analysis, 1 week for recommendations."

### Code Review
> "For code reviews, I analyze your codebase for security issues, performance bottlenecks, technical debt, and scalability concerns. Deliverable: Markdown report with findings ranked by severity, plus refactoring recommendations. Timeline: 2-4 days depending on codebase size."

### Feasibility Analysis
> "For feasibility analysis, I evaluate your requirements against current AI capabilities, estimate development effort, identify risks, and recommend MVP scope. Deliverable: Feasibility report with go/no-go recommendation. Timeline: 1 week."

---

## CTA Options (Choose Based on Engagement Type)

### 1. Discovery Call (Most Effective)
> "I'm available for a 30-minute discovery call [this week] to understand your current architecture and pain points. No charge for the initial call."

**When to use**: P1 consulting jobs, complex engagements, or when you want to qualify the client.

### 2. Proposal Draft
> "Based on your description, I can draft a proposal outlining scope, timeline, and deliverables. Want me to send that over?"

**When to use**: Well-defined posts, clients who prefer written communication.

### 3. Quick Assessment
> "If you can share [your architecture diagram / current codebase / API response times], I can give you a quick (free) assessment of where the issues likely are."

**When to use**: Performance audits, debugging engagements, or when you want to demonstrate value upfront.

### 4. Case Study / Reference
> "Happy to share a case study from a similar engagement where I [reduced costs / improved accuracy / optimized performance]. Would that be helpful?"

**When to use**: Risk-averse clients, enterprise engagements, or when credibility is key.

### 5. Portfolio Link
> "I'm available [this week] if you'd like to discuss. Here's my full portfolio: https://chunkytortoise.github.io"

**When to use**: P2 jobs, when you need more context before committing.

---

## Customization Checklist

Before sending, verify:

- [ ] Hook addresses their specific problem (not generic "I do consulting")
- [ ] Proof points match their domain (RAG vs. chatbot vs. performance)
- [ ] Engagement phases are clear and match their needs
- [ ] CTA is low-pressure (discovery call > "let's sign a contract")
- [ ] Total word count <275
- [ ] No typos in client name, company, or technical terms
- [ ] Rate quoted is $100-150/hr (consulting commands higher rates)

---

## Rate Guidance

| Engagement Type | Suggested Rate |
|-----------------|----------------|
| Code review / audit (1-3 days) | $100-120/hr or $2K-$5K fixed |
| Architecture design (1-2 weeks) | $120-140/hr or $5K-$10K fixed |
| Performance optimization consulting | $120-140/hr or $4K-$8K fixed |
| Strategic advisory (ongoing) | $140-150/hr or $3K-$5K/month retainer |
| Feasibility analysis (3-5 days) | $100-120/hr or $2K-$4K fixed |

**Why higher rates?**
- Consulting requires deep expertise, not just coding
- Clients pay for your judgment and recommendations
- Deliverables are strategic (impact entire projects)
- No long-term commitment (short, high-value engagements)

**Phased pricing approach**:
- Phase 1: Discovery + analysis ($2K-$3K, 5-10 hours)
- Phase 2: Recommendations + spec ($3K-$5K, 10-15 hours)
- Phase 3: Implementation support ($120/hr, as-needed)

**Retainer model** (for ongoing advisory):
- $3K-$5K/month for 10-15 hours
- Includes architecture reviews, code reviews, strategic planning
- Good for startups building AI products

---

## Domain-Specific Adjustments

### RAG / Document AI
Focus on retrieval quality, chunking strategies, cost per query:
> "I've debugged RAG systems where accuracy was <70% and brought them to >90% by fixing chunking strategy, implementing hybrid retrieval, and tuning prompt engineering. Cost per query also matters — I can help you balance quality and expense."

### Multi-Agent Systems
Emphasize orchestration, handoff logic, state management:
> "Multi-agent systems fail when handoff logic is brittle or agents step on each other. I've designed conversation routers with circular prevention, confidence thresholds, and analytics to track which agent performs best for which intents."

### LLM Cost Optimization
Lead with specific savings numbers:
> "I've helped clients reduce LLM API costs by 60-89% without sacrificing quality. The levers are: caching strategy, prompt optimization, provider selection, and batching. I can audit your current usage and identify quick wins."

### Integration / API Design
Focus on resilience, rate limiting, error handling:
> "Third-party integrations fail in production when teams don't handle rate limits, webhook failures, or OAuth token expiry. I've designed integration layers that are resilient to all three and provide clear error messages when things go wrong."

---

## Deliverable Examples

Make deliverables concrete in your proposal:

### Architecture Review
> "Deliverables: Mermaid architecture diagram, technical spec (10-15 pages), risk assessment, tech stack recommendations with cost estimates, and a prioritized roadmap."

### Performance Audit
> "Deliverables: Performance profiling report with P50/P95/P99 latency breakdown, bottleneck analysis, prioritized optimization recommendations (ranked by effort vs. impact), and load testing results."

### Code Review
> "Deliverables: Code review report with findings categorized by severity (critical/high/medium/low), refactoring recommendations, security audit, and test coverage gap analysis."

### Feasibility Analysis
> "Deliverables: Feasibility report with go/no-go recommendation, effort estimate (person-weeks), risk matrix, MVP scope definition, and vendor/tool recommendations."

---

## Red Flags to Avoid

Consulting jobs attract tire-kickers. Watch for:

| Red Flag | Why It Matters |
|----------|---------------|
| "Just need a quick opinion" | Wants free advice, won't pay for deliverables |
| No budget stated | Fishing for lowest bid |
| "Looking for a co-founder" | Wants equity instead of payment |
| "We'll pay if it works" | Contingency-based = high risk of non-payment |
| Vague problem description | Client doesn't know what they need (endless scope creep) |

**If you see 2+ red flags, skip the job.** Consulting time is valuable — only bid on serious clients.

---

**Last Updated**: February 14, 2026
