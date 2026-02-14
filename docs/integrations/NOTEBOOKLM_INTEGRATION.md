# NotebookLM Integration for EnterpriseHub

**Status**: ✅ Available
**Version**: 1.0
**Last Updated**: February 13, 2026

## Overview

NotebookLM is integrated as an MCP server to provide Claude Code with advanced research and knowledge base capabilities. This enables intelligent organization, querying, and synthesis of information relevant to EnterpriseHub development and real estate operations.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Claude Code                            │
│  (Main AI Agent - Planning, Development, Research)          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ MCP Protocol (stdio)
                         │
┌────────────────────────▼────────────────────────────────────┐
│              NotebookLM MCP Server                          │
│  (.claude/mcp-servers/notebooklm/server.py)                 │
│                                                             │
│  Tools:                                                     │
│  • notebooklm_create_notebook                              │
│  • notebooklm_add_source                                   │
│  • notebooklm_query                                        │
│  • notebooklm_list_notebooks                               │
│  • notebooklm_generate_study_guide                         │
│  • notebooklm_generate_audio_overview                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ notebooklm-py (unofficial API)
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Google NotebookLM                              │
│  (Research Tool & Knowledge Base)                           │
│                                                             │
│  • Multi-source intelligence                               │
│  • AI-powered querying with citations                      │
│  • Content generation (study guides, audio)                │
│  • Knowledge synthesis                                     │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### 1. Install Dependencies

```bash
# Navigate to MCP server directory
cd .claude/mcp-servers/notebooklm

# Run installation script
./install.sh

# Or install manually
pip install -r requirements.txt
```

### 2. Configure Authentication

**Method 1: gcloud CLI (Recommended for development)**

```bash
# Install gcloud CLI if not already installed
# Visit: https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth application-default login
```

**Method 2: Service Account (Recommended for production)**

```bash
# 1. Create service account in Google Cloud Console
# 2. Download credentials JSON
# 3. Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

# Add to .env file
echo 'GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"' >> .env
```

### 3. Verify Installation

```bash
# Test MCP server
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
  python3 .claude/mcp-servers/notebooklm/server.py
```

### 4. Restart Claude Code

After installation, restart Claude Code to load the new MCP server.

## Usage in Claude Code

### Create Research Notebook

```
User: Create a NotebookLM notebook for Rancho Cucamonga market research

Claude Code will:
1. Call notebooklm_create_notebook with appropriate title
2. Return notebook ID for future operations
```

### Add Sources

```
User: Add these market reports to the notebook:
- https://www.realtor.com/research/rancho-cucamonga-ca/
- https://www.zillow.com/rancho-cucamonga-ca/home-values/

Claude Code will:
1. Call notebooklm_add_source for each URL
2. Confirm sources are added
```

### Query for Insights

```
User: What are the current pricing trends in Rancho Cucamonga?

Claude Code will:
1. Call notebooklm_query with the question
2. Return answer with citations from sources
```

### Generate Study Materials

```
User: Generate a study guide about our Jorge bot architecture

Claude Code will:
1. Create or find relevant notebook
2. Add architecture documentation as sources
3. Call notebooklm_generate_study_guide
4. Return formatted study guide
```

## Programmatic Access

The NotebookLM service can also be used directly in EnterpriseHub code:

```python
from ghl_real_estate_ai.services.notebooklm_service import NotebookLMService

# Initialize service
service = NotebookLMService()

# Create market research notebook
notebook = await service.create_market_research_notebook(
    market_name="Rancho Cucamonga",
    include_sources=[
        "https://www.zillow.com/rancho-cucamonga-ca/",
        "https://www.realtor.com/realestateandhomes-search/Rancho-Cucamonga_CA"
    ]
)

# Query for insights
insights = await service.generate_market_insights(
    notebook_id=notebook["notebook_id"],
    focus_areas=["pricing trends", "inventory levels", "buyer demand"]
)

# Add conversation transcript
await service.add_conversation_transcript(
    notebook_id=notebook["notebook_id"],
    transcript="[Conversation text here]",
    metadata={
        "date": "2026-02-13",
        "participants": "Jorge Lead Bot, John Smith",
        "contact_id": "ghl_contact_123"
    }
)

# Analyze client preferences
preferences = await service.analyze_client_preferences(
    notebook_id=client_notebook_id,
    analysis_type="comprehensive"
)

# Generate audio briefing
audio = await service.generate_audio_briefing(
    notebook_id=notebook["notebook_id"],
    duration_minutes=10
)
```

## Use Cases

### 1. Market Intelligence

**Scenario**: Track Rancho Cucamonga real estate market trends

**Workflow**:
1. Create "Rancho Cucamonga Market Intelligence" notebook
2. Add sources:
   - Zillow market reports
   - Realtor.com statistics
   - Local news articles
   - MLS data snapshots
3. Query weekly for trend analysis
4. Generate audio briefings for agents

**Benefits**:
- Centralized market intelligence
- AI-synthesized insights from multiple sources
- Citation tracking for verification

### 2. Property Research

**Scenario**: Deep dive on a specific listing

**Workflow**:
1. Create notebook for property address
2. Add sources:
   - MLS listing data
   - Comparable sales analysis
   - Neighborhood demographics
   - School district information
3. Query for pricing strategy insights
4. Generate property intelligence report

**Benefits**:
- Comprehensive property context
- Competitive positioning insights
- Data-driven pricing recommendations

### 3. Client Insights

**Scenario**: Understand buyer preferences from conversations

**Workflow**:
1. Create "Client: John Smith (Buyer)" notebook
2. Add conversation transcripts as sources
3. Query for:
   - Property preferences
   - Budget considerations
   - Timeline urgency
   - Decision patterns
4. Generate preference profile

**Benefits**:
- Pattern recognition across conversations
- Preference extraction
- Behavioral insights

### 4. Training & Documentation

**Scenario**: Create onboarding materials for new agents

**Workflow**:
1. Create "Agent Onboarding" notebook
2. Add sources:
   - Best practice documentation
   - Successful conversation examples
   - Process guides
3. Generate study guide
4. Create audio training overview

**Benefits**:
- Structured learning materials
- Multiple format options
- Auto-generated from best practices

## Configuration

### Environment Variables

Add to `.env`:

```bash
# Google Cloud authentication
GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

# Optional: NotebookLM service configuration
NOTEBOOKLM_DEFAULT_NOTEBOOK_ID="your-default-notebook-id"
NOTEBOOKLM_CACHE_TTL=3600
```

### MCP Server Config

Located in `.mcp.json`:

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "python3",
      "args": [".claude/mcp-servers/notebooklm/server.py"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "${GOOGLE_APPLICATION_CREDENTIALS}"
      }
    }
  }
}
```

## Limitations

1. **Unofficial API**: Uses `notebooklm-py` which relies on undocumented APIs that may change
2. **Authentication**: Requires Google Cloud authentication
3. **Rate Limits**: Subject to NotebookLM usage quotas
4. **Audio Generation**: May have separate rate limits
5. **Source Types**: Limited to URLs, text, and certain document formats

## Security Considerations

1. **Credentials**: Never commit `GOOGLE_APPLICATION_CREDENTIALS` file to git
2. **PII**: Be cautious adding client PII to notebooks
3. **Access Control**: Use service accounts with minimal permissions
4. **Data Location**: Understand where NotebookLM stores data
5. **Audit Trail**: Citations provide source tracking

## Troubleshooting

### Tools Not Available

**Problem**: NotebookLM tools don't appear in Claude Code

**Solutions**:
1. Restart Claude Code
2. Check `.mcp.json` syntax
3. Verify Python dependencies installed
4. Check server.py file permissions

### Authentication Errors

**Problem**: "Authentication failed" or "Credentials not found"

**Solutions**:
```bash
# Re-authenticate with gcloud
gcloud auth application-default login

# Verify credentials
gcloud auth application-default print-access-token

# Check environment variable
echo $GOOGLE_APPLICATION_CREDENTIALS

# Test credentials
python3 -c "from notebooklm import NotebookLM; NotebookLM()"
```

### Import Errors

**Problem**: "ModuleNotFoundError: No module named 'notebooklm'"

**Solutions**:
```bash
# Install package
pip install notebooklm-py

# Verify installation
python3 -c "import notebooklm; print(notebooklm.__version__)"
```

### Server Crashes

**Problem**: MCP server exits immediately

**Solutions**:
1. Check Python version (3.9+ required)
2. Verify all dependencies installed
3. Check server.py for syntax errors
4. Review logs for error messages

## Monitoring

### Health Checks

The MCP server implements basic health monitoring:

```python
# Check if service is available
from ghl_real_estate_ai.services.notebooklm_service import NotebookLMService

service = NotebookLMService()
if service.is_available():
    print("✓ NotebookLM service is ready")
else:
    print("✗ NotebookLM service unavailable")
```

### Usage Metrics

Track NotebookLM usage:
- Notebooks created
- Sources added
- Queries executed
- Study guides generated
- Audio overviews created

## Future Enhancements

1. **Official API Support**: Migrate to official NotebookLM Enterprise API when available
2. **Caching**: Implement intelligent query result caching
3. **Batch Operations**: Support bulk source uploads
4. **Webhooks**: Real-time updates when sources are processed
5. **Advanced Querying**: Support for complex multi-notebook queries
6. **Export Options**: Additional export formats and integrations

## References

- [NotebookLM Official Site](https://notebooklm.google.com)
- [notebooklm-py GitHub](https://github.com/teng-lin/notebooklm-py)
- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [Google Cloud Authentication](https://cloud.google.com/docs/authentication)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review MCP server logs
3. Check notebooklm-py GitHub issues
4. Contact EnterpriseHub development team

---

**Maintained by**: EnterpriseHub Development Team
**Integration Type**: MCP Server (stdio)
**Dependencies**: notebooklm-py, google-auth
**Authentication**: Google Cloud OAuth
