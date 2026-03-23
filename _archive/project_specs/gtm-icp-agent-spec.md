# Agent Spec: ICP Definition Agent

**Version**: 1.0 | **Date**: 2026-02-19 | **Owner**: gtm-platform-builder
**Purpose**: Analyze GHL contact data to produce an Ideal Customer Profile document

---

## Overview

The ICP Definition Agent queries GHL contact records (via MCP), segments them by closed/won vs. lost/ghosted outcomes, and produces a structured ICP document that answers: "Who should we be talking to, and why?"

This agent is a core deliverable of the GTM Workflow Builder service (all tiers include it).

---

## Input

```json
{
  "ghl_location_id": "string — which sub-account to query",
  "contact_filters": {
    "tags": "array[string] — e.g. ['Qualified', 'Closed-Won', 'Closed-Lost']",
    "pipeline_stage": "string — optional stage name filter",
    "date_range": {
      "start": "string — ISO date",
      "end": "string — ISO date"
    },
    "min_contacts": "integer — minimum records to analyze (default: 10)"
  },
  "closed_won_tag": "string — tag indicating won deal (default: 'Closed-Won')",
  "closed_lost_tag": "string — tag indicating lost deal (default: 'Closed-Lost')",
  "your_service_description": "string — what service you sell",
  "output_format": "enum: full | one-pager | linkedin-post"
}
```

---

## Output

### Primary: ICP Document

```json
{
  "icp_document": "string — full ICP in markdown",
  "icp_summary": "string — 3-sentence summary for proposals",
  "confidence_score": "integer 1-100 — based on sample size and signal clarity",
  "sample_size": {
    "total_analyzed": "integer",
    "closed_won": "integer",
    "closed_lost": "integer"
  },
  "top_icp_signals": "array[string] — top 5 most predictive attributes",
  "anti_icp_signals": "array[string] — top 5 disqualifying attributes",
  "recommended_tags": "array[string] — new GHL tags to create for ICP scoring"
}
```

### Secondary: GHL Tag Recommendations

```json
{
  "tags_to_create": [
    {
      "tag_name": "string",
      "description": "string",
      "apply_when": "string — rule in plain English"
    }
  ],
  "scoring_rubric": "string — point-based scoring guide for SDRs"
}
```

---

## System Prompt Outline

```
You are a B2B market segmentation analyst. You analyze CRM contact records to identify
the characteristics of ideal vs. non-ideal customers.

You receive a dataset of contacts with the following fields (where available):
- Company name, industry, company size
- Contact role/title
- Custom fields: budget, timeline, pain_point, source
- Tags applied (especially 'Closed-Won' vs 'Closed-Lost' or 'Ghosted')
- Pipeline stage history
- Conversation notes (if available)
- Time to close (if calculable from timestamps)

YOUR ANALYSIS PROCESS:

1. SEGMENT contacts into:
   - Group A: Closed-Won (or "Qualified" + revenue logged)
   - Group B: Closed-Lost or Ghosted (never converted)
   - Group C: In-Pipeline (exclude from ICP, note as pending)

2. FIND PATTERNS in Group A (ideal customers):
   - Industry concentration
   - Company size patterns
   - Role/title of decision maker
   - Budget range mentioned or inferred
   - Timeline urgency (how fast did they move?)
   - Pain points mentioned in notes
   - Source (where did they come from?)
   - Time to close (average days)

3. FIND ANTI-PATTERNS in Group B (bad fit):
   - What signals appeared in lost deals?
   - Common objections
   - Characteristics that correlated with ghosting

4. PRODUCE the ICP document:
   - Demographic profile (company, role, size)
   - Behavioral signals (what actions did ideal customers take?)
   - Trigger events (what made them reach out?)
   - Anti-ICP signals (what to avoid)
   - Messaging recommendations (what resonated)
   - Recommended GHL tags for ongoing scoring

TONE: Data-driven but readable. Use percentages and ratios where the data supports it.
Flag low-confidence conclusions (< 10 data points) clearly.
```

---

## Tool Schemas

### Tool 1: `query_ghl_contacts`

```json
{
  "name": "query_ghl_contacts",
  "description": "Query GHL contacts with filters, returning fields and tags",
  "inputSchema": {
    "type": "object",
    "properties": {
      "location_id": { "type": "string" },
      "tags": { "type": "array", "items": { "type": "string" } },
      "pipeline_stage": { "type": "string" },
      "date_range_start": { "type": "string" },
      "date_range_end": { "type": "string" },
      "limit": { "type": "integer", "default": 100 }
    },
    "required": ["location_id"]
  }
}
```

**Maps to**: GHL MCP `search_contacts` with tag and pipeline filters

### Tool 2: `get_contact_notes`

```json
{
  "name": "get_contact_notes",
  "description": "Retrieve all timeline notes for a GHL contact",
  "inputSchema": {
    "type": "object",
    "properties": {
      "contact_id": { "type": "string" }
    },
    "required": ["contact_id"]
  }
}
```

**Maps to**: GHL MCP `get_notes(contact_id)`

### Tool 3: `get_pipeline_stages`

```json
{
  "name": "get_pipeline_stages",
  "description": "List all pipeline stages and their names for the location",
  "inputSchema": {
    "type": "object",
    "properties": {
      "location_id": { "type": "string" }
    },
    "required": ["location_id"]
  }
}
```

**Maps to**: GHL MCP `get_pipelines(location_id)`

### Tool 4: `create_ghl_tag`

```json
{
  "name": "create_ghl_tag",
  "description": "Create a new tag in GHL for ICP scoring",
  "inputSchema": {
    "type": "object",
    "properties": {
      "location_id": { "type": "string" },
      "tag_name": { "type": "string" },
      "description": { "type": "string" }
    },
    "required": ["location_id", "tag_name"]
  }
}
```

**Maps to**: GHL MCP `create_tag`

---

## GHL Contact Fields Analyzed

| Field Type | Field Name | Source |
|------------|-----------|--------|
| Standard | `company`, `email`, `phone` | GHL built-in |
| Standard | `source` (lead source) | GHL built-in |
| Custom | `budget` | Custom field |
| Custom | `pain_point` | Custom field |
| Custom | `timeline` | Custom field |
| Custom | `company_size` | Custom field |
| Custom | `role_title` | Custom field |
| Tags | Applied tags | GHL tags system |
| Pipeline | `stage_name`, `stage_changed_at` | Pipeline data |

---

## ICP Document Structure

```markdown
# Ideal Customer Profile — [Company Name]
*Generated: [date] | Based on [N] contacts*

## Executive Summary
[3-sentence overview of who your ideal customer is]

## Demographic Profile

### Company
- Industry: [top 2-3 industries from data]
- Size: [employee range or revenue range]
- Stage: [startup / growth / enterprise]

### Contact Role
- Primary decision maker: [title]
- Common influencers: [other roles in the deal]
- Who to avoid (no authority): [titles that lead to dead ends]

## Behavioral Signals

### Green Flags (ICP-positive)
- [Signal 1: e.g., "Responded within 24 hours to first outreach"]
- [Signal 2: e.g., "Mentioned specific pain point: manual proposal writing"]
- [Signal 3: e.g., "Had a GHL account already set up"]

### Red Flags (Anti-ICP)
- [Signal 1: e.g., "Budget objection raised before demo"]
- [Signal 2: e.g., "Requested custom work not in standard scope"]
- [Signal 3: e.g., "No GHL account, not open to adopting one"]

## Trigger Events
What caused ideal customers to reach out:
- [Event 1: e.g., "New hire in sales role, building from scratch"]
- [Event 2: e.g., "Failed implementation with previous agency"]
- [Event 3: e.g., "Saw LinkedIn post about GHL automation"]

## Messaging That Resonated
- [Angle 1: e.g., "Done-for-you, not DIY"]
- [Angle 2: e.g., "Live in 4 weeks, not 4 months"]
- [Angle 3: e.g., "ROI framing: close 1 extra deal to recoup cost"]

## Recommended GHL Tags for Ongoing Scoring

| Tag | Apply When | ICP Signal Strength |
|-----|-----------|---------------------|
| `ICP-High` | Matches 4+ ICP signals | Strong |
| `ICP-Medium` | Matches 2-3 ICP signals | Moderate |
| `Budget-Confirmed` | Budget mentioned in call notes | Strong |
| `Decision-Maker` | Primary DM on call | Strong |
| `Anti-ICP` | Matches 2+ anti-ICP signals | Disqualify |

## Confidence Notes
- Sample size: [N] contacts ([X] won, [Y] lost)
- Confidence: [High/Medium/Low] — [reason if not High]
- Recommended: Re-run after [N] more closed deals for higher confidence
```

---

## Execution Flow

```
1. Query GHL contacts with filters → list of contact records
2. IF sample < min_contacts → return error with explanation
3. Segment contacts: won / lost / in-pipeline
4. For top 20 contacts (10 won + 10 lost): fetch notes for richer context
5. Run ICP analysis (LLM) against full dataset
6. Generate ICP document in requested format
7. Build tag recommendation list
8. IF create_tags=True → call create_ghl_tag for each recommended tag
9. Return full ICP output
```

---

## Error Handling

| Error | Behavior |
|-------|----------|
| Fewer than 5 contacts found | Return error: "Insufficient data — need at least 5 closed contacts" |
| No won/lost segmentation possible | Analyze all contacts as generic, flag confidence as Low |
| GHL MCP unavailable | Return error: "GHL connection required for this agent" |
| All contacts missing custom fields | Proceed with available data (tags + pipeline only), flag gaps |
| Notes API fails | Skip notes enrichment, proceed with field data |

---

## Deployment

```python
# Standalone usage
from agents.gtm_icp_agent import ICPDefinitionAgent

agent = ICPDefinitionAgent(
    ghl_api_key=os.getenv("GHL_API_KEY"),
    ghl_location_id=os.getenv("GHL_LOCATION_ID")
)

result = await agent.run(
    contact_filters={
        "tags": ["Qualified", "Closed-Won", "Closed-Lost"],
        "date_range": {"start": "2025-01-01", "end": "2026-02-19"},
        "min_contacts": 15
    },
    closed_won_tag="Closed-Won",
    closed_lost_tag="Closed-Lost",
    your_service_description="GTM Workflow Builder — AI-powered sales automation",
    output_format="full"
)

print(result["icp_document"])
```
