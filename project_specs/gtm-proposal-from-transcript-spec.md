# Agent Spec: Proposal-from-Transcript

**Version**: 1.0 | **Date**: 2026-02-19 | **Owner**: gtm-platform-builder
**Purpose**: Transform a sales call transcript into a structured, GHL-ready proposal

---

## Overview

The Proposal-from-Transcript agent takes a raw sales call transcript (any format — Otter.ai export, Zoom auto-transcript, manual notes), extracts the key qualification signals, and produces:

1. A formatted proposal document (PDF-ready markdown)
2. A GHL contact record update (fields + tags populated)
3. A GHL workflow trigger (moves deal to next stage)

This agent is the core deliverable of the GTM Workflow Builder Tier 1 service.

---

## Input

### Primary Input

```json
{
  "transcript": "string — raw transcript text (min 200 words)",
  "ghl_contact_id": "string — optional; if provided, agent reads existing GHL fields",
  "proposal_tier": "enum: starter | growth | enterprise — optional override",
  "your_service_name": "string — e.g. 'GTM Workflow Builder'",
  "your_pricing": {
    "tier1_price": "integer",
    "tier2_price": "integer",
    "tier3_price": "integer"
  }
}
```

### Optional GHL Enrichment (if `ghl_contact_id` provided)

Agent reads these GHL fields before generating proposal:
- Contact name, company, email
- Pipeline stage
- Tags applied
- Existing custom fields (budget, pain_point, timeline)
- Previous conversation notes

---

## Output

### Artifact 1: Proposal Document

```json
{
  "proposal_markdown": "string — full proposal in markdown (PDF-ready)",
  "proposal_title": "string",
  "recommended_tier": "enum: starter | growth | enterprise",
  "total_price": "integer",
  "timeline_weeks": "integer",
  "executive_summary": "string — 3-sentence hook",
  "pain_points_addressed": "array[string] — extracted from transcript",
  "deliverables_list": "array[string]",
  "roi_statement": "string — quantified where possible"
}
```

### Artifact 2: GHL Update Payload

```json
{
  "contact_id": "string",
  "fields_to_update": {
    "custom_field_budget": "string — extracted budget from transcript",
    "custom_field_pain_point": "string — primary pain point",
    "custom_field_timeline": "string — e.g. '30 days', 'ASAP', 'Q2'",
    "custom_field_proposal_tier": "string",
    "custom_field_proposal_sent_date": "string — ISO date"
  },
  "tags_to_add": ["Proposal-Sent", "Tier-{tier}"],
  "tags_to_remove": ["Needs-Qualifying"],
  "note_body": "string — summary of call + proposal details for GHL timeline"
}
```

### Artifact 3: Workflow Trigger

```json
{
  "workflow_id": "string — from env var PROPOSAL_WORKFLOW_ID",
  "contact_id": "string",
  "trigger_reason": "string — human-readable log entry"
}
```

---

## System Prompt Outline

```
You are a senior sales consultant and proposal writer. You specialize in AI/automation services.

Given a sales call transcript, you will:

1. EXTRACT key qualification signals:
   - Budget (explicit or implied from company size/urgency)
   - Timeline (when do they want this live?)
   - Primary pain point (1 sentence)
   - Decision maker present? (yes/no)
   - Objections raised
   - Technical sophistication (beginner/intermediate/advanced)

2. DETERMINE the right service tier:
   - Starter ($2,500): Solo operator, one clear problem, 4-week timeline OK
   - Growth ($3,500): Team, multiple workflows needed, urgency present
   - Enterprise ($5,000): Budget >$5K mentioned, pipeline >$50K/mo, complex integration

3. WRITE the proposal using this structure:
   - Executive Summary (3 sentences, lead with their pain point)
   - Problem Statement (their words from transcript, validated)
   - Proposed Solution (what you'll build, specifically)
   - Deliverables (bulleted, concrete)
   - Timeline (week-by-week)
   - Investment (price, payment terms)
   - Next Steps (book kickoff call, sign agreement, pay deposit)

4. TONE: Confident, specific, no fluff. Use numbers where available. Reference their exact words.

CONSTRAINTS:
- Never invent metrics not supported by the transcript
- If budget is unclear, use the recommended tier's default price but flag it
- If timeline is unrealistic, note it politely in Next Steps
- Proposal should be 400-600 words (executive + body, not counting deliverables list)
```

---

## Tool Schemas

### Tool 1: `read_ghl_contact`

```json
{
  "name": "read_ghl_contact",
  "description": "Read a GHL contact record including custom fields, tags, and recent notes",
  "inputSchema": {
    "type": "object",
    "properties": {
      "contact_id": { "type": "string" }
    },
    "required": ["contact_id"]
  }
}
```

**Maps to**: GHL MCP `get_contact` tool

### Tool 2: `update_ghl_contact`

```json
{
  "name": "update_ghl_contact",
  "description": "Update GHL contact fields, add/remove tags, and add a timeline note",
  "inputSchema": {
    "type": "object",
    "properties": {
      "contact_id": { "type": "string" },
      "fields": { "type": "object" },
      "tags_add": { "type": "array", "items": { "type": "string" } },
      "tags_remove": { "type": "array", "items": { "type": "string" } },
      "note": { "type": "string" }
    },
    "required": ["contact_id"]
  }
}
```

**Maps to**: GHL MCP `update_contact`, `add_tag`, `remove_tag`, `create_note`

### Tool 3: `trigger_ghl_workflow`

```json
{
  "name": "trigger_ghl_workflow",
  "description": "Trigger a named GHL workflow for a contact",
  "inputSchema": {
    "type": "object",
    "properties": {
      "contact_id": { "type": "string" },
      "workflow_id": { "type": "string" }
    },
    "required": ["contact_id", "workflow_id"]
  }
}
```

**Maps to**: GHL MCP `trigger_workflow`

### Tool 4: `extract_transcript_signals`

```json
{
  "name": "extract_transcript_signals",
  "description": "Parse a sales call transcript and return structured qualification data",
  "inputSchema": {
    "type": "object",
    "properties": {
      "transcript": { "type": "string" },
      "output_format": {
        "type": "object",
        "properties": {
          "budget": { "type": "string" },
          "timeline": { "type": "string" },
          "pain_point": { "type": "string" },
          "decision_maker_present": { "type": "boolean" },
          "objections": { "type": "array", "items": { "type": "string" } },
          "technical_level": { "type": "string", "enum": ["beginner", "intermediate", "advanced"] }
        }
      }
    },
    "required": ["transcript"]
  }
}
```

**Implementation**: Handled by the LLM itself (structured output extraction), not a real MCP tool

---

## GHL MCP Integration

### Environment Variables Required

```bash
GHL_API_KEY=                    # GoHighLevel API key
GHL_LOCATION_ID=                # Sub-account location ID
PROPOSAL_WORKFLOW_ID=           # GHL workflow ID to trigger on proposal creation
```

### GHL MCP Tools Used

| Action | GHL MCP Tool | Notes |
|--------|-------------|-------|
| Read contact | `get_contact(contact_id)` | Reads all fields including custom |
| Update fields | `update_contact(contact_id, fields)` | Custom fields by field ID |
| Add tags | `add_tag(contact_id, tag_name)` | Creates tag if not exists |
| Remove tags | `remove_tag(contact_id, tag_name)` | No-op if tag absent |
| Add note | `create_note(contact_id, body)` | Appears in GHL timeline |
| Trigger workflow | `trigger_workflow(contact_id, workflow_id)` | Async — fires and forgets |

---

## Execution Flow

```
1. Receive transcript + optional ghl_contact_id
2. IF ghl_contact_id → call read_ghl_contact → enrich context
3. Call extract_transcript_signals (LLM structured extraction)
4. Determine tier based on signals + existing GHL data
5. Generate proposal_markdown (full LLM generation)
6. Build GHL update payload (fields + tags + note)
7. Call update_ghl_contact with payload
8. Call trigger_ghl_workflow with PROPOSAL_WORKFLOW_ID
9. Return: { proposal_markdown, ghl_update_result, workflow_trigger_result }
```

---

## Error Handling

| Error | Behavior |
|-------|----------|
| GHL contact not found | Proceed without GHL enrichment, flag in output |
| GHL update fails | Log error, return proposal (don't block on CRM write) |
| Transcript too short (<200 words) | Return error: "Transcript too short for reliable extraction" |
| Budget not detected | Use tier 1 default, add flag: "budget_inferred: true" |
| Workflow ID not set | Skip workflow trigger, log warning |

---

## Testing Strategy

1. **Unit**: Test `extract_transcript_signals` with 5 sample transcripts (hot/warm/cold, various budgets)
2. **Integration**: Mock GHL MCP tools, verify correct field updates
3. **End-to-end**: Run with real GHL sandbox contact, verify proposal + CRM update + workflow

### Sample Test Transcripts

Stored in `tests/fixtures/transcripts/`:
- `transcript_hot_lead.txt` — clear budget, urgent timeline, decision maker present
- `transcript_warm_lead.txt` — budget unclear, interested but not urgent
- `transcript_cold_lead.txt` — no budget mentioned, research phase

---

## Deployment

```python
# Standalone usage
from agents.gtm_proposal_agent import ProposalFromTranscriptAgent

agent = ProposalFromTranscriptAgent(
    ghl_api_key=os.getenv("GHL_API_KEY"),
    ghl_location_id=os.getenv("GHL_LOCATION_ID"),
    proposal_workflow_id=os.getenv("PROPOSAL_WORKFLOW_ID")
)

result = await agent.run(
    transcript=transcript_text,
    ghl_contact_id="abc123",
    your_service_name="GTM Workflow Builder",
    your_pricing={"tier1": 2500, "tier2": 3500, "tier3": 5000}
)
```
