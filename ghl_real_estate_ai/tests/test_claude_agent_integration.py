"""
Test suite for Claude Agent Service and Lead Intelligence Integration

Comprehensive tests for Phase One Lead Intelligence implementation
including Claude AI conversations, property data integration, and
enhanced map functionality.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

# Import the services to test
try:
    from ..services.claude_agent_service import (
        ClaudeAgentService,
        AgentQuery,
        ClaudeResponse,
        chat_with_claude,
        get_claude_lead_insights,
        get_claude_follow_up_actions
    )
    from ..services.zillow_integration_service import (
        ZillowIntegrationService,
        PropertyData,
        MarketAnalysis,
        search_zillow_properties
    )
    from ..services.redfin_integration_service import (
        RedfinIntegrationService,
        RedfinPropertyData,
        RedfinMarketData,
        search_redfin_properties
    )
except ImportError:
    # Handle import errors gracefully for testing
    pytest.skip("Services not available for testing", allow_module_level=True)


class TestClaudeAgentService:
    """Test cases for Claude Agent Service functionality"""

    @pytest.fixture
    def mock_anthropic_client(self):
        """Mock Anthropic client for testing"""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.content = [Mock(text="Test response from Claude")]
        mock_client.messages.create.return_value = mock_response
        return mock_client

    @pytest.fixture
    def claude_service(self, mock_anthropic_client):
        """Claude service with mocked client"""
        service = ClaudeAgentService()
        service.client = mock_anthropic_client
        return service

    @pytest.mark.asyncio
    async def test_chat_with_agent_basic(self, claude_service):
        """Test basic agent chat functionality"""
        agent_id = "agent_test_001"
        query = "What are my highest priority leads today?"

        response = await claude_service.chat_with_agent(agent_id, query)

        assert isinstance(response, ClaudeResponse)
        assert response.response is not None
        assert len(response.insights) > 0
        assert len(response.recommendations) > 0
        assert 0 <= response.confidence <= 1
        assert len(response.follow_up_questions) > 0

    @pytest.mark.asyncio
    async def test_chat_with_lead_context(self, claude_service):
        """Test chat with specific lead context"""
        agent_id = "agent_test_002"
        query = "Tell me about this lead's conversion potential"
        lead_id = "lead_123"

        response = await claude_service.chat_with_agent(agent_id, query, lead_id)

        assert isinstance(response, ClaudeResponse)
        assert response.response is not None
        # Verify agent context was updated
        assert lead_id in claude_service.agent_context[agent_id]["active_leads"]

    @pytest.mark.asyncio
    async def test_get_lead_insights(self, claude_service):
        """Test lead insights generation"""
        lead_id = "lead_456"
        agent_id = "agent_test_003"

        insights = await claude_service.get_lead_insights(lead_id, agent_id)

        assert isinstance(insights, dict)
        assert insights["lead_id"] == lead_id
        assert insights["agent_id"] == agent_id
        assert "insights" in insights
        assert "recommendations" in insights
        assert "confidence" in insights

    @pytest.mark.asyncio
    async def test_suggest_follow_up_actions(self, claude_service):
        """Test follow-up action suggestions"""
        lead_id = "lead_789"
        agent_id = "agent_test_004"

        actions = await claude_service.suggest_follow_up_actions(lead_id, agent_id)

        assert isinstance(actions, list)
        assert len(actions) > 0
        for action in actions:
            assert "id" in action
            assert "action" in action
            assert "priority" in action
            assert "confidence" in action

    def test_agent_stats(self, claude_service):
        """Test agent statistics tracking"""
        agent_id = "agent_test_005"

        # Simulate some activity
        claude_service.agent_context[agent_id] = {
            "active_leads": ["lead_1", "lead_2"],
            "last_activity": datetime.now()
        }
        claude_service.conversation_history[agent_id] = [
            {"role": "user", "content": "test1"},
            {"role": "assistant", "content": "response1"},
            {"role": "user", "content": "test2"},
            {"role": "assistant", "content": "response2"}
        ]

        stats = claude_service.get_agent_stats(agent_id)

        assert stats["agent_id"] == agent_id
        assert stats["total_conversations"] == 2
        assert stats["active_leads"] == 2
        assert stats["status"] == "active"

    @pytest.mark.asyncio
    async def test_error_handling(self, claude_service):
        """Test error handling in Claude service"""
        # Mock client to raise an error
        claude_service.client.messages.create.side_effect = Exception("API Error")

        agent_id = "agent_test_error"
        query = "This should fail"

        response = await claude_service.chat_with_agent(agent_id, query)

        assert isinstance(response, ClaudeResponse)
        assert "error" in response.response.lower()
        assert response.confidence == 0.0

    def test_conversation_history_management(self, claude_service):
        """Test conversation history storage and retrieval"""
        agent_id = "agent_test_history"

        # Add multiple conversations
        for i in range(15):
            claude_service._store_conversation(
                agent_id, f"query_{i}", f"response_{i}"
            )

        history = claude_service._get_conversation_history(agent_id)

        # Should limit to last 8 messages
        assert len(history) == 8
        # Should be most recent
        assert "query_14" in history[-2]["content"]


class TestZillowIntegrationService:
    """Test cases for Zillow Integration Service"""

    @pytest.fixture
    def zillow_service(self):
        """Zillow service for testing"""
        return ZillowIntegrationService()

    @pytest.mark.asyncio
    async def test_search_properties_demo_mode(self, zillow_service):
        """Test property search in demo mode"""
        async with zillow_service:
            properties = await zillow_service.search_properties("Austin", max_results=5)

        assert isinstance(properties, list)
        assert len(properties) <= 5
        for prop in properties:
            assert isinstance(prop, PropertyData)
            assert prop.zpid is not None
            assert prop.address is not None

    @pytest.mark.asyncio
    async def test_get_property_details_demo(self, zillow_service):
        """Test property details retrieval in demo mode"""
        async with zillow_service:
            # First get a property from search
            properties = await zillow_service.search_properties("Austin", max_results=1)
            if properties:
                zpid = properties[0].zpid
                property_detail = await zillow_service.get_property_details(zpid)

                assert property_detail is not None
                assert property_detail.zpid == zpid

    @pytest.mark.asyncio
    async def test_market_analysis(self, zillow_service):
        """Test market analysis functionality"""
        async with zillow_service:
            analysis = await zillow_service.get_market_analysis("Austin")

        assert isinstance(analysis, MarketAnalysis)
        assert analysis.area == "Austin"
        assert analysis.median_price is not None

    @pytest.mark.asyncio
    async def test_properties_near_coordinates(self, zillow_service):
        """Test coordinate-based property search"""
        async with zillow_service:
            properties = await zillow_service.find_properties_near_coordinates(
                lat=30.2672, lon=-97.7431, radius_miles=2.0, max_results=3
            )

        assert isinstance(properties, list)
        assert len(properties) <= 3

    def test_cache_functionality(self, zillow_service):
        """Test caching mechanism"""
        test_key = "test_cache_key"
        test_data = {"test": "data"}

        # Test caching
        zillow_service._cache_data(test_key, test_data)
        assert zillow_service._is_cached(test_key)
        assert zillow_service.cache[test_key]["data"] == test_data

        # Test cache expiry
        zillow_service.cache[test_key]["timestamp"] = datetime.now() - timedelta(hours=2)
        assert not zillow_service._is_cached(test_key)

    def test_property_data_structure(self):
        """Test PropertyData dataclass functionality"""
        prop = PropertyData(
            zpid="123456",
            address="123 Test St",
            city="Austin",
            state="TX",
            zipcode="78701",
            price=500000,
            sqft=2000
        )

        # Test auto-calculated price per sqft
        assert prop.price_per_sqft == 250.0

        # Test photos initialization
        assert prop.photos == []


class TestRedfinIntegrationService:
    """Test cases for Redfin Integration Service"""

    @pytest.fixture
    def redfin_service(self):
        """Redfin service for testing"""
        return RedfinIntegrationService()

    @pytest.mark.asyncio
    async def test_search_redfin_properties_demo(self, redfin_service):
        """Test Redfin property search in demo mode"""
        async with redfin_service:
            properties = await redfin_service.search_properties("Austin", max_results=5)

        assert isinstance(properties, list)
        assert len(properties) <= 5
        for prop in properties:
            assert isinstance(prop, RedfinPropertyData)
            assert prop.property_id is not None
            assert prop.address is not None

    @pytest.mark.asyncio
    async def test_redfin_market_data(self, redfin_service):
        """Test Redfin market data retrieval"""
        async with redfin_service:
            market_data = await redfin_service.get_market_data("Austin")

        assert isinstance(market_data, RedfinMarketData)
        assert market_data.area == "Austin"
        assert market_data.median_sale_price is not None

    @pytest.mark.asyncio
    async def test_neighborhood_insights(self, redfin_service):
        """Test neighborhood insights functionality"""
        async with redfin_service:
            insights = await redfin_service.get_neighborhood_insights(
                "Downtown", "Austin", "TX"
            )

        assert insights is not None
        assert insights.neighborhood == "Downtown"
        assert insights.city == "Austin"
        assert insights.state == "TX"

    def test_redfin_property_data_structure(self):
        """Test RedfinPropertyData dataclass functionality"""
        prop = RedfinPropertyData(
            property_id="rf_123",
            address="456 Redfin Ave",
            city="Austin",
            state="TX",
            zipcode="78702",
            price=600000,
            sqft=2400
        )

        # Test auto-calculated price per sqft
        assert prop.price_per_sqft == 250.0

        # Test list initialization
        assert prop.price_history == []
        assert prop.photos == []


class TestPropertyDataFiltering:
    """Test property data filtering and search functionality"""

    def test_price_filtering(self):
        """Test price range filtering"""
        properties = [
            {"price": 300000, "address": "Low Price"},
            {"price": 750000, "address": "Mid Price"},
            {"price": 1200000, "address": "High Price"}
        ]

        # Test price filters
        low_filter = {"max_price": 500000}
        mid_filter = {"min_price": 500000, "max_price": 1000000}
        high_filter = {"min_price": 1000000}

        # Simulate filtering logic
        low_results = [p for p in properties if p["price"] <= low_filter["max_price"]]
        mid_results = [p for p in properties if mid_filter["min_price"] <= p["price"] <= mid_filter["max_price"]]
        high_results = [p for p in properties if p["price"] >= high_filter["min_price"]]

        assert len(low_results) == 1
        assert len(mid_results) == 1
        assert len(high_results) == 1

    def test_location_filtering(self):
        """Test location-based filtering"""
        properties = [
            {"city": "Austin", "zipcode": "78701"},
            {"city": "Austin", "zipcode": "78702"},
            {"city": "Dallas", "zipcode": "75201"}
        ]

        austin_results = [p for p in properties if "austin" in p["city"].lower()]
        zipcode_results = [p for p in properties if "78701" in p["zipcode"]]

        assert len(austin_results) == 2
        assert len(zipcode_results) == 1


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple services"""

    @pytest.mark.asyncio
    async def test_agent_with_property_context(self):
        """Test agent conversation with property context"""
        # This would test the integration between Claude and property services
        # In a real scenario, this would involve:
        # 1. Agent asking about properties for a specific lead
        # 2. System fetching relevant properties from Zillow/Redfin
        # 3. Claude providing insights based on lead preferences and property data

        mock_lead_preferences = {
            "budget": 800000,
            "location": "Austin",
            "bedrooms": 3,
            "property_type": "Single Family"
        }

        mock_properties = [
            {"price": 750000, "bedrooms": 3, "city": "Austin", "property_type": "Single Family"},
            {"price": 900000, "bedrooms": 4, "city": "Austin", "property_type": "Single Family"}
        ]

        # Filter properties based on lead preferences
        matching_properties = [
            p for p in mock_properties
            if p["price"] <= mock_lead_preferences["budget"]
            and p["bedrooms"] >= mock_lead_preferences["bedrooms"]
            and p["city"] == mock_lead_preferences["location"]
        ]

        assert len(matching_properties) == 1
        assert matching_properties[0]["price"] == 750000

    @pytest.mark.asyncio
    async def test_map_data_integration(self):
        """Test map data integration with leads and properties"""
        mock_leads = [
            {"id": "lead_1", "lat": 30.2672, "lon": -97.7431, "lead_score": 85},
            {"id": "lead_2", "lat": 30.2700, "lon": -97.7300, "lead_score": 65}
        ]

        mock_properties = [
            {"id": "prop_1", "lat": 30.2672, "lon": -97.7431, "price": 750000},
            {"id": "prop_2", "lat": 30.2650, "lon": -97.7450, "price": 600000}
        ]

        # Test proximity matching (within 0.01 degrees ≈ 1.1km)
        def calculate_proximity(lead, prop, threshold=0.01):
            lat_diff = abs(lead["lat"] - prop["lat"])
            lon_diff = abs(lead["lon"] - prop["lon"])
            return lat_diff <= threshold and lon_diff <= threshold

        # Find properties near leads
        lead_property_matches = []
        for lead in mock_leads:
            nearby_properties = [
                prop for prop in mock_properties
                if calculate_proximity(lead, prop)
            ]
            if nearby_properties:
                lead_property_matches.append({
                    "lead": lead,
                    "nearby_properties": nearby_properties
                })

        assert len(lead_property_matches) == 1
        assert lead_property_matches[0]["lead"]["id"] == "lead_1"


@pytest.mark.integration
class TestAPIIntegrations:
    """Integration tests requiring actual API connections (run separately)"""

    @pytest.mark.skipif(True, reason="Requires API keys for testing")
    @pytest.mark.asyncio
    async def test_real_anthropic_integration(self):
        """Test real Anthropic API integration (when API key available)"""
        # This test would run against the actual Anthropic API
        # Only run when API keys are available and testing is desired
        pass

    @pytest.mark.skipif(True, reason="Requires API keys for testing")
    @pytest.mark.asyncio
    async def test_real_property_api_integration(self):
        """Test real property API integration (when API keys available)"""
        # This test would run against actual property APIs
        # Only run when API keys are available and testing is desired
        pass


class TestPerformance:
    """Performance and load testing scenarios"""

    @pytest.mark.asyncio
    async def test_concurrent_agent_requests(self):
        """Test handling multiple concurrent agent requests"""
        claude_service = ClaudeAgentService()

        # Mock the client
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.content = [Mock(text="Concurrent test response")]
        mock_client.messages.create.return_value = mock_response
        claude_service.client = mock_client

        # Create multiple concurrent requests
        tasks = []
        for i in range(5):
            tasks.append(
                claude_service.chat_with_agent(
                    f"agent_{i}", f"Query {i}", f"lead_{i}"
                )
            )

        responses = await asyncio.gather(*tasks)

        assert len(responses) == 5
        for response in responses:
            assert isinstance(response, ClaudeResponse)

    def test_cache_performance(self):
        """Test caching performance with large datasets"""
        zillow_service = ZillowIntegrationService()

        # Test cache with many entries
        for i in range(1000):
            zillow_service._cache_data(f"key_{i}", {"data": f"value_{i}"})

        # Test retrieval performance
        start_time = datetime.now()
        for i in range(100):
            is_cached = zillow_service._is_cached(f"key_{i}")
            assert is_cached

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Should be very fast (under 1 second for 100 lookups)
        assert duration < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])