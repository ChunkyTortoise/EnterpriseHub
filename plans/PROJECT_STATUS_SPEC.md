# Project Status Spec — ChunkyTortoise Portfolio

**Date**: February 9, 2026
**Author**: Claude Code (Opus 4.6)
**Purpose**: Comprehensive snapshot of portfolio state, remaining work, content assets, and blockers.

---

## 1. Portfolio Overview

**11 repositories, all CI green, ~7,243 tests across portfolio.**

| Repo | Tests | Key Tech | Streamlit Demo | CI |
|------|-------|----------|----------------|----|
| **EnterpriseHub** | ~4,937 | FastAPI, Claude AI, PostgreSQL, Redis, CRM adapters (GHL/HubSpot/Salesforce), chatbot widget | ct-enterprise-ai.streamlit.app | Green |
| **jorge_real_estate_bots** | 279 | FastAPI, Claude AI, PostgreSQL | — | Green |
| **ai-orchestrator** (AgentForge) | 289 | httpx, async, Click CLI, tools, tracing, viz, REST API, ReAct agent, eval framework, model registry | ct-agentforge.streamlit.app (pending) | Green |
| **Revenue-Sprint** | 240 | Claude AI, SQLite, Click CLI | — | Green |
| **insight-engine** | 405 | Streamlit, scikit-learn, forecasting, clustering, model observatory, statistical tests, KPI framework, dimensionality reduction | ct-insight-engine.streamlit.app | Green |
| **docqa-engine** | 382 | BM25, TF-IDF, chunking, citation scoring, REST API, demo mode, re-ranker, query expansion, answer quality | ct-document-engine.streamlit.app | Green |
| **scrape-and-serve** | 236 | BeautifulSoup, httpx, scheduler, SEO, validators | ct-scrape-and-serve.streamlit.app | Green |
| **mcp-toolkit** | 158 | FastMCP v2, Click CLI, GitPython | ct-mcp-toolkit.streamlit.app | Green |
| **prompt-engineering-lab** | 127 | Prompt patterns, A/B testing, optimizer, token counter | — (pending) | Green |
| **llm-integration-starter** | 149 | Mock LLM, streaming, circuit breaker, fallback chains, caching | — (pending) | Green |
| **chunkytortoise.github.io** | — | Tailwind CSS, GitHub Pages portfolio site | — | Green |

### Beads Tracker
- **Total**: 184 beads
- **Closed**: 179 (97.3%)
- **Open**: 5 (all human-action items, no dev work remaining)
- **Avg lead time**: 0.6 hours

---

## 2. Remaining Work (5 Open Beads)

### Bead `qaiq` — P0 — Fiverr: Create seller account + list 3 gigs

| Field | Value |
|-------|-------|
| **Priority** | P0 (Critical) |
| **Blocker** | Profile photo upload required to pass onboarding step 0 |
| **Est. time** | 30 min after photo upload |

**Content files**:
- `content/fiverr/gig1-rag-qa-system.md` — RAG Q&A System gig ($100-$500)
- `content/fiverr/gig2-ai-chatbot.md` — AI Chatbot gig ($150-$600)
- `content/fiverr/gig3-data-dashboard.md` — Data Dashboard gig ($75-$300)
- `content/fiverr/seller-profile.md` — Seller profile copy

**Steps**:
1. Upload profile photo on Fiverr
2. Click Continue past onboarding wizard
3. Create 3 gigs using content from the files above
4. Set pricing tiers per each gig file
5. Publish all 3 gigs

---

### Bead `4j2` — P2 — Upwork: Buy Connects + submit Round 2 proposals

| Field | Value |
|-------|-------|
| **Priority** | P2 (Medium) |
| **Blocker** | $12 budget for 80 Connects |
| **Est. time** | 20 min after purchase |

**Content files**:
- `plans/archive/job-search/UPWORK_PROPOSALS_FEB8_ROUND2.md` — 5 drafted proposals
- `content/upwork-profile-improvements.md` — Profile refresh content

**Targets**: Semantic RAG, Education RAG, RAG Debugging, Modular AI Platform, Support Chatbot

**Steps**:
1. Go to Upwork > Settings > Membership > Buy Connects ($0.15/ea x 80 = $12)
2. Open each job listing from the proposals file
3. Paste personalized proposal from the drafts
4. Submit all 5 proposals

---

### Bead `9je` — P2 — LinkedIn: Send 3-5 recommendation requests

| Field | Value |
|-------|-------|
| **Priority** | P2 (Medium) |
| **Blocker** | None |
| **Est. time** | 15 min |

**Content files**:
- `plans/archive/linkedin/LINKEDIN_RECOMMENDATION_REQUESTS.md` — 5 templates (colleague, client, mentor, peer, open-source)

**Steps**:
1. Open LinkedIn > Messaging
2. For each contact, copy the relevant template from the file
3. Replace bracket placeholders with real names/projects
4. Send message

---

### Bead `pbz` — P3 — LinkedIn: Weekly content + daily engagement cadence

| Field | Value |
|-------|-------|
| **Priority** | P3 (Low) |
| **Blocker** | None (ongoing cadence) |
| **Est. time** | ~25 min/day ongoing |

**Content files**:
- `plans/archive/linkedin/LINKEDIN_POSTS_DRAFT.md` — Week 1 posts (Mon/Tue/Thu)
- `plans/archive/linkedin/LINKEDIN_POSTS_WEEK2.md` — Week 2 posts
- `plans/archive/linkedin/LINKEDIN_DELIVERABLE.md` — 3 education entries
- `plans/archive/linkedin/LINKEDIN_OPTIMIZATION_SPEC_FEB_2026.md` — Full optimization spec
- `content/REDDIT_POST_NOW.md` — Ready-to-post Reddit content
- `content/reddit/` — Additional Reddit posts
- `content/social/hn-show-agentforge.md` — HN Show post

**Daily cadence**: 3-5 comments on relevant posts, 10-20 targeted connection requests

---

### Bead `vp9` — P3 — Upwork: Complete remaining profile improvements

| Field | Value |
|-------|-------|
| **Priority** | P3 (Low) |
| **Blocker** | None |
| **Est. time** | 45 min |

**Content files**:
- `content/upwork-profile-improvements.md` — Full profile refresh content
- `content/upwork-video-script.md` — Video intro script

**Checklist**:
1. Set contract-to-hire preference
2. Complete Working Style Assessment
3. Record video intro (use script from file)
4. Connect GitHub account (Settings > Connected Services)
5. Add 5 portfolio items with live demo URLs
6. Update 15 skill tags
7. Replace profile summary with content from file

---

## 3. Content Asset Inventory

### Fiverr (4 files in `content/fiverr/`)
| File | Description |
|------|-------------|
| `gig1-rag-qa-system.md` | RAG Q&A System gig — $100-$500 |
| `gig2-ai-chatbot.md` | AI Chatbot gig — $150-$600 |
| `gig3-data-dashboard.md` | Data Dashboard gig — $75-$300 |
| `seller-profile.md` | Seller profile copy |

### Gumroad (5 files in `content/gumroad/`)
| File | Description |
|------|-------------|
| `product1-docqa-engine.md` | DocQA Engine — $49+ |
| `product2-agentforge.md` | AgentForge — $39+ |
| `product3-scrape-and-serve.md` | Web Scraper — $29+ |
| `product4-insight-engine.md` | Data Intelligence Dashboard — $39+ |
| `seller-profile.md` | Gumroad seller profile copy |

### LinkedIn (7 files in `plans/archive/linkedin/`)
| File | Description |
|------|-------------|
| `LINKEDIN_POSTS_DRAFT.md` | Week 1 posts (Mon/Tue/Thu) |
| `LINKEDIN_POSTS_WEEK2.md` | Week 2 posts |
| `LINKEDIN_DELIVERABLE.md` | 3 education entries |
| `LINKEDIN_RECOMMENDATION_REQUESTS.md` | 5 recommendation request templates |
| `LINKEDIN_OPTIMIZATION_SPEC_FEB_2026.md` | Full profile optimization spec |
| `LINKEDIN_AGENT_PROMPT.md` | Agent prompt for LinkedIn automation |
| `LINKEDIN_SPRINT_FEB7.md` | Sprint planning doc |

### Reddit (5 files in `content/reddit/` + `content/REDDIT_POST_NOW.md`)
| File | Description |
|------|-------------|
| `content/REDDIT_POST_NOW.md` | Ready-to-post Reddit content |
| `content/reddit/r_python_post.md` | r/Python post |
| `content/reddit/r_sideproject_post.md` | r/SideProject post |
| `content/reddit/engagement_templates.md` | Comment/engagement templates |
| `content/reddit/CAMPAIGN_EXECUTION_GUIDE.md` | Full campaign execution guide |

### Social / Cross-Platform (5 files in `content/social/`)
| File | Description |
|------|-------------|
| `reddit-post1-11-repos.md` | "11 Repos in 5 Days" post |
| `reddit-post2-rag-pipeline.md` | RAG Pipeline post |
| `reddit-python-langchain.md` | Python/LangChain alternative post |
| `reddit-ml-rag.md` | ML + RAG post |
| `hn-show-agentforge.md` | Hacker News Show HN post |

### Cold Outreach (3 files in `content/outreach/`)
| File | Description |
|------|-------------|
| `TARGET_RESEARCH.md` | 30 outreach targets with contact info |
| `EMAIL_SEQUENCE.md` | 3 email templates (initial, follow-up, final) |
| `CAMPAIGN_TRACKER.md` | Tracking spreadsheet template |

### Upwork (2 files + 5 archived)
| File | Description |
|------|-------------|
| `content/upwork-profile-improvements.md` | Full profile refresh content |
| `content/upwork-video-script.md` | Video intro script |
| `plans/archive/job-search/UPWORK_PROPOSALS_FEB8_ROUND2.md` | 5 Round 2 proposal drafts |
| `plans/archive/job-search/UPWORK_PROPOSALS_FEB8.md` | Round 1 proposals |
| `plans/archive/job-search/UPWORK_PROPOSAL_TEMPLATES.md` | Reusable proposal templates |
| `plans/archive/job-search/JOB_LISTINGS_FEB7.md` | Job listings snapshot |
| `plans/archive/job-search/COVER_LETTERS_FEB7.md` | Cover letter drafts |

### Dev.to Articles (4 files in `content/devto/`)
| File | Description |
|------|-------------|
| `article1-production-rag.md` | "Building a Production RAG System" |
| `article2-replaced-langchain.md` | "I Replaced LangChain" |
| `article3-csv-dashboard.md` | "CSV to Dashboard" |
| `article3-csv-to-dashboard.md` | Alternate version |

### GitHub Sponsors (3 files in `content/github-sponsors/`)
| File | Description |
|------|-------------|
| `TIERS.md` | Sponsorship tier definitions |
| `SPONSORS_SECTION.md` | README sponsors section |
| `SETUP.md` | Setup instructions |

### Product Hunt (1 file in `content/producthunt/`)
| File | Description |
|------|-------------|
| `agentforge-launch.md` | AgentForge launch copy |

### Streamlit Deployment
| File | Description |
|------|-------------|
| `content/streamlit_cloud_deployment.md` | Streamlit Cloud deployment guide |

### Other
| File | Description |
|------|-------------|
| `content/LAUNCH_ACTION_GUIDE.md` | Master launch action guide |
| `plans/PLATFORM_PROFILES.md` | Freelancer, Toptal, Arc.dev, Contra profile content |
| `plans/KIALASH_CALL_PREP.md` | Call prep doc for Feb 10 interview |
| `plans/WAVE2_QUICK_DEPLOY.md` | Wave 2 deployment plan |
| `plans/WAVE2_DEPLOY_NOW.md` | Immediate deployment steps |

---

## 4. Job Pipeline Status

### Active Conversations
| # | Company | Role | Platform | Status | Rate |
|---|---------|------|----------|--------|------|
| 1 | FloPro Jamaica (Chase) | AI Secretary SaaS | Upwork | Awaiting contract offer | $75/hr |
| 2 | Kialash Persad | Sr AI Agent Eng | Upwork | **Call Tue Feb 10, 4 PM EST** | TBD |

**Call prep**: `plans/KIALASH_CALL_PREP.md`

### Pending Applications
| # | Company | Role | Platform | Status | Rate |
|---|---------|------|----------|--------|------|
| 3 | Code Intelligence | RAG/LLM Engineer | Upwork | Viewed by client | $500 fixed |
| 4 | Concourse | Founding AI/ML | WorkAtAStartup | Signup form filled, needs password | $150K-$250K |
| 10 | Prompt Health | Sr AI Engineer | Ashby | Submitted | $160K-$220K |
| 11 | Rula | Principal AI Eng | Ashby | Submitted | $229K-$284K |

### Round 2 Targets (Blocked by Connects)
| # | Role | Rate |
|---|------|------|
| 5 | Semantic RAG | $55-65/hr |
| 6 | Education RAG | $55-65/hr |
| 7 | RAG Debugging | $55-65/hr |
| 8 | Modular AI Platform | $55-65/hr |
| 9 | Support Chatbot | $55-65/hr |

---

## 5. Blockers & Dependencies

| Blocker | Affects | Resolution |
|---------|---------|------------|
| **Fiverr profile photo** | Bead `qaiq` — cannot complete onboarding without it | Upload any professional headshot |
| **$12 for Upwork Connects** | Bead `4j2` — cannot submit Round 2 proposals | Settings > Membership > Buy Connects |
| **Gumroad bank account** | 4 products cannot publish | Settings > Payments > Connect bank |
| **Streamlit deploy URLs** | Cold outreach needs live demo links in emails | Deploy 3 apps to Streamlit Cloud |
| **Concourse password** | YC application stalled at signup | Enter password, fill profile, submit |
| **Updated portfolio links** | Platform profiles need live demo URLs | Deploy first, then update profiles |

### Dependency Chain
```
Deploy Streamlit apps
  └── Cold outreach campaign (needs live URLs)
  └── Platform profiles (needs portfolio links)
  └── Gumroad product descriptions (needs demo links)

Upload Fiverr photo
  └── Complete Fiverr onboarding
  └── Create 3 gigs

Buy Upwork Connects ($12)
  └── Submit 5 Round 2 proposals

Connect Gumroad bank account
  └── Publish 4 products
```

---

## 6. Recommended Execution Order

### Tier 1: No Blockers (Do Now)
| Action | Time | Content File |
|--------|------|-------------|
| Post to Reddit (r/Python, r/SideProject) | 10 min | `content/REDDIT_POST_NOW.md`, `content/reddit/` |
| Send LinkedIn recommendation requests | 15 min | `plans/archive/linkedin/LINKEDIN_RECOMMENDATION_REQUESTS.md` |
| Publish LinkedIn posts (Week 1) | 10 min | `plans/archive/linkedin/LINKEDIN_POSTS_DRAFT.md` |
| Upwork profile improvements | 45 min | `content/upwork-profile-improvements.md` |
| Post to HN (Show HN: AgentForge) | 5 min | `content/social/hn-show-agentforge.md` |
| Post to Dev.to | 15 min | `content/devto/article1-production-rag.md` |

### Tier 2: After Photo Upload (1 Blocker)
| Action | Time | Content File |
|--------|------|-------------|
| Complete Fiverr onboarding + create 3 gigs | 30 min | `content/fiverr/` (4 files) |

### Tier 3: After Budget ($12)
| Action | Time | Content File |
|--------|------|-------------|
| Buy 80 Upwork Connects | 2 min | — |
| Submit 5 Round 2 proposals | 20 min | `plans/archive/job-search/UPWORK_PROPOSALS_FEB8_ROUND2.md` |

### Tier 4: After Bank Account Connected
| Action | Time | Content File |
|--------|------|-------------|
| Publish 4 Gumroad products | 15 min | `content/gumroad/` (5 files) |

### Tier 5: After Streamlit Deploys
| Action | Time | Content File |
|--------|------|-------------|
| Launch cold outreach campaign | 30 min | `content/outreach/` (3 files) |
| Create platform profiles | 20 min | `plans/PLATFORM_PROFILES.md` |
| Product Hunt launch | 15 min | `content/producthunt/agentforge-launch.md` |
| Set up GitHub Sponsors | 15 min | `content/github-sponsors/` (3 files) |

### Ongoing (Daily)
| Action | Time | Content File |
|--------|------|-------------|
| LinkedIn engagement (comments + connections) | 25 min/day | `plans/archive/linkedin/LINKEDIN_OPTIMIZATION_SPEC_FEB_2026.md` |
| LinkedIn Week 2+ posts | 10 min/post | `plans/archive/linkedin/LINKEDIN_POSTS_WEEK2.md` |

---

## Appendix: Key Commits (Recent)

| Date | Repo | Commit | Description |
|------|------|--------|-------------|
| Feb 9 | ai-orchestrator | `400231e` | ReAct agent, eval framework, model registry (+75 tests) |
| Feb 9 | docqa-engine | `0f61c4f` | Re-ranker, query expansion, answer quality (+60 tests) |
| Feb 9 | insight-engine | `41a85a7` | Statistical tests, KPI framework, dim reduction (+92 tests) |
| Feb 9 | EnterpriseHub | `81f3c4b` | Salesforce CRM adapter with OAuth 2.0 (+29 tests) |
| Feb 8 | EnterpriseHub | `2c24703` | Chatbot widget, CRM adapter tests (+91 tests) |
| Feb 8 | llm-integration-starter | `fcc1aa9` | Edge-case tests (+44 tests) |
| Feb 8 | mcp-toolkit | — | Edge-case tests across 7 modules (+88 tests) |
