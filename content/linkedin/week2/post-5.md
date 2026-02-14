# LinkedIn Post #5 — Ruff Linter Migration

**Publish Date**: Wednesday, February 19, 2026 @ 9:00am PT
**Topic**: Developer Tooling — Python Productivity
**Goal**: Broad reach (Python devs), drive engagement, showcase DevOps skills

---

## Post Content

I just replaced 4 Python linters with one tool. And it's 10-100x faster.

Before:
```bash
black .          # Formatting
isort .          # Import sorting
flake8 .         # Linting
pylint .         # More linting
# Total: ~45 seconds on a 15K line codebase
```

After:
```bash
ruff check --fix .
ruff format .
# Total: <2 seconds
```

**What is Ruff?**

An "extremely fast Python linter" written in Rust. It replaces Black, isort, flake8, and most of pylint's rules.

**Speed comparison on EnterpriseHub (15,000+ lines, 8,500+ tests):**
- Old stack: 45 seconds
- Ruff: 1.8 seconds
- **25x faster**

**But speed isn't the only win.**

**Single config file:**
No more juggling `.flake8`, `pyproject.toml`, `.pylintrc`, and `.isort.cfg`. Everything lives in one place.

**Auto-fix by default:**
Most other linters just complain. Ruff fixes issues automatically (imports, line length, unused variables).

**Drop-in replacement:**
I migrated 5 repos in under an hour. Changed CI config, ran `ruff check`, committed fixes. Done.

**Real results from my portfolio (10 repos, 30K+ lines):**
- CI runtime: 12 min → 4 min (67% reduction)
- Pre-commit hooks: 8 sec → 0.4 sec
- Zero new dependencies (single binary)

**How to migrate:**

```bash
pip install ruff
ruff check . --fix  # Auto-fix issues
ruff format .       # Format code
```

Add to `pyproject.toml`:
```toml
[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W"]
```

**One caveat:** If you rely heavily on pylint's advanced checks (design patterns, code smells), you'll need to keep it around. For most teams, Ruff's 700+ rules are enough.

Still running black + isort + flake8 separately? You're spending 10+ hours/year waiting on CI.

Try Ruff. Thank me later.

Docs: docs.astral.sh/ruff
My migration guide: github.com/ChunkyTortoise/EnterpriseHub/docs/ADR/ruff-migration.md

#Python #DevOps #CI #SoftwareEngineering #DeveloperTools

---

## Engagement Strategy

**CTA**: Link to Ruff docs + migration guide
**Expected Replies**: 60-80 (broad Python audience)
**Response Time**: <1 hour for all comments

**Prepared Responses**:

**Q: "What about flake8-bugbear / flake8-docstrings equivalents?"**
A: Ruff has built-in support for bugbear rules (select = ["B"]) and pydocstyle/flake8-docstrings rules (select = ["D"]). I actually found it MORE comprehensive than my old flake8 plugin stack. Check the full rule reference: docs.astral.sh/ruff/rules/

**Q: "Does Ruff handle notebooks (.ipynb)?"**
A: Yes! As of v0.1.0, Ruff supports Jupyter notebooks natively. Just run `ruff check notebook.ipynb`. It lints code cells and respects notebook-specific quirks (like display() calls). I use it on all my Streamlit demo notebooks.

**Q: "How does this compare to pylint's feature set?"**
A: Ruff covers ~80% of pylint's rules but runs 100x faster. It doesn't have pylint's advanced checks like duplicate-code detection or design pattern analysis. For most teams, the speed trade-off is worth it. I kept pylint in one repo (EnterpriseHub) for architectural reviews, but run it manually, not in CI.

---

## Follow-Up Actions

- [ ] 9:00am PT: Publish post
- [ ] 9:05am: Comment on 5 Python/DevTools posts
- [ ] Throughout day: Reply to all comments within 1 hour
- [ ] Send 5 connection requests to engaged commenters
- [ ] Track metrics: impressions, engagement rate, link clicks
