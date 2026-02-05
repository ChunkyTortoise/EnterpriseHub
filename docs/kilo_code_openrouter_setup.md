# Kilo Code + OpenRouter Setup Guide

## Quick Setup for Kilo Code

Add these settings to your VS Code `settings.json`:

### Method 1: Open VS Code Settings
1. Press `Cmd+Shift+P` (Command Palette)
2. Type: **"Preferences: Open User Settings (JSON)"**
3. Add these settings:

```json
{
  "kilocode.apiProvider": "openrouter",
  "kilocode.openRouterApiKey": "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",
  "kilocode.openRouterModel": "anthropic/claude-3.5-sonnet",
  "kilocode.apiBaseUrl": "https://openrouter.ai/api/v1"
}
```

### Method 2: Via Kilo Code Settings UI
1. Open VS Code Settings: `Cmd+,`
2. Search for "Kilo Code"
3. Configure:
   - **API Provider**: Select "OpenRouter" or "Custom"
   - **API Key**: `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`
   - **Model**: `anthropic/claude-3.5-sonnet`
   - **Base URL**: `https://openrouter.ai/api/v1`

## Alternative: Use OpenAI-Compatible Format

Some tools work better with OpenAI-compatible settings:

```json
{
  "kilocode.apiProvider": "openai",
  "kilocode.openai.apiKey": "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",
  "kilocode.openai.baseURL": "https://openrouter.ai/api/v1",
  "kilocode.model": "anthropic/claude-3.5-sonnet"
}
```

## Popular Models to Try

- `anthropic/claude-3.5-sonnet` - Best for code (default)
- `openai/gpt-4-turbo` - Strong reasoning
- `google/gemini-pro-1.5` - Fast and capable
- `meta-llama/llama-3.1-70b-instruct` - Open source

## Testing

After configuration:
1. Open any code file in VS Code
2. Select some code
3. Use Kilo Code commands (e.g., "Explain", "Refactor")
4. Should now use OpenRouter!

## Notes

- **Antigravity** (this tool) uses Google's backend - no config needed
- **Your EnterpriseHub code** - already configured via `.env`
- **Kilo Code** - configure via VS Code settings as above

## Troubleshooting

If Kilo Code doesn't have OpenRouter-specific settings:
- Try the OpenAI-compatible format above
- OpenRouter is OpenAI API-compatible
- Set provider to "openai" but use OpenRouter's base URL
