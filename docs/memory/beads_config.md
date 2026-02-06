# Beads Configuration & Usage

Beads is a Git-backed issue tracker for AI agents. It provides a structured memory of tasks, dependencies, and project state that persists across sessions.

## Project Structure
- `.beads/`: Contains the issue database (JSONL format).
- Memory is versioned alongside code, allowing for seamless session transitions for AI agents.

## Global Integration
Beads is initialized at the repository root to provide a unified task memory for all sub-components:
- Advanced RAG System
- Enterprise UI
- Backend Services
- Agent Coordination Layer

## Agent Usage
AI agents should read `.beads/issues.jsonl` to:
1. Understand the current project state.
2. Identify blocked or ready tasks.
3. Record progress and new discoveries.

## Claude Code Integration
- **17 domain-agnostic agents** in `.claude/agents/` — all have "Project-Specific Guidance" sections
- **5 MCP servers**: memory, postgres, redis, stripe, playwright
- **11 GitHub Actions workflows** (consolidated from 17)
- Agents adapt to project domain via `CLAUDE.md` and `.claude/reference/` files

### Adding an Issue
Issues should be added as JSON lines to `.beads/issues.jsonl`.
```json
{"id": "SHORT_HASH", "title": "Task title", "status": "todo", "created_at": "ISO_TIMESTAMP", "tags": ["tag1"], "description": "Details"}
```
