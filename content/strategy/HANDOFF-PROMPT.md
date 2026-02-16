# Portfolio Build — Team Execution Handoff

Paste everything below the `---` into a new Claude Code chat to continue.

---

## Context

We have a 5-product AI SaaS portfolio with a complete technical spec and parallel execution plan. All planning is done — now we need to BUILD. The spec and plan are in the repo. 39 old overlapping beads were closed and replaced by 6 clean workstream epics.

## Current State

- **$0 revenue**, 11 repos with 8,500+ tests
- **Spec**: `content/strategy/optimized-product-spec.md` (4,100 lines, sections 0-10)
- **Execution plan**: `content/strategy/agent-execution-plan.md` (780 lines, 6 workstreams)
- **Market research**: `content/strategy/04-perplexity-market-research-results.md`

## Beads Epics (6 workstreams, ~395 total hours)

| Bead ID | WS | Product | Hours | Priority | Blocked By |
|---------|-----|---------|-------|----------|------------|
| `EnterpriseHub-7jti` | WS-1 | Shared Infrastructure (schemas, auth, billing, CI/CD) | 30h | P0 | None — CRITICAL PATH |
| `EnterpriseHub-lzx9` | WS-2 | Voice AI Agent Platform (Pipecat, per-min billing, GHL white-label) | 160h | P0 | WS-1 |
| `EnterpriseHub-5h5s` | WS-3 | MCP Server Toolkit & Marketplace (framework + 7 servers) | 60h | P0 | None |
| `EnterpriseHub-h2rp` | WS-4 | AI DevOps Suite (monitoring + pipeline + prompt registry merged) | 55h | P1 | WS-1 |
| `EnterpriseHub-r6qw` | WS-5 | RAG-as-a-Service (multi-tenant hosted DocQA API) | 80h | P1 | WS-1 |
| `EnterpriseHub-jkpk` | WS-6 | Cohort Course + GTM (Maven, Discord, content marketing) | 40h+ | P0 | None |

### Dependency Graph
```
WS-1 (Shared Infra, 30h) ──blocks──▶ WS-2 (Voice AI), WS-4 (DevOps Suite), WS-5 (RAG)
WS-3 (MCP Toolkit) ──────────────▶ fully independent
WS-6 (Course + GTM) ─────────────▶ fully independent
```

## Task

Create a team and execute the build plan. Here's the approach:

### Phase 1 — Start 3 independent workstreams NOW (Week 1-2)

1. **WS-1: Shared Infrastructure** — MUST complete first (unblocks 3 others)
   - Read `optimized-product-spec.md` Section 0 for schemas/code
   - Read `agent-execution-plan.md` WS-1 for file list and milestones
   - Deliverable: `shared-schemas/` package with tenant, auth, billing schemas + Stripe service + auth middleware + CI templates
   - Update bead `EnterpriseHub-7jti` to in_progress, close when done

2. **WS-3: MCP Server Toolkit** — independent, start immediately
   - Read `optimized-product-spec.md` Section 2 for architecture/code
   - Read `agent-execution-plan.md` WS-3 for file list
   - Start with: EnhancedMCP framework + database query server + web scraping server
   - Update bead `EnterpriseHub-5h5s` to in_progress

3. **WS-6: Course + GTM** — independent, start immediately
   - Read `optimized-product-spec.md` Section 4 for course structure
   - Read `agent-execution-plan.md` WS-6 for setup tasks
   - Start with: Maven course config, Discord server structure, ConvertKit waitlist sequences
   - Update bead `EnterpriseHub-jkpk` to in_progress

### Phase 2 — After WS-1 completes, start remaining 3

4. **WS-2: Voice AI Platform** — largest workstream (160h)
5. **WS-4: AI DevOps Suite** — merged product (55h)
6. **WS-5: RAG-as-a-Service** — multi-tenant (80h)

### Agent Types to Use
- `general-purpose` for all build agents (need file write + bash access)
- Each agent should read ONLY their spec section + Section 0 (shared contracts)
- Use `bd update <id> --status=in_progress` when starting, `bd close <id>` when done

### Key Files Each Agent Needs
| Agent | Spec Sections | Plan Section |
|-------|--------------|--------------|
| infra-lead | Section 0 | WS-1 |
| mcp-builder | Section 0 + Section 2 | WS-3 |
| course-gtm | Section 4 | WS-6 |
| voice-ai-builder | Section 0 + Section 1 | WS-2 |
| devops-suite-builder | Section 0 + Section 3 | WS-4 |
| rag-builder | Section 0 + Section 5 | WS-5 |

### Products Summary (5 total, compliance CUT)
1. **Voice AI Agent Platform** — Pipecat + Deepgram STT + ElevenLabs TTS + Twilio. Per-minute pricing ($0.10-$0.20/min). GHL-native. Fly.io deployment. White-label for agencies.
2. **MCP Server Toolkit** — EnhancedMCP framework + 7 servers. PyPI + Gumroad ($49-$149/server). A2A compatibility.
3. **AI DevOps Suite** — Merged: Agent Monitoring + Web Data Pipeline + Prompt Registry. $49-$199/mo. Single repo.
4. **Cohort Course** — Maven platform, 6-week "Production AI Systems". $797-$1,997. Self-paced $397 on Gumroad after.
5. **RAG-as-a-Service** — Schema-per-tenant pgvector. $99-$999/mo + $0.005/query. PII detection + audit logging as premium.

### Session Protocol
- Use `bd` for all task tracking (not TodoWrite/TaskCreate)
- `bd sync` + `git push` before ending session
- Each agent commits to its own branch, merges to main when milestone complete
