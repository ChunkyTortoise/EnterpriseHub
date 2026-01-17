# GHL Integration Workflow

**Skill**: GHL Integration Development
**Category**: Real Estate AI - API Integration
**Version**: 1.0.0
**Last Updated**: 2026-01-14

## Purpose

Standardize the development workflow for GoHighLevel (GHL) API integrations in the EnterpriseHub project. Ensures consistent authentication, error handling, rate limiting, and testing patterns across all GHL services.

## When to Use This Skill

Invoke this skill when:
- Adding new GHL API endpoints
- Debugging GHL API integration issues
- Implementing webhook handlers
- Creating GHL data sync services
- Testing GHL API interactions

## Prerequisites

- GHL API credentials configured in environment
- Understanding of GHL API documentation
- Base service layer knowledge

## Workflow Steps

### 1. Planning & API Discovery

**Research Phase:**
```bash
# Check GHL API documentation
# Use Context7 MCP server for latest docs
mcp query-docs --library "/gohighlevel/docs" --query "contact management API"

# Explore existing GHL integrations
grep -r "ghl_client" ghl_real_estate_ai/services/
```

**Key Questions:**
- What GHL endpoint are we integrating?
- What authentication method is required?
- What rate limits apply?
- Does this need webhooks or polling?
- What data transformations are needed?

### 2. Service Implementation Pattern

**File Structure:**
```
ghl_real_estate_ai/services/
├── ghl_[feature]_service.py      # New service
└── tests/
    └── test_ghl_[feature]_service.py  # Tests
```

**Service Template:**
```python
"""
GHL [Feature] Service
Handles [description] with GoHighLevel API
"""
from typing import Optional, Dict, Any
import httpx
from pydantic import BaseModel
from ..core.llm_client import get_ghl_client
from .cache_service import CacheService
import logging

logger = logging.getLogger(__name__)


class GHL[Feature]Request(BaseModel):
    """Request model for GHL [feature] operation"""
    location_id: str
    # Add specific fields


class GHL[Feature]Response(BaseModel):
    """Response model for GHL [feature] operation"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class GHL[Feature]Service:
    """Service for GHL [feature] operations"""

    def __init__(
        self,
        ghl_api_key: str,
        location_id: str,
        cache_service: Optional[CacheService] = None
    ):
        self.ghl_api_key = ghl_api_key
        self.location_id = location_id
        self.cache = cache_service
        self.base_url = "https://services.leadconnectorhq.com"

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to GHL API with error handling.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body for POST/PUT
            params: Query parameters

        Returns:
            Response data as dictionary

        Raises:
            httpx.HTTPError: On API errors
        """
        headers = {
            "Authorization": f"Bearer {self.ghl_api_key}",
            "Version": "2021-07-28",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=f"{self.base_url}{endpoint}",
                    headers=headers,
                    json=data,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                logger.error(f"GHL API error: {e.response.status_code} - {e.response.text}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error: {str(e)}")
                raise

    async def [operation_name](
        self,
        request: GHL[Feature]Request
    ) -> GHL[Feature]Response:
        """
        [Description of operation]

        Args:
            request: Validated request model

        Returns:
            Response with success status and data
        """
        try:
            # Check cache if applicable
            cache_key = f"ghl:[feature]:{request.location_id}"
            if self.cache:
                cached = await self.cache.get(cache_key)
                if cached:
                    return GHL[Feature]Response(success=True, data=cached)

            # Make API request
            data = await self._make_request(
                method="GET",  # or POST, PUT, DELETE
                endpoint=f"/locations/{request.location_id}/[resource]",
                params={"key": "value"}
            )

            # Cache result
            if self.cache:
                await self.cache.set(cache_key, data, ttl=300)

            return GHL[Feature]Response(success=True, data=data)

        except Exception as e:
            logger.error(f"Error in [operation_name]: {str(e)}")
            return GHL[Feature]Response(success=False, error=str(e))
```

### 3. Authentication & Configuration

**Environment Variables:**
```bash
# Required in .env (NEVER commit actual values)
GHL_API_KEY=your_api_key_here
GHL_LOCATION_ID=your_location_id
GHL_BASE_URL=https://services.leadconnectorhq.com

# Optional
GHL_RATE_LIMIT=100  # requests per minute
GHL_TIMEOUT=30  # seconds
```

**Configuration Service:**
```python
# Use existing config pattern
from ..ghl_utils.config import get_ghl_config

config = get_ghl_config()
api_key = config.ghl_api_key
location_id = config.ghl_location_id
```

### 4. Error Handling & Rate Limiting

**Rate Limiting Pattern:**
```python
import asyncio
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_requests: int = 100, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []

    async def acquire(self):
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.time_window)
        self.requests = [req for req in self.requests if req > cutoff]

        if len(self.requests) >= self.max_requests:
            sleep_time = (self.requests[0] + timedelta(seconds=self.time_window) - now).total_seconds()
            await asyncio.sleep(sleep_time)

        self.requests.append(now)
```

**Error Handling:**
```python
# Retry with exponential backoff
import tenacity

@tenacity.retry(
    wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
    stop=tenacity.stop_after_attempt(3),
    retry=tenacity.retry_if_exception_type(httpx.HTTPError)
)
async def make_ghl_request(...):
    # API call here
    pass
```

### 5. Testing Pattern

**Test File Template:**
```python
"""
Tests for GHL [Feature] Service
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from ..services.ghl_[feature]_service import GHL[Feature]Service, GHL[Feature]Request


@pytest.fixture
def mock_ghl_client():
    """Mock GHL API client"""
    client = AsyncMock()
    client.request.return_value.json.return_value = {"success": True}
    return client


@pytest.fixture
def service(mock_ghl_client):
    """Create service instance with mocked client"""
    return GHL[Feature]Service(
        ghl_api_key="test_key",
        location_id="test_location"
    )


@pytest.mark.asyncio
async def test_successful_operation(service, mock_ghl_client):
    """Test successful API operation"""
    request = GHL[Feature]Request(location_id="test_location")

    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.request = mock_ghl_client.request

        response = await service.[operation_name](request)

        assert response.success is True
        assert response.error is None
        assert response.data is not None


@pytest.mark.asyncio
async def test_api_error_handling(service):
    """Test API error handling"""
    request = GHL[Feature]Request(location_id="test_location")

    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.request.side_effect = httpx.HTTPError("API Error")

        response = await service.[operation_name](request)

        assert response.success is False
        assert "API Error" in response.error


@pytest.mark.asyncio
async def test_caching_behavior(service):
    """Test that results are cached"""
    # Test cache hit scenario
    pass


@pytest.mark.asyncio
async def test_rate_limiting(service):
    """Test rate limiting prevents exceeding limits"""
    # Test rate limiter
    pass
```

### 6. Webhook Handling (if needed)

**Webhook Handler Pattern:**
```python
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/webhooks/ghl")


class GHLWebhookPayload(BaseModel):
    """GHL webhook payload structure"""
    type: str
    location_id: str
    data: dict


@router.post("/[webhook-type]")
async def handle_ghl_webhook(
    request: Request,
    payload: GHLWebhookPayload
):
    """
    Handle GHL webhook for [event type]

    Webhook documentation: https://highlevel.stoplight.io/docs/integrations/
    """
    # Verify webhook signature
    signature = request.headers.get("X-GHL-Signature")
    if not verify_signature(signature, await request.body()):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Process webhook
    try:
        # Handle the event
        result = await process_webhook_event(payload)
        return {"success": True, "processed": True}
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return {"success": False, "error": str(e)}
```

## Quality Checklist

Before considering the integration complete:

- [ ] Service implements authentication correctly
- [ ] Rate limiting is in place
- [ ] Error handling covers all API error codes
- [ ] Retry logic implemented for transient failures
- [ ] Response data is validated with Pydantic models
- [ ] Caching implemented for expensive operations
- [ ] Unit tests cover happy path
- [ ] Unit tests cover error scenarios
- [ ] Integration test with real API (optional)
- [ ] Webhook signature verification (if webhooks used)
- [ ] Logging includes request IDs for debugging
- [ ] Documentation updated with new endpoints
- [ ] Environment variables documented in .env.example

## Common Issues & Solutions

**Issue**: 401 Unauthorized
- **Solution**: Check API key format and location ID validity

**Issue**: 429 Too Many Requests
- **Solution**: Implement or adjust rate limiter

**Issue**: Webhook signature verification fails
- **Solution**: Verify webhook secret and signature algorithm

**Issue**: Response schema mismatch
- **Solution**: Update Pydantic models to match GHL API response

## References

- [GHL API Documentation](https://highlevel.stoplight.io/docs/integrations/)
- Existing integration: `ghl_real_estate_ai/services/ghl_sync_service.py`
- Cache service: `ghl_real_estate_ai/services/cache_service.py`
- Config utilities: `ghl_real_estate_ai/ghl_utils/config.py`

## Related Skills

- `test-driven-development` - Use for TDD workflow
- `defense-in-depth` - Security validation patterns
- `systematic-debugging` - When integration issues arise
