# Gemini CLI Maximization Guide: Advanced Workflows & Agentic Systems

This guide centralizes strategies for getting the most out of Gemini CLI, leveraging Skills, MCP, Hooks, and structured workflows.

## 1. NotebookLM Integration
A dedicated notebook has been created for research and orchestration:
- **Notebook ID:** `98baeac8-6091-4808-9c34-963e37e534c0`
- **Title:** Gemini CLI Mastery: Advanced Workflows & Agentic Systems

## 2. Agent Skills
Skills are specialized, on-demand capabilities stored in `.gemini/skills/` or `~/.gemini/skills/`.

### How to use:
Gemini automatically discovers skills. Use the `activate_skill` tool to pull in specialized expertise.

### How to create:
- **Auto:** Ask Gemini: "create a new skill called 'my-skill-name'"
- **Manual:** Create a directory in `.gemini/skills/` with a `SKILL.md` file.
  - `SKILL.md` must have YAML frontmatter with `name` and `description`.

## 3. Model Context Protocol (MCP)
The following MCP servers are configured in `gemini.toml`:
- `context-compressor`: Specialized for managing large contexts.
- `prompt-library`: Access to high-quality reusable prompts.
- `enterprise-hub`: Direct integration with this project's core logic.
- `notebooklm`: Direct query and sync capabilities for NotebookLM.
- `obsidian`: Full-text search and note management in your vault.

## 4. Hooks (Workflow Orchestration)
Hooks allow executing custom scripts at specific lifecycle points. Configure these in `.gemini/settings.json`.

### Available Events:
- **`BeforeTool`**: Executes before a tool is called. Use for security auditing or input validation.
- **`AfterModel`**: Executes after the model responds. Use for logging or reacting to tool outputs.
- **`AfterAgent`**: Executes after the entire turn is complete. Use for final validation or cleanup.

### Example Configuration:
```json
{
  "hooks": {
    "BeforeTool": [
      {
        "matcher": "write_file",
        "hooks": [
          {
            "name": "audit",
            "type": "command",
            "command": "node .gemini/hooks/audit.js"
          }
        ]
      }
    ]
  }
}
```

## 5. Structured Workflows (Conductor)
The **Conductor** workflow (located in `.gemini/conductor/`) defines the development lifecycle for EnterpriseHub:
1. **Track Creation**: `/conductor:newTrack`
2. **Spec Review**: Mandatory security/performance audit of `spec.md`.
3. **Plan Approval**: Must include explicit testing tasks.
4. **Implementation**: Persistent progress tracking via `/conductor:implement`.
5. **Validation**: Mandatory `pytest` and `ruff check`.

## 7. Recent Enhancements (Feb 15, 2026)
- **Security Guardrails**: `BeforeTool` hook integrated with `.gemini/hooks/security_scan.js` for real-time destructive command and PII protection.
- **Autonomous Orchestration**: Maestro extension enabled with `experimental.enableAgents` and `general.autonomous_execution` for parallel sub-agent workflows.
- **Plan Mode**: `experimental.plan` enabled for safe, read-only research phases.
- **Lead Intelligence Skill**: Ported advanced 28-feature lead scoring logic from Claude Code to Gemini CLI as a native skill.
- **Token Optimization**: `experimental.toolOutputMasking` enabled to reduce context bloat from large tool responses.
