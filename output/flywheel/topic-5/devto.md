---
title: "The Two Python Productivity Wins That Compound Over Time: Ruff + ADRs"
published: false
tags: python, devops, productivity, ci
cover_image:
canonical_url:
---

# The Two Python Productivity Wins That Compound Over Time: Ruff + ADRs

I manage 10 Python repositories with 30K+ lines of code and 8,500+ tests. Two changes had the biggest compound impact on developer productivity: migrating to Ruff and adopting Architecture Decision Records.

Neither is a novel idea. But the compound effect of fast tooling + documented decisions is dramatic.

---

## Part 1: Ruff Migration

### Before

My linting stack was standard:
- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Style linting
- **pylint**: Advanced checks

Four tools. Four config files (`.flake8`, `pyproject.toml` for Black, `.pylintrc`, `.isort.cfg`). Occasional conflicts between them (Black and isort disagreed on import formatting). 45 seconds per run on a 15K-line codebase.

### After

```bash
pip install ruff
ruff check . --fix
ruff format .
```

One tool. One config section in `pyproject.toml`. 1.8 seconds. 25x faster.

### The Migration

The actual migration across 5 repos took under an hour:

1. Install Ruff: `pip install ruff`
2. Run auto-fix: `ruff check . --fix`
3. Run formatter: `ruff format .`
4. Add config to `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "B", "UP"]
```

5. Update CI config (replace 4 linter steps with 2 Ruff steps)
6. Remove old configs (`.flake8`, `.pylintrc`, `.isort.cfg`)
7. Commit + push

### Portfolio-Wide Results

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| CI runtime (all repos) | 12 min | 4 min | -67% |
| Pre-commit hooks | 8 sec | 0.4 sec | -95% |
| Config files | 4 per repo | 1 section | -75% |
| Dependencies added | 0 | 0 (single binary) | -- |

The pre-commit speed is the most impactful daily change. At 8 seconds, developers mentally context-switch. At 0.4 seconds, it's invisible. Over a year of commits, that saves hours.

### One Caveat

Ruff doesn't fully replace pylint's advanced checks: duplicate code detection, design pattern analysis, code smell detection. I kept pylint in one repo (EnterpriseHub) for quarterly architecture reviews, but removed it from CI. The time-per-run trade-off isn't worth it for CI pipelines.

---

## Part 2: Architecture Decision Records

### The Problem ADRs Solve

Six months after making a technical decision, you'll stare at your code asking "why did I choose FAISS over Pinecone?"

That question cost me 3 days. I started rewriting the vector store integration. Halfway through, I remembered the original reason (cold-start latency requirements for serverless deployment). Reverted everything.

That's when I started writing ADRs.

### The Format

An ADR is a one-page markdown file that captures four things:

```markdown
# ADR-XXX: [Decision Title]

**Status**: Accepted | Superseded | Deprecated
**Date**: YYYY-MM-DD

## Context
[What problem were you solving? What constraints did you have?]

## Decision
[What did you choose and why?]

## Consequences
[Trade-offs, both positive and negative]

## Alternatives Considered
[What else did you evaluate and why you rejected it?]
```

### Real Example

```markdown
# ADR-017: Hybrid BM25 + Dense Retrieval over Pure Semantic Search

Status: Accepted
Date: 2025-09-15

## Context
Pure embedding search returned semantically similar but factually wrong
chunks. Users searching for "FHA loan requirements" got results about
"VA loan benefits."

## Decision
Implement hybrid retrieval with Reciprocal Rank Fusion (BM25 + Dense).

## Consequences
+ Precision@5 improved 34%
+ Keyword-exact queries now return correct results
- Added BM25 index maintenance (~2min rebuild on update)
- Slightly higher latency (+12ms P95)

## Alternatives
- Re-ranking with cross-encoder: Too slow at 200ms+ overhead
- Fine-tuned embeddings: Insufficient domain training data
```

15 minutes to write. Saved 3 days when we revisited the retrieval strategy.

### 33 ADRs Later

Across 10 repos:

- **Every architectural choice** traceable to a documented reason
- **Onboarding 10x faster**: New contributors read ADRs instead of guessing
- **Zero re-debates**: "We already evaluated that -- see ADR-012"
- **Living history**: Some ADRs have "Superseded by ADR-025" -- that's healthy evolution

### What to Document vs. Skip

**Document**: Database choices, API patterns, caching strategies, authentication approaches, testing strategies, model/provider selection.

**Skip**: Library version bumps, code style preferences (that's what linters are for), obvious choices with no real alternatives.

The bar: "Will future-me wonder why I did this?" If yes, write it. If no, skip it.

---

## The Compound Effect

Fast tooling + documented decisions create a compound productivity loop:

1. **Ruff**: Every commit is faster. CI is faster. Pre-commit is invisible. Developers stay in flow.
2. **ADRs**: Every revisit is faster. Onboarding is faster. Architecture discussions reference docs, not memory.

Across 10 repos and 8,500+ tests:
- All tests run in under 2 minutes
- Every decision documented
- Zero time re-debating settled choices
- Pre-commit hooks feel instant

Neither change was dramatic on its own. Together, they've saved more time than any single feature I've built.

---

## Getting Started

### Ruff (10 minutes)

```bash
pip install ruff
ruff check . --fix
ruff format .
```

### ADRs (15 minutes per decision)

Create `docs/ADR/` in your repo. Copy the template above. Write your first ADR for the last technical decision your team debated.

---

*Want the full template collection? All 33 ADRs are in my repos: [github.com/ChunkyTortoise](https://github.com/ChunkyTortoise)*
