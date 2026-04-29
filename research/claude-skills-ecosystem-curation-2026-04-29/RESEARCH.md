# Research: Claude Skills, Agents & Plugins Worth Adopting (2025–2026)

**Generated**: 2026-04-29  
**Pipeline**: Perplexity → Gemini → Grok → ChatGPT → Claude → NotebookLM  
**Steps completed**: 1 (Perplexity), 2 (Gemini), 3 (Grok — fallback), 4 (ChatGPT), 5 (Claude synthesis), 6 (NotebookLM — auth expired, questions queued)

---

## Bottom Line Up Front

For someone at 35 skills + 33 agents + 24 MCPs, the highest-leverage actions are:

1. **Set `export SLASH_COMMAND_TOOL_CHAR_BUDGET=30000` now** — silent skill drops are happening
2. **Audit and prune before adding** — you are at or past the useful density ceiling
3. **Install 10 external items** (see Phase 2 below)
4. **Build 4 custom skills** that don't exist in the community (see Phase 3 below)

---

## Key Findings

### The Ecosystem (Perplexity)
- Launched October 2025; claude-plugins.dev indexes 6,000+ skills; tonsofskills.com has 2,807 skills / 423 plugins
- SKILL.md is now an open standard (agentskills.io) — adopted by Codex CLI, Gemini CLI, GitHub Copilot, Cursor, Windsurf
- Three-level lazy loading: frontmatter (~100 tokens, always); body (~750 tokens, on-demand); referenced files (~700 tokens, on reference)
- anthropics/skills repo: `document-skills` (docx/pptx/xlsx/pdf) + `example-skills` bundles — official, Apache 2.0

### Architecture (Gemini)
- **Skill+Agent Hybrid is the only pattern that scales to 50+ skills** — isolates context per subagent
- Monolithic SKILL.md breaks at 5,000 tokens (compaction truncation)
- Router pattern hallucinating file paths at 15-20 skills
- Plugin+MCP = 8.5/10 difficulty: zombie processes, port conflicts, env mismatches
- **claude-mem's genius**: Progressive Disclosure (~40 tokens/entry always loaded, 1,000 tokens on relevance hit) — dodges compaction limits entirely

### What's Overbuilt (Grok/contrarian)
- 6,000+ skills claim is vanity — ~4,400 are low quality at 73% failure rate
- Skills fatigue is real — adding more past ~35 is likely counterproductive without first pruning
- Only 5 genuinely non-native additions: planning-with-files, claude-mem, social-media-skills, evals-skills, obsidian-skills
- Migration burden: 2-4 hrs per major CC version for a 50+ skill library
- Context compaction API changed Q1 2026 — planning-with-files needs PostToolUse hook

### Pruning Framework (ChatGPT)
| Layer | Current | Target |
|-------|---------|--------|
| Skills | 35 | 20-25 |
| Agents | 33 | 15-20 |
| MCP Servers | 24 | 18-20 |

**Rule**: Static context → CLAUDE.md. Procedures invoked occasionally → Skill. Isolated/parallel tasks → Skill+Agent Hybrid.

---

## Action Plan

### Phase 0 — Immediate

```bash
export SLASH_COMMAND_TOOL_CHAR_BUDGET=30000
echo 'export SLASH_COMMAND_TOOL_CHAR_BUDGET=30000' >> ~/.zshrc
```

Also add to `EnterpriseHub/.claude/CLAUDE.md`:
> "Always require DROP/ALTER column operations to include a corresponding rollback migration"

### Phase 1 — Prune First (before installing anything)

1. Run `/skills` — audit all 35 for pre-Feb 2026 description language (rewrite to "Command when…" or remove)
2. Remove skills that duplicate native CC v2.x (basic commit, basic PR review)
3. Identify MCPs with 0 tool calls this month → remove
4. Collapse agent duplicates → target ≤20 agents

### Phase 2 — Install

| Priority | Item | Install Command | Track |
|----------|------|-----------------|-------|
| P0 | pyright-lsp | `/plugin install pyright-lsp@claude-plugins-official` | Work |
| P0 | typescript-lsp | `/plugin install typescript-lsp@claude-plugins-official` | Work |
| P0 | kepano/obsidian-skills | `git clone https://github.com/kepano/obsidian-skills` | Personal |
| P0 | hamelsmu/evals-skills | `git clone https://github.com/hamelsmu/evals-skills` | Work |
| P1 | blacktwist/social-media-skills | `git clone https://github.com/blacktwist/social-media-skills` | Personal |
| P1 | disler/claude-code-hooks-mastery | `git clone https://github.com/disler/claude-code-hooks-mastery && npm install` | Work |
| P1 | planning-with-files | `npx skills add https://github.com/othmanadi/planning-with-files` | Work |
| P1 | claude-mem | `git clone https://github.com/thedotmack/claude-mem` + pip install | Work |
| P2 | addyosmani/web-quality-skills | `npx skills add addyosmani/web-quality-skills` | Work |
| P2 | sentry (official) | `/plugin install sentry@claude-plugins-official` | Work |
| P2 | obra/superpowers | `/plugin marketplace add obra/superpowers-marketplace` (project-scoped only) | Work |

**Important caveats:**
- `claude-mem`: implement TTL/superseded_by schema on day 1; verify it doesn't conflict with existing `memory` MCP
- `planning-with-files`: needs PostToolUse hook for Q1 2026 compaction changes (disler/hooks-mastery makes this easier — install it first)
- `obra/superpowers`: project-scoped only, never global; too rigid for hotfixes/debugging

### Phase 3 — Build Custom Skills

All 4 specs are in `04-chatgpt.md`. Build in this order:

| Priority | Skill | What It Does |
|----------|-------|-------------|
| P0 | `alembic-migration-safety` | Intercepts DROP/ALTER, requires rollback script + local `alembic upgrade head` test |
| P0 | `api-contract-enforcer` | Detects FastAPI→Next.js OpenAPI drift, generates updated TypeScript types |
| P1 | `incident-triage` | Parses uvicorn logs, classifies P0/P1/P2, searches incident history |
| P1 | `saas-orchestrator` | Validates state consistency across GHL + Stripe + local DB |

### Skip List

| Item | Reason |
|------|--------|
| commit-commands (official) | Native CC v2.x |
| pr-review-toolkit (official) | Native CC v2.x |
| hashicorp/agent-skills | Native Terraform knowledge |
| dead-code-detector | grep + native |
| confidence-check | Low value |
| temporal-reasoning-sleuth | Low signal |
| humanize-writing | Low value + overlap |

---

## Source Files

| File | Model | Role |
|------|-------|------|
| `01-perplexity.md` | Perplexity Deep Research | Web landscape + citations |
| `02-gemini.md` | Gemini 2.5 Pro | Deep technical analysis |
| `03-grok.md` | Claude as Grok-role (fallback) | Contrarian challenge |
| `04-chatgpt.md` | ChatGPT | Structured matrix + SKILL.md specs |
| `05-claude-synthesis.md` | Claude | Claim reconciliation + synthesis |
| `06-notebooklm.md` | NotebookLM | Auth expired — questions queued |
| `RECOMMENDATIONS.csv` | — | Sortable shortlist |

---

## NotebookLM

Auth expired. Run `notebooklm login` then ask these 3 questions (in `06-notebooklm.md`):
1. Which installed skills overlap with new recommended installs?
2. Should claude-mem coexist with or replace the existing memory MCP?
3. Any prior project evidence on skill invocation frequency or conflicts?
