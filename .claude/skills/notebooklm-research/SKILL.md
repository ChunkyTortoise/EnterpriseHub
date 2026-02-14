# NotebookLM Research Skill

**Purpose**: Use Google NotebookLM as an intelligent research tool and knowledge base for the EnterpriseHub project.

**When to use**:
- Researching market trends and real estate data
- Organizing project documentation and architecture knowledge
- Compiling client insights and preferences
- Creating study guides and training materials
- Generating audio briefings from research

## Prerequisites

```bash
# Install NotebookLM Python package
pip install notebooklm-py

# Authenticate with Google
gcloud auth application-default login

# Or set service account credentials
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

## MCP Tools Available

The NotebookLM MCP server provides these tools:

1. **notebooklm_create_notebook** - Create research notebooks
2. **notebooklm_add_source** - Add URLs, text, or documents as sources
3. **notebooklm_query** - Ask questions and get cited answers
4. **notebooklm_list_notebooks** - View all notebooks
5. **notebooklm_generate_study_guide** - Generate structured learning materials
6. **notebooklm_generate_audio_overview** - Create AI podcast summaries

## Example Workflows

### Research Market Trends

```
User: "Research recent Rancho Cucamonga real estate trends using NotebookLM"

Claude Code will:
1. Create notebook: "Rancho Cucamonga Market Trends 2026"
2. Add sources from relevant market reports
3. Query for key insights
4. Summarize findings with citations
```

### Document Project Architecture

```
User: "Create a NotebookLM knowledge base of our Jorge bot architecture"

Claude Code will:
1. Create notebook: "Jorge Bot Architecture Knowledge Base"
2. Add CLAUDE.md and related docs as sources
3. Enable intelligent querying about implementation
```

### Generate Training Content

```
User: "Generate a study guide about our API design patterns"

Claude Code will:
1. Find existing architecture notebook or create new one
2. Add relevant API documentation
3. Generate structured study guide with examples
```

## Integration with EnterpriseHub

The NotebookLM service can be used programmatically via:

```python
from ghl_real_estate_ai.services.notebooklm_service import NotebookLMService

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
```

## Use Cases

### Market Intelligence
- **Organize**: Market reports, pricing data, inventory statistics
- **Query**: "What are the current pricing trends?"
- **Generate**: Audio briefings for agents

### Property Research
- **Organize**: Listing data, comparable sales, neighborhood info
- **Query**: "What are the key selling points?"
- **Generate**: Property intelligence reports

### Client Insights
- **Organize**: Conversation transcripts, preference notes, behavior patterns
- **Query**: "What are the client's top 3 priorities?"
- **Generate**: Client preference profiles

### Training & Onboarding
- **Organize**: Best practices, procedures, case studies
- **Query**: "How do we handle buyer objections?"
- **Generate**: Study guides and quizzes

## Configuration

Set up environment variables in `.env`:

```bash
# Google Cloud authentication (choose one method)
# Method 1: Application Default Credentials (gcloud CLI)
# Run: gcloud auth application-default login

# Method 2: Service Account
GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

## Limitations

- Uses unofficial NotebookLM API (may change without notice)
- Requires Google authentication
- Subject to NotebookLM usage quotas
- Audio generation has rate limits

## Troubleshooting

**Problem**: Tools not appearing in Claude Code

**Solution**:
```bash
# Restart Claude Code after editing .mcp.json
# Or manually reload MCP servers
```

**Problem**: Authentication errors

**Solution**:
```bash
# Re-authenticate
gcloud auth application-default login

# Verify credentials work
python -c "from notebooklm import NotebookLM; NotebookLM()"
```

**Problem**: "notebooklm-py not installed"

**Solution**:
```bash
pip install notebooklm-py
```

## Best Practices

1. **Organize by topic**: Create separate notebooks for markets, properties, clients
2. **Add sources gradually**: Don't overwhelm notebooks with too many sources at once
3. **Use citations**: Always request citations for audit trails
4. **Cache insights**: Store generated insights in project documentation
5. **Audio briefings**: Great for daily market updates and client prep

## References

- [NotebookLM Official](https://notebooklm.google.com)
- [notebooklm-py GitHub](https://github.com/teng-lin/notebooklm-py)
- [MCP Server Implementation](.claude/mcp-servers/notebooklm/server.py)
- [Service Integration](../../ghl_real_estate_ai/services/notebooklm_service.py)
