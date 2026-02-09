# Spec 02: Async/Performance Critical Fixes (P0)

**Agent**: `performance-optimizer`  
**Estimated scope**: ~8 files modified  
**Priority**: P0 (Critical)  
**Dependencies**: None

---

## Context

Performance audit identified blocking synchronous I/O in async FastAPI app, N+1 query patterns, and lazy singleton anti-patterns that cause first-request latency spikes.

---

## 2a. Replace Blocking GHL API Client

### Location
- **File**: `ghl_real_estate_ai/ghl_utils/ghl_api_client.py`

### Problem
Uses synchronous `requests` library which blocks the FastAPI event loop, causing performance degradation under load.

### Fix
Replace `requests` with `httpx.AsyncClient`:

```python
import httpx
from contextlib import asynccontextmanager

class GHLAPIClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0
            )
        return self._client

    async def get_contact(self, contact_id: str) -> dict:
        client = await self._get_client()
        response = await client.get(f"/contacts/{contact_id}")
        response.raise_for_status()
        return response.json()

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
```

### Callers to Update
Search and update all files importing from `ghl_real_estate_ai.ghl_utils.ghl_api_client`:

```bash
grep -rn "from ghl_real_estate_ai.ghl_utils.ghl_api_client import" ghl_real_estate_ai/
grep -rn "from ghl_real_estate_ai.ghl_utils import ghl_api_client" ghl_real_estate_ai/
```

### Acceptance Criteria
- Zero imports of `requests` in production code
- `httpx.AsyncClient` used everywhere
- All callers converted to `async`/`await`
- Existing tests pass

---

## 2b. Fix N+1 Query in Lead Scoring

### Location
- **File**: `ghl_real_estate_ai/api/routes/leads.py:73-95`

### Problem
Loop makes individual DB calls per contact, causing O(n) × latency performance degradation.

### Fix
Batch load contexts with single query, then score in parallel:

```python
import asyncio
from typing import List

async def batch_score_leads(contact_ids: List[str]) -> List[dict]:
    # Single batch query for all contexts
    contexts = await db.fetch_all(
        "SELECT * FROM lead_contexts WHERE contact_id = ANY($1)",
        contact_ids
    )
    context_map = {ctx["contact_id"]: ctx for ctx in contexts}
    
    # Score in parallel
    scoring_tasks = [
        score_single_lead(contact_id, context_map.get(contact_id, {}))
        for contact_id in contact_ids
    ]
    results = await asyncio.gather(*scoring_tasks, return_exceptions=True)
    
    return [
        result if not isinstance(result, Exception) else {"error": str(result)}
        for result in results
    ]
```

### Acceptance Criteria
- Single endpoint benchmark shows < 200ms for 50 contacts
- No individual DB calls inside loops for batch operations

---

## 2c. Replace Lazy Singletons with FastAPI DI

### Location
- **File**: `ghl_real_estate_ai/api/routes/leads.py:22-46` (and similar patterns)

### Problem
Global `_memory_service = None` pattern causes first-request latency and makes testing difficult.

### Current Anti-Pattern
```python
_memory_service = None

def get_memory_service():
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()  # Slow first request
    return _memory_service
```

### Fix
Use FastAPI `Depends()` with lifespan-initialized services:

```python
# In services/di_container/__init__.py (already exists)
from functools import lru_cache

@lru_cache()
def get_memory_service() -> MemoryService:
    return MemoryService()

# In routes
from ghl_real_estate_ai.services.di_container import get_memory_service

@router.get("/leads")
async def get_leads(
    memory_service: MemoryService = Depends(get_memory_service)
):
    # Use injected service
    ...
```

### Files to Update
Search for global singleton patterns:

```bash
grep -rn "global _" ghl_real_estate_ai/api/routes/ --include="*.py"
grep -rn "= None$" ghl_real_estate_ai/api/routes/ --include="*.py" | grep -v "Optional"
```

### Acceptance Criteria
- No global singleton patterns in route files
- Services initialized via DI container or lifespan
- All routes use `Depends()` for service injection

---

## 2d. Reduce Database Command Timeout

### Location
- **File**: `ghl_real_estate_ai/database/connection_manager.py:92-104`

### Problem
60s command timeout masks slow queries, making performance issues invisible.

### Fix
```python
import logging
import time

logger = logging.getLogger(__name__)

# Reduce timeout
DATABASE_CONFIG = {
    "command_timeout": 15,  # Was 60
    "pool_size": 10,
    "max_overflow": 5
}

# Add slow query logging
class SlowQueryMiddleware:
    SLOW_QUERY_THRESHOLD = 1.0  # seconds
    
    @staticmethod
    async def log_slow_query(query: str, duration: float):
        if duration > SlowQueryMiddleware.SLOW_QUERY_THRESHOLD:
            logger.warning(
                f"Slow query detected ({duration:.2f}s): {query[:200]}..."
            )
```

### Acceptance Criteria
- `command_timeout=15` in database config
- Slow query logger active for queries > 1s
- Logs properly formatted for monitoring systems

---

## Verification Commands

```bash
# Check for blocking requests library - should return 0
grep -rn "import requests" ghl_real_estate_ai/ --include="*.py" | grep -v test

# Check for global singleton pattern - should return 0
grep -rn "global _" ghl_real_estate_ai/api/routes/ --include="*.py"

# Run performance-related tests
pytest tests/ -k "leads or ghl" -v

# Full test suite
pytest tests/ -x --timeout=60
```

---

## Files to Modify

| File | Change Type |
|------|-------------|
| `ghl_real_estate_ai/ghl_utils/ghl_api_client.py` | Convert to httpx async |
| `ghl_real_estate_ai/api/routes/leads.py` | Fix N+1, add DI |
| `ghl_real_estate_ai/database/connection_manager.py` | Reduce timeout, add logging |
| `ghl_real_estate_ai/services/di_container/__init__.py` | Register services |
| Multiple route files | Replace global singletons with DI |
