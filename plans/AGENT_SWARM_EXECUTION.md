# Agent Swarm: Content Launch Campaign — Execution Spec

**Created**: 2026-02-09
**Status**: Ready to Execute
**Goal**: Publish pre-written content to Reddit, HN, Dev.to, and LinkedIn using parallel browser automation agents.
**Est. wall time**: ~25 min (Playwright track is bottleneck path)

---

## 1. Team Architecture

### Team: `content-launch` (2 browser agents + lead)

| Agent | Type | Browser Tool | Tasks | Est. Time |
|-------|------|-------------|-------|-----------|
| **team-lead** (main session) | coordinator | None | Verification, bead tracking, spawn agents, collect results | ~5 min |
| **playwright-poster** | `general-purpose` | Playwright MCP (exclusive) | Reddit (2 posts + pin comments), HN (1 post), Dev.to (3 articles) = 8 sequential tasks | ~20 min |
| **chrome-poster** | `general-purpose` | Chrome Ext MCP (exclusive) | LinkedIn (3 Week 1 posts) = 3 sequential tasks | ~12 min |

**Why 2+1**: Two browser tools (Playwright, Chrome ext) are each single-instance. Two browser agents is the max parallelism. Lead coordinates + handles non-browser work. Adding agents beyond this would cause browser conflicts.

**Constraint**: Agents must NOT share browser tools. `playwright-poster` uses ONLY `mcp__playwright__*` tools. `chrome-poster` uses ONLY `mcp__claude-in-chrome__*` tools. Mixing causes session conflicts.

---

## 2. Task Dependency Graph

```
Phase 0: VERIFICATION (team-lead, ~2 min)
  ├── [T0.1] Read all 10 content files in parallel
  ├── [T0.2] WebFetch https://ct-agentforge.streamlit.app (HN prerequisite)
  ├── [T0.3] Validate: content present, no placeholders, no broken refs
  ├── [T0.4] Create tracking beads
  └── [T0.5] Spawn both browser agents with full instructions

Phase 1A: PLAYWRIGHT TRACK (~20 min, sequential)     ─┐
  [T1.1] Reddit r/Python post                          │
  [T1.2] Pin TL;DR comment on r/Python                 │
  [T1.3] Reddit r/SideProject post                     │  RUN IN
  [T1.4] Pin TL;DR comment on r/SideProject            │  PARALLEL
  [T1.5] HN Show post (skip if Streamlit app down)     │
  [T1.6] Dev.to Article 1: Production RAG               │
  [T1.7] Dev.to Article 2: Replaced LangChain           │
  [T1.8] Dev.to Article 3: CSV to Dashboard             │
                                                        │
Phase 1B: CHROME TRACK (~12 min, sequential)           ─┘
  [T2.1] LinkedIn Post 3: Hot Take (Build Your Own AI)
  [T2.2] LinkedIn Post 1: Token Cost Reduction
  [T2.3] LinkedIn Post 2: Multi-Agent Handoff

Phase 2: WRAP-UP (team-lead, ~3 min)
  [T3.1] Collect all published post URLs from agent reports
  [T3.2] Produce human handoff checklist (LinkedIn recs, Upwork, engagement)
  [T3.3] bd close campaign beads + bd sync
  [T3.4] Shutdown agents, delete team
  [T3.5] git commit + push
```

### Dependency Rules
- **Phase 1A/1B depend on Phase 0 completion** (content validation must pass first)
- **T1.2 depends on T1.1** (need post URL to pin comment)
- **T1.4 depends on T1.3** (same — need post URL)
- **T1.5 depends on T0.2 success** (skip HN if Streamlit app is down)
- **Phase 1A and 1B are fully independent** (different browser tools, run in parallel)
- **Phase 2 depends on both Phase 1A and 1B completion**

---

## 3. Content Files → Tasks Mapping

| Task | Content File | Platform | Content Status |
|------|-------------|----------|----------------|
| T1.1 | `content/reddit/r_python_post.md` | r/Python | Ready to paste |
| T1.2 | `content/reddit/CAMPAIGN_EXECUTION_GUIDE.md` §2.1 (TL;DR) | r/Python comment | Extract TL;DR section |
| T1.3 | `content/reddit/r_sideproject_post.md` | r/SideProject | Ready to paste |
| T1.4 | `content/reddit/CAMPAIGN_EXECUTION_GUIDE.md` §2.1 (TL;DR) | r/SideProject comment | Extract TL;DR section |
| T1.5 | `content/social/hn-show-agentforge.md` | Hacker News | Ready (title + URL + text) |
| T1.6 | `content/devto/article1-production-rag.md` | Dev.to | Set `published: true` in frontmatter |
| T1.7 | `content/devto/article2-replaced-langchain.md` | Dev.to | Set `published: true` in frontmatter |
| T1.8 | `content/devto/article3-csv-dashboard.md` | Dev.to | Set `published: true` in frontmatter |
| T2.1 | `plans/archive/linkedin/LINKEDIN_POSTS_DRAFT.md` (Post 3) | LinkedIn | Ready — "Hot Take: Build Your Own AI" |
| T2.2 | `plans/archive/linkedin/LINKEDIN_POSTS_DRAFT.md` (Post 1) | LinkedIn | Ready — "Token Cost Reduction" |
| T2.3 | `plans/archive/linkedin/LINKEDIN_POSTS_DRAFT.md` (Post 2) | LinkedIn | Ready — "Multi-Agent Handoff" |

### Duplicate Alert
Two versions of Dev.to article 3 exist:
- `content/devto/article3-csv-dashboard.md` (511 lines, comprehensive) ← **USE THIS ONE**
- `content/devto/article3-csv-to-dashboard.md` (423 lines, punchier) — save for future round

---

## 4. Browser Workflow Details

### 4.1 Reddit Posting (Playwright) — T1.1-T1.4

**For each subreddit** (r/Python, then r/SideProject):

```
Step 1: ToolSearch "playwright navigate" → load Playwright tools
Step 2: browser_navigate → https://www.reddit.com/r/{subreddit}/submit
Step 3: browser_snapshot → verify logged-in state (check for username in top-right)
        → If NOT logged in: screenshot → report to lead → SKIP
Step 4: browser_snapshot → identify form elements (title field, editor mode toggle)
Step 5: browser_click → switch to Markdown editor mode (not rich text)
Step 6: browser_fill_form / browser_type → enter title from content file
Step 7: browser_type → paste post body from content file into markdown editor
Step 8: browser_click → Submit / "Post" button
Step 9: browser_wait_for → wait for redirect to new post page
Step 10: browser_snapshot → capture post URL from browser address bar
Step 11: browser_type → add TL;DR comment in comment box
Step 12: browser_click → submit comment
Step 13: SendMessage → report post URL + comment URL to team-lead
```

**Content extraction**:
- Title: first `# ` heading from the content file
- Body: everything after the title
- TL;DR comment: from Campaign Guide §2.1 ("Pin this as first comment")

**Reddit rate limit handling**: If "you are doing that too much" appears after T1.1, wait 10 minutes before T1.3. Use the wait time to attempt T1.5 (HN) instead, then return to T1.3.

### 4.2 Hacker News Posting (Playwright) — T1.5

```
Step 1: browser_navigate → https://news.ycombinator.com/submit
Step 2: browser_snapshot → verify logged in (check for username link)
        → If NOT logged in: screenshot → report → SKIP
Step 3: browser_fill_form →
        title: "Show HN: AgentForge – Multi-LLM orchestrator built with 15KB of httpx"
        url: https://github.com/ChunkyTortoise/ai-orchestrator
        text: (body from hn-show-agentforge.md, excluding the title/URL header lines)
Step 4: browser_click → submit button
Step 5: browser_snapshot → capture post URL
Step 6: SendMessage → report URL to team-lead
```

**Prerequisite**: T0.2 must confirm `https://ct-agentforge.streamlit.app` returns 200. If it's down, SKIP this task and report: "HN post skipped — Streamlit demo is down. Post manually when it's live."

### 4.3 Dev.to Publishing (Playwright) — T1.6-T1.8

**For each article** (3x):

```
Step 1: browser_navigate → https://dev.to/new
Step 2: browser_snapshot → verify logged in
        → If NOT logged in: screenshot → report → SKIP
Step 3: browser_snapshot → identify editor (V2 editor with frontmatter support)
Step 4: Read content file → change "published: false" to "published: true" in memory
Step 5: browser_click → click into the editor area
Step 6: browser_type → paste entire article content (frontmatter + body)
        NOTE: Paste with published: true already set
Step 7: browser_snapshot → verify tags appeared correctly from frontmatter
Step 8: browser_click → "Publish" button (or "Save changes" if editing existing draft)
Step 9: browser_wait_for → wait for article page to load
Step 10: browser_snapshot → capture article URL
Step 11: SendMessage → report URL to team-lead
```

**Dev.to gotcha**: The V2 editor may override frontmatter `published` field with its own UI toggle. After pasting, verify the publish toggle is ON before clicking save.

### 4.4 LinkedIn Posting (Chrome Extension) — T2.1-T2.3

**For each post** (3x):

```
Step 1: ToolSearch "chrome navigate" → load Chrome extension tools
Step 2: tabs_context_mcp → check current browser tabs
Step 3: tabs_create_mcp → open new tab (or navigate existing)
Step 4: navigate → https://www.linkedin.com/feed/
Step 5: read_page → verify logged in (check for profile photo/name)
        → If NOT logged in: report to lead → SKIP
Step 6: find → locate "Start a post" button
Step 7: computer (click via ref) → click the "Start a post" button
        ⚠️ CRITICAL: Use ref-based click, NEVER coordinate-based (tab-switching bug)
Step 8: read_page → verify post composer modal opened
Step 9: form_input → paste post content from LINKEDIN_POSTS_DRAFT.md
        Include hashtags at the end of the post
Step 10: find → locate "Post" button in the composer
Step 11: computer (click via ref) → click Post button
Step 12: read_page → verify post appeared in feed
Step 13: SendMessage → report post URL to team-lead
```

**LinkedIn timing note**: Today is Sunday Feb 9. The campaign guide recommends Mon/Tue/Thu. Options:
- **Option A**: Post all 3 now (suboptimal timing but content goes live)
- **Option B**: Use LinkedIn's native scheduling for Mon 9am / Tue 8am / Thu 8am PT
- **Recommendation**: Use Option B if scheduling UI is available; otherwise Option A

**Chrome extension safety**:
- Always call `tabs_context_mcp` first to get fresh tab state
- Use `ref`-based clicks exclusively (documented bug with coordinate clicks)
- Wait 2-3 seconds between posts for LinkedIn to stabilize
- If "posting too frequently" warning appears, wait 5 minutes

---

## 5. Agent Spawn Instructions

### 5.1 Playwright-Poster Agent Prompt

```
You are the playwright-poster agent on team content-launch. Your job is to publish
content to Reddit, Hacker News, and Dev.to using ONLY Playwright MCP tools.

DO NOT use claude-in-chrome tools — those belong to the chrome-poster agent.

TASK SEQUENCE (execute in order):

1. Use ToolSearch to load Playwright browser tools
2. Read these content files:
   - /Users/cave/Documents/GitHub/EnterpriseHub/content/reddit/r_python_post.md
   - /Users/cave/Documents/GitHub/EnterpriseHub/content/reddit/r_sideproject_post.md
   - /Users/cave/Documents/GitHub/EnterpriseHub/content/reddit/CAMPAIGN_EXECUTION_GUIDE.md
   - /Users/cave/Documents/GitHub/EnterpriseHub/content/social/hn-show-agentforge.md
   - /Users/cave/Documents/GitHub/EnterpriseHub/content/devto/article1-production-rag.md
   - /Users/cave/Documents/GitHub/EnterpriseHub/content/devto/article2-replaced-langchain.md
   - /Users/cave/Documents/GitHub/EnterpriseHub/content/devto/article3-csv-dashboard.md

3. REDDIT (T1.1-T1.4):
   - Navigate to reddit.com/r/Python/submit → post r_python_post.md
   - Add TL;DR pin comment from Campaign Guide §2.1
   - Navigate to reddit.com/r/SideProject/submit → post r_sideproject_post.md
   - Add TL;DR pin comment
   - If rate-limited ("doing that too much"), skip to HN, come back after 10 min

4. HACKER NEWS (T1.5):
   - ONLY if team-lead confirmed Streamlit app is live
   - Navigate to news.ycombinator.com/submit
   - Title: "Show HN: AgentForge – Multi-LLM orchestrator built with 15KB of httpx"
   - URL: https://github.com/ChunkyTortoise/ai-orchestrator
   - Text: body from hn-show-agentforge.md

5. DEV.TO (T1.6-T1.8):
   - For each article: navigate to dev.to/new
   - Paste with published: true in frontmatter
   - Click Publish, capture URL

ERROR HANDLING:
- Not logged in → screenshot + skip + report
- CAPTCHA → screenshot + skip + report
- Timeout → retry 3x with 15s delay, then skip
- Always take browser_snapshot after key actions

REPORTING:
- After EACH successful post, send a message to team-lead with the published URL
- After all tasks done, send final summary with all URLs and any skipped tasks
- Mark your tasks as completed in the task list
```

### 5.2 Chrome-Poster Agent Prompt

```
You are the chrome-poster agent on team content-launch. Your job is to publish
3 LinkedIn posts using ONLY Claude-in-Chrome browser extension tools.

DO NOT use Playwright tools — those belong to the playwright-poster agent.

TASK SEQUENCE (execute in order):

1. Use ToolSearch to load Chrome extension tools (search "chrome")
2. Call tabs_context_mcp to get current browser state
3. Read this content file:
   - /Users/cave/Documents/GitHub/EnterpriseHub/plans/archive/linkedin/LINKEDIN_POSTS_DRAFT.md

4. LINKEDIN POSTS (T2.1-T2.3):
   Post order: Post 3 (Hot Take), then Post 1 (Token Cost), then Post 2 (Multi-Agent)

   For each post:
   a. Create new tab or navigate to https://www.linkedin.com/feed/
   b. read_page → verify logged in
   c. find → locate "Start a post" button
   d. Click via ref (NEVER coordinates — known tab-switching bug)
   e. form_input → paste post content including hashtags
   f. find → locate "Post" button
   g. Click Post via ref
   h. read_page → verify post appeared
   i. Wait 3 seconds between posts

   SCHEDULING OPTION:
   - If LinkedIn's post scheduling UI is available, schedule:
     Post 3 → Monday 9am PT, Post 1 → Tuesday 8am PT, Post 2 → Thursday 8am PT
   - If no scheduling available, post all 3 immediately

ERROR HANDLING:
- Not logged in → report to team-lead, skip all tasks
- Tab-switching bug → re-navigate to correct URL, retry with ref-based click
- "Posting too frequently" → wait 5 min, retry
- Always use ref-based clicks, never coordinate-based

REPORTING:
- After EACH successful post, send a message to team-lead with the post URL
- After all 3 posts done, send final summary
- Mark your tasks as completed in the task list
```

---

## 6. Error Handling Matrix

| Error | Detection | Immediate Response | Fallback |
|-------|-----------|-------------------|----------|
| Site unreachable | Navigation timeout / error page | Retry 3x with 15s delay | Skip task, log URL + error, move to next |
| Not logged in | Login page detected in snapshot | Take screenshot, report to team-lead | Flag for human to authenticate, re-queue task |
| CAPTCHA / anti-bot | Interactive challenge in DOM | Screenshot, skip immediately | Add to manual handoff list |
| Post rejected (spam filter) | Error message in DOM after submit | Screenshot + extract error text | Retry once with minor edits; if fails, flag |
| Streamlit app down (T0.2) | WebFetch returns non-200 | Skip HN post (T1.5) entirely | Add HN to manual list: "post when app is live" |
| Reddit 10-min cooldown | "You are doing that too much" | Reorder: skip to HN/Dev.to, return after 10 min | If still rate-limited, flag for manual |
| Chrome tab-switching bug | Wrong page receives click action | Navigate explicitly to correct URL, retry | If persistent, use JavaScript `element.click()` |
| Dev.to publish toggle | `published: false` persists in UI | Manually toggle the publish switch in editor | Check article status page after save |
| LinkedIn compose modal stuck | Modal doesn't open after click | Refresh page, retry "Start a post" | Try direct URL: linkedin.com/feed/?shareActive=true |

**Critical principle**: Every failed task gets a `browser_snapshot` / screenshot before skipping. The team-lead's Phase 2 report includes all failures with screenshots and manual remediation steps.

---

## 7. Manual Handoff Checklist (Phase 2 Output)

These tasks **cannot and should not** be automated:

| Task | Reason | Bead | Content File | Human Action |
|------|--------|------|-------------|-------------|
| LinkedIn recommendations | Templates need specific contact names + personalization | `9je` | `plans/archive/linkedin/LINKEDIN_RECOMMENDATION_REQUESTS.md` | Pick 3-5 contacts, fill `[Name]`/`[project]` placeholders, send via LinkedIn DM |
| Upwork profile | Chrome ext lacks Upwork permissions; Playwright blocked by anti-bot | `vp9` | `content/upwork-profile-improvements.md` | Manual copy-paste: summary, skills, portfolio items, working style |
| Reddit first-hour engagement | Bot-like replies risk account suspension | — | `content/reddit/engagement_templates.md` | Monitor posts 60 min after publishing, reply authentically using templates as guides |
| LinkedIn post-publish engagement | Authentic comments drive algorithmic reach | — | — | Comment on 3-5 AI/Python posts within 30 min of each LinkedIn post |

---

## 8. Bead Tracking Protocol

| Phase | Command | Notes |
|-------|---------|-------|
| Phase 0 | `bd create --title="Content launch: Reddit + HN + Dev.to" --type=task --priority=2` | Track Playwright agent work |
| Phase 0 | `bd create --title="Content launch: LinkedIn Week 1 posts" --type=task --priority=2` | Track Chrome agent work |
| Phase 0 | `bd update <reddit-bead> --status=in_progress` | When Playwright agent starts |
| Phase 0 | `bd update <linkedin-bead> --status=in_progress` | When Chrome agent starts |
| Phase 2 | `bd close <reddit-bead> <linkedin-bead>` | After both agents report success |
| Phase 2 | `bd sync` | Sync to git |
| Phase 2 | NOT closed: `9je` (recs) and `vp9` (Upwork) | Flagged as manual in handoff checklist |

---

## 9. Execution Checklist (Team-Lead Script)

```bash
# === PHASE 0: VERIFICATION ===
# 1. Read all content files (parallel)
Read content/reddit/r_python_post.md
Read content/reddit/r_sideproject_post.md
Read content/reddit/CAMPAIGN_EXECUTION_GUIDE.md
Read content/social/hn-show-agentforge.md
Read content/devto/article1-production-rag.md
Read content/devto/article2-replaced-langchain.md
Read content/devto/article3-csv-dashboard.md
Read plans/archive/linkedin/LINKEDIN_POSTS_DRAFT.md

# 2. Verify Streamlit app is live
WebFetch https://ct-agentforge.streamlit.app

# 3. Create tracking beads
bd create --title="Content launch: Reddit + HN + Dev.to" --type=task --priority=2
bd create --title="Content launch: LinkedIn Week 1 posts" --type=task --priority=2

# === PHASE 1: SPAWN AGENTS (PARALLEL) ===
# 4. Create team
TeamCreate team_name="content-launch"

# 5. Create task list
TaskCreate "Reddit r/Python post" ...
TaskCreate "Reddit r/SideProject post" ...
TaskCreate "HN Show post" ...
TaskCreate "Dev.to article 1" ...
TaskCreate "Dev.to article 2" ...
TaskCreate "Dev.to article 3" ...
TaskCreate "LinkedIn Post 3" ...
TaskCreate "LinkedIn Post 1" ...
TaskCreate "LinkedIn Post 2" ...

# 6. Spawn both agents IN PARALLEL (single message, two Task calls)
Task subagent_type=general-purpose team_name=content-launch name=playwright-poster
Task subagent_type=general-purpose team_name=content-launch name=chrome-poster

# === PHASE 1: MONITOR ===
# 7. Wait for agent messages (automatic delivery)
# 8. Track progress via TaskList

# === PHASE 2: WRAP-UP ===
# 9. Collect URLs from agent reports
# 10. Close beads
bd close <reddit-bead> <linkedin-bead>
bd sync

# 11. Produce human handoff checklist (from §7 above)
# 12. Shutdown agents
SendMessage type=shutdown_request recipient=playwright-poster
SendMessage type=shutdown_request recipient=chrome-poster

# 13. Delete team
TeamDelete

# 14. Commit and push
git add plans/AGENT_SWARM_EXECUTION.md
git commit -m "docs: content launch swarm execution spec"
git push
```

---

## 10. Success Criteria

| Metric | Target |
|--------|--------|
| Reddit posts published | 2 (r/Python + r/SideProject) |
| Reddit pin comments added | 2 |
| HN Show post published | 1 (skip if Streamlit down) |
| Dev.to articles published | 3 |
| LinkedIn posts published | 3 |
| Total content pieces live | 11 |
| Failed tasks | 0 (or all failures documented with screenshots) |
| Beads closed | 2 new campaign beads |
| Human handoff checklist | Complete with 4 manual items |

---

## Appendix: Timeline Estimate

```
T=0:00   Phase 0 starts (team-lead reads files, verifies URLs)
T=2:00   Phase 0 complete → spawn both agents simultaneously
         ├── playwright-poster begins T1.1 (Reddit r/Python)
         └── chrome-poster begins T2.1 (LinkedIn Post 3)
T=5:00   T1.1 done → T1.2 (pin comment)
         T2.1 in progress
T=7:00   T1.2 done → T1.3 (Reddit r/SideProject)
         T2.1 done → T2.2 (LinkedIn Post 1)
T=10:00  T1.3 done → T1.4 (pin comment)
         T2.2 in progress
T=12:00  T1.4 done → T1.5 (HN Show post)
         T2.2 done → T2.3 (LinkedIn Post 2)
T=14:00  T1.5 done → T1.6 (Dev.to article 1)
         T2.3 in progress
T=17:00  T1.6 done → T1.7 (Dev.to article 2)
         T2.3 done ✅ CHROME TRACK COMPLETE
T=20:00  T1.7 done → T1.8 (Dev.to article 3)
T=23:00  T1.8 done ✅ PLAYWRIGHT TRACK COMPLETE
T=25:00  Phase 2 complete → all URLs collected, beads closed, team shutdown
```
