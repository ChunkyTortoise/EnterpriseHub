# Content Development Team Specification Package

**Version**: 1.0
**Created**: 2026-02-16
**Purpose**: Parallel content asset creation using AI agent swarm

---

## 📦 What's Included

This specification package provides everything needed to execute a **23-asset content development sprint** using a coordinated team of 5 AI agents working in parallel.

### Core Documents

| Document | Purpose | Read Time | Use When |
|----------|---------|-----------|----------|
| **`CONTENT_DEV_TEAM_SPEC.md`** | Complete technical specification | 30 min | Planning and agent design |
| **`CONTENT_DEV_EXECUTION_RUNBOOK.md`** | Step-by-step execution guide | 20 min | During sprint execution |
| **`CONTENT_DEV_QUICK_REFERENCE.md`** | One-page cheat sheet | 5 min | Quick lookups during sprint |
| **`preflight-check.sh`** | Pre-flight validation script | 2 min | Before starting Session 1 |

---

## 🎯 Sprint Overview

### What You'll Create

**23 high-impact content assets** across 4 categories:

1. **Video Assets** (6) - Scripts for product demos and recording guide
2. **Visual Assets** (6) - Screenshot specs and graphics designs
3. **Technical Assets** (5) - Competitive matrices and ROI calculator
4. **Marketing Copy** (6) - Executive docs and case studies

### Why This Matters

Based on February 2026 portfolio audit findings:
- **Missing videos** cited as #1 gap across all repos
- **No screenshots** blocking Gumroad product launches
- **No ROI calculator** losing 40% of enterprise leads
- **No competitive comparisons** causing trust issues

**Revenue Impact**: $2K-$10K unlock potential (audit-validated)

### Time Savings

| Approach | Duration | Cost |
|----------|----------|------|
| **Sequential** (you alone) | 45 hours | 45h |
| **Parallel** (5-agent team) | 8-12 hours | 8-12h |
| **Time Saved** | 33-37 hours | **73-82%** |

---

## 🚀 Quick Start

### Prerequisites

- [ ] EnterpriseHub repo cloned and current
- [ ] Git working directory clean (or changes committed)
- [ ] Beads installed and initialized (`bd stats` works)
- [ ] 4-hour uninterrupted block available (Session 1)
- [ ] Read this README (you are here!)

### Step 1: Validate Environment

```bash
cd /Users/cave/Documents/GitHub/EnterpriseHub
bash .claude/specs/preflight-check.sh
```

**Expected output**: `✅ PRE-FLIGHT PASSED` or `⚠️ PASSED WITH WARNINGS`

If failed, fix issues before proceeding.

### Step 2: Read the Runbook (20 minutes)

```bash
# Open in your editor
code .claude/specs/CONTENT_DEV_EXECUTION_RUNBOOK.md

# Or read in terminal
cat .claude/specs/CONTENT_DEV_EXECUTION_RUNBOOK.md | less
```

Focus on **Session 1** steps (you'll execute these first).

### Step 3: Keep Quick Reference Handy

```bash
# Open in split pane or second monitor
code .claude/specs/CONTENT_DEV_QUICK_REFERENCE.md
```

You'll reference this during execution for quick command lookups.

### Step 4: Start Session 1

Follow **Session 1, Step 1.1** in the Runbook:
- Create 23 tasks via `bd create`
- Set up dependencies via `bd dep add`
- Spawn 5-agent team
- Begin Wave 1 execution

---

## 📚 Documentation Guide

### For First-Time Users

Read in this order:

1. **This README** (5 min) - Overview and quick start
2. **CONTENT_DEV_QUICK_REFERENCE.md** (5 min) - Get familiar with commands and phases
3. **CONTENT_DEV_TEAM_SPEC.md** (30 min) - Understand agent roles, deliverables, and quality gates
4. **CONTENT_DEV_EXECUTION_RUNBOOK.md** (20 min) - Learn step-by-step execution

**Total**: ~60 minutes prep time (saves 37+ hours in execution)

### During Sprint Execution

**Primary reference**: `CONTENT_DEV_EXECUTION_RUNBOOK.md`
**Quick lookups**: `CONTENT_DEV_QUICK_REFERENCE.md`
**Deep dives**: `CONTENT_DEV_TEAM_SPEC.md` (for agent prompts, quality criteria, etc.)

### For Troubleshooting

1. Check **Runbook Troubleshooting section** first
2. Review **Spec section** related to your issue
3. Use `bd prime` for Beads command help
4. Check agent prompts in Spec (they have detailed instructions)

---

## 🏗️ Architecture Overview

### Team Structure

```
Content Team Lead (portfolio-coordinator)
│
├─ Video Agent (content-marketing-engine)
│  └─ 6 video assets
│
├─ Visual Agent (dashboard-design)
│  └─ 6 visual specs
│
├─ Tech Agent (architecture-sentinel)
│  └─ 5 technical docs
│
├─ Copy Agent (content-marketing-engine)
│  └─ 6 marketing assets
│
└─ QA Agent (quality-gate)
   └─ 4 validation gates
```

### Execution Phases

```
Session 1 (4h):  Setup → Wave 1 → Gate 1
Session 2 (6h):  Wave 2 → Gate 2 → Wave 3 → Gate 3
Session 3 (2h):  Gate 4 → Commit → Shutdown
```

### Parallelization Strategy

**Wave 1**: 3 agents work simultaneously (video + visual + tech)
**Wave 2**: 2 agents work simultaneously (tech + copy)
**Wave 3**: 2 agents work simultaneously (copy + visual)
**Wave 4**: Sequential (QA validation, then wrap-up)

---

## 📊 Deliverables Matrix

### Video Assets (Wave 1, 9h effort → 2h wall-clock)

| Asset | Owner | Output Location |
|-------|-------|----------------|
| EnterpriseHub 6:30 script | Video | `content/video/enterprisehub-final.md` |
| AgentForge 2-min script | Video | `content/video/agentforge-demo-script.md` |
| DocQA 5-min script | Video | `content/video/docqa-demo-script.md` |
| Prompt Lab pattern script | Video | `content/video/prompt-lab-script.md` |
| LLM Starter quickstart | Video | `content/video/llm-starter-script.md` |
| Recording guide | Video | `content/video/RECORDING_GUIDE.md` |

### Visual Assets (Wave 1 & 3, 7h effort → 2.5h wall-clock)

| Asset | Owner | Output Location |
|-------|-------|----------------|
| Screenshot master plan | Visual | `content/visual/SCREENSHOT_PLAN.md` |
| AgentForge screenshots | Visual | `content/visual/agentforge-screenshots.md` |
| DocQA screenshots | Visual | `content/visual/docqa-screenshots.md` |
| Insight screenshots | Visual | `content/visual/insight-screenshots.md` |
| Scraper screenshots | Visual | `content/visual/scraper-screenshots.md` |
| Metrics graphics | Visual | `content/visual/metrics-graphics-spec.md` |

### Technical Assets (Wave 1 & 2, 12h effort → 3.5h wall-clock)

| Asset | Owner | Output Location |
|-------|-------|----------------|
| AgentForge competitive matrix | Tech | `ai-orchestrator/docs/COMPETITIVE_MATRIX.md` |
| DocQA competitive matrix | Tech | `docqa-engine/docs/COMPETITIVE_MATRIX.md` |
| EnterpriseHub vs DIY | Tech | `docs/COMPETITIVE_ANALYSIS.md` |
| ROI calculator spec | Tech | `content/business/roi-calculator-spec.md` |
| ROI calculator code | Tech | `content/business/roi_calculator.py` |

### Marketing Copy (Wave 2 & 3, 13h effort → 4h wall-clock)

| Asset | Owner | Output Location |
|-------|-------|----------------|
| EnterpriseHub For-Prospects | Copy | `docs/FOR_PROSPECTS.md` |
| AgentForge For-Executives | Copy | `ai-orchestrator/docs/FOR_EXECUTIVES.md` |
| DocQA For-Executives | Copy | `docqa-engine/docs/FOR_EXECUTIVES.md` |
| EnterpriseHub case study | Copy | `content/case-studies/enterprisehub-case-study.md` |
| AgentForge case study | Copy | `content/case-studies/agentforge-case-study.md` |
| DocQA case study | Copy | `content/case-studies/docqa-case-study.md` |

---

## ✅ Quality Standards

### Quality Gates (4 checkpoints)

Each wave ends with validation:

- **Gate 1** (Wave 1): Markdown linting, link checking, structure validation
- **Gate 2** (Wave 2): Code execution, readability scoring, citation checking
- **Gate 3** (Wave 3): Format compliance, quantification, specs completeness
- **Gate 4** (Final): Comprehensive review, brand consistency, git cleanliness

**Pass Threshold**: 90-100% depending on gate (see Spec for details)

### Success Metrics

Sprint completes when:

✅ All 23 deliverables exist
✅ All quality gates passed
✅ All tasks closed in Beads
✅ All changes committed & pushed
✅ Team gracefully shutdown
✅ Portfolio status updated

---

## 🔧 Tools & Commands

### Essential Commands

```bash
# Pre-flight
bash .claude/specs/preflight-check.sh

# Beads
bd create --title="Task" --type=task --priority=0
bd list --status=open
bd ready
bd update beads-xxx --status=in_progress
bd close beads-xxx beads-yyy beads-zzz
bd sync

# Git
git status
git add content/ docs/
git commit -m "feat: Add 23 content assets"
git push origin main
```

### Tell Claude (Team Operations)

```
"Create team: content-dev-team"
"Spawn all 5 agents in parallel using spec"
"Assign Wave 1 tasks to agents"
"QA agent: Run Gate 1 validation"
"Send shutdown_request to all agents"
"Delete team"
```

---

## 🎯 Expected Outcomes

### Immediate (Sprint Completion)

- ✅ **23 content assets created** in 8-12 hours (vs 45h sequential)
- ✅ **4 quality gates passed** with 90-100% validation
- ✅ **All files committed** to git with detailed commit message
- ✅ **Team cleanly shutdown** with no orphaned processes
- ✅ **Portfolio updated** to reflect new assets

### Week 1 Post-Sprint

Using the created assets:
- 🎬 Record 5 product demo videos (using scripts)
- 📸 Capture 20+ screenshots (following specs)
- 🚀 Deploy ROI calculator (Streamlit Cloud)
- 🛍️ Update Gumroad pages (add visuals)
- 📧 Launch cold outreach (link to resources)

### Month 1 Impact

Target metrics:
- 50+ ROI calculator sessions
- 100+ video views (combined)
- 20+ Gumroad wishlist adds
- 5+ Gumroad purchases
- 3+ discovery calls booked

**Revenue Impact**: $2K-$5K in Month 1 (conservative estimate)

---

## 🐛 Troubleshooting

### Common Issues

| Issue | Quick Fix | Details |
|-------|-----------|---------|
| Agent stuck | `"Show output for [agent]"` | Runbook §3.1 |
| QA gate fails | Create fix tasks, reassign | Runbook §3.2 |
| Dependency blocking | Check with `bd show`, find other work | Runbook §3.3 |
| Git conflict | Resolve manually, notify agents | Runbook §3.4 |
| Pre-flight fails | Fix issues listed in output | Runbook Pre-Flight |

### Get Help

1. **First**: Check Runbook Troubleshooting section
2. **Second**: Review Spec section for your issue
3. **Third**: Use `bd prime` or `bd doctor` for Beads issues
4. **Fourth**: Review agent prompts in Spec (they have detailed instructions)

---

## 📈 After the Sprint

### Immediate Next Steps (Day 1-2)

1. **Record videos** using scripts from `content/video/`
2. **Capture screenshots** following specs from `content/visual/`
3. **Deploy ROI calculator** to Streamlit Cloud
4. **Test all outputs** (watch videos, try calculator, review docs)

### Week 1 Actions

1. Update Gumroad product pages (add screenshots, videos)
2. Update repository READMEs (link to new docs)
3. Launch cold outreach campaign (use ROI calc, case studies)
4. Publish videos to YouTube/Vimeo

### Week 2 Review

1. Measure impact (GA4, Gumroad analytics, outreach replies)
2. Iterate based on data (which assets drove conversions?)
3. Plan next sprint (Revenue-Sprint products? Platform profiles?)
4. Document lessons learned

---

## 📝 Feedback & Iteration

### After Sprint Retrospective

Consider:
- Which agents were most efficient?
- Which quality gates caught issues?
- What took longer than expected?
- What could be parallelized better?
- How well did communication work?

**Document in**: Update this README or Spec with lessons learned

### For Next Sprint

Reuse this framework for:
- Revenue-Sprint product finalization (14h → 3-4h)
- Platform profile creation (20h → 5-6h)
- Additional case studies (12h → 3h)
- Video course modules (40h → 10-12h)

**Same structure, different deliverables!**

---

## 🔗 References

### Portfolio Context

- **Audit reports**: `~/.claude/teams/portfolio-dev-team/audit-*.md`
- **Deployment strategy**: `~/.claude/teams/portfolio-dev-team/deployment-strategy.md`
- **Content inventory**: `~/.claude/reference/freelance/content-assets.md`
- **Portfolio status**: `~/.claude/reference/freelance/portfolio-repos.md`

### Team Documentation

- **This package**: `.claude/specs/` (you are here)
- **Agent types**: `.claude/agents/` (if custom agents added)
- **Project context**: `CLAUDE.md` (domain knowledge for agents)

### External Resources

- **Beads documentation**: https://github.com/beadsinc/beads
- **Team coordination**: Claude Code team features
- **MCP servers**: `.mcp.json` configuration

---

## 📄 License & Usage

This specification package is part of the EnterpriseHub project and follows the same license (see `LICENSE` in repo root).

**Reuse**: Feel free to adapt this framework for your own portfolio sprints. Just update:
- Agent assignments (different repos)
- Deliverables list (your assets)
- Quality criteria (your standards)
- Timeline (your availability)

---

## ✨ Summary

**What**: 23-asset content development sprint via 5-agent team
**Why**: Fill critical portfolio gaps identified in Feb 2026 audit
**How**: Parallel execution with quality gates at each wave
**Time**: 8-12 hours (vs 45h sequential) = 73-82% savings
**Impact**: $2K-$10K revenue unlock potential

**Status**: ✅ Ready to execute
**Next Step**: Run `bash .claude/specs/preflight-check.sh`

---

**Questions?** Re-read the relevant section above or check the Runbook.

**Ready to start?** Begin with Session 1, Step 1.1 in `CONTENT_DEV_EXECUTION_RUNBOOK.md`

**Good luck with your sprint! 🚀**
