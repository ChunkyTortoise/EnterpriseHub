# Spec 08: Code Duplication & Dead Code Cleanup (P3)

**Agent**: `feature-enhancement-guide`  
**Estimated scope**: ~20 files modified  
**Priority**: P3 (Backlog)  
**Dependencies**: Specs 4-7 should be completed first

---

## Context

Codebase has duplicate patterns, dead code, and 125 `time.sleep()` calls in tests blocking async operations.

---

## 8a. Extract Shared Scoring Result Builder

### File
`services/enhanced_lead_scorer.py`

### Problem
3 methods with ~50 lines duplicated each for building results.

### Fix
```python
def _create_base_result(
    self,
    lead_id: str,
    score: float,
    factors: List[Dict],
) -> ScoringResult:
    return {
        "lead_id": lead_id,
        "score": score,
        "factors": factors,
        "timestamp": datetime.utcnow().isoformat(),
        "version": self.VERSION,
    }
```

---

## 8b. Extract Shared Error Handling

### File
`services/claude_assistant.py`

### Problem
3 duplicated error handling blocks.

### Fix
Create decorator or context manager:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def handle_ai_errors(operation: str, fallback=None):
    try:
        yield
    except AITimeoutError as e:
        logger.warning(f"{operation} timeout: {e}")
        if fallback:
            return fallback
    except AIRateLimitError as e:
        logger.warning(f"{operation} rate limited: {e}")
        await asyncio.sleep(1)
        raise
```

---

## 8c. Remove Dead Code

### Audit Commands
```bash
vulture ghl_real_estate_ai/ --min-confidence 80
ruff check ghl_real_estate_ai/ --select F401  # unused imports
```

### Remove
- Unused imports flagged by ruff
- Commented-out code blocks
- `if __name__ == "__main__"` test blocks in service files

---

## 8d. Remove time.sleep() from Tests

### Problem
125 `time.sleep()` calls blocking async tests.

### Fix
```python
# Before
time.sleep(1)

# After
await asyncio.sleep(0.1)  # or use pytest-timeout
```

For retry patterns, use tenacity:
```python
from tenacity import retry, wait_exponential

@retry(wait=wait_exponential(min=0.1, max=2))
async def flaky_operation():
    ...
```

---

## Verification

```bash
ruff check ghl_real_estate_ai/ --select F401  # should be 0
grep -rn "time.sleep" tests/ --include="*.py" | wc -l  # target < 10
pytest tests/ -x
```

---

## Acceptance Criteria

- [ ] Shared result builder extracted
- [ ] Error handling decorator created
- [ ] Zero unused imports
- [ ] time.sleep() in tests < 10
- [ ] All tests pass
