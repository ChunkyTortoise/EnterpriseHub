# Agent Swarm: Content Launch Campaign — Execution Spec

**Created**: 2026-02-09
**Status**: Executable
**Goal**: Publish pre-written content to Reddit, HN, Dev.to, and LinkedIn using parallel browser automation agents.

---

## Team: `content-launch` (3 agents + lead)

| Agent | Type | Browser Tool | Tasks |
|-------|------|-------------|-------|
| **team-lead** (main) | coordinator | None | Verification, bead tracking, spawn agents, collect results |
| **playwright-poster** | `general-purpose` | Playwright MCP | Reddit (2 posts + comments), HN (1 post), Dev.to (3 articles) |
| **chrome-poster** | `general-purpose` | Chrome Ext MCP | LinkedIn (3 Week 1 posts) |

---

## Execution Phases

### Phase 0: VERIFICATION (team-lead)
- [x] Read all 10 content files — verified present, no broken placeholders
- [ ] WebFetch `https://ct-agentforge.streamlit.app` (HN prerequisite)
- [ ] Create beads for tracking
- [ ] Spawn both browser agents

### Phase 1A: PLAYWRIGHT TRACK (sequential)

| Task | Content File | Platform |
|------|-------------|----------|
| T1.1 | `content/reddit/r_python_post.md` | r/Python |
| T1.2 | TL;DR from `content/reddit/CAMPAIGN_EXECUTION_GUIDE.md` §2.1 | r/Python comment |
| T1.3 | `content/reddit/r_sideproject_post.md` | r/SideProject |
| T1.4 | TL;DR from `content/reddit/CAMPAIGN_EXECUTION_GUIDE.md` §2.1 | r/SideProject comment |
| T1.5 | `content/social/hn-show-agentforge.md` | Hacker News |
| T1.6 | `content/devto/article1-production-rag.md` | Dev.to |
| T1.7 | `content/devto/article2-replaced-langchain.md` | Dev.to |
| T1.8 | `content/devto/article3-csv-dashboard.md` | Dev.to |

### Phase 1B: CHROME TRACK (sequential)

| Task | Content File | Platform |
|------|-------------|----------|
| T2.1 | Post 3 (Hot Take) from `plans/archive/linkedin/LINKEDIN_POSTS_DRAFT.md` | LinkedIn |
| T2.2 | Post 1 (Token Cost) from `plans/archive/linkedin/LINKEDIN_POSTS_DRAFT.md` | LinkedIn |
| T2.3 | Post 2 (Multi-Agent Handoff) from `plans/archive/linkedin/LINKEDIN_POSTS_DRAFT.md` | LinkedIn |

### Phase 2: WRAP-UP (team-lead)
- [ ] Collect all published post URLs
- [ ] Produce human handoff checklist
- [ ] Close beads, bd sync
- [ ] Shutdown team

---

## Browser Workflow Details

### Reddit (Playwright)
1. `browser_navigate` -> `reddit.com/r/{sub}/submit`
2. `browser_snapshot` -> verify logged in
3. Fill title + switch to markdown editor + paste body
4. Submit -> `browser_snapshot` -> capture post URL
5. Navigate to post -> add TL;DR comment
6. Report URL to team-lead

### HN (Playwright)
1. `browser_navigate` -> `news.ycombinator.com/submit`
2. Fill title: "Show HN: AgentForge -- Multi-LLM orchestrator in 15KB"
3. Fill URL: `https://github.com/ChunkyTortoise/ai-orchestrator`
4. Fill text from content file (body only)
5. Submit -> report URL

### Dev.to (Playwright)
1. `browser_navigate` -> `dev.to/new`
2. `browser_snapshot` -> verify logged in
3. Paste article with `published: true` in frontmatter
4. Verify tags set correctly
5. Click Publish -> capture article URL -> report

### LinkedIn (Chrome Extension)
1. `navigate` -> `linkedin.com/feed/`
2. `read_page` -> verify logged in
3. Click "Start a post" (ref-based click, NOT coordinates)
4. Paste post content from drafts
5. Add hashtags at end
6. Click Post (ref-based click)
7. `read_page` -> verify posted -> capture URL -> report

---

## Error Handling

| Error | Detection | Response |
|-------|-----------|----------|
| Site unreachable | Navigation timeout | Retry 3x, 15s delay; skip + log if all fail |
| Not logged in | Login page in snapshot | Screenshot -> flag for human auth -> skip task |
| CAPTCHA / anti-bot | Challenge detected | Screenshot -> skip immediately -> add to manual list |
| Post rejected (spam) | Error in DOM after submit | Screenshot + extract error -> retry once -> flag |
| Streamlit app down | Non-200 response | Skip HN post entirely -> add to manual list |
| Reddit cooldown | "Doing that too much" | Wait 10 min -> retry |
| Chrome tab-switching | Wrong page receives click | Use ref-based clicks only; verify URL after action |

---

## Manual Handoff Items (NOT automated)

| Task | Reason | Bead |
|------|--------|------|
| LinkedIn recommendations | Needs personal contact names | `9je` |
| Upwork profile | Chrome ext lacks permissions | `vp9` |
| Reddit first-hour engagement | Requires human replies | -- |
| LinkedIn post-publish engagement | Authentic comments drive algorithm | -- |

---

## Bead Tracking

| When | Action |
|------|--------|
| Phase 0 | `bd create --title="Reddit + HN + Dev.to content launch" --type=task --priority=2` |
| Phase 0 | `bd create --title="LinkedIn Week 1 posts" --type=task --priority=2` |
| Phase 2 | `bd close` both new beads |
| Phase 2 | `bd sync` |
