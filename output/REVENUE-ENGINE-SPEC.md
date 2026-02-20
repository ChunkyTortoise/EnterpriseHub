# Revenue Engine — Ground Truth Spec
**Date**: 2026-02-19 | **Status**: Active Execution | **Team**: revenue-engine
**CWD for all agents**: `/Users/cave/Projects/EnterpriseHub_new`

---

## Infrastructure Inventory

### MCP Servers
| Server | Config | Auth | Notes |
|--------|--------|------|-------|
| gumroad | `.mcp.json` | `GUMROAD_ACCESS_TOKEN` | **READ-ONLY** — use playwright for uploads |
| upwork | `.mcp.json` | none required | Job search, proposals |
| ghl | `.mcp.json` | `GHL_API_KEY`, `GHL_LOCATION_ID` | CRM integration |
| playwright | plugin (global) | none | Browser automation for uploads/publishing |
| stripe | plugin (global) | `STRIPE_SECRET_KEY` | Revenue data |
| memory | `.mcp.json` | none | Knowledge graph |

### Key Agents (in `~/.claude/agents/`)
- `content-marketing-engine.md` — multi-format content from single topic
- `technical-proposal-writer.md` — proposals + SOWs
- `outreach-personalizer.md` — personalized cold outreach sequences
- `platform-profile-optimizer.md` — platform profile optimization
- `case-study-generator.md` — case studies from repo metrics
- `llm-cost-optimizer.md` — cost efficiency engineering

### Key Skills
- `/proposal` — Upwork/freelance proposal generation
- `/outreach` — Cold outreach sequence generation
- `/draft-content` — Multi-format content generation
- `/case-study` — Case study transformation
- `/weekly-status` — Weekly freelance progress report
- `/revenue-update` — Revenue tracker update

### Critical File Paths
| File | Purpose |
|------|---------|
| `content/gumroad/GUMROAD_UPLOAD_MANIFEST.md` | All 21 product definitions |
| `output/gumroad-upload-top2-feb19.md` | Top 2 priority uploads |
| `~/.claude/reference/freelance/client-pipeline.md` | All proposals, prospects |
| `~/.claude/reference/freelance/content-assets.md` | Published/drafted content status |
| `~/.claude/reference/freelance/revenue-tracker.md` | Income by channel/month |
| `content/outreach/BATCH_2_SEQUENCES.md` | Batch 2 outreach sequences |
| `content/linkedin/content-calendar-feb-mar-2026.md` | LinkedIn posting calendar |
| `content/linkedin/week2/` | Posts #4, #5, #6 (ready to publish) |
| `output/batch2-send-ready.md` | ← CREATE: 10 emails formatted |
| `output/upwork-opportunities-2026-02-19.md` | ← CREATE: Scored job list |
| `output/flywheel/` | ← CREATE: Content flywheel outputs |

---

## Human-in-the-Loop Gates

**CRITICAL: These require human action before automation can proceed.**

| Gate | Trigger | Agent Action | Human Action Required |
|------|---------|--------------|----------------------|
| G1: Gumroad Upload | Task 2.2 start | Pause, message orchestrator with blocker | Login at gumroad.com, confirm session active |
| G2: LinkedIn Publishing | Task 1.6 start | Attempt playwright, report status | Login at linkedin.com if session expired |
| G3: Email Sending | Task 4.1 complete | Mark output as "READY-TO-SEND-HUMAN" | Copy/paste from output file, send from Gmail |
| G4: Upwork Submission | Task 3.5 complete | Mark proposals as "READY-TO-SUBMIT-HUMAN" | Copy/paste proposals to Upwork, submit manually |

**When blocked**: Send message to `revenue-orchestrator` with format:
```
BLOCKER: [Gate ID] [Task ID]
Reason: [specific reason]
File: [output file path where draft is saved]
Next step for human: [exact action needed]
```

---

## Task Registry — Phase 1 (Streams 1–4)

### Stream 1 — Content Repurposing Flywheel (Builder A: content-flywheel-builder)

| ID | Task | Dependencies | Output Path | Acceptance Criteria |
|----|------|-------------|-------------|---------------------|
| 1.1 | Audit content dirs, identify top 5 topics | none | `output/content-topic-map.md` | Table: topic, source path, repurposing value |
| 1.2 | Run flywheel on topic #1 via content-marketing-engine | 1.1 | `output/flywheel/topic-1/` | 6 files: linkedin, twitter, devto, newsletter, reddit, youtube-script |
| 1.3 | Write Gumroad listing for flywheel system ($49-99) | 1.2 | `content/gumroad/content-flywheel-starter-LISTING.md` | Full listing: name, price, description, tags, slug |
| 1.4 | Write Fiverr micro-gig for $150/batch service | 1.2 | `content/fiverr/content-flywheel-gig.md` | Full gig: title, packages, FAQ, tags |
| 1.5 | Batch run flywheel on topics 2-5 | 1.2 | `output/flywheel/topic-[2-5]/` | 4 directories, 6 files each |
| 1.6 | Publish LinkedIn posts 4, 5, 6 via playwright | none | Update `~/.claude/reference/freelance/content-assets.md` | Posts published OR blocker logged |

**Scoring**: Topic repurposing value = existing reach × content depth × monetization potential

---

### Stream 2 — Gumroad Upload Automation (Builder B: gumroad-uploader)

| ID | Task | Dependencies | Output Path | Acceptance Criteria |
|----|------|-------------|-------------|---------------------|
| 2.1 | Parse all 21 product manifests into upload queue | none | `output/gumroad-upload-queue.json` | 21 entries: name, price, slug, desc_path, cover_needed, zip_needed |
| 2.2 | Upload top 2: Prompt Toolkit ($29) + AI Starter ($39) | 2.1 | `output/gumroad-upload-log.md` | Both live at gumroad.com with correct prices; URLs logged |
| 2.3 | Upload AgentForge 3-tier ($49/$199/$999) | 2.2 | Append to upload log | 3 products live; tier pricing correct |
| 2.4 | Upload remaining 16 products (batches of 4) | 2.3 | Append to upload log | All 16 products live; log complete |
| 2.5 | Verify all via gumroad MCP | 2.4 | Append verification to upload log | gumroad MCP returns 21 products, status=published |
| 2.6 | Update revenue-tracker with Gumroad inventory | 2.5 | `~/.claude/reference/freelance/revenue-tracker.md` | Gumroad section: 21 products, prices, URLs |

**⚠️ Gate G1 applies to Task 2.2**: Check for active Gumroad session before attempting playwright upload.

---

### Stream 3 — Proposal Intelligence (Builder C: proposal-intelligence-builder)

| ID | Task | Dependencies | Output Path | Acceptance Criteria |
|----|------|-------------|-------------|---------------------|
| 3.1 | Fetch + score Upwork job postings | none | `output/upwork-opportunities-2026-02-19.md` | Top 10 jobs: title, budget, fit score 1-10, rationale, URL |
| 3.2 | Generate proposals for score >= 7 jobs | 3.1 | `proposals/2026-02-19-[job-slug].md` | 1 proposal per qualifying job; passes 9-point quality check |
| 3.3 | Create follow-up tracking for A1-A9 proposals | none (parallel) | `~/.claude/reference/freelance/client-pipeline.md` | Follow-up dates added for all 9 proposals |
| 3.4 | Build daily opportunity digest template | 3.1 | `output/upwork-daily-digest-template.md` | Reusable template + MCP query params + scoring rubric |
| 3.5 | Format top 3 proposals for submission | 3.2 | Append to each proposal file | Upwork-pasteable format; status tracked in client-pipeline.md |

**Scoring rubric**: Skill match (4pts) + budget $60+/hr or $500+ fixed (2pts) + few proposals (2pts) + urgency signals (1pt) + scope clarity (1pt) = 10 max

---

### Stream 4 — Cold Outreach Automation (Builder C, parallel with Stream 3)

| ID | Task | Dependencies | Output Path | Acceptance Criteria |
|----|------|-------------|-------------|---------------------|
| 4.1 | Finalize Batch 2 (10 emails) for sending | none | `output/batch2-send-ready.md` | 10 emails formatted, personalized, ready-to-paste |
| 4.2 | Write Email 2 follow-ups for Batch 1 (Feb 21) | none (parallel) | `output/batch1-followup2-feb21.md` | 10 personalized follow-ups referencing their pain points |
| 4.3 | Write Email 3 final follow-ups for Batch 1 (Feb 25) | 4.2 | `output/batch1-followup3-feb25.md` | 10 "case study + soft close" emails; no duplication with Email 2 |
| 4.4 | Update client-pipeline with full campaign status | 4.1, 4.2 | `~/.claude/reference/freelance/client-pipeline.md` | Cold Outreach section: per-prospect status, send dates, follow-up dates |

**⚠️ Gate G3 applies to Task 4.1**: Mark output as "READY-TO-SEND-HUMAN". Agent does NOT send emails.

---

## Task Registry — Phase 2 (Streams 5–7)
**Trigger**: Spawn Builder D when Phase 1 is 80% complete (17 of 21 tasks done)

### Stream 5 — GTM Workflow Builder (Builder D: gtm-platform-builder)

| ID | Task | Output Path | Acceptance Criteria |
|----|------|-------------|---------------------|
| 5.1 | Write GTM Workflow Builder SOW template | `output/gtm-sow-template.md` | 3 tiers: $2,500/$3,500/$5,000; deliverables + timeline |
| 5.2 | Design Proposal-from-Transcript agent spec | `project_specs/gtm-proposal-from-transcript-spec.md` | Inputs/outputs/prompts/tools/GHL MCP integration |
| 5.3 | Design ICP Definition agent spec | `project_specs/gtm-icp-agent-spec.md` | Agent spec from CRM data → ICP document |
| 5.4 | Write Fiverr premium gig listing ($2,500-5,000) | `content/fiverr/gtm-workflow-builder-gig.md` | Full Fiverr listing for the service |

### Stream 6 — Skills MCP Server (Builder D, parallel with Stream 5)

| ID | Task | Output Path | Acceptance Criteria |
|----|------|-------------|---------------------|
| 6.1 | Audit skills for MCP packaging | `output/skills-mcp-inventory.md` | Table: skill, I/O schema, monetization potential |
| 6.2 | Design Skills MCP Server architecture | `project_specs/skills-mcp-server-spec.md` | Tool schemas, pricing model, Agent37 submission requirements |
| 6.3 | Build mcp-server-toolkit skeleton | `mcp-server-toolkit/` | Valid MCP server entry point + 4 tool stubs + README |

**Skills to bundle**: `/proposal` + `/outreach` + `/draft-content` + `/case-study`

### Stream 7 — Revenue Intelligence Dashboard (Builder D, parallel with 5+6)

| ID | Task | Output Path | Acceptance Criteria |
|----|------|-------------|---------------------|
| 7.1 | Design ETL from Stripe + Gumroad + Upwork MCPs | `output/revenue-dashboard-etl-design.md` | Data sources, field mappings, normalized schema, refresh schedule |
| 7.2 | Build `revenue_auto_update.py` | `scripts/revenue_auto_update.py` | Queries MCPs, updates revenue-tracker.md, exits 0 |
| 7.3 | Build `revenue_dashboard.py` Streamlit app | `scripts/revenue_dashboard.py` | Monthly revenue chart, YTD total, transaction log, weekly trend |
| 7.4 | Run /weekly-status and generate first report | `output/weekly-status-2026-02-19.md` | Dashboard runs with `streamlit run`; report generated |

---

## Parallel Execution Diagram

```
Phase 1 (Days 1-3):
Builder A: [1.6]──[1.1]──[1.2]──[1.3+1.4]──[1.5]
Builder B: [2.1]──[2.2*]──[2.3]──[2.4]──[2.5]──[2.6]  (*gate G1)
Builder C: [3.3+4.1+4.2 parallel]──[3.1]──[3.2]──[3.4+3.5]──[4.3]──[4.4]

Phase 2 trigger: 80% Phase 1 done → Spawn Builder D
Builder D: [6.1]──[6.2]──[6.3]
           [5.1]──[5.2+5.3]──[5.4]
           [7.1]──[7.2]──[7.3]──[7.4]
```

---

## Output Conventions

- All markdown files: GitHub-flavored markdown
- All JSON files: minified, valid JSON
- Log files: append-only, with timestamps `[2026-02-19 HH:MM]` prefix
- Proposal files: named `proposals/2026-02-19-[job-slug].md`
- Flywheel dirs: `output/flywheel/topic-[N]/` with 6 files: `linkedin.md`, `twitter.md`, `devto.md`, `newsletter.md`, `reddit.md`, `youtube-script.md`
- Status updates: sent to `revenue-orchestrator` via SendMessage

---

## Phase Completion Criteria

**Phase 1 Complete When:**
- `output/flywheel/` has 5 subdirectories with 6 files each (30 total)
- `output/gumroad-upload-log.md` lists 21 products
- `output/upwork-opportunities-2026-02-19.md` has 10 scored opportunities
- `proposals/` has at least 3 new proposal files dated 2026-02-19
- `output/batch2-send-ready.md` has 10 emails
- `output/batch1-followup2-feb21.md` has 10 emails
- `~/.claude/reference/freelance/client-pipeline.md` updated

**Phase 2 Complete When:**
- `output/gtm-sow-template.md` exists with 3 pricing tiers
- `mcp-server-toolkit/` exists with valid MCP server skeleton
- `scripts/revenue_auto_update.py` is syntactically valid Python
- `scripts/revenue_dashboard.py` runs with `streamlit run`
- `output/weekly-status-2026-02-19.md` generated
