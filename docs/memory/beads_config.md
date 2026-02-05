# Beads Configuration & Usage

Beads is a Git-backed issue tracker for AI agents. It provides a structured memory of tasks, dependencies, and project state that persists across sessions.

## Project Structure
- `.beads/`: Contains the issue database (JSONL format).
- Memory is versioned alongside code, allowing for seamless session transitions for AI agents.

## Global Integration
Beads is initialized at the repository root to provide a unified task memory for all sub-components:
- Advanced RAG System
- Jorge Bot Ecosystem
- Enterprise UI
- GHL Real Estate AI

## Agent Usage
AI agents (like Antigravity) should read `.beads/issues.jsonl` to:
1. Understand the current project state.
2. Identify blocked or ready tasks.
3. Record progress and new discoveries.

### Adding an Issue
Issues should be added as JSON lines to `.beads/issues.jsonl`.
```json
{"id": "SHORT_HASH", "title": "Task title", "status": "todo", "created_at": "ISO_TIMESTAMP", "tags": ["tag1"], "description": "Details"}
```
