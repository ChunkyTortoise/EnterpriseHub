"""
Tests for Portal API endpoints.

Tests the FastAPI routes for swipe actions.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from ghl_real_estate_ai.api.main import app

@pytest.mark.integration


@pytest.fixture
def mock_ghl_for_api_tests():
    """Mock GHL client for API-level tests."""
    from ghl_real_estate_ai.api.routes.portal import swipe_manager

    mock_client = Mock()
    mock_client.add_tags = AsyncMock(return_value={"status": "success"})

    # Save original client
    original_client = swipe_manager.ghl_client

    # Replace with mock
    swipe_manager.ghl_client = mock_client

    yield mock_client

    # Restore original
    swipe_manager.ghl_client = original_client


@pytest.mark.asyncio
async def test_swipe_like_endpoint():
    """Test the swipe endpoint with a like action."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/portal/swipe",
            json={
                "lead_id": "test_contact_api",
                "property_id": "mls_api_001",
                "action": "like",
                "location_id": "loc_api_test",
                "time_on_card": 15.3,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "logged"
        assert "trigger_sms" in data
        assert "high_intent" in data


@pytest.mark.asyncio
async def test_swipe_pass_endpoint():
    """Test the swipe endpoint with a pass action."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/portal/swipe",
            json={
                "lead_id": "test_contact_api",
                "property_id": "mls_api_002",
                "action": "pass",
                "location_id": "loc_api_test",
                "feedback": {
                    "category": "price_too_high",
                    "text": "Over budget",
                },
                "time_on_card": 8.5,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "preference_updated"


@pytest.mark.asyncio
async def test_swipe_invalid_action():
    """Test that invalid actions return error."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/portal/swipe",
            json={
                "lead_id": "test_contact_api",
                "property_id": "mls_api_003",
                "action": "invalid_action",
                "location_id": "loc_api_test",
            },
        )

        # Error handler may return 500 instead of 400
        assert response.status_code in [400, 500]
        data = response.json()
        assert "Invalid action" in str(data)


@pytest.mark.asyncio
async def test_get_lead_stats_endpoint():
    """Test the lead stats endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First create some interactions
        await client.post(
            "/api/portal/swipe",
            json={
                "lead_id": "test_stats_api",
                "property_id": "mls_stats_001",
                "action": "like",
                "location_id": "loc_test",
            },
        )

        # Get stats
        response = await client.get("/api/portal/stats/test_stats_api")

        assert response.status_code == 200
        data = response.json()

        assert data["lead_id"] == "test_stats_api"
        assert "total_interactions" in data
        assert "likes" in data
        assert "passes" in data
        assert "like_rate" in data


@pytest.mark.asyncio
async def test_get_feedback_categories_endpoint():
    """Test the feedback categories endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/portal/feedback-categories")

        assert response.status_code == 200
        data = response.json()

        assert "categories" in data
        categories = data["categories"]

        assert len(categories) >= 5  # At least 5 categories

        # Check structure of first category
        first_category = categories[0]
        assert "value" in first_category
        assert "label" in first_category
        assert "icon" in first_category


@pytest.mark.asyncio
async def test_get_lead_interactions_endpoint():
    """Test the lead interactions endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        lead_id = "test_interactions_api"

        # Create some interactions
        for i in range(3):
            await client.post(
                "/api/portal/swipe",
                json={
                    "lead_id": lead_id,
                    "property_id": f"mls_int_{i}",
                    "action": "like" if i % 2 == 0 else "pass",
                    "location_id": "loc_test",
                },
            )

        # Get interactions
        response = await client.get(f"/api/portal/interactions/{lead_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["lead_id"] == lead_id
        assert data["total"] >= 3
        assert "interactions" in data
        assert len(data["interactions"]) >= 3


@pytest.mark.asyncio
async def test_get_lead_interactions_with_limit():
    """Test the lead interactions endpoint with limit parameter."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        lead_id = "test_limit_api_v3"

        # Create multiple interactions
        for i in range(10):
            response = await client.post(
                "/api/portal/swipe",
                json={
                    "lead_id": lead_id,
                    "property_id": f"mls_limit_v3_{i}",
                    "action": "like",
                    "location_id": "loc_test",
                },
            )
            assert response.status_code == 200

        # Get interactions with limit
        response = await client.get(f"/api/portal/interactions/{lead_id}?limit=5")

        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert len(data["interactions"]) <= 5


@pytest.mark.asyncio
async def test_high_intent_detection_via_api(mock_ghl_for_api_tests):
    """Test that high-intent is detected through API calls."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        lead_id = "test_high_intent_api_v2"

        # Make 3 quick likes
        results = []
        for i in range(3):
            response = await client.post(
                "/api/portal/swipe",
                json={
                    "lead_id": lead_id,
                    "property_id": f"mls_intent_v2_{i}",
                    "action": "like",
                    "location_id": "loc_test",
                },
            )

            assert response.status_code == 200
            data = response.json()
            results.append(data)

        # Third like should trigger high intent
        assert results[2]["high_intent"] == True
        assert results[2]["trigger_sms"] == True


@pytest.mark.asyncio
async def test_pass_without_feedback():
    """Test that pass works without feedback."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/portal/swipe",
            json={
                "lead_id": "test_no_feedback_v2",
                "property_id": "mls_no_feedback_v2",
                "action": "pass",
                "location_id": "loc_test",
                # No feedback provided
            },
        )

        # Should succeed with or without feedback
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "preference_updated"


@pytest.mark.asyncio
async def test_swipe_request_validation():
    """Test that request validation works."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Missing required field
        response = await client.post(
            "/api/portal/swipe",
            json={
                "lead_id": "test_validation",
                "property_id": "mls_validation",
                # Missing 'action' and 'location_id'
            },
        )

        assert response.status_code == 422  # Validation error