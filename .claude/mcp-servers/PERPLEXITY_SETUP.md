# Perplexity MCP Server - Setup Complete ✅

## What Was Created

```
.claude/mcp-servers/perplexity/
├── server.py              # MCP server with 4 tools
├── requirements.txt       # httpx, mcp dependencies  ✅ INSTALLED
├── test_installation.py   # Validation script
├── __init__.py           # Package marker
└── README.md             # Full documentation
```

## Configuration Updates

### 1. Research Profile (`.claude/mcp-profiles/research.json`)
- ✅ Added Perplexity MCP server
- ✅ Configured with venv Python path
- ✅ Token overhead: ~2000 tokens

## 🚨 REQUIRED: Security Setup

**You MUST complete these steps before using Perplexity:**

1. **Revoke exposed API key** at https://www.perplexity.ai/settings/api
   - The key you shared in chat is now PUBLIC and MUST be revoked

2. **Generate NEW API key**

3. **Add to .env file**:
   ```bash
   # Open .env file and add (or update):
   PERPLEXITY_API_KEY=pplx-your-new-key-here
   ```

4. **Verify installation**:
   ```bash
   source .venv/bin/activate
   python .claude/mcp-servers/perplexity/test_installation.py
   ```

## Available Tools

Once configured, you'll have access to:

### 1. `perplexity_search`
Real-time web search with citations
```
Search Perplexity for Python 3.13 features
```

### 2. `perplexity_research`
Deep research with structured output
```
Research: Real estate AI automation, focusing on lead scoring
```

### 3. `perplexity_news`
Latest news and updates
```
Get latest news about Claude AI from the past week
```

### 4. `perplexity_compare`
Compare technologies/approaches
```
Compare Redis vs Memcached vs In-memory caching for real-time apps
```

## How to Use

### Method 1: Switch to Research Profile
```bash
# In Claude Code CLI
/profile research
```

Then ask questions like:
- "Search Perplexity for latest Streamlit features"
- "Research Python async best practices"
- "Get latest news about GoHighLevel API changes"

### Method 2: Direct Tool Calls
When in research profile, I can call Perplexity tools automatically based on your questions about current information.

## When to Use Perplexity

**Use Perplexity when you need:**
- ✅ Current information (last day/week/month)
- ✅ Real-time technology updates
- ✅ Latest API changes and features
- ✅ Comparative analysis of tools
- ✅ Industry news and trends

**Use Context7 when you need:**
- 📚 Official stable documentation
- 📚 Framework reference guides
- 📚 API specifications

**Use Serena when you need:**
- 🔍 Local codebase search
- 🔍 Symbol definitions
- 🔍 Code references

## Cost

- **Perplexity Pro**: ~$20/month (unlimited searches)
- No per-token costs
- Each search = 1 request (regardless of length)

## Troubleshooting

### "PERPLEXITY_API_KEY not found"
```bash
# Check .env file
cat .env | grep PERPLEXITY_API_KEY

# Verify it's loaded
source .env
echo $PERPLEXITY_API_KEY
```

### Dependencies Missing
```bash
source .venv/bin/activate
pip install -r .claude/mcp-servers/perplexity/requirements.txt
```

### Server Not Loading
1. Restart Claude Code
2. Check MCP profile is active: `/profile research`
3. Check logs for MCP server errors

## Next Steps

1. ⚠️ **REVOKE OLD API KEY** (exposed in chat)
2. ⚠️ **GENERATE NEW KEY**
3. ⚠️ **ADD TO .env FILE**
4. ✅ Run test script to verify
5. 🚀 Restart Claude Code
6. 🔬 Switch to research profile
7. 🎯 Start using Perplexity search!

## Documentation

- **Full README**: `.claude/mcp-servers/perplexity/README.md`
- **Configuration**: `.claude/mcp-servers/perplexity.json`
- **Research Profile**: `.claude/mcp-profiles/research.json`

---

**Created**: 2026-01-16
**Status**: Installation Complete - Awaiting API Key Configuration
**Next Action**: Add PERPLEXITY_API_KEY to .env file
