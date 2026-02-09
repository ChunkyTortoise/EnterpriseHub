# Spec 06: God Class Decomposition (P2)

**Agent**: `architecture-sentinel`  
**Estimated scope**: ~6 files refactored, ~8 new files created  
**Priority**: P2 (Medium)  
**Dependencies**: Spec 4 (clean error handling) should be completed first

---

## Context

Audit found "god classes" with 1,000+ lines violating Single Responsibility Principle.

---

## 6a. Split claude_assistant.py (1,163 lines)

### Source
`ghl_real_estate_ai/services/claude_assistant.py`

### Extract Into:
1. `services/claude_market_context.py` — Market context (lines 50-94)
2. `services/claude_ui_renderer.py` — UI rendering (lines 96-119)
3. `services/claude_report_generator.py` — Reports (lines 182-294)
4. Keep `claude_assistant.py` as thin orchestrator

### Constraint
All existing public API methods must remain importable from original path.

---

## 6b. Split streamlit_demo/app.py (3,000+ lines)

### Target Structure
```
streamlit_demo/
├── app.py              # Main entry (< 200 lines)
├── pages/
│   ├── 01_dashboard.py
│   ├── 02_leads.py
│   └── 03_analytics.py
├── components/
│   ├── sidebar.py
│   └── charts.py
└── data_loaders.py
```

---

## 6c. Fix Tight Coupling via DI

### File
`ghl_real_estate_ai/services/enhanced_lead_scorer.py`

### Problem
Direct instantiation of LeadScorer(), PredictiveLeadScorer()

### Fix
```python
def __init__(self, jorge_scorer=None, ml_scorer=None):
    self.jorge_scorer = jorge_scorer or LeadScorer()
    self.ml_scorer = ml_scorer or PredictiveLeadScorer()
```

---

## Verification

```bash
wc -l ghl_real_estate_ai/services/claude_assistant.py  # < 300
wc -l ghl_real_estate_ai/streamlit_demo/app.py  # < 500
pytest tests/ -x
```

---

## Acceptance Criteria

- [ ] claude_assistant.py < 300 lines
- [ ] streamlit_demo/app.py < 500 lines
- [ ] All existing imports still work
- [ ] All tests pass
