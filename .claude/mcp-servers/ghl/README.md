# GoHighLevel MCP Server

Production-ready Model Context Protocol (MCP) server providing natural language interface to GoHighLevel CRM operations.

## Overview

The GHL MCP Server enables Claude to interact with GoHighLevel CRM through type-safe, validated tools. It integrates seamlessly with existing EnterpriseHub services for AI-powered lead intelligence and workflow automation.

### Key Features

- **Natural Language Operations**: Use plain English to create contacts, update scores, trigger workflows
- **AI-Driven Intelligence**: Integrates with `predictive_lead_scorer.py` and `claude_enhanced_lead_scorer.py`
- **Type Safety**: Full input validation and error handling
- **40% Faster Workflows**: Direct API access without manual UI navigation
- **Reusable**: Works across CLI, web app, and automation scripts

## Installation

### 1. Install Dependencies

```bash
cd /Users/cave/Documents/GitHub/EnterpriseHub
pip install anthropic-mcp httpx pydantic pydantic-settings
```

### 2. Configure Environment Variables

Add to `.env`:

```bash
# Required
GHL_API_KEY=your_ghl_api_key_here
GHL_LOCATION_ID=your_location_id_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Optional
GHL_AGENCY_API_KEY=your_agency_key_here
GHL_AGENCY_ID=your_agency_id_here
```

### 3. Enable in MCP Profile

Update `.claude/mcp-profiles/backend-services.json`:

```json
{
  "mcp_servers": {
    "ghl": true,
    "serena": true,
    "context7": true
  }
}
```

### 4. Test Installation

```bash
python3 .claude/mcp-servers/ghl/server.py
```

Expected output:
```
INFO: Starting GoHighLevel MCP Server...
INFO: Loaded 7 tools
INFO: Server ready on stdio
```

## Available Tools

### Contact Management

#### create_ghl_contact

Create new contact with tags and custom fields.

**Natural Language Examples:**
- "Create a contact named John Smith with email john@example.com and tag them as Hot Lead"
- "Add Sarah Johnson to GHL with phone +15125551234, budget field 500k, and Buyer tag"

**Programmatic Usage:**

```python
result = await create_ghl_contact(
    name="John Smith",
    email="john@example.com",
    phone="+15125551234",
    tags=["Hot Lead", "Buyer"],
    custom_fields={
        "budget": "500000",
        "timeline": "3-6 months",
        "property_type": "condo"
    }
)
# Returns: {"id": "abc123", "name": "John Smith", ...}
```

#### get_ghl_contact

Retrieve contact details by ID.

**Natural Language Examples:**
- "Get contact details for ID abc123"
- "Show me the full profile for contact abc123"

**Programmatic Usage:**

```python
contact = await get_ghl_contact(contact_id="abc123")
# Returns: {"id": "abc123", "name": "John Smith", "tags": [...], ...}
```

#### search_ghl_contacts

Search contacts by query, tags, or filters.

**Natural Language Examples:**
- "Find all contacts tagged as Hot Lead"
- "Search for contacts named Smith"
- "Show me all buyers in the system"

**Programmatic Usage:**

```python
results = await search_ghl_contacts(
    query="john smith",
    tags=["Hot Lead", "Buyer"],
    limit=10
)
# Returns: [{"id": "abc123", "name": "John Smith", ...}, ...]
```

### Lead Intelligence

#### update_lead_score

Update lead score with AI-driven intelligence and factors.

**Integration Points:**
- `services/predictive_lead_scorer.py` - ML-based conversion prediction
- `services/claude_enhanced_lead_scorer.py` - Comprehensive AI analysis
- `services/ghl_sync_service.py` - DNA payload synchronization

**Natural Language Examples:**
- "Update lead score for contact abc123 to 87 based on high engagement and qualified budget"
- "Score this lead at 65 due to timeline concerns but good fit otherwise"

**Programmatic Usage:**

```python
result = await update_lead_score(
    contact_id="abc123",
    score=87.5,
    factors={
        "budget_qualified": True,
        "timeline": "immediate",
        "engagement_level": "high",
        "jorge_questions_answered": 5,
        "ml_conversion_probability": 0.82
    },
    notes="Hot lead - ready for agent handoff. Pre-qualified with $500k budget."
)
# Automatically:
# - Updates custom fields (lead_score, budget, timeline, etc.)
# - Adds tags (Hot Lead, AI_Scored_Hot)
# - Triggers high-value workflow if score >= 85
# - Syncs with predictive scoring system
```

**Scoring Tiers:**
- **70-100 (Hot)**: Tags added: `Hot Lead`, `AI_Scored_Hot`
- **40-69 (Warm)**: Tags added: `AI_Scored_Warm`
- **0-39 (Cold)**: Tags added: `AI_Scored_Cold`

**High-Value Trigger:**
- Scores >= 85 automatically trigger `notify_agent_workflow_id`
- Enables immediate agent handoff for ready-to-close leads

### Workflow Automation

#### trigger_ghl_workflow

Trigger GHL automation workflow for a contact.

**Natural Language Examples:**
- "Trigger the qualification sequence workflow for contact abc123"
- "Start the nurture campaign for this lead"

**Programmatic Usage:**

```python
result = await trigger_ghl_workflow(
    contact_id="abc123",
    workflow_id="wf_qualification_sequence",
    custom_values={
        "property_type": "condo",
        "budget": "500k",
        "timeline": "3-6 months"
    }
)
```

#### send_ghl_sms

Send SMS message to contact.

**Natural Language Examples:**
- "Send SMS to abc123 saying 'Your property viewing is confirmed for tomorrow at 2pm'"
- "Text this lead about the open house on Saturday"

**Programmatic Usage:**

```python
result = await send_ghl_sms(
    contact_id="abc123",
    message="Hi John! Your property viewing is confirmed for tomorrow at 2pm. See you there!",
    message_type="transactional"
)
```

**Message Types:**
- `transactional`: Appointment confirmations, updates (no opt-out required)
- `marketing`: Promotional messages (requires prior consent)

### Opportunity Management

#### create_ghl_opportunity

Create opportunity in GHL pipeline.

**Natural Language Examples:**
- "Create opportunity for contact abc123 in sales pipeline, initial contact stage, for Downtown Condo Sale worth 550k"
- "Add this contact to the buyer pipeline at qualification stage"

**Programmatic Usage:**

```python
result = await create_ghl_opportunity(
    contact_id="abc123",
    pipeline_id="pipeline_sales",
    stage_id="stage_initial_contact",
    name="Downtown Condo Sale - John Smith",
    value=550000,
    notes="Referred by existing client. Pre-qualified with lender approval."
)
```

## Integration with Existing Services

### Predictive Lead Scorer

The MCP server integrates with `ghl_real_estate_ai/services/predictive_lead_scorer.py`:

```python
# When updating lead score, automatically syncs with ML predictions
from ghl_real_estate_ai.services.predictive_lead_scorer import PredictiveLeadScorer

scorer = PredictiveLeadScorer()
ml_score = scorer.score_lead(lead_id, lead_context)

# MCP server uses ML factors in update_lead_score
await update_lead_score(
    contact_id=lead_id,
    score=ml_score.score,
    factors={
        "ml_conversion_probability": ml_score.score / 100,
        "ml_tier": ml_score.tier,
        "ml_reasoning": ml_score.reasoning
    }
)
```

### Claude Enhanced Lead Scorer

Integrates with `ghl_real_estate_ai/services/claude_enhanced_lead_scorer.py`:

```python
# Comprehensive AI analysis with strategic insights
from ghl_real_estate_ai.services.claude_enhanced_lead_scorer import ClaudeEnhancedLeadScorer

enhanced_scorer = ClaudeEnhancedLeadScorer()
analysis = await enhanced_scorer.analyze_lead_comprehensive(lead_id, lead_context)

# Push comprehensive analysis to GHL
await update_lead_score(
    contact_id=lead_id,
    score=analysis.final_score,
    factors={
        "jorge_score": analysis.jorge_score,
        "ml_score": analysis.ml_conversion_score,
        "churn_risk": analysis.churn_risk_score,
        "engagement": analysis.engagement_score,
        "strategic_summary": analysis.strategic_summary,
        "next_action": analysis.next_best_action
    },
    notes=analysis.reasoning
)
```

### GHL Sync Service

Coordinates with `ghl_real_estate_ai/services/ghl_sync_service.py`:

```python
# DNA payload synchronization
from ghl_real_estate_ai.services.ghl_sync_service import GHLSyncService

sync_service = GHLSyncService()

# After scoring, sync DNA factors to GHL custom fields
await sync_service.sync_dna_to_ghl(
    contact_id=lead_id,
    dna_payload={
        "factors": {...},  # 25+ qualification factors
        "dimensions": {...}  # 16+ lifestyle dimensions
    }
)
```

## Common Workflows

### 1. New Lead Qualification Flow

```python
# Step 1: Create contact from web form
contact = await create_ghl_contact(
    name="Jane Doe",
    email="jane@example.com",
    phone="+15125559876",
    tags=["New Lead", "Buyer"]
)

# Step 2: Run comprehensive analysis
from ghl_real_estate_ai.services.claude_enhanced_lead_scorer import analyze_lead_with_claude

analysis = await analyze_lead_with_claude(
    contact["id"],
    lead_context={
        "budget": "600k",
        "timeline": "immediate",
        "location": "downtown austin",
        "property_type": "condo"
    }
)

# Step 3: Update GHL with score and intelligence
await update_lead_score(
    contact_id=contact["id"],
    score=analysis.final_score,
    factors={
        "comprehensive_analysis": True,
        "claude_strategic_summary": analysis.strategic_summary,
        "next_best_action": analysis.next_best_action,
        "success_probability": analysis.success_probability
    },
    notes=analysis.reasoning
)

# Step 4: Trigger appropriate workflow
if analysis.final_score >= 70:
    await trigger_ghl_workflow(contact["id"], "wf_hot_lead_handoff")
elif analysis.final_score >= 40:
    await trigger_ghl_workflow(contact["id"], "wf_warm_nurture")
else:
    await trigger_ghl_workflow(contact["id"], "wf_cold_reengagement")
```

### 2. Bulk Lead Scoring Update

```python
# Search for unscored leads
contacts = await search_ghl_contacts(
    tags=["Need to Qualify", "Unscored"],
    limit=50
)

# Score each lead
for contact in contacts:
    try:
        # Get lead context from GHL custom fields
        lead_context = {
            "name": contact["name"],
            "email": contact.get("email"),
            "phone": contact.get("phone"),
            "custom_fields": contact.get("customFields", {})
        }

        # Run AI analysis
        analysis = await analyze_lead_with_claude(contact["id"], lead_context)

        # Update score
        await update_lead_score(
            contact_id=contact["id"],
            score=analysis.final_score,
            factors={"bulk_scored": True, "analysis_version": "v2.0"},
            notes=f"Automated bulk scoring: {analysis.classification}"
        )

    except Exception as e:
        logger.error(f"Failed to score {contact['id']}: {e}")
```

### 3. High-Value Lead Detection

```python
# Monitor for high-value signals
async def monitor_high_value_leads():
    """Continuously monitor and act on high-value lead signals"""

    # Search for recently engaged leads
    engaged = await search_ghl_contacts(
        tags=["Recent Activity", "Engaged"],
        limit=20
    )

    for lead in engaged:
        # Get comprehensive intelligence
        analysis = await analyze_lead_with_claude(lead["id"], lead_context)

        # Check for high-value signals
        if analysis.final_score >= 85 and analysis.success_probability >= 80:
            # Immediate agent notification
            await send_ghl_sms(
                contact_id=settings.default_agent_id,
                message=f"🔥 HIGH VALUE ALERT: {lead['name']} scored {analysis.final_score}/100. {analysis.next_best_action}",
                message_type="transactional"
            )

            # Create high-priority opportunity
            await create_ghl_opportunity(
                contact_id=lead["id"],
                pipeline_id="pipeline_hot_leads",
                stage_id="stage_immediate_followup",
                name=f"Hot Lead: {lead['name']}",
                value=analysis.estimated_value,
                notes=analysis.strategic_summary
            )
```

## Error Handling

### Common Error Patterns

```python
try:
    contact = await create_ghl_contact(name="Test User")
except httpx.HTTPError as e:
    if e.response.status_code == 401:
        logger.error("Invalid API key. Check GHL_API_KEY in .env")
    elif e.response.status_code == 429:
        logger.error("Rate limit exceeded. Wait before retrying.")
    elif e.response.status_code == 404:
        logger.error("Location not found. Check GHL_LOCATION_ID")
    else:
        logger.error(f"GHL API error: {e}")
```

### Validation Errors

```python
# Invalid phone format
await create_ghl_contact(
    name="Test",
    phone="555-1234"  # Invalid - should be E.164 format
)
# Fix: phone="+15125551234"

# Missing required fields
await update_lead_score(
    contact_id="abc123",
    score=75
    # Missing: factors parameter (required)
)
```

## Performance Optimization

### Batch Operations

```python
# Instead of multiple individual calls
for contact_id in contact_ids:
    await get_ghl_contact(contact_id)  # 10 API calls

# Use search with filters (when possible)
contacts = await search_ghl_contacts(
    tags=["Target Group"],
    limit=100
)  # 1 API call
```

### Caching Strategy

The MCP server includes built-in caching (5-minute TTL):

```python
# First call - hits API
contact1 = await get_ghl_contact("abc123")  # API call

# Within 5 minutes - uses cache
contact2 = await get_ghl_contact("abc123")  # Cached

# After 5 minutes - refreshes
contact3 = await get_ghl_contact("abc123")  # API call
```

### Rate Limiting

Configured limits:
- **60 requests per minute** (normal operations)
- **10 request burst** (short spikes allowed)

```python
# Automatic rate limiting with exponential backoff
# No manual throttling needed
```

## Testing

### Test Mode

Enable test mode in `.env`:

```bash
TEST_MODE=true
```

All MCP operations will return mock data:

```python
# With TEST_MODE=true
contact = await create_ghl_contact(name="Test")
# Returns: {"id": "mock_contact_123", "name": "Test", ...}
# No actual GHL API call made
```

### Integration Tests

```bash
# Run MCP server tests
pytest .claude/mcp-servers/ghl/tests/ -v

# Expected output:
# test_create_contact ✓
# test_search_contacts ✓
# test_update_lead_score ✓
# test_trigger_workflow ✓
```

## Security

### API Key Protection

- API keys stored in `.env` (git-ignored)
- Never hardcode keys in scripts
- Use environment variables for all credentials

### Operation Restrictions

Configured in `ghl.json`:

```json
{
  "security": {
    "allowed_operations": ["create", "read", "update"],
    "forbidden_operations": ["delete"]
  }
}
```

Delete operations are disabled for safety.

### Input Validation

All inputs validated against JSON schema:

```python
# Invalid input caught before API call
await create_ghl_contact(
    name=None  # Fails validation
)
# ValidationError: 'name' is required
```

## Monitoring

### Metrics Tracked

- Request count per tool
- Average response time
- Error rates
- API usage quota

### Logging

Logs written to `logs/ghl_mcp_server.log`:

```
2026-01-16 10:30:15 INFO: Created contact: abc123 - John Smith
2026-01-16 10:30:16 INFO: Updated lead score for abc123: 87.5
2026-01-16 10:30:17 INFO: Triggered workflow wf_hot_lead for abc123
```

### Alerts

Configure alerts in `ghl.json`:

```json
{
  "monitoring": {
    "alert_on_errors": true,
    "error_threshold": 5,
    "alert_webhook": "https://hooks.slack.com/..."
  }
}
```

## Troubleshooting

### Server won't start

**Issue**: `ModuleNotFoundError: No module named 'anthropic_mcp'`

**Solution**:
```bash
pip install anthropic-mcp httpx pydantic pydantic-settings
```

### Authentication errors

**Issue**: `401 Unauthorized`

**Solution**:
- Verify `GHL_API_KEY` in `.env`
- Check key permissions in GHL dashboard
- Ensure API key has required scopes

### Rate limiting

**Issue**: `429 Too Many Requests`

**Solution**:
- Wait 60 seconds before retrying
- Reduce concurrent operations
- Implement exponential backoff

### Contact not found

**Issue**: `404 Not Found`

**Solution**:
- Verify `contact_id` is correct
- Check `GHL_LOCATION_ID` matches contact's location
- Ensure contact hasn't been deleted

## Support

### Documentation
- GoHighLevel API Docs: https://highlevel.stoplight.io/
- MCP Protocol Spec: https://modelcontextprotocol.io/
- EnterpriseHub Services: `/ghl_real_estate_ai/services/`

### Common Issues
- See `TROUBLESHOOTING.md` for detailed solutions
- Check existing service implementations for patterns
- Review integration tests for usage examples

---

**Version**: 1.0.0
**Last Updated**: January 16, 2026
**Author**: EnterpriseHub Team
**License**: Proprietary
