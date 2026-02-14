# NotebookLM MCP Server - Quick Start Guide

Get NotebookLM integrated with Claude Code in 5 minutes.

## Step 1: Install Dependencies (2 minutes)

```bash
# Navigate to project root
cd /Users/cave/Documents/GitHub/EnterpriseHub

# Run installation script
./.claude/mcp-servers/notebooklm/install.sh
```

This will:
- Install `notebooklm-py` package
- Set up Google authentication
- Test the MCP server

## Step 2: Authenticate with Google (1 minute)

**Option A: gcloud CLI (easiest)**

```bash
# If you have gcloud installed
gcloud auth application-default login
```

**Option B: Service Account**

```bash
# Download service account key from Google Cloud Console
# Then set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

# Add to .env for persistence
echo 'GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"' >> .env
```

## Step 3: Restart Claude Code (1 minute)

Close and reopen Claude Code to load the new MCP server.

## Step 4: Test It Out! (1 minute)

Try these commands in Claude Code:

### Example 1: Create Your First Notebook

```
Create a NotebookLM notebook called "EnterpriseHub Research"
```

Claude Code will use the `notebooklm_create_notebook` tool and return a notebook ID.

### Example 2: Add a Source

```
Add this URL to the notebook: https://github.com/anthropics/claude-code
```

Claude Code will add the URL as a research source.

### Example 3: Query It

```
What features does Claude Code provide?
```

Claude Code will query the notebook and return an answer with citations.

## Common Use Cases

### Market Research

```
Create a NotebookLM notebook for Rancho Cucamonga real estate market research.
Add these sources:
- https://www.zillow.com/rancho-cucamonga-ca/
- https://www.realtor.com/realestateandhomes-search/Rancho-Cucamonga_CA

Then query: What are the current market trends?
```

### Documentation Knowledge Base

```
Create a NotebookLM notebook for EnterpriseHub architecture.
Add our CLAUDE.md file as a source.
Then ask: How does the Jorge bot handoff system work?
```

### Generate Study Materials

```
Create a study guide about our API design patterns in markdown format.
```

## Verification Checklist

- [ ] Python dependencies installed (`pip list | grep notebooklm`)
- [ ] Google authentication configured (gcloud or service account)
- [ ] `.mcp.json` contains notebooklm server config
- [ ] Claude Code restarted
- [ ] Can create notebook successfully
- [ ] Can add source successfully
- [ ] Can query notebook successfully

## Troubleshooting

### "Authentication failed"

```bash
# Re-authenticate
gcloud auth application-default login

# Test credentials
python3 -c "from notebooklm import NotebookLM; NotebookLM()"
```

### "Module not found: notebooklm"

```bash
pip install notebooklm-py
```

### "Tools not appearing"

1. Check `.mcp.json` syntax
2. Restart Claude Code
3. Run: `echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 .claude/mcp-servers/notebooklm/server.py`

## Next Steps

- Read the full documentation: `docs/integrations/NOTEBOOKLM_INTEGRATION.md`
- Explore skill guide: `.claude/skills/notebooklm-research/SKILL.md`
- Try programmatic access: `ghl_real_estate_ai/services/notebooklm_service.py`

## Get Help

If you encounter issues:
1. Check the troubleshooting section above
2. Review MCP server README: `.claude/mcp-servers/notebooklm/README.md`
3. Check server logs for errors

---

**Ready to research smarter!** 🚀
