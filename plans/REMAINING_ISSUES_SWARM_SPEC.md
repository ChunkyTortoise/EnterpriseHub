# Remaining Issues Swarm Execution Spec

**Date**: 2026-02-14
**Scope**: 19 open beads issues across 5 workstreams
**Method**: Agent team with parallel workstreams + dependency-aware sequencing
**Estimated time**: 4-6 hours agent time

---

## Issue Inventory

### Currently In Progress (WP Team — Do Not Duplicate)
| ID | Issue | Status |
|----|-------|--------|
| `nce6` | WP1: Fix 4 failing Jorge tests | IN_PROGRESS |

### Blocked Until WP1 Completes
| ID | Issue | Blocked By |
|----|-------|------------|
| `do6h` | WP5: End-to-end conversation flow tests | WP1 (`nce6`) |
| `ximk` | WP7: Documentation and deployment readiness | WP1 + WP2 + WP3 |

### Ready to Execute (19 issues, 5 workstreams)

**Workstream A: Jorge Bot Completion** (code — 3 issues)
**Workstream B: PyPI Publishing** (packaging — 2 issues)
**Workstream C: Content & Outreach** (writing — 5 issues)
**Workstream D: Platform Setup** (browser/manual — 4 issues)
**Workstream E: Freelance Pipeline** (mixed — 5 issues)

---

## Workstream A: Jorge Bot Completion

**Agent type**: `general-purpose` (needs Edit, Bash)
**Parallel with**: B, C, D, E
**Dependencies**: WP1 must finish first for `do6h` and `ximk`

| Order | Bead ID | Task | Effort | Agent Action |
|-------|---------|------|--------|--------------|
| A1 | `v9ae` | Verify calendar integration for HOT sellers | 30 min | Read `calendar_booking_service.py`, write integration test, verify GHL calendar API mock works |
| A2 | `p28d` | Phase 3: Close Critical Feedback Loops (5 loops) | 2-3 hr | Implement 5 feedback loops per Jorge enhancement spec. Read `docs/jorge-enhancement-p0-implementation.md` for context. Wire handoff outcome → threshold adjustment, abandonment → recovery trigger, A/B result → strategy selection, alert → escalation, performance → routing weight |
| A3 | `do6h` | WP5: End-to-end conversation flow tests | 1-2 hr | **BLOCKED until WP1 done.** Write e2e tests covering Lead→Buyer, Lead→Seller, and Seller→Buyer handoff flows. Use `JorgeHandoffService.evaluate_handoff()` + bot `process_*_conversation()` APIs |
| A4 | `ximk` | WP7: Documentation and deployment readiness | 1 hr | **BLOCKED until WP1+WP2+WP3 done.** Update deployment docs, verify Docker Compose config, document all GHL field IDs and workflow IDs |

**Key files**:
- `ghl_real_estate_ai/services/jorge/calendar_booking_service.py`
- `ghl_real_estate_ai/services/jorge/jorge_handoff_service.py`
- `ghl_real_estate_ai/services/jorge/performance_tracker.py`
- `ghl_real_estate_ai/services/jorge/alerting_service.py`
- `ghl_real_estate_ai/services/jorge/ab_testing_service.py`
- `docs/jorge-enhancement-p0-implementation.md`

---

## Workstream B: PyPI Publishing

**Agent type**: `repo-scaffold` or `general-purpose` (needs Bash for build/twine)
**Parallel with**: A, C, D, E
**Dependencies**: None

| Order | Bead ID | Task | Effort | Agent Action |
|-------|---------|------|--------|--------------|
| B1 | `weekly-plan-003` | Publish docqa-engine to PyPI | 45 min | Verify `pyproject.toml` exists and is valid (name, version, deps, entry points). Run `python -m build`. Run `twine check dist/*`. Dry-run upload with `--repository testpypi`. Update README with `pip install docqa-engine` instructions |
| B2 | `weekly-plan-004` | Publish insight-engine to PyPI | 45 min | Same process for insight-engine |

**Key files**:
- `advanced_rag_system/` (docqa-engine source)
- `ghl_real_estate_ai/streamlit_demo/` (insight-engine source)
- Look for `pyproject.toml` or `setup.py` in each package root
- If missing, create `pyproject.toml` following modern Python packaging conventions

**Pre-flight checks**:
1. Verify package names aren't taken on PyPI: `pip index versions docqa-engine`
2. Ensure `__version__` is set in `__init__.py`
3. Verify LICENSE file exists
4. Test local install: `pip install -e .`

**Note**: If PyPI credentials aren't available as env vars (`TWINE_USERNAME`, `TWINE_PASSWORD`), prepare everything up to the upload step and flag for manual upload.

---

## Workstream C: Content & Outreach Generation

**Agent type**: `content-marketing-engine` or `general-purpose`
**Parallel with**: A, B, D, E
**Dependencies**: None (all blockers resolved)

| Order | Bead ID | Task | Effort | Agent Action |
|-------|---------|------|--------|--------------|
| C1 | `u1ya` | Launch AgentForge on social media | 30 min | Generate final LinkedIn post + Twitter thread from bead description. Write to `content/social/agentforge-launch-linkedin.md` and `content/social/agentforge-launch-twitter.md`. Fill in actual Gumroad URLs. **Cannot post** — output files for manual posting |
| C2 | `1g4y` | Set up Gumroad email sequences | 45 min | Write the 2 upsell email sequences (Starter→Pro, Pro→Enterprise) to `content/gumroad/email-sequence-starter-to-pro.md` and `content/gumroad/email-sequence-pro-to-enterprise.md`. Include subject lines, body, CTA links. **Cannot configure in Gumroad** — output for manual setup |
| C3 | `mvkx` | Post LinkedIn Week 2 content | 30 min | Read `content/linkedin/LINKEDIN_WEEK2_PLAN.md` (or `plans/archive/linkedin/`). Generate 3 ready-to-post updates with hashtags. Write to `content/social/linkedin-week2-post-1.md`, `-2.md`, `-3.md`. **Cannot post** — output for manual posting |
| C4 | `nevv` | Send cold outreach batch 1 (10 emails) | 1 hr | Read `content/outreach/*.md` guides. Generate 10 personalized outreach emails. Write to `content/outreach/batch1/`. Include prospect name placeholders, pain points, portfolio evidence. **Cannot send** — output for manual sending |
| C5 | `9je` | LinkedIn recommendation requests | 15 min | Read `plans/archive/linkedin/LINKEDIN_RECOMMENDATION_REQUESTS.md`. Personalize 5 templates with real names/projects from portfolio context. Write to `content/social/linkedin-recommendations/`. **Cannot send** — output for manual messaging |

**Key reference files**:
- `~/.claude/reference/freelance/content-assets.md`
- `~/.claude/reference/freelance/portfolio-repos.md`
- `content/linkedin/` and `content/outreach/`
- Gumroad product URLs from `content/gumroad/`

---

## Workstream D: Platform Setup (Mostly Manual)

**Agent type**: `platform-profile-optimizer` or `general-purpose`
**Parallel with**: A, B, C, E
**Dependencies**: Some require human action

| Order | Bead ID | Task | Effort | Agent Action |
|-------|---------|------|--------|--------------|
| D1 | `qaiq` | Fiverr: Create seller account + list 3 gigs | 30 min | Read `output/fiverr-gigs-optimized.md`. Verify gig content is ready (titles, descriptions, pricing, tags, FAQs). Generate final copy-paste-ready gig listings in `content/fiverr/gig-1-dashboard.md`, `gig-2-rag.md`, `gig-3-chatbot.md`. **Cannot create account** — output for manual setup. Note: Fiverr blocks Playwright (PerimeterX) |
| D2 | `ty1t` | Sign up on Contra (0% commission) | 20 min | Read `~/.claude/reference/freelance/platform-profiles.md` and `~/.claude/reference/freelance/skills-certs.md`. Generate Contra profile copy matching the 3 Fiverr gigs. Write to `content/contra/profile.md` and `content/contra/service-1.md`, `-2.md`, `-3.md`. **Cannot create account** — output for manual setup |
| D3 | `l1ve` | Connect Gumroad bank account | 5 min | **100% MANUAL** — requires human to log into Gumroad > Settings > Payouts > Add bank. Agent can only write a checklist to `content/gumroad/bank-setup-checklist.md` |
| D4 | `jrgy` | Execute LinkedIn Week 2 posts | 15 min | Depends on C3 output. Verify posts are ready, create scheduling guide with dates (Feb 17, 19, 21). Write to `content/social/linkedin-week2-schedule.md`. **Cannot post** — requires Chrome ext with authenticated LinkedIn session |

---

## Workstream E: Freelance Pipeline

**Agent type**: `general-purpose`
**Parallel with**: A, B, C, D
**Dependencies**: Some blocked

| Order | Bead ID | Task | Effort | Agent Action |
|-------|---------|------|--------|--------------|
| E1 | `4j2` | Upwork: Purchase Connects + submit proposals | 30 min | **Deprioritized per notes** (out of Connects/money). Read `plans/UPWORK_PROPOSALS_FEB8_ROUND2.md`. Polish 5 proposal drafts and write final versions to `content/upwork/proposals/`. Flag as "ready when funded" |
| E2 | `vp9` | Upwork: Complete remaining profile improvements | 30 min | Read `~/.claude/reference/freelance/platform-profiles.md`. Generate optimized profile sections (headline, overview, skills, portfolio items). Write to `content/upwork/profile-update.md` |
| E3 | `pbz` | LinkedIn: Weekly content + daily engagement cadence | 30 min | Create a 4-week content calendar with post topics, hashtags, and engagement targets. Write to `content/linkedin/content-calendar-feb-mar-2026.md` |
| E4 | `82lt` | Update tracking files | 30 min | **Partially blocked** (needs `mvkx` done). Update `~/.claude/reference/freelance/` files with current state: revenue-tracker, content-assets, platform-profiles, client-pipeline. Can do partial update now |
| E5 | `js8i` | Test Issue | — | **Close** — stale test issue (P4) |

---

## Team Configuration

### Agent Roster (5 agents)

| Agent Name | Type | Workstream | Mode |
|------------|------|------------|------|
| `jorge-dev` | `general-purpose` | A (Jorge Bot) | `bypassPermissions` |
| `pypi-publisher` | `general-purpose` | B (PyPI) | `bypassPermissions` |
| `content-writer` | `general-purpose` | C (Content) | `bypassPermissions` |
| `platform-prep` | `general-purpose` | D (Platform Setup) | `bypassPermissions` |
| `pipeline-ops` | `general-purpose` | E (Freelance Pipeline) | `bypassPermissions` |

### Execution Order

```
Phase 1 (Parallel — all 5 agents start immediately):
├── jorge-dev:     A1 (calendar verify) → A2 (feedback loops)
├── pypi-publisher: B1 (docqa) → B2 (insight)
├── content-writer: C1 (AgentForge social) → C2 (Gumroad emails) → C3 (LinkedIn Week 2)
├── platform-prep:  D1 (Fiverr gigs) → D2 (Contra profile) → D3 (bank checklist)
└── pipeline-ops:   E1 (Upwork proposals) → E2 (Upwork profile) → E3 (content calendar)

Phase 2 (After WP1 completes + Phase 1):
├── jorge-dev:     A3 (e2e tests) → A4 (deployment docs)
├── content-writer: C4 (cold outreach) → C5 (LinkedIn recs)
├── platform-prep:  D4 (LinkedIn scheduling)
└── pipeline-ops:   E4 (tracking files) → E5 (close test issue)
```

### Completion Criteria

Each agent must:
1. Read relevant source files before writing
2. Write output to appropriate `content/` subdirectory
3. Mark beads as closed: `bd close <id> --reason="<summary>"`
4. Run `bd sync` after closing beads

### Beads to Close on Completion

```bash
# Phase 1 closures (after agent work)
bd close EnterpriseHub-v9ae --reason="Calendar integration verified"
bd close EnterpriseHub-weekly-plan-003 --reason="docqa-engine packaged for PyPI"
bd close EnterpriseHub-weekly-plan-004 --reason="insight-engine packaged for PyPI"
bd close EnterpriseHub-u1ya --reason="Social media launch content generated"
bd close EnterpriseHub-1g4y --reason="Gumroad email sequences written"
bd close EnterpriseHub-mvkx --reason="LinkedIn Week 2 posts generated"
bd close EnterpriseHub-qaiq --reason="Fiverr gig listings prepared"
bd close EnterpriseHub-ty1t --reason="Contra profile copy generated"
bd close EnterpriseHub-l1ve --reason="Bank setup checklist created (manual action needed)"
bd close EnterpriseHub-4j2 --reason="Proposals polished, ready when funded"
bd close EnterpriseHub-vp9 --reason="Profile update copy generated"
bd close EnterpriseHub-pbz --reason="Content calendar created"
bd close EnterpriseHub-9je --reason="Recommendation request templates personalized"
bd close EnterpriseHub-js8i --reason="Stale test issue"

# Phase 2 closures (after WP1 done)
bd close EnterpriseHub-do6h --reason="E2E conversation flow tests passing"
bd close EnterpriseHub-ximk --reason="Deployment docs updated"
bd close EnterpriseHub-p28d --reason="5 feedback loops implemented"
bd close EnterpriseHub-nevv --reason="10 outreach emails generated"
bd close EnterpriseHub-jrgy --reason="LinkedIn Week 2 scheduling guide created"
```

### Human Actions Required (Cannot Automate)

| Action | Bead | Time |
|--------|------|------|
| Create Fiverr seller account + paste gig copy | `qaiq` | 30 min |
| Create Contra account + paste profile/services | `ty1t` | 20 min |
| Connect Gumroad bank account | `l1ve` | 5 min |
| Post LinkedIn content (3 posts) | `mvkx`, `jrgy` | 15 min |
| Post AgentForge launch on LinkedIn + Twitter | `u1ya` | 10 min |
| Send LinkedIn recommendation DMs | `9je` | 15 min |
| Send cold outreach emails | `nevv` | 30 min |
| Upload to PyPI (if no credentials in env) | `weekly-plan-003/004` | 5 min |
| Purchase Upwork Connects (when funded) | `4j2` | 5 min |

**Total human time**: ~2.5 hours (spread across days)

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| WP1 takes longer than expected | Phase 2 items (A3, A4) can wait; Phase 1 is fully independent |
| PyPI package names taken | Check availability first; fall back to `enterprisehub-docqa` / `enterprisehub-insight` |
| No `pyproject.toml` exists | Agent creates one from scratch using repo metadata |
| Content quality varies | Content agent reads `~/.claude/reference/freelance/` for consistent voice/metrics |
| Gumroad API not available | Email sequences written as markdown for manual paste |
| Git conflicts from parallel agents | Each workstream writes to different directories; leader handles merge |

---

*Generated for agent team execution | 19 issues | 5 workstreams | ~4-6hr agent + ~2.5hr human*
