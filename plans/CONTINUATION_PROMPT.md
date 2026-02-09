# Continuation Prompt — ChunkyTortoise Portfolio

> Paste this into a new Claude Code session to resume work from Feb 9, 2026.

---

## Session Startup

```bash
# 1. Prime beads (loads task tracker context)
bd prime

# 2. See available work
bd ready

# 3. Inspect a specific bead
bd show qaiq    # P0 — Fiverr gigs
bd show 4j2     # P2 — Upwork proposals
bd show 9je     # P2 — LinkedIn recommendations
bd show pbz     # P3 — LinkedIn content cadence
bd show vp9     # P3 — Upwork profile improvements
```

---

## Project State Summary

**Portfolio**: 11 repos, all CI green, ~7,243 tests (5,004 in EnterpriseHub).
**Beads**: 184 total, 179 closed (97.3%), 5 open — all are human-action items (no dev work remaining).
**Dev work**: Complete. All code, tests, CI pipelines, agents, and integrations are shipped.

### What's Done
- EnterpriseHub: FastAPI + Claude AI + PostgreSQL + Redis + 3 CRM adapters (GHL, HubSpot, Salesforce) + chatbot widget + 22 Claude Code agents + 5 MCP servers
- 10 supporting repos: jorge bots, AgentForge, Revenue-Sprint, insight-engine, docqa-engine, scrape-and-serve, mcp-toolkit, prompt-engineering-lab, llm-integration-starter, portfolio site
- Content assets: 50+ files across Fiverr, Gumroad, LinkedIn, Reddit, Upwork, Dev.to, HN, Product Hunt, cold outreach, GitHub Sponsors
- Job pipeline: 2 active conversations, 4 pending applications, 5 Round 2 targets

### What's Open (5 Beads)

| ID | P | Title | Blocker | Files |
|----|---|-------|---------|-------|
| `qaiq` | P0 | Fiverr: Create seller account + list 3 gigs | Profile photo upload | `content/fiverr/` (4 files) |
| `4j2` | P2 | Upwork: Buy Connects + submit proposals | $12 budget | `plans/archive/job-search/UPWORK_PROPOSALS_FEB8_ROUND2.md` |
| `9je` | P2 | LinkedIn: Send 3-5 recommendation requests | None | `plans/archive/linkedin/LINKEDIN_RECOMMENDATION_REQUESTS.md` |
| `pbz` | P3 | LinkedIn: Weekly content + daily engagement | None (ongoing) | `plans/archive/linkedin/LINKEDIN_POSTS_DRAFT.md`, `LINKEDIN_POSTS_WEEK2.md` |
| `vp9` | P3 | Upwork: Profile improvements | None | `content/upwork-profile-improvements.md` |

---

## Known Blockers

1. **Fiverr profile photo** — Cannot complete onboarding without uploading a headshot. Once uploaded, 3 gigs can be created in ~30 min.
2. **$12 for Upwork Connects** — Need 80 Connects at $0.15/ea to submit 5 Round 2 proposals.
3. **Gumroad bank account** — Must connect bank (Settings > Payments) before 4 products can publish. Products are drafted but "Publish" fails without payment method.
4. **Streamlit deploy URLs** — Cold outreach emails reference live demo links. Deploy 3 apps first: ct-enterprise-ai, ct-agentforge, ct-insight-engine.
5. **Concourse (YC) password** — Application stalled at WorkAtAStartup signup form.

---

## Key File Paths

### Content Assets (Ready to Use)
```
content/
  fiverr/                          # 4 files: 3 gig descriptions + seller profile
  gumroad/                         # 5 files: 4 product descriptions + seller profile
  reddit/                          # 4 files: 2 posts + engagement templates + campaign guide
  social/                          # 5 files: Reddit/HN/cross-platform posts
  outreach/                        # 3 files: 30 targets + email templates + tracker
  devto/                           # 4 files: 3 Dev.to articles
  github-sponsors/                 # 3 files: tiers + sponsors section + setup
  producthunt/                     # 1 file: AgentForge launch copy
  LAUNCH_ACTION_GUIDE.md           # Master launch checklist
  REDDIT_POST_NOW.md               # Ready-to-post Reddit content
  upwork-profile-improvements.md   # Full Upwork profile refresh
  upwork-video-script.md           # Video intro script
  streamlit_cloud_deployment.md    # Streamlit Cloud deploy guide
```

### Plans & Job Search
```
plans/
  PROJECT_STATUS_SPEC.md           # Comprehensive status spec (Feb 9)
  KIALASH_CALL_PREP.md             # Call prep for Feb 10 interview
  PLATFORM_PROFILES.md             # Freelancer/Toptal/Arc.dev/Contra profiles
  WAVE2_QUICK_DEPLOY.md            # Streamlit deployment plan
  archive/
    linkedin/                      # 7 files: posts, recommendations, optimization
    job-search/                    # 5 files: proposals, templates, listings
```

---

## Priority Action List

### Do Now (No Blockers)
1. **LinkedIn recommendations** — Paste templates from `plans/archive/linkedin/LINKEDIN_RECOMMENDATION_REQUESTS.md` into LinkedIn messages. 15 min.
2. **Reddit posts** — Post from `content/REDDIT_POST_NOW.md` and `content/reddit/r_python_post.md`. 10 min.
3. **HN Show post** — Post from `content/social/hn-show-agentforge.md`. 5 min.
4. **LinkedIn Week 1 posts** — Publish from `plans/archive/linkedin/LINKEDIN_POSTS_DRAFT.md`. 10 min.
5. **Upwork profile** — Apply improvements from `content/upwork-profile-improvements.md`. 45 min.
6. **Dev.to articles** — Publish from `content/devto/`. 15 min.

### After Photo Upload
7. **Fiverr gigs** — Create 3 gigs from `content/fiverr/`. 30 min.

### After $12 Budget
8. **Upwork Connects** — Buy 80 Connects, submit 5 proposals from `plans/archive/job-search/UPWORK_PROPOSALS_FEB8_ROUND2.md`. 20 min.

### After Bank Account Connected
9. **Gumroad products** — Publish 4 products from `content/gumroad/`. 15 min.

### After Streamlit Deploys
10. **Cold outreach** — Launch campaign from `content/outreach/`. 30 min.
11. **Platform profiles** — Create from `plans/PLATFORM_PROFILES.md`. 20 min.
12. **Product Hunt** — Launch from `content/producthunt/agentforge-launch.md`. 15 min.
13. **GitHub Sponsors** — Set up from `content/github-sponsors/`. 15 min.

---

## Upcoming Calendar

- **Tue Feb 10, 4 PM EST** — Kialash Persad call (Sr AI Agent Eng). Prep: `plans/KIALASH_CALL_PREP.md`
- **Ongoing** — FloPro Jamaica: awaiting contract offer ($75/hr)
- **Pending** — Concourse (YC), Prompt Health, Rula applications

---

## Bead Commands Reference

```bash
bd prime                    # Load context in new session
bd ready                    # Show unblocked work
bd show <id>                # Full bead details
bd update <id> --status=in_progress  # Claim work
bd close <id>               # Mark complete
bd close <id1> <id2> ...    # Close multiple
bd sync                     # Sync with git remote
bd stats                    # Project statistics
```

---

## Technical Notes

- **Python**: 3.11 (pyright basic mode)
- **Hooks**: PostToolUse (ruff auto-fix), PreToolUse (secret file write guard)
- **MCP servers**: memory, postgres, redis, stripe, playwright
- **22 Claude Code agents**: All domain-agnostic, configured in `.claude/agents/`
- **Beads**: Task tracker in `.beads/` directory, auto-synced with git hooks
- **Browser automation**: Chrome extension preferred (Fiverr blocks Playwright). Use `ref`-based clicks, not coordinates.
- **Gumroad content editor**: ProseMirror/Tiptap — use clipboard paste, not innerHTML injection.
