# EnterpriseHub Test Strategy Context (for Research Tools)

## Current State
- **Total test functions**: 8,600+ across the entire codebase
- **Tests running in CI**: ~181 (unit tests without external dependencies)
- **Tests requiring services**: ~8,419 need PostgreSQL and/or Redis
- **CI service containers**: NONE (no `services:` block in any CI job)

## Test Directory Structure
```
tests/unit/              # ~100 tests, CI-compatible
ghl_real_estate_ai/tests/unit/  # ~81 tests, CI-compatible
ghl_real_estate_ai/tests/integration/  # 1000s of tests, need PostgreSQL
advanced_rag_system/tests/  # 1,012+ RAG tests, need vector store
```

## CI Configuration Problem
```yaml
# ci.yml - Integration tests job (BROKEN)
- name: Run integration tests
  run: pytest -m integration -v --tb=short
  # No service containers! Fails with connection refused
```

Compare with what it SHOULD be:
```yaml
services:
  postgres:
    image: pgvector/pgvector:pg15
    env:
      POSTGRES_PASSWORD: test
    options: >-
      --health-cmd pg_isready
  redis:
    image: redis:7-alpine
```

## Test Coverage
- `pyproject.toml` sets `fail_under = 60` for coverage
- But with only 181/8600 tests running, actual covered percentage is misleading
- Many integration tests use real services (no mocking strategy)

## Testing Technology Stack
- pytest + pytest-asyncio
- pytest-mock for mocking
- httpx + pytest-httpx for API testing
- NO testcontainers (would solve the CI problem)
- NO factory_boy or similar for test data

## What We Need
1. **testcontainers-python** to spin up PostgreSQL + Redis in CI
2. **Proper pytest markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.e2e`
3. **Service container GitHub Actions** with health checks
4. **Test data factories** for real estate domain objects
5. **Coverage enforcement** that's actually meaningful (based on real test runs)
