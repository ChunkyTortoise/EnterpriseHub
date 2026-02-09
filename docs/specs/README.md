# EnterpriseHub Comprehensive Improvement Specs

## Overview

This directory contains 8 self-contained specification documents for systematic codebase improvements. Each spec is designed to be executed by an agent in a separate chat session.

**Audit Summary:**
- 81 files with bare `except:` clauses
- 786 files using `Dict[str, Any]`
- Blocking sync I/O in async FastAPI app
- CORS wildcard + credentials enabled
- Open redirect in SSO flow
- CI unit test path points to nonexistent directory
- 76% of API routes untested (60 of 79)
- God classes (1,000+ lines) and tight coupling

---

## Execution Phases

### Phase 1: Critical Fixes (P0) - Run in Parallel

| Spec | Agent | Files | Focus |
|------|-------|-------|-------|
| [01-security-hardening](spec-01-security-hardening.md) | security-auditor | ~15 | CORS, redirects, passwords |
| [02-async-performance](spec-02-async-performance.md) | performance-optimizer | ~8 | GHL async, N+1 queries |
| [03-ci-test-infrastructure](spec-03-ci-test-infrastructure.md) | quality-gate | ~5 | Test paths, coverage |

**Estimated time:** 2-3 days (parallel execution)

### Phase 2: Quality Improvements (P1)

| Spec | Agent | Files | Focus | Dependencies |
|------|-------|-------|-------|--------------|
| [04-bare-except-elimination](spec-04-bare-except-elimination.md) | feature-enhancement-guide | 81 | Exception handling | None |
| [05-test-coverage-core](spec-05-test-coverage-core.md) | test-engineering | ~15 new | Core service tests | Spec 3 |

**Estimated time:** 3-4 days

### Phase 3: Architecture (P2)

| Spec | Agent | Files | Focus | Dependencies |
|------|-------|-------|-------|--------------|
| [06-god-class-decomposition](spec-06-god-class-decomposition.md) | architecture-sentinel | ~14 | Split large files | Spec 4 |
| [07-type-safety](spec-07-type-safety.md) | feature-enhancement-guide | ~30 | TypedDicts | Spec 6 |

**Estimated time:** 2-3 days

### Phase 4: Cleanup (P3)

| Spec | Agent | Files | Focus | Dependencies |
|------|-------|-------|-------|--------------|
| [08-dead-code-cleanup](spec-08-dead-code-cleanup.md) | feature-enhancement-guide | ~20 | Duplication, dead code | Specs 4-7 |

**Estimated time:** 1-2 days

---

## Quick Start

### For Each Spec:

1. **Open new agent session** with recommended agent type
2. **Copy entire spec** into chat
3. **Execute** following the spec's structure
4. **Verify** using provided commands
5. **Commit** changes with descriptive message

### Example Workflow:

```bash
# Start 3 parallel sessions for Phase 1
claude --agent security-auditor
# Paste spec-01-security-hardening.md

claude --agent performance-optimizer
# Paste spec-02-async-performance.md

claude --agent quality-gate
# Paste spec-03-ci-test-infrastructure.md
```

---

## Verification Commands

Each spec includes verification commands. Run these after completion:

```bash
# Security (Spec 1)
grep -rn "allow_origins.*\*" ghl_real_estate_ai/ --include="*.py"
pytest tests/ -k "security or auth" -v

# Performance (Spec 2)
grep -rn "import requests" ghl_real_estate_ai/ --include="*.py"
pytest tests/ -k "leads or ghl" -v

# CI/CD (Spec 3)
pytest tests/ -m unit -v
pytest tests/ --cov=ghl_real_estate_ai --cov-fail-under=60

# Bare Excepts (Spec 4)
grep -rn "except:" ghl_real_estate_ai/ --include="*.py" | grep -v "except [A-Z]" | wc -l

# Test Coverage (Spec 5)
pytest tests/ --co -q | wc -l
pytest tests/ -m unit -v

# God Classes (Spec 6)
wc -l ghl_real_estate_ai/services/claude_assistant.py
wc -l ghl_real_estate_ai/streamlit_demo/app.py

# Type Safety (Spec 7)
grep -rn "Dict\[str, Any\]" ghl_real_estate_ai/ --include="*.py" | wc -l
mypy ghl_real_estate_ai/ --ignore-missing-imports

# Cleanup (Spec 8)
ruff check ghl_real_estate_ai/ --select F401
grep -rn "time.sleep" tests/ --include="*.py" | wc -l
```

---

## Success Metrics

| Metric | Before | Target | Spec |
|--------|--------|--------|------|
| Security vulnerabilities | 5 | 0 | 1 |
| Blocking I/O calls | Multiple | 0 | 2 |
| Test coverage | ~60% | 80% | 3, 5 |
| Bare except clauses | 200+ | 0 | 4 |
| Untested routes | 60/79 | 0/79 | 5 |
| Files > 1000 lines | 3 | 0 | 6 |
| Dict[str, Any] usage | 786 | <400 | 7 |
| time.sleep() in tests | 125 | <10 | 8 |

---

## Notes

- **Parallel execution**: Phase 1 specs (1-3) can run simultaneously
- **Dependencies**: Check "Dependencies" column before starting
- **Testing**: Run full test suite after each spec completion
- **Commits**: Make atomic commits per spec for easy rollback
- **Documentation**: Update relevant docs after architectural changes

---

## Support

For questions or issues during implementation:
- Check spec's "Acceptance Criteria" section
- Review "Verification Commands" for debugging
- Consult original audit in parent plan document
