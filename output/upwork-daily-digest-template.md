# Upwork Daily Opportunity Digest -- Template

**Purpose**: Repeatable daily workflow for sourcing, scoring, and proposing on Upwork opportunities.
**Frequency**: Daily (M-F), 15-20 minutes
**Owner**: Cayman Roden

---

## Step 1: Search Queries (Run All 5)

Execute these searches on Upwork's job search page. Use "Most Recent" sort order.

### Primary Searches (run daily)

1. **AI/ML Core**:
   - Search: `Python AI RAG LLM agent`
   - Filters: Posted last 24 hours, Hourly $50+/hr OR Fixed $500+, Less than 10 proposals
   - URL: https://www.upwork.com/nx/search/jobs/?q=Python+AI+RAG+LLM+agent&sort=recency&payment_verified=1

2. **Claude / MCP Specialist**:
   - Search: `Claude API MCP agent`
   - Filters: Posted last 24 hours, Any budget
   - URL: https://www.upwork.com/nx/search/jobs/?q=Claude+API+MCP+agent&sort=recency

3. **GoHighLevel + AI**:
   - Search: `GoHighLevel AI automation`
   - Filters: Posted last 3 days, Any budget
   - URL: https://www.upwork.com/nx/search/jobs/?q=GoHighLevel+AI+automation&sort=recency

4. **RAG Pipeline**:
   - Search: `RAG pipeline production Python`
   - Filters: Posted last 24 hours, Hourly $50+/hr OR Fixed $300+
   - URL: https://www.upwork.com/nx/search/jobs/?q=RAG+pipeline+production+Python&sort=recency

5. **Multi-Agent Systems**:
   - Search: `multi-agent AI orchestration`
   - Filters: Posted last 3 days, Any budget
   - URL: https://www.upwork.com/nx/search/jobs/?q=multi-agent+AI+orchestration&sort=recency

### Secondary Searches (run 2-3x/week)

6. **CRM + AI Integration**:
   - Search: `CRM AI integration Python`
   - Filters: Posted last 7 days, Hourly $40+/hr

7. **Streamlit / Dashboard**:
   - Search: `Streamlit dashboard AI Python`
   - Filters: Posted last 7 days, Any budget

8. **FastAPI Backend**:
   - Search: `FastAPI backend AI LLM`
   - Filters: Posted last 7 days, Hourly $50+/hr

---

## Step 2: Scoring Rubric

For each opportunity found, score on a 10-point scale:

| Factor | Points | Criteria |
|--------|--------|----------|
| **Skill Match** | 0-4 | 4 = exact stack match (RAG + agents + Python + LLM). 3 = strong overlap. 2 = partial. 1 = tangential. 0 = no match. |
| **Budget** | 0-2 | 2 = $60+/hr or $500+ fixed. 1 = $40-59/hr or $200-499 fixed. 0 = below $40/hr or $200 fixed. |
| **Competition** | 0-2 | 2 = < 5 proposals. 1 = 5-15 proposals. 0 = 15+ proposals. |
| **Urgency** | 0-1 | 1 = "ASAP", "immediate start", posted < 24hrs. 0 = no urgency signals. |
| **Scope Clarity** | 0-1 | 1 = clear deliverables, timeline, tech stack. 0 = vague or unclear. |

**Action thresholds**:
- **8-10**: Submit proposal immediately (Priority 1)
- **7**: Submit if connects available (Priority 2)
- **5-6**: Bookmark for later review
- **< 5**: Skip

---

## Step 3: Proposal Template

For each qualifying opportunity (score >= 7), generate a proposal using this structure:

```markdown
# Opening Hook (2-3 sentences)
- Reference something specific about the job posting
- State your direct experience with their exact problem

# Proof Points (3-4 bullets)
- Metric 1: 89% LLM cost reduction via 3-tier caching
- Metric 2: 88% cache hit rate / 0.88 citation faithfulness
- Metric 3: 8,500+ tests across 11 production repos
- Metric 4: Relevant throughput or latency metric

# Relevant Portfolio (2-3 items)
- Repo + live demo URL
- Key metric from that repo

# Call to Action
- Availability statement
- Specific next step ("Available for a call this week")

# Signature
Cayman Roden
Portfolio: https://chunkytortoise.github.io
```

**Customization points** (adapt per job):
- **RAG jobs**: Lead with advanced_rag_system, cite 0.88 faithfulness
- **Agent jobs**: Lead with AgentForge, cite 4.3M dispatches/sec
- **GHL jobs**: Lead with EnterpriseHub, cite $50M+ pipeline
- **Claude/MCP jobs**: Lead with MCP integration experience, cite production workflows
- **Cost optimization**: Lead with 89% reduction metric

---

## Step 4: Daily Log Format

After completing the search, log results in this format:

```markdown
## [DATE] Daily Digest

**Searched**: [time] | **New opportunities**: [count] | **Proposals sent**: [count]

| # | Job Title | Score | Rate | Status |
|---|-----------|-------|------|--------|
| 1 | [title] | [score]/10 | [rate] | PROPOSED / BOOKMARKED / SKIPPED |

**Notes**: [any market observations]
```

---

## Step 5: Weekly Review (Fridays)

1. Review all proposals sent this week
2. Check response rates
3. Adjust scoring weights if needed
4. Update client-pipeline.md with new proposals
5. Identify trending search terms to add

---

## Automation Notes

**If Upwork MCP becomes available**:
- Replace manual searches with MCP job search queries
- Auto-score using the rubric above
- Generate proposal drafts via Claude
- Human reviews and submits manually (Gate G4)

**Current state**: Manual search + manual scoring + AI-assisted proposal writing

---

## Quick Reference: Portfolio Metrics

| Metric | Value | Use For |
|--------|-------|---------|
| LLM cost reduction | 89% | RAG, agent, cost optimization jobs |
| Cache hit rate | 88% | RAG, caching, performance jobs |
| Citation faithfulness | 0.88 | RAG, knowledge management jobs |
| Agent throughput | 4.3M dispatches/sec | Agent, orchestration jobs |
| P99 latency | 0.095ms | Performance, latency-sensitive jobs |
| Test count | 8,500+ across 11 repos | Any job (production credibility) |
| Pipeline managed | $50M+ | CRM, real estate, enterprise jobs |
| Bot tests | 205 passing | Chatbot, conversational AI jobs |
