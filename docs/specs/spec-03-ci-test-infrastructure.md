# Spec 03: CI/CD & Test Infrastructure (P0)

**Agent**: `quality-gate` or `test-engineering`  
**Estimated scope**: ~5 files modified, test reorganization  
**Priority**: P0 (Critical)  
**Dependencies**: None

---

## Context

CI pipeline has critical issues: tests run against non-existent directories, integration tests silently pass on failure, mypy coverage is minimal, and there's no coverage enforcement.

---

## 3a. Fix Broken CI Unit Test Path

### Location
- **File**: `.github/workflows/ci.yml`

### Problem
CI runs `pytest tests/unit/` but that directory doesn't exist, causing tests to silently skip.

### Fix Options

**Option A (Recommended)**: Update CI to use marker-based test selection:

```yaml
jobs:
  test-unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run unit tests
        run: pytest tests/ -m unit -v --timeout=30
```

**Option B**: Create `tests/unit/` and move unit tests there (more disruptive).

### Acceptance Criteria
- CI unit test job correctly runs unit tests
- `pytest tests/ -m unit` runs successfully locally
- No silent test skips in CI logs

---

## 3b. Fix Integration Test False Negatives

### Location
- **File**: `.github/workflows/ci.yml`

### Problem
Integration tests use `|| true` suffix, causing them to always pass even on failure.

### Current (Bad)
```yaml
- name: Run integration tests
  run: pytest tests/ -m integration || true
```

### Fix
```yaml
- name: Run integration tests
  run: pytest tests/ -m integration -v --timeout=30
  continue-on-error: false  # Or true if you want non-blocking initially
```

If you need non-blocking integration tests temporarily:
```yaml
- name: Run integration tests
  run: pytest tests/ -m integration -v --timeout=30
  continue-on-error: true  # Makes step non-blocking at job level

- name: Check integration test results
  if: steps.integration-tests.outcome == 'failure'
  run: echo "::warning::Integration tests failed - see logs"
```

### Acceptance Criteria
- No `|| true` on test commands
- Integration test failures visible in CI
- Add `--timeout=30` to prevent hangs

---

## 3c. Expand mypy Coverage

### Location
- **File**: `.github/workflows/ci.yml`

### Problem
mypy only checks `app.py` and `utils/`, missing the main codebase.

### Current (Incomplete)
```yaml
- name: Type check
  run: mypy app.py utils/
```

### Fix
```yaml
- name: Type check
  run: |
    mypy ghl_real_estate_ai/ \
      --ignore-missing-imports \
      --no-error-summary \
      --show-error-codes \
      --warn-unused-ignores
```

For gradual adoption, start with critical paths:
```yaml
- name: Type check (core)
  run: |
    mypy ghl_real_estate_ai/services/ \
         ghl_real_estate_ai/api/ \
         --ignore-missing-imports
```

### Acceptance Criteria
- mypy checks `ghl_real_estate_ai/` directory
- No new type errors introduced
- Type errors visible in CI output

---

## 3d. Add Coverage Enforcement

### Location
- **Files**: `.github/workflows/ci.yml`, `pyproject.toml`

### Problem
No minimum coverage requirement; coverage can drop to 0% without CI failure.

### Fix - CI Configuration
```yaml
- name: Run tests with coverage
  run: |
    pytest tests/ \
      --cov=ghl_real_estate_ai \
      --cov-report=xml \
      --cov-report=term-missing \
      --cov-fail-under=60

- name: Upload coverage
  uses: codecov/codecov-action@v4
  with:
    files: ./coverage.xml
    fail_ci_if_error: true
```

### Fix - pyproject.toml
```toml
[tool.pytest.ini_options]
addopts = "--cov=ghl_real_estate_ai --cov-fail-under=60"

[tool.coverage.run]
branch = true
source = ["ghl_real_estate_ai"]
omit = ["*/tests/*", "*/__pycache__/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
fail_under = 60
```

### Coverage Roadmap
- Phase 1: Set `--cov-fail-under=60` (current baseline)
- Phase 2: Increase to `70` after Spec 5 (test coverage)
- Phase 3: Target `80` as final goal

### Acceptance Criteria
- CI fails if coverage drops below threshold
- Coverage reports uploaded to Codecov
- Clear visibility into uncovered code

---

## Verification Commands

```bash
# Test CI configuration locally (requires act)
act -j test-unit

# Or run directly
pytest tests/ -m unit -v
pytest tests/ -m integration -v --timeout=30

# Check mypy
mypy ghl_real_estate_ai/ --ignore-missing-imports

# Check coverage
pytest tests/ --cov=ghl_real_estate_ai --cov-report=term-missing
```

---

## Files to Modify

| File | Change Type |
|------|-------------|
| `.github/workflows/ci.yml` | Fix test paths, remove `\|\| true`, add mypy, coverage |
| `pyproject.toml` | Add coverage configuration |
| `pytest.ini` or `pyproject.toml` | Register markers (unit, integration, slow) |

---

## Marker Registration

Add to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests (fast, no external dependencies)",
    "integration: Integration tests (may need services)",
    "slow: Slow tests (heavy fixtures or network calls)",
    "security: Security-related tests",
]
```
