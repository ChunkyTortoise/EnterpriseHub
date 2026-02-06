## Summary

<!-- Provide a brief, clear description of what this PR does -->

### Type of Change

<!-- Check all that apply. Use conventional commit prefixes in your PR title. -->

- [ ] `feat:` New feature (non-breaking change that adds functionality)
- [ ] `fix:` Bug fix (non-breaking change that fixes an issue)
- [ ] `docs:` Documentation update
- [ ] `style:` Code style/formatting (no functional changes)
- [ ] `refactor:` Code refactoring (no functional changes)
- [ ] `perf:` Performance improvement
- [ ] `test:` Test additions or improvements
- [ ] `chore:` Build process, dependencies, or tooling changes
- [ ] `ci:` CI/CD pipeline changes
- [ ] **Breaking change** (fix or feature that would cause existing functionality to change)

---

## Description

<!--
Describe your changes in detail:
- What problem does this solve?
- What approach did you take?
- Are there any trade-offs or limitations?
-->

### Module(s) Affected

<!-- Check all modules that are modified by this PR -->

- [ ] Jorge Bots (`agents/jorge_*_bot.py`)
- [ ] BI Dashboard (`streamlit_demo/`)
- [ ] FastAPI Routes (`api/`)
- [ ] GHL CRM Integration (`services/enhanced_ghl_client.py`)
- [ ] AI Orchestration (`services/claude_orchestrator.py`)
- [ ] ML Scoring Engines (`services/*engine*.py`)
- [ ] RAG Pipeline (`advanced_rag_system/`)
- [ ] Voice AI (`services/voice_ai_integration.py`)
- [ ] Stripe Billing (`services/subscription_manager.py`)
- [ ] Agent Mesh (`services/agent_mesh_coordinator.py`)
- [ ] Models (`models/`)
- [ ] Utilities (`utils/`)
- [ ] Core App (`app.py`)
- [ ] Tests (`tests/`)
- [ ] CI/CD (`.github/`)
- [ ] Docker/Infrastructure (`docker-compose*.yml`, `Dockerfile*`)

---

## Test Plan

<!-- Describe how you tested your changes -->

### Automated Testing

- [ ] All existing tests pass: `pytest tests/ -v`
- [ ] Added new unit tests for new functionality
- [ ] Added integration tests (if applicable)
- [ ] Test coverage meets 80%+ threshold for new code: `pytest --cov`

### Manual Testing

- [ ] Ran FastAPI locally: `uvicorn ghl_real_estate_ai.api.main:app`
- [ ] Ran Streamlit locally: `streamlit run ghl_real_estate_ai/streamlit_demo/app.py`
- [ ] Tested affected module(s) end-to-end
- [ ] Verified edge cases and error handling

---

## Code Quality Checklist

### Linting and Formatting

- [ ] `ruff check .` passes with no errors
- [ ] `ruff format --check .` passes with no formatting issues
- [ ] Pre-commit hooks pass: `pre-commit run --all-files`

### Type Safety

- [ ] `pyright` passes with no errors
- [ ] All new functions have complete type hints (parameters and return types)

### Security

- [ ] `bandit -r ghl_real_estate_ai/` passes with no high-severity issues
- [ ] No secrets, credentials, or API keys in the code
- [ ] User inputs are validated with Pydantic at boundaries
- [ ] PII handling follows encryption requirements (Fernet)

### Architecture Compliance

- [ ] Follows existing patterns in the affected module
- [ ] API endpoints use response envelope (success/data/meta)
- [ ] Database changes include Alembic migration with downgrade
- [ ] External API calls use circuit breaker pattern
- [ ] Proper error handling with structured JSON responses

---

## Screenshots

<!-- If this PR includes UI changes, add before/after screenshots -->

<details>
<summary>Click to expand screenshots</summary>

| Before | After |
|--------|-------|
| (screenshot) | (screenshot) |

</details>

---

## Related Issues

<!-- Link any related issues using GitHub keywords -->

- Closes #
- Fixes #
- Related to #

---

## Additional Notes

<!--
Any additional context, implementation notes, or questions for reviewers?
-->

---

_By submitting this PR, I confirm that my contribution follows the project's coding standards and architecture constraints as defined in CLAUDE.md._
