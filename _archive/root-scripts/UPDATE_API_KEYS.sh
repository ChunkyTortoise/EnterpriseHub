#!/bin/bash

# Quick API Key Update Script for EnterpriseHub MCP Setup
echo "🔑 EnterpriseHub MCP API Key Setup"
echo "================================="

echo ""
echo "1. GitHub Personal Access Token:"
echo "   Go to: https://github.com/settings/tokens/new"
echo "   Scopes: repo, read:user, user:email"
echo ""
read -p "Enter your GitHub token (ghp_...): " GITHUB_TOKEN

echo ""
echo "2. Firecrawl API Key:"
echo "   Go to: https://firecrawl.dev"
echo "   Dashboard → API Keys"
echo ""
read -p "Enter your Firecrawl API key (fc-...): " FIRECRAWL_KEY

echo ""
echo "📝 Updating .mcp.json..."

# Update .mcp.json with actual API keys
sed -i.bak "s|your_github_token_here|$GITHUB_TOKEN|g" .mcp.json
sed -i.bak "s|your_firecrawl_api_key_here|$FIRECRAWL_KEY|g" .mcp.json

echo "✅ Configuration updated!"
echo ""
echo "🔄 Next steps:"
echo "1. Exit Claude Code: type 'exit'"
echo "2. Restart: type 'claude' in this directory"
echo "3. Test with: 'Query Jorge's GHL leads and find matching Rancho Cucamonga properties'"
echo ""
echo "🎯 Expected tools after restart:"
echo "- ✅ PostgreSQL (working now)"
echo "- ✅ Memory & Sequential Thinking (working now)"
echo "- ✅ GoHighLevel (Jorge's account access)"
echo "- ✅ GitHub (repository operations)"
echo "- ✅ Firecrawl (property scraping)"
echo ""
echo "Jorge's GHL Location: 3xt4qayAh35BIDLaUv7P"
echo "Database: enterprisehub (ready for BI queries)"