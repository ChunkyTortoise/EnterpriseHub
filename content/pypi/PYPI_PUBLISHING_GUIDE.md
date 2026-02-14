# PyPI Publishing Guide -- docqa-engine & insight-engine

**Date**: 2026-02-13
**Packages**: docqa-engine v0.1.0, insight-engine v0.1.0
**Status**: Ready to publish (all metadata verified)

---

## Pre-Publishing Verification

Both packages have been verified with:
- [x] `pyproject.toml` with hatchling build system
- [x] `__init__.py` with `__version__ = "0.1.0"` and `__all__` exports
- [x] `py.typed` marker for type checking support
- [x] Professional README.md with badges, architecture diagrams, metrics
- [x] MIT LICENSE file
- [x] Test suites (550+ for docqa, 520+ for insight)
- [x] CI/CD via GitHub Actions
- [x] Live Streamlit demos deployed

---

## Step 1: Create PyPI Account (One-Time)

1. Go to https://pypi.org/account/register/
2. Create account with `cayman.roden@gmail.com`
3. Enable 2FA (required for new accounts)
4. Create an API token at https://pypi.org/manage/account/token/
   - Scope: "Entire account" (for first publish)
   - Save the token securely

---

## Step 2: Install Build Tools

```bash
pip install build twine
```

---

## Step 3: Build docqa-engine

```bash
cd /Users/cave/Documents/GitHub/docqa-engine

# Clean any previous builds
rm -rf dist/ build/ *.egg-info

# Build the package
python -m build

# Verify the build
twine check dist/*
```

Expected output:
```
dist/docqa_engine-0.1.0-py3-none-any.whl
dist/docqa_engine-0.1.0.tar.gz
```

---

## Step 4: Build insight-engine

```bash
cd /Users/cave/Documents/GitHub/insight-engine

# Clean any previous builds
rm -rf dist/ build/ *.egg-info

# Build the package
python -m build

# Verify the build
twine check dist/*
```

Expected output:
```
dist/insight_engine-0.1.0-py3-none-any.whl
dist/insight_engine-0.1.0.tar.gz
```

---

## Step 5: Test Upload (TestPyPI -- Recommended)

```bash
# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Test install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ docqa-engine
pip install --index-url https://test.pypi.org/simple/ insight-engine
```

---

## Step 6: Publish to PyPI (Production)

```bash
# docqa-engine
cd /Users/cave/Documents/GitHub/docqa-engine
twine upload dist/*

# insight-engine
cd /Users/cave/Documents/GitHub/insight-engine
twine upload dist/*
```

When prompted:
- Username: `__token__`
- Password: `pypi-AgEIcH...` (your API token)

---

## Step 7: Verify Publication

After publishing, verify at:
- https://pypi.org/project/docqa-engine/
- https://pypi.org/project/insight-engine/

Test install:
```bash
pip install docqa-engine
pip install insight-engine
```

---

## Step 8: Add PyPI Badges to READMEs

Add these badges to both READMEs after publishing:

**docqa-engine:**
```markdown
[![PyPI](https://img.shields.io/pypi/v/docqa-engine.svg)](https://pypi.org/project/docqa-engine/)
[![Downloads](https://img.shields.io/pypi/dm/docqa-engine.svg)](https://pypi.org/project/docqa-engine/)
```

**insight-engine:**
```markdown
[![PyPI](https://img.shields.io/pypi/v/insight-engine.svg)](https://pypi.org/project/insight-engine/)
[![Downloads](https://img.shields.io/pypi/dm/insight-engine.svg)](https://pypi.org/project/insight-engine/)
```

---

## Step 9: GitHub Release

Create GitHub releases to match:

```bash
# docqa-engine
cd /Users/cave/Documents/GitHub/docqa-engine
git tag v0.1.0
git push origin v0.1.0
gh release create v0.1.0 --title "v0.1.0 - Initial Release" --notes "$(cat <<'EOF'
## docqa-engine v0.1.0

Upload documents, ask questions -- get cited answers with a prompt engineering lab.

### Highlights
- Hybrid retrieval (BM25 + Dense + RRF fusion)
- Citation scoring (faithfulness, coverage, redundancy)
- Prompt engineering lab for A/B testing
- 550+ automated tests
- REST API with JWT auth and rate limiting
- Docker deployment ready

### Install
```
pip install docqa-engine
```

### Links
- [Live Demo](https://ct-document-engine.streamlit.app)
- [Documentation](https://github.com/ChunkyTortoise/docqa-engine/blob/main/README.md)
- [PyPI](https://pypi.org/project/docqa-engine/)
EOF
)"

# insight-engine
cd /Users/cave/Documents/GitHub/insight-engine
git tag v0.1.0
git push origin v0.1.0
gh release create v0.1.0 --title "v0.1.0 - Initial Release" --notes "$(cat <<'EOF'
## insight-engine v0.1.0

Upload CSV/Excel, get instant dashboards, predictive models, and PDF reports.

### Highlights
- Auto-profiling with column type detection
- 4 marketing attribution models
- ML predictions with SHAP explainability
- K-means and DBSCAN clustering
- Time series forecasting
- 520+ automated tests
- Docker deployment ready

### Install
```
pip install insight-engine
```

### Links
- [Live Demo](https://ct-insight-engine.streamlit.app)
- [Documentation](https://github.com/ChunkyTortoise/insight-engine/blob/main/README.md)
- [PyPI](https://pypi.org/project/insight-engine/)
EOF
)"
```

---

## LinkedIn Announcement Copy

### Post: docqa-engine on PyPI

```
Just published docqa-engine on PyPI -- an open-source RAG pipeline for document Q&A.

pip install docqa-engine

What it does:
-- Upload PDFs, Word docs, Markdown, CSV
-- Hybrid retrieval (BM25 + dense vectors + RRF fusion)
-- Citation scoring for every answer
-- Prompt engineering lab for A/B testing

Built with 550+ automated tests. Try the live demo: ct-document-engine.streamlit.app

GitHub: github.com/ChunkyTortoise/docqa-engine
PyPI: pypi.org/project/docqa-engine/

#Python #RAG #AI #OpenSource #NLP #DocumentIntelligence
```

### Post: insight-engine on PyPI

```
insight-engine is now on PyPI -- upload CSV/Excel and get instant dashboards with ML predictions.

pip install insight-engine

Features:
-- Auto-profiling (column types, distributions, outliers)
-- 4 marketing attribution models
-- ML predictions with SHAP explanations
-- K-means clustering and anomaly detection
-- Time series forecasting

520+ automated tests. Live demo: ct-insight-engine.streamlit.app

GitHub: github.com/ChunkyTortoise/insight-engine
PyPI: pypi.org/project/insight-engine/

#Python #DataScience #BusinessIntelligence #OpenSource #MachineLearning
```

---

## Automated Publishing (Future)

For future releases, consider adding GitHub Actions for automatic PyPI publishing:

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI
on:
  release:
    types: [published]
jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install build
      - run: python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

This uses PyPI's trusted publisher feature (no API token needed).

---

## Package Metadata Summary

### docqa-engine

| Field | Value |
|-------|-------|
| Name | docqa-engine |
| Version | 0.1.0 |
| Python | >=3.11 |
| License | MIT |
| Author | Cayman Roden |
| Build | hatchling |
| Tests | 550+ |
| Demo | ct-document-engine.streamlit.app |
| Keywords | rag, document-qa, llm, embeddings, vector-search, prompt-engineering |

### insight-engine

| Field | Value |
|-------|-------|
| Name | insight-engine |
| Version | 0.1.0 |
| Python | >=3.11 |
| License | MIT |
| Author | Cayman Roden |
| Build | hatchling |
| Tests | 520+ |
| Demo | ct-insight-engine.streamlit.app |
| Keywords | business-intelligence, dashboards, predictive-analytics, csv, excel, data-visualization |
| Entry Points | `insight-engine` (API server), `insight-profile` (Streamlit app) |
| Optional | shap, database (postgres, bigquery) |
