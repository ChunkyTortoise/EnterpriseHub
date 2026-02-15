# Exception Handling Audit Report
**Date**: 2026-02-15  
**Auditor**: test-engineering agent  
**Scope**: Jorge Bot exception handling patterns

## Executive Summary

Audited 39 `except Exception` blocks across 3 bot files:
- **3 Critical** (no logging) - Health check code, non-blocking
- **23 Warnings** (too broad) - Should use specific exception types
- **13 OK** (background tasks, external services)

**Recommendation**: Refactor 23 warning cases to use specific exceptions. Add logging to 3 critical cases.

---

## Audit Criteria

### ✅ Appropriate Use of `except Exception`
- Background tasks / fire-and-forget operations
- External service calls (GHL, Retell, etc.) with logging
- Fallback scenarios where any error should trigger default behavior
- **Must have**: Logging at ERROR or WARNING level

### ⚠️ Too Broad (Needs Refactoring)
- Core business logic (scoring, intent analysis, state management)
- Input validation
- Data transformation
- **Should use**: Specific exception types (ValueError, KeyError, AttributeError, etc.)

### 🔴 Critical Issues
- No logging (silent failures)
- Swallowing errors in critical paths
- Missing error propagation

---

## Detailed Findings

### Lead Bot (`lead_bot.py`) - 13 blocks

| Line | Context | Severity | Recommendation |
|------|---------|----------|----------------|
| 74 | Background task wrapper | ✅ OK | Already has logging |
| 436 | GHL contact preferences fetch | ✅ OK | External service, logged |
| 815 | Voice call data check | ⚠️ WARNING | Use `KeyError, AttributeError` |
| 1057 | Intelligence gathering | ⚠️ WARNING | Use `TimeoutError, ConnectionError` |
| 1189 | Track 3.1 market intelligence | ⚠️ WARNING | Use specific ML exceptions |
| 2021 | SMS send via GHL | ✅ OK | External service, logged |
| 2046 | Retell call background | ✅ OK | Background task, logged |
| 2103 | Email send via GHL | ✅ OK | External service, logged |
| 2168 | CMA email attachment | ✅ OK | PDF/email failure, logged |
| 2225 | Day 30 SMS send | ✅ OK | External service, logged |
| 2824 | Metrics→alerting feed | ⚠️ WARNING | Use specific collector exceptions |
| 2848 | process_lead_conversation error | ⚠️ WARNING | Too broad for main entry point |
| 2854 | Error metrics recording | ⚠️ WARNING | Nested exception, too broad |

**Summary**:
- Critical: 0
- Warning: 6 (refactor to specific exceptions)
- OK: 7 (external services, background tasks)

---

### Buyer Bot (`jorge_buyer_bot.py`) - 10 blocks

| Line | Context | Severity | Recommendation |
|------|---------|----------|----------------|
| 356 | Buyer intent analysis | ⚠️ WARNING | Use `ValueError, AttributeError` |
| 368 | Financial readiness calculation | ⚠️ WARNING | Use `KeyError, ValueError` |
| 402 | Property preference extraction | ⚠️ WARNING | Use `KeyError, ValueError` |
| 639 | Property matching | ⚠️ WARNING | Use `ValueError, TimeoutError` |
| 717 | Urgency score calculation | ⚠️ WARNING | Use `AttributeError, ValueError` |
| 722 | Budget clarity scoring | ⚠️ WARNING | Use `KeyError, ValueError` |
| 728 | Decision authority scoring | ⚠️ WARNING | Use `KeyError, ValueError` |
| 808 | Buyer temperature classification | ⚠️ WARNING | Use `ValueError` |
| 911 | GHL contact fetch | ✅ OK | External service call |
| 929 | process_buyer_conversation error | ⚠️ WARNING | Too broad for main entry point |

**Summary**:
- Critical: 0
- Warning: 9 (core business logic needs specific exceptions)
- OK: 1 (external service)

---

### Seller Bot (`jorge_seller_bot.py`) - 16 blocks

| Line | Context | Severity | Recommendation |
|------|---------|----------|----------------|
| 701 | FRS score calculation | ⚠️ WARNING | Use `KeyError, AttributeError, ValueError` |
| 767 | PCS score calculation | ⚠️ WARNING | Use `KeyError, AttributeError, ValueError` |
| 1214 | CMA generation | ⚠️ WARNING | Use `FileNotFoundError, ValueError` |
| 1249 | Calendar booking | ⚠️ WARNING | Use `TimeoutError, ValueError` |
| 1388 | Motivation score calculation | ⚠️ WARNING | Use `KeyError, ValueError` |
| 1398 | Timeline urgency scoring | ⚠️ WARNING | Use `KeyError, ValueError` |
| 1446 | Property condition scoring | ⚠️ WARNING | Use `KeyError, ValueError` |
| 1452 | Equity position scoring | ⚠️ WARNING | Use `KeyError, ValueError` |
| 1772 | Progressive skills health check | 🔴 CRITICAL | **Add logging** |
| 1780 | Agent mesh health check | 🔴 CRITICAL | **Add logging** |
| 1791 | MCP integration health check | 🔴 CRITICAL | **Add logging** |
| (others) | GHL/external services | ✅ OK | External services with logging |

**Summary**:
- Critical: 3 (health checks without logging)
- Warning: 8 (scoring logic needs specific exceptions)
- OK: 5 (external services)

---

## Recommended Refactoring Patterns

### Pattern 1: Scoring Logic (FRS/PCS/Intent)
**Before**:
```python
try:
    score = calculate_score(data)
except Exception as e:
    logger.error(f"Scoring failed: {e}")
    score = 0.0
```

**After**:
```python
try:
    score = calculate_score(data)
except (KeyError, AttributeError) as e:
    logger.warning(f"Missing expected field for scoring: {e}")
    score = 0.0
except ValueError as e:
    logger.error(f"Invalid value in scoring calculation: {e}")
    score = 0.0
```

### Pattern 2: External Service Calls (Keep Broad)
**Current** (OK to keep):
```python
try:
    await self.ghl_client.send_message(...)
except Exception as e:
    logger.error(f"GHL message send failed: {e}")
    # Fallback or skip
```

### Pattern 3: Health Checks (Add Logging)
**Before**:
```python
try:
    health_status["feature"] = "healthy"
except Exception as e:
    health_status["feature"] = f"error: {e}"
```

**After**:
```python
try:
    health_status["feature"] = "healthy"
except Exception as e:
    logger.warning(f"Health check failed for feature: {e}", exc_info=True)
    health_status["feature"] = f"error: {e}"
```

---

## Implementation Priority

### Phase 1: Critical Fixes (30 min)
- [ ] Add logging to Seller Bot lines 1772, 1780, 1791

### Phase 2: High-Value Refactoring (2-3 hours)
- [ ] Refactor main entry point error handlers (lead_bot.py:2848, buyer_bot.py:929, seller_bot.py TBD)
- [ ] Refactor FRS/PCS scoring logic (8 cases in seller_bot.py)
- [ ] Refactor buyer qualification logic (9 cases in buyer_bot.py)

### Phase 3: Comprehensive Cleanup (2-3 hours)
- [ ] Refactor remaining 6 warning cases in lead_bot.py
- [ ] Document exception handling patterns in CLAUDE.md
- [ ] Add exception handling tests to test suite

---

## Metrics

**Before Audit**:
- Total `except Exception` blocks: 39
- No logging: 3 (7.7%)
- Too broad for context: 23 (59.0%)
- Appropriate use: 13 (33.3%)

**Target After Refactoring**:
- Total `except Exception` blocks: ~16 (external services only)
- Specific exception handling: 23+ cases
- Test coverage for exception paths: 100%

---

## Testing Recommendations

For each refactored exception handler, add tests:

```python
def test_scoring_handles_missing_field():
    """Test graceful handling of missing data fields."""
    incomplete_data = {"field1": "value"}  # Missing field2
    score = calculate_score(incomplete_data)
    assert score == 0.0  # Fallback value

def test_scoring_handles_invalid_type():
    """Test handling of invalid data types."""
    invalid_data = {"field": "not_a_number"}
    with pytest.raises(ValueError, match="Invalid value"):
        calculate_score(invalid_data, strict=True)
```

---

## Conclusion

The audit reveals **no catastrophic issues** (no silent failures in critical paths), but **significant opportunity for improvement** through specific exception handling.

**Key Takeaways**:
1. External service calls correctly use broad exception handling with logging ✅
2. Business logic (scoring, intent) should use specific exceptions for better debugging ⚠️
3. Health checks need logging added 🔴

**Estimated Effort**: 5-6 hours for full refactoring + testing.

---

**Audited by**: test-engineering agent  
**Review Status**: Ready for team-lead approval  
**Next Action**: Await approval to proceed with Phase 1 (critical fixes)
