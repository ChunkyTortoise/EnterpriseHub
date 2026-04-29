# Research Query — Claude Skills Ecosystem Curation

**Date**: 2026-04-29  
**Flags**: full pipeline (no --quick, no --skip-notebooklm)

---

## Topic

Comprehensive 2025-2026 landscape of Claude Code SKILLS, AGENTS, and PLUGINS worth
adopting by a senior AI engineer. Two tracks of equal weight:

(A) WORK FIT — Python/FastAPI + Next.js + Streamlit + Postgres + Redis + Claude/
    Gemini/Perplexity + GHL + Stripe + freelance ops automation

(B) GENERAL CAPABILITY — utility, personal productivity, writing, knowledge mgmt,
    learning, life-admin, research, communication, browser automation — anything
    that makes the operator more capable/efficient as an individual, regardless of
    project domain

Cover: Anthropic's official skills cookbook, the Claude Code plugin marketplace,
awesome-claude-skills lists, GitHub topic:claude-skill / topic:claude-code-plugin
repos, individual practitioner repos, HN/Reddit/dev.to discussions.

For each item include:
- name, kind (skill/agent/plugin), source URL
- install command (e.g. `cp -r <repo>/skill ~/.claude/skills/<name>` or `/plugin install <id>`)
- problem it solves / use case
- why it beats writing a custom one OR using native Claude
- install risk (auth required, MCP deps, secrets, maintenance status)
- overlap with existing items (see inventory below) — tag as HIGH/LOW
- tag: [work] or [personal-productivity]
- category bucket: one of: writing | knowledge-mgmt | research-learning | communication | life-admin | reading-summarization | journaling-habits | browser-automation | dev-productivity | code-review-testing | ops-observability | data-bi | freelance-ops | ai-engineering | ui-design | security | misc

Exclude items already in my inventory (see below). Flag if something in my inventory
is duplicated by a better alternative.

---

## Already Installed — EXCLUDE THESE (dedup baseline)

### Skills (35)
ask, claude-prompt-engineer, compare, design-md, docker-patterns, draft-email,
enhance-prompt, fastapi-patterns, frontend-aesthetics, ghl-bot, git-maintain,
github-actions, hospitality-resume, large-context-review, lead-scan,
multi-llm-routing, nextjs-patterns, pgvector-rag, postgres-migration,
prompt-engineer, pytest-patterns, quality-standards, react-components,
realtime-check, redis-patterns, render-deploy, research-pipeline, second-opinion,
second-opinion-checkpoint, shadcn-ui, skill-creator, spec-creator, stitch-design,
stitch-loop, streamlit-dashboard, visual-audit

### Agents (33)
ats-assembler, case-study-generator, claude-prompt-architect, data-pipeline-architect,
email-drafter, follow-up-scheduler, freelance-ops-digest-writer,
freelance-ops-gmail-scout, freelance-ops-lead, freelance-ops-lead-check,
freelance-ops-linkedin, freelance-ops-pipeline-tracker, freelance-ops-upwork,
ghl-integration-specialist, human-queue-builder, lead-check-lite, lead-scan-fiverr,
lead-scan-gmail, lead-scan-indeed, lead-scan-linkedin, lead-scan-orchestrator,
llm-cost-optimizer, multi-model-researcher, pipeline-groomer, project-scope-analyst,
prompt-engineering-specialist, strategy-consolidator, technical-proposal-writer,
visual-audit-api-tester, visual-audit-crawler, visual-audit-evaluator,
visual-audit-monitor, visual-repo-auditor

### MCP Servers (24)
atlassian, claude-in-chrome, claude_ai_Canva, claude_ai_Excalidraw,
claude_ai_Gmail, claude_ai_Google_Calendar, claude_ai_Google_Drive,
claude_ai_Hugging_Face, claude_ai_Indeed, claude_ai_Slack, claude_ai_Supabase,
claude_ai_Vercel, figma, gemini, ghl, grok-mcp, grok-media, gumroad, memory,
multi-llm, notebooklm, obsidian, plugin_compound-engineering_context7, upwork

---

## Seed Sources (models MUST investigate all of these)

See `00-seed-sources.md` for full list including:
- github.com/anthropics/claude-code, anthropics/anthropic-cookbook
- github.com/obra/superpowers, wshobson/agents, wshobson/commands
- github.com/disler/claude-code-hooks-mastery
- GitHub topics: claude-skill, claude-code-plugin, claude-agent, claude-code
- awesome-claude-code, awesome-claude-skills lists
- Claude Code plugin marketplace + claudelog.com
- Reddit r/ClaudeAI, HN, dev.to, X/Twitter recent posts

---

## Required Output Schema (RECOMMENDATIONS.csv)

name, kind, source_url, install_cmd, category, track, fit_score_0_5, install_risk, overlap_with, last_commit, stars, verified

---

## Category Buckets (enforce breadth — must have recs in each non-empty bucket)

writing | knowledge-mgmt | research-learning | communication | life-admin |
reading-summarization | journaling-habits | browser-automation | dev-productivity |
code-review-testing | ops-observability | data-bi | freelance-ops | ai-engineering |
ui-design | security | misc

---

## Codebase Context (EnterpriseHub project)

**Stack**: FastAPI (async) | Streamlit BI | PostgreSQL + Alembic | Redis L1/L2/L3 cache |
Claude + Gemini + Perplexity | GoHighLevel CRM | Stripe | Docker Compose

**Active workstreams**:
1. Jorge bots — AI lead qualification chatbots (buyer/seller/general)
2. Freelance ops — daily automated pipeline (Gmail scout → LinkedIn → Upwork → digest)
3. Portfolio BI dashboards — Streamlit metrics visualization
4. EnterpriseHub RAG system — advanced_rag_system with vector store + embeddings
