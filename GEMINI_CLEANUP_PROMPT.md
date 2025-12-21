# TASK: Clean Up Development Artifacts in EnterpriseHub

## PROJECT CONTEXT

EnterpriseHub is a production-ready Streamlit application with 7 business intelligence modules. The codebase has accumulated **50+ development artifacts**, planning documents, session notes, marketing templates, personal files, and system cache files that were useful during development but are now redundant or outdated.

**Current Project State:**
- Production-ready application with 220+ tests
- Core code in: `app.py`, `modules/`, `utils/`, `tests/`
- Essential docs: `README.md`, `CLAUDE.md`, `modules/README_*.md`
- Archive folder: `_archive/` (read-only historical content)

## YOUR MISSION

Review all files in the repository and create a **DELETE/ARCHIVE/REVISE/MOVE plan** for development artifacts. Then execute the plan systematically.

---

## CLEANUP CATEGORIES & ACTIONS

### 🗑️ CATEGORY 1: DELETE IMMEDIATELY
**Files to completely remove (outdated, redundant, or one-time use):**

#### Root Directory Files
- `/evaluation_prompt.md` - One-time decision framework
- `/.aider.chat.history.md` - Chat logs (not source controlled)
- `/.aider.input.history` - Aider CLI command history
- `/CRITICAL_FIXES_NEEDED.md` - Task list (completed)
- `/CRITICAL_FIXES_APPLIED.md` - Already logged in git history
- `/CLEANUP_REPORT.md` - Historical report (info in git)
- `/IMPLEMENTATION_SUMMARY.md` - Superseded by git commits
- `/SCREENSHOT_AUTOMATION_SUMMARY.md` - Details in code comments
- `/UI_UX_ENHANCEMENT_SUMMARY.md` - Details in git history
- `/UI_UX_IMPROVEMENT_REPORT.md` - Duplicate of above
- `/HANDOFF_SESSION.md` - Stale session handoff
- `/VIDEO-SCRIPT.md` - Demo video scripts (completed artifact)
- `/.gitignore.bak` - Backup file (redundant)
- `/.resume_timestamp` - Temporary tracking file

#### System/Cache Files
- `/.DS_Store` - macOS system file (should be in .gitignore)
- `/.aider.tags.cache.v4/` - Cache directory (entire folder)
- `/.coverage` - pytest coverage data file
- `/htmlcov/` - HTML coverage reports (entire directory)
- `/customer_clusters.png` - Test output file
- `/elbow_method.png` - Test output file
- `/.mypy_cache/` - mypy type checker cache
- `/.pytest_cache/` - pytest cache
- `/.ruff_cache/` - ruff linter cache

#### Assets Directory Files
- `/assets/SESSION_SUMMARY.md` - Stale session notes
- `/assets/SCREENSHOT_CHECKLIST.md` - Redundant with SCREENSHOT_GUIDE
- `/assets/QUICK_COPY_PASTE.md` - Duplicate of READY_TO_POST.md
- `/assets/Certs.md` - Personal certifications (belongs in resume, not project)
- `/assets/Courses.md` - Personal courses list (if exists)

#### .agent/workflows/ Directory (MAJOR CLEANUP)
- `/.agent/workflows/claude_sonnet_4.5_jailbreak.md` - Unrelated security research
- `/.agent/workflows/claude_sonnet_4.5_oneshot_jailbreak.md` - Unrelated security research
- `/.agent/workflows/coursera_text.txt` - Random text file
- `/.agent/workflows/project_comet_red_team/` - Entire security research project (DELETE entire folder)
- `/.agent/workflows/.snapshots/` - Workflow snapshots (temporary files)
- `/.agent/workflows/CLEANUP_PLAN.md` - Workflow planning doc
- `/.agent/workflows/HOW_TO_USE_SKILLS.md` - Workflow instructions
- `/.agent/workflows/QUICK_REFERENCE.md` - Workflow reference
- `/.agent/workflows/SKILLS_CATALOG.md` - Workflow catalog

**Criteria:** Files that duplicate git history, completed one-time tasks, stale session notes, system caches, or unrelated security research.

---

### 📦 CATEGORY 2: MOVE TO _archive/
**Files to preserve for historical reference but remove from active repo:**

#### Project Status Files
- `/SESSION_STATE.md` → `_archive/session_notes/SESSION_STATE_2025-12-19.md`
- `/PROJECT_STATE.md` → `_archive/project_tracking/PROJECT_STATE_FINAL.md`
- `/PORTFOLIO-ENHANCEMENT-STATE.md` → `_archive/project_tracking/PORTFOLIO_ENHANCEMENT_COMPLETE.md`

#### Already Archived (Keep as-is)
- `/_archive/reports/PRIORITY_4_COMPLETION_REPORT.md` (already archived, keep)
- `/_archive/reports/REPO_CLEANUP_RECOMMENDATIONS.md` (already archived, keep)
- `/_archive/reports/CODE_QUALITY_REPORT.md` (already archived, keep)
- `/_archive/reports/REVIEW_SUMMARY.md` (already archived, keep)
- `/_archive/documentation/RESUME.md` (already archived, keep)

**Criteria:** Project snapshots and session handoffs that document completed phases.

---

### ✏️ CATEGORY 3: REVISE & CONSOLIDATE
**Files to merge, update, or significantly revise:**

#### A. Consolidate Launch/Startup Guides
**Current files:**
- `/48HR-EARNING-GAMEPLAN.md`
- `/EARNING_POTENTIAL_ROADMAP.md`
- `/assets/READY_TO_POST.md`
- `/assets/START_HERE.md`

**Action:** Create **single consolidated file** → `/MONETIZATION_GUIDE.md`
- Merge best content from all 4 files
- Remove redundant sections
- Update for current project state (already production-ready)
- Add "Last Updated" timestamp
- **Delete originals after consolidation**

#### B. Consolidate Screenshot/Demo Instructions
**Current files:**
- `/assets/SCREENSHOT_GUIDE_SIMPLE.md`
- `/assets/SCREENSHOT-INSTRUCTIONS.md`
- `/assets/DEMO_VIDEO_GUIDE.md`
- `/assets/DEMO-VIDEO-INSTRUCTIONS.md`
- `/assets/DEMO_VIDEO_SCRIPT_60SEC.md`
- `/QUICK_START_SCREENSHOTS.md`

**Action:** Create **single consolidated file** → `/docs/MEDIA_PRODUCTION_GUIDE.md`
- Merge all screenshot instructions (keep simplified version)
- Merge all demo video content
- Include 60-second script
- Organize into clear sections: Screenshots, Demo Videos, Scripts
- **Delete originals after consolidation**

#### C. Organize Marketing Templates
**Current files:**
- `/assets/LINKEDIN_POSTS.md`
- `/assets/UPWORK_PROPOSALS.md`
- `/TESTIMONIALS.md` (marketing/social proof content)

**Action:** Create new directory `/marketing/` and reorganize
- `/marketing/LINKEDIN_TEMPLATES.md` (updated with current features)
- `/marketing/UPWORK_TEMPLATES.md` (updated with current tech stack)
- `/marketing/TESTIMONIALS.md` (move from root)
- **Delete originals from /assets/ and root after moving**

#### D. Simplify Module Prioritization
**Current file:**
- `/assets/MODULE_PRIORITIZATION.md`

**Action:** Revise or delete
- If all modules are complete: **DELETE**
- If still relevant for future work: **REVISE** to reflect current priorities

#### E. Update .gitignore
**Action:** Add missing entries to `.gitignore`
```gitignore
# macOS
.DS_Store

# Coverage
.coverage
htmlcov/

# Cache directories
.mypy_cache/
.pytest_cache/
.ruff_cache/
.aider.tags.cache.v4/

# Temporary files
.resume_timestamp
*.bak

# Test outputs
customer_clusters.png
elbow_method.png

# Agent workflows (if keeping)
.agent/workflows/.snapshots/
```

---

### 🔁 CATEGORY 4: MOVE (Reorganize within repo)
**Files that belong in different locations:**

#### Personal/Resume Content
**Current locations:**
- `/assets/Certs.md` → Consider moving to `_archive/personal/` or deleting entirely
- Personal certification lists don't belong in project repo

#### Documentation Improvements
**Potential moves:**
- `/DEMO.md` → `/docs/DEMO_GUIDE.md` (if keeping)
- `/Deploy.md` → `/docs/DEPLOYMENT.md` (if keeping)
- `/FAQ.md` → `/docs/FAQ.md` (if keeping)

---

### ✅ CATEGORY 5: KEEP AS-IS
**Essential files that should NOT be modified:**

**Core Application:**
- `/app.py` - Main application entry point
- `/modules/*.py` - All 7 module files
- `/utils/*.py` - All utility modules
- `/tests/**/*` - All test files
- `/requirements.txt`, `/dev-requirements.txt` - Dependencies
- `/.gitignore` - Git configuration (update, don't delete)
- `/LICENSE` - Legal

**Essential Documentation:**
- `/README.md` - Primary project documentation
- `/CLAUDE.md` - AI assistant context (project-specific)
- `/PORTFOLIO.md` - Portfolio presentation
- `/modules/README_SMART_FORECAST.md` - Module-specific docs
- `/modules/README_*.md` - All module READMEs
- `/_archive/**/*` - All archived content (read-only)

**Configuration & Assets:**
- `/.pre-commit-config.yaml` - Git hooks
- `/pyproject.toml` - Project configuration
- `/Makefile` - Build automation
- `/packages.txt` - System packages
- `/mypy_baseline.txt` - Type checking baseline
- `/assets/AUTOMATION_README.md` - Technical docs for automation scripts
- `/assets/logo.png` (if exists) - Visual assets
- `/scenarios/*.md` - Industry templates (keep)
- `/docs/ARCHITECTURE.md` - Architecture documentation

**Community Files:**
- `/CODE_OF_CONDUCT.md`
- `/CONTRIBUTING.md`
- `/SECURITY.md`
- `/SUPPORT.md`
- `/AUTHORS.md`
- `/CHANGELOG.md`
- `/.github/**/*` - GitHub templates

**Special Consideration - .agent/workflows/**
**Decision needed:** Should the entire `.agent/workflows/` directory be kept or removed?
- **Option A (Recommended):** DELETE entire directory if it's just workflow experiments
- **Option B:** Keep ONLY if actively using Claude Code Agent SDK for development
- **Assessment:** Most content appears to be skill libraries and unrelated security research

---

## EXECUTION PLAN

### PHASE 1: ASSESSMENT (provide this report first)
Before making ANY changes, provide a structured report:

```
# EnterpriseHub Cleanup Assessment Report

## Files to DELETE (count: X)
### Root Directory (count: X)
- [file path] - [reason]

### System/Cache Files (count: X)
- [file path] - [reason]

### Assets Directory (count: X)
- [file path] - [reason]

### .agent/workflows/ (count: X)
- [file path] - [reason]

## Files to ARCHIVE (count: X)
- [current path] → [new path] - [reason]

## Files to REVISE/CONSOLIDATE (count: X)
- [consolidation group name]
  - Source files: [list]
  - Output file: [path]
  - Changes: [summary]

## Files to MOVE (count: X)
- [current path] → [new path] - [reason]

## Files to KEEP (count: X)
- [category]: X files

## .gitignore Updates Needed
- [list of new entries]

## Estimated Impact
- Total files removed from root: X
- Total files removed from /assets/: X
- Total files removed from /.agent/workflows/: X
- Total space saved: ~X KB
- Consolidations: X files → Y files
- New directory structure: /marketing/, /docs/
```

### PHASE 2: EXECUTION (after approval)
1. **Create backup** of all files to be deleted/modified (zip archive)
2. **Update .gitignore** with new entries
3. **Execute deletions** in Category 1 (start with system/cache files)
4. **Execute archive moves** in Category 2
5. **Create new directories** (/marketing/, /docs/ if needed)
6. **Create consolidated files** in Category 3 (write new files first)
7. **Move files** in Category 4
8. **Delete source files** only after confirming consolidation/moves worked
9. **Update any internal references** (links in markdown files)
10. **Test application** still runs: `streamlit run app.py`
11. **Run tests**: `pytest --cov=modules --cov=utils -v`

### PHASE 3: VALIDATION
- Verify no broken markdown links
- Confirm application still launches
- Check all tests still pass
- Verify all essential docs remain intact
- Verify `_archive/` structure is clean
- Confirm .gitignore prevents system files from being tracked

---

## SAFETY RULES

❌ **NEVER DELETE/MODIFY:**
- Anything in `/modules/` (core application code)
- Anything in `/utils/` (shared utilities)
- Anything in `/tests/` (test suite)
- `README.md`, `CLAUDE.md`, `PORTFOLIO.md` (essential docs)
- `.gitignore`, `requirements.txt`, `LICENSE`, `.pre-commit-config.yaml`
- Code files (`.py`, `.toml`, `.yaml` configs)
- `/scenarios/` (industry templates)
- `/_archive/` (read-only)

✅ **ONLY DELETE/MODIFY:**
- Markdown files in root directory (excluding README/CLAUDE/PORTFOLIO.md)
- Files in `/assets/` that are planning/tracking/marketing documents
- Session state, project state, and handoff files
- Completed task lists and implementation summaries
- Redundant guides and instructions
- System cache files and macOS artifacts
- Personal resume/certification files
- Unrelated security research in `.agent/workflows/`

---

## SUCCESS CRITERIA

After cleanup, the repository should have:
- ✅ Clean root directory (only essential docs + new MONETIZATION_GUIDE.md)
- ✅ No redundant planning documents
- ✅ Consolidated guides in `/docs/` (max 1-2 well-organized files)
- ✅ Clear `/marketing/` directory for all promotional templates
- ✅ Organized `/_archive/` with dated historical content
- ✅ Updated `.gitignore` preventing system files from being tracked
- ✅ No duplicate or redundant markdown files
- ✅ Application still runs perfectly (`streamlit run app.py`)
- ✅ All tests still pass (`pytest --cov=modules --cov=utils -v`)
- ✅ All essential documentation intact
- ✅ Clear separation: code vs docs vs marketing vs archive

---

## DELIVERABLE

**First:** Provide the assessment report (Phase 1)
**Then:** After approval, execute the cleanup and provide:
- Summary of changes made (grouped by category)
- List of files deleted/moved/consolidated (with counts)
- New directory structure overview
- Any warnings or issues encountered
- Confirmation that application tested successfully
- Confirmation that tests pass
- Git commands to commit changes (if applicable)
