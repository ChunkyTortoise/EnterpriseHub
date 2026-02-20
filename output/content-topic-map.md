# Content Topic Map -- Flywheel Candidates

**Created**: 2026-02-19
**Method**: Scored by (existing reach) x (content depth) x (monetization potential) on 1-5 scale each

---

## Content Inventory Summary

| Directory | Files | Topics Covered |
|-----------|-------|----------------|
| `content/adr-articles/` | 5 | Redis caching, handoff confidence, intent decoder, agent mesh, FRS/PCS scoring |
| `content/case-studies/` | 13 | AgentForge, DocQA, EnterpriseHub, GHL Jorge Bot (short/long/metrics) |
| `content/devto/` | 9 | Production RAG, LangChain replacement, CSV to dashboard, LLM cost reduction, multi-agent |
| `content/linkedin/week2-5/` | 12 | Caching, Ruff, LLM benchmarks, ADRs, prototype-to-prod, RAG poll, handoffs, agents, CRM patterns, market rates, recap |
| `content/community/` | 7 | GHL architecture, GHL teardown, HN hiring, LinkedIn connection templates |
| `content/social/` | 14 | AgentForge launch (LinkedIn, Twitter, HN, Reddit), engagement responses |
| `content/gumroad/` | 50+ | 21 product listings (3 tiers each for AgentForge, DocQA, Insight Engine), bundles, SEO |
| `content/services/` | 8 | Audit templates, SOW templates, service tiers, landing page |
| `CASE_STUDY_*.md` (root) | 5 | BI Analytics, Multi-Agent Orchestration, Lead Qualification, RAG Pro, Real Estate Automation |

---

## Topic Scoring

**Scoring formula**: Reach (1-5) x Depth (1-5) x Monetization (1-5) = Max 125

| Rank | Topic | Source Content | Reach | Depth | Monetization | Score | Rationale |
|------|-------|---------------|-------|-------|-------------|-------|-----------|
| **1** | **LLM Cost Optimization (3-Tier Caching)** | ADR-001, LinkedIn #4, Dev.to article-5, CASE_STUDY root files, case-studies/ghl-jorge-bot-* | 5 | 5 | 5 | **125** | Universal pain point for anyone using LLMs in production. Deep technical content with real metrics (89% reduction, $847->$93). Maps to Gumroad products, Fiverr gigs, consulting services, and Upwork proposals. Already validated: LinkedIn #4 expected 40-60 replies. |
| **2** | **Multi-Agent Orchestration (Bot Handoffs)** | CASE_STUDY_ENTERPRISE_MULTI_AGENT_ORCHESTRATION.md, AgentForge case study, LinkedIn #10, ADR-002 (handoff confidence), content/social/agentforge-launch-* | 5 | 5 | 4 | **100** | AgentForge launch week (Feb 24) creates a time-sensitive amplification window. Deep content: confidence thresholds, circular prevention, rate limiting, pattern learning. Maps to AgentForge 3-tier Gumroad products ($49-$999). Slight monetization discount: framework sales are lower-margin than consulting. |
| **3** | **GHL/CRM AI Integration** | content/community/ghl-teardown-POST.md, ghl-architecture-POST.md, case-studies/ghl-jorge-bot-SHORT.md + LONG.md + METRICS.md, content/services/SOW templates | 4 | 5 | 5 | **100** | Niche but high-converting: GHL Facebook Group yields 5+ DMs/week and $5K-$15K engagements (per distribution plan). Deep technical content (3 case study variants, architecture post, teardown). Direct path to service revenue. Lower reach than topics 1-2 because GHL is a niche platform. |
| **4** | **Production RAG Pipeline** | content/devto/article-4-production-rag.md, article1-production-rag.md, CASE_STUDY_RAG_Pro_Document_Intelligence.md, LinkedIn #9 (RAG poll), content/reddit/r_python_post.md | 4 | 4 | 4 | **64** | RAG is trending in AI engineering. Multiple existing articles and case studies. Maps to DocQA Gumroad products and Fiverr RAG gig ($300-$1,200). LinkedIn #9 poll expected 70-100 replies. Slightly less depth than topics 1-2 (fewer ADR-level technical articles). |
| **5** | **Python DevOps & Developer Tooling** | LinkedIn #5 (Ruff), LinkedIn #7 (ADRs), content/devto/article3-csv-dashboard.md, ADR-004 (agent mesh governance), content/services/AUDIT_TEMPLATE.md | 4 | 3 | 3 | **36** | Broadest audience (all Python devs), good for reach and brand awareness. Ruff post expected 60-80 replies. Less monetizable directly -- harder to sell a product around linting/tooling. Works best as top-of-funnel content that drives profile visits. |

---

## Top 5 Topics for Flywheel

1. **LLM Cost Optimization** -- Score 125
2. **Multi-Agent Orchestration** -- Score 100
3. **GHL/CRM AI Integration** -- Score 100
4. **Production RAG Pipeline** -- Score 64
5. **Python DevOps & Developer Tooling** -- Score 36

---

## Flywheel Output Plan

Each topic produces 6 platform outputs:
- `linkedin.md` -- 300-500 word post with engagement question
- `twitter.md` -- 7-tweet thread with hook + data + CTA
- `devto.md` -- 1,500-2,500 word technical article with code samples
- `newsletter.md` -- 800-1,200 word email newsletter edition
- `reddit.md` -- r/MachineLearning or r/Python post (varies by topic)
- `youtube-script.md` -- 5-8 minute video script with timestamps

---

## Source File Reference

| Topic | Primary Sources | Supporting Sources |
|-------|----------------|-------------------|
| LLM Cost Optimization | `content/adr-articles/ADR-001-redis-caching-strategy.md`, `content/devto/article-5-llm-cost-reduction.md` | `content/linkedin/week2/post-4.md`, `content/case-studies/ghl-jorge-bot-SHORT.md` |
| Multi-Agent Orchestration | `CASE_STUDY_ENTERPRISE_MULTI_AGENT_ORCHESTRATION.md`, `content/case-studies/agentforge-CASE-STUDY.md` | `content/linkedin/week4/post-10.md`, `content/social/agentforge-launch-*` |
| GHL/CRM AI Integration | `content/community/ghl-teardown-POST.md`, `content/case-studies/ghl-jorge-bot-LONG.md` | `content/community/ghl-architecture-POST.md`, `content/services/SOW_TEMPLATE_BUILD.md` |
| Production RAG Pipeline | `content/devto/article-4-production-rag.md`, `CASE_STUDY_RAG_Pro_Document_Intelligence.md` | `content/reddit/r_python_post.md`, `content/linkedin/week3/post-9.md` |
| Python DevOps & Tooling | `content/linkedin/week2/post-5.md`, `content/linkedin/week3/post-7.md` | `content/devto/article3-csv-dashboard.md`, `content/services/AUDIT_TEMPLATE.md` |
