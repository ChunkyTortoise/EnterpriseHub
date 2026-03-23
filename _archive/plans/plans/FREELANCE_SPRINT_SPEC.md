# Freelance Growth Sprint — Parallel Agent Execution Spec

**Date**: 2026-02-14
**Goal**: Maximize revenue pipeline in one session using 7 parallel agent streams
**Estimated Duration**: 30-45 min agent work + 30 min human actions
**Revenue Target**: Unblock $2K-$5K/month recurring within 48 hours

---

## Current State Summary

| Metric | Value |
|--------|-------|
| Revenue to date | $0 |
| Products ready (not uploaded) | 21 Gumroad listings |
| Fiverr gigs drafted | 3 (account not created) |
| Cold outreach prospects researched | 30 (emails not sent) |
| LinkedIn Week 2 posts | 3 (not posted) |
| Streamlit apps ready | 3 (not deployed) |
| PyPI packages ready | 2 (not published) |
| Open beads (ready) | 10 |
| Warm leads | 2 (FloPro Jamaica, Kialash Persad) |

**The bottleneck is execution, not preparation.** Content exists for everything — it needs packaging, verification, and delivery.

---

## Team Architecture

```
┌─────────────────────────────────────────────────────┐
│                   TEAM LEAD (you)                    │
│          Orchestrates, reviews, merges               │
└──────────┬──────────┬──────────┬──────────┬─────────┘
           │          │          │          │
     ┌─────▼───┐ ┌───▼────┐ ┌──▼───┐ ┌───▼────┐
     │Stream 1 │ │Stream 2│ │Str 3 │ │Stream 4│
     │Gumroad  │ │Deploy  │ │Outreach│ │Content │
     │Products │ │Streamlit│ │Emails │ │LinkedIn│
     └─────────┘ └────────┘ └──────┘ └────────┘
           │          │          │          │
     ┌─────▼───┐ ┌───▼────┐ ┌──▼───┐
     │Stream 5 │ │Stream 6│ │Str 7 │
     │Jorge Bot│ │PyPI    │ │Platform│
     │Code Fix │ │Publish │ │Profiles│
     └─────────┘ └────────┘ └───────┘
```

**7 parallel streams, 0 cross-dependencies between streams.**

---

## Stream Definitions

### Stream 1: Gumroad Product Packaging (P0 — Revenue Critical)

**Agent**: `content-marketing-engine`
**Bead**: `cfoc`
**Input**: 21 listing files in `content/gumroad/`
**Output**: Verified, upload-ready product packages

**Tasks**:
1. Audit all 21 listing files for completeness (title, description, price, features, FAQ)
2. Verify 3-tier consistency across all 7 products (Starter/Pro/Enterprise)
3. Generate a `GUMROAD_UPLOAD_MANIFEST.md` with exact copy-paste fields per product:
   - Product name, price, description (HTML-formatted), cover image spec, tags
4. Create bundle listing content (3 bundles: Original Starters, Original Pro, Sprint Starters)
5. Generate SEO-optimized short descriptions (140 chars) for social sharing

**Success Criteria**: Single manifest file where each of 21+3 products has every Gumroad field ready to paste.

---

### Stream 2: Streamlit Deployment Scripts (P1 — Unblocks Outreach)

**Agent**: `devops-infrastructure`
**Bead**: `oom6`
**Input**: 3 repos (ai-orchestrator, prompt-engineering-lab, llm-integration-starter)
**Output**: Verified deployment configs + step-by-step deploy guide

**Tasks**:
1. Verify each repo has correct `requirements.txt` (no `-e .` for Streamlit Cloud)
2. Verify `.streamlit/config.toml` exists with theme settings
3. Verify main Streamlit entry point is correctly named and importable
4. Create/verify `streamlit_app.py` wrapper if needed for each repo
5. Generate `STREAMLIT_DEPLOY_GUIDE.md` with exact CLI commands:
   ```
   # For each app:
   streamlit cloud deploy --app-name ct-{name} --repo ChunkyTortoise/{repo} --branch main
   ```
6. Verify no secrets are hardcoded (env vars only)
7. Test that `streamlit run <entry_point>` would work (import checks)

**Success Criteria**: Human can deploy all 3 apps in <5 min by following the guide.

---

### Stream 3: Cold Outreach Batch Prep (P1 — Revenue Pipeline)

**Agent**: `outreach-personalizer`
**Bead**: `5sd4`
**Input**: 30 prospect files in `content/outreach/personalized/`
**Output**: 10 send-ready emails ranked by likelihood to convert

**Tasks**:
1. Review all 30 prospect files, rank by:
   - Company funding stage / size (funded > bootstrapped)
   - Pain-point match to our portfolio (RAG, chatbots, dashboards)
   - Decision-maker accessibility (direct email available)
2. Select top 10 prospects for Batch 1
3. For each, generate a 3-touch email sequence:
   - Email 1: Cold intro (send immediately)
   - Email 2: Value-add follow-up (send day 3)
   - Email 3: Case study + soft close (send day 7)
4. Personalize each email with:
   - Specific company pain point (from their website/product)
   - Matching portfolio evidence (metrics, test counts, demos)
   - Live demo URL placeholders (Streamlit apps — fill after Stream 2)
5. Output: `OUTREACH_BATCH_1_READY.md` with copy-paste emails

**Success Criteria**: 10 personalized 3-touch sequences ready to send via Gmail/Formspree.

---

### Stream 4: Content Marketing Finalization (P1 — Visibility)

**Agent**: `content-marketing-engine`
**Bead**: `mdmf`
**Input**: `content/linkedin/LINKEDIN_WEEK2_PLAN.md`
**Output**: Multi-platform content ready to post

**Tasks**:
1. Finalize LinkedIn Week 2 posts (3 posts) — verify hooks, CTAs, hashtags
2. Adapt LinkedIn content into:
   - 1 Dev.to article (technical deep-dive, 800-1200 words)
   - 1 Reddit post for r/MachineLearning or r/LangChain (value-first, no spam)
   - 1 Hacker News "Show HN" post (concise, links to GitHub)
3. Create posting schedule with optimal times:
   - LinkedIn: Tue/Wed/Thu 8-10 AM EST
   - Dev.to: Wednesday
   - Reddit: Thursday afternoon
   - HN: Friday morning
4. Write engagement prompts (5 thoughtful comments per platform for day-of posting)
5. Output: `CONTENT_WEEK2_READY.md` with all content + schedule

**Success Criteria**: All content copy-paste ready with platform-specific formatting.

---

### Stream 5: Jorge Bot Question Flow Fix (P0 — Product Quality)

**Agent**: `general-purpose` (needs file edit access)
**Bead**: `xkhn`
**Input**: `ghl_real_estate_ai/agents/jorge_seller_bot.py`, `lead_bot.py`
**Output**: Aligned question flow (4-question quick vs 10-question full)

**Tasks**:
1. Read current lead_bot.py and seller_bot.py question flows
2. Document the current state: which bot has 4 questions, which has 10
3. Identify the design intent (Upwork spec says 10-question qualification)
4. Implement dual-mode flow:
   - **Quick mode** (4 questions): For warm leads / handoff from other bots
   - **Full mode** (10 questions): For cold leads entering directly
5. Add mode selection logic based on lead source/temperature
6. Ensure all existing tests still pass
7. Update any related test files

**Success Criteria**: Both modes work, tests pass, no regression.

---

### Stream 6: PyPI Publishing Prep (P1 — Distribution)

**Agent**: `devops-infrastructure`
**Bead**: `kbtp`
**Input**: docqa-engine repo, insight-engine repo
**Output**: Publish-ready packages with automation script

**Tasks**:
1. Verify `pyproject.toml` for both packages:
   - Package name (no conflicts on PyPI)
   - Version, description, author, license
   - Dependencies listed correctly
   - Entry points / CLI commands if any
2. Verify package structure (src layout vs flat)
3. Run `python -m build` dry-run equivalent (check setup)
4. Check for PyPI name availability (`docqa-engine`, `insight-engine`)
5. Create `PYPI_PUBLISH_SCRIPT.sh`:
   ```bash
   cd /path/to/docqa-engine && python -m build && twine upload dist/*
   cd /path/to/insight-engine && python -m build && twine upload dist/*
   ```
6. Verify README renders correctly as PyPI long_description
7. Output: Ready-to-run publish script + any fixes needed

**Success Criteria**: Running the script publishes both packages (needs PyPI token from human).

---

### Stream 7: Platform Profile Expansion (P2 — Channel Diversification)

**Agent**: `platform-profile-optimizer`
**Bead**: `ty1t` (Contra signup)
**Input**: `~/.claude/reference/freelance/platform-profiles.md`, `skills-certs.md`
**Output**: Ready-to-paste profiles for 3 new platforms

**Tasks**:
1. Generate Contra profile (0% commission — high priority):
   - Bio, skills, portfolio items, rates, availability
2. Generate Toptal profile application:
   - Technical depth emphasis (8,500 tests, production metrics)
   - Algorithm/system design prep notes
3. Optimize current Upwork profile:
   - Enhance overview with latest metrics and portfolio evidence
   - Suggest 3 additional portfolio items to add
   - Recommend skill endorsements to prioritize
4. Generate a unified "elevator pitch" (30 seconds) usable across all platforms
5. Output: `PLATFORM_PROFILES_READY.md` with per-platform sections

**Success Criteria**: Copy-paste ready profiles for Contra + Toptal + Upwork improvements.

---

## Dependency Map

```
Stream 1 (Gumroad)      ──→ Human uploads to Gumroad
Stream 2 (Streamlit)     ──→ Human deploys via Streamlit Cloud ──→ Stream 3 gets live URLs
Stream 3 (Outreach)      ──→ Human sends emails (after Stream 2 URLs ready)
Stream 4 (Content)       ──→ Human posts via Chrome ext / manual
Stream 5 (Jorge Code)    ──→ Code merged (no human dependency beyond review)
Stream 6 (PyPI)          ──→ Human runs publish script with PyPI token
Stream 7 (Profiles)      ──→ Human signs up on platforms + pastes profiles
```

**Key**: Streams 1-7 run fully in parallel. Human actions happen AFTER all streams complete.

---

## Agent Configuration

| Stream | Agent Type | Model | Mode | Max Turns |
|--------|-----------|-------|------|-----------|
| 1 | content-marketing-engine | sonnet | bypassPermissions | 25 |
| 2 | devops-infrastructure | sonnet | bypassPermissions | 20 |
| 3 | outreach-personalizer | sonnet | bypassPermissions | 25 |
| 4 | content-marketing-engine | sonnet | bypassPermissions | 20 |
| 5 | general-purpose | sonnet | default | 30 |
| 6 | devops-infrastructure | sonnet | bypassPermissions | 20 |
| 7 | platform-profile-optimizer | sonnet | bypassPermissions | 20 |

**Why Sonnet**: Cost-efficient for content generation and config verification. Opus reserved for team lead orchestration.

---

## Human Action Checklist (Post-Agent)

After all 7 streams complete, execute in this order (~30 min total):

### Immediate (Revenue-Generating)
- [ ] **Gumroad**: Upload 21 products using Stream 1 manifest (~15 min)
- [ ] **Streamlit**: Deploy 3 apps using Stream 2 guide (~5 min)
- [ ] **Update outreach emails**: Replace demo URL placeholders with live Streamlit URLs

### Same Day
- [ ] **Cold Outreach**: Send Batch 1 (10 emails) from Stream 3 output
- [ ] **LinkedIn**: Post Week 2 content from Stream 4 output via Chrome ext
- [ ] **PyPI**: Run publish script from Stream 6 with your PyPI token

### This Week
- [ ] **Fiverr**: Upload photo, create account, list 3 gigs (needs human)
- [ ] **Contra**: Sign up + paste profile from Stream 7
- [ ] **Upwork**: Buy 80 Connects ($12), update profile per Stream 7 recommendations

---

## Bead Updates (On Completion)

```bash
# Close after agent work completes:
bd close EnterpriseHub-cfoc   # Gumroad products packaged
bd close EnterpriseHub-oom6   # Streamlit configs verified
bd close EnterpriseHub-5sd4   # Outreach batch ready
bd close EnterpriseHub-mdmf   # LinkedIn content ready
bd close EnterpriseHub-xkhn   # Jorge question flow fixed
bd close EnterpriseHub-kbtp   # PyPI packages ready
bd close EnterpriseHub-ty1t   # Contra profile ready

# Close stale in-progress items if resolved:
bd close EnterpriseHub-ruzg   # Fiverr gigs (content done, needs human upload)
bd close EnterpriseHub-rryk   # Seller pricing objection (if addressed in Stream 5)

bd sync
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Gumroad products live | 21 listings + 3 bundles |
| Streamlit apps deployed | 3 live URLs |
| Cold emails sent | 10 (Batch 1) |
| LinkedIn posts scheduled | 3 (Week 2) |
| Cross-platform content | 3 pieces (Dev.to, Reddit, HN) |
| PyPI packages published | 2 (docqa-engine, insight-engine) |
| New platform profiles | 2 (Contra, Toptal) |
| Jorge bot modes working | 2 (quick + full qualification) |
| Beads closed | 7-9 |

## Expected Revenue Impact (30 days post-execution)

| Channel | Conservative | Optimistic |
|---------|-------------|------------|
| Gumroad (21 products) | $500 | $2,000 |
| Cold outreach (10 prospects) | $1,000 | $5,000 |
| Fiverr (3 gigs) | $300 | $1,200 |
| Upwork (proposals) | $500 | $2,000 |
| **Total** | **$2,300** | **$10,200** |
