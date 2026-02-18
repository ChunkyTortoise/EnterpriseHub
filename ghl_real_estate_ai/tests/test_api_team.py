"""
Integration tests for Team API routes.
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from ghl_real_estate_ai.api.main import app



@pytest.fixture(autouse=True)
def mock_rate_limiter():
    """Mock rate limiter to always allow requests."""
    with patch("ghl_real_estate_ai.api.middleware.rate_limiter.RateLimiter.is_allowed", new_callable=AsyncMock) as mock:
        mock.return_value = True
        yield mock


async def test_add_and_list_agents():
    """Test adding and listing agents."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Add agent
        agent_data = {
            "id": "agent_test_1",
            "name": "Test Agent",
            "email": "test@example.com",
            "role": "agent",
            "specialties": ["miami"],
        }
        response = await ac.post("/api/team/test_location/agents", json=agent_data)
        assert response.status_code == 200
        assert response.json()["agent_id"] == "agent_test_1"

        # List agents
        response = await ac.get("/api/team/test_location/agents")
        assert response.status_code == 200
        agents = response.json()
        assert any(a["id"] == "agent_test_1" for a in agents)


async def test_get_leaderboard():
    """Test getting team leaderboard."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/team/test_location/leaderboard")
        assert response.status_code == 200
        # Leaderboard might be empty but should return 200
        assert isinstance(response.json(), list)


async def test_assign_lead():
    """Test lead assignment."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # First ensure there's an agent
        agent_data = {"id": "agent_test_2", "name": "Test Agent 2", "email": "test2@example.com"}
        await ac.post("/api/team/test_location/agents", json=agent_data)

        # Assign lead
        response = await ac.post("/api/team/test_location/assign?contact_id=contact_123")
        assert response.status_code == 200
        assert response.json()["contact_id"] == "contact_123"
        assert "assigned_to" in response.json()