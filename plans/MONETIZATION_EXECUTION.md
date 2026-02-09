# Monetization Execution Spec — Parallel Agent Workstreams

**Status**: Ready to execute | **Created**: 2026-02-08
**Prereq**: `plans/MONETIZATION_SPEC.md` (all copy, pricing, templates ready)
**Constraint**: $0 budget. All work is code/content creation agents can do.

---

## Architecture: 6 Parallel Workstreams

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MONETIZATION EXECUTION                           │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ WS1:     │  │ WS2:     │  │ WS3:     │  │ WS4:     │          │
│  │ Portfolio │  │ Gumroad  │  │ Content  │  │ Streamlit│          │
│  │ Site     │  │ Packaging│  │ Marketing│  │ Deploy   │          │
│  │ Updates  │  │ (4 repos)│  │ Drafts   │  │ Prep     │          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
│       │              │              │              │                │
│       ▼              ▼              ▼              ▼                │
│  ┌──────────────────────────────────────────────────────┐          │
│  │          WS5: Alternative Platform Profiles           │          │
│  │          (depends on WS1 for updated links)           │          │
│  └───────────────────────┬──────────────────────────────┘          │
│                          ▼                                          │
│  ┌──────────────────────────────────────────────────────┐          │
│  │          WS6: Cold Outreach Prep                      │          │
│  │          (depends on WS1 + WS2 for live links)        │          │
│  └──────────────────────────────────────────────────────┘          │
│                                                                     │
│  ════════════════════════════════════════════════════════           │
│  HUMAN ACTIONS (after agents finish):                               │
│  1. Create Gumroad account → upload ZIPs from WS2                  │
│  2. Create Fiverr account → paste gig copy from MONETIZATION_SPEC  │
│  3. Deploy 3 Streamlit apps (configs from WS4)                     │
│  4. Push portfolio site changes from WS1                           │
│  5. Post content from WS3 to Reddit/HN/Dev.to                     │
│  6. Send cold emails from WS6                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Dependency Graph
```
WS1 (Portfolio Site) ───┐
WS2 (Gumroad Packaging) ├──→ WS5 (Platform Profiles) ──→ WS6 (Cold Outreach)
WS3 (Content Marketing) ┘         (needs links)            (needs everything)
WS4 (Streamlit Prep) ─────────→ (independent, human deploys after)
```

**WS1-WS4 run fully in parallel. WS5 after WS1. WS6 after WS1+WS2.**

---

## WS1: Portfolio Site Updates

**Agent**: general-purpose (code edits across HTML files)
**Repo**: `chunkytortoise.github.io`
**Estimated tasks**: 7 file edits

### Tasks

| # | File | Change | Details |
|---|------|--------|---------|
| 1.1 | `index.html` | Update hero stats | "5,300+" → "7,000+" tests |
| 1.2 | `index.html` | Update meta description | Match new test count |
| 1.3 | `projects.html` | Update all test counts | EnterpriseHub: 4,937, docqa: 322, insight: 313, scrape: 236, mcp: 158, ai-orch: 214, jorge: 279, revenue: 240, prompt-lab: 127, llm-starter: 149 |
| 1.4 | `projects.html` | Update total test badge | "5,300+" → "7,000+" |
| 1.5 | `services.html` | Add "Starter Kits" section | New section after existing services with 4 Gumroad product cards (use placeholder `[GUMROAD_LINK]` — human fills after account creation) |
| 1.6 | `services.html` | Update repo count in CTA | "8 public repos" → "11 public repos" |
| 1.7 | `services.html` | Add Fiverr to footer CTA | Add "Fiverr" link alongside existing Upwork link (use placeholder `[FIVERR_PROFILE]`) |

### Acceptance Criteria
- [ ] All test counts match MONETIZATION_SPEC numbers
- [ ] Starter Kits section renders with 4 cards matching Tailwind design system
- [ ] No broken links (placeholders are OK — marked clearly)
- [ ] `git diff` shows only intended changes

---

## WS2: Gumroad Product Packaging

**Agent**: 4 parallel sub-agents (one per repo), general-purpose
**Repos**: `docqa-engine`, `ai-orchestrator`, `scrape-and-serve`, `insight-engine`
**Estimated tasks**: 8 files (2 per repo)

### Per-Repo Tasks

For **each** of the 4 repos, create these 2 files:

#### CUSTOMIZATION.md (this is the value-add over free GitHub clone)

| # | Repo | File | Content Focus |
|---|------|------|---------------|
| 2.1 | docqa-engine | `CUSTOMIZATION.md` | How to: add your own documents, swap embedding model, change chunking strategy, add auth to API, deploy to Railway/Render, customize Streamlit theme |
| 2.2 | ai-orchestrator | `CUSTOMIZATION.md` | How to: add a new LLM provider, customize retry/rate-limit config, add function calling tools, integrate into existing FastAPI app, deploy CLI as package |
| 2.3 | scrape-and-serve | `CUSTOMIZATION.md` | How to: define new scraper targets (YAML), set price alert thresholds, add custom validators, schedule recurring scrapes, deploy monitoring dashboard |
| 2.4 | insight-engine | `CUSTOMIZATION.md` | How to: add custom chart types, configure attribution models for your channels, add new ML models, customize PDF report template, deploy for team use |

#### DEMO_MODE.md (prove it works without API keys)

| # | Repo | File | Content Focus |
|---|------|------|---------------|
| 2.5 | docqa-engine | `DEMO_MODE.md` | Steps to run with TF-IDF (no OpenAI), sample documents included, expected output screenshots |
| 2.6 | ai-orchestrator | `DEMO_MODE.md` | Steps to run with MockProvider, all tests pass without API keys, example CLI commands |
| 2.7 | scrape-and-serve | `DEMO_MODE.md` | Steps to run with sample YAML configs, cached sample data, no live scraping needed |
| 2.8 | insight-engine | `DEMO_MODE.md` | Steps to run with included sample CSVs, all features work with demo data |

### Acceptance Criteria
- [ ] Each CUSTOMIZATION.md is 200-400 lines with code examples
- [ ] Each DEMO_MODE.md has step-by-step instructions a junior dev can follow
- [ ] No references to private/internal tools or services
- [ ] Files committed to each repo's main branch

---

## WS3: Content Marketing Drafts

**Agent**: general-purpose (writing)
**Output**: `plans/content/` directory with ready-to-post drafts
**Estimated tasks**: 7 content pieces

### Tasks

| # | Platform | File | Content |
|---|----------|------|---------|
| 3.1 | Dev.to | `plans/content/devto_rag_without_vector_db.md` | "Building a RAG Pipeline Without a Vector Database" — 1500-2000 words, code snippets from docqa-engine, link to live demo + Gumroad |
| 3.2 | Dev.to | `plans/content/devto_replace_langchain.md` | "Why I Replaced LangChain with 15KB of httpx" — 1500-2000 words, benchmarks, code comparison, link to AgentForge |
| 3.3 | Dev.to | `plans/content/devto_csv_to_dashboard.md` | "From CSV to Dashboard in 30 Seconds with Python" — 1500-2000 words, walkthrough with screenshots described, link to insight-engine |
| 3.4 | Reddit | `plans/content/reddit_portfolio_post.md` | r/Python + r/SideProject post — use template from MONETIZATION_SPEC, add personal narrative |
| 3.5 | Reddit | `plans/content/reddit_rag_post.md` | r/MachineLearning post — technical deep-dive on hybrid retrieval, use template from MONETIZATION_SPEC |
| 3.6 | HN | `plans/content/hn_show_agentforge.md` | Show HN post for AgentForge — use template from MONETIZATION_SPEC, refine |
| 3.7 | ProductHunt | `plans/content/producthunt_agentforge.md` | Product Hunt launch copy — tagline, description, maker comment, first comment |

### Acceptance Criteria
- [ ] Each Dev.to article is 1500+ words with code blocks
- [ ] All posts include live demo links and Gumroad placeholders
- [ ] Tone is authentic/technical, not salesy
- [ ] Reddit posts follow subreddit rules (no direct sales pitch)
- [ ] All files are markdown, ready to copy-paste

---

## WS4: Streamlit Deployment Prep

**Agent**: general-purpose (code verification + config)
**Repos**: `ai-orchestrator`, `prompt-engineering-lab`, `llm-integration-starter`
**Estimated tasks**: 9 checks/files

### Per-Repo Tasks

For **each** of the 3 repos:

| # | Task | Details |
|---|------|---------|
| 4.1-4.3 | Verify `app.py` entry point | Confirm the Streamlit app launches, has demo mode, doesn't crash without API keys |
| 4.4-4.6 | Verify/create `requirements.txt` | Must include all deps for Streamlit Cloud (streamlit, plotly, pandas, etc.) — no `torch` or other heavy deps that exceed 1GB limit |
| 4.7-4.9 | Verify/create `.streamlit/config.toml` | Match existing theme (indigo primary, dark background) |

### Acceptance Criteria
- [ ] Each repo has: `app.py`, `requirements.txt`, `.streamlit/config.toml`
- [ ] `streamlit run app.py` works locally with `DEMO_MODE=true`
- [ ] Requirements stay under Streamlit Cloud's 1GB limit
- [ ] Theme matches existing live demos (indigo/dark)

---

## WS5: Alternative Platform Profile Drafts

**Agent**: general-purpose (writing)
**Depends on**: WS1 (needs updated portfolio links)
**Output**: `plans/profiles/` directory
**Estimated tasks**: 4 platform profiles

### Tasks

| # | Platform | File | Content |
|---|----------|------|---------|
| 5.1 | Freelancer.com | `plans/profiles/freelancer_profile.md` | Title, headline, bio (500 chars), skills list, portfolio description, hourly rate ($65-85). Emphasize: 7K tests, live demos, MIT repos |
| 5.2 | Toptal | `plans/profiles/toptal_application.md` | Application answers: background, specialties, notable projects (3), why Toptal. Emphasize: production AI systems, not toy projects |
| 5.3 | Arc.dev | `plans/profiles/arcdev_profile.md` | Profile: bio, tech stack, work samples (link to demos), availability, rate ($70-100/hr) |
| 5.4 | Contra.com | `plans/profiles/contra_profile.md` | Profile: bio, services offered (match Fiverr gigs), portfolio links, rates. Contra = no commission, good for higher-ticket |

### Acceptance Criteria
- [ ] Each profile draft is copy-paste ready (within platform character limits)
- [ ] All reference updated portfolio site URLs
- [ ] Skills/tech stack consistent across platforms
- [ ] Rates are consistent ($65-100/hr range)

---

## WS6: Cold Outreach Target Research + Personalization

**Agent**: general-purpose (web research + writing)
**Depends on**: WS1 + WS2 (needs live links for emails)
**Output**: `plans/outreach/` directory
**Estimated tasks**: 4 research + personalization tasks

### Tasks

| # | Task | File | Details |
|---|------|------|---------|
| 6.1 | Research 10 AI startup targets | `plans/outreach/targets_ai_startups.md` | From YC S25/W25 batch pages, Product Hunt AI launches. For each: company name, what they build, contact (CTO/founder name), email guess pattern, which demo to link |
| 6.2 | Research 10 agency targets | `plans/outreach/targets_agencies.md` | From Clutch.co "AI development" + "data analytics" agencies. For each: agency name, services, contact, which demo to link |
| 6.3 | Research 10 e-commerce targets | `plans/outreach/targets_ecommerce.md` | From LinkedIn/AngelList. Mid-size e-commerce companies that would benefit from price monitoring. For each: company, contact, which demo to link |
| 6.4 | Personalize 30 emails | `plans/outreach/personalized_emails.md` | Take the 3 templates from MONETIZATION_SPEC + 30 targets, produce 30 personalized first lines. One email per target, ready to send |

### Acceptance Criteria
- [ ] 30 real companies with real contact names
- [ ] Each target has: company, name, role, email pattern, relevant demo link
- [ ] Personalized first line references something specific about the company
- [ ] Emails use correct template (AI startup/agency/ecommerce)

---

## Execution Order

### Phase 1: Parallel (All at once)
```bash
# Launch 4 workstreams simultaneously
WS1: Portfolio Site Updates          # ~30 min agent time
WS2: Gumroad Packaging (4 repos)    # ~45 min agent time (4 parallel sub-agents)
WS3: Content Marketing Drafts       # ~60 min agent time
WS4: Streamlit Deploy Prep          # ~20 min agent time
```

### Phase 2: Sequential (After Phase 1)
```bash
WS5: Platform Profile Drafts        # ~20 min agent time (needs WS1 links)
```

### Phase 3: Sequential (After Phase 1+2)
```bash
WS6: Cold Outreach Research          # ~45 min agent time (needs WS1+WS2)
```

### Phase 4: Human Actions (After all agents finish)
```
[ ] 1. Review all agent output in plans/ directories
[ ] 2. Create Gumroad account → upload ZIPs → paste descriptions
[ ] 3. Create Fiverr account → paste gig descriptions
[ ] 4. Deploy 3 Streamlit apps on share.streamlit.io
[ ] 5. Push portfolio site changes (git push chunkytortoise.github.io)
[ ] 6. Fill in [GUMROAD_LINK] and [FIVERR_PROFILE] placeholders
[ ] 7. Create Freelancer.com / Toptal / Arc.dev / Contra accounts → paste profiles
[ ] 8. Post content to Reddit / HN / Dev.to
[ ] 9. Send 30 cold emails (10/day over 3 days)
```

---

## Agent Launch Commands

```bash
# Phase 1 — launch all 4 in parallel
Task WS1: "Update portfolio site test counts and add Starter Kits section"
Task WS2a: "Create CUSTOMIZATION.md + DEMO_MODE.md for docqa-engine"
Task WS2b: "Create CUSTOMIZATION.md + DEMO_MODE.md for ai-orchestrator"
Task WS2c: "Create CUSTOMIZATION.md + DEMO_MODE.md for scrape-and-serve"
Task WS2d: "Create CUSTOMIZATION.md + DEMO_MODE.md for insight-engine"
Task WS3: "Write 7 content marketing drafts (3 Dev.to, 2 Reddit, 1 HN, 1 PH)"
Task WS4: "Verify/fix Streamlit configs for 3 pending deployment repos"

# Phase 2 — after Phase 1 completes
Task WS5: "Draft profiles for Freelancer, Toptal, Arc.dev, Contra"

# Phase 3 — after Phase 2 completes
Task WS6: "Research 30 outreach targets and personalize cold emails"
```

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Portfolio site accuracy | 100% test counts match reality | Manual review |
| Gumroad products ready | 4 repos have CUSTOMIZATION.md + DEMO_MODE.md | File exists + review |
| Content pieces ready | 7 drafts in plans/content/ | File count + quality |
| Streamlit configs ready | 3 repos deployable | `streamlit run app.py` works |
| Platform profiles ready | 4 drafts in plans/profiles/ | File count + quality |
| Outreach targets ready | 30 personalized emails in plans/outreach/ | File count + quality |
| **Time to first dollar** | < 7 days after human actions | First Gumroad sale or Fiverr order |

---

## Revenue Impact (from MONETIZATION_SPEC)

| Channel | Month 1 | Month 2 |
|---------|---------|---------|
| Gumroad (4 products) | $195-390 | $390-780 |
| Fiverr (3 gigs) | $300-600 | $800-1,600 |
| Cold email (30 targets) | $1,000 | $3,000 |
| Alt platforms (4 profiles) | $0-500 | $500-2,000 |
| Content (7 posts) | indirect | $200-500 (leads) |
| **Total** | **$1,495-2,490** | **$4,890-7,880** |

---

*Execute Phase 1 now. Everything else follows.*
