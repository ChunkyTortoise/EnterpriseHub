# 🚀 Continue MCP Setup - Quick Reference

## 📋 EXACT Continuation Prompt

```
I'm continuing MCP setup for EnterpriseHub real estate AI. Jorge's GoHighLevel credentials are configured in .mcp.json but PostgreSQL needs installation and I'm missing GitHub/Firecrawl API keys.

Current status:
- ✅ GHL configured (Location: 3xt4qayAh35BIDLaUv7P)
- ✅ Memory & Sequential Thinking working
- ❌ PostgreSQL not installed
- ❌ Missing GitHub token & Firecrawl key

Priority: Install PostgreSQL, get remaining API keys, then test GHL integration with "Query recent leads from Jorge's GHL account".

Key files: .mcp.json, MCP_SETUP_STATUS.md
```

## ⚡ Immediate Commands

### 1. Check Current Status
```bash
# Check what's working
ToolSearch query="postgres"
mcp__postgres__query sql="SELECT 1"

# Check GHL tools availability
ToolSearch query="gohl"
ToolSearch query="leadconnector"
```

### 2. PostgreSQL Installation
```bash
# Option A: Homebrew
brew install postgresql@14
brew services start postgresql@14
createdb enterprisehub

# Option B: Check if already installed
which psql
brew services list | grep postgres

# Test connection
psql -d enterprisehub -c "SELECT 1"
```

### 3. API Key Collection URLs
- **GitHub**: https://github.com/settings/tokens/new (repo access)
- **Firecrawl**: https://firecrawl.dev/app/api-keys

## 🎯 Success Criteria

When setup is complete, these should work:

```bash
# Test 1: Database connection
mcp__postgres__query sql="SELECT current_database()"

# Test 2: GHL lead query
mcp__leadconnector__list_contacts location_id="3xt4qayAh35BIDLaUv7P"

# Test 3: Property scraping
mcp__firecrawl__scrape url="https://www.zillow.com/rancho_cucamonga-tx/"

# Test 4: Full workflow
"Query GHL for leads with budget >$500k, find matching Rancho Cucamonga properties, create outreach plan"
```

## 🔧 File Locations

- **Config**: `/Users/cave/Documents/GitHub/EnterpriseHub/.mcp.json`
- **Status**: `/Users/cave/Documents/GitHub/EnterpriseHub/MCP_SETUP_STATUS.md`
- **Project Context**: `/Users/cave/Documents/GitHub/EnterpriseHub/CLAUDE.md`
- **Universal Context**: `/Users/cave/.claude/CLAUDE.md`

## 📞 Jorge's Credentials (Reference)

```
Location ID: [REPLACE_WITH_JORGE_LOCATION_ID]
API Key: [REPLACE_WITH_JORGE_GHL_API_KEY]
Realtor Email: realtorjorgesalas@gmail.com
```

---

**Next Session Goal**: Complete PostgreSQL + API keys → Test Jorge's GHL integration → Deploy full AI+CRM automation