# NotebookLM MCP Server for Claude Code

MCP server integration that enables Claude Code to use Google NotebookLM as a research tool and knowledge base.

## Features

- **Research Notebooks**: Create and manage research notebooks
- **Source Management**: Add URLs, documents, and text sources
- **Intelligent Querying**: Ask questions and get cited answers
- **Content Generation**: Generate study guides, audio overviews, and insights
- **Knowledge Organization**: Structured information retrieval from multiple sources

## Installation

```bash
# Install the unofficial Python API
pip install notebooklm-py

# Authenticate with Google
# Option 1: Using gcloud CLI
gcloud auth application-default login

# Option 2: Set up service account (for production)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

## Claude Code Integration

The MCP server is configured in `.mcp.json` to make NotebookLM tools available to Claude Code.

### Available Tools

1. **notebooklm_create_notebook**
   - Create a new research notebook
   - Parameters: `title` (required), `description` (optional)

2. **notebooklm_add_source**
   - Add sources (URL, text, document) to notebooks
   - Parameters: `notebook_id`, `source_type`, `content`, `title`

3. **notebooklm_query**
   - Query notebooks to find information
   - Parameters: `notebook_id`, `query`, `include_citations`

4. **notebooklm_list_notebooks**
   - List all available notebooks
   - Parameters: `limit` (default: 50)

5. **notebooklm_generate_study_guide**
   - Generate study guides from sources
   - Parameters: `notebook_id`, `format` (markdown/quiz/flashcards/outline)

6. **notebooklm_generate_audio_overview**
   - Generate AI podcast/audio overview
   - Parameters: `notebook_id`, `duration_minutes`

## Usage Examples

### Example 1: Research a Topic

```
User: Research the Rancho Cucamonga real estate market

Claude Code will:
1. Create a notebook titled "Rancho Cucamonga Market Research"
2. Add relevant sources (market reports, statistics, news)
3. Query the notebook for insights
4. Generate a comprehensive report
```

### Example 2: Organize Codebase Knowledge

```
User: Create a NotebookLM notebook about our Jorge bot architecture

Claude Code will:
1. Create notebook "Jorge Bot Architecture"
2. Add source documents (CLAUDE.md, architecture files)
3. Enable querying about bot implementation details
```

### Example 3: Generate Training Materials

```
User: Generate a study guide about our API design patterns

Claude Code will:
1. Find or create relevant notebook
2. Add API documentation sources
3. Generate structured study guide
```

## Configuration

The MCP server uses stdio transport and communicates via JSON-RPC 2.0.

**Prerequisites**:
- Python 3.9+
- `notebooklm-py` package installed
- Google authentication configured

**Security**:
- Uses Google OAuth for authentication
- No API keys stored in config
- Credentials managed via gcloud or service account

## Troubleshooting

### "NotebookLM client unavailable"
```bash
pip install notebooklm-py
```

### "Authentication failed"
```bash
# Re-authenticate
gcloud auth application-default login

# Verify credentials
gcloud auth application-default print-access-token
```

### "Package not found"
The `notebooklm-py` package uses unofficial APIs. Ensure you have the latest version:
```bash
pip install --upgrade notebooklm-py
```

## Use Cases for EnterpriseHub

- **Market Research**: Organize Rancho Cucamonga market data and trends
- **Property Intelligence**: Compile insights on specific properties
- **Client Preferences**: Track buyer/seller interaction patterns
- **Competitive Analysis**: Monitor competitor strategies and positioning
- **Training Materials**: Generate agent training content from best practices

## Limitations

- Uses unofficial Google NotebookLM APIs (may change)
- Requires Google authentication
- Subject to NotebookLM usage limits
- Audio generation may have quota limits

## References

- [notebooklm-py GitHub](https://github.com/teng-lin/notebooklm-py)
- [NotebookLM Documentation](https://notebooklm.google.com)
- [MCP Protocol Specification](https://modelcontextprotocol.io)
