#!/bin/bash
# NotebookLM MCP Server Installation Script

set -e

echo "🚀 Installing NotebookLM MCP Server for Claude Code..."
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Python $PYTHON_VERSION detected"

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip3 install -r "$(dirname "$0")/requirements.txt"

# Check for Google authentication
echo ""
echo "🔐 Checking Google authentication..."

if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "✓ Service account credentials found: $GOOGLE_APPLICATION_CREDENTIALS"
elif command -v gcloud &> /dev/null; then
    echo "✓ gcloud CLI detected"
    echo ""
    echo "Setting up Application Default Credentials..."
    gcloud auth application-default login
else
    echo "⚠️  Warning: No authentication method found"
    echo ""
    echo "Please set up authentication using one of these methods:"
    echo ""
    echo "Method 1: Install gcloud CLI and run:"
    echo "  gcloud auth application-default login"
    echo ""
    echo "Method 2: Set service account credentials:"
    echo "  export GOOGLE_APPLICATION_CREDENTIALS='/path/to/credentials.json'"
    echo ""
    echo "Visit: https://cloud.google.com/docs/authentication/getting-started"
    echo ""
fi

# Test the MCP server
echo ""
echo "🧪 Testing MCP server..."

# Create a test JSON-RPC request
TEST_REQUEST='{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

# Test server startup (timeout after 5 seconds)
if echo "$TEST_REQUEST" | timeout 5 python3 "$(dirname "$0")/server.py" > /dev/null 2>&1; then
    echo "✓ MCP server test successful"
else
    echo "⚠️  Server test failed - check authentication and dependencies"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "📚 Next steps:"
echo "1. Restart Claude Code to load the new MCP server"
echo "2. Verify tools are available with: /tools"
echo "3. Create your first research notebook!"
echo ""
echo "💡 Quick start:"
echo '   Ask Claude Code: "Create a NotebookLM notebook for my research"'
echo ""
