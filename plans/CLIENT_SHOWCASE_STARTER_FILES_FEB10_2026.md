# Client Showcase Starter Files (New Chat)

Use this file list to bootstrap a new chat fast without loading unnecessary context.

---

## 1) Primary Execution Files

1. `plans/CLIENT_SHOWCASE_COMPLETION_SPEC_FEB10_2026.md`  
   Full scope, phases, acceptance criteria, and verification matrix.

2. `plans/CLIENT_SHOWCASE_NEW_CHAT_PROMPT_FEB10_2026.md`  
   Copy/paste prompt for immediate continuation.

3. `streamlit_cloud/app.py`  
   Current client showcase implementation and latest metric constants.

4. `README.md`  
   Public-facing claims and quick-start commands to keep aligned with demo output.

---

## 2) Streamlit / Demo Files

5. `ghl_real_estate_ai/streamlit_demo/app.py`  
   Main demo app path used by `make demo`.

6. `app.py`  
   Root launcher/proxy behavior for Streamlit entrypoint.

7. `Makefile`  
   Canonical local commands (`demo`, `test`, `lint`, `build`).

---

## 3) Frontend MVP Files (`enterprise-ui`)

8. `enterprise-ui/.env.example`  
   Base env surface for frontend runtime configuration.

9. `enterprise-ui/src/lib/api/client.ts`  
   Shared HTTP client behavior.

10. `enterprise-ui/src/lib/api/AgentEcosystemAPI.ts`  
    Agent status/metrics client contracts.

11. `enterprise-ui/src/lib/api/CustomerJourneyAPI.ts`  
    Journey and analytics contracts.

12. `enterprise-ui/src/lib/api/ClaudeConciergeAPI.ts`  
    Concierge insights/suggestions/chat contracts.

13. `enterprise-ui/src/lib/api/PropertyIntelligenceAPI.ts`  
    Property analysis contract.

---

## 4) Validation / Known-Blocker Files

14. `tests/test_app_structure.py`  
    Known test collection blocker observed; fix or isolate.

15. `pytest.ini`  
    Test discovery and strict settings reference.

16. `pyproject.toml`  
    Lint/type tooling config constraints.

---

## 5) Quick Start Commands

```bash
cd /Users/cave/Documents/New\ project/enterprisehub
git status --short

# Streamlit showcase checks
ruff check streamlit_cloud/app.py
python3 -m py_compile streamlit_cloud/app.py
python3 -m streamlit run streamlit_cloud/app.py --server.headless=true --server.port=8765

# Test blocker verification
pytest -q tests/test_app_structure.py
```

