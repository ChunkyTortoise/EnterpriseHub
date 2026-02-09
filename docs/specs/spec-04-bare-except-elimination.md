# Spec 04: Bare Except Elimination (P1)

**Agent**: `feature-enhancement-guide`  
**Estimated scope**: 81 files, ~200+ except clause fixes  
**Priority**: P1 (High)  
**Dependencies**: None

---

## Context

Audit found 81 files with bare `except:` clauses that silently swallow errors, making debugging and monitoring impossible.

---

## Strategy

### Step 1: Generate Full List
```bash
grep -rn "except:" ghl_real_estate_ai/ --include="*.py" > bare_excepts.txt
```

### Step 2: Classify Each Exception

For each bare `except:`, determine the appropriate exception type based on context:

| Context | Exception Types |
|---------|-----------------|
| Network/HTTP calls | `except (httpx.HTTPError, ConnectionError, TimeoutError)` |
| JSON parsing | `except (json.JSONDecodeError, ValueError)` |
| Redis/Cache operations | `except (redis.RedisError, ConnectionError)` |
| File I/O | `except (IOError, FileNotFoundError, PermissionError)` |
| Database operations | `except (DatabaseError, IntegrityError)` |
| Generic fallback (last resort) | `except Exception as e:` with logging |

### Step 3: Apply Fixes

**Never use:**
- `except:` (bare)
- `except Exception: pass` (silent failure)

**Always include:**
- Specific exception types
- Logging at minimum `logger.warning()` level
- Context in log message

---

## Priority Files (Most Instances)

### 1. `ghl_real_estate_ai/services/semantic_response_caching.py` (7 instances)

```python
# Before
try:
    result = cache.get(key)
except:
    result = None

# After
import logging
logger = logging.getLogger(__name__)

try:
    result = cache.get(key)
except (redis.RedisError, ConnectionError) as e:
    logger.warning(f"Cache lookup failed for key {key}: {e}")
    result = None
```

### 2. `ghl_real_estate_ai/services/enhanced_lead_scorer.py` (6 instances)

```python
# Before
try:
    score = calculate_score(data)
except:
    score = 0.5

# After
try:
    score = calculate_score(data)
except (ValueError, TypeError, KeyError) as e:
    logger.warning(f"Score calculation failed, using default: {e}")
    score = 0.5
except Exception as e:
    logger.error(f"Unexpected error in score calculation: {e}", exc_info=True)
    score = 0.5
```

### 3. `ghl_real_estate_ai/services/enhanced_ghl_client.py` (5 instances)

```python
# Before
try:
    response = await client.post(url, data)
except:
    return None

# After
try:
    response = await client.post(url, data)
except httpx.TimeoutException as e:
    logger.warning(f"GHL API timeout for {url}: {e}")
    return None
except httpx.HTTPStatusError as e:
    logger.warning(f"GHL API error for {url}: {e.response.status_code}")
    return None
except Exception as e:
    logger.error(f"Unexpected GHL API error: {e}", exc_info=True)
    return None
```

### 4. `ghl_real_estate_ai/services/behavioral_weighting_engine.py` (4 instances)

```python
# Before
try:
    weight = compute_weight(behavior)
except:
    weight = 1.0

# After
try:
    weight = compute_weight(behavior)
except (ValueError, ZeroDivisionError) as e:
    logger.warning(f"Weight computation failed for {behavior}: {e}")
    weight = 1.0
```

---

## Transformation Rules

### Rule 1: Identify Exception Source
```python
# Look at the operation inside try block
try:
    json.loads(data)        # → json.JSONDecodeError
    requests.get(url)       # → requests.RequestException, TimeoutError
    open(filepath)          # → IOError, FileNotFoundError
    int(value)              # → ValueError
    dict_obj[key]           # → KeyError
```

### Rule 2: Add Logging Context
```python
# Include relevant context in log message
logger.warning(
    f"Operation failed for {identifier}: {error}",
    extra={"operation": "cache_lookup", "key": key}
)
```

### Rule 3: Preserve Error Recovery
```python
# Keep the recovery logic, just make it explicit
except SpecificError as e:
    logger.warning(f"Using fallback: {e}")
    return fallback_value
```

---

## Complete File List

Run this to get the current list:
```bash
grep -rln "except:" ghl_real_estate_ai/ --include="*.py" | sort
```

Expected high-priority files:
- `services/semantic_response_caching.py`
- `services/enhanced_lead_scorer.py`
- `services/enhanced_ghl_client.py`
- `services/behavioral_weighting_engine.py`
- `services/claude_orchestrator.py`
- `services/jorge/jorge_handoff_service.py`
- `api/routes/webhook.py`
- `api/routes/leads.py`
- `core/conversation_manager.py`

---

## Verification Commands

```bash
# Count remaining bare excepts (should be 0)
grep -rn "except:" ghl_real_estate_ai/ --include="*.py" | grep -v "except [A-Z]" | wc -l

# Verify no silent pass patterns
grep -rn "except.*:.*pass" ghl_real_estate_ai/ --include="*.py" | wc -l

# Run full test suite to verify no regressions
pytest tests/ -x --timeout=60

# Check that logging is present
grep -rn "except.*as e:" ghl_real_estate_ai/ --include="*.py" | head -20
```

---

## Acceptance Criteria

- [ ] Zero bare `except:` clauses in production code
- [ ] All caught exceptions have specific types
- [ ] All exception handlers include logging
- [ ] All tests pass after changes
- [ ] No new `except Exception: pass` patterns

---

## Estimated Effort

| Priority | Files | Instances | Time Est. |
|----------|-------|-----------|-----------|
| High | 10 | ~35 | 2 hours |
| Medium | 30 | ~80 | 3 hours |
| Low | 41 | ~85 | 3 hours |
| **Total** | **81** | **~200** | **8 hours** |
