# Claude Skills Ecosystem — Perplexity Web Research
**Date**: 2026-04-29
**Model**: Perplexity AI (Deep Research — manual paste)
**Role**: Broad landscape with citations

---

# Claude Code Skills, Agents & Plugins: Complete Ecosystem Guide (2025–2026)

> **Audience:** Senior AI engineer with an existing production stack (Python/FastAPI, Next.js, Streamlit, Postgres, Redis, GoHighLevel, Stripe) and a large portfolio of installed skills and MCP servers. All skills listed in the user's already-installed set are excluded from recommendations.
>
> **Structure:** (1) Current State, (2) Key Players & Registries, (3) Technical Formats Deep Dive, (4) Production Case Studies, (5) Failure Modes & Gotchas, (6) Coverage Gaps, (7) Future Trajectory, (8) Curated New-Install Recommendations.

---

## 1. Current State of the Ecosystem (2025–2026)

### Launch and Explosion

Anthropic officially launched Agent Skills for Claude Code in **October 2025**. The system was described as "one of the most significant updates to Claude Code" and was supported from day one across Claude.ai, Claude Code, the Claude Agent SDK, and the Claude Developer Platform. The ecosystem exploded almost immediately: by early 2026, community members counted thousands of publicly available skills, with one registry (claude-plugins.dev) indexing over **6,000+ public skills** within weeks of launch. The tonsofskills.com marketplace currently indexes **2,807 skills across 423 plugins**.

A major architectural upgrade occurred in early 2026, informally called **"Skills 2.0"** by the community. The shift moved skills from saved prompts to full **executable workflow packages** — skills can now bundle instructions, scripts, templates, and reference materials that Claude runs via bash. The Skills launch was followed in February–March 2026 by Claude Cowork plugin expansion (with private enterprise plugin marketplaces announced on February 24, 2026).

### Official vs. Community

- **Anthropic's official skills** live at github.com/anthropics/skills — **120k stars, 13.8k forks** as of April 2026. The repo contains two main plugin bundles: `document-skills` (docx, pptx, xlsx, pdf) and `example-skills` (all open Apache 2.0).
- **The official Claude Code plugin marketplace** (`claude-plugins-official`) is auto-available in every Claude Code session. Run `/plugin` → Discover tab, or view the catalog at `claude.com/plugins`.
- **Community registries** include tonsofskills.com, claude-plugins.dev, buildwithclaude.com/marketplaces, claudemarketplaces.com, mcpmarket.com, and aimcp.info.
- **Anthropic's Claude Marketplace** (enterprise layer) launched in March 2026 in limited preview, consolidating enterprise spend across partner tools.

### The Agent Skills Open Standard

SKILL.md is no longer just a Claude Code format — it became an **open standard** called "Agent Skills," documented at agentskills.io. As of April 2026, the following tools support the SKILL.md format: **Claude Code, Codex CLI (OpenAI), Gemini CLI (Google), GitHub Copilot (VS Code), Cursor, Windsurf, Cline, and OpenCode**. Skills built following the core spec are largely portable across agents with minimal modification.

---

## 2. Key Players & Registries

### Official Anthropic

| Resource | URL | Stars | Contents | Install |
|----------|-----|-------|----------|---------|
| anthropics/skills | github.com/anthropics/skills | 120k | document-skills (docx/pptx/xlsx/pdf), example-skills (skill-creator, frontend-design, mcp-builder, claude-api, webapp-testing) | `/plugin marketplace add anthropics/skills` then `/plugin install document-skills@anthropic-agent-skills` |
| Official marketplace | claude.com/plugins | — | Code intelligence LSPs, external integrations (github, gitlab, atlassian, linear, figma, vercel, firebase, supabase, slack, sentry), dev workflow plugins (commit-commands, pr-review-toolkit, agent-sdk-dev, plugin-dev), output styles | `/plugin install <name>@claude-plugins-official` |

The official `claude-api` skill bundles up-to-date reference material for building on the Anthropic API across 8 programming languages using progressive disclosure — only the docs relevant to your language and task load.

### Community Superstars

| Repo | Stars | Description | Install |
|------|-------|-------------|---------|
| obra/superpowers | 43.7k | Full agentic dev lifecycle: brainstorm → plan → TDD → code review. Enforced, not optional. | `/plugin marketplace add obra/superpowers-marketplace` then `/plugin install superpowers@superpowers-marketplace` |
| hesreallyhim/awesome-claude-code | ~28k | Master curated directory of all skills, hooks, slash commands, agents, plugins | Browse/reference |
| thedotmack/claude-mem | 89k+ | Persistent cross-session memory via SQLite + Chroma vector DB; hooks-based capture/compress/inject | `git clone` + pip install |
| OthmanAdi/planning-with-files | 13.4k | Manus-style file-based task planning (task_plan.md, findings.md, progress.md) across sessions | `npx skills add https://github.com/othmanadi/planning-with-files` |
| addyosmani/web-quality-skills | 496 | 150+ Lighthouse audits encoded: performance, Core Web Vitals, WCAG 2.1 accessibility, SEO | `npx skills add addyosmani/web-quality-skills` |
| kepano/obsidian-skills | ~7k | 44 skills for Obsidian vault management, built by Obsidian CEO Steph Ango | `git clone` + copy to vault `.claude/skills/` |
| nextlevelbuilder/ui-ux-pro-max-skill | ~16k | 50+ UI styles, 97 color palettes, 57 font pairings, auto-generates design system | git clone → copy skill |
| disler/claude-code-hooks-mastery | 1.4k | 13 lifecycle hooks for deterministic AI control: before/after plan, file write, execute | `git clone` + npm install |
| hamelsmu/evals-skills | — | 7 skills for LLM evals: error-analysis, synthetic-data, judge-prompt, validate-evaluator, evaluate-rag, build-review-interface | `/plugin install hamelsmu-evals-skills` or git clone |
| jeremylongshore/claude-code-plugins-plus-skills | 1.7k | 423 plugins, 2,807 skills, 177 agents; backed by ccpi CLI | `/plugin marketplace add jeremylongshore/claude-code-plugins` |
| wshobson/agents | — | 44 production-ready subagents: RESTful API design, GraphQL schemas, backend arch, React dev | Copy `.md` files to `.claude/agents/` |
| wshobson/commands | — | Slash commands for multi-agent orchestration | Copy to `.claude/commands/` |
| hashicorp/agent-skills | 303 | Terraform code generation, testing, module refactoring, HCP Stacks, provider development | `npx skills add hashicorp/agent-skills` |
| blacktwist/social-media-skills | — | 13 skills for social content: post-writer, thread-writer, hook-writer, content-calendar, voice-preserving | git clone |
| BehiSecc/awesome-claude-skills | — | Curated list spanning PKM, git, security, docs, research | Browse/reference |

### Notable Aggregators / Indexes

- **tonsofskills.com** — searchable index of 2,807 skills; also has `ccpi` CLI for terminal-native install (`pnpm add -g @intentsolutionsio/ccpi`)
- **claude-plugins.dev** — 6,000+ skills indexed from public GitHub; includes stars and download tracking
- **buildwithclaude.com/marketplaces** — directory of community plugin marketplaces
- **claudelog.com** — community blog covering plugin announcements and new releases
- **aimcp.info** — MCP and skills dual-index
- **agentskills.io** — official open standard documentation and cross-platform compatibility listings
- **VoltAgent/awesome-agent-skills** — 1,000+ agent skills from official dev teams and community, cross-platform
- **GitHub topics**: `claude-skill`, `claude-code-plugin`, `agent-skills`, `claude-code`

---

## 3. Technical Formats Deep Dive

### 3.1 SKILL.md — The Core Format

Every skill is a directory with a mandatory `SKILL.md` file.

**YAML Frontmatter:**
```yaml
---
name: my-skill-name           # Required. Lowercase-hyphenated. Must match folder name.
description: "Use when..."    # Required. One sentence. THE routing label Claude reads.
when_to_use: "..."            # Optional. Explicit trigger conditions.
argument-hint: "<target>"     # Optional. Placeholder text shown in slash command.
allowed-tools: [Bash, Read]   # Optional. Whitelist of tools the skill may invoke.
disable-model-invocation: false # Optional.
user-invocable: true          # Optional.
model: "claude-opus-4-5"      # Optional. Override default model.
effort: high                  # Optional. low/medium/high for extended thinking.
---
```

**Three-level loading system:**
1. **Level 1**: YAML frontmatter — always loaded at session start (~100 tokens per skill, name + description only)
2. **Level 2**: SKILL.md body — loaded on-demand when skill is relevant/invoked (~750 tokens avg)
3. **Level 3**: Referenced files within skill folder — loaded only when body references them (~700 tokens per file avg)

**Storage locations (four levels):**
- `~/.claude/skills/<name>/SKILL.md` — personal, all projects
- `.claude/skills/<name>/SKILL.md` — project-specific
- `<plugin>/skills/<name>/SKILL.md` — plugin-scoped
- Enterprise managed settings — org-wide

### 3.2 Agent `.md` Files — Sub-Agents

| Dimension | Skill (SKILL.md) | Sub-Agent (.agent.md) |
|-----------|-----------------|----------------------|
| Purpose | Teaches Claude *how* to do one task | Gives Claude a *persona* with dedicated context |
| Context | Shares main context window (on-demand load) | Own isolated context window |
| Invocation | Auto-detect or `/skill-name` | `@agent-name` or auto-delegation |
| Best for | Repeatable procedures, checklists, reference workflows | Parallel tasks, specialized roles, code review, security |
| File location | `.claude/skills/<name>/SKILL.md` | `.claude/agents/<name>.md` |

### 3.3 Plugin Format — The Packaging Layer

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json          # Manifest (ONLY here)
├── skills/
├── agents/
├── commands/
├── hooks/
├── .mcp.json
└── README.md
```

**Install commands:**
```bash
/plugin marketplace add <owner/repo>   # Register a marketplace
/plugin install <name>@<marketplace>   # Install a plugin
/reload-plugins                        # Activate without restart
```

### 3.4 CLAUDE.md vs SKILL.md Token Economy

CLAUDE.md content costs tokens **every turn** (~2,000 tokens per 100 lines). The same content in SKILL.md costs near-zero until invoked — **cutting baseline context by up to 83%** for procedures. Anthropic recommends keeping CLAUDE.md under 200 lines.

---

## 4. Production Case Studies

- **Cory Zue** (Saas Pegasus): "My mental model for when skills are useful is any low-to-medium complexity task I do regularly. Instead of doing the task I write up the instructions for how I would do the task in a new skill, and then ask the agent to use it."
- **Hamel Husain** (ML engineer): `evals-skills` — full LLM eval pipeline as parallel sub-agents. Spawns sub-agents per diagnostic area, synthesizes to single report.
- **Compound Engineering v2.31.0**: Fixed agent descriptions from 1,400 chars average → 180 chars average, cutting context by 79%.
- **kepano/obsidian-skills**: Obsidian CEO released 44 official skills in January 2026 teaching Claude correct Obsidian formats — .md wikilinks, .base database layer, .canvas spatial maps, defuddle web-to-markdown stripping.
- **LinkedIn voice matching**: Scraped posts → extracted voice rules → built `/linkedin-post` skill that runs 5-question interview before drafting. First drafts sound like the author.
- **session-retro pattern**: End-of-session skill reads git diff + planning files → generates structured retro → writes to Obsidian vault via MCP.

---

## 5. Failure Modes & Gotchas

### Silent Skill Drops — #1 Issue
Hidden **character budget of ~15,000 characters** for all combined skill descriptions. Exceed it and Claude Code silently stops seeing some skills — no error. Fix:
```bash
export SLASH_COMMAND_TOOL_CHAR_BUDGET=30000
```
Keep descriptions to **one single line under 180 characters**.

### Other Failure Modes
- **Broken internal path references**: 73% of 214 audited community skills scored below 60/100; broken paths are the #1 violation
- **Directive vs descriptive language**: Post-Feb 2026 update, descriptions need directive language ("command when X must happen") not descriptive ("helps with X")
- **Case sensitivity**: `SKILL.md` works, `skill.md` does not
- **Context budget exhaustion**: One engineer found 40 of 47 installed skills made output worse by adding tokens. Practical ceiling ~100 skills
- **Hidden MCP dependencies**: Community plugins sometimes reference MCP tools without declaring dependencies
- **Dead repos**: Many October–November 2025 repos already abandoned. Use claude-plugins.dev "last updated" filter

---

## 6. Coverage Gaps

- **Observability/monitoring**: No polished skill integrating OpenTelemetry tracing + alerting + runbook execution; Prometheus/Grafana workflows near-absent
- **Advanced AI/ML engineering**: A/B testing of prompts, systematic regression detection across model versions, cost attribution across multi-agent chains, Red Team skills
- **Personal productivity/PKM**: Readwise integration (no dedicated skill), structured journaling with spaced repetition, learning/reading tracker, weekly review automation, voice-note-to-structured-note
- **Communication automation**: Judgment-encoding skills on top of Gmail/Calendar MCPs (lead quality → follow-up drafting, inbound email classification, cold outreach sequences)
- **Stripe-specific workflows**: No community skill for subscription lifecycle management, failed payment recovery flows, webhook verification
- **Advanced testing**: Load testing, contract testing (Pact), mutation testing, chaos engineering

---

## 7. Future Trajectory

- **Skills 2.0** already deployed — full executable workflow bundles with script support
- **LSP plugins** (pyright-lsp, typescript-lsp) now in official marketplace — give Claude real-time type errors
- **Enterprise private marketplaces** with per-user provisioning via Claude Cowork admin
- **Agent Skills open standard** — adopted by Codex CLI, Gemini CLI, Copilot, Cursor — skill library becomes team-wide AI workflow standard
- **Claude 5 Opus (Q2–Q3 2026)** expected to improve skill routing accuracy and reduce under-triggering

---

## 8. Curated New-Install Recommendations

### Track A: Work / Engineering — Tier 1 (Install Immediately)

| Skill / Plugin | URL | Why |
|----------------|-----|-----|
| planning-with-files | github.com/OthmanAdi/planning-with-files | Persistent file-based task planning across sessions, 13.4k stars |
| obra/superpowers | github.com/obra/superpowers | Enforces brainstorm→plan→TDD→review discipline, 43.7k stars |
| evals-skills | github.com/hamelsmu/evals-skills | 7 LLM eval skills, ML expert-authored |
| commit-commands (official) | `/plugin install commit-commands@claude-plugins-official` | Official git commit/PR workflow |
| pr-review-toolkit (official) | `/plugin install pr-review-toolkit@claude-plugins-official` | Official specialized PR review sub-agents |
| addyosmani/web-quality-skills | github.com/addyosmani/web-quality-skills | 150+ Lighthouse audits, WCAG 2.1, by Addy Osmani |
| pyright-lsp (official) | `/plugin install pyright-lsp@claude-plugins-official` | Real-time Python type errors for FastAPI |
| typescript-lsp (official) | `/plugin install typescript-lsp@claude-plugins-official` | Real-time TypeScript type errors for Next.js |

### Track A: Tier 2 (Install Within a Week)

| Skill / Plugin | URL | Why |
|----------------|-----|-----|
| claude-mem | github.com/thedotmack/claude-mem | 89k+ stars — persistent cross-session memory via SQLite + Chroma |
| hashicorp/agent-skills | github.com/hashicorp/agent-skills | Official Terraform code gen, refactoring, HCP Stacks |
| sentry (official) | `/plugin install sentry@claude-plugins-official` | Error tracking + performance monitoring MCP integration |
| disler/claude-code-hooks-mastery | github.com/disler/claude-code-hooks-mastery | 13 lifecycle hooks for deterministic CI/unattended control |
| dead-code-detector | github.com/CuriousLearner/devkit | Unused imports, vars, funcs, CSS, orphaned types |
| agent-sdk-dev (official) | `/plugin install agent-sdk-dev@claude-plugins-official` | Claude Agent SDK tooling |

### Track B: Personal Productivity — Tier 1

| Skill / Plugin | URL | Why |
|----------------|-----|-----|
| kepano/obsidian-skills | github.com/kepano/obsidian-skills | 44 skills by Obsidian CEO — correct Obsidian formats for Claude |
| obsidian-second-brain | lobehub.com/skills/sennabruno-... | Full PARA methodology + MCP sub-skills + cron syncs |
| blacktwist/social-media-skills | github.com/blacktwist/social-media-skills | 13 social content skills with voice preservation |

### Track B: Tier 2

| Skill / Plugin | URL | Why |
|----------------|-----|-----|
| nextlevelbuilder/ui-ux-pro-max-skill | github.com/nextlevelbuilder/ui-ux-pro-max-skill | Design system generator, 16k stars |
| confidence-check | tonsofskills.com context-engineering-pack | 19.8k installs — response reliability self-assessment |
| temporal-reasoning-sleuth | tonsofskills.com | 32k installs — detects stale training data reasoning |
| explanatory-output-style (official) | `/plugin install explanatory-output-style@claude-plugins-official` | Educational mode — explains why it made choices |
| humanize-writing | tonsofskills.com | 16 installs — rewrites AI-generated text for proposals/outreach |

### Build-Your-Own High-ROI Custom Skills

1. **`ghl-lead-intake`**: GHL contact → lead score → pipeline route → Gmail draft
2. **`stripe-revenue-recovery`**: Failed payment detection + recovery email workflow
3. **`readwise-digest`**: Weekly highlight synthesis → spaced repetition → Obsidian note
4. **`freelance-proposal-writer`**: Job post interview → portfolio context from NotebookLM → proposal
5. **`session-retro`**: git diff + planning files → structured retro → Obsidian vault

---

## Handoff Summary

**KEY CLAIMS:**
- Ecosystem launched Oct 2025; claude-plugins.dev indexes 6,000+ skills; tonsofskills.com has 2,807 skills / 423 plugins (source: Perplexity)
- anthropics/skills repo has 120k stars — document-skills + example-skills bundles. Install via `/plugin marketplace add anthropics/skills` (source: Perplexity)
- SKILL.md is now an open standard (agentskills.io) — cross-compatible with Codex CLI, Gemini CLI, Copilot, Cursor, Windsurf (source: Perplexity)
- Three-level lazy loading: frontmatter (~100 tokens) always; body (~750 tokens) on-demand; referenced files (~700 tokens) on reference (source: Perplexity)
- CRITICAL BUG: character budget of ~15k for all skill descriptions — silent drop. Fix: `export SLASH_COMMAND_TOOL_CHAR_BUDGET=30000` (source: Perplexity)
- obra/superpowers (43.7k stars) — enforced plan-before-code workflow. claude-mem (89k stars) — SQLite+Chroma persistent memory. planning-with-files (13.4k) — file-based multi-session planning (source: Perplexity)
- 73% of 214 audited community skills scored below 60/100 — broken path references are #1 issue (source: Perplexity)
- LSP plugins (pyright-lsp, typescript-lsp) now in official marketplace — real-time type diagnostics (source: Perplexity)
- kepano/obsidian-skills (~7k stars) — 44 skills by Obsidian CEO for correct Obsidian format handling (source: Perplexity)
- Practical skill ceiling ~100 before efficiency degrades; one engineer found 40/47 installed skills made output worse (source: Perplexity)

**NEW INSIGHTS (Perplexity only):**
- SLASH_COMMAND_TOOL_CHAR_BUDGET env var exists to raise the 15k limit
- thedotmack/claude-mem (89k stars) is the dominant persistent memory solution — hooks-based, SQLite+Chroma
- hamelsmu/evals-skills covers the AI eval pipeline gap comprehensively
- description directive language requirement changed in Feb 2026 update
- ccpi CLI (`pnpm add -g @intentsolutionsio/ccpi`) for terminal-native skill install

**GAPS IDENTIFIED:**
- Actual GitHub URLs need verification (some may be approximate/constructed)
- claude-mem install complexity and overhead vs. our existing memory system
- Whether pyright-lsp/typescript-lsp require system language servers (PATH requirement)
- tonsofskills.com skills quality variance — need filtering criteria

**DISPUTED/UNCERTAIN:**
- obra/superpowers and claude-mem star counts (89k for claude-mem seems extremely high — needs verification)
- Which tonsofskills skills are actually well-maintained vs one-commit wonders

**RECOMMENDATIONS SO FAR:**
- Install obra/superpowers for enforced dev discipline
- Install pyright-lsp + typescript-lsp from official marketplace for real-time type checking
- Install kepano/obsidian-skills for Obsidian MCP + Claude integration
- Set `SLASH_COMMAND_TOOL_CHAR_BUDGET=30000` immediately
- Consider claude-mem for cross-session memory (verify vs our existing system)
- Skip tonsofskills skills until quality-filtered
