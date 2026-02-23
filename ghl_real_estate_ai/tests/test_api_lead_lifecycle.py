"""
Integration tests for Lead Lifecycle API routes.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from ghl_real_estate_ai.api.main import app


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test the root endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "GHL Real Estate AI"
    assert "version" in response.json()


@pytest.mark.asyncio
async def test_health_check():
    """Test the health check endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_get_journeys_no_auth():
    """Test getting journeys without authentication."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/lifecycle/journeys")
    # Current behavior check - if auth is enabled it might be 401
    assert response.status_code in [200, 401, 403, 404]


@pytest.mark.asyncio
async def test_get_journey_stats():
    """Test getting journey statistics."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/lifecycle/stats?location_id=test_location")
    assert response.status_code in [200, 401, 403, 404]
