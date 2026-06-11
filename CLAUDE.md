# EnterpriseHub: top-level CLAUDE.md / AGENTS.md

Read order on session start:
1. `~/.claude/CLAUDE.md` (global)
2. `.claude/CLAUDE.md` (this repo's per-project file with stack, architecture, deploy info)
3. This file (shared between Claude Code and Codex agents via the AGENTS.md symlink)

## Mistakes (agent failure log)

<!-- One line per corrected bad behavior. Format: YYYY-MM-DD: what went wrong -> fix applied -->
<!-- Agents: add a new entry whenever you correct a repeated mistake in this repo -->
2026-06-02: Integration tests were masking 4xx client errors as 500s -> checked response.status_code before raising HTTPError; affected endpoints returned correct 4xx to callers (PR #90)

