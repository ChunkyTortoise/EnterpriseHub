# Freelance Growth Tooling Research

**Date**: 2026-02-14 | **Sources**: 3 research agents (plugins, MCP servers, custom agents/skills)

---

## SECTION 1: Plugins to Enable

Your `settings.json` shows these plugins are available but **disabled**:

| Plugin | Status | Relevance to Freelance Growth | Recommendation |
|--------|--------|-------------------------------|----------------|
| `playwright` | OFF | E2E testing demos, automated screenshots for Gumroad | **ENABLE** — product screenshots, demo recording |
| `stripe` | OFF | Subscription management, payment analytics | **ENABLE** — track Gumroad/Stripe revenue |
| `figma` | OFF | Design mockups for portfolio | LOW — not needed now |
| `asana` | OFF | Project management | LOW — using beads instead |
| `atlassian` | OFF | Jira/Confluence | LOW — not using Atlassian |
| `gitlab` | OFF | Git hosting | LOW — using GitHub |
| `supabase` | OFF | Database hosting | LOW — using Postgres MCP |
| `greptile` | OFF | Codebase search | LOW — already have Serena + Grep |
| `pinecone` | OFF | Vector DB | MEDIUM — could demo RAG capabilities |
| `hookify` | OFF | Hook management | LOW |
| `frontend-design` | OFF | UI/UX assistance | MEDIUM — portfolio site updates |

**Action**: Enable `playwright` and `stripe` plugins immediately.

---

## SECTION 2: MCP Servers to Add

### CRITICAL — Direct Revenue Impact

| Server | Package/Repo | What It Does | Freelance Growth Use |
|--------|-------------|--------------|---------------------|
| **Upwork** | `@chinchillaenterprises/mcp-upwork` | 12 tools: search jobs, manage proposals, track contracts, monitor earnings | **CRITICAL** — Automate job search + proposal tracking on your active platform |
| **Gumroad** | `keithah/gumroad-mcp` | Product data, sales, subscriptions, offer codes | **CRITICAL** — Manage 21 product listings, track revenue, customer data |
| **GoHighLevel** | `Funding-Machine/ghl-mcp` | Automate GHL across CRM, messaging, calendars, marketing | **Critical** — GHL is your #1 niche. Direct API integration for demos, case studies, marketplace app |
| **LinkedIn** | `adhikasp/mcp-linkedin` | LinkedIn feeds, job API, profile access, post creation | **Critical** — automate LinkedIn content posting, job search, connection management |
| **Zapier** | `zapier.com/mcp` (official) | Connect to 8,000 apps with 30,000+ actions | **Critical** — One connection replaces multiple individual MCP servers |
| **Google Calendar** | `nspady/google-calendar-mcp` | Event management, availability, scheduling | **High** — schedule client calls, manage availability for consulting |
| **HubSpot** | Official beta at `developers.hubspot.com/mcp` | CRM read access (contacts, deals, companies) | **High** — demo CRM integration capabilities to prospects |

### MEDIUM PRIORITY — Content, Community & Productivity

| Server | Package/Repo | What It Does | Freelance Growth Use |
|--------|-------------|--------------|---------------------|
| **Firecrawl** | `firecrawl/firecrawl-mcp-server` | AI-ready web scraping, clean JSON/Markdown output | Competitor research, SEO analysis, content strategy |
| **n8n** | Official at `docs.n8n.io/advanced-ai/` | Native MCP, workflow automation, self-hosted | Custom automation workflows for content/outreach |
| **Notion** | Official at `developers.notion.com/docs/mcp` | Read/write Notion pages | Content calendar, client deliverable tracking |
| **Google Sheets** | `xing5/mcp-google-sheets` | Create/modify spreadsheets, Drive integration | Revenue tracking, outreach campaign tracking |
| **Telegram** | `chigwell/telegram-mcp` | Read/send messages, manage groups | Community engagement, client communication |
| **X (Twitter)** | `mbelinky/x-mcp-server` | Post tweets, search, OAuth 2.0 | Content distribution, audience building |
| **Slack** | Official plugin (available, disabled) | Channel messaging, DMs, history | Client communication hub |
| **Fiverr Scraper** | `apify.com/piotrv1001/fiverr-listings-scraper/api/mcp` | Search/extract Fiverr gig data | Competitive analysis, pricing strategy |
| **Shopify** | Official at `shopify.dev/docs/apps/build/devmcp` | E-commerce integration | Demo e-commerce AI integration to prospects |

### LOWER PRIORITY — Future Expansion

| Server | Package/Repo | What It Does | Freelance Growth Use |
|--------|-------------|--------------|---------------------|
| **Explorium** | `Explorium-mcp-explorium` | Live B2B company/contact data | Cold outreach prospect research |
| **MailJunky** | MCP email server | Send/track emails | Cold outreach automation |
| **Discord** | `Danushkumar-V-mcp-discord` | Discord integration | Community management |
| **Slack** | Official plugin (available but disabled) | Slack messaging | Client communication |
| **Jira** | `@anthropic/jira-mcp` | Issue tracking | Client project management |

---

## SECTION 3: Custom Agents to Create

### You Already Have (Useful for Freelance)

| Agent | Location | Use in Freelance Growth |
|-------|----------|------------------------|
| `technical-proposal-writer` | `~/.claude/agents/` | **Directly useful** — Upwork proposals, client pitches |
| `project-scope-analyst` | `~/.claude/agents/` | **Directly useful** — Scoping client projects, estimates |
| `prompt-engineering-specialist` | `~/.claude/agents/` | Bot personality optimization, demo quality |
| `llm-cost-optimizer` | `~/.claude/agents/` | Cost reduction case studies |
| `data-pipeline-architect` | `~/.claude/agents/` | Client project architecture |
| `portfolio-coordinator` | `.claude/agents/` (project) | Cross-repo portfolio management |

### Agents to CREATE

#### 1. `content-marketing-engine` (P0)
**Purpose**: Multi-format content creation from a single topic
**Source**: [WomenDefiningAI/claudecode-writer](https://github.com/WomenDefiningAI/claudecode-writer)
**Workflow**: Research → long-form article → LinkedIn post → Dev.to article → newsletter → social media variants
**Tools**: Read, Write, Grep, WebSearch, WebFetch
**Why**: You need consistent content across 5+ platforms. This agent transforms one idea into 5+ content pieces.

```
Content input: "Sub-1ms SSE micro-batching in production"
Outputs:
  - LinkedIn post (300 words, engagement hooks)
  - Dev.to article (1,500 words, code samples)
  - Reddit post (r/Python, r/SaaS angles)
  - HN Show post (technical focus)
  - Gumroad product description angle
  - Cold email proof point
```

#### 2. `platform-profile-optimizer` (P0)
**Purpose**: Generate and optimize profiles for freelance platforms
**Workflow**: Read portfolio data → adapt messaging per platform → generate platform-specific profiles
**Tools**: Read, Write, Grep, WebSearch
**Why**: You need profiles for 6+ new platforms (A.Team, Toptal, Braintrust, Gun.io, Arc.dev, GHL Directory). Each has different formatting/requirements.

#### 3. `outreach-personalizer` (P1)
**Purpose**: Personalize cold outreach at scale
**Source**: MarketBetter.ai patterns + existing `content/outreach/` templates
**Workflow**: Read prospect data → research company → personalize template → generate email + LinkedIn InMail
**Tools**: Read, Write, Grep, WebSearch, WebFetch
**Why**: 30+ outreach targets need personalized emails. Claude's 200K context window can ingest entire LinkedIn profiles + company data for deep personalization.

#### 4. `market-research-analyst` (P1)
**Purpose**: Competitive analysis, pricing research, market sizing
**Source**: [dmend3z/market-research-plugins](https://www.claudepluginhub.com/plugins/dmend3z-market-research-plugins-market-research)
**Workflow**: Research competitors → analyze pricing → identify gaps → recommend positioning
**Tools**: Read, Write, WebSearch, WebFetch
**Why**: Ongoing need to validate pricing ($150+/hr positioning), find new GHL agencies, track market trends.

#### 5. `case-study-generator` (P2)
**Purpose**: Transform project metrics into compelling case studies
**Workflow**: Read repo metrics/benchmarks → structure narrative → generate multiple formats (long, short, visual)
**Tools**: Read, Write, Grep, Glob
**Why**: You have 11 repos with rich metrics but no case studies yet. This agent mines benchmarks, test counts, and architecture to produce client-facing narratives.

#### 6. `ghl-integration-specialist` (P2)
**Purpose**: GHL-specific development, marketplace apps, API integration
**Workflow**: Read GHL API docs → design integrations → build marketplace apps
**Tools**: Read, Write, Edit, Bash, WebFetch
**Why**: GHL ecosystem is your highest-value niche. Dedicated agent for GHL marketplace app development and community content.

---

## SECTION 4: Skills (Slash Commands) to Create

### From Community Research

Source: [wshobson/agents](https://github.com/wshobson/agents) (112 agents, 146 skills), [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills), [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)

### Skills to Create for `.claude/commands/`

| Skill | Command | What It Does | Priority |
|-------|---------|-------------|----------|
| `/draft-content` | Content drafting | Generate blog post, LinkedIn post, email, or case study from a topic + portfolio evidence | P0 |
| `/proposal` | Proposal generator | Generate Upwork/platform proposal from job posting URL (uses `technical-proposal-writer` agent) | P0 |
| `/outreach` | Cold email generator | Personalize outreach template for a specific prospect | P1 |
| `/platform-profile` | Profile generator | Generate platform-specific profile from master bio | P1 |
| `/audit-scorecard` | Client audit template | Generate "2026 AI Architecture Readiness" scorecard for a prospect | P1 |
| `/case-study` | Case study generator | Transform repo metrics into formatted case study | P2 |
| `/weekly-status` | Weekly status report | Summarize week's progress: revenue, content published, proposals sent, pipeline | P2 |
| `/ghl-teardown` | GHL architecture post | Generate GHL community post from Jorge Bot architecture | P2 |
| `/hn-post` | HN formatted post | Format content for "Show HN" or "Who Wants to Be Hired" | P3 |
| `/revenue-update` | Revenue tracker update | Update `revenue-tracker.md` with new transactions | P3 |

### Marketing Skills (from coreyhaines31/marketingskills)

Available at: https://github.com/coreyhaines31/marketingskills

| Skill | What It Does | Relevance |
|-------|-------------|-----------|
| CRO (Conversion Rate Optimization) | Landing page optimization, A/B test design | Gumroad product pages, portfolio site |
| Copywriting | Sales copy, headlines, CTAs | Product descriptions, outreach |
| SEO | Keyword research, content optimization | Dev.to articles, portfolio site |
| Analytics | Data interpretation, funnel analysis | Track content/outreach performance |
| Growth Engineering | Growth loops, viral mechanics | Product launch strategy |

### Content Research Writer Skill

Available at: [ComposioHQ/awesome-claude-skills/content-research-writer](https://github.com/ComposioHQ/awesome-claude-skills/blob/master/content-research-writer/SKILL.md)

Assists in writing high-quality content by conducting research, adding citations, improving hooks, and providing section-by-section feedback. Can be installed directly.

---

## SECTION 5: Installable Packages (Ready to Use)

### Marketing Skills — `coreyhaines31/marketingskills` (P0)
**Install**: `npx skills add coreyhaines31/marketingskills`
**25+ skills** including:
- **CRO**: `page-cro`, `signup-flow-cro`, `form-cro`, `paywall-upgrade-cro`
- **Content**: `copywriting`, `copy-editing`, `email-sequence`, `social-content`
- **SEO**: `seo-audit`, `programmatic-seo`, `competitor-alternatives`, `schema-markup`
- **Growth**: `free-tool-strategy`, `referral-program`, `marketing-ideas` (140+ strategies)
- **Strategy**: `pricing-strategy`, `launch-strategy`, `product-marketing-context`

### Agent Framework — `wshobson/agents` (P1)
**Install**: `git clone` to `~/.claude/agents/wh-bundle`
**112 agents + 73 plugins + 146 skills** including business agents:
- SEO & Content Specialist, Analytics Specialist, Customer/Sales Agent, Technical Writer

### Slash Commands — `wshobson/commands` (P1)
**Install**: Copy to `.claude/commands/`
**57 commands** including: `/feature-development`, `/deploy-checklist`, `/compliance-check`, `/monitor-setup`

### VoltAgent Business Suite — `voltagent-biz` (P1)
**Install**: `npx claude-plugin install voltagent-biz`
**Agents**: `content-marketer`, `product-manager`, `business-analyst`, `sales-engineer`, `ux-researcher`

### VoltAgent Research Suite — `voltagent-research` (P1)
**Install**: `npx claude-plugin install voltagent-research`
**Agents**: `market-researcher`, `competitive-analyst`, `trend-analyst`, `research-analyst`

### Content Writer Workspace — `WomenDefiningAI/claudecode-writer` (P2)
**Install**: `git clone`
**Pipeline**: Research → long-form article → LinkedIn → newsletter → social → podcast Q&A

---

## SECTION 6: Community Marketplaces

| Marketplace | URL | What It Offers |
|-------------|-----|---------------|
| **Claude Plugins Official** | Already installed | Anthropic-managed plugins |
| **ComposioHQ** | `github.com/ComposioHQ/awesome-claude-plugins` | connect-apps (500+ services), content tools |
| **ccplugins** | `github.com/ccplugins/awesome-claude-code-plugins` | Curated community plugins |
| **VoltAgent** | `github.com/VoltAgent/awesome-claude-code-subagents` | 100+ specialized subagents |
| **VoltAgent Skills** | `github.com/VoltAgent/awesome-agent-skills` | 300+ agent skills |
| **Claude Plugins Dev** | `claude-plugins.dev` | Community registry with CLI |
| **harrylowkey** | `github.com/harrylowkey/claude-code-plugins` | SEO content creation agents |
| **wshobson** | `github.com/wshobson/agents` | 112 agents, 146 skills, 79 tools |
| **WomenDefiningAI** | `github.com/WomenDefiningAI/claudecode-writer` | Multi-format content writer |

---

## SECTION 7: Prioritized Implementation Plan

### Phase 1: Quick Wins — Install Existing Packages (30 min)

1. Enable `playwright` and `stripe` plugins in `settings.json`
2. Install marketing skills: `npx skills add coreyhaines31/marketingskills` (25+ skills)
3. Add Upwork MCP: `@chinchillaenterprises/mcp-upwork`
4. Add Gumroad MCP: `keithah/gumroad-mcp`
5. Add LinkedIn MCP: `adhikasp/mcp-linkedin`
6. Add GHL MCP: `Funding-Machine/ghl-mcp`

### Phase 2: Install Agent Bundles (1 hour)

7. Install VoltAgent business suite: `npx claude-plugin install voltagent-biz`
8. Install VoltAgent research suite: `npx claude-plugin install voltagent-research`
9. Clone wshobson commands (57 slash commands) to `.claude/commands/`
10. Install content-research-writer skill from ComposioHQ

### Phase 3: Create Custom Agents (2-3 hours)

11. Create `content-marketing-engine` agent (topic → 5+ platform content pieces)
12. Create `platform-profile-optimizer` agent (master bio → platform profiles)
13. Create `outreach-personalizer` agent (prospect research → personalized email)
14. Create `case-study-generator` agent (repo metrics → client narrative)
15. Create `ghl-integration-specialist` agent (GHL marketplace + API)

### Phase 4: Create Custom Skills (2-3 hours)

16. `/draft-content` — Generate platform-specific content from topic
17. `/proposal` — Generate proposal from job posting (uses technical-proposal-writer)
18. `/outreach` — Personalize cold email for specific prospect
19. `/platform-profile` — Generate platform-specific profile from master bio
20. `/audit-scorecard` — Generate "2026 AI Architecture Readiness" scorecard
21. `/case-study` — Transform repo metrics into formatted case study

### Phase 5: Additional MCP Servers (1-2 hours)

22. Add Google Calendar MCP: `nspady/google-calendar-mcp`
23. Add Zapier MCP: `zapier.com/mcp` (connects 8,000 apps)
24. Add Firecrawl MCP: `firecrawl/firecrawl-mcp-server` (web scraping)
25. Add Google Sheets MCP: `xing5/mcp-google-sheets` (revenue tracking)

---

## Implementation Status (2026-02-14)

### Phase 1: DONE
- [x] Enabled `playwright` and `stripe` plugins
- [x] Installed 25 marketing skills (coreyhaines31/marketingskills)
- [x] Added Upwork, Gumroad, LinkedIn, GHL MCP servers
- [x] Generated Gumroad OAuth token via Chrome extension

### Phase 2: DONE (partial — skip VoltAgent)
- [x] VoltAgent packages (`voltagent-biz`, `voltagent-research`) — **DO NOT EXIST on npm** (hallucinated by research agent)
- [x] wshobson repos exist but contain generic boilerplate, not worth installing wholesale
- [x] Marketing skills already cover the useful functionality

### Phase 3: DONE
- [x] Created `content-marketing-engine` agent
- [x] Created `platform-profile-optimizer` agent
- [x] Created `outreach-personalizer` agent
- [x] Created `case-study-generator` agent
- [x] Created `ghl-integration-specialist` agent

### Phase 4: DONE
- [x] `/draft-content` — multi-format content from topic
- [x] `/proposal` — Upwork proposal from job posting
- [x] `/outreach` — personalized cold outreach sequence
- [x] `/platform-profile` — platform-specific profile generator
- [x] `/case-study` — repo metrics → case study
- [x] `/weekly-status` — weekly freelance progress report
- [x] `/audit-scorecard` — AI architecture readiness audit
- [x] `/revenue-update` — update revenue tracker
- [x] `/ghl-teardown` — GHL community architecture post

### Phase 5: DONE
- [x] Added Google Calendar MCP server
- [x] Added Firecrawl MCP server
- [x] Added Google Sheets MCP server
- [ ] Zapier MCP — no npm package, web-only access

### API Keys Still Needed
- [ ] `GHL_API_KEY` + `GHL_LOCATION_ID` — need GHL login → Settings → API
- [ ] `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` — Google Cloud Console
- [ ] `FIRECRAWL_API_KEY` — firecrawl.dev dashboard
- [ ] `GOOGLE_SHEETS_CLIENT_ID` + `GOOGLE_SHEETS_CLIENT_SECRET` — Google Cloud Console

---

## Key Sources

- [Anthropic Plugin Docs](https://code.claude.com/docs/en/discover-plugins)
- [Official Plugin Directory](https://github.com/anthropics/claude-plugins-official)
- [ComposioHQ Awesome Plugins](https://github.com/ComposioHQ/awesome-claude-plugins)
- [VoltAgent 100+ Subagents](https://github.com/VoltAgent/awesome-claude-code-subagents)
- [VoltAgent 300+ Skills](https://github.com/VoltAgent/awesome-agent-skills)
- [wshobson 112 Agents](https://github.com/wshobson/agents)
- [Marketing Skills](https://github.com/coreyhaines31/marketingskills)
- [Content Research Writer](https://github.com/ComposioHQ/awesome-claude-skills/blob/master/content-research-writer/SKILL.md)
- [Claude Code Writer](https://github.com/WomenDefiningAI/claudecode-writer)
- [GHL MCP](https://github.com/Funding-Machine/ghl-mcp)
- [LinkedIn MCP](https://github.com/adhikasp/mcp-linkedin)
- [Google Calendar MCP](https://github.com/nspady/google-calendar-mcp)
- [PulseMCP Directory](https://www.pulsemcp.com/servers)
- [Best MCP Servers 2026](https://www.builder.io/blog/best-mcp-servers-2026)
- [SEO Content Plugin](https://github.com/harrylowkey/claude-code-plugins)
