# Upwork Profile Swarm — Continuation Prompt
**Created**: 2026-02-17
**Use this**: Paste this into a new Claude Code session to launch the swarm

---

## Context

You are helping Cayman Roden (AI/ML freelancer) complete his Upwork profile optimization.
A full audit was done in the previous session. All tasks are now specced in a single file.

**Spec file**: `/Users/cave/Documents/GitHub/EnterpriseHub/plans/UPWORK_PROFILE_SWARM_SPEC.md`

Read the spec file first — it contains all context, metrics, live demo URLs, and exact deliverable formats.

## Your Job

Launch 5 agents in parallel to produce all Upwork content.
Then create child beads for all human action items.
Then close the parent bead.

## Wave 1 — Launch All 5 Agents Simultaneously

Send a single message with all 5 Task tool calls at once:

```
Agent 1 — Profile Copywriter
  subagent_type: general-purpose
  model: sonnet
  prompt: |
    Read the full spec at /Users/cave/Documents/GitHub/EnterpriseHub/plans/UPWORK_PROFILE_SWARM_SPEC.md.
    Find the "AGENT 1: Profile Copywriter" section.
    Execute all deliverables exactly as specified.
    Output file: /Users/cave/Documents/GitHub/EnterpriseHub/content/upwork/profile-update.md
    Create the output directory if it doesn't exist.
    When done, run from /Users/cave/Documents/GitHub/EnterpriseHub:
      bd comment EnterpriseHub-y920 "Agent 1 complete: profile-update.md written"
    Report: what you wrote, word count, headline recommendation.

Agent 2 — Specialized Profiles Architect
  subagent_type: general-purpose
  model: sonnet
  prompt: |
    Read the full spec at /Users/cave/Documents/GitHub/EnterpriseHub/plans/UPWORK_PROFILE_SWARM_SPEC.md.
    Find the "AGENT 2: Specialized Profiles Architect" section.
    Execute all 3 specialized profiles exactly as specified.
    Output file: /Users/cave/Documents/GitHub/EnterpriseHub/content/upwork/specialized-profiles.md
    Create the output directory if it doesn't exist.
    When done, run from /Users/cave/Documents/GitHub/EnterpriseHub:
      bd comment EnterpriseHub-y920 "Agent 2 complete: specialized-profiles.md written"
    Report: 3 profile titles, headline recommendations, word counts.

Agent 3 — Proposal Rewriter
  subagent_type: general-purpose
  model: sonnet
  prompt: |
    Read the full spec at /Users/cave/Documents/GitHub/EnterpriseHub/plans/UPWORK_PROFILE_SWARM_SPEC.md.
    Find the "AGENT 3: Proposal Rewriter" section.
    The 5 existing proposals are at:
      /Users/cave/Documents/GitHub/EnterpriseHub/content/upwork/proposals/proposal-1-semantic-rag.md
      /Users/cave/Documents/GitHub/EnterpriseHub/content/upwork/proposals/proposal-2-education-rag.md
      /Users/cave/Documents/GitHub/EnterpriseHub/content/upwork/proposals/proposal-3-rag-debugging.md
      /Users/cave/Documents/GitHub/EnterpriseHub/content/upwork/proposals/proposal-4-modular-ai-platform.md
      /Users/cave/Documents/GitHub/EnterpriseHub/content/upwork/proposals/proposal-5-support-chatbot.md
    If any files don't exist, create them with a strong proposal from scratch using the formula in the spec.
    Rewrite each file in-place. Add "## Rewrite Notes" section at bottom of each.
    When done, run from /Users/cave/Documents/GitHub/EnterpriseHub:
      bd comment EnterpriseHub-y920 "Agent 3 complete: 5 proposals rewritten"
    Report: key change for each proposal, new first line for each.

Agent 4 — Quick-Close Job Strategy
  subagent_type: general-purpose
  model: sonnet
  prompt: |
    Read the full spec at /Users/cave/Documents/GitHub/EnterpriseHub/plans/UPWORK_PROFILE_SWARM_SPEC.md.
    Find the "AGENT 4: Quick-Close Job Strategy" section.
    Execute all 3 deliverables: job categories, 3 ready proposals, playbook.
    Output file: /Users/cave/Documents/GitHub/EnterpriseHub/content/upwork/quick-close-strategy.md
    Create the output directory if it doesn't exist.
    When done, run from /Users/cave/Documents/GitHub/EnterpriseHub:
      bd comment EnterpriseHub-y920 "Agent 4 complete: quick-close-strategy.md written"
    Report: 5 job categories identified, 3 proposal titles.

Agent 5 — Video Script + Portfolio Items
  subagent_type: general-purpose
  model: sonnet
  prompt: |
    Read the full spec at /Users/cave/Documents/GitHub/EnterpriseHub/plans/UPWORK_PROFILE_SWARM_SPEC.md.
    Find the "AGENT 5: Video Intro Script + Portfolio Items" section.
    Execute both deliverables: 90-second script and 5 portfolio item descriptions.
    Output file: /Users/cave/Documents/GitHub/EnterpriseHub/content/upwork/video-and-portfolio.md
    Create the output directory if it doesn't exist.
    When done, run from /Users/cave/Documents/GitHub/EnterpriseHub:
      bd comment EnterpriseHub-y920 "Agent 5 complete: video-and-portfolio.md written"
    Report: script word count, 5 portfolio item titles.
```

## After All 5 Agents Complete

Run these bead updates from `/Users/cave/Documents/GitHub/EnterpriseHub`:

```bash
# Mark y920 in-progress (it was open)
bd start EnterpriseHub-y920

# Create child beads for human action items
bd create --title "Upwork: Apply profile-update.md to profile (headline, overview, skills, rate)" --priority P1 --type task --description "Content ready at content/upwork/profile-update.md. Copy headline, paste overview, add skills in listed order, set rate. Est: 15 min."

bd create --title "Upwork: Create 3 specialized profiles" --priority P1 --type task --description "Content ready at content/upwork/specialized-profiles.md. Go to Profile > Specialized Profiles > Add New. Est: 30 min."

bd create --title "Upwork: Record + upload 90-second video intro" --priority P1 --type task --description "Script ready at content/upwork/video-and-portfolio.md. Phone camera OK, good lighting. Upload to Profile > Video Introduction. Est: 30 min."

bd create --title "Upwork: Send 2-3 quick-close proposals daily (target: 3 reviews in 30 days)" --priority P1 --type task --description "Templates + strategy at content/upwork/quick-close-strategy.md. Filter: Fixed price $150-500, posted last 24hr. Jobs: RAG debug, Streamlit dashboard, LLM integration."

bd create --title "Upwork: Connect GitHub account" --priority P2 --type task --description "Settings > Connected Services > GitHub. Takes 2 min. Adds trust badge to profile."

bd create --title "Upwork: Add 5 portfolio items with screenshots" --priority P2 --type task --description "Descriptions ready at content/upwork/video-and-portfolio.md. Profile > Portfolio > Add Work. Screenshot each live Streamlit demo. Est: 30 min."

# Close the parent bead
bd close EnterpriseHub-y920 --reason "All Upwork content complete: profile-update.md, specialized-profiles.md, 5 proposals rewritten, quick-close-strategy.md, video-and-portfolio.md. Human action child beads created."
```

## Verify Success

```bash
# Check files exist
ls -la /Users/cave/Documents/GitHub/EnterpriseHub/content/upwork/
ls -la /Users/cave/Documents/GitHub/EnterpriseHub/content/upwork/proposals/

# Check bead status
bd show EnterpriseHub-y920
bd list | grep y920
```

## Expected Output Files

```
content/upwork/
├── profile-update.md          (Agent 1 — headline, overview, skills, rate)
├── specialized-profiles.md    (Agent 2 — 3 specialized profile pages)
├── quick-close-strategy.md    (Agent 4 — job types, 3 proposals, playbook)
├── video-and-portfolio.md     (Agent 5 — script, 5 portfolio items)
└── proposals/
    ├── proposal-1-semantic-rag.md        (Agent 3 — rewritten)
    ├── proposal-2-education-rag.md       (Agent 3 — rewritten)
    ├── proposal-3-rag-debugging.md       (Agent 3 — rewritten)
    ├── proposal-4-modular-ai-platform.md (Agent 3 — rewritten)
    └── proposal-5-support-chatbot.md     (Agent 3 — rewritten)
```
