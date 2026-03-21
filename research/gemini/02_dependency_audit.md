# Dependency Audit

**Date**: 2026-03-19
**Scope**: requirements.txt (146 lines), requirements-dev.txt, requirements-ml.txt, requirements-observability.txt, pyproject.toml

---

## Current State

### File Inventory

| File | Direct Deps | Notes |
|------|------------|-------|
| `requirements.txt` | ~55 packages | Core production — 146 lines including comments |
| `requirements-dev.txt` | ~25 packages | `-r requirements.txt` included |
| `requirements-ml.txt` | ~14 packages | `-r requirements.txt` included |
| `requirements-observability.txt` | 8 packages | Optional, standalone |
| `pyproject.toml` | 7 packages | **Stale** — severely out of sync with requirements.txt |

**Total direct production deps**: ~55
**Estimated transitive deps** (production install): ~250–300 (boto3/botocore alone pull ~40; opentelemetry suite ~20; langchain ecosystem ~30+)

### Dependency Categories (production)

| Category | Packages |
|----------|---------|
| Core framework | streamlit, fastapi, uvicorn |
| Data / analysis | pandas, numpy, scipy, scikit-learn, joblib |
| Visualization | plotly, geopy |
| Market data | yfinance, ta |
| AI / LLM | anthropic, openai, tiktoken, google-generativeai, textblob, langgraph, langchain-core, langchain-anthropic, langsmith, fastmcp, notebooklm-py, google-auth, google-auth-oauthlib |
| DB / cache | psycopg2-binary, asyncpg, pgvector, sqlalchemy, aiohttp, aiosqlite, alembic, redis, aioredis |
| Auth / security | pydantic, pydantic-settings, httpx, python-jose, passlib, PyJWT, cryptography |
| Integrations | twilio, sendgrid, SpeechRecognition, apscheduler, bleach, stripe |
| Utilities | python-dotenv, openpyxl, PyYAML, Jinja2, reportlab, qrcode, aiofiles, nest-asyncio |
| AWS | aioboto3, boto3, botocore |
| Performance | hiredis, uvloop, uvicorn[standard], httptools, orjson, msgpack, cachetools, cloudpickle |
| Observability | opentelemetry-api/sdk + 6 instrumentations, prometheus-client, structlog |
| Real-time | websockets, python-socketio, python-engineio, psutil |
| Async helpers | python-multipart |

---

## Deprecated Packages (P0)

### aioredis — REMOVE

**Status**: Superseded. `aioredis` merged into `redis-py` (the `redis` package) in v4.2.0 (2022). `redis>=5.0.0` (already pinned) provides full async support via `redis.asyncio`.

**Current situation in the codebase**:
- `requirements.txt` pins both `redis>=5.0.0,<6.0` AND `aioredis>=2.0.1,<3.0` — redundant and conflicting.
- The only aioredis import in the codebase is in `ghl_real_estate_ai/services/realtime_config.py` and it is already wrapped in a `try/except ImportError` guard (`AIOREDIS_AVAILABLE = True/False`), meaning it is optional and non-breaking to remove.

**Action**: Remove `aioredis>=2.0.1,<3.0` from `requirements.txt`. No code changes required — the try/except guard handles the missing package gracefully. Async Redis clients should use `redis.asyncio.Redis(...)` from the existing `redis` package.

### python-jose — Monitor

`python-jose[cryptography]` has had CVEs related to its ECDSA implementation (CVE-2024-33663 / algorithm confusion). The `PyJWT>=2.8.0` package (also present) is the preferred modern alternative. If JWT issuance/verification can be consolidated to PyJWT, python-jose can be removed.

### google-generativeai — Likely superseded

Google renamed/replaced `google-generativeai` with `google-genai` (the new unified SDK). The old package still receives updates but Google is pushing users to `google-genai>=1.0.0`. Not urgent but worth tracking.

### passlib[bcrypt] — Low maintenance

`passlib` is not actively maintained (last release 2023). For new code, `bcrypt` directly or `argon2-cffi` is preferred. Existing usage is safe but no security patches are expected.

### notebooklm-py — Unofficial

`notebooklm-py` is an unofficial/community package, not a Google-published SDK. Pin to an exact version and audit before any production security audit.

---

## Version Conflicts

### pyproject.toml vs requirements.txt — CRITICAL divergence

`pyproject.toml` is effectively stale. It lists only 7 packages pinned at old exact versions:

| Package | pyproject.toml | requirements.txt | Risk |
|---------|---------------|-----------------|------|
| streamlit | `==1.28.0` | `>=1.41.1,<2.0` | 13+ minor versions behind |
| pandas | `==2.1.3` | `>=2.1.3,<3.0` | Compatible but exact vs range |
| numpy | `==1.26.2` | `>=1.26.2,<3.0` | Compatible |
| plotly | `==5.17.0` | `==5.18.0` | Conflict — pyproject is one patch behind |
| yfinance | `==0.2.33` | `==0.2.33` | Match |
| ta | `==0.11.0` | `==0.11.0` | Match |
| python-dotenv | `==1.0.0` | `==1.0.0` | Match |

`pyproject.toml` also references `black` and `flake8` as dev tools, which are not in `requirements-dev.txt` (replaced by `ruff`). `pyproject.toml` does not declare any of the ~48 other production dependencies.

**Resolution**: Either update `pyproject.toml` to reflect the full dependency set (making it the source of truth), or explicitly document that `requirements.txt` is authoritative and `pyproject.toml` is only used for package metadata/tooling config.

### observability version drift

`requirements.txt` pins opentelemetry instrumentations at `>=0.41b0,<1.0`, while `requirements-observability.txt` requires `>=0.43b0` and `requirements-dev.txt` also pins `opentelemetry-api/sdk>=1.21.0`. These are compatible but inconsistent — a single source of truth would be cleaner.

### scikit-learn / joblib pinning

`scikit-learn==1.4.0` and `joblib==1.3.2` are exact pins. scikit-learn 1.5.x and 1.6.x are released. These are not conflicting but may miss bug fixes and performance improvements. Consider switching to range pins `>=1.4.0,<2.0`.

---

## Heavy Dependencies (Consider Lazy Importing)

The codebase already notes: "sentence-transformers, transformers, spacy removed — they pull PyTorch (~2GB) and cause Railway builds to timeout." The following remaining packages are heavy and should be evaluated for lazy loading:

| Package | Approx install size | Already lazy? | Recommendation |
|---------|-------------------|---------------|----------------|
| `scipy` | ~35MB + numpy | No | Lazy-import in modules that call it; not needed at server startup |
| `scikit-learn` | ~30MB | No | Lazy-import in ML prediction paths only |
| `yfinance` | ~5MB + many transitive | No | Lazy-import in market data routes |
| `ta` (technical analysis) | ~2MB | No | Co-locate with yfinance lazy import |
| `reportlab` | ~15MB | No | Lazy-import in PDF generation endpoint only |
| `SpeechRecognition` | ~5MB | No | Lazy-import in voice/transcription routes |
| `boto3` + `botocore` | ~30MB + transitive | No | Lazy-import; only needed for S3/AWS features |
| `aioboto3` | depends on boto3 | No | Same as boto3 |
| `mlflow` (ml deps) | ~80MB+ | N/A (ml file) | ML only — keep in requirements-ml.txt |
| `numba` + `llvmlite` (ml deps) | ~100MB | N/A (ml file) | ML only — correct placement |
| `prophet` (ml deps) | ~50MB | N/A (ml file) | ML only — correct placement |
| `kafka-python` (ml deps) | ~5MB | N/A (ml file) | Evaluate if actively used |
| `celery` (ml deps) | ~10MB | N/A (ml file) | Evaluate if actively used vs arq/asyncpg path |

**Lazy import pattern** (already used for sentence-transformers):
```python
def get_sklearn():
    try:
        from sklearn.ensemble import RandomForestClassifier
        return RandomForestClassifier
    except ImportError:
        raise RuntimeError("Install scikit-learn: pip install scikit-learn")
```

---

## Security-Sensitive Packages

These packages require active CVE monitoring and prompt upgrades:

| Package | Why it's sensitive | Current pin | Action |
|---------|-------------------|------------|--------|
| `cryptography` | Core crypto primitives; frequent CVEs | `>=41.0.0,<44.0` | Upper bound risks missing security patches — consider `>=41.0.0` without upper bound or widen to `<46.0` |
| `python-jose[cryptography]` | JWT + ECDSA — CVE-2024-33663 (algorithm confusion) | `>=3.3.0,<4.0` | Evaluate replacing with PyJWT; or pin `==3.3.0` and monitor |
| `passlib[bcrypt]` | Password hashing | `>=1.7.4,<2.0` | Unmaintained; migrate to `bcrypt` directly or `argon2-cffi` |
| `PyJWT` | JWT issuance/verification | `>=2.8.0,<3.0` | Keep updated; PyJWT 2.9+ has security improvements |
| `anthropic` / `openai` | API key exposure if misconfigured | `>=0.40.0` / `>=1.50.0` | Keys must remain env-only; keep at latest minor |
| `stripe` | Financial transactions | `>=8.0.0,<12.0` | Wide upper bound — narrow to `<10.0` or `<11.0` once tested |
| `bleach` | HTML sanitization (XSS prevention) | `>=6.0.0,<7.0` | Keep current; bleach 6.x is maintained |
| `httpx` | HTTP client — SSRF surface | `>=0.26.0,<1.0` | Validate all outbound URLs; do not pass user-controlled URLs directly |
| `sqlalchemy` | ORM / SQL injection surface | `>=2.0.0,<3.0` | Always use parameterized queries; never raw string interpolation |
| `psycopg2-binary` | DB driver | `>=2.9.0,<3.0` | Consider migrating to `psycopg[binary]` (psycopg3) for async-native support |

### Recommended monitoring
Run `pip audit` or `safety check` in CI (already in requirements-dev.txt as `safety>=3.0.0`). Add `bandit` scan to pre-commit hooks (already listed).

---

## Recommended Minimal Production Set

Current production install is estimated at ~300 transitive packages. A leaner set for the core API-only deployment (no Streamlit, no ML, no AWS):

### Tier 1 — API Core (always required)
```
fastapi>=0.109.0,<1.0
uvicorn[standard]>=0.27.0,<1.0
pydantic>=2.7.4,<3.0
pydantic-settings>=2.1.0,<3.0
python-dotenv==1.0.0
httpx[http2]>=0.26.0,<1.0
aiofiles>=24.1.0,<25.0
redis>=5.0.0,<6.0          # replaces aioredis
hiredis>=2.2.3,<4.0
psycopg2-binary>=2.9.0,<3.0
asyncpg>=0.29.0,<1.0
sqlalchemy>=2.0.0,<3.0
alembic>=1.13.0,<2.0
pgvector>=0.2.0,<1.0
aiohttp==3.13.3
orjson>=3.9.10,<4.0
structlog>=23.2.0,<25.0
PyJWT>=2.8.0,<3.0
python-jose[cryptography]>=3.3.0,<4.0
passlib[bcrypt]>=1.7.4,<2.0
cryptography>=41.0.0,<46.0
python-multipart>=0.0.6,<1.0
PyYAML>=6.0,<7.0
Jinja2>=3.1.0,<4.0
bleach>=6.0.0,<7.0
```

### Tier 2 — AI/LLM (required for bot functionality)
```
anthropic>=0.40.0,<1.0
openai>=1.50.0,<2.0
tiktoken>=0.7.0,<1.0
google-generativeai>=0.8.0,<1.0
google-auth>=2.20.0
google-auth-oauthlib>=1.0.0
langgraph==1.0.6
langchain-core>=1.0.0,<2.0.0
langchain-anthropic>=0.1.0,<2.0.0
langsmith>=0.1.0,<1.0
fastmcp>=0.2.0,<1.0
```

### Tier 3 — Integration (enable per deployment)
```
twilio>=9.0.0,<10.0
sendgrid>=6.11.0,<7.0
stripe>=8.0.0,<10.0
apscheduler>=3.10.0,<4.0
websockets>=12.0,<14.0
python-socketio>=5.11.0,<6.0
python-engineio>=4.8.0,<5.0
psutil>=5.9.0,<7.0
```

### Tier 4 — Dashboard (Streamlit deployments only)
```
streamlit>=1.41.1,<2.0
pandas>=2.1.3,<3.0
numpy>=1.26.2,<3.0
plotly==5.18.0
geopy>=2.4.0,<3.0
yfinance==0.2.33
ta==0.11.0
scipy>=1.11.4,<2.0
scikit-learn>=1.4.0,<2.0
joblib>=1.3.2,<2.0
textblob==0.17.1
openpyxl==3.1.2
reportlab>=4.0,<5.0
qrcode[pil]>=7.4.2,<8.0
SpeechRecognition>=3.10.0,<4.0
```

### Tier 5 — AWS (only if S3/cloud storage is used)
```
aioboto3>=12.3.0,<14.0
boto3>=1.34.0,<2.0
botocore>=1.34.0,<2.0
```

### Packages to remove entirely
| Package | Reason |
|---------|--------|
| `aioredis>=2.0.1,<3.0` | Superseded by `redis>=5.0.0` async API |
| `nest-asyncio>=1.5.8,<2.0` | Workaround for nested event loops — indicates architectural issue; remove and fix the root cause |
| `notebooklm-py>=0.3.2` | Unofficial package; evaluate whether it's used in production paths |
| `aiosqlite>=0.19.0,<1.0` | SQLite not used in production (PostgreSQL is); dev/test only |
| `cachetools>=5.3.2,<6.0` | Likely redundant with Redis cache layers; audit actual usage |
| `cloudpickle>=3.0.0,<4.0` | Verify if used outside ML paths; if so, move to requirements-ml.txt |
| `msgpack>=1.0.7,<2.0` | Verify active use; if only for Redis serialization, may be replaceable with orjson |
| `httptools>=0.6.1,<1.0` | Pulled in by uvicorn[standard] already as transitive dep — explicit pin is redundant |

---

## Migration to uv/Poetry Groups

### Option A: uv (recommended — fastest, modern)

uv reads from `pyproject.toml`. Migrate by updating `pyproject.toml` to be the authoritative dependency file:

```toml
[project]
name = "enterprise-hub"
version = "5.0.1"
requires-python = ">=3.12"
dependencies = [
    # Tier 1 + Tier 2 + Tier 3 inline here
]

[project.optional-dependencies]
dashboard = [
    # Tier 4 — streamlit, pandas, numpy, plotly, etc.
]
aws = [
    # Tier 5 — aioboto3, boto3, botocore
]
ml = [
    # requirements-ml.txt contents
]
observability = [
    # requirements-observability.txt contents
]
dev = [
    # requirements-dev.txt contents (without -r requirements.txt)
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.1.8",
    "mypy>=1.7.0",
    # ... etc
]

[build-system]
requires = ["hatchling"]  # or keep setuptools
build-backend = "hatchling.build"  # or setuptools.build_meta
```

**Install commands with uv:**
```bash
uv sync                          # production only
uv sync --extra dashboard        # + Streamlit/pandas/etc.
uv sync --extra ml               # + ML packages
uv sync --extra dev              # + all dev tools
uv sync --all-extras             # everything
```

**uv.lock** replaces requirements.txt pin files — commit it for reproducible deploys.

### Option B: Poetry groups

```toml
[tool.poetry.dependencies]
python = "^3.12"
fastapi = ">=0.109.0,<1.0"
# ... core deps

[tool.poetry.group.dashboard.dependencies]
streamlit = ">=1.41.1,<2.0"
pandas = ">=2.1.3,<3.0"

[tool.poetry.group.ml.dependencies]
xgboost = ">=3.1.0"
mlflow = ">=2.8.0"

[tool.poetry.group.observability.dependencies]
opentelemetry-api = ">=1.22.0"

[tool.poetry.group.dev.dependencies]
pytest = ">=8.0.0"
ruff = ">=0.1.8"
```

### Recommended migration sequence

1. **Immediate** (no code changes): Remove `aioredis` from `requirements.txt`
2. **Short-term** (1 sprint): Update `pyproject.toml` to match actual dependency set; retire stale version pins (streamlit 1.28, plotly 5.17)
3. **Short-term** (1 sprint): Move `aiosqlite`, `cloudpickle`, `msgpack` to conditional groups; audit `notebooklm-py` usage
4. **Medium-term** (2–3 sprints): Migrate to uv with `pyproject.toml` as single source of truth; generate `uv.lock`; delete `requirements*.txt` files in favor of uv extras
5. **Medium-term**: Investigate `python-jose` replacement with `PyJWT`; migrate `passlib` to `bcrypt` directly
6. **Long-term**: Widen `cryptography` upper bound; narrow `stripe` upper bound to tested range

### Railway/render build size impact

Switching to uv groups would allow Railway to install `uv sync` (core only) and skip `--extra ml` (saves ~300MB from numba/llvmlite/mlflow/prophet). This directly addresses the Railway timeout issue mentioned in requirements.txt comments.
