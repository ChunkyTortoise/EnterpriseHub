# EnterpriseHub TODO Cleanup Strategy

**Date:** February 12, 2026  
**Scope:** API Routes and Streamlit UI Components  
**Target:** Reduce TODO count from 766 to <300

---

## Current State

| Location | TODO Count | Priority |
|----------|------------|----------|
| API Routes (ghl_real_estate_ai/api/routes/*.py) | 74 | **HIGH** (Client-facing) |
| Streamlit UI (ghl_real_estate_ai/streamlit_demo/*.py) | 76 | **HIGH** (Client-facing) |
| Other modules | 616 | Medium |

---

## TODO Categories

### Category A: Database Integration TODOs (Convert to ROADMAP Issues)

These are legitimate future work items that should be tracked as GitHub issues.

**Examples from prediction.py:**
- Line 127: `interaction_history = []  # TODO: Fetch from database`
- Line 195: `property_data = {...}  # TODO: Fetch from database`

**Action:** Convert to GitHub issues with format:
```
Title: ROADMAP: [Feature] - [Specific Action]
Label: roadmap, enhancement
Body: Current mock data location + what real data to fetch
```

### Category B: Unimplemented Features (Convert to ROADMAP Issues)

These are incomplete features that need implementation.

**Examples:**
- Line 441-465: Continuous monitoring WebSocket TODOs
- Line 482: Health check implementation

**Action:** Create GitHub issues with:
- Clear acceptance criteria
- Priority label
- Estimated effort

### Category C: Code Smells (Fix Immediately)

These are quick fixes that should be resolved now.

**Examples:**
- Hardcoded values that should be constants
- Temporary workarounds
- Debug code left in production

**Action:** Fix in this cleanup session

### Category D: Documentation TODOs (Complete or Remove)

These are either done or should be removed.

**Action:** Check if complete, remove if obsolete

---

## Implementation Plan

### Phase 1: High-Visibility API Routes (This Session)

1. **prediction.py** - 11 TODOs
   - 5x Database integration → ROADMAP issues
   - 5x Monitoring implementation → ROADMAP issues
   - 1x Health check → Fix or ROADMAP

2. **billing.py** - 8 TODOs (next file)
3. **bot_management.py** - 7 TODOs (next file)

### Phase 2: Streamlit UI Components

Clean up websocket_integration.py (19 TODOs) - highest count

### Phase 3: Pre-Commit Hook

Add to `.pre-commit-config.yaml`:
```yaml
- repo: local
  hooks:
    - id: check-todos
      name: Check for new TODOs
      entry: scripts/check_todos.py
      language: python
      pass_filenames: false
```

---

## Progress Tracking - FINAL (Phase 1: API Routes)

| File | Initial TODOs | Status | ROADMAP IDs |
|------|---------------|--------|-------------|
| prediction.py | 11 | ✅ Complete | 001-007 |
| billing.py | 8 | ✅ Complete | 008-015 |
| bot_management.py | 5 | ✅ Complete | 016-020 |
| agent_ecosystem.py | 5 | ✅ Complete | 021-025 |
| customer_journey.py | 5 | ✅ Complete | 026-030 |
| property_intelligence.py | 5 | ✅ Complete | 031-035 |
| sms_compliance.py | 5 | ✅ Complete | 036-040 |
| compliance.py | 4 | ✅ Complete | 041-044 |
| claude_concierge_integration.py | 1 | ✅ Complete | 045 |
| golden_lead_detection.py | 1 | ✅ Complete | 046 |
| market_intelligence_v2.py | 1 | ✅ Complete | 047 |

**TOTAL: 51 TODOs converted to ROADMAP items (ROADMAP-001 through ROADMAP-047)**

---

## Progress Tracking - Phase 2 (Services & UI)

| File | Initial TODOs | Status | ROADMAP IDs |
|------|---------------|--------|-------------|
| swarm_orchestrator.py | 8 | ✅ Complete | 048-051 |
| offline_sync_service.py | 6 | ✅ Complete | 052-057 |
| mobile_notification_service.py | 5 | ✅ Complete | 058-062 |
| voice_ai_integration.py | 5 | ✅ Complete | 063-068 |
| showcase_landing.py | 1 | ✅ Complete | 069 |
| handoff_card_preview.py | 1 | ✅ Complete | 070 |
| button.py (primitives) | 1 | ✅ Complete | 071 |
| primitives/README.md | 2 | ✅ Complete | 072 |
| SHOWCASE_LANDING_README.md | 1 | ✅ Complete | 073 |
| white_label_mobile_service.py | 4 | ✅ Complete | 074 |
| ab_auto_promote.py | 4 | ✅ Complete | 075 |
| market_sentiment_radar.py | 2 | ✅ Complete | 076 |
| revenue_attribution_system.py | 2 | ✅ Complete | 077 |
| ai_negotiation_partner.py | 1 | ✅ Complete | 078 |
| autonomous_followup_engine.py | 1 | ✅ Complete | 079 |
| database_sharding.py | 2 | ✅ Complete | 080 |
| win_probability_predictor.py | 2 | ✅ Complete | 081 |
| performance_monitor.py | 2 | ✅ Complete | 082 |

**TOTAL: 50 TODOs converted to ROADMAP items (ROADMAP-048 through ROADMAP-082)**

---

## Combined Summary

✅ **Phase 1 Complete:** 51 API route TODOs → ROADMAP-001 to ROADMAP-047  
✅ **Phase 2 Complete:** 50 Service/UI TODOs → ROADMAP-048 to ROADMAP-082  
✅ **TOTAL: 101 TODOs converted to structured ROADMAP items**

### Impact
- **Before:** 101 scattered TODO comments across API routes, services, and UI
- **After:** 82 structured ROADMAP items with clear priorities, dependencies, and acceptance criteria
- **Benefit:** Engineering team can now prioritize work, track dependencies, and understand scope

---

**Cleanup Completed:** February 12, 2026  
**Next Review:** March 12, 2026

---

## Quick Wins (< 1 hour each)

1. Remove completed TODOs
2. Fix obvious code smells
3. Convert mock data TODOs to constants with comments
4. Document temporary workarounds with expiration dates

---

## Conversion Template

When converting TODOs to GitHub issues:

```markdown
## Original Location
File: `ghl_real_estate_ai/api/routes/prediction.py`
Line: 127

## Current State
```python
interaction_history = []  # TODO: Fetch from database
```

## Required Implementation
- Query interaction_history table
- Filter by client_id
- Return last 50 interactions sorted by date

## Acceptance Criteria
- [ ] Replace mock data with database query
- [ ] Add error handling for missing data
- [ ] Add caching for frequently accessed clients
- [ ] Update tests

## Priority: P2
## Estimated Effort: 4 hours
```

---

**Next Action:** Clean prediction.py - convert 11 TODOs to ROADMAP issues
