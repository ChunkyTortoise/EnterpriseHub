# GHL MCP Server Installation Guide

Quick installation guide for the GoHighLevel MCP server.

## Prerequisites

- Python 3.11+
- EnterpriseHub project environment
- GoHighLevel API credentials

## Installation Steps

### 1. Install Dependencies

All required dependencies are already in `requirements.txt`:

```bash
cd /Users/cave/Documents/GitHub/EnterpriseHub
pip install -r requirements.txt
```

**Required packages** (already included):
- `httpx>=0.26.0` - HTTP client
- `pydantic>=2.5.0` - Data validation
- `pydantic-settings>=2.1.0` - Settings management
- `anthropic==0.18.1` - Claude API

**Optional MCP packages** (install if needed):
```bash
pip install anthropic-mcp>=0.1.0
```

### 2. Configure Environment Variables

Add to `.env` file in project root:

```bash
# GoHighLevel Configuration
GHL_API_KEY=your_api_key_here
GHL_LOCATION_ID=your_location_id_here
GHL_AGENCY_API_KEY=your_agency_key_here  # Optional
GHL_AGENCY_ID=your_agency_id_here        # Optional

# Claude Configuration (should already exist)
ANTHROPIC_API_KEY=your_anthropic_key_here

# Optional: Custom Field IDs
CUSTOM_FIELD_LEAD_SCORE=lead_score
CUSTOM_FIELD_BUDGET=budget
CUSTOM_FIELD_TIMELINE=timeline
CUSTOM_FIELD_LOCATION=preferred_location

# Optional: Workflow IDs
NOTIFY_AGENT_WORKFLOW_ID=wf_high_value_alert
```

### 3. Enable in MCP Profile

The GHL server is already configured in `.claude/mcp-profiles/backend-services.json`:

```json
{
  "mcpServers": {
    "ghl": {
      "enabled": true,
      "config": {
        "command": "python3",
        "args": ["/Users/cave/Documents/GitHub/EnterpriseHub/.claude/mcp-servers/ghl/server.py"]
      }
    }
  }
}
```

To activate:

```bash
export CLAUDE_PROFILE=backend-services
```

### 4. Verify Installation

Run the test script:

```bash
cd /Users/cave/Documents/GitHub/EnterpriseHub
python3 .claude/mcp-servers/ghl/test_installation.py
```

**Expected output:**

```
==================================================
GHL MCP SERVER INSTALLATION TEST
==================================================

Checking dependencies...
✓ httpx installed
✓ pydantic installed
✓ pydantic-settings installed
✓ All dependencies installed

Checking environment variables...
✓ ANTHROPIC_API_KEY = sk-ant-a...
✓ GHL_API_KEY = eyJhbGc...
✓ GHL_LOCATION_ID = loc_xyz...
✓ All environment variables configured

Checking GHL API access...
✓ GHL API accessible
✓ Location ID: loc_xyz789

Testing MCP server tools...
  Testing search_ghl_contacts...
  ✓ search_ghl_contacts returned 5 results
  Testing create_ghl_contact...
  ✓ create_ghl_contact returned ID: mock_contact_123
  Testing update_lead_score...
  ✓ update_lead_score completed: success
✓ All MCP tools functioning correctly

==================================================
INSTALLATION TEST SUMMARY
==================================================
✓ PASS: Dependencies
✓ PASS: Environment
✓ PASS: GHL API
✓ PASS: MCP Tools
==================================================
✓ GHL MCP Server installation complete!

Next steps:
1. Start using natural language GHL operations
2. Try: 'Create contact named John Smith with email john@example.com'
3. Try: 'Update lead score for contact abc123 to 85'
4. See README.md for full documentation
==================================================
```

### 5. Test Natural Language Operations

Try these commands in Claude:

```
User: "Create a contact named Test User with email test@example.com and tag them as Hot Lead"

Claude: [Uses create_ghl_contact MCP tool]
✓ Created contact: test_contact_123
```

```
User: "Find all contacts tagged as Hot Lead"

Claude: [Uses search_ghl_contacts MCP tool]
Found 15 contacts:
- John Smith (ID: abc123)
- Jane Doe (ID: def456)
...
```

```
User: "Update lead score for contact abc123 to 87 based on high engagement and qualified budget"

Claude: [Uses update_lead_score MCP tool]
✓ Updated lead score: 87/100
✓ Tags added: Hot Lead, AI_Scored_Hot
✓ Triggered high-value workflow
```

## Troubleshooting

### Issue: ModuleNotFoundError: No module named 'httpx'

**Solution:**
```bash
pip install httpx pydantic pydantic-settings
```

### Issue: 401 Unauthorized

**Solution:**
- Check `GHL_API_KEY` in `.env`
- Verify API key has required permissions in GHL dashboard
- Ensure key is for correct location

### Issue: 404 Not Found (Location)

**Solution:**
- Verify `GHL_LOCATION_ID` in `.env`
- Check you're using location ID (not agency ID)
- Confirm location exists in GHL account

### Issue: MCP server won't start

**Solution:**
1. Check Python version: `python3 --version` (should be 3.11+)
2. Verify file path in `backend-services.json` is correct
3. Check file permissions: `chmod +x .claude/mcp-servers/ghl/server.py`
4. Test server directly: `python3 .claude/mcp-servers/ghl/server.py`

### Issue: Test mode enabled unintentionally

**Solution:**
Remove or set to false in `.env`:
```bash
TEST_MODE=false
```

## Directory Structure

```
.claude/
├── mcp-servers/
│   ├── ghl/
│   │   ├── server.py              # Main MCP server
│   │   ├── test_installation.py   # Installation test
│   │   ├── README.md              # Full documentation
│   │   ├── USAGE_EXAMPLES.md      # Integration examples
│   │   └── INSTALLATION.md        # This file
│   └── ghl.json                   # MCP server config
└── mcp-profiles/
    └── backend-services.json      # Profile with GHL enabled
```

## Integration Files

The MCP server integrates with these existing services:

```
ghl_real_estate_ai/
├── services/
│   ├── ghl_client.py                      # Base GHL API client
│   ├── ghl_sync_service.py                # DNA payload sync
│   ├── predictive_lead_scorer.py          # ML scoring
│   └── claude_enhanced_lead_scorer.py     # AI analysis
├── ghl_utils/
│   ├── config.py                          # Settings
│   └── logger.py                          # Logging
└── api/
    └── schemas/
        └── ghl.py                          # GHL schemas
```

## Next Steps

1. **Read Documentation**: See `README.md` for full API reference
2. **Review Examples**: Check `USAGE_EXAMPLES.md` for integration patterns
3. **Run Tests**: Execute integration tests to verify service connections
4. **Start Using**: Begin with simple contact operations, then explore advanced features

## Performance Benchmarks

Expected performance (with test API):

- **Contact Creation**: ~200ms
- **Contact Search**: ~150ms
- **Lead Score Update**: ~250ms (with workflow trigger)
- **Workflow Trigger**: ~180ms
- **SMS Send**: ~220ms

With GHL API rate limits:
- **60 requests/minute** (normal operations)
- **10 request burst** (short spikes)

## Support Resources

- **Full Documentation**: `README.md`
- **Usage Examples**: `USAGE_EXAMPLES.md`
- **GHL API Docs**: https://highlevel.stoplight.io/
- **MCP Protocol**: https://modelcontextprotocol.io/
- **Integration Services**: See `ghl_real_estate_ai/services/`

---

**Version**: 1.0.0
**Last Updated**: January 16, 2026
**Installation Time**: ~5 minutes
**Difficulty**: Easy (automated setup)
