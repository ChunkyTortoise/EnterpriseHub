# Twitter/X Thread: Python DevOps & Developer Tooling

**Topic**: Python DevOps & Developer Tooling
**Format**: 7-tweet thread
**CTA**: Template sharing + engagement

---

## Tweet 1 (Hook)

I replaced 4 Python linters with one tool.

CI runtime: 12 min -> 4 min
Pre-commit: 8 sec -> 0.4 sec
Lines of code: 30K+
Repos: 10

The tool is Ruff. Here's the migration and results:

[thread]

---

## Tweet 2 (Before)

Before:
- Black (formatting)
- isort (imports)
- flake8 (linting)
- pylint (advanced checks)

4 tools. 4 config files. 45 seconds per run on 15K lines.

And they occasionally fought each other (Black vs. isort import formatting).

---

## Tweet 3 (After)

After:
- Ruff (everything)

1 tool. 1 config. 1.8 seconds. 25x faster.

700+ rules built-in. Auto-fix by default. Written in Rust.

The migration across 5 repos took under an hour.

---

## Tweet 4 (Migration Steps)

The migration:

```bash
pip install ruff
ruff check . --fix
ruff format .
```

Add to pyproject.toml:
```toml
[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W"]
```

Update CI config. Done. Under 10 minutes per repo.

---

## Tweet 5 (Portfolio-Wide Results)

Results across 10 repos, 30K+ lines:

- CI runtime: 12 min -> 4 min (-67%)
- Pre-commit: 8 sec -> 0.4 sec (-95%)
- Zero new dependencies (single binary)
- 8,500+ tests run in under 2 min
- Pre-commit hooks feel instant

Developer experience matters.

---

## Tweet 6 (ADRs)

The other productivity multiplier: Architecture Decision Records.

33 ADRs across 10 repos. 15 min to write each.

One ADR saved me 3 days. I was about to rewrite a FAISS integration. The ADR reminded me why I chose FAISS (cold-start latency). Reverted before wasting a week.

---

## Tweet 7 (CTA)

Two quick wins for any Python project:

1. Replace your linter stack with Ruff (~10 min)
2. Start writing ADRs for non-obvious decisions (~15 min each)

Compound effect: faster CI, faster pre-commit, every decision documented.

What's your CI runtime? If it's over 5 min, you probably have a quick win.
