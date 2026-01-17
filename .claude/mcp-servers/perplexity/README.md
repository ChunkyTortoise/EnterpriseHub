# Perplexity MCP Server

Real-time web search and research using Perplexity AI Pro.

## Features

- **Real-time Web Search**: Access current information with citations
- **Deep Research**: Comprehensive topic analysis with structured output
- **News Lookup**: Latest updates filtered by timeframe
- **Comparative Analysis**: Compare technologies, approaches, and solutions

## Installation

1. **Set up API Key**:
   ```bash
   # Add to .env (already configured in .env.example)
   PERPLEXITY_API_KEY=your-key-here
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r .claude/mcp-servers/perplexity/requirements.txt
   ```

3. **Verify Installation**:
   ```bash
   python .claude/mcp-servers/perplexity/test_installation.py
   ```

## Tools

### 1. `perplexity_search`
Real-time web search with citations.

**Use Cases**:
- Current technical documentation
- Latest API changes
- Real-time market research

**Example**:
```json
{
  "query": "What are the latest features in Python 3.13?",
  "search_recency_filter": "month"
}
```

### 2. `perplexity_research`
Deep research with structured output.

**Use Cases**:
- Comprehensive topic analysis
- Technology deep-dives
- Best practices research

**Example**:
```json
{
  "topic": "Real estate AI automation",
  "focus": "lead scoring and qualification",
  "depth": "comprehensive"
}
```

### 3. `perplexity_news`
Latest news and updates.

**Use Cases**:
- Technology announcements
- Framework updates
- Industry trends

**Example**:
```json
{
  "topic": "Claude AI announcements",
  "timeframe": "week"
}
```

### 4. `perplexity_compare`
Compare approaches/technologies.

**Use Cases**:
- Technology selection
- Architecture decisions
- Tool evaluation

**Example**:
```json
{
  "topic": "Real-time caching strategies",
  "approaches": ["Redis", "Memcached", "In-memory caching"]
}
```

## Available Models

- `llama-3.1-sonar-large-128k-online` (default) - Best balance of speed and quality
- `llama-3.1-sonar-small-128k-online` - Faster, lighter queries
- `llama-3.1-sonar-huge-128k-online` - Maximum quality for complex research

## Integration

### Works Best With

- **Context7**: Official documentation (Perplexity for real-time, Context7 for stable docs)
- **Serena**: Codebase search (Perplexity for web, Serena for local)
- **Greptile**: Code intelligence (Perplexity for concepts, Greptile for implementation)

### Optimal MCP Profiles

- **research**: Documentation and real-time research
- **backend-services**: Technology decisions and API research

## Security

- API key stored in `.env` (never committed)
- `.env` is in `.gitignore` and blocked by permissions
- Use `.env.example` as template

## Troubleshooting

### API Key Not Found
```bash
# Verify environment variable
echo $PERPLEXITY_API_KEY

# Or check .env file exists and has key
cat .env | grep PERPLEXITY_API_KEY
```

### Rate Limiting
Perplexity Pro has generous limits, but if you hit them:
- Add delays between requests
- Use `search_recency_filter` to narrow results
- Consider using `sonar-small` model for simple queries

## Cost Management

- **Perplexity Pro**: ~$20/month unlimited searches
- Each search counts as 1 request (no per-token billing)
- Use appropriate depth: `quick` < `balanced` < `comprehensive`

## Development

### Testing
```bash
# Run test suite
python .claude/mcp-servers/perplexity/test_installation.py

# Test specific tool
python -c "
import asyncio
from server import PerplexityMCPServer

async def test():
    server = PerplexityMCPServer()
    result = await server.search('Python 3.13 features')
    print(result)

asyncio.run(test())
"
```

### Debugging
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Version

- **Version**: 1.0.0
- **MCP Protocol**: 0.9.0
- **Python**: 3.11+
