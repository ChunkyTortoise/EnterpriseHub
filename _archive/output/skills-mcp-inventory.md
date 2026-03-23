# Skills MCP Inventory — Audit Report

**Date**: 2026-02-19 | **Purpose**: Identify skills suitable for MCP packaging as monetizable tools

---

## Audit Methodology

Skills were located by scanning:
1. `~/.claude/skills/` — global Claude Code skills directory
2. `/Users/cave/Projects/EnterpriseHub_new/` — project-level skill files
3. `~/.claude/CLAUDE.md` — documented skill shortcuts (`/proposal`, `/outreach`, etc.)
4. `~/.claude/agents/` — agent files that function as skill templates

---

## Skills Found

### 1. `/proposal` — Freelance Proposal Generator

**Source**: Documented in `CLAUDE.md` and `REVENUE-ENGINE-SPEC.md`; logic in `scripts/proposal_generator.py`

| Field | Value |
|-------|-------|
| File path | `scripts/proposal_generator.py` |
| Trigger | `/proposal` |
| Agent backing | `~/.claude/agents/technical-proposal-writer.md` |

**Input Schema**

```json
{
  "job_title": "string — job posting title",
  "job_description": "string — full job description text",
  "budget": "string — hourly rate or fixed budget from posting",
  "client_background": "string — any context about the client",
  "skills_to_highlight": "array[string] — optional override of default skills"
}
```

**Output Schema**

```json
{
  "proposal_text": "string — ready-to-paste Upwork/Fiverr proposal (300-500 words)",
  "fit_score": "integer 1-10",
  "key_differentiators": "array[string]",
  "estimated_rate": "string",
  "follow_up_hook": "string — one-line hook for follow-up message"
}
```

**Monetization Potential**: HIGH
- B2B SaaS founders, agency owners, and consultants need proposals constantly
- Competing tools: Proposify ($49/mo), Qwilr ($35/mo) — but none are AI-native + MCP-integrated
- Viable as: $0.25/call API, $29/mo subscription, or bundled with GTM service

---

### 2. `/outreach` — Cold Outreach Sequence Generator

**Source**: `CLAUDE.md`, `REVENUE-ENGINE-SPEC.md`; agent: `~/.claude/agents/outreach-personalizer.md`

| Field | Value |
|-------|-------|
| File path | `scripts/outreach_helper.py` |
| Trigger | `/outreach` |
| Agent backing | `~/.claude/agents/outreach-personalizer.md` |

**Input Schema**

```json
{
  "company_name": "string",
  "contact_name": "string",
  "contact_role": "string",
  "company_pain_point": "string — researched or inferred pain point",
  "your_service": "string — what you offer",
  "sequence_length": "integer — number of emails (default: 3)",
  "tone": "enum: formal | conversational | direct"
}
```

**Output Schema**

```json
{
  "emails": [
    {
      "sequence_number": "integer",
      "subject": "string",
      "body": "string",
      "send_delay_days": "integer",
      "personalization_hooks": "array[string]"
    }
  ],
  "total_emails": "integer",
  "recommended_send_window": "string"
}
```

**Monetization Potential**: HIGH
- Every B2B company needs outreach sequences; personalization at scale is a hard problem
- Competing tools: Apollo ($49/mo), Clay ($149/mo) — neither integrates with MCP/GHL
- Viable as: $0.50/sequence API, $39/mo subscription, bundled with GTM workflow service

---

### 3. `/draft-content` — Multi-Format Content Generator

**Source**: `CLAUDE.md`, `REVENUE-ENGINE-SPEC.md`; agent: `~/.claude/agents/content-marketing-engine.md`

| Field | Value |
|-------|-------|
| File path | `output/flywheel/` (output target) |
| Trigger | `/draft-content` |
| Agent backing | `~/.claude/agents/content-marketing-engine.md` |

**Input Schema**

```json
{
  "topic": "string — core topic or article title",
  "source_content": "string — optional source material to repurpose",
  "formats": "array[enum]: linkedin | twitter | devto | newsletter | reddit | youtube-script",
  "tone": "enum: technical | conversational | educational | thought-leader",
  "target_audience": "string",
  "call_to_action": "string — optional CTA for all formats"
}
```

**Output Schema**

```json
{
  "formats": {
    "linkedin": "string — 150-300 word post with hooks",
    "twitter": "string — thread (5-7 tweets)",
    "devto": "string — full article markdown (800-1200 words)",
    "newsletter": "string — email body (400-600 words)",
    "reddit": "string — subreddit-appropriate post",
    "youtube-script": "string — 5-7 min script with timestamps"
  },
  "seo_keywords": "array[string]",
  "hashtags": "array[string]",
  "estimated_reach_score": "integer 1-100"
}
```

**Monetization Potential**: MEDIUM-HIGH
- Content repurposing is a $10B+ market; single-input → multi-format is the key value prop
- Competing tools: Buffer AI ($18/mo), Jasper ($49/mo) — no MCP integration, no technical depth
- Viable as: $0.10/format API ($0.60 for all 6), $19/mo subscription, Fiverr $150/batch service

---

### 4. `/case-study` — Case Study Generator

**Source**: `CLAUDE.md`, `REVENUE-ENGINE-SPEC.md`; agent: `~/.claude/agents/case-study-generator.md`

| Field | Value |
|-------|-------|
| File path | `CASE_STUDY_*.md` files (output target) |
| Trigger | `/case-study` |
| Agent backing | `~/.claude/agents/case-study-generator.md` |

**Input Schema**

```json
{
  "project_name": "string",
  "client_type": "string — industry/company type",
  "problem_statement": "string — what was broken or missing",
  "solution_description": "string — what was built",
  "metrics": {
    "before": "object — baseline metrics (optional)",
    "after": "object — result metrics",
    "timeframe": "string"
  },
  "tech_stack": "array[string]",
  "format": "enum: star | narrative | one-pager | linkedin-post"
}
```

**Output Schema**

```json
{
  "case_study": "string — full case study in requested format",
  "headline": "string — attention-grabbing title",
  "stat_callouts": "array[string] — 3-5 bold metrics for visual emphasis",
  "excerpt": "string — 2-sentence summary for proposal attachment",
  "linkedin_version": "string — abbreviated version for social"
}
```

**Monetization Potential**: MEDIUM
- Case studies are high-leverage for sales but time-consuming to write; AI can 10x the speed
- Use case: agencies, consultants, SaaS companies wanting to productize their wins
- Viable as: $0.25/call API, bundled with GTM Workflow Builder service

---

### 5. `/weekly-status` — Freelance Progress Report

**Source**: `CLAUDE.md`, `REVENUE-ENGINE-SPEC.md`

| Field | Value |
|-------|-------|
| Input | Revenue tracker, client pipeline, content assets files |
| Trigger | `/weekly-status` |
| Output | Formatted weekly report markdown |

**Input Schema**

```json
{
  "week_ending": "string — ISO date",
  "revenue_tracker_path": "string — path to revenue-tracker.md",
  "pipeline_path": "string — path to client-pipeline.md",
  "content_assets_path": "string — path to content-assets.md",
  "focus_areas": "array[string] — optional override of default sections"
}
```

**Output Schema**

```json
{
  "report_markdown": "string — full weekly status report",
  "revenue_delta": "number — change from last week",
  "pipeline_score": "integer 1-100 — overall pipeline health",
  "top_priorities": "array[string] — top 3 actions for next week",
  "blockers": "array[string]"
}
```

**Monetization Potential**: LOW-MEDIUM
- Niche audience: freelancers managing multiple platforms
- Best used internally or as an add-on to GTM service
- Viable as: bundled with GTM service, not standalone product

---

### 6. `/revenue-update` — Revenue Tracker Update

**Source**: `CLAUDE.md`, `REVENUE-ENGINE-SPEC.md`

| Field | Value |
|-------|-------|
| Input | MCP data from Stripe, Gumroad, Upwork |
| Trigger | `/revenue-update` |
| Output | Updated `revenue-tracker.md` |

**Input Schema**

```json
{
  "data_sources": "array[enum]: stripe | gumroad | upwork | manual",
  "date_range": {
    "start": "string — ISO date",
    "end": "string — ISO date"
  },
  "manual_entries": "array[object] — optional manual transactions"
}
```

**Output Schema**

```json
{
  "updated_tracker_path": "string",
  "new_transactions": "integer",
  "revenue_added": "number",
  "summary": "string"
}
```

**Monetization Potential**: LOW
- Highly personalized to individual setup; hard to generalize
- Best used as internal automation, not a public product

---

## Skills Excluded From MCP Packaging

| Skill | Reason |
|-------|--------|
| `visualization-suite` | Already a full skill suite with its own runtime; MCP wrapping would add friction |
| `market-drift-monitor.skill` | Domain-specific (real estate); limited general market |

---

## MCP Packaging Priority

| Priority | Skill | Revenue Model | Reason |
|----------|-------|---------------|--------|
| 1 (HIGH) | `/proposal` | $0.25/call | Universal demand, clear ROI, easy to demo |
| 2 (HIGH) | `/outreach` | $0.50/sequence | High WTP, differentiated from Apollo/Clay |
| 3 (MED) | `/draft-content` | $0.10/format | Large TAM, easy to upsell full 6-format batch |
| 4 (MED) | `/case-study` | $0.25/call | Bundled value for GTM service clients |
| 5 (LOW) | `/weekly-status` | Bundled | Internal use first, productize later |
| 6 (LOW) | `/revenue-update` | Bundled | Too personalized for general sale |

---

## Recommended Initial Bundle: 4-Tool MCP Server

Package `/proposal` + `/outreach` + `/draft-content` + `/case-study` as `mcp-server-toolkit`.

**Rationale**: These 4 have clear inputs/outputs, demonstrable ROI, and map to the Agent37 marketplace's "productivity tool" category. The other 2 remain internal.

**Pricing model**:
- Free tier: 10 calls/month (for Agent37 listing, drives discovery)
- Pay-per-use: $0.10-$0.50/call (billed via Stripe)
- Monthly flat: $49/mo unlimited (primary revenue target)
