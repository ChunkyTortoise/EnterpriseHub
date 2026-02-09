# Spec 05: Test Coverage for Core Services (P1)

**Agent**: `test-engineering`  
**Estimated scope**: ~15 new test files  
**Priority**: P1 (High)  
**Dependencies**: Spec 3 (CI fix) should be completed first

---

## Context

Audit found 76% of API routes untested (60 of 79) and only 24 of 268 test files have pytest markers. This spec adds comprehensive tests for critical services.

---

## 5a. Claude Orchestrator Tests

### Source
- **File**: `ghl_real_estate_ai/services/claude_orchestrator.py`

### Create
- **File**: `tests/unit/test_claude_orchestrator.py`

### Coverage Targets
- Multi-strategy parsing logic
- L1/L2/L3 cache flow
- Error handling and fallback behavior
- Rate limiting

### Test Structure
```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from ghl_real_estate_ai.services.claude_orchestrator import ClaudeOrchestrator

@pytest.fixture
def mock_redis():
    return MagicMock()

@pytest.fixture
def mock_ai_client():
    return AsyncMock()

@pytest.fixture
def orchestrator(mock_redis, mock_ai_client):
    return ClaudeOrchestrator(cache=mock_redis, ai_client=mock_ai_client)

class TestClaudeOrchestrator:
    @pytest.mark.unit
    async def test_l1_cache_hit(self, orchestrator, mock_redis):
        """L1 cache returns cached response without API call."""
        mock_redis.get.return_value = '{"response": "cached"}'
        result = await orchestrator.get_response("test prompt")
        assert result == {"response": "cached"}
        orchestrator.ai_client.complete.assert_not_called()

    @pytest.mark.unit
    async def test_l1_cache_miss_l2_hit(self, orchestrator):
        """L1 miss falls through to L2 cache."""
        # Test implementation

    @pytest.mark.unit
    async def test_fallback_on_api_error(self, orchestrator, mock_ai_client):
        """API error triggers fallback response."""
        mock_ai_client.complete.side_effect = Exception("API Error")
        result = await orchestrator.get_response("test prompt")
        assert "error" in result or result is not None

    @pytest.mark.unit
    async def test_rate_limiting(self, orchestrator):
        """Rate limiting prevents excessive API calls."""
        # Test implementation
```

---

## 5b. Enhanced GHL Client Tests

### Source
- **File**: `ghl_real_estate_ai/services/enhanced_ghl_client.py`

### Create
- **File**: `tests/unit/test_enhanced_ghl_client.py`

### Coverage Targets
- Contact CRUD operations
- Opportunity management
- Webhook processing
- Rate limiting
- Health check endpoint

### Test Structure
```python
import pytest
import httpx
from unittest.mock import AsyncMock, patch
from ghl_real_estate_ai.services.enhanced_ghl_client import EnhancedGHLClient

@pytest.fixture
def ghl_client():
    return EnhancedGHLClient(api_key="test-key", base_url="https://api.test")

class TestEnhancedGHLClient:
    @pytest.mark.unit
    async def test_get_contact_success(self, ghl_client):
        """Successfully retrieves contact by ID."""
        with patch.object(ghl_client, '_request') as mock_req:
            mock_req.return_value = {"id": "123", "name": "Test"}
            result = await ghl_client.get_contact("123")
            assert result["id"] == "123"

    @pytest.mark.unit
    async def test_get_contact_not_found(self, ghl_client):
        """Returns None for non-existent contact."""
        with patch.object(ghl_client, '_request') as mock_req:
            mock_req.side_effect = httpx.HTTPStatusError(
                "Not Found", request=None, response=MagicMock(status_code=404)
            )
            result = await ghl_client.get_contact("invalid")
            assert result is None

    @pytest.mark.unit
    async def test_rate_limiting_backoff(self, ghl_client):
        """Rate limit triggers exponential backoff."""
        # Test implementation

    @pytest.mark.unit
    async def test_health_check(self, ghl_client):
        """Health check returns service status."""
        # Test implementation
```

---

## 5c. Jorge Handoff Service Tests

### Source
- **File**: `ghl_real_estate_ai/services/jorge/jorge_handoff_service.py`

### Create
- **File**: `tests/unit/test_jorge_handoff_service.py`

### Coverage Targets
- Circular prevention logic
- Rate limiting (3/hr, 10/day limits)
- Confidence thresholds
- Pattern learning

### Edge Cases
- Concurrent handoffs
- Expired time windows
- Minimum data points for learning

### Test Structure
```python
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from ghl_real_estate_ai.services.jorge.jorge_handoff_service import JorgeHandoffService

@pytest.fixture
def handoff_service():
    return JorgeHandoffService()

class TestJorgeHandoffService:
    @pytest.mark.unit
    async def test_circular_prevention_blocks_repeat(self, handoff_service):
        """Prevents handoff to same agent within time window."""
        await handoff_service.record_handoff("lead-1", "agent-a")
        result = await handoff_service.can_handoff("lead-1", "agent-a")
        assert result is False

    @pytest.mark.unit
    async def test_hourly_rate_limit(self, handoff_service):
        """Blocks after 3 handoffs per hour."""
        for i in range(3):
            await handoff_service.record_handoff(f"lead-{i}", "agent-a")
        result = await handoff_service.can_handoff("lead-4", "agent-a")
        assert result is False

    @pytest.mark.unit
    async def test_daily_rate_limit(self, handoff_service):
        """Blocks after 10 handoffs per day."""
        # Test implementation

    @pytest.mark.unit
    async def test_confidence_threshold(self, handoff_service):
        """Low confidence prevents handoff."""
        result = await handoff_service.should_handoff(confidence=0.3)
        assert result is False

    @pytest.mark.unit
    async def test_expired_window_allows_retry(self, handoff_service):
        """Allows handoff after time window expires."""
        # Test implementation
```

---

## 5d. Untested API Route Tests (Top 20)

### Sources
60 untested files in `ghl_real_estate_ai/api/routes/`

### Priority Routes
1. `billing.py` - Financial operations
2. `compliance.py` - Regulatory requirements
3. `revenue_optimization.py` - Business logic
4. `enterprise_partnerships.py` - B2B integrations
5. `analytics.py` - Data endpoints

### Pattern
```python
import pytest
from httpx import AsyncClient
from fastapi import status

@pytest.fixture
async def async_client(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

class TestBillingRoutes:
    @pytest.mark.integration
    async def test_get_subscription_status(self, async_client, auth_headers):
        response = await async_client.get("/api/billing/subscription", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert "plan" in response.json()

    @pytest.mark.integration
    async def test_get_subscription_unauthorized(self, async_client):
        response = await async_client.get("/api/billing/subscription")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.integration
    async def test_update_payment_method_validation(self, async_client, auth_headers):
        response = await async_client.post(
            "/api/billing/payment-method",
            json={"invalid": "data"},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
```

---

## 5e. Add Pytest Markers to Existing Tests

### Task
Add appropriate markers to all 268 test files.

### Marker Definitions
```python
@pytest.mark.unit        # Fast, no external dependencies
@pytest.mark.integration # May need services (DB, Redis, etc.)
@pytest.mark.slow        # Heavy fixtures or network calls
@pytest.mark.security    # Security-related tests
```

### Detection Script
```bash
# Find test files without markers
for f in $(find tests -name "test_*.py"); do
    if ! grep -q "@pytest.mark" "$f"; then
        echo "$f"
    fi
done
```

### Update Strategy
1. Files with `time.sleep()` → add `@pytest.mark.slow`
2. Files with DB fixtures → add `@pytest.mark.integration`
3. Files with only pure functions → add `@pytest.mark.unit`
4. Files testing auth → add `@pytest.mark.security`

---

## Verification Commands

```bash
# Count test files
pytest tests/ --co -q | wc -l  # Should increase by ~200+

# Verify markers work
pytest tests/ -m unit -v
pytest tests/ -m integration -v

# Check coverage improvement
pytest tests/ --cov=ghl_real_estate_ai --cov-report=term-missing

# Verify new test files exist
ls -la tests/unit/test_claude_orchestrator.py
ls -la tests/unit/test_enhanced_ghl_client.py
ls -la tests/unit/test_jorge_handoff_service.py
```

---

## Acceptance Criteria

- [ ] `tests/unit/test_claude_orchestrator.py` created with 10+ tests
- [ ] `tests/unit/test_enhanced_ghl_client.py` created with 10+ tests
- [ ] `tests/unit/test_jorge_handoff_service.py` created with 10+ tests
- [ ] 20 priority route test files created
- [ ] All 268 test files have appropriate pytest markers
- [ ] `pytest tests/ -m unit` runs successfully
- [ ] Coverage increases by at least 10%

---

## Files to Create

| File | Coverage Target |
|------|-----------------|
| `tests/unit/test_claude_orchestrator.py` | AI orchestration |
| `tests/unit/test_enhanced_ghl_client.py` | GHL API client |
| `tests/unit/test_jorge_handoff_service.py` | Handoff logic |
| `tests/integration/test_billing_routes.py` | Billing API |
| `tests/integration/test_compliance_routes.py` | Compliance API |
| `tests/integration/test_analytics_routes.py` | Analytics API |
| ... (up to 15 new files) | Various routes |
