# Claude Skills Ecosystem — NotebookLM
**Date**: 2026-04-29
**Status**: COMPLETED — authenticated via Playwright persistent profile
**Notebook**: Claude Skills Ecosystem Research 2026-04-29 (ID: 56c4ba0a-b943-45a5-953b-ae7413fd34e3)
**Sources ingested**: 02-gemini, 03-grok, 05-claude-synthesis, Memory MCP Architecture Context

---

## Q1 — Overlap Detection

### Clear Replacements (remove the old skill)

| New Skill | Replace | Reason |
|-----------|---------|--------|
| `alembic-migration-safety` | `postgres-migration` | Native Alembic knowledge + safety gap fills both needs. Keeping postgres-migration is redundant and less safe. |
| `web-quality-audit` | `visual-audit` | Specificity to technical standards (Core Web Vitals, Lighthouse metrics) beats generic visual audit. |
| `write-judge-prompt` | `prompt-engineer` | write-judge-prompt is specialized evaluation procedural knowledge; keep `claude-prompt-engineer` for general work. |

### Coexist (both serve different purposes)

| New Skills | Existing Skill | Reason |
|------------|----------------|--------|
| `evaluate-rag`, `eval-audit`, `validate-evaluator`, `build-review-interface`, `generate-synthetic-data`, `write-judge-prompt`, `error-analysis` | `pgvector-rag` | evals-skills cover evaluation pipelines (non-native procedural); pgvector-rag covers RAG implementation. Different lifecycle stages. |
| `social-media-*` skills (13 from blacktwist) | Any existing writing skills | Claude generates generic content without BlackTwist voice-preserving skills. Coexist. |

### Existing Overlaps to Prune (unrelated to new installs)

- `prompt-engineer` vs `claude-prompt-engineer` → keep `claude-prompt-engineer` (Anthropic best practices, post-Feb-2026 language)
- `second-opinion` vs `compare` → evaluate which sees more use; likely collapse to one

---

## Q2 — Memory Conflict

**Verdict: REPLACE the existing graph-based `memory` MCP server with `claude-mem`. Do NOT coexist.**

### Specific Risks of Running Both Simultaneously

1. **Tool name collision**: Both expose memory-style tools (e.g., `search_memory`). Claude faces ambiguous routing — unclear which database to query or update.
2. **Double context injection**: Graph-based server loads entity index + claude-mem loads ~40 token/entry index at every session start. Compounds compaction problem; could push past the 30,000-char budget where skills are silently dropped.
3. **Observation drift + contradiction**: Two databases can diverge. Claude receives contradictory "memories" from different points in time → hallucinations.
4. **Latency persists**: Graph traversal latency stays even if claude-mem handles primary memory. No benefit from keeping both.

### Migration Requirements

Before installing claude-mem:
1. Remove the existing `memory` MCP from the 24-server inventory (`.mcp.json`)
2. Implement TTL/superseded_by tags in claude-mem schema from day one
3. Export any valuable observations from the existing memory graph before removal

---

## Q3 — Skill Invocation History

### Evidence of Silent Failures and Quality Issues

**Skills that cannot trigger (empty descriptions):**
- `hospitality-resume`, `large-context-review`, `second-opinion-checkpoint`, `realtime-check`

**Skills that under-trigger (pre-Feb 2026 description language):**
Any skill using "helps with X" or "assists with Y" rather than "Command when X must happen"

**Known architectural failure thresholds:**
- Router pattern breaks at 15-20 skills → Claude hallucinates file paths
- Monolithic SKILL.md breaks at 5,000 tokens (auto-compaction truncation)
- SLASH_COMMAND_TOOL_CHAR_BUDGET: skills silently dropped when total loaded > 30,000 chars

**Existing overlaps causing routing confusion:**
- `prompt-engineer` vs `claude-prompt-engineer` (confirmed)
- `second-opinion` vs `compare` (confirmed)
- `memory` MCP vs claude-mem (if both installed: tool name collision)

**Native redundancies (skills Claude no longer needs):**
- FastAPI, Postgres, Next.js, Redis, Stripe, Alembic: Claude handles natively since v2.x
- Basic commit messages: native
- Basic PR description: native

### Pruning Priority Order

1. Remove skills with empty descriptions (4 candidates)
2. Audit all skills for pre-Feb 2026 description language → rewrite to "Command when..." or remove
3. Replace `postgres-migration` with `alembic-migration-safety`
4. Replace `visual-audit` with `web-quality-audit`
5. Replace `prompt-engineer` with `write-judge-prompt` (keep `claude-prompt-engineer`)
6. Evaluate `second-opinion` vs `compare` → collapse to one
7. Remove graph-based `memory` MCP before installing `claude-mem`

---

## Action Summary

| Decision | Action |
|----------|--------|
| claude-mem vs memory MCP | **Replace** memory MCP with claude-mem (don't coexist) |
| postgres-migration | **Remove** (alembic-migration-safety covers this better) |
| visual-audit | **Remove** (web-quality-audit is more specific) |
| prompt-engineer | **Remove** (keep claude-prompt-engineer + write-judge-prompt) |
| hospitality-resume, large-context-review, second-opinion-checkpoint, realtime-check | **Fix descriptions or remove** |
| second-opinion vs compare | **Evaluate usage, collapse to one** |
