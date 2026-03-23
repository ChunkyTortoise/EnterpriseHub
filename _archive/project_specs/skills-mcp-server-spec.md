# Skills MCP Server Architecture Spec

**Server name**: `mcp-server-toolkit`
**Version**: 1.0 | **Date**: 2026-02-19 | **Owner**: gtm-platform-builder
**Target marketplace**: Agent37

---

## Overview

`mcp-server-toolkit` is a monetizable MCP server that exposes 4 AI-powered productivity tools as callable MCP tools. Any Claude agent, Claude Desktop user, or MCP-compatible client can connect to this server and call these tools.

The server runs locally or as a hosted service. Revenue is generated via per-call billing (Stripe) or monthly subscription.

---

## Architecture

```
Client (Claude Desktop / Claude Agent)
    │
    │ MCP stdio or SSE transport
    ▼
mcp-server-toolkit
    ├── tools/proposal.ts      — /proposal skill
    ├── tools/outreach.ts      — /outreach skill
    ├── tools/draft-content.ts — /draft-content skill
    └── tools/case-study.ts    — /case-study skill
         │
         │ HTTP/SDK
         ▼
    Anthropic API (claude-haiku-4-5 for cost, claude-sonnet-4-6 for quality)
```

### Transport

- **Primary**: `stdio` (standard MCP transport, works with Claude Desktop)
- **Future**: HTTP+SSE for hosted deployment (enables per-call billing)

### Runtime

- **Language**: TypeScript (Node.js 20+)
- **Framework**: `@modelcontextprotocol/sdk` v1.x
- **LLM calls**: `@anthropic-ai/sdk`
- **Auth** (future hosted mode): JWT bearer token validated per-request

---

## Tool Specifications

### Tool 1: `generate_proposal`

**Description**: Generate a tailored freelance or agency proposal from a job description

**JSON Schema — Input**

```json
{
  "type": "object",
  "properties": {
    "job_title": {
      "type": "string",
      "description": "Job posting title"
    },
    "job_description": {
      "type": "string",
      "description": "Full job description text",
      "minLength": 100
    },
    "budget": {
      "type": "string",
      "description": "Budget from posting (e.g. '$5,000', '$75/hr')"
    },
    "client_background": {
      "type": "string",
      "description": "Any known context about the client or company"
    },
    "your_skills": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Skills to highlight (overrides defaults if provided)"
    },
    "tone": {
      "type": "string",
      "enum": ["technical", "conversational", "direct"],
      "default": "conversational"
    }
  },
  "required": ["job_title", "job_description"]
}
```

**Output**: `string` — 300-500 word proposal, ready to paste into Upwork or Fiverr

**Model**: `claude-haiku-4-5` (fast, cost-effective for proposal generation)

**Pricing**: $0.25/call

---

### Tool 2: `generate_outreach_sequence`

**Description**: Create a personalized cold outreach email sequence (1-5 emails)

**JSON Schema — Input**

```json
{
  "type": "object",
  "properties": {
    "company_name": {
      "type": "string"
    },
    "contact_name": {
      "type": "string"
    },
    "contact_role": {
      "type": "string",
      "description": "e.g. 'VP of Sales', 'Founder', 'Head of Marketing'"
    },
    "company_pain_point": {
      "type": "string",
      "description": "Researched or inferred pain point for this company"
    },
    "your_service": {
      "type": "string",
      "description": "What you offer (1-2 sentences)"
    },
    "sequence_length": {
      "type": "integer",
      "minimum": 1,
      "maximum": 5,
      "default": 3
    },
    "tone": {
      "type": "string",
      "enum": ["formal", "conversational", "direct"],
      "default": "conversational"
    },
    "your_name": {
      "type": "string"
    },
    "social_proof": {
      "type": "string",
      "description": "Optional: one stat or result to include (e.g. '89% cost reduction')"
    }
  },
  "required": ["company_name", "contact_name", "company_pain_point", "your_service"]
}
```

**Output**: JSON string with array of `{ subject, body, send_delay_days }` objects

**Model**: `claude-sonnet-4-6` (quality matters for outreach)

**Pricing**: $0.50/call

---

### Tool 3: `draft_content`

**Description**: Repurpose a topic or article into multiple content formats simultaneously

**JSON Schema — Input**

```json
{
  "type": "object",
  "properties": {
    "topic": {
      "type": "string",
      "description": "Core topic, article title, or source content to repurpose",
      "minLength": 10
    },
    "source_content": {
      "type": "string",
      "description": "Optional: existing article or post to repurpose"
    },
    "formats": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["linkedin", "twitter", "devto", "newsletter", "reddit", "youtube-script"]
      },
      "description": "Which formats to generate. Defaults to all 6 if not specified."
    },
    "tone": {
      "type": "string",
      "enum": ["technical", "conversational", "educational", "thought-leader"],
      "default": "educational"
    },
    "target_audience": {
      "type": "string",
      "description": "e.g. 'CTOs at Series B startups', 'freelance developers'"
    },
    "call_to_action": {
      "type": "string",
      "description": "Optional CTA to include in all formats"
    }
  },
  "required": ["topic"]
}
```

**Output**: JSON string with a key per requested format, each containing the content string

**Model**: `claude-haiku-4-5` (volume tool, cost matters)

**Pricing**: $0.10/format (so $0.60 for all 6)

---

### Tool 4: `generate_case_study`

**Description**: Transform project metrics and outcomes into a professional case study

**JSON Schema — Input**

```json
{
  "type": "object",
  "properties": {
    "project_name": {
      "type": "string"
    },
    "client_type": {
      "type": "string",
      "description": "Industry or company type (anonymized is fine)"
    },
    "problem_statement": {
      "type": "string",
      "description": "What was broken, missing, or painful before your work"
    },
    "solution_description": {
      "type": "string",
      "description": "What you built or implemented"
    },
    "metrics": {
      "type": "object",
      "properties": {
        "before": { "type": "object", "description": "Baseline metrics (optional)" },
        "after": { "type": "object", "description": "Result metrics" },
        "timeframe": { "type": "string", "description": "e.g. '30 days', '3 months'" }
      },
      "required": ["after"]
    },
    "tech_stack": {
      "type": "array",
      "items": { "type": "string" }
    },
    "format": {
      "type": "string",
      "enum": ["star", "narrative", "one-pager", "linkedin-post"],
      "default": "narrative"
    }
  },
  "required": ["project_name", "problem_statement", "solution_description", "metrics"]
}
```

**Output**: JSON string with `{ case_study, headline, stat_callouts, excerpt, linkedin_version }`

**Model**: `claude-sonnet-4-6` (quality matters for sales materials)

**Pricing**: $0.25/call

---

## Pricing Model

### Per-Call (API mode)

| Tool | Price per Call |
|------|---------------|
| `generate_proposal` | $0.25 |
| `generate_outreach_sequence` | $0.50 |
| `draft_content` | $0.10/format |
| `generate_case_study` | $0.25 |

### Subscription (hosted mode)

| Tier | Price | Calls/Month | Overage |
|------|-------|-------------|---------|
| Free | $0 | 10 (any tool) | N/A |
| Starter | $19/mo | 100 calls | $0.25/call |
| Pro | $49/mo | Unlimited | — |

### Implementation Path

1. **Phase 1** (now): stdio transport, no billing — use locally or give clients direct access
2. **Phase 2** (hosted): HTTP+SSE, Stripe metered billing via `stripe.usageRecords.create()`
3. **Phase 3** (marketplace): Agent37 listing, in-app purchase via Agent37's billing rails

---

## Agent37 Marketplace Requirements

Based on Agent37 submission guidelines for MCP tools:

### Listing Requirements

| Field | Value |
|-------|-------|
| Server name | `mcp-server-toolkit` |
| Category | Productivity / Content Creation |
| Tagline | "4 AI tools for freelancers: proposals, outreach, content, case studies" |
| Demo video | Required — 2-3 min Loom showing each tool in Claude Desktop |
| README | Must include installation instructions + all tool schemas |
| License | MIT |
| Pricing | Free tier required for listing approval |

### Technical Requirements

| Requirement | Status |
|-------------|--------|
| Valid `package.json` with `name`, `version`, `description` | Required |
| MCP SDK `^1.0.0` | Required |
| `stdio` transport support | Required |
| Tool schemas match JSON Schema draft-07 | Required |
| Error responses follow MCP error format | Required |
| README with `npx mcp-server-toolkit` quickstart | Required |

### Submission Checklist

- [ ] Server starts with `npx mcp-server-toolkit` (or `node dist/index.js`)
- [ ] All 4 tools listed in `listTools` response
- [ ] Each tool accepts test input without crashing
- [ ] README includes: install, config (env vars), tool descriptions, examples
- [ ] `ANTHROPIC_API_KEY` env var documented
- [ ] Demo video uploaded to Agent37 submission form

---

## File Structure

```
mcp-server-toolkit/
├── package.json              — name, version, dependencies, bin entry
├── tsconfig.json             — TypeScript config targeting Node 20
├── src/
│   ├── index.ts              — MCP server entry point, registers all tools
│   ├── tools/
│   │   ├── proposal.ts       — generate_proposal tool
│   │   ├── outreach.ts       — generate_outreach_sequence tool
│   │   ├── draft-content.ts  — draft_content tool
│   │   └── case-study.ts     — generate_case_study tool
│   ├── prompts/
│   │   ├── proposal.prompt.ts
│   │   ├── outreach.prompt.ts
│   │   ├── draft-content.prompt.ts
│   │   └── case-study.prompt.ts
│   └── utils/
│       ├── anthropic.ts      — shared Anthropic client
│       └── schema.ts         — shared Zod validation
├── dist/                     — compiled JS (gitignored)
├── tests/
│   ├── proposal.test.ts
│   ├── outreach.test.ts
│   ├── draft-content.test.ts
│   └── case-study.test.ts
└── README.md                 — Agent37 marketplace copy + quickstart
```

---

## Environment Variables

```bash
ANTHROPIC_API_KEY=            # Required — your Anthropic API key
MCP_DEFAULT_MODEL=            # Optional — default: claude-haiku-4-5
MCP_QUALITY_MODEL=            # Optional — default: claude-sonnet-4-6
MCP_MAX_TOKENS=               # Optional — default: 2048
```

---

## Error Handling

All tools follow MCP error response format:

```typescript
// MCP error response
{
  "isError": true,
  "content": [
    {
      "type": "text",
      "text": "Error: [human-readable message]"
    }
  ]
}
```

| Error Type | Response |
|------------|----------|
| Missing required input | isError: true, message: "Missing required field: [field]" |
| Anthropic API error | isError: true, message: "LLM call failed: [error message]" |
| Input too short | isError: true, message: "Input too short: [field] requires minimum [N] characters" |
| API key not set | isError: true, message: "ANTHROPIC_API_KEY environment variable not set" |
