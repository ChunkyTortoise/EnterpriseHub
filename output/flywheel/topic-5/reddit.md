# Reddit Post: Python DevOps & Developer Tooling

**Topic**: Python DevOps & Developer Tooling
**Subreddit**: r/Python
**Format**: Practical tips with data
**Flair**: [Discussion]

---

## Title

Replaced 4 Python linters with Ruff across 10 repos (30K+ lines). CI went from 12 min to 4 min. Here are the details.

## Body

**tl;dr**: Migrated from Black + isort + flake8 + pylint to Ruff across 10 repos. CI runtime -67%, pre-commit -95%. Migration took under an hour for 5 repos. Also sharing my ADR template that's saved significant debugging time.

---

**Before**:
- Black: formatting
- isort: import sorting
- flake8: style linting
- pylint: advanced checks

4 tools, 4 config files, 45 seconds per run on 15K-line codebase. Occasional Black/isort conflicts on import formatting.

**After**: Ruff. 1 tool, 1 config section, 1.8 seconds. 25x faster.

**Migration per repo (~10 min each)**:

```bash
pip install ruff
ruff check . --fix
ruff format .
```

`pyproject.toml`:
```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "B", "UP"]
```

Update CI config, remove old configs (`.flake8`, `.pylintrc`, `.isort.cfg`), commit.

**Portfolio results (10 repos, 30K+ lines, 8,500+ tests)**:

| Metric | Before | After |
|--------|--------|-------|
| CI runtime | 12 min | 4 min |
| Pre-commit hooks | 8 sec | 0.4 sec |
| Config files per repo | 4 | 1 section |
| Dependencies added | 0 | 0 |

**Caveat**: Ruff doesn't fully replace pylint's advanced checks (duplicate-code, design patterns). I kept pylint in one repo for quarterly reviews, removed it from CI. For most projects, Ruff's 700+ rules are sufficient.

**Bonus: ADR template**

The other productivity win: Architecture Decision Records. 33 across 10 repos. Each takes 15 minutes. One saved me 3 days (was about to rewrite a FAISS integration -- ADR reminded me why I chose it).

Template:

```markdown
# ADR-XXX: [Decision Title]
Status: Accepted | Superseded | Deprecated
Date: YYYY-MM-DD
Context: [Problem and constraints]
Decision: [What you chose and why]
Consequences: [Trade-offs]
Alternatives: [What you rejected and why]
```

Document: database choices, API patterns, caching strategies, auth approaches.
Skip: version bumps, style preferences, obvious choices.

**The compound**: Fast linting (every commit) + documented decisions (every revisit) = significant time savings that grow with repo count and team size.

Happy to answer questions about the Ruff migration or ADR adoption process.
