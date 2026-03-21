# Test Strategy for EnterpriseHub

## Current State Assessment

### Test Inventory

| Suite | Location | Files | Test Functions | CI Job |
|-------|----------|-------|----------------|--------|
| `ghl_real_estate_ai/tests/unit/` | Primary unit suite | 10 test files | 181 functions | `test-unit` step 1 |
| `tests/unit/` | Extended unit suite | 28 test files | 704 functions | `test-unit` step 2 (continue-on-error) |
| `ghl_real_estate_ai/tests/integration/` | Integration suite | 6 test files | 90 functions | `test-integration` (broken) |
| `tests/` (other subdirs) | Agents, API, GHL integration, visual | 362 test files | ~1400+ functions | Not in CI |

**Critical gap**: The 181 tests the CI actually enforces (step 1, `--cov-fail-under=50`) are just the `ghl_real_estate_ai/tests/unit/` suite. The 704-function `tests/unit/` suite runs with `continue-on-error: true` and `--cov-fail-under=0`, meaning CI passes even if every test there fails.

### What the 181 CI-Enforced Tests Actually Cover

The 10 test files in `ghl_real_estate_ai/tests/unit/` exercise specific service-layer units:

| File | Subject | Key Behaviors Tested |
|------|---------|---------------------|
| `test_claude_orchestrator.py` | JSON extraction from LLM responses | Markdown blocks, plain JSON, invalid JSON edge cases |
| `test_agent_mesh_coordinator.py` | Agent registration, routing, task dispatch | Capacity, SLA/cost/capability filters, metrics |
| `test_handoff_redis.py` | Cross-bot handoff state persistence | fakeredis in-memory store, circular prevention, rate limits |
| `test_task_queue.py` | Async task queue | fakeredis queue, DLQ, RQ fallback |
| `test_security_framework.py` | JWT, HMAC webhook validation, input sanitization | GHL/VAPI/Apollo signature verification |
| `test_cost_tracker.py` | Token cost calculation | Input/output pricing, cache read pricing |
| `test_digest_service.py` | Email digest builder | HTML generation, SendGrid mock |
| `test_property_matching.py` | Buyer property filtering | Budget, bedroom, zip code filters |
| `test_insurance_config.py` | YAML config loading | jorge_bots.yaml structure |
| `test_claude_timeout.py` | LLM circuit breaker | Consecutive failure tracking, failover logic |

**What these tests do NOT cover**:
- FastAPI route handlers (`api/routes/`)
- Bot conversation flows (`agents/jorge_*_bot.py`, `agents/lead_bot.py`)
- GHL client HTTP interactions (`services/enhanced_ghl_client.py`)
- Database models and repositories
- Response pipeline stages (TCPA, compliance, SB 243 disclosure, SMS truncation)
- Handoff service persistence to PostgreSQL
- Streamlit BI dashboard components
- RAG system (`advanced_rag_system/`)

### conftest.py Hierarchy

```
/conftest.py                              # Integration-focused; asyncpg pool, Redis pool, mock fixtures
/tests/conftest.py                        # pytest_configure hook (registers markers), psutil perf monitor
/ghl_real_estate_ai/tests/conftest.py    # Env var defaults before import, market fixture
/ghl_real_estate_ai/tests/unit/conftest.py  # Monkeypatches TESTING=1, SQLite URL, Redis localhost
```

**Problem**: The root `/conftest.py` applies `autouse=True` fixtures to ALL tests, including `psutil` performance monitoring. If `psutil` is not installed in CI, the entire `tests/` suite fails silently (due to `continue-on-error`). More critically, `psutil` IS in `requirements.txt` but its `monitor_test_performance` fixture adds overhead to every test.

---

## CI Pipeline Issues Found

### Line-by-Line Analysis of ci.yml

**Line 103 — Primary unit test command:**
```yaml
pytest ghl_real_estate_ai/tests/unit/ -m unit --override-ini="addopts=" --cov=ghl_real_estate_ai \
  --cov-report=xml --cov-report=term-missing --cov-fail-under=50 -v
```
Issues:
- `--override-ini="addopts="` strips `--strict-markers` from `pytest.ini`. Tests using unknown markers will silently pass instead of error.
- `--cov-fail-under=50` is the only real gate. `pytest.ini` specifies 80% but is overridden.
- Runs `-m unit` which only collects tests decorated with `@pytest.mark.unit`. Only 43 of the 181 functions have this marker; the remaining 138 lack the `@pytest.mark.unit` decorator but are included because the directory path is passed directly, overriding the marker filter.

**Line 111-112 — Extended unit tests:**
```yaml
pytest tests/unit/ --override-ini="addopts=" --cov=ghl_real_estate_ai --cov-append \
  --cov-report=xml --cov-report=term-missing --cov-fail-under=0 --tb=short -q
continue-on-error: true
```
Issues:
- `--cov-fail-under=0` combined with `continue-on-error: true` means this step is decorative — it can fail completely and CI still passes.
- Coverage from this step appends to the previous report via `--cov-append`, so Codecov sees blended data that may overstate actual coverage.
- 704 test functions not gating CI is the largest structural risk in the pipeline.

**Lines 122-159 — Integration test job:**
```yaml
test-integration:
  name: Integration Tests
  runs-on: ubuntu-latest
  needs: [test-unit]
  steps:
    ...
    - name: Run integration tests
      run: pytest -m integration -v --tb=short
```
Critical problems:
1. **No service containers defined.** The `conftest.py` at root expects `postgresql://postgres:password@localhost:5432/test_ghl_real_estate` and `redis://localhost:6379/1`. Neither service is running. Every fixture that calls `asyncpg.create_pool()` or `redis.ping()` will hit the `except` branch and yield `None`.
2. **Graceful degradation hides failures.** The `database_connection_pool` and `redis_connection_pool` fixtures catch all exceptions and yield `None`, so tests degrade to mocks rather than failing loudly. The integration test job passes (trivially) while testing nothing against real infrastructure.
3. **No `--cov-fail-under` on the integration job.** Even if tests ran against real services, no coverage gate is applied.
4. **`pytest -m integration` from the repo root** collects tests from both `testpaths` (`tests/` and `ghl_real_estate_ai/tests/`). But most integration tests in `ghl_real_estate_ai/tests/integration/` do NOT have `@pytest.mark.integration` at the module level — they only have it on selected classes or functions. The 6-file integration suite has 90 test functions but only 4 use `@pytest.mark.integration` at the class level. The rest are skipped by the `-m integration` filter.

**Lines 161-180 — Type check job:**
```yaml
- name: Run mypy
  run: mypy ghl_real_estate_ai src utils advanced_rag_system
```
Issue: `pyproject.toml` sets `ignore_errors = true` for essentially every application module (`ghl_real_estate_ai.*`, `portal_api.*`, `utils.*`, etc.). mypy CI step provides no real type safety signal.

**Lines 182-206 — Build job:**
```yaml
- name: Verify app can be imported
  run: python -c "import app; print('App imported successfully')"
```
Issue: This only verifies the import chain completes — it does not validate routing, middleware, or startup events. A misconfigured lifespan handler would pass this check.

---

## Recommended CI Configuration

### Immediate Fix: Integration Job with Service Containers

Replace the existing `test-integration` job with:

```yaml
test-integration:
  name: Integration Tests
  runs-on: ubuntu-latest
  needs: [test-unit]

  services:
    postgres:
      image: pgvector/pgvector:pg16
      env:
        POSTGRES_USER: postgres
        POSTGRES_PASSWORD: password
        POSTGRES_DB: test_ghl_real_estate
      ports:
        - 5432:5432
      options: >-
        --health-cmd "pg_isready -U postgres"
        --health-interval 10s
        --health-timeout 5s
        --health-retries 5

    redis:
      image: redis:7-alpine
      ports:
        - 6379:6379
      options: >-
        --health-cmd "redis-cli ping"
        --health-interval 10s
        --health-timeout 5s
        --health-retries 5

  steps:
    - uses: actions/checkout@v4

    - name: Set up Python 3.12
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-3.12-${{ hashFiles('**/requirements.txt', '**/requirements-dev.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-3.12-

    - name: Install Python dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run Alembic migrations
      env:
        DATABASE_URL: postgresql://postgres:password@localhost:5432/test_ghl_real_estate
      run: |
        alembic upgrade head

    - name: Run integration tests
      env:
        ANTHROPIC_API_KEY: sk-test-key-for-ci-only
        GHL_API_KEY: test-ghl-key-for-ci-only
        GHL_LOCATION_ID: test-location-id-for-ci-only
        TEST_DATABASE_URL: postgresql://postgres:password@localhost:5432/test_ghl_real_estate
        TEST_REDIS_URL: redis://localhost:6379/1
        DATABASE_URL: postgresql://postgres:password@localhost:5432/test_ghl_real_estate
        REDIS_URL: redis://localhost:6379/1
      run: |
        pytest ghl_real_estate_ai/tests/integration/ \
          --override-ini="addopts=" \
          --cov=ghl_real_estate_ai \
          --cov-report=xml \
          --cov-report=term-missing \
          --cov-fail-under=30 \
          --tb=short \
          -v

    - name: Upload integration coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: integration
        fail_ci_if_error: false
```

### Redis-Only Integration: fakeredis Upgrade Path

For tests that only need Redis (no PostgreSQL), use `fakeredis` already in `requirements-dev.txt`. The pattern in `test_handoff_redis.py` is correct:

```python
import fakeredis
server = fakeredis.FakeServer()
fake_redis = fakeredis.FakeRedis(server=server)
```

For async Redis tests, use `fakeredis.aioredis.FakeRedis()`. This eliminates the service container dependency for the unit-test job while maintaining realistic Redis behavior (sorted sets, pipelines, TTL).

### Unit Test Job Fix

Replace the two-step unit test run with a single enforced command:

```yaml
- name: Run unit tests
  env:
    ANTHROPIC_API_KEY: sk-test-key-for-ci-only
    GHL_API_KEY: test-ghl-key-for-ci-only
    GHL_LOCATION_ID: test-location-id-for-ci-only
  run: |
    pytest ghl_real_estate_ai/tests/unit/ tests/unit/ \
      --override-ini="addopts=" \
      --strict-markers \
      --cov=ghl_real_estate_ai \
      --cov-report=xml \
      --cov-report=term-missing \
      --cov-fail-under=55 \
      --tb=short \
      -q
```

Key changes from current state:
- Combines both unit directories into one run (no `cov-append` complexity).
- Adds `--strict-markers` back explicitly (was stripped by `--override-ini`).
- Raises threshold to 55% immediately (achievable given both suites together).
- Removes `continue-on-error`.

---

## pytest Marker Strategy

### Current State

Markers are registered in `pytest.ini` (`--strict-markers` is in `addopts`) but:
- CI strips `--strict-markers` via `--override-ini="addopts="`.
- The `tests/conftest.py` re-registers markers via `pytest_configure`, but only for a subset of markers.
- `ghl_real_estate_ai/tests/unit/` tests: 43 have `@pytest.mark.unit`, 138 do not.
- `ghl_real_estate_ai/tests/integration/` tests: 4 classes have `@pytest.mark.integration`, 86 functions do not.

### Recommended Marker Convention

**Rule 1: Module-level `pytestmark` as the default**

Every test file should declare its category at the top:

```python
# ghl_real_estate_ai/tests/unit/test_*.py
import pytest
pytestmark = pytest.mark.unit

# ghl_real_estate_ai/tests/integration/test_*.py
import pytest
pytestmark = pytest.mark.integration
```

This is already done correctly in `tests/unit/__init__.py` (module-level via `__init__.py`) and in some `tests/unit/test_*.py` files. Apply the same pattern to all files.

**Rule 2: Layer markers by file location, not decorator repetition**

The auto-marker logic already exists in `tests/conftest.py`'s `pytest_collection_modifyitems`. However it checks `item.fspath.dirname` which works inconsistently across Python path configurations. Explicit `pytestmark` at module level is more reliable.

**Rule 3: Use compound markers for complex tests**

```python
@pytest.mark.integration
@pytest.mark.database
async def test_handoff_persists_to_postgres(db_session):
    ...

@pytest.mark.integration
@pytest.mark.redis
async def test_handoff_cache_round_trip(redis_client):
    ...
```

This enables fine-grained filtering: `pytest -m "integration and not database"` for Redis-only integration, `pytest -m "unit and not slow"` for fast feedback.

**Rule 4: Enforce markers in CI (do not strip `--strict-markers`)**

Remove `--override-ini="addopts="` from the CI commands. Instead, selectively override only what needs changing:

```bash
# Instead of stripping all addopts:
pytest ... --override-ini="addopts=" --strict-markers ...

# Pass only the options you want to change:
pytest ... --no-header -q  # Only override display options
```

Or accept the `pytest.ini` defaults and just add the CI-specific flags:

```bash
pytest ghl_real_estate_ai/tests/unit/ -m unit
# pytest.ini addopts already includes --cov, --strict-markers, etc.
```

### Marker Cleanup Effort (per suite)

| Suite | Files needing `pytestmark` | Estimated effort |
|-------|---------------------------|-----------------|
| `ghl_real_estate_ai/tests/unit/` | 10 files (add `pytestmark = pytest.mark.unit`) | 30 minutes |
| `ghl_real_estate_ai/tests/integration/` | 6 files (add `pytestmark = pytest.mark.integration`) | 20 minutes |
| `tests/unit/` | 28 files (most already have it) | 30 minutes to audit |

---

## Coverage Improvement Plan

### Current Coverage Reality

The `pytest.ini` declares `--cov-fail-under=80` but CI overrides to `--cov-fail-under=50` for the enforced suite and `0` for the extended suite. `pyproject.toml` sets `fail_under = 60` in `[tool.coverage.report]`. There are three conflicting thresholds.

The 181 enforced tests cover roughly 10 service-layer files in depth. The `--cov=ghl_real_estate_ai` flag measures coverage across the entire `ghl_real_estate_ai/` package, which includes:

- `ghl_real_estate_ai/agents/` — 0% coverage from unit tests (only called in integration tests with heavy mocking)
- `ghl_real_estate_ai/api/routes/` — 0% from unit tests
- `ghl_real_estate_ai/services/jorge/response_pipeline/` — 0% from unit tests
- `ghl_real_estate_ai/services/enhanced_ghl_client.py` — covered in `tests/unit/test_enhanced_ghl_client.py` (extended suite, not enforced)

### 80%+ Coverage Roadmap

**Phase 1 — Fix the gate (Week 1)**

1. Stop overriding `--strict-markers` in CI. This will expose the 138 unmarked unit tests and force them to be properly categorized.
2. Set a single authoritative threshold: remove `fail_under` from `pyproject.toml`; keep `--cov-fail-under` only in `pytest.ini` and CI.
3. Run the combined `ghl_real_estate_ai/tests/unit/ + tests/unit/` suite and measure actual coverage with `--cov-report=term-missing`. This is the baseline.

**Phase 2 — High-ROI unit tests (Weeks 1-2)**

Target the response pipeline (5 stages, pure functions, no I/O):

```
ghl_real_estate_ai/services/jorge/response_pipeline/
├── pipeline.py           # PipelineContext, ResponsePipeline.process()
├── processors/
│   ├── language_mirror.py    # LanguageMirrorProcessor
│   ├── tcpa.py              # TCPAOptOutProcessor
│   ├── compliance.py        # ComplianceCheckProcessor
│   ├── disclosure.py        # AIDisclosureProcessor
│   └── sms_truncation.py    # SMSTruncationProcessor
```

These processors take a string in and return a string out (or short-circuit). They are the highest-value untested code: TCPA opt-out detection and SMS truncation are compliance-critical, and each processor is testable in pure isolation with `unittest.mock`. Estimated: 40+ tests, ~200 lines of coverage.

**Phase 3 — API route tests with `TestClient` (Weeks 2-3)**

Use FastAPI's `TestClient` to cover the route layer without a live server:

```python
from fastapi.testclient import TestClient
from ghl_real_estate_ai.app import app

client = TestClient(app)

def test_webhook_route_requires_signature():
    response = client.post("/webhook/ghl", json={})
    assert response.status_code == 401
```

Target the 5 highest-traffic routes: `/webhook/ghl`, `/api/leads`, `/api/conversations`, `/health`, `/api/handoff`. This covers `api/routes/` which currently has 0% coverage and is called by the production bot.

**Phase 4 — Bot conversation flow tests (Weeks 3-4)**

The integration tests in `ghl_real_estate_ai/tests/integration/` already have good fixtures (`_mock_seller_deps`, etc.) that mock all external dependencies. These tests call the real LangGraph workflow nodes. The problem is they are not enforced in CI.

Steps:
1. Add `pytestmark = pytest.mark.integration` to all 6 integration test files.
2. Add service containers to the CI integration job (see Recommended CI Configuration above).
3. Add `--cov-fail-under=30` to the integration job as an initial gate.

**Phase 5 — Database repository tests with testcontainers (Week 4+)**

For full persistence layer coverage, add `testcontainers` to `requirements-dev.txt`:

```
testcontainers[postgres]>=3.7.0
```

Then create fixtures in `conftest.py`:

```python
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def pg_container():
    with PostgresContainer("pgvector/pgvector:pg16") as postgres:
        # Run alembic migrations
        import subprocess
        subprocess.run(
            ["alembic", "upgrade", "head"],
            env={**os.environ, "DATABASE_URL": postgres.get_connection_url()},
            check=True
        )
        yield postgres

@pytest.fixture
async def db_session(pg_container):
    pool = await asyncpg.create_pool(pg_container.get_connection_url())
    async with pool.acquire() as conn:
        async with conn.transaction():
            yield conn
            raise Exception("rollback")  # Force rollback for test isolation
    await pool.close()
```

**Testcontainers vs Service Containers: When to use which**

| Scenario | Recommendation |
|----------|---------------|
| CI integration job | GitHub Actions service containers (simpler, no extra dep) |
| Local development with `pytest` | `testcontainers` (spins up automatically, no manual Docker needed) |
| Tests that need schema control (DDL) | `testcontainers` with Alembic in fixture |
| Redis unit tests | `fakeredis` (fastest, no Docker) |

### Coverage Target Timeline

| Milestone | When | Target | Method |
|-----------|------|--------|--------|
| Baseline measured | Week 1 | ~35-45% (estimate) | Run combined unit suites |
| Unit threshold raised | Week 1 | 55% gate | Fix CI combined run |
| Response pipeline tests added | Week 2 | 60% | ~40 new unit tests |
| API route tests added | Week 3 | 68% | TestClient, ~30 tests |
| Integration job gating | Week 3 | 30% integration gate | Service containers live |
| Bot flow tests enforced | Week 4 | 75% overall | Integration suite in CI |
| Repository tests with DB | Week 5+ | 80%+ | testcontainers or service containers |

---

## Effort Estimate

| Task | Effort | Risk | Value |
|------|--------|------|-------|
| Add `pytestmark` to all integration test files (6 files) | 1 hour | Low | High — makes `-m integration` actually work |
| Fix integration job: add service containers | 2 hours | Low | High — integration tests currently test nothing |
| Fix unit job: remove `continue-on-error`, combine suites | 1 hour | Low-Medium | High — enforces 704 currently-ignored tests |
| Write response pipeline unit tests (~40 tests) | 4 hours | Low | High — covers compliance-critical code paths |
| Write FastAPI `TestClient` route tests (~30 tests) | 4 hours | Low | High — zero coverage today on route handlers |
| Add `pytestmark` to all unit test files (10 files) | 30 min | Low | Medium — cleaner CI filtering |
| Reconcile three conflicting coverage thresholds | 30 min | Low | Medium — eliminates confusion |
| Resolve `--strict-markers` being stripped in CI | 30 min | Low | Medium — restores `pytest.ini` intent |
| Add testcontainers for local dev DB fixtures | 3 hours | Medium | Medium-High — better local dev experience |
| mypy: tighten `ignore_errors` overrides incrementally | ongoing | Medium | Low-Medium — currently zero signal |

**Total to reach 80% coverage: ~15-20 hours of focused work over 4-5 weeks.**

The highest-leverage single change is adding service containers to the integration job (2 hours) combined with adding `pytestmark = pytest.mark.integration` to the 6 integration files (1 hour). This transforms the integration job from "trivially passing by catching all connection errors" into "actually exercising bot conversation workflows."

The second-highest-leverage change is removing `continue-on-error: true` from the extended unit test step. This immediately surfaces failures in the 704-function suite that are currently hidden.
