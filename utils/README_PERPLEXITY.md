# Perplexity MCP Server for Claude Code

This utility allows Claude Code to search the web using Perplexity's API via the Model Context Protocol (MCP).

## Prerequisites

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    (Ensure `fastmcp` and `httpx` are installed)

2.  **Get API Key:**
    Get a Perplexity API key from [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api).

## Configuration

### Option A: Standard Claude Code CLI

Add the following to your Claude Code configuration file.
*   **macOS:** `~/Library/Application Support/Claude/config.json`
*   **Linux:** `~/.config/Claude/config.json`
*   **Windows:** `%APPDATA%\Claude\config.json`

```json
{
  "mcpServers": {
    "perplexity": {
      "command": "python3",
      "args": [
        "/Users/cave/enterprisehub/utils/perplexity_mcp.py"
      ],
      "env": {
        "PERPLEXITY_API_KEY": "pplx-YOUR_API_KEY_HERE"
      }
    }
  }
}
```

### Option B: Auto-Claude Framework

If you are using the `auto-claude` system in this repository, you can configure it via the `.auto-claude/.env` file:

```bash
CUSTOM_MCP_SERVERS=[{"id":"perplexity","type":"command","command":"python3","args":["utils/perplexity_mcp.py"],"env":{"PERPLEXITY_API_KEY":"pplx-YOUR_KEY"}}]
```

## Testing

You can test the server directly:

```bash
export PERPLEXITY_API_KEY=pplx-YOUR_KEY
python3 utils/perplexity_mcp.py
```
