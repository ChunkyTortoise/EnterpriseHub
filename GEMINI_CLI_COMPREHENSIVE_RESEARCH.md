# Gemini CLI Comprehensive Research & Configuration Guide

**Research Date:** January 9, 2026
**Gemini CLI Version:** 0.23.0
**Comparison Target:** Claude Code (Anthropic)

---

## Executive Summary

This document provides a complete analysis of Gemini CLI's configuration capabilities, architectural patterns, and a detailed comparison with Claude Code. The research covers configuration files, approval modes, session management, extension systems, MCP integration, and advanced features.

### Key Findings

1. **Configuration Locations:** 4 hierarchical levels (system defaults, user, project, system override)
2. **Approval Modes:** 3 modes (default, auto_edit, yolo) with CLI and keyboard shortcuts
3. **Session Storage:** Project-specific in `~/.gemini/tmp/<project_hash>/chats/`
4. **Extension System:** Comprehensive with auto-discovery, git installation, local linking
5. **MCP Integration:** Full Model Context Protocol support with OAuth discovery
6. **Hooks System:** Complete lifecycle hooks (BeforeTool, AfterTool, etc.)

---

## 1. Configuration Files & Locations

### 1.1 Configuration File Hierarchy

Gemini CLI uses **JSON settings files** across **four hierarchical locations**:

| Priority | Location | Path | Scope |
|----------|----------|------|-------|
| 1 (Lowest) | System Defaults | `/etc/gemini-cli/system-defaults.json` (Linux/macOS)<br>`C:\ProgramData\gemini-cli\system-defaults.json` (Windows) | Base layer defaults |
| 2 | User Settings | `~/.gemini/settings.json` | All sessions for current user |
| 3 | Project Settings | `.gemini/settings.json` | Project-specific overrides |
| 4 | System Override | `/etc/gemini-cli/settings.json` (Linux/macOS)<br>`C:\ProgramData\gemini-cli\settings.json` (Windows) | Enterprise-level overrides |

**Path Overrides:**
- `GEMINI_CLI_SYSTEM_DEFAULTS_PATH` - Override system defaults location
- `GEMINI_CLI_SYSTEM_SETTINGS_PATH` - Override system settings location

### 1.2 Configuration Precedence (Low to High)

1. **Default hardcoded values** (built into application)
2. **System defaults file** (`/etc/gemini-cli/system-defaults.json`)
3. **User settings file** (`~/.gemini/settings.json`)
4. **Project settings file** (`.gemini/settings.json`)
5. **System settings file** (`/etc/gemini-cli/settings.json`)
6. **Environment variables** (including `.env` files)
7. **Command-line arguments** (**HIGHEST precedence**)

### 1.3 Configuration Format

**File Format:** JSON
**Schema Validation:** Available at `https://raw.githubusercontent.com/google-gemini/gemini-cli/main/schemas/settings.schema.json`

**Example Structure:**
```json
{
  "general": {
    "previewFeatures": true,
    "vimMode": false
  },
  "ui": {
    "theme": "dark",
    "hideFooter": false
  },
  "security": {
    "auth": {
      "selectedType": "oauth-personal"
    }
  },
  "tools": {
    "sandbox": true,
    "allowed": ["bash", "write"]
  },
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"]
    }
  }
}
```

### 1.4 Environment Variables (.env files)

**Loading Order:**
1. Current directory: `./.env`
2. Parent directories: Search upwards until `.env` found
3. Project root: Stop at `.git` folder
4. User home: `~/.env` (fallback)

**Project-specific .env:**
- `.gemini/.env` - Gemini CLI-specific variables (higher precedence)
- Variables from `.gemini/.env` override root `.env`

**Variable Substitution in settings.json:**
```json
{
  "mcpServers": {
    "github": {
      "env": {
        "GITHUB_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"
      }
    }
  }
}
```

---

## 2. Complete Settings Schema

### 2.1 `general` Category

| Setting | Type | Default | Description | Requires Restart |
|---------|------|---------|-------------|------------------|
| `previewFeatures` | boolean | `false` | Enable preview features/models | No |
| `preferredEditor` | string | - | Editor to open files | No |
| `vimMode` | boolean | `false` | Enable Vim keybindings | No |
| `disableAutoUpdate` | boolean | `false` | Prevent automatic updates | No |
| `disableUpdateNag` | boolean | `false` | Suppress update prompts | No |
| `checkpointing.enabled` | boolean | `false` | Session recovery checkpoints | **Yes** |
| `enablePromptCompletion` | boolean | `false` | AI-powered prompt suggestions | **Yes** |
| `retryFetchErrors` | boolean | `false` | Retry network failures | No |
| `debugKeystrokeLogging` | boolean | `false` | Console keystroke logging | No |
| `sessionRetention.enabled` | boolean | `false` | Auto cleanup old sessions | No |
| `sessionRetention.maxAge` | string | - | Age limit (e.g., "30d", "24h") | No |
| `sessionRetention.maxCount` | number | - | Session count limit | No |
| `sessionRetention.minRetention` | string | `"1d"` | Safety minimum retention | No |

### 2.2 `output` Category

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `format` | enum | `"text"` | CLI output format: `"text"` \| `"json"` |

### 2.3 `ui` Category

| Setting | Type | Default | Description | Requires Restart |
|---------|------|---------|-------------|------------------|
| `theme` | string | - | Color theme selection | No |
| `customThemes` | object | `{}` | Custom theme definitions | No |
| `hideWindowTitle` | boolean | `false` | Hide window title bar | **Yes** |
| `showStatusInTitle` | boolean | `false` | Show status in window title | No |
| `showHomeDirectoryWarning` | boolean | `true` | Warn when running from home | **Yes** |
| `hideTips` | boolean | `false` | Hide helpful tips | No |
| `hideBanner` | boolean | `false` | Hide application banner | No |
| `hideContextSummary` | boolean | `false` | Hide GEMINI.md indicator | No |
| `footer.hideCWD` | boolean | `false` | Hide working directory | No |
| `footer.hideSandboxStatus` | boolean | `false` | Hide sandbox indicator | No |
| `footer.hideModelInfo` | boolean | `false` | Hide model/context usage | No |
| `footer.hideContextPercentage` | boolean | `true` | Hide context percentage | No |
| `hideFooter` | boolean | `false` | Hide entire footer | No |
| `showMemoryUsage` | boolean | `false` | Display memory statistics | No |
| `showLineNumbers` | boolean | `true` | Line numbers in chat | No |
| `showCitations` | boolean | `false` | Show text citations | No |
| `showModelInfoInChat` | boolean | `false` | Model name per turn | No |
| `useFullWidth` | boolean | `true` | Use full terminal width | No |
| `useAlternateBuffer` | boolean | `false` | Use alternate screen buffer | **Yes** |
| `incrementalRendering` | boolean | `true` | Incremental response rendering | **Yes** |
| `customWittyPhrases` | array | `[]` | Custom loading messages | No |
| `accessibility.disableLoadingPhrases` | boolean | `false` | Disable loading phrases | **Yes** |
| `accessibility.screenReader` | boolean | `false` | Screen reader mode | **Yes** |

### 2.4 `ide` Category

| Setting | Type | Default | Description | Requires Restart |
|---------|------|---------|-------------|------------------|
| `enabled` | boolean | `false` | IDE integration mode | **Yes** |
| `hasSeenNudge` | boolean | `false` | Nudge tracking (internal) | No |

### 2.5 `privacy` Category

| Setting | Type | Default | Description | Requires Restart |
|---------|------|---------|-------------|------------------|
| `usageStatisticsEnabled` | boolean | `true` | Opt-in usage statistics | **Yes** |

### 2.6 `model` Category

| Setting | Type | Default | Description | Requires Restart |
|---------|------|---------|-------------|------------------|
| `name` | string | - | Gemini model selection | No |
| `maxSessionTurns` | number | `-1` | Turn limit (-1 = unlimited) | No |
| `summarizeToolOutput` | object | - | Token budgets per tool | No |
| `compressionThreshold` | number | `0.5` | Context compression threshold | **Yes** |
| `skipNextSpeakerCheck` | boolean | `true` | Skip speaker validation | No |

### 2.7 `modelConfigs` Category

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `aliases` | object | - | Named model config presets (supports inheritance) |
| `customAliases` | object | `{}` | User-defined presets |
| `customOverrides` | array | `[]` | Custom config overrides |
| `overrides` | array | `[]` | Conditional config application |

### 2.8 `context` Category

| Setting | Type | Default | Description | Requires Restart |
|---------|------|---------|-------------|------------------|
| `fileName` | string \| array | `undefined` | Context file(s) to load (default: `GEMINI.md`) | No |
| `importFormat` | string | - | Memory import format | No |
| `discoveryMaxDirs` | number | `200` | Max directories searched | No |
| `includeDirectories` | array | `[]` | Additional directories for context | No |
| `loadMemoryFromIncludeDirectories` | boolean | `false` | Load memory from included dirs | No |
| `fileFiltering.respectGitIgnore` | boolean | `true` | Honor `.gitignore` | **Yes** |
| `fileFiltering.respectGeminiIgnore` | boolean | `true` | Honor `.geminiignore` | **Yes** |
| `fileFiltering.enableRecursiveFileSearch` | boolean | `true` | Recursive file discovery | **Yes** |
| `fileFiltering.disableFuzzySearch` | boolean | `false` | Disable fuzzy matching | **Yes** |

### 2.9 `tools` Category

| Setting | Type | Default | Description | Requires Restart |
|---------|------|---------|-------------|------------------|
| `sandbox` | boolean \| string | - | Sandbox mode: `true`, `false`, `"docker"`, `"podman"`, or custom path | **Yes** |
| `shell.enableInteractiveShell` | boolean | `true` | Enable interactive shell | **Yes** |
| `shell.pager` | string | `"cat"` | Pager command | No |
| `shell.showColor` | boolean | `false` | Color output in shell | No |
| `shell.inactivityTimeout` | number | `300` | Seconds before timeout | No |
| `shell.enableShellOutputEfficiency` | boolean | `true` | Optimize shell output | No |
| `autoAccept` | boolean | `false` | Auto-approve safe operations | No |
| `core` | array | - | Allowlist of built-in tools | **Yes** |
| `allowed` | array | - | Tools bypassing confirmation | **Yes** |
| `exclude` | array | - | Tools to hide | **Yes** |
| `discoveryCommand` | string | - | Custom tool discovery command | **Yes** |
| `callCommand` | string | - | Custom tool invocation command | **Yes** |
| `useRipgrep` | boolean | `true` | Use ripgrep for faster search | No |
| `enableToolOutputTruncation` | boolean | `true` | Truncate long tool outputs | **Yes** |
| `truncateToolOutputThreshold` | number | `4000000` | Truncation threshold (chars) | **Yes** |
| `truncateToolOutputLines` | number | `1000` | Truncation limit (lines) | **Yes** |
| `enableHooks` | boolean | `true` | Enable hooks system | **Yes** |

### 2.10 `mcp` Category

| Setting | Type | Default | Description | Requires Restart |
|---------|------|---------|-------------|------------------|
| `serverCommand` | string | - | MCP server startup command | **Yes** |
| `allowed` | array | - | Allowlisted MCP servers | **Yes** |
| `excluded` | array | - | Excluded MCP servers | **Yes** |

### 2.11 `useWriteTodos` Category

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `useWriteTodos` | boolean | `true` | Enable `write_todos` tool |

### 2.12 `security` Category

| Setting | Type | Default | Description | Requires Restart |
|---------|------|---------|-------------|------------------|
| `disableYoloMode` | boolean | `false` | Disable YOLO mode globally | **Yes** |
| `enablePermanentToolApproval` | boolean | `false` | Allow permanent tool approval | No |
| `blockGitExtensions` | boolean | `false` | Block git-related extensions | **Yes** |
| `folderTrust.enabled` | boolean | `false` | Enable folder trust system | **Yes** |
| `environmentVariableRedaction.allowed` | array | `[]` | Allowed env vars (never redacted) | **Yes** |
| `environmentVariableRedaction.blocked` | array | `[]` | Blocked env vars (always redacted) | **Yes** |
| `environmentVariableRedaction.enabled` | boolean | `false` | Enable env var redaction | **Yes** |
| `auth.selectedType` | string | - | Authentication type | **Yes** |
| `auth.enforcedType` | string | - | Enforced auth type | **Yes** |
| `auth.useExternal` | boolean | - | Use external auth | **Yes** |

### 2.13 `advanced` Category

| Setting | Type | Default | Description | Requires Restart |
|---------|------|---------|-------------|------------------|
| `autoConfigureMemory` | boolean | `false` | Auto-configure memory settings | **Yes** |
| `dnsResolutionOrder` | string | - | DNS resolution priority | **Yes** |
| `excludedEnvVars` | array | `["DEBUG", "DEBUG_MODE"]` | Vars excluded from project `.env` | No |
| `bugCommand` | object | - | Bug report configuration | No |

### 2.14 `experimental` Category

| Setting | Type | Default | Description | Requires Restart |
|---------|------|---------|-------------|------------------|
| `enableAgents` | boolean | `false` | Enable agents feature | **Yes** |
| `extensionManagement` | boolean | `true` | Enable extension management | **Yes** |
| `extensionReloading` | boolean | `false` | Hot reload extensions | **Yes** |
| `jitContext` | boolean | `false` | Just-in-time context loading | **Yes** |
| `skills` | boolean | `false` | Enable skills system | **Yes** |
| `codebaseInvestigatorSettings.enabled` | boolean | `true` | Enable codebase investigator | **Yes** |
| `codebaseInvestigatorSettings.maxNumTurns` | number | `10` | Max investigator turns | **Yes** |
| `codebaseInvestigatorSettings.maxTimeMinutes` | number | `3` | Max investigator time | **Yes** |
| `codebaseInvestigatorSettings.thinkingBudget` | number | `8192` | Thinking token budget | **Yes** |
| `codebaseInvestigatorSettings.model` | string | `"auto"` | Investigator model | **Yes** |
| `useOSC52Paste` | boolean | `false` | Enable OSC52 clipboard | No |
| `cliHelpAgentSettings.enabled` | boolean | `true` | Enable CLI help agent | **Yes** |

### 2.15 `skills` Category

| Setting | Type | Default | Description | Requires Restart |
|---------|------|---------|-------------|------------------|
| `disabled` | array | `[]` | Disabled skill names | **Yes** |

### 2.16 `hooks` Category

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `enabled` | boolean | `false` | Enable hooks system |
| `disabled` | array | `[]` | Disabled hook names |
| `notifications` | boolean | `true` | Show hook notifications |
| `BeforeTool` | array | `[]` | Pre-tool execution hooks |
| `AfterTool` | array | `[]` | Post-tool execution hooks |
| `BeforeAgent` | array | `[]` | Pre-agent hooks |
| `AfterAgent` | array | `[]` | Post-agent hooks |
| `Notification` | array | `[]` | Notification hooks |
| `SessionStart` | array | `[]` | Session start hooks |
| `SessionEnd` | array | `[]` | Session end hooks |
| `PreCompress` | array | `[]` | Pre-compression hooks |
| `BeforeModel` | array | `[]` | Pre-model inference hooks |
| `AfterModel` | array | `[]` | Post-model inference hooks |
| `BeforeToolSelection` | array | `[]` | Pre-tool selection hooks |

### 2.17 `admin` Category

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `secureModeEnabled` | boolean | `false` | Disallow YOLO mode |
| `extensions.enabled` | boolean | `true` | Allow extensions |
| `mcp.enabled` | boolean | `true` | Allow MCP servers |

### 2.18 `mcpServers` Category

Configure Model-Context Protocol server connections by server name:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `command` | string | optional | Startup command |
| `args` | array | optional | Command arguments |
| `env` | object | optional | Environment variables |
| `cwd` | string | optional | Working directory |
| `url` | string | optional | SSE endpoint URL |
| `httpUrl` | string | optional | HTTP endpoint (precedence over `url`) |
| `headers` | object | optional | HTTP headers |
| `timeout` | number | optional | Request timeout (milliseconds) |
| `trust` | boolean | optional | Bypass tool confirmations |
| `description` | string | optional | Server description |
| `includeTools` | array | optional | Allowlisted tools (only these will be available) |
| `excludeTools` | array | optional | Excluded tools (takes precedence over `includeTools`) |

**Example:**
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      },
      "includeTools": ["create_issue", "list_repos"],
      "excludeTools": ["delete_repo"]
    },
    "filesystem": {
      "httpUrl": "http://localhost:8080/mcp",
      "trust": false,
      "timeout": 5000
    }
  }
}
```

### 2.19 `telemetry` Category

| Setting | Type | Description |
|---------|------|-------------|
| `enabled` | boolean | Enable telemetry collection |
| `target` | string | Destination: `"local"` or `"gcp"` |
| `otlpEndpoint` | string | OpenTelemetry Protocol endpoint |
| `otlpProtocol` | string | Protocol: `"grpc"` or `"http"` |
| `logPrompts` | boolean | Include prompt content in telemetry |
| `outfile` | string | Local telemetry file path |
| `useCollector` | boolean | Use external OTLP collector |

---

## 3. Permission & Approval Modes

### 3.1 Available Approval Modes

Gemini CLI supports **3 approval modes** for tool execution:

| Mode | Description | Safety Level | Use Case |
|------|-------------|--------------|----------|
| **default** | Prompt for approval on every tool action that modifies the system | **Highest** | Production work, learning, cautious development |
| **auto_edit** | Auto-approve file edits only; prompt for other operations | **Medium** | Active development, trusted environments |
| **yolo** | Auto-approve **ALL** tool actions without prompts | **Lowest** | Rapid prototyping, throw-away projects |

### 3.2 Activation Methods

#### **3.2.1 Command-Line Flags**

```bash
# Default mode (safe, prompts for all)
gemini

# Auto-edit mode (auto-approve edits)
gemini --approval-mode=auto_edit

# YOLO mode (auto-approve everything)
gemini --approval-mode=yolo
# OR (legacy flag)
gemini --yolo
```

#### **3.2.2 Keyboard Shortcuts (In-Session)**

| Shortcut | Action |
|----------|--------|
| **Ctrl+Y** | Toggle YOLO mode (auto-approval) |
| **Shift+Tab** | Toggle Auto Edit mode (auto-accept edits) |

#### **3.2.3 Settings Configuration**

```json
{
  "security": {
    "disableYoloMode": false,
    "enablePermanentToolApproval": false
  },
  "tools": {
    "autoAccept": false,
    "allowed": ["bash", "write", "edit"]
  }
}
```

### 3.3 Per-Tool Permission Controls

#### **3.3.1 Allowed Tools (Bypass Confirmation)**

**CLI Flag:**
```bash
gemini --allowed-tools bash,write,read
```

**settings.json:**
```json
{
  "tools": {
    "allowed": ["bash", "write", "read", "edit"]
  }
}
```

#### **3.3.2 Excluded Tools (Blocked)**

```json
{
  "tools": {
    "exclude": ["run_shell_command", "delete_file"]
  }
}
```

#### **3.3.3 Core Tools (Allowlist Only)**

Restrict to specific built-in tools:

```json
{
  "tools": {
    "core": ["bash", "read", "write", "edit", "glob"]
  }
}
```

### 3.4 MCP Server Permission Settings

Control tool access per MCP server:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx -y @modelcontextprotocol/server-github",
      "trust": false,
      "includeTools": ["create_issue", "list_repos", "create_pr"],
      "excludeTools": ["delete_repo", "force_push"]
    }
  }
}
```

**Key Concepts:**
- `trust: true` - Bypass all confirmations for this server
- `includeTools` - Allowlist (only these tools available)
- `excludeTools` - Blocklist (takes precedence over `includeTools`)

### 3.5 Security Features

#### **3.5.1 Sandbox Mode**

Automatically enabled with `--yolo` or `--approval-mode=yolo`:

```bash
gemini --yolo  # Sandbox auto-enabled
gemini --approval-mode=yolo --sandbox=false  # Disable sandbox
```

**Configuration:**
```json
{
  "tools": {
    "sandbox": true  // or "docker", "podman", "/path/to/custom"
  }
}
```

#### **3.5.2 Folder Trust System**

```json
{
  "security": {
    "folderTrust": {
      "enabled": true
    }
  }
}
```

#### **3.5.3 Environment Variable Redaction**

**Automatic redaction for variables containing:**
- `TOKEN`, `SECRET`, `PASSWORD`, `KEY`, `AUTH`, `CREDENTIAL`, `PRIVATE`, `CERT`

**Specific blocklist:**
- `CLIENT_ID`, `DB_URI`, `DATABASE_URL`, `CONNECTION_STRING`

**Allowlist (never redacted):**
- `PATH`, `HOME`, `USER`, `SHELL`, `TERM`, `LANG`, `GEMINI_CLI_*`

**Custom configuration:**
```json
{
  "security": {
    "environmentVariableRedaction": {
      "enabled": true,
      "allowed": ["MY_PUBLIC_KEY"],
      "blocked": ["INTERNAL_IP_ADDRESS"]
    }
  }
}
```

---

## 4. Session Management

### 4.1 Session Storage Location

**Path:** `~/.gemini/tmp/<project_hash>/chats/`

**Structure:**
```
~/.gemini/tmp/
└── 2b3e2ec35691dfcb4bb3e724514a8a0a160171808728b97f16953181b666040c/
    └── chats/
        ├── session-2026-01-09T12-30-4e65d8da.json
        ├── session-2026-01-08T18-45-2e975b07.json
        └── session-2026-01-07T10-15-ee3ff210.json
```

**Project Hash:**
- Derived from project directory path
- Ensures sessions are project-specific
- Switching directories switches session history

### 4.2 Session Persistence

**Automatic Saving:**
- Enabled by default (v0.20.0+)
- Saves every interaction in real-time
- No manual intervention required

**What Gets Saved:**
- Complete conversation history
- All prompts and model responses
- Tool executions (inputs and outputs)
- Token usage statistics (input/output/cached)
- Assistant thoughts/reasoning summaries

### 4.3 Session Resumption Capabilities

#### **4.3.1 CLI Commands**

```bash
# Resume most recent session
gemini --resume
gemini --resume latest

# Resume by index (see list)
gemini --resume 5

# Resume by UUID
gemini --resume 4e65d8da-41ab-4530-a8e8-23821a8a8deb
```

#### **4.3.2 In-Session Commands**

```bash
# Open Session Browser
/resume

# Filter sessions by keyword
/  # Press '/' and type to filter

# Select and restore session
# Press Enter on session to restore
```

#### **4.3.3 Session Management Commands**

```bash
# List all sessions for current project
gemini --list-sessions

# Delete specific session
gemini --delete-session 5
gemini --delete-session 4e65d8da-41ab-4530-a8e8-23821a8a8deb
```

### 4.4 Session Retention Policies

**Configuration:**
```json
{
  "general": {
    "sessionRetention": {
      "enabled": true,
      "maxAge": "30d",
      "maxCount": 100,
      "minRetention": "1d"
    }
  }
}
```

**Options:**
- `maxAge`: Auto-delete sessions older than (e.g., `"30d"`, `"24h"`)
- `maxCount`: Keep only N most recent sessions
- `minRetention`: Safety minimum (always keep sessions newer than this)

### 4.5 Session Format

**JSON Structure:**
```json
{
  "id": "4e65d8da-41ab-4530-a8e8-23821a8a8deb",
  "timestamp": "2026-01-09T19:43:00Z",
  "projectHash": "2b3e2ec35691dfcb4bb3e724514a8a0a160171808728b97f16953181b666040c",
  "turns": [
    {
      "role": "user",
      "content": "..."
    },
    {
      "role": "assistant",
      "content": "...",
      "toolCalls": [...]
    }
  ],
  "tokenUsage": {
    "input": 12345,
    "output": 6789,
    "cached": 3456
  }
}
```

---

## 5. Extension System

### 5.1 Extension Architecture

**Directory Structure:**
```
~/.gemini/extensions/
├── extension-name/
│   ├── gemini-extension.json       # Manifest (REQUIRED)
│   ├── GEMINI.md                   # Context/instructions
│   ├── mcpServers.json             # MCP server definitions
│   ├── commands/                   # Custom slash commands
│   │   └── hello.toml
│   ├── scripts/                    # Helper utilities
│   │   └── setup.sh
│   └── .env                        # Extension-specific env vars
```

**Key Principles:**
- **Manifest Required:** `gemini-extension.json` defines the extension
- **Component Directories:** At plugin root level (NOT inside `.gemini-plugin/`)
- **Context Files:** `GEMINI.md` provides model instructions
- **MCP Integration:** `mcpServers.json` for external tool connections

### 5.2 Extension Components

| Component | Directory | Description |
|-----------|-----------|-------------|
| **MCP Server Configurations** | Root | External tools and APIs via Model Context Protocol |
| **Context Files** | `GEMINI.md` | Model-specific instructions and context |
| **Custom Slash Commands** | `commands/` | TOML files defining reusable prompts |
| **Tool Restrictions** | Manifest | `excludeTools` to disable built-in tools |

### 5.3 Extension Installation & Management

#### **5.3.1 Install from GitHub**

```bash
gemini extensions install https://github.com/user/extension-name
gemini extensions install https://github.com/user/extension-name --auto-update
gemini extensions install https://github.com/user/extension-name --pre-release
```

#### **5.3.2 Install from Local Path**

```bash
gemini extensions install /path/to/extension
```

#### **5.3.3 Link for Development**

```bash
gemini extensions link /path/to/extension-dev
```

Live changes reflected immediately (hot reload if `experimental.extensionReloading: true`)

#### **5.3.4 Uninstall**

```bash
gemini extensions uninstall extension-name
```

#### **5.3.5 List Installed**

```bash
gemini extensions list
gemini --list-extensions  # Alternative
```

#### **5.3.6 Enable/Disable**

```bash
# Disable extension
gemini extensions disable extension-name
gemini extensions disable extension-name --scope=project

# Enable extension
gemini extensions enable extension-name
gemini extensions enable extension-name --scope=project
```

#### **5.3.7 Update**

```bash
# Update all extensions
gemini extensions update --all

# Update specific extension
gemini extensions update extension-name
```

#### **5.3.8 Validate**

```bash
gemini extensions validate /path/to/extension
```

#### **5.3.9 Create New**

```bash
gemini extensions new /path/to/new-extension [template]
```

#### **5.3.10 Extension Settings**

```bash
gemini extensions settings <command>
```

### 5.4 Using Extensions

**CLI Flag:**
```bash
# Use specific extensions
gemini -e extension1,extension2

# Use all installed extensions (default)
gemini
```

**Configuration:**
```json
{
  "admin": {
    "extensions": {
      "enabled": true
    }
  },
  "experimental": {
    "extensionManagement": true,
    "extensionReloading": false
  }
}
```

### 5.5 Extension Manifest (gemini-extension.json)

**Example:**
```json
{
  "name": "my-extension",
  "version": "1.0.0",
  "description": "Custom extension for...",
  "author": "Your Name",
  "license": "MIT",
  "geminiVersion": ">=0.20.0",
  "settings": {
    "tools": {
      "exclude": ["dangerous_tool"]
    }
  },
  "dependencies": {
    "npm": {
      "@modelcontextprotocol/server-github": "^1.0.0"
    }
  }
}
```

### 5.6 Custom Commands (TOML Format)

**Example:** `commands/hello.toml`

```toml
name = "hello"
description = "Greet the user"

[prompt]
system = """
You are a friendly assistant. Greet the user warmly.
"""

user = """
Say hello to {{username}}.
"""

[arguments]
username = { type = "string", required = true, description = "User's name" }
```

**Usage:**
```bash
gemini /hello --username="Alice"
```

### 5.7 Extension Discovery & Auto-Discovery

**Official Extensions Catalog:**
- https://geminicli.com/extensions/
- Ranked by GitHub stars
- Community, partner, and Google-built extensions

**Discovery:**
```bash
gemini extensions list --available  # Browse available extensions
```

### 5.8 Extension Scoping

**Global Extensions:** `~/.gemini/extensions/`
**Project Extensions:** `.gemini/extensions/` (project-specific)

**Precedence:**
- Project extensions override global extensions
- Settings merge with project taking precedence

---

## 6. MCP (Model Context Protocol) Integration

### 6.1 MCP Overview

**Purpose:** Connect Gemini CLI to external tools and APIs through standardized protocol

**Benefits:**
- Extend capabilities beyond built-in tools
- Integrate with GitHub, Slack, databases, custom APIs
- Standardized interface for tool discovery and execution

### 6.2 MCP Server Configuration

**Location:** `settings.json` → `mcpServers` object

**Example:**
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      },
      "includeTools": ["create_issue", "list_repos", "create_pr"],
      "excludeTools": ["delete_repo"],
      "trust": false,
      "timeout": 5000
    },
    "filesystem": {
      "httpUrl": "http://localhost:8080/mcp",
      "headers": {
        "Authorization": "Bearer ${FS_API_KEY}"
      },
      "trust": true
    },
    "database": {
      "url": "sse://db-server.example.com/mcp",
      "cwd": "/var/app",
      "description": "Database query interface"
    }
  }
}
```

### 6.3 MCP Transport Mechanisms

| Type | Configuration | Use Case |
|------|---------------|----------|
| **stdio** | `command` + `args` | Local processes (npm packages) |
| **HTTP** | `httpUrl` | HTTP-based servers |
| **SSE** | `url` | Server-Sent Events |

### 6.4 MCP CLI Management

```bash
# Add MCP server
gemini mcp add github npx -y @modelcontextprotocol/server-github

# Add with arguments
gemini mcp add myserver /path/to/server --arg1 value1

# Remove MCP server
gemini mcp remove github

# List all configured MCP servers
gemini mcp list
```

### 6.5 MCP Tool Discovery Process

**Startup Sequence:**
1. CLI reads `mcpServers` from `settings.json`
2. Attempts connection to each configured server
3. Fetches tool definitions via MCP protocol
4. Validates and sanitizes tool schemas (Gemini API compatibility)
5. Registers tools in global registry with conflict resolution

**Conflict Resolution:**
- Multiple servers with same tool name
- First registration wins unprefixed name
- Subsequent servers get prefixed: `serverName__toolName`

**Example:**
```
Server A: create_file
Server B: create_file

Result:
- create_file → from Server A
- serverB__create_file → from Server B
```

### 6.6 MCP Server Filtering

**Global Filtering:**
```json
{
  "mcp": {
    "allowed": ["github", "filesystem"],
    "excluded": ["experimental-server"]
  }
}
```

**Per-Server Tool Filtering:**
```json
{
  "mcpServers": {
    "github": {
      "includeTools": ["create_issue", "list_repos"],
      "excludeTools": ["delete_repo", "force_push"]
    }
  }
}
```

**Precedence:**
- `excludeTools` takes precedence over `includeTools`
- If tool in both lists, it's excluded

### 6.7 MCP Authentication

**OAuth Discovery:**
```json
{
  "mcpServers": {
    "oauth-server": {
      "httpUrl": "https://api.example.com/mcp",
      "oauth": "dynamic_discovery"
    }
  }
}
```

**Manual Token:**
```json
{
  "mcpServers": {
    "github": {
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

### 6.8 MCP Allowed Server Names

**CLI Flag:**
```bash
gemini --allowed-mcp-server-names github,filesystem
```

**Configuration:**
```json
{
  "mcp": {
    "allowed": ["github", "filesystem"]
  }
}
```

### 6.9 MCP in Extensions

Extensions can bundle MCP server configurations:

**Extension Structure:**
```
my-extension/
├── gemini-extension.json
└── mcpServers.json
```

**mcpServers.json:**
```json
{
  "my-custom-api": {
    "httpUrl": "https://api.example.com/mcp",
    "headers": {
      "API-Key": "${MY_API_KEY}"
    }
  }
}
```

---

## 7. Advanced Features

### 7.1 Hooks System

**Purpose:** Intercept lifecycle events in Gemini agent loop for custom automation

**Available Hook Events:**
- `BeforeTool` - Before tool execution
- `AfterTool` - After tool execution
- `BeforeAgent` - Before agent invocation
- `AfterAgent` - After agent completion
- `Notification` - On notifications
- `SessionStart` - Session initialization
- `SessionEnd` - Session termination
- `PreCompress` - Before context compression
- `BeforeModel` - Before model inference
- `AfterModel` - After model inference
- `BeforeToolSelection` - Before tool selection

**Hook Types:**
1. **Command Hooks:** Run shell commands (communicate via exit codes/stdio)
2. **Plugin Hooks:** npm packages with `geminicli-plugin` label

**Configuration:**
```json
{
  "hooks": {
    "enabled": true,
    "notifications": true,
    "BeforeTool": [
      {
        "name": "prevent-commit-secrets",
        "command": "bash",
        "args": ["-c", "grep -r 'API_KEY' ."],
        "targetTools": ["bash", "write"],
        "exit": {
          "0": "allow",
          "1": "block"
        }
      }
    ],
    "AfterTool": [
      {
        "name": "auto-format",
        "command": "prettier",
        "args": ["--write", "${TOOL_OUTPUT_FILE}"],
        "targetTools": ["write", "edit"]
      }
    ]
  }
}
```

**Use Cases:**
- Prevent committing secrets (`BeforeTool`)
- Auto-format code after edits (`AfterTool`)
- Run tests after file changes (`AfterTool`)
- Filter available tools dynamically (`BeforeToolSelection`)
- Custom logging and analytics (`AfterModel`)

**Hook Management:**
```bash
# Open hooks panel
/hooks panel

# Enable/disable hooks
/hooks enable hook-name
/hooks disable hook-name

# Migrate from Claude Code
/hooks migrate
```

**Migration from Claude Code:**
- Automatic conversion of Claude Code hooks
- Tool name transformations
- Environment variable mapping: `$CLAUDE_PROJECT_DIR` → `$GEMINI_PROJECT_DIR`

### 7.2 Context Files & Memory

**Default File:** `GEMINI.md`

**Hierarchical Loading Order:**
1. Global: `~/.gemini/GEMINI.md`
2. Project ancestry: Current dir → up to `.git` or home
3. Subdirectories: Below current working dir (max 200 dirs)

**Configuration:**
```json
{
  "context": {
    "fileName": ["GEMINI.md", "CONTEXT.md"],
    "discoveryMaxDirs": 200,
    "includeDirectories": ["/path/to/extra/context"],
    "loadMemoryFromIncludeDirectories": true,
    "fileFiltering": {
      "respectGitIgnore": true,
      "respectGeminiIgnore": true,
      "enableRecursiveFileSearch": true,
      "disableFuzzySearch": false
    }
  }
}
```

**Import Syntax:**
```markdown
<!-- GEMINI.md -->
# Project Context

@path/to/architecture.md
@docs/api-reference.md

## Additional context...
```

**Commands:**
```bash
# Refresh context files
/memory refresh

# Show combined context
/memory show
```

### 7.3 Experimental Features

**Enable in settings.json:**
```json
{
  "general": {
    "previewFeatures": true
  },
  "experimental": {
    "enableAgents": true,
    "extensionManagement": true,
    "extensionReloading": false,
    "jitContext": true,
    "skills": true,
    "codebaseInvestigatorSettings": {
      "enabled": true,
      "maxNumTurns": 10,
      "maxTimeMinutes": 3,
      "thinkingBudget": 8192,
      "model": "auto"
    },
    "useOSC52Paste": false,
    "cliHelpAgentSettings": {
      "enabled": true
    }
  }
}
```

**Features:**
- **Agents:** Multi-agent workflows
- **JIT Context:** Just-in-time context loading (reduce token usage)
- **Skills:** Skills system (similar to Claude Code)
- **Codebase Investigator:** Deep codebase analysis agent
- **CLI Help Agent:** Intelligent CLI assistance
- **OSC52 Paste:** Clipboard integration via OSC52 escape codes

### 7.4 Sandbox Configuration

**Options:**
```json
{
  "tools": {
    "sandbox": true  // Boolean: enable/disable
    // OR
    "sandbox": "docker"  // Use Docker
    // OR
    "sandbox": "podman"  // Use Podman
    // OR
    "sandbox": "/path/to/custom/sandbox"  // Custom sandbox
  }
}
```

**Build Custom Sandbox:**
```dockerfile
# .gemini/sandbox.Dockerfile
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y \
    python3 \
    nodejs \
    npm
WORKDIR /workspace
```

**Environment Variable:**
```bash
BUILD_SANDBOX=1 gemini
```

**macOS Sandbox Profiles:**
```bash
SEATBELT_PROFILE=permissive-open gemini
# OR
SEATBELT_PROFILE=strict gemini
```

### 7.5 Telemetry & Observability

**Configuration:**
```json
{
  "telemetry": {
    "enabled": true,
    "target": "local",
    "otlpEndpoint": "http://localhost:4318",
    "otlpProtocol": "grpc",
    "logPrompts": false,
    "outfile": "/tmp/gemini-telemetry.json",
    "useCollector": false
  }
}
```

**Environment Variables:**
```bash
GEMINI_TELEMETRY_ENABLED=true
GEMINI_TELEMETRY_TARGET=gcp
GEMINI_TELEMETRY_OTLP_ENDPOINT=http://collector:4318
GEMINI_TELEMETRY_OTLP_PROTOCOL=http
GEMINI_TELEMETRY_LOG_PROMPTS=false
GEMINI_TELEMETRY_OUTFILE=/var/log/gemini.json
GEMINI_TELEMETRY_USE_COLLECTOR=true
```

### 7.6 Custom Tool Discovery

**Configuration:**
```json
{
  "tools": {
    "discoveryCommand": "/path/to/discover-tools.sh",
    "callCommand": "/path/to/call-tool.sh"
  }
}
```

**discoveryCommand Output (JSON):**
```json
[
  {
    "name": "custom_tool",
    "description": "Does something useful",
    "parameters": {
      "arg1": { "type": "string", "required": true }
    }
  }
]
```

**callCommand Input:**
```bash
# STDIN receives JSON:
# {
#   "tool": "custom_tool",
#   "arguments": { "arg1": "value" }
# }
```

### 7.7 Skills System (Experimental)

**Enable:**
```json
{
  "experimental": {
    "skills": true
  },
  "skills": {
    "disabled": ["skill-name"]
  }
}
```

**Skills Directory (in extensions):**
```
extension-name/
└── skills/
    └── my-skill/
        └── SKILL.md
```

**SKILL.md Format:**
```markdown
---
name: my-skill
description: Brief description
---

# Skill Instructions

Detailed instructions for the model...
```

### 7.8 Model Configuration & Aliases

**Configuration:**
```json
{
  "model": {
    "name": "gemini-2.5-flash",
    "maxSessionTurns": -1,
    "compressionThreshold": 0.5,
    "summarizeToolOutput": {
      "bash": 10000,
      "read": 50000
    }
  },
  "modelConfigs": {
    "aliases": {
      "fast": {
        "model": "gemini-2.5-flash",
        "temperature": 0.7
      },
      "precise": {
        "model": "gemini-2.5-pro",
        "temperature": 0.3
      }
    },
    "customAliases": {},
    "overrides": [
      {
        "match": { "language": "python" },
        "config": { "temperature": 0.5 }
      }
    ]
  }
}
```

**CLI:**
```bash
gemini --model gemini-2.5-pro
gemini -m fast  # Use alias
```

**Environment Variable:**
```bash
GEMINI_MODEL=gemini-2.5-flash gemini
```

### 7.9 Output Formats

**CLI Flag:**
```bash
gemini --output-format text  # Default
gemini --output-format json
gemini -o stream-json
```

**Configuration:**
```json
{
  "output": {
    "format": "text"
  }
}
```

**Options:**
- `text` - Human-readable terminal output
- `json` - Structured JSON response
- `stream-json` - Streaming JSON (NDJSON)

---

## 8. Environment Variables Reference

### 8.1 Authentication & API

| Variable | Description | Example |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Gemini API key | `AIzaSy...` |
| `GOOGLE_API_KEY` | Google Cloud API key | `AIzaSy...` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to credentials JSON | `/path/to/creds.json` |
| `GOOGLE_CLOUD_PROJECT` | GCP Project ID | `my-project-123` |
| `GOOGLE_CLOUD_LOCATION` | GCP region | `us-central1` |

### 8.2 Model & Runtime

| Variable | Description | Example |
|----------|-------------|---------|
| `GEMINI_MODEL` | Override default model | `gemini-2.5-flash` |
| `GEMINI_SANDBOX` | Enable sandbox mode | `true` |

### 8.3 System Prompt

| Variable | Description | Example |
|----------|-------------|---------|
| `GEMINI_SYSTEM_MD` | Path to custom system prompt | `./.gemini/system.md` |
| `GEMINI_WRITE_SYSTEM_MD` | Write built-in prompt to file | `true` |

### 8.4 Telemetry

| Variable | Description | Example |
|----------|-------------|---------|
| `GEMINI_TELEMETRY_ENABLED` | Enable/disable telemetry | `true` |
| `GEMINI_TELEMETRY_TARGET` | Destination (local/gcp) | `local` |
| `GEMINI_TELEMETRY_OTLP_ENDPOINT` | OTLP endpoint | `http://localhost:4318` |
| `GEMINI_TELEMETRY_OTLP_PROTOCOL` | Protocol (grpc/http) | `grpc` |
| `GEMINI_TELEMETRY_LOG_PROMPTS` | Include prompts | `false` |
| `GEMINI_TELEMETRY_OUTFILE` | Local file path | `/tmp/telemetry.json` |
| `GEMINI_TELEMETRY_USE_COLLECTOR` | Use OTLP collector | `true` |

### 8.5 Sandbox (macOS)

| Variable | Description | Example |
|----------|-------------|---------|
| `SEATBELT_PROFILE` | macOS sandbox profile | `permissive-open`, `strict` |

### 8.6 Utilities

| Variable | Description | Example |
|----------|-------------|---------|
| `DEBUG` or `DEBUG_MODE` | Verbose logging | `true` |
| `NO_COLOR` | Disable color output | `1` |
| `CLI_TITLE` | Custom CLI title | `My Dev Session` |
| `CODE_ASSIST_ENDPOINT` | Code assist server URL | `https://codeassist.example.com` |
| `OTLP_GOOGLE_CLOUD_PROJECT` | GCP project for telemetry | `my-project-123` |
| `BUILD_SANDBOX` | Build custom sandbox | `1` |

### 8.7 Path Overrides

| Variable | Description |
|----------|-------------|
| `GEMINI_CLI_SYSTEM_DEFAULTS_PATH` | Override system defaults location |
| `GEMINI_CLI_SYSTEM_SETTINGS_PATH` | Override system settings location |

---

## 9. Command-Line Arguments Reference

### 9.1 Basic Usage

```bash
gemini [options] [command] [query...]
```

### 9.2 Complete Flag Reference

| Flag | Short | Type | Description |
|------|-------|------|-------------|
| `--debug` | `-d` | boolean | Run in debug mode |
| `--model <name>` | `-m` | string | Override model |
| `--prompt <text>` | `-p` | string | Non-interactive prompt (deprecated, use positional) |
| `--prompt-interactive <text>` | `-i` | string | Execute prompt and continue interactive |
| `--sandbox` | `-s` | boolean | Enable sandbox |
| `--yolo` | `-y` | boolean | Auto-approve all actions (YOLO mode) |
| `--approval-mode <mode>` | | string | Set approval mode: `default`, `auto_edit`, `yolo` |
| `--experimental-acp` | | boolean | Start in ACP mode |
| `--allowed-mcp-server-names <list>` | | array | Allowed MCP server names |
| `--allowed-tools <list>` | | array | Tools allowed without confirmation |
| `--extensions <list>` | `-e` | array | Specific extensions to use |
| `--list-extensions` | `-l` | boolean | List all available extensions and exit |
| `--resume [id]` | `-r` | string | Resume session (latest or by index/UUID) |
| `--list-sessions` | | boolean | List available sessions and exit |
| `--delete-session <id>` | | string | Delete session by index/UUID |
| `--include-directories <dirs>` | | array | Additional workspace directories |
| `--screen-reader` | | boolean | Enable screen reader mode |
| `--output-format <format>` | `-o` | string | Output format: `text`, `json`, `stream-json` |
| `--version` | `-v` | boolean | Show version number |
| `--help` | `-h` | boolean | Show help |

### 9.3 Subcommands

#### **MCP Management**

```bash
gemini mcp add <name> <commandOrUrl> [args...]
gemini mcp remove <name>
gemini mcp list
```

#### **Extensions Management**

```bash
gemini extensions install <source> [--auto-update] [--pre-release]
gemini extensions uninstall <names..>
gemini extensions list
gemini extensions update [<name>] [--all]
gemini extensions disable [--scope] <name>
gemini extensions enable [--scope] <name>
gemini extensions link <path>
gemini extensions new <path> [template]
gemini extensions validate <path>
gemini extensions settings <command>
```

---

## 10. Gemini CLI vs Claude Code: Comprehensive Comparison

### 10.1 Feature Matrix

| Category | Feature | Gemini CLI | Claude Code | Notes |
|----------|---------|------------|-------------|-------|
| **Configuration** | Global config location | `~/.gemini/settings.json` | `~/.claude/settings.json` | Both similar |
| | Project config | `.gemini/settings.json` | `.claude/settings.json` | Both similar |
| | Config format | JSON | JSON | Identical |
| | Hierarchical config | 4 levels | 2 levels | Gemini has system defaults + override |
| | Environment variables | Extensive (`GEMINI_*`) | Limited (`CLAUDE_*`) | Gemini more flexible |
| **Approval Modes** | Default (safe) | ✅ | ✅ | Both support |
| | Auto-edit | ✅ | ✅ | Both support |
| | YOLO (auto-all) | ✅ | ✅ | Both support |
| | Per-tool permissions | ✅ | ✅ | Both support |
| | Keyboard shortcuts | ✅ (Ctrl+Y, Shift+Tab) | ✅ | Both have shortcuts |
| **Session Management** | Auto-save sessions | ✅ (v0.20.0+) | ✅ | Both automatic |
| | Resume by index | ✅ | ✅ | Both support |
| | Resume by UUID | ✅ | ✅ | Both support |
| | Session browser | ✅ (`/resume`) | ✅ | Both interactive |
| | Session retention policies | ✅ | ❌ | Gemini has auto-cleanup |
| | Session storage location | `~/.gemini/tmp/<project>/chats/` | `~/.claude/sessions/<project>/` | Different paths |
| **Extension System** | Extension directory | `~/.gemini/extensions/` | Plugin system (`.claude-plugin/`) | Different architectures |
| | Install from GitHub | ✅ | ✅ | Both support |
| | Local development linking | ✅ | ✅ | Both support |
| | Auto-update extensions | ✅ | ❌ | Gemini has `--auto-update` |
| | Extension marketplace | ✅ (geminicli.com/extensions) | ✅ (claude-plugins.dev) | Both have catalogs |
| | Custom commands | ✅ (TOML format) | ✅ (slash commands) | Different formats |
| **MCP Integration** | MCP server support | ✅ | ✅ | Both full support |
| | Per-server tool filtering | ✅ | ✅ | Both support |
| | OAuth discovery | ✅ | ✅ | Both support |
| | CLI MCP management | ✅ (`gemini mcp`) | ✅ (`claude mcp`) | Both have CLI |
| **Hooks System** | Lifecycle hooks | ✅ (12 events) | ✅ (6+ events) | Gemini has more events |
| | BeforeTool / AfterTool | ✅ | ✅ | Both support |
| | Hook migration from other CLI | ✅ (from Claude Code) | ❌ | Gemini can import Claude hooks |
| | Hook management UI | ✅ (`/hooks panel`) | ✅ | Both have UI |
| **Skills System** | Skills architecture | ✅ (experimental) | ✅ (production) | Claude more mature |
| | Skills directory | `extensions/skills/` | `.claude/skills/` | Different structure |
| | Skills format | SKILL.md | SKILL.md | Same format |
| **Context & Memory** | Context files | `GEMINI.md` | `CLAUDE.md` | Same concept, different names |
| | Hierarchical loading | ✅ | ✅ | Both support |
| | Import syntax | `@path/to/file.md` | `@path/to/file.md` | Identical |
| | Max directory discovery | 200 (configurable) | N/A | Gemini has limit |
| **Model Support** | Context window | 1M tokens (Gemini 2.0 Flash) | 200k tokens (Claude 3.5 Sonnet) | Gemini 5x larger |
| | Model aliases | ✅ | ✅ | Both support |
| | Model-specific overrides | ✅ | ✅ | Both support |
| **Pricing** | Free tier | ✅ (1,000 requests/day) | ❌ | Gemini has generous free tier |
| | Subscription required | ❌ (for free tier) | ✅ (Pro/Max/Team/Enterprise) | Claude requires subscription |
| | API-only option | ✅ | ✅ (AWS/Vertex) | Both support |
| **Performance** | Benchmark speed | Slower (1h17m typical) | Faster (avg task completion) | Claude generally faster |
| | Token efficiency | Lower (higher consumption) | Higher (auto-compaction) | Claude more efficient |
| | Code quality | Good (Gemini Pro 2.5) | Excellent (Claude Sonnet 3.5/Opus) | Claude better for coding |
| **Sandbox** | Sandbox modes | Docker, Podman, custom | Docker, custom | Similar |
| | Auto-sandbox with YOLO | ✅ | ✅ | Both enable |
| **Security** | Environment var redaction | ✅ (automatic + custom) | ✅ | Both support |
| | Folder trust system | ✅ | ✅ | Both support |
| | Disable YOLO mode | ✅ | ✅ | Both support |
| **Telemetry** | Local telemetry | ✅ | ❌ | Gemini supports local OTLP |
| | GCP telemetry | ✅ | ❌ | Gemini has GCP integration |
| | Opt-out | ✅ | ✅ | Both allow opt-out |
| **Output Formats** | Text output | ✅ | ✅ | Both support |
| | JSON output | ✅ | ✅ | Both support |
| | Streaming JSON | ✅ | ✅ | Both support |
| **IDE Integration** | VS Code integration | ✅ | ✅ | Both support |
| | IDE mode flag | ✅ | ✅ | Both support |
| **Experimental Features** | JIT context loading | ✅ | ❌ | Gemini has token optimization |
| | Codebase investigator | ✅ | ✅ (different implementation) | Both have codebase analysis |
| | Multi-agent workflows | ✅ | ✅ | Both experimental |

### 10.2 Performance Comparison

**Benchmark Results (10M token test):**

| Metric | Gemini CLI | Claude Code | Winner |
|--------|------------|-------------|--------|
| **Execution Time** | 1h17m (manual nudging) | ~1h (full autonomy) | Claude Code |
| **Cost** | $7.06 (fragmented) | $4.80 (smooth) | Claude Code |
| **Token Efficiency** | Lower (no auto-compaction) | Higher (auto-compaction) | Claude Code |
| **Code Quality** | Good (Gemini Pro 2.5) | Excellent (Claude Sonnet 3.5) | Claude Code |
| **UX Polish** | Decent | Cleaner, smoother | Claude Code |

### 10.3 Context Window Comparison

| Model | Context Window | Advantage |
|-------|----------------|-----------|
| **Gemini 2.0 Flash** | 1M tokens | 5x larger for massive codebases |
| **Claude 3.5 Sonnet** | 200k tokens | Sufficient for most projects |

### 10.4 Pricing Comparison

| Tier | Gemini CLI | Claude Code |
|------|------------|-------------|
| **Free** | 1,000 requests/day (Gemini 2.0 Flash) | ❌ None |
| **Paid** | API usage pricing | $20/month (Pro) to Enterprise |
| **Best For** | Budget-conscious, large context needs | Professional development, code quality |

### 10.5 Customization Comparison

| Feature | Gemini CLI | Claude Code |
|---------|------------|-------------|
| **Project context file** | `GEMINI.md` | `CLAUDE.md` |
| **Inheritance** | Hierarchical (global → project) | Hierarchical (global → project) |
| **Extension/Plugin format** | `gemini-extension.json` | `plugin.json` |
| **Command format** | TOML files | Markdown with frontmatter |
| **Skills format** | SKILL.md (experimental) | SKILL.md (production) |

### 10.6 Integration Capabilities

**MCP Integration:**
- **Gemini CLI:** Cleaner JSON configuration, OAuth discovery, per-server filtering
- **Claude Code:** Similar capabilities, slightly different syntax

**Hooks System:**
- **Gemini CLI:** 12 lifecycle events, migration from Claude Code
- **Claude Code:** 6+ events, production-ready

### 10.7 User Experience

**Gemini CLI:**
- Faster execution for simple tasks
- Sticks to prompt (minimal extra work)
- Great for shell-level tasks
- Output can feel rushed or minimal

**Claude Code:**
- Smarter follow-up questions
- Cleaner UI
- Sometimes builds more than asked
- Better for complex projects

### 10.8 Summary Recommendations

**Use Gemini CLI If:**
- Budget-conscious (free tier attractive)
- Working with massive codebases (1M context window)
- Need extensive customization (4-level config hierarchy)
- Prefer quick, utility-focused tasks
- Want advanced telemetry (local OTLP)

**Use Claude Code If:**
- Code quality is top priority
- Professional development workflow
- Need faster, more autonomous execution
- Want production-ready skills system
- Prefer cleaner UX and polish

**Hybrid Approach:**
- Use Gemini CLI for exploration, prototyping, large context analysis
- Use Claude Code for production development, complex features, code refactoring
- Both support MCP servers, so tools/integrations can be shared

---

## 11. Configuring Gemini CLI to Match Claude Code

### 11.1 Directory Structure Mapping

**Claude Code:**
```
.claude/
├── settings.json
├── CLAUDE.md
├── skills/
│   └── my-skill/
│       └── SKILL.md
├── agents/
│   └── my-agent.md
└── memory/
```

**Gemini CLI Equivalent:**
```
.gemini/
├── settings.json
├── GEMINI.md
└── extensions/
    └── my-extension/
        ├── gemini-extension.json
        ├── GEMINI.md
        ├── skills/
        │   └── my-skill/
        │       └── SKILL.md
        └── commands/
            └── my-command.toml
```

### 11.2 Configuration Alignment

**Create `.gemini/settings.json` to match Claude Code behavior:**

```json
{
  "general": {
    "previewFeatures": true,
    "enablePromptCompletion": true,
    "sessionRetention": {
      "enabled": true,
      "maxAge": "30d",
      "maxCount": 100
    }
  },
  "security": {
    "auth": {
      "selectedType": "oauth-personal"
    },
    "environmentVariableRedaction": {
      "enabled": true
    }
  },
  "tools": {
    "sandbox": true,
    "allowed": ["bash", "write", "edit", "read", "glob"],
    "enableHooks": true
  },
  "hooks": {
    "enabled": true,
    "notifications": true
  },
  "experimental": {
    "enableAgents": true,
    "skills": true,
    "jitContext": true,
    "codebaseInvestigatorSettings": {
      "enabled": true,
      "maxNumTurns": 10,
      "maxTimeMinutes": 3
    }
  },
  "ui": {
    "showLineNumbers": true,
    "hideContextSummary": false,
    "useFullWidth": true
  },
  "context": {
    "fileName": "GEMINI.md",
    "fileFiltering": {
      "respectGitIgnore": true,
      "enableRecursiveFileSearch": true
    }
  }
}
```

### 11.3 Context File Migration

**Convert `CLAUDE.md` to `GEMINI.md`:**

```bash
# Simple copy if content is generic
cp .claude/CLAUDE.md .gemini/GEMINI.md

# Or use sed for specific transformations
sed 's/Claude Code/Gemini CLI/g' .claude/CLAUDE.md > .gemini/GEMINI.md
```

### 11.4 Hook Migration

**Use built-in migration:**

```bash
gemini
# In session:
/hooks migrate
```

**Manual migration example:**

**Claude Code Hook (`.claude/hooks/pre-commit.sh`):**
```bash
#!/bin/bash
# Prevent committing secrets
if grep -r "API_KEY\|SECRET" "$CLAUDE_PROJECT_DIR"; then
  echo "ERROR: Found secrets in project"
  exit 1
fi
```

**Gemini CLI Hook (`.gemini/settings.json`):**
```json
{
  "hooks": {
    "BeforeTool": [
      {
        "name": "prevent-commit-secrets",
        "command": "bash",
        "args": ["-c", "grep -r 'API_KEY|SECRET' \"$GEMINI_PROJECT_DIR\""],
        "targetTools": ["bash"],
        "exit": {
          "0": "block",
          "1": "allow"
        }
      }
    ]
  }
}
```

### 11.5 MCP Server Configuration Alignment

**Claude Code (`.claude/settings.json`):**
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

**Gemini CLI (`.gemini/settings.json`):**
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

**Identical configuration!**

### 11.6 Approval Mode Parity

**Match Claude Code approval behavior:**

```bash
# Claude Code: auto-edit mode
claude --auto-edit

# Gemini CLI equivalent
gemini --approval-mode=auto_edit

# Claude Code: YOLO mode
claude --yolo

# Gemini CLI equivalent
gemini --yolo
# OR
gemini --approval-mode=yolo
```

### 11.7 Skills System Alignment

**Enable experimental skills:**

```json
{
  "experimental": {
    "skills": true
  }
}
```

**Create skills directory:**

```bash
mkdir -p .gemini/extensions/my-skills/skills/lead-scoring
```

**Skill format (identical to Claude Code):**

```markdown
---
name: lead-scoring
description: Score leads using ML model
---

# Lead Scoring Skill

Use the trained ML model to score leads based on:
- Budget alignment
- Location preference
- Engagement level
```

### 11.8 Environment Variables

**Map Claude Code env vars to Gemini:**

```bash
# .env
# Claude Code variables
CLAUDE_API_KEY=sk-ant-...
CLAUDE_PROJECT_DIR=/path/to/project

# Gemini CLI equivalents
GEMINI_API_KEY=AIzaSy...
GEMINI_PROJECT_DIR=/path/to/project  # Set in hook migration

# Shared variables (both support)
GITHUB_TOKEN=ghp_...
DATABASE_URL=postgresql://...
```

### 11.9 Session Management Parity

**Both support identical session commands:**

```bash
# List sessions
claude --list-sessions
gemini --list-sessions

# Resume latest
claude --resume
gemini --resume

# Resume by index
claude --resume 5
gemini --resume 5

# Delete session
claude --delete-session 5
gemini --delete-session 5
```

### 11.10 Complete Migration Checklist

**Step-by-Step Migration:**

1. **Install Gemini CLI:**
   ```bash
   npm install -g @google/generative-ai-cli
   # OR
   brew install gemini-cli
   ```

2. **Create project config:**
   ```bash
   mkdir -p .gemini
   cp .claude/settings.json .gemini/settings.json
   ```

3. **Migrate context file:**
   ```bash
   sed 's/Claude Code/Gemini CLI/g' .claude/CLAUDE.md > .gemini/GEMINI.md
   ```

4. **Migrate hooks:**
   ```bash
   gemini
   # In session: /hooks migrate
   ```

5. **Update environment variables:**
   ```bash
   # Add to .env
   echo "GEMINI_API_KEY=$YOUR_API_KEY" >> .env
   ```

6. **Test approval modes:**
   ```bash
   gemini --approval-mode=auto_edit
   ```

7. **Verify MCP servers:**
   ```bash
   gemini mcp list
   ```

8. **Enable experimental features:**
   ```json
   {
     "experimental": {
       "skills": true,
       "enableAgents": true,
       "jitContext": true
     }
   }
   ```

9. **Test session resumption:**
   ```bash
   gemini --list-sessions
   gemini --resume latest
   ```

10. **Verify skills (if using):**
    ```bash
    # Ensure skills directory exists
    ls .gemini/extensions/*/skills/
    ```

---

## 12. Key Differences & Limitations

### 12.1 Gemini CLI Limitations vs Claude Code

1. **Code Quality:** Gemini Pro 2.5 is weaker than Claude Sonnet 3.5/Opus for programming
2. **Token Efficiency:** No auto-compaction (higher costs)
3. **Autonomy:** Requires more manual nudging
4. **Skills Maturity:** Experimental vs production-ready
5. **UX Polish:** Less refined interface

### 12.2 Gemini CLI Advantages vs Claude Code

1. **Free Tier:** 1,000 requests/day (Gemini 2.0 Flash)
2. **Context Window:** 1M tokens (5x larger)
3. **Telemetry:** Local OTLP support
4. **Configuration:** 4-level hierarchy (more flexible)
5. **Hook Events:** 12 lifecycle events (vs 6+)

### 12.3 Feature Parity Status

| Feature | Parity Status | Notes |
|---------|---------------|-------|
| **Configuration Files** | ✅ Complete | JSON format, hierarchical loading |
| **Approval Modes** | ✅ Complete | Same modes, different names |
| **Session Management** | ✅ Complete | Identical capabilities |
| **MCP Integration** | ✅ Complete | Same protocol, similar config |
| **Hooks System** | ⚠️ Partial | More events, but different syntax |
| **Skills System** | ⚠️ Experimental | Same format, less mature |
| **Extension System** | ⚠️ Different | Similar capabilities, different architecture |
| **Context Files** | ✅ Complete | Identical import syntax |

---

## 13. Best Practices

### 13.1 Hybrid Workflow

**Recommended Approach:**

1. **Use Gemini CLI for:**
   - Initial exploration (free tier)
   - Large codebase analysis (1M context)
   - Quick scripts and utilities
   - Prototyping ideas

2. **Use Claude Code for:**
   - Production feature development
   - Complex refactoring
   - Code quality requirements
   - Final implementation

3. **Share configuration:**
   - Identical MCP servers in both
   - Sync `.env` files
   - Mirror approval mode settings

### 13.2 Configuration Organization

**Recommended structure:**

```
project/
├── .env                          # Shared environment variables
├── .gitignore                    # Ignore both .claude/ and .gemini/
├── .claude/
│   ├── settings.json
│   └── CLAUDE.md
├── .gemini/
│   ├── settings.json
│   └── GEMINI.md
└── mcp-servers/                  # Shared MCP server definitions
    └── github-config.json
```

### 13.3 Security Best Practices

1. **Never commit secrets:**
   ```bash
   # .gitignore
   .env
   .claude/settings.local.json
   .gemini/settings.local.json
   **/oauth_creds.json
   ```

2. **Use environment variable redaction:**
   ```json
   {
     "security": {
       "environmentVariableRedaction": {
         "enabled": true,
         "blocked": ["INTERNAL_API_KEY"]
       }
     }
   }
   ```

3. **Enable sandbox for YOLO:**
   ```json
   {
     "tools": {
       "sandbox": true
     },
     "security": {
       "disableYoloMode": false
     }
   }
   ```

### 13.4 Performance Optimization

**Gemini CLI optimizations:**

```json
{
  "model": {
    "compressionThreshold": 0.7,
    "summarizeToolOutput": {
      "bash": 5000,
      "read": 20000
    }
  },
  "experimental": {
    "jitContext": true
  },
  "tools": {
    "useRipgrep": true,
    "enableToolOutputTruncation": true,
    "truncateToolOutputThreshold": 2000000
  }
}
```

---

## 14. Troubleshooting

### 14.1 Common Issues

**Issue:** Sessions not saving

**Solution:**
```json
{
  "general": {
    "checkpointing": {
      "enabled": true
    }
  }
}
```

**Issue:** MCP server not connecting

**Solution:**
```bash
# Check MCP server status
gemini mcp list

# Test connection
gemini --debug
```

**Issue:** Hooks not running

**Solution:**
```json
{
  "tools": {
    "enableHooks": true
  },
  "hooks": {
    "enabled": true
  }
}
```

**Issue:** Context file not loading

**Solution:**
```bash
# Verify file exists
ls .gemini/GEMINI.md

# Check discovery settings
{
  "context": {
    "fileName": "GEMINI.md",
    "fileFiltering": {
      "enableRecursiveFileSearch": true
    }
  }
}
```

### 14.2 Debug Mode

```bash
gemini --debug
```

Enables:
- Verbose logging
- Keystroke logging (if `debugKeystrokeLogging: true`)
- Network request details
- Tool execution traces

---

## 15. Resources

### 15.1 Official Documentation

- **Gemini CLI Docs:** https://geminicli.com/docs/
- **GitHub Repository:** https://github.com/google-gemini/gemini-cli
- **Configuration Guide:** https://geminicli.com/docs/get-started/configuration/
- **Extension Marketplace:** https://geminicli.com/extensions/

### 15.2 Community Resources

- **Community Tips:** https://github.com/addyosmani/gemini-cli-tips
- **Extension Examples:** https://github.com/philschmid/gemini-cli-extension
- **Tutorial Series:** https://medium.com/google-cloud/gemini-cli-tutorial-series

### 15.3 Comparison Articles

- **Gemini CLI vs Claude Code (Composio):** https://composio.dev/blog/gemini-cli-vs-claude-code-the-better-coding-agent
- **Milvus Comparison:** https://milvus.io/blog/claude-code-vs-gemini-cli-which-ones-the-real-dev-co-pilot.md
- **Shipyard Analysis:** https://shipyard.build/blog/claude-code-vs-gemini-cli/

---

## 16. Conclusion

### 16.1 Summary of Findings

Gemini CLI offers **comprehensive configuration capabilities** with:
- 4-level hierarchical configuration system
- 3 approval modes with per-tool granularity
- Automatic session persistence with retention policies
- Mature extension system with marketplace
- Full MCP integration with OAuth discovery
- 12 lifecycle hooks for customization
- Experimental skills system

**Configuration parity with Claude Code:** ~90% feature-complete

### 16.2 Recommended Configuration for EnterpriseHub

**Create `.gemini/settings.json`:**

```json
{
  "general": {
    "previewFeatures": true,
    "enablePromptCompletion": true,
    "sessionRetention": {
      "enabled": true,
      "maxAge": "30d",
      "maxCount": 100
    }
  },
  "security": {
    "auth": {
      "selectedType": "oauth-personal"
    },
    "environmentVariableRedaction": {
      "enabled": true,
      "allowed": ["GHL_LOCATION_ID"],
      "blocked": ["GHL_WEBHOOK_SECRET", "OPENAI_API_KEY"]
    }
  },
  "tools": {
    "sandbox": true,
    "allowed": ["bash", "write", "edit", "read", "glob"],
    "enableHooks": true,
    "useRipgrep": true
  },
  "hooks": {
    "enabled": true,
    "notifications": true,
    "BeforeTool": [
      {
        "name": "prevent-commit-secrets",
        "command": "bash",
        "args": ["-c", "grep -r 'API_KEY\\|SECRET\\|TOKEN' . || exit 1"],
        "targetTools": ["bash"],
        "exit": {
          "0": "block",
          "1": "allow"
        }
      }
    ]
  },
  "experimental": {
    "enableAgents": true,
    "skills": true,
    "jitContext": true,
    "codebaseInvestigatorSettings": {
      "enabled": true,
      "maxNumTurns": 10,
      "maxTimeMinutes": 3,
      "thinkingBudget": 8192
    }
  },
  "model": {
    "name": "gemini-2.5-flash",
    "compressionThreshold": 0.7,
    "summarizeToolOutput": {
      "bash": 5000,
      "read": 20000
    }
  },
  "ui": {
    "theme": "dark",
    "showLineNumbers": true,
    "hideContextSummary": false,
    "useFullWidth": true,
    "footer": {
      "hideContextPercentage": false
    }
  },
  "context": {
    "fileName": "GEMINI.md",
    "includeDirectories": ["ghl_real_estate_ai/"],
    "fileFiltering": {
      "respectGitIgnore": true,
      "enableRecursiveFileSearch": true
    }
  },
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      },
      "includeTools": ["create_issue", "list_repos", "create_pr"],
      "trust": false
    }
  }
}
```

**Create `.gemini/GEMINI.md`:**

```markdown
# EnterpriseHub GHL Real Estate AI

@CLAUDE.md

## Gemini CLI-Specific Configuration

- Use `gemini-2.5-flash` for rapid development
- Switch to `gemini-2.5-pro` for complex ML tasks
- Leverage 1M context window for full codebase analysis

## Project Structure

Main codebase: `ghl_real_estate_ai/`
Tests: `ghl_real_estate_ai/tests/`
Streamlit: `ghl_real_estate_ai/streamlit_demo/`

## Key Commands

- `/memory refresh` - Reload project context
- `/resume` - Continue previous session
- Ctrl+Y - Toggle YOLO mode for rapid prototyping
```

### 16.3 Next Steps

1. **Create `.gemini/` directory** in EnterpriseHub project
2. **Copy recommended configuration** above
3. **Test approval modes** with `--approval-mode=auto_edit`
4. **Verify session persistence** with `--list-sessions`
5. **Enable experimental features** for skills system
6. **Configure MCP servers** for GitHub integration
7. **Set up hooks** for pre-commit secret detection

---

**End of Document**

**Research Completed:** January 9, 2026
**Total Configuration Options Documented:** 150+
**CLI Flags Documented:** 25+
**Environment Variables Documented:** 30+
**MCP Integration:** Full coverage
**Feature Parity:** ~90% with Claude Code

**Sources:**
- [Gemini CLI Configuration](https://geminicli.com/docs/get-started/configuration/)
- [Gemini CLI GitHub Repository](https://github.com/google-gemini/gemini-cli)
- [MCP Server Documentation](https://geminicli.com/docs/tools/mcp-server/)
- [Session Management Guide](https://geminicli.com/docs/cli/session-management/)
- [Hooks System Documentation](https://geminicli.com/docs/hooks/)
- [Extensions Guide](https://geminicli.com/docs/extensions/)
- [Gemini CLI vs Claude Code Comparison](https://composio.dev/blog/gemini-cli-vs-claude-code-the-better-coding-agent)
- [Medium Tutorial Series](https://medium.com/google-cloud/gemini-cli-tutorial-series-part-3-configuration-settings-via-settings-json-and-env-files-669c6ab6fd44)
