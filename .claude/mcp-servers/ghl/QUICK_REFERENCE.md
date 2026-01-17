# GHL MCP Server Quick Reference

One-page reference for common operations.

## Natural Language Commands

### Contact Management

```
✓ "Create contact named [Name] with email [email] and phone [phone]"
✓ "Add tags [tag1, tag2] to contact [id]"
✓ "Find all contacts tagged as [tag]"
✓ "Search for contacts named [query]"
✓ "Get contact details for [id]"
```

### Lead Scoring

```
✓ "Update lead score for [id] to [score] based on [factors]"
✓ "Score all unqualified leads using ML predictor"
✓ "Run comprehensive Claude analysis on contact [id]"
✓ "Sync DNA factors to GHL for contact [id]"
```

### Workflows & Communication

```
✓ "Trigger [workflow_id] workflow for contact [id]"
✓ "Send SMS to [id] saying '[message]'"
✓ "Notify agent about high-value lead [id]"
✓ "Start nurture campaign for warm leads"
```

### Opportunities

```
✓ "Create opportunity for contact [id] in [pipeline] at [stage]"
✓ "Create opportunity named [name] worth [value] for contact [id]"
```

## Tool Reference

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `create_ghl_contact` | Create new contact | name (req), email, phone, tags, custom_fields |
| `get_ghl_contact` | Retrieve contact | contact_id (req) |
| `search_ghl_contacts` | Search contacts | query, tags, limit |
| `update_lead_score` | AI-driven scoring | contact_id (req), score (req), factors (req), notes |
| `trigger_ghl_workflow` | Start workflow | contact_id (req), workflow_id (req), custom_values |
| `send_ghl_sms` | Send SMS | contact_id (req), message (req), message_type |
| `create_ghl_opportunity` | Create pipeline opp | contact_id (req), pipeline_id (req), stage_id (req), name (req) |

## Score Tiers

| Score | Tier | Auto Tags | Auto Actions |
|-------|------|-----------|--------------|
| 70-100 | Hot | `Hot Lead`, `AI_Scored_Hot` | Trigger high-value workflow if >=85 |
| 40-69 | Warm | `AI_Scored_Warm` | Standard nurture |
| 0-39 | Cold | `AI_Scored_Cold` | Re-engagement campaign |

## Integration Patterns

### Predictive Lead Scorer

```python
from ghl_real_estate_ai.services.predictive_lead_scorer import PredictiveLeadScorer
from server import GHLMCPServer

scorer = PredictiveLeadScorer()
ml_score = scorer.score_lead(lead_id, context)

mcp = GHLMCPServer()
await mcp.update_lead_score(
    contact_id=lead_id,
    score=ml_score.score,
    factors={"ml_tier": ml_score.tier}
)
```

### Claude Enhanced Scorer

```python
from ghl_real_estate_ai.services.claude_enhanced_lead_scorer import analyze_lead_with_claude
from server import GHLMCPServer

analysis = await analyze_lead_with_claude(lead_id, context)

mcp = GHLMCPServer()
await mcp.update_lead_score(
    contact_id=lead_id,
    score=analysis.final_score,
    factors={"next_action": analysis.next_best_action}
)
```

### GHL Sync Service

```python
from ghl_real_estate_ai.services.ghl_sync_service import GHLSyncService

sync = GHLSyncService()
await sync.sync_dna_to_ghl(contact_id, dna_payload)
```

## Common Workflows

### New Lead Qualification

```python
# 1. Create contact
contact = await mcp.create_ghl_contact(name=..., email=..., tags=["New Lead"])

# 2. Score with ML
ml_score = scorer.score_lead(contact["id"], context)

# 3. Sync to GHL
await mcp.update_lead_score(contact["id"], ml_score.score, factors)

# 4. Trigger workflow based on tier
if ml_score.tier == "hot":
    await mcp.trigger_ghl_workflow(contact["id"], "wf_hot_lead_handoff")
```

### Batch Scoring

```python
# Find unscored
leads = await mcp.search_ghl_contacts(tags=["Unscored"], limit=50)

# Score each
for lead in leads:
    ml_score = scorer.score_lead(lead["id"], context)
    await mcp.update_lead_score(lead["id"], ml_score.score, factors)
```

### High-Value Detection

```python
# Comprehensive analysis
analysis = await analyze_lead_with_claude(lead_id, context)

# If high-value, immediate action
if analysis.final_score >= 85:
    await mcp.trigger_ghl_workflow(lead_id, "wf_hot_lead_handoff")
    await mcp.send_ghl_sms(agent_id, f"Hot lead: {analysis.next_best_action}")
```

## Environment Variables

```bash
# Required
GHL_API_KEY=your_key
GHL_LOCATION_ID=your_location
ANTHROPIC_API_KEY=your_key

# Optional
GHL_AGENCY_API_KEY=agency_key
GHL_AGENCY_ID=agency_id
CUSTOM_FIELD_LEAD_SCORE=lead_score
CUSTOM_FIELD_BUDGET=budget
CUSTOM_FIELD_TIMELINE=timeline
NOTIFY_AGENT_WORKFLOW_ID=wf_id
```

## Rate Limits

- **60 requests/minute** (normal)
- **10 request burst** (spikes)
- Auto-retry with exponential backoff

## Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 401 | Unauthorized | Check API key |
| 404 | Not found | Verify contact/location ID |
| 429 | Rate limit | Wait 60s, retry |
| 500 | Server error | Check GHL status |

## Test Mode

Enable in `.env`:
```bash
TEST_MODE=true
```

All operations return mock data (no API calls).

## File Locations

```
.claude/mcp-servers/ghl/
├── server.py              # MCP server
├── test_installation.py   # Tests
├── README.md              # Full docs
├── USAGE_EXAMPLES.md      # Examples
├── INSTALLATION.md        # Setup guide
└── QUICK_REFERENCE.md     # This file

.claude/mcp-profiles/
└── backend-services.json  # Config

ghl_real_estate_ai/services/
├── ghl_client.py
├── ghl_sync_service.py
├── predictive_lead_scorer.py
└── claude_enhanced_lead_scorer.py
```

## Performance

- Contact create: ~200ms
- Contact search: ~150ms
- Score update: ~250ms
- Workflow trigger: ~180ms
- SMS send: ~220ms

## Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure .env
# Add GHL_API_KEY, GHL_LOCATION_ID, ANTHROPIC_API_KEY

# 3. Test
python3 .claude/mcp-servers/ghl/test_installation.py

# 4. Use
export CLAUDE_PROFILE=backend-services
claude "Create contact named John Smith with email john@example.com"
```

---

**Version**: 1.0.0
**Last Updated**: January 16, 2026
