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

- [ ] Market Pulse (`modules/market_pulse.py`)
- [ ] Financial Analyst (`modules/financial_analyst.py`)
- [ ] Margin Hunter (`modules/margin_hunter.py`)
- [ ] Agent Logic (`modules/agent_logic.py`)
- [ ] Content Engine (`modules/content_engine.py`)
- [ ] Data Detective (`modules/data_detective.py`)
- [ ] Marketing Analytics (`modules/marketing_analytics.py`)
- [ ] Multi-Agent Workflow (`modules/multi_agent.py`)
- [ ] Smart Forecast (`modules/smart_forecast.py`)
- [ ] Design System (`modules/design_system.py`)
- [ ] Utilities (`utils/`)
- [ ] Core App (`app.py`)
- [ ] Tests (`tests/`)
- [ ] CI/CD (`.github/`)

---

## Test Plan

<!-- Describe how you tested your changes -->

### Automated Testing

- [ ] All existing tests pass: `pytest tests/ -v`
- [ ] Added new unit tests for new functionality
- [ ] Added integration tests (if applicable)
- [ ] Test coverage meets 80%+ threshold for new code: `pytest --cov=modules --cov=utils`

### Manual Testing

- [ ] Ran the app locally: `streamlit run app.py`
- [ ] Tested affected module(s) end-to-end
- [ ] Verified edge cases and error handling
- [ ] Tested with missing API key (if AI features affected)

---

## Code Quality Checklist

### Linting and Formatting

- [ ] `ruff check .` passes with no errors
- [ ] `ruff format --check .` passes with no formatting issues
- [ ] Pre-commit hooks pass: `pre-commit run --all-files`

### Type Safety

- [ ] `mypy modules/ utils/` passes with no errors
- [ ] All new functions have complete type hints (parameters and return types)

### Security

- [ ] `bandit -r modules/ utils/` passes with no high-severity issues
- [ ] No secrets, credentials, or API keys in the code
- [ ] User inputs are validated at boundaries

### Architecture Compliance

- [ ] **No cross-module imports** (modules only import from `utils/`)
- [ ] Session state initialized at module top level (not inside functions)
- [ ] Expensive operations use `@st.cache_data(ttl=300)`
- [ ] Proper error handling with custom exceptions from `utils/exceptions.py`
- [ ] API integrations have graceful fallbacks when keys are missing

### Documentation

- [ ] Docstrings added to all new public functions
- [ ] CLAUDE.md updated (if adding new modules or patterns)
- [ ] CHANGELOG.md updated (for user-facing changes)

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
- Known limitations?
- Future improvements planned?
- Areas that need careful review?
-->

---

## Reviewer Guidance

<!-- Help reviewers focus on what matters most -->

**Key files to review:**
-

**Areas needing careful review:**
-

---

_By submitting this PR, I confirm that my contribution follows the project's coding standards and architecture constraints as defined in CLAUDE.md._
