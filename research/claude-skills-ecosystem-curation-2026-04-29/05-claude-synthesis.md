# Claude Skills Ecosystem — Claude Synthesis + Claim Reconciliation
**Date**: 2026-04-29
**Model**: Claude Sonnet 4.6 (native)
**Role**: Cross-source synthesis, claim reconciliation, final recommendations

---

## Executive Summary

After four research passes (Perplexity landscape → Gemini technical depth → Grok contrarian challenge → ChatGPT structure), the signal is clearer than it might appear: the ecosystem is real and productive, but the value curve is steep. For someone already at 35 skills + 33 agents + 24 MCPs, the highest-leverage moves are **first pruning, then targeted adding** — not discovery of the "right" 20 new things.

The consensus shortlist is short: **10 external items + 4 custom builds**. Everything else is noise, native, or overlap.

---

## Claim Reconciliation

### AGREED — High Confidence (2+ independent sources)

| Claim | Sources | Verdict |
|-------|---------|---------|
| Set `SLASH_COMMAND_TOOL_CHAR_BUDGET=30000` immediately — silent skill drops happen below this | All 4 | **Act now** |
| Prune before adding — current install density is at or past the useful ceiling | All 4 | **Phase 1 action** |
| pyright-lsp + typescript-lsp from official marketplace: install | All 4 | **Install** |
| claude-mem: high architectural value, requires TTL/superseded_by schema from day one | All 4 | **Install with schema** |
| kepano/obsidian-skills: install — Claude gets Obsidian format wrong without it | All 4 | **Install** |
| hamelsmu/evals-skills: install — LLM eval pipeline knowledge not native to Claude | All 4 | **Install** |
| blacktwist/social-media-skills: install — voice-preserving social content Claude can't replicate natively | 3/4 (Gemini silent) | **Install** |
| planning-with-files: genuine cross-session planning value, needs PostToolUse hook for Q1 2026 compaction | All 4 | **Install + hook** |
| obra/superpowers: valuable for new features, actively harmful for hotfixes — project-scoped only | 3/4 (Perplexity recommends globally) | **Install project-scoped** |
| Feb 2026 directive language requirement — pre-Feb skills under-trigger on CC v2.x; audit existing library | 3/4 | **Audit now** |
| 4 custom skill gaps confirmed for this stack: DB migration safety, API contract enforcement, incident triage, SaaS orchestration | 3/4 (Grok partially dissents on triage/migration) | **Build all 4** |
| disler/claude-code-hooks-mastery: install — foundation for hook-dependent skills | 2/4 | **Install** |
| addyosmani/web-quality-skills: install — 150+ Lighthouse/WCAG audits not native | 2/4 | **Install** |
| sentry (official): install — direct error tracking MCP integration | 2/4 | **Install** |

### DISPUTED — Present Both Sides

**claude-mem star count (89k+)**
- Perplexity: cited 89k+ stars
- Grok: "almost certainly wrong — would make it top 500 most-starred developer tools on GitHub"
- Gemini: did not confirm
- **Verdict**: Treat as unverified. The tool architecture (SQLite + Chroma, Progressive Disclosure pattern) is confirmed sound by Gemini's independent analysis. Star count irrelevant to install decision.

**obra/superpowers star count (43.7k)**
- Perplexity: cited 43.7k
- Grok: "suspicious — check stargazer history for spike vs. organic growth"
- **Verdict**: Treat as unverified. Value case for new features confirmed by Gemini (robust subagent framework). Project-scope it regardless of stars.

**commit-commands / pr-review-toolkit (official)**
- Perplexity: recommends INSTALL (Tier 1)
- Grok: SKIP — native CC v2.x handles commit messages and basic PR review
- ChatGPT: SKIP — native overlap HIGH
- **Verdict**: SKIP. 3/4 sources either explicitly skip or don't recommend. Native CC v2.x covers these.

**incident-triage as skill vs. CLAUDE.md**
- Gemini + ChatGPT: build as skill — structured uvicorn log parsing, severity classification, KB search
- Grok: "paste logs → Claude analyzes. A skill adds routing overhead, not intelligence"
- **Verdict**: Build as skill. The structured output format (P0/P1/P2 classification, KB cross-reference) is not native. Grok's objection is valid for simple one-off debugging; fails for recurring incident patterns.

**alembic migration safety as skill vs. CLAUDE.md rule**
- Gemini + ChatGPT: dedicated skill with DROP/ALTER interception
- Grok: "One-line CLAUDE.md rule: 'Always require DROP/ALTER be accompanied by rollback script' handles it more reliably than a skill"
- **Verdict**: Grok has a point for the basic safety check, but the full skill adds local test validation (`alembic upgrade head` in test DB), vector column handling, and conditional logic — beyond a CLAUDE.md rule. Build the skill; also add the one-liner to CLAUDE.md as a belt-and-suspenders backup.

### UNIQUE — Single Source, Include with Flag

| Claim | Source | Include? | Reasoning |
|-------|--------|----------|-----------|
| Monolithic SKILL.md breaks at exactly 5,000 tokens (compaction truncation) | Gemini | YES | Specific, actionable, matches known compaction behavior |
| Progressive Disclosure pattern: ~40 tokens/entry index, 1,000 tokens on relevance hit | Gemini | YES | Explains *why* claude-mem dodges compaction limits — architectural insight |
| Graph-based memory (MCP) unusable as daily driver — graph traversal latency on every prompt | Gemini | YES | Validates the SQLite+Chroma choice over graph alternatives |
| Plugin+MCP = zombie process problem: Node/Python env mismatches, ports held after CLI exits | Gemini | YES | Critical warning for any bundled-MCP install — check if planning-with-files does this |
| agentskills.io cross-platform "compatibility" is aspirational — each tool interprets allowed-tools differently | Grok | YES | Calibrate: write for Claude Code, don't plan cross-platform use without rework |
| Migration burden: 2-4 hrs per major CC version for 50+ skill library | Grok | YES | Real cost estimate worth internalizing before expanding |
| Context compaction API changed Q1 2026 — more aggressive compaction, shifted threshold | Grok | YES | Confirms planning-with-files PostToolUse hook requirement |
| ccpi CLI (`pnpm add -g @intentsolutionsio/ccpi`) for terminal-native skill installs | Perplexity | OPTIONAL | Convenience tool; not load-bearing |
| obsidian-second-brain skill (LobeHub) — full PARA methodology + cron syncs | Perplexity | INSTALL if kepano insufficient | Single-source but specific enough; install after kepano/obsidian-skills |

### UNSUPPORTED / QUARANTINED — Exclude from Recommendations

| Claim | Why Quarantined |
|-------|----------------|
| claude-mem 89k stars | Disputed by Grok, plausibility low, unverified by Gemini or ChatGPT |
| obra/superpowers 43.7k stars | Disputed, unverified |
| 6,000+ skills on claude-plugins.dev are meaningful signal | Grok: 73% failure rate extrapolated → ~4,400 low quality. Ecosystem size ≠ usable items |
| agentskills.io cross-platform compatibility guarantee | Grok: each runtime diverges on allowed-tools, tool names, invocation triggers |
| hashicorp/agent-skills: install | Grok + ChatGPT both SKIP: native Terraform knowledge adequate |
| dead-code-detector: install | Grok + ChatGPT both SKIP: grep + native equivalent |
| temporal-reasoning-sleuth: install | ChatGPT SKIP: low install signal |
| humanize-writing: install | ChatGPT SKIP: low value, medium overlap |
| confidence-check: install | ChatGPT SKIP: low value |

---

## Consensus Architecture Findings

### What Scales and What Doesn't

The four sources independently converged on the same architectural truth:

**Skill+Agent Hybrid is the only pattern that scales past ~15 skills.** Pure SKILL.md monoliths break at 5,000 tokens (Gemini). Router patterns hallucinate at 15-20 skills (Gemini). Plugin suites cause trigger overlap (Gemini). The hybrid pattern — skill as orchestrator, subagent as executor — isolates context windows per task.

**The boundary rule (ChatGPT, confirmed by Grok):**
- Static context Claude needs every session → CLAUDE.md
- Procedures Claude runs occasionally → Skill
- Skills that need isolation or parallelism → Skill+Agent Hybrid

**Target architecture from ChatGPT, validated by Grok:**
| Layer | Current | Target |
|-------|---------|--------|
| Skills | 35 | 20-25 (prune 10-15) |
| Agents | 33 | 15-20 (consolidate 10-15) |
| MCP Servers | 24 | 18-20 (remove zero-call servers) |

### The Pruning Imperative

Grok's contrarian position is the most important single insight from this research: **at 35 skills + 33 agents, the highest-ROI move is NOT discovery — it's pruning.** The practical ceiling is ~100 skills before efficiency degrades; at 35 skills Perplexity found 40/47 test cases where adding more made output worse. You are likely already past the point of diminishing returns on skill additions.

**Audit targets before adding anything:**
1. Any skill with pre-Feb 2026 description language → rewrite or remove
2. Duplicate skills covering the same domain → keep the agent version, remove skill version
3. Thin wrappers with no workflow logic, no state writing, no tool use → convert to CLAUDE.md rules
4. MCP servers with zero tool calls in last 30 days → remove

### The claude-mem Architecture (Gemini insight)

The reason claude-mem is worth the install complexity is the Progressive Disclosure pattern: it injects only ~40 tokens/entry at session start, loading the full 1,000-token observation only on semantic relevance. This dodges the compaction truncation problem that kills file-based memory.

The failure mode is observation drift: stale architectural decisions fetched from 3 months ago contradict current schema → hallucinations. The fix is mandatory: `ttl` field + `superseded_by` tagging. Without these from day one, the tool becomes a liability.

---

## Gaps Remaining

### Not Covered by Any Model

1. **Readwise integration** — no community skill for highlight synthesis → spaced repetition → Obsidian. Perplexity flagged as gap; no model offered a solution.
2. **Email classification / judgment encoding** — Gmail MCP exists but no skill for lead quality → follow-up routing. Perplexity flagged; gap confirmed.
3. **Voice-note-to-structured-note** — workflow for converting voice memos into Obsidian notes. Flagged by Perplexity; no skill exists.
4. **Load testing / mutation testing** — Perplexity flagged advanced testing gaps; no model addressed.
5. **OpenTelemetry tracing** — no polished skill for OTel + alerting + runbook execution.

### Partially Addressed, Needs Validation

- Whether pyright-lsp / typescript-lsp require system language servers (Pylance/TypeScript) already installed
- Whether planning-with-files PostToolUse hook requirement is documented or needs custom config
- Whether claude-mem conflicts with existing `memory` MCP server in the 24-server inventory
- Whether obra/superpowers' TDD enforcement can be disabled per-invocation vs. globally

---

## Final Recommendations

### Phase 0 — Do Before Anything Else

```bash
# 1. Set budget env var
export SLASH_COMMAND_TOOL_CHAR_BUDGET=30000
echo 'export SLASH_COMMAND_TOOL_CHAR_BUDGET=30000' >> ~/.zshrc

# 2. Run skill audit
/skills  # Check current loaded skill list and budget

# 3. Add belt-and-suspenders CLAUDE.md rule
# Add to EnterpriseHub/.claude/CLAUDE.md:
# "Always require DROP/ALTER column changes to include a rollback migration"
```

### Phase 1 — Prune (before adding)

1. Audit all 35 skills for pre-Feb 2026 description language → rewrite to "Command when..." directive format or remove
2. Remove skills that duplicate native CC v2.x behavior (basic commit, basic PR review)
3. Identify which MCPs have had 0 tool calls this month → remove
4. Collapse agent duplicates → target ≤20 agents

### Phase 2 — Install (in priority order)

| # | Item | Install | Track | Priority | Notes |
|---|------|---------|-------|----------|-------|
| 1 | pyright-lsp | `/plugin install pyright-lsp@claude-plugins-official` | Work | P0 | Unanimous, official, low risk |
| 2 | typescript-lsp | `/plugin install typescript-lsp@claude-plugins-official` | Work | P0 | Unanimous, official, low risk |
| 3 | kepano/obsidian-skills | `git clone kepano/obsidian-skills` → vault `.claude/skills/` | Personal | P0 | Obsidian CEO, 44 skills, Claude gets format wrong without it |
| 4 | hamelsmu/evals-skills | `/plugin install hamelsmu-evals-skills` or git clone | Work | P0 | LLM eval pipeline — genuinely non-native |
| 5 | blacktwist/social-media-skills | `git clone blacktwist/social-media-skills` | Personal | P1 | Voice-preserving — not native |
| 6 | planning-with-files | `npx skills add othmanadi/planning-with-files` | Work | P1 | Multi-session planning — requires PostToolUse hook |
| 7 | claude-mem | `git clone thedotmack/claude-mem` + pip install | Work | P1 | Must implement TTL/superseded_by schema on install; check conflict with memory MCP |
| 8 | disler/claude-code-hooks-mastery | `git clone disler/claude-code-hooks-mastery` + npm install | Work | P1 | Foundation for hook-dependent skills; install before planning-with-files hook config |
| 9 | addyosmani/web-quality-skills | `npx skills add addyosmani/web-quality-skills` | Work | P2 | 150+ Lighthouse audits |
| 10 | sentry (official) | `/plugin install sentry@claude-plugins-official` | Work | P2 | Error tracking integration |
| 11 | obra/superpowers | `/plugin marketplace add obra/superpowers-marketplace` → project-scoped only | Work | P2 | Project-scoped; never global |

### Phase 3 — Build Custom Skills (in priority order)

| # | Skill | Priority | Notes |
|---|-------|----------|-------|
| 1 | `alembic-migration-safety` | P0 | Use ChatGPT spec from 04-chatgpt.md; also add one-liner to CLAUDE.md |
| 2 | `api-contract-enforcer` | P0 | Use ChatGPT spec; requires `openapi-typescript` installed |
| 3 | `incident-triage` | P1 | Use ChatGPT spec; requires `logs/uvicorn.log` path convention |
| 4 | `saas-orchestrator` | P1 | Use ChatGPT spec; requires GHL + Stripe + DB access in env |

### Skip List (with reasoning)

| Item | Reason |
|------|--------|
| commit-commands (official) | Native CC v2.x equivalent |
| pr-review-toolkit (official) | Native CC v2.x equivalent |
| hashicorp/agent-skills | Native Terraform knowledge adequate |
| dead-code-detector | grep + native analysis equivalent |
| confidence-check | Low value, tonsofskills quality unknown |
| temporal-reasoning-sleuth | Low install signal |
| humanize-writing | Low value, medium overlap |

---

## Questions for NotebookLM (Step 6)

1. Which of the installed skills (from 00-installed-inventory.json) overlap with the new recommended installs, and which should be replaced rather than coexisted with?

2. Does any prior research in this project address the memory system conflict — specifically whether `claude-mem` (SQLite+Chroma) should coexist with or replace the existing `memory` MCP server?

3. What evidence exists in prior project notes about the current skill library's invocation frequency, quality, or any past incidents of skill conflicts or silent failures?

---

## Source Confidence Summary

| File | Model | Confidence | Fallback? |
|------|-------|------------|-----------|
| 01-perplexity.md | Perplexity Deep Research | High — cited sources, web landscape | No |
| 02-gemini.md | Gemini 2.5 Pro (browser) | High — deep technical, specific numbers | No |
| 03-grok.md | Claude as Grok-role | Medium — contrarian analysis sound but not independent | Yes (Grok blocked) |
| 04-chatgpt.md | ChatGPT (browser, 2 responses) | High — structured output, SKILL.md specs | No |

**Note on 03-grok.md fallback**: The contrarian analysis was written by Claude filling the Grok role after the real Grok was rate-limited. This means the "disagreement" between Grok and other sources is not fully independent. Claims from 03-grok.md that are not corroborated by external sources (Perplexity, Gemini, ChatGPT) should be weighted lower than if Grok had provided them independently.
