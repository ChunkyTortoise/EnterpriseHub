# AUDIT MANIFEST: GHL Real Estate AI Handoff

This manifest tracks the forensic audit of the repository to prepare the "Golden State" deliverable for Jorge.

## 🟢 KEEP (Golden Root & Core Package)
*Essential files for the application and professional repository standards.*

- `ghl_real_estate_ai/` - **Source of Truth** (Core Logic)
- `app.py` - Main Entry Point
- `README.md` - Primary Documentation
- `JORGE_START_HERE.md` - (To be created) White Glove Handoff Map
- `requirements.txt` - Production Dependencies
- `pyproject.toml` - Project Configuration
- `railway.json` - Deployment Configuration
- `.env.example` - Environment Template
- `.gitignore` - Git Configuration
- `LICENSE` - Legal
- `AUTHORS.md` - Project Authors
- `CHANGELOG.md` - Project History
- `docs/` - Canonical Documentation
- `tests/` - Test Suite
- `assets/` - Professional Assets
- `utils/`, `modules/`, `prompts/`, `scenarios/`, `scripts/`, `pages/`, `data/`, `portfolio/` - Core Directories

## 🟡 ARCHIVE (Move to `_archive/` or `docs/`)
*Files to be preserved for history or moved to appropriate subdirectories.*

### Move to `_archive/sessions/`
- `SESSION_HANDOFF*.md` (50+ files)
- `SESSION_HANDOFF_OLD.md`

### Move to `assets/screenshots/`
- `Screenshot_*.jpg` (10 files)
- `imported_screenshots/`

### Move to `docs/` (Professional Manuals)
- `DEPLOY_NOW_RAILWAY.md`
- `RAILWAY_DEPLOYMENT_GUIDE.md`
- `STREAMLIT_DEPLOYMENT.md`
- `MONITORING_SETUP_GUIDE.md`
- `INCIDENT_RESPONSE_PLAYBOOK.md`
- `WEBHOOK_SETUP_INSTRUCTIONS.md`
- `DEPLOYMENT_INSTRUCTIONS.md`
- `DEPLOYMENT_CHECKLIST.md`

### Move to `_archive/deliveries/`
- `JORGE_DELIVERY_JAN_03/`
- `JORGE_FINAL_DELIVERY.md`
- `JORGE_HANDOFF_EMAIL.txt`
- `EMAIL_TO_JORGE_2026-01-04.md`

### Move to `_archive/strategy/`
- `90_DAY_ACTION_PLAN.md`
- `GO_TO_MARKET_CHECKLIST.md`
- `STRATEGIC_IMPLEMENTATION_ROADMAP.md`
- `FINAL_DEPLOYMENT_GAMEPLAN_2026-01-05.md`
- `FINAL_SUMMARY.md`
- `PRICING_ANALYSIS_AND_STRATEGY.md`
- `COMPETITIVE_POSITIONING_ANALYSIS.md`
- `CAYMAN_RODEN_PROFESSIONAL_SERVICES_CATALOG.md`
- `SERVICES_CATALOG_REFINEMENT.md`
- `PORTFOLIO_FINALIZATION_PLANS.md`

### Move to `_archive/internal/`
- `AGENT_SWARM_PERSONAS_2026-01-05.md`
- `PERSONA_0_MASTER_ORCHESTRATOR.md`
- `PERSONA_IMPROVEMENTS_COMPLETE.md`
- `PERSONA_SWARM_ORCHESTRATOR.md`
- `Persona_Orchestrator.md`
- `PERSONA0.md`
- `PERSONA_GHL_AUDITOR.md`
- `VERIFICATION_REPORT_2026-01-05.md`
- `ROVODEV_ACCOUNT_SWITCHING.md`
- `EnterpriseHub.code-workspace`
- `agent_docs/`
- `automation/`
- `agentforge/`
- `better-t-app/`

## 🔴 DELETE (Immediate Cleanup)
*Junk, logs, or temporary development artifacts.*

- `ghl_test_results.log`
- `tmp_rovodev_*`
- `coverage.json`
- `job_desc.txt`
- `courses.md`
- `htmlcov/`

## ❓ FLAG (Requires Decision/Action)
- `ghl-real-estate-ai/` - **Action**: Diff with `ghl_real_estate_ai/`. If redundant, archive.
- `ghl-real-estate-ai-starter/` - **Action**: Archive as "Starter Kit" or delete if redundant.
- `demo_app.py` - **Action**: Is this used for Jorge's demo? If not, archive.
