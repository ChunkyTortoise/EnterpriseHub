# Spec 07: Type Safety Improvements (P2)

**Agent**: `feature-enhancement-guide`  
**Estimated scope**: ~30 files modified  
**Priority**: P2 (Medium)  
**Dependencies**: Spec 6 (class structure settled) should be completed first

---

## Context

786 files use `Dict[str, Any]` which provides no type safety. This spec creates TypedDicts and replaces weak typing in high-traffic paths.

---

## 7a. Create TypedDicts for Core Data Structures

### Create
`ghl_real_estate_ai/models/typed_dicts.py`

```python
from typing import TypedDict, Optional, List
from datetime import datetime

class ScoringContext(TypedDict, total=False):
    lead_id: str
    contact_info: dict
    interaction_history: List[dict]
    property_preferences: dict
    score_timestamp: datetime

class WebhookPayload(TypedDict):
    event_type: str
    timestamp: str
    data: dict
    signature: Optional[str]

class DashboardData(TypedDict, total=False):
    metrics: dict
    charts: List[dict]
    alerts: List[dict]
    last_updated: datetime

class CacheEntry(TypedDict):
    key: str
    value: str
    ttl: int
    created_at: datetime

class HandoffContext(TypedDict, total=False):
    lead_id: str
    from_agent: str
    to_agent: str
    confidence: float
    reason: str
    timestamp: datetime
```

---

## 7b. Replace Dict[str, Any] in High-Traffic Paths

### Priority Files

1. `services/enhanced_lead_scorer.py`
2. `services/enhanced_ghl_client.py`
3. `services/jorge/jorge_handoff_service.py`
4. `api/routes/webhook.py`
5. `services/claude_orchestrator.py`

### Example Fix
```python
# Before
def score_lead(context: Dict[str, Any]) -> Dict[str, Any]:
    ...

# After
from ghl_real_estate_ai.models.typed_dicts import ScoringContext, ScoringResult

def score_lead(context: ScoringContext) -> ScoringResult:
    ...
```

---

## 7c. Fix Circular Import Patterns

### Files
- `services/claude_assistant.py:29-32`
- `services/enhanced_lead_scorer.py:34-35`

### Problem
```python
try:
    from .some_module import SomeClass
except ImportError:
    SomeClass = None  # Circular import workaround
```

### Fix
Move shared types to `models/` to break cycles, or use Protocol classes:

```python
from typing import Protocol

class LeadScorerProtocol(Protocol):
    def score(self, data: dict) -> float: ...
```

---

## Verification

```bash
# Count remaining Dict[str, Any] - target < 400
grep -rn "Dict\[str, Any\]" ghl_real_estate_ai/ --include="*.py" | wc -l

# Type check
mypy ghl_real_estate_ai/ --ignore-missing-imports
```

---

## Acceptance Criteria

- [ ] TypedDicts file created with 5+ definitions
- [ ] Dict[str, Any] count reduced from 786 to < 400
- [ ] No circular import workarounds
- [ ] mypy passes with no new errors
