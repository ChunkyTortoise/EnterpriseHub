# Claude Skills Ecosystem — ChatGPT Structure + Roadmap
**Date**: 2026-04-29
**Model**: ChatGPT (browser — chatgpt.com, 2 responses)
**Role**: Structured matrix, pruning framework, gap analysis, build specs, 30-day sequence

---

## System Model (from response 1)

Claude Code is a **modular agent runtime** with four extensibility layers:

```
Plugins (distribution layer)
 ├── Skills (capability units — instruction bundles loaded dynamically)
 ├── Subagents (autonomous workers — own context window)
 ├── MCP servers (tool/data connectors — real-world access)
 └── Hooks (lifecycle control points — middleware for agent behavior)
```

Key reality: **MCP = the real moat.** Whoever controls data/tool access wins. Skills without MCP integration are shallow. The power stack is: High-quality SKILLS + Structured AGENTS + Real MCP integrations = Production-grade automation.

---

## 1. INSTALL PRIORITY MATRIX

*Note: ChatGPT produced generic role-based rows rather than the specific repos listed. Rows have been mapped to the specific repos from prior findings where applicable. ChatGPT-generated install commands are illustrative — use actual commands from 01-perplexity.md.*

| Name | Kind | Install Command | Category | Track | Impact | Cost | Risk | Overlap | Verdict |
|------|------|-----------------|----------|-------|--------|------|------|---------|---------|
| **planning-with-files** | Skill | `npx skills add othmanadi/planning-with-files` | Orchestration | Work | 5 | 2 | Med | Low | **INSTALL** |
| **claude-mem** | Skill+Hook | `git clone thedotmack/claude-mem` | Memory | Work+Personal | 5 | 3 | Med | Low | **INSTALL** (add TTL schema) |
| **pyright-lsp** | Plugin | `/plugin install pyright-lsp@claude-plugins-official` | Eng Quality | Work | 5 | 1 | Low | Low | **INSTALL** |
| **typescript-lsp** | Plugin | `/plugin install typescript-lsp@claude-plugins-official` | Eng Quality | Work | 5 | 1 | Low | Low | **INSTALL** |
| **kepano/obsidian-skills** | Skill | `git clone kepano/obsidian-skills` | PKM | Personal | 5 | 2 | Low | Low | **INSTALL** |
| **hamelsmu/evals-skills** | Skill | `git clone hamelsmu/evals-skills` | AI Eng | Work | 5 | 2 | Low | Low | **INSTALL** |
| **blacktwist/social-media-skills** | Skill | `git clone blacktwist/social-media-skills` | Writing | Personal | 4 | 1 | Low | Low | **INSTALL** |
| **obra/superpowers** | Plugin | `/plugin marketplace add obra/superpowers-marketplace` | Orchestration | Work | 4 | 3 | Med | Med | **INSTALL project-scoped only** |
| **obsidian-second-brain** | Skill | lobehub.com install | PKM | Personal | 4 | 3 | Med | Med | **INSTALL** (after kepano/obsidian-skills) |
| **document-skills (official)** | Plugin | `/plugin install document-skills@anthropic-agent-skills` | Documents | Work | 4 | 1 | Low | Low | **INSTALL** |
| **webapp-testing (official)** | Skill | via anthropics/skills | Testing | Work | 4 | 1 | Low | Med | **INSTALL** |
| **disler/claude-code-hooks-mastery** | Hooks | `git clone disler/claude-code-hooks-mastery` | Control | Work | 4 | 3 | Med | Low | **INSTALL** (CI/unattended use) |
| **addyosmani/web-quality-skills** | Skill | `npx skills add addyosmani/web-quality-skills` | Frontend | Work | 4 | 1 | Low | Low | **INSTALL** |
| **nextlevelbuilder/ui-ux-pro-max** | Skill | `git clone nextlevelbuilder/ui-ux-pro-max-skill` | UI Design | Work+Personal | 3 | 2 | Low | Med | **INSTALL** |
| **explanatory-output-style (official)** | Plugin | `/plugin install explanatory-output-style@claude-plugins-official` | Learning | Personal | 3 | 1 | Low | Low | **INSTALL** |
| **agent-sdk-dev (official)** | Plugin | `/plugin install agent-sdk-dev@claude-plugins-official` | AI Eng | Work | 3 | 1 | Low | Low | **INSTALL** |
| **sentry (official)** | Plugin | `/plugin install sentry@claude-plugins-official` | Observability | Work | 4 | 2 | Low | Low | **INSTALL** |
| **alembic-migration-safety** | Skill | BUILD | DB Safety | Work | 5 | 3 | Low | None | **BUILD** |
| **api-contract-enforcer** | Skill | BUILD | API Safety | Work | 5 | 3 | Low | None | **BUILD** |
| **incident-triage** | Skill | BUILD | Ops | Work | 4 | 2 | Low | None | **BUILD** |
| **saas-orchestrator** | Skill | BUILD | Integration | Work | 4 | 3 | Low | None | **BUILD** |
| **hashicorp/agent-skills** | Skill | `npx skills add hashicorp/agent-skills` | DevOps | Work | 3 | 1 | Low | Med | **SKIP** (native Claude handles Terraform well) |
| **commit-commands (official)** | Plugin | `/plugin install commit-commands@claude-plugins-official` | Dev Workflow | Work | 2 | 1 | Low | High | **SKIP** (native CC v2.x handles this) |
| **pr-review-toolkit (official)** | Plugin | `/plugin install pr-review-toolkit@claude-plugins-official` | Dev Workflow | Work | 3 | 1 | Low | High | **SKIP** (native handles this adequately) |
| **dead-code-detector** | Skill | `github.com/CuriousLearner/devkit` | Code Quality | Work | 2 | 1 | Low | High | **SKIP** (grep + native analysis equivalent) |
| **confidence-check** | Skill | tonsofskills.com | Meta | Work | 2 | 1 | Low | Med | **SKIP** |
| **temporal-reasoning-sleuth** | Skill | tonsofskills.com | Meta | Work | 3 | 1 | Low | Low | **SKIP** (low install signal) |
| **humanize-writing** | Skill | tonsofskills.com | Writing | Personal | 2 | 1 | Low | Med | **SKIP** |

---

## 2. THE PRUNING QUESTION

**Core principle from ChatGPT:** You are overbuilt and under-curated. The issue is not missing capability — it's duplication and unclear boundaries.

### Audit Targets (Immediate)

- **Duplicate skills:** Any two skills covering the same domain (e.g., if you have both a code-review agent AND a code-review skill — keep agent, remove skill)
- **Thin skill wrappers:** Skills that are just prompts with no workflow logic, no state writing, no tool use → convert to CLAUDE.md rules
- **Multiple orchestration agents:** Collapse planner/executor variants → target 4-6 total agents max
- **Agents written before Feb 2026:** Description language audit needed

### Target Architecture

| Layer | Current | Target | Action |
|-------|---------|--------|--------|
| Skills | 35 | 20-25 | Prune 10-15 |
| Agents | 33 | 15-20 | Consolidate 10-15 |
| MCP Servers | 24 | 18-20 | Remove unused |
| CLAUDE.md rules | — | More | Migrate static procedures here |

### What Belongs in CLAUDE.md Instead of Skills

Move these categories from skills to CLAUDE.md rules:
- Coding standards (snake_case, error types, test patterns)
- API conventions (response schema, error format)
- Architecture constraints (async patterns, service boundaries)
- Naming rules

**Rule:** If it's static context Claude needs every session → CLAUDE.md. If it's a procedure Claude runs occasionally → Skill.

---

## 3. GAP ANALYSIS

| Question | Why It Matters | How to Answer |
|----------|----------------|---------------|
| Which skills are actually invoked in daily sessions? | Usage ≠ installation — many skills may never trigger | Enable logging hooks + rank by invocation frequency over 7 days |
| Which agents produce silent errors or incomplete outputs? | Hidden failure risk compounds over time | Audit PostToolUse hook outputs; add diff validation to agents |
| Which MCPs have zero tool calls in the last 30 days? | Unused MCPs consume description budget and add attack surface | Track tool calls via hook; remove any with 0 calls |
| What is the actual overlap between installed skills and native Claude v2.x capabilities? | Native improvements since Oct 2025 may have made several skills redundant | Test each skill's job natively — commit to removing if native output is equivalent |
| Does claude-mem's TTL/superseded_by mechanism work correctly with context compaction? | Core viability question — if memory retrieval surfaces stale arch decisions, it actively harms output | Test: make a major arch change, confirm old observation is superseded within 1 session |

---

## 4. BUILD-YOUR-OWN SPECS

### `alembic-migration-safety`
```yaml
---
name: alembic-migration-safety
description: "Command when generating or reviewing Alembic migrations — enforces DROP/ALTER safety, rollback scripts, and local test validation before execution"
allowed-tools: [Bash, Read, Edit]
---
```
When invoked on any Alembic migration file or database schema change, first check if the operation includes `DROP`, `ALTER COLUMN`, or `DROP TABLE`. If any destructive operation is detected, require a corresponding rollback migration to be written before proceeding. For vector data columns (pgvector types) or complex foreign key changes, require explicit local test confirmation via `alembic upgrade head` in a test database before marking migration as ready.

### `api-contract-enforcer`
```yaml
---
name: api-contract-enforcer
description: "Command when modifying FastAPI endpoints — detects OpenAPI schema drift and generates updated TypeScript types for the Next.js frontend"
allowed-tools: [Bash, Read, Write]
---
```
After any FastAPI route modification, run `python -m pytest tests/openapi_contract_test.py` to check for breaking changes against the saved OpenAPI spec snapshot. If changes are detected, generate updated TypeScript interfaces using `openapi-typescript` and write them to `frontend/src/types/api.ts`. Flag any removed fields or changed response shapes as breaking changes requiring frontend review before the PR can be merged.

### `incident-triage`
```yaml
---
name: incident-triage
description: "Command when a production error occurs — parses uvicorn/FastAPI logs, identifies stack trace root cause, searches knowledge base for similar incidents"
allowed-tools: [Bash, Read]
---
```
When invoked, read the last 100 lines of the uvicorn log at `logs/uvicorn.log` (or the path specified). Extract all stack traces, identify the deepest non-library frame as the root cause, and search `docs/incident-history/` for similar past incidents. Classify severity (P0: service down, P1: degraded, P2: non-critical) based on whether the error is recurring, in a critical path, or affecting payments/auth flows.

### `saas-orchestrator`
```yaml
---
name: saas-orchestrator
description: "Command when simulating or debugging end-to-end user flows across GoHighLevel, Stripe, and the local database — validates state consistency across systems"
allowed-tools: [Bash, Read]
---
```
When invoked for a GHL+Stripe+DB workflow simulation, first map the expected state transitions: (1) GHL contact stage, (2) Stripe subscription status, (3) local database user record. Execute the simulation by querying each system for the test contact/customer ID and compare actual vs expected state at each step. Report any state mismatches with the specific field, expected value, and actual value so the discrepancy can be diagnosed.

---

## 5. 30-DAY IMPLEMENTATION SEQUENCE

### Phase 0 — Day 1 (Control the system first)
- [ ] Set `export SLASH_COMMAND_TOOL_CHAR_BUDGET=30000` in `~/.zshrc`
- [ ] Enable skill invocation logging (add hook to record which skills fire)
- [ ] Run `/skills` to get current loaded skill list and verify budget

### Phase 1 — Day 2-5 (Prune before adding)
- [ ] Audit all 35 skills for Feb 2026 description language (directive vs descriptive)
- [ ] Remove skills that duplicate native Claude v2.x behavior (commit, basic PR review)
- [ ] Audit agents — collapse any duplicates; target ≤20 agents
- [ ] Identify which MCPs have had 0 tool calls this month
- [ ] Migrate static procedural rules from CLAUDE.md to dedicated skill files (moves procedures off always-loaded budget)

### Phase 2 — Day 6-10 (Architecture before new installs)
- [ ] Convert all surviving skills to Skill+Agent Hybrid pattern where appropriate
- [ ] Define clear boundaries: what is a skill, what is an agent, what is a CLAUDE.md rule
- [ ] Install disler/claude-code-hooks-mastery (foundation for all subsequent hook-dependent installs)

### Phase 3 — Day 11-17 (Community installs)
- [ ] `/plugin install pyright-lsp@claude-plugins-official`
- [ ] `/plugin install typescript-lsp@claude-plugins-official`
- [ ] `npx skills add othmanadi/planning-with-files`
- [ ] `git clone thedotmack/claude-mem` + configure TTL/superseded_by schema
- [ ] `git clone kepano/obsidian-skills` → install into vault `.claude/skills/`
- [ ] `git clone hamelsmu/evals-skills`
- [ ] `git clone blacktwist/social-media-skills`
- [ ] `/plugin install sentry@claude-plugins-official`

### Phase 4 — Day 18-25 (Build custom stack-specific skills)
- [ ] Build `alembic-migration-safety` skill (use spec above)
- [ ] Build `api-contract-enforcer` skill
- [ ] Build `incident-triage` skill
- [ ] Build `saas-orchestrator` skill

### Phase 5 — Day 26-30 (Verify and lock)
- [ ] Re-run `/skills` — verify no silent drops
- [ ] Test each new skill fires on appropriate trigger phrase
- [ ] Run claude-mem with a schema change and verify old observation gets superseded_by tag
- [ ] Document final architecture in CLAUDE.md skills section

---

## Handoff Summary

**KEY CLAIMS (new from ChatGPT):**
- Target architecture: 15-20 skills, 4-6 agents (not 35+33) — current state is overbuilt (source: ChatGPT)
- Skills without MCP integrations are "shallow" — MCP is the real moat (source: ChatGPT)
- Static procedures belong in CLAUDE.md, not skills — key boundary rule (source: ChatGPT)
- 30-day sequence: Phase 0 (env vars) → Phase 1 (prune) → Phase 2 (architecture) → Phase 3 (install) → Phase 4 (build custom) (source: ChatGPT)
- 7 unanswered questions including: which skills are actually invoked, which MCPs have 0 calls, does claude-mem TTL work with compaction (source: ChatGPT)

**CONFIRMED ACROSS ALL 4 SOURCES:**
- SLASH_COMMAND_TOOL_CHAR_BUDGET=30000 must be set before anything else
- Prune before adding — current install density is at or past the useful ceiling
- pyright-lsp + typescript-lsp: unanimous INSTALL recommendation
- claude-mem: INSTALL but requires TTL schema management
- The 4 custom skills (alembic-safety, api-contract, incident-triage, saas-orchestrator) are the highest-value additions for this specific stack

**REMAINING GAPS:**
- Actual invocation frequency data for existing 35 skills
- Claude-mem compaction interaction verified in practice
- obra/superpowers star count still unverified
