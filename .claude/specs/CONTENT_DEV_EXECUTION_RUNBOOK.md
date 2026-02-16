# Content Development Team - Execution Runbook
**Companion to**: `CONTENT_DEV_TEAM_SPEC.md`
**Purpose**: Step-by-step commands to execute the content development sprint
**User**: Cave (team lead)

---

## Pre-Flight Checklist

Before starting the sprint, verify:

```bash
# 1. Working directory is EnterpriseHub
cd /Users/cave/Documents/GitHub/EnterpriseHub
pwd  # Should show: /Users/cave/Documents/GitHub/EnterpriseHub

# 2. Git status is clean (or commit current work)
git status

# 3. Beads is working
bd stats

# 4. Read the spec
cat .claude/specs/CONTENT_DEV_TEAM_SPEC.md

# 5. Create output directories
mkdir -p content/video content/visual content/business content/case-studies
```

**Estimated Time to Complete**: 8-12 hours (wall-clock) across 2-3 sessions

---

## Session 1: Setup + Wave 1 (4 hours)

### Step 1.1: Create Epic and Tasks (15 minutes)

```bash
# Create epic for tracking
bd create \
  --title="Content Development Sprint - 23 Assets" \
  --type=epic \
  --priority=0

# Capture epic ID
EPIC_ID=$(bd list --status=open | grep "Content Development Sprint" | awk '{print $1}')
echo "Epic ID: $EPIC_ID"

# Create all 23 tasks (organized by wave)
# Wave 1: Video tasks (5 scripts + guide)
bd create --title="Video: EnterpriseHub script review and finalization" --type=task --priority=0
bd create --title="Video: AgentForge 2-min demo script" --type=task --priority=0
bd create --title="Video: DocQA 5-min demo script" --type=task --priority=0
bd create --title="Video: Prompt Lab pattern demo script" --type=task --priority=0
bd create --title="Video: LLM Starter quickstart script" --type=task --priority=0
bd create --title="Video: Recording guide with technical specs" --type=task --priority=1

# Wave 1: Visual tasks (5 screenshot specs + plan)
bd create --title="Visual: Screenshot capture master plan" --type=task --priority=0
bd create --title="Visual: AgentForge screenshot specifications" --type=task --priority=0
bd create --title="Visual: DocQA screenshot specifications" --type=task --priority=0
bd create --title="Visual: Insight Engine screenshot specifications" --type=task --priority=0
bd create --title="Visual: Scraper screenshot specifications" --type=task --priority=0
bd create --title="Visual: Before/After metrics graphics design" --type=task --priority=1

# Wave 1: Technical tasks (3 competitive matrices)
bd create --title="Tech: AgentForge competitive comparison matrix" --type=task --priority=0
bd create --title="Tech: DocQA competitive comparison matrix" --type=task --priority=0
bd create --title="Tech: EnterpriseHub vs DIY comparison" --type=task --priority=0

# Wave 2: Technical tasks (ROI calculator)
bd create --title="Tech: ROI calculator specification" --type=task --priority=1
bd create --title="Tech: ROI calculator Streamlit implementation" --type=task --priority=1

# Wave 2: Copy tasks (For-Executives docs)
bd create --title="Copy: EnterpriseHub For-Prospects documentation" --type=task --priority=1
bd create --title="Copy: AgentForge For-Executives documentation" --type=task --priority=1
bd create --title="Copy: DocQA For-Executives documentation" --type=task --priority=1

# Wave 3: Copy tasks (Case studies)
bd create --title="Copy: EnterpriseHub case study (STAR format)" --type=task --priority=2
bd create --title="Copy: AgentForge case study (STAR format)" --type=task --priority=2
bd create --title="Copy: DocQA case study (STAR format)" --type=task --priority=2

# QA validation task
bd create --title="QA: Final validation and quality gate check" --type=task --priority=3

# View all tasks
bd list --status=open
```

### Step 1.2: Set Up Task Dependencies (5 minutes)

```bash
# Find task IDs (substitute actual IDs from bd list output)
# You'll need to capture these from the output above

# Example (use actual IDs):
# ROI code depends on ROI spec
bd dep add beads-roi-code beads-roi-spec

# Case studies depend on screenshot plan
bd dep add beads-case-eh beads-screenshot-plan
bd dep add beads-case-af beads-screenshot-plan
bd dep add beads-case-dq beads-screenshot-plan

# For-Executives docs depend on competitive matrices
bd dep add beads-exec-af beads-comp-af
bd dep add beads-exec-dq beads-comp-dq

# Verify dependencies
bd show beads-roi-code  # Should show "Blocked by: beads-roi-spec"
```

### Step 1.3: Create Team (5 minutes)

Tell Claude (in a new message):

```
Create a content development team for parallel asset creation.

Team name: content-dev-team
Team lead: portfolio-coordinator agent

The team will create 23 content assets following the spec at:
.claude/specs/CONTENT_DEV_TEAM_SPEC.md

Please create the team now.
```

**Expected Output**: Team created at `~/.claude/teams/content-dev-team/`

### Step 1.4: Spawn All 5 Agents in Parallel (10 minutes)

**IMPORTANT**: Send this as a SINGLE message to Claude so agents spawn in parallel:

```
Spawn all 5 content development agents in parallel using the specifications from:
.claude/specs/CONTENT_DEV_TEAM_SPEC.md

Use the detailed agent prompts from the "Agent Spawn Commands" section.

Agents to spawn:
1. video-agent (content-marketing-engine) - Video scripts
2. visual-agent (dashboard-design) - Screenshots and graphics
3. tech-agent (architecture-sentinel) - Technical comparisons and ROI calc
4. copy-agent (content-marketing-engine) - Marketing copy and case studies
5. qa-agent (quality-gate) - Quality validation

Team: content-dev-team

Spawn all 5 agents NOW in a single message (5 Task tool calls).
```

**Wait for**: All 5 agents to report idle (you'll see 5 idle notifications)

### Step 1.5: Assign Wave 1 Tasks (10 minutes)

Once agents are spawned, tell Claude:

```
Assign Wave 1 tasks to agents following the spec:

Video Agent gets:
- All 5 video script tasks
- Recording guide task

Visual Agent gets:
- Screenshot master plan
- All 4 product screenshot spec tasks
- Before/After metrics graphics

Tech Agent gets:
- All 3 competitive matrix tasks

Use bd update with --assignee parameter.

After assignment, notify each agent via SendMessage about their assigned work.
```

### Step 1.6: Monitor Wave 1 Execution (2.5-3 hours)

**What to watch for**:
- Agents report task completion via SendMessage
- Agents go idle between tasks (NORMAL - not a problem)
- Agents self-assign next available tasks from `bd ready`

**Your role**:
- Read agent completion messages (auto-delivered)
- Don't interrupt unless agent reports blocker
- Let agents work autonomously

**Check progress periodically**:
```bash
# See what's completed
bd list --status=completed

# See what's in progress
bd list --status=in_progress

# See what's available
bd ready
```

### Step 1.7: Wave 1 QA Validation (30 minutes)

Once all Wave 1 tasks show completed, tell Claude:

```
Wave 1 is complete. QA agent: Run Gate 1 validation following the spec.

Check:
- All 5 video scripts exist in content/video/
- All 5 screenshot specs exist in content/visual/
- All 3 competitive matrices exist in correct docs/ folders
- Markdown linting passes
- No broken links
- Scripts follow 3-act structure

Report validation results with pass/fail counts.
```

**Expected Output**: Validation report with ✅/⚠️/❌ counts

**If Gate 1 fails**: Create fix tasks, assign to responsible agent, re-validate

---

## Session 2: Wave 2 + Wave 3 (5-6 hours)

### Step 2.1: Assign Wave 2 Tasks (5 minutes)

Tell Claude:

```
Wave 1 validation passed. Assign Wave 2 tasks:

Tech Agent gets:
- ROI calculator spec (must complete before code task)
- ROI calculator implementation (blocked until spec done)

Copy Agent gets:
- EnterpriseHub For-Prospects doc
- AgentForge For-Executives doc
- DocQA For-Executives doc

Notify agents via SendMessage. Tech agent: do spec task first, then code.
```

### Step 2.2: Monitor Wave 2 Execution (2.5-3 hours)

**Key dependency**: ROI calculator code cannot start until spec is done

```bash
# Check if ROI spec is complete
bd show beads-roi-spec

# Once spec is done, ROI code task should become unblocked
bd ready  # Should show ROI code task
```

**Check progress**:
```bash
bd list --status=in_progress
bd list --status=completed
```

### Step 2.3: Wave 2 QA Validation (30 minutes)

Tell Claude:

```
Wave 2 complete. QA agent: Run Gate 2 validation.

Check:
- ROI calculator runs without errors: streamlit run content/business/roi_calculator.py
- Calculator produces realistic outputs
- For-Executives docs are readable (Flesch-Kincaid grade < 10)
- All metrics have citations
- CTAs are actionable

Report validation results.
```

### Step 2.4: Assign Wave 3 Tasks (5 minutes)

Tell Claude:

```
Wave 2 validation passed. Assign Wave 3 tasks:

Copy Agent gets:
- EnterpriseHub case study
- AgentForge case study
- DocQA case study

Visual Agent gets:
- Before/After metrics graphics implementation

These tasks are now unblocked (screenshot plan is complete).

Notify agents via SendMessage.
```

### Step 2.5: Monitor Wave 3 Execution (2-3 hours)

```bash
# Monitor case study creation
bd list --status=in_progress | grep "case study"

# Check for completion
bd list --status=completed | grep "Wave 3"
```

### Step 2.6: Wave 3 QA Validation (30 minutes)

Tell Claude:

```
Wave 3 complete. QA agent: Run Gate 3 validation.

Check:
- Case studies follow STAR format (Situation/Task/Action/Result sections)
- All metrics are quantified (no vague claims)
- Graphics specs have color codes, fonts, dimensions
- Before/After graphics show dramatic visual contrast

Report validation results.
```

---

## Session 3: Wave 4 + Wrap-Up (2 hours)

### Step 3.1: Final Validation (1 hour)

Tell Claude:

```
All waves complete. QA agent + Team lead: Run Gate 4 final validation.

Comprehensive checks:
- All 23 deliverables exist at specified paths
- No TODO/FIXME/PLACEHOLDER text
- Brand consistency (URLs, company name, tone)
- Cross-references valid
- File sizes reasonable
- Git status clean (all files tracked)

This is the final quality gate. 100% pass required.

Report detailed validation results.
```

**If issues found**: Fix immediately before proceeding

### Step 3.2: Commit Everything (15 minutes)

```bash
# Review what was created
git status

# Stage all content files
git add content/ docs/
git add ai-orchestrator/docs/ docqa-engine/docs/ 2>/dev/null || true

# Check what's staged
git diff --cached --stat

# Commit with detailed message
git commit -m "$(cat <<'EOF'
feat: Add 23 content assets from parallel dev sprint

Created via 5-agent swarm (video, visual, tech, copy, qa):

Video Assets (6):
- EnterpriseHub 6:30 walkthrough script
- AgentForge 2-min demo script
- DocQA 5-min demo script
- Prompt Lab pattern demo script
- LLM Starter quickstart script
- Recording guide with technical specs

Visual Assets (6):
- Screenshot capture master plan
- AgentForge screenshot specifications
- DocQA screenshot specifications
- Insight Engine screenshot specifications
- Scraper screenshot specifications
- Before/After metrics graphics design

Technical Assets (5):
- AgentForge competitive comparison matrix
- DocQA competitive comparison matrix
- EnterpriseHub vs DIY comparison
- ROI calculator specification
- ROI calculator Streamlit implementation

Marketing Copy (6):
- EnterpriseHub For-Prospects documentation
- AgentForge For-Executives documentation
- DocQA For-Executives documentation
- EnterpriseHub case study (STAR format)
- AgentForge case study (STAR format)
- DocQA case study (STAR format)

Total effort: 45 hours compressed to 8-12 hours via parallelization
Quality gates: 4/4 passed
Team: 5 agents (video, visual, tech, copy, qa)
Sprint duration: 2-3 sessions

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"

# Verify commit
git log -1 --stat
```

### Step 3.3: Close Beads Tasks (10 minutes)

```bash
# Get all completed task IDs
COMPLETED_TASKS=$(bd list --status=completed | awk '{print $1}' | grep "beads-" | tr '\n' ' ')

# Close all completed tasks at once (efficient)
bd close $COMPLETED_TASKS

# Close the epic
bd close $EPIC_ID --reason="Sprint completed: 23/23 assets delivered, 4/4 quality gates passed"

# Sync beads changes
bd sync

# Verify all closed
bd list --status=completed | wc -l  # Should show 24 (23 tasks + 1 epic)
```

### Step 3.4: Push Everything (5 minutes)

```bash
# Push code changes
git push origin main

# Beads already synced (bd sync above)

# Verify remote has changes
git log origin/main -1 --oneline
```

### Step 3.5: Shutdown Team (10 minutes)

Tell Claude:

```
Sprint complete! Shutdown all agents gracefully.

Send shutdown_request to all 5 agents:
- video-agent
- visual-agent
- tech-agent
- copy-agent
- qa-agent

Wait for shutdown confirmations, then delete the team.
```

**Expected sequence**:
1. 5 SendMessage calls (type: shutdown_request)
2. 5 agent shutdown confirmations
3. TeamDelete

### Step 3.6: Update Portfolio Status (10 minutes)

```bash
# Update content assets inventory
code ~/.claude/reference/freelance/content-assets.md

# Add these 23 new assets to relevant sections:
# - Video assets: 6 new scripts
# - Visual assets: 6 new specs
# - Technical docs: 5 new files
# - Marketing copy: 6 new files

# Commit the update
cd ~/.claude
git add reference/freelance/content-assets.md
git commit -m "docs: Update content inventory after dev sprint (23 new assets)"
git push
```

---

## Post-Sprint Next Steps

### Immediate Actions (Day 1-2)

**1. Record Videos** (use scripts from content/video/)
```bash
# Set up recording environment
# - Clean desktop (no clutter visible)
# - Test microphone (Blue Yeti, Rode, or MacBook built-in)
# - Close notifications (Do Not Disturb mode)
# - Prepare demo environments (Streamlit apps running)

# Recording tools:
# Option A: Loom (free, easiest)
# Option B: OBS Studio (free, professional)
# Option C: ScreenFlow (paid, Mac only, best quality)

# Upload destinations:
# - YouTube (public, SEO)
# - Vimeo (professional, no ads)
# - Loom (quick sharing)
```

**2. Capture Screenshots** (follow specs from content/visual/)
```bash
# Run Streamlit apps locally or use live demos
streamlit run ai-orchestrator/streamlit_app.py  # Port 8501
streamlit run prompt-engineering-lab/streamlit_app.py  # Port 8502
streamlit run llm-integration-starter/streamlit_app.py  # Port 8503

# Capture with built-in tool
# Cmd+Shift+4 then:
# - Space bar to capture window (includes shadow)
# - Drag to select region (exact dimensions)

# Or use CleanShot X for annotations
```

**3. Deploy ROI Calculator**
```bash
# Test locally first
cd content/business
streamlit run roi_calculator.py

# Deploy to Streamlit Cloud
# 1. Push to GitHub (already done)
# 2. Visit share.streamlit.io
# 3. New app → EnterpriseHub repo → content/business/roi_calculator.py
# 4. App URL: ct-roi-calculator.streamlit.app
```

### Week 1 Actions

**1. Update Gumroad Product Pages**
- Add screenshots (5-7 per product)
- Embed video demos (YouTube links)
- Update descriptions with For-Executives copy
- Add "See competitive comparison" links

**2. Update Repository READMEs**
- Add competitive matrix links
- Embed ROI calculator
- Link to case studies
- Update demo section with screenshots

**3. Launch Cold Outreach**
- Use ROI calculator in emails
- Link to case studies
- Reference video demos
- Include before/after graphics

### Week 2 Actions

**1. Measure Impact**
```bash
# Track metrics:
# - Gumroad product page views (Analytics dashboard)
# - Streamlit app visitors (Google Analytics)
# - Video views (YouTube Analytics)
# - Cold outreach reply rate (CRM)
```

**2. Iterate Based on Data**
- Which case study gets most views? → Create more like it
- Which video has best retention? → Replicate that style
- Which ROI calc inputs are most common? → Add presets

**3. Plan Next Sprint**
Options:
- Revenue-Sprint product finalization
- Platform profiles (Upwork, Contra, Freelancer.com)
- GitHub Sponsors setup + tiers
- Additional case studies (Insight Engine, Scraper)

---

## Troubleshooting

### Problem: Agent Reports Blocker

**Symptom**: Agent says "Waiting for [dependency]"

**Solution**:
```bash
# Check dependency status
bd show beads-dependency-id

# If upstream delayed, reassign agent
bd update beads-blocked-task --assignee=different-agent

# Or give agent different work
# Find available tasks: bd ready
# Assign: bd update beads-xxx --assignee=blocked-agent
```

### Problem: QA Gate Fails

**Symptom**: QA reports >5% failure rate

**Solution**:
```bash
# Create fix tasks
bd create --title="Fix: [specific issue]" --type=task --priority=0

# Assign to responsible agent
bd update beads-fix --assignee=original-agent

# Agent fixes, then re-run QA
# QA re-validates: "Run Gate [N] validation again"
```

### Problem: Agent Stuck/Unresponsive

**Symptom**: Agent idle >30 min with active task

**Solution**:
```bash
# Check agent output
# Tell Claude: "Show me output for [agent-name]"

# If stuck, stop agent
# Tell Claude: "Stop [agent-name] task"

# Reassign task
bd update beads-stuck-task --assignee=different-agent
```

### Problem: Git Merge Conflict

**Symptom**: Two agents modified same file

**Prevention**:
- Task assignments ensure no file overlap (see spec)

**If it happens**:
```bash
# Manually resolve
git status  # See conflicted files
code path/to/conflicted/file  # Fix conflicts
git add path/to/conflicted/file
git commit -m "fix: Resolve merge conflict in [file]"

# Notify both agents
# Tell Claude: "Notify [agent-1] and [agent-2] about conflict resolution"
```

### Problem: Agent Output Quality Low

**Symptom**: QA flags quality issues repeatedly

**Solution**:
1. Review agent prompt in spec - is it clear enough?
2. Provide example output: "Here's what good looks like: [example]"
3. Give specific feedback: "Include 15+ criteria, not just 5"
4. If persistent, reassign to different agent type

---

## Success Criteria

### Sprint Completion Checklist

Before calling sprint "done", verify:

- [ ] All 23 tasks closed: `bd list --status=completed | wc -l` shows 23
- [ ] Epic closed: `bd show $EPIC_ID` shows status=completed
- [ ] All files committed: `git status` shows clean
- [ ] Changes pushed: `git log origin/main -1` matches local
- [ ] Beads synced: `bd sync --status` shows up-to-date
- [ ] Team deleted: `~/.claude/teams/content-dev-team/` does not exist
- [ ] All agents shutdown: No active teammates
- [ ] QA Gate 4 passed: 100% validation
- [ ] Portfolio status updated: `~/.claude/reference/freelance/content-assets.md` reflects new assets

### Quality Metrics

Target metrics (from spec):

- [x] **23/23 deliverables completed** (100%)
- [x] **≤12 hours wall-clock time** (vs 45h sequential)
- [x] **≥90% QA pass rate** per wave
- [x] **≤5 critical issues** in final validation
- [x] **Zero git merge conflicts**

### Impact Metrics (Track Post-Sprint)

Week 1 targets:
- 50+ ROI calculator sessions
- 100+ video views (total across all 5)
- 20+ Gumroad wishlist adds
- 5+ cold outreach replies

Month 1 targets:
- 5+ Gumroad purchases (screenshots + videos impact)
- 3+ discovery calls booked (case studies impact)
- 50+ competitive matrix views (SEO impact)

---

## Command Reference Quick Sheet

```bash
# Beads task management
bd create --title="Task name" --type=task --priority=0-4
bd list --status=open|in_progress|completed
bd show beads-xxx
bd update beads-xxx --status=in_progress --assignee=agent-name
bd close beads-xxx beads-yyy beads-zzz  # Close multiple
bd dep add beads-dependent beads-blocker  # Add dependency
bd ready  # Show tasks ready to work (unblocked)
bd sync  # Sync with git remote
bd stats  # Project statistics

# Git workflow
git status
git add content/ docs/
git commit -m "message"
git push origin main

# File operations
mkdir -p content/{video,visual,business,case-studies}
ls -lh content/video/
cat content/video/script.md
```

---

## Contact & Support

**If you get stuck**:
1. Re-read the spec: `.claude/specs/CONTENT_DEV_TEAM_SPEC.md`
2. Check this runbook's Troubleshooting section
3. Review agent prompts - they have detailed instructions
4. Use `bd prime` for Beads command reference

**For Beads issues**:
```bash
bd doctor  # Check for problems
bd prime   # Show full command reference
```

**For team/agent issues**:
- Agents should be autonomous - let them work
- Only intervene if >30min idle with active task
- Trust the QA validation process

---

**Good luck with your sprint! 🚀**

**Remember**: The goal is 23 assets in 8-12 hours. Let the agents work in parallel, validate at gates, and don't micromanage between waves.
