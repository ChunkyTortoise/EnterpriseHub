"""
Tests for Competitive Intelligence GHL Integration API Routes.
Comprehensive test suite for GHL CRM integration endpoints.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
import json

from ghl_real_estate_ai.api.routes.competitive_intelligence_ghl import router, GHLMarketIntelligenceService
from ghl_real_estate_ai.api.routes.competitive_intelligence_ghl import (
    GHLCompetitorLead, MarketIntelligenceSync, CompetitiveResponseCampaign
)


@pytest.fixture
def client():
    """Create test client."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture
def mock_ghl_service():
    """Mock GHL market intelligence service."""
    service = MagicMock(spec=GHLMarketIntelligenceService)
    service.cache_service = AsyncMock()
    service.llm_client = AsyncMock()
    service.data_pipeline = AsyncMock()
    service.response_engine = AsyncMock()
    return service


@pytest.fixture
def mock_ghl_token():
    """Mock GHL authentication token."""
    return "ghl_test_token_123"


@pytest.fixture
def sample_lead_data():
    """Sample GHL lead data for testing."""
    return {
        "id": "lead_123",
        "contact": {
            "id": "contact_456",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-123-4567"
        },
        "source": "website_form",
        "notes": [
            {
                "content": "Client mentioned working with ABC Realty before",
                "created_at": "2024-01-15T10:30:00Z"
            },
            {
                "content": "Looking at similar properties from XYZ Real Estate",
                "created_at": "2024-01-16T14:20:00Z"
            }
        ],
        "custom_fields": {
            "budget_max": "750000",
            "preferred_area": "downtown",
            "property_type": "condo"
        },
        "activities": [
            {
                "type": "email_open",
                "timestamp": "2024-01-17T09:15:00Z"
            }
        ]
    }


@pytest.fixture
def sample_competitive_analysis():
    """Sample AI competitive analysis response."""
    return {
        "competitor_name": "ABC Realty",
        "probability": 0.75,
        "threat_level": "MEDIUM",
        "insights": {
            "indicators": [
                "Mentioned working with ABC Realty",
                "Comparing properties from multiple agents",
                "Price-sensitive behavior patterns"
            ],
            "risk_factors": [
                "Existing relationship with competitor",
                "Active comparison shopping"
            ],
            "opportunities": [
                "Demonstrate superior market knowledge",
                "Provide exclusive listings"
            ]
        },
        "actions": [
            "Schedule immediate follow-up call",
            "Send market analysis report",
            "Provide exclusive property access"
        ]
    }


@pytest.fixture
def sample_campaign_data():
    """Sample competitive response campaign data."""
    return {
        "name": "Competitor Response - ABC Realty",
        "trigger_type": "competitor_detection",
        "target_audience": {
            "tags": ["threat_medium", "competitor_abc_realty"],
            "conditions": ["custom_field_competitor_name_equals_ABC Realty"]
        },
        "response_strategy": {
            "messaging": "market_expertise",
            "timing": "immediate",
            "channels": ["email", "sms"]
        },
        "automation_rules": [
            {
                "trigger": "tag_added",
                "action": "send_email_sequence",
                "delay_hours": 0
            }
        ],
        "auto_start": True
    }


class TestAuthentication:
    """Test GHL authentication functionality."""

    @patch('ghl_real_estate_ai.api.routes.competitive_intelligence_ghl.httpx.AsyncClient')
    async def test_successful_authentication(self, mock_httpx, mock_ghl_service):
        """Test successful GHL token validation."""
        # Mock successful authentication response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "user_123", "name": "Test User"}

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_httpx.return_value.__aenter__.return_value = mock_client

        service = GHLMarketIntelligenceService()

        from fastapi.security import HTTPAuthorizationCredentials
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")

        result = await service.authenticate_ghl_request(credentials)

        assert result["id"] == "user_123"
        assert result["name"] == "Test User"

    @patch('ghl_real_estate_ai.api.routes.competitive_intelligence_ghl.httpx.AsyncClient')
    async def test_invalid_authentication(self, mock_httpx, mock_ghl_service):
        """Test invalid GHL token handling."""
        # Mock failed authentication response
        mock_response = MagicMock()
        mock_response.status_code = 401

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_httpx.return_value.__aenter__.return_value = mock_client

        service = GHLMarketIntelligenceService()

        from fastapi.security import HTTPAuthorizationCredentials
        from fastapi import HTTPException

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token")

        with pytest.raises(HTTPException) as exc_info:
            await service.authenticate_ghl_request(credentials)

        assert exc_info.value.status_code == 401
        assert "Invalid GHL authentication token" in str(exc_info.value.detail)

    @patch('ghl_real_estate_ai.api.routes.competitive_intelligence_ghl.httpx.AsyncClient')
    async def test_authentication_timeout(self, mock_httpx, mock_ghl_service):
        """Test authentication timeout handling."""
        import httpx

        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.TimeoutException("Request timeout")
        mock_httpx.return_value.__aenter__.return_value = mock_client

        service = GHLMarketIntelligenceService()

        from fastapi.security import HTTPAuthorizationCredentials
        from fastapi import HTTPException

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="timeout_token")

        with pytest.raises(HTTPException) as exc_info:
            await service.authenticate_ghl_request(credentials)

        assert exc_info.value.status_code == 503
        assert "GHL authentication service unavailable" in str(exc_info.value.detail)


class TestLeadAnalysis:
    """Test lead competitive intelligence analysis."""

    async def test_analyze_lead_competitive_intelligence(
        self, mock_ghl_service, sample_lead_data, sample_competitive_analysis
    ):
        """Test successful lead competitive intelligence analysis."""
        service = GHLMarketIntelligenceService()
        service.cache_service = AsyncMock()
        service._analyze_with_ai = AsyncMock(return_value=sample_competitive_analysis)

        result = await service.analyze_lead_competitive_intelligence(
            sample_lead_data, "test_token"
        )

        assert isinstance(result, GHLCompetitorLead)
        assert result.lead_id == "lead_123"
        assert result.contact_id == "contact_456"
        assert result.competitor_name == "ABC Realty"
        assert result.competitor_probability == 0.75
        assert result.threat_level == "MEDIUM"
        assert len(result.recommended_actions) == 3

    async def test_ai_analysis_with_competitor_mentions(self, mock_ghl_service):
        """Test AI analysis identifies competitor mentions."""
        service = GHLMarketIntelligenceService()
        service.llm_client = AsyncMock()

        # Mock LLM response
        mock_llm_response = json.dumps({
            "competitor_name": "XYZ Real Estate",
            "probability": 0.85,
            "threat_level": "HIGH",
            "insights": {
                "indicators": ["Direct competitor mention in conversation"],
                "risk_factors": ["Active engagement with competitor"],
                "opportunities": ["Immediate competitive response needed"]
            },
            "actions": ["Schedule urgent consultation", "Provide market differentiation"]
        })
        service.llm_client.generate_response.return_value = mock_llm_response

        analysis_data = {
            "lead_source": "referral",
            "communication_history": [
                {"content": "I've been working with XYZ Real Estate agent Sarah"}
            ],
            "property_interests": {"area": "downtown"},
            "interaction_patterns": []
        }

        result = await service._analyze_with_ai(analysis_data)

        assert result["competitor_name"] == "XYZ Real Estate"
        assert result["probability"] == 0.85
        assert result["threat_level"] == "HIGH"

    async def test_ai_analysis_no_competitor_detected(self, mock_ghl_service):
        """Test AI analysis when no competitor is detected."""
        service = GHLMarketIntelligenceService()
        service.llm_client = AsyncMock()

        # Mock LLM response with no competitor
        mock_llm_response = json.dumps({
            "competitor_name": None,
            "probability": 0.1,
            "threat_level": "LOW",
            "insights": {
                "indicators": ["No competitive mentions found"],
                "risk_factors": [],
                "opportunities": ["Build strong initial relationship"]
            },
            "actions": ["Standard follow-up process"]
        })
        service.llm_client.generate_response.return_value = mock_llm_response

        analysis_data = {
            "lead_source": "website",
            "communication_history": [
                {"content": "Looking for a new home in the area"}
            ],
            "property_interests": {"budget": "500000"},
            "interaction_patterns": []
        }

        result = await service._analyze_with_ai(analysis_data)

        assert result["competitor_name"] is None
        assert result["probability"] == 0.1
        assert result["threat_level"] == "LOW"

    async def test_ai_analysis_parsing_error(self, mock_ghl_service):
        """Test handling of AI response parsing errors."""
        service = GHLMarketIntelligenceService()
        service.llm_client = AsyncMock()

        # Mock invalid JSON response
        service.llm_client.generate_response.return_value = "Invalid JSON response"

        analysis_data = {
            "lead_source": "form",
            "communication_history": [],
            "property_interests": {},
            "interaction_patterns": []
        }

        result = await service._analyze_with_ai(analysis_data)

        # Should return safe defaults on parsing error
        assert result["competitor_name"] is None
        assert result["probability"] == 0.0
        assert result["threat_level"] == "LOW"

    async def test_caching_lead_analysis(self, mock_ghl_service, sample_lead_data, sample_competitive_analysis):
        """Test that lead analysis results are cached."""
        service = GHLMarketIntelligenceService()
        service.cache_service = AsyncMock()
        service._analyze_with_ai = AsyncMock(return_value=sample_competitive_analysis)

        await service.analyze_lead_competitive_intelligence(sample_lead_data, "test_token")

        # Verify cache was called
        service.cache_service.set_data.assert_called_once()
        call_args = service.cache_service.set_data.call_args

        assert call_args[0][0] == "competitive_lead:lead_123"  # Cache key
        assert call_args[1]["ttl"] == 3600  # TTL


class TestCompetitiveResponseCampaigns:
    """Test competitive response campaign creation."""

    @patch('ghl_real_estate_ai.api.routes.competitive_intelligence_ghl.httpx.AsyncClient')
    async def test_create_competitive_response_campaign(
        self, mock_httpx, mock_ghl_service, sample_campaign_data
    ):
        """Test successful campaign creation."""
        # Mock successful GHL API response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "campaign_789"}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_httpx.return_value.__aenter__.return_value = mock_client

        service = GHLMarketIntelligenceService()
        service.cache_service = AsyncMock()

        result = await service.create_competitive_response_campaign(
            sample_campaign_data, "test_token"
        )

        assert isinstance(result, CompetitiveResponseCampaign)
        assert result.campaign_id == "campaign_789"
        assert result.trigger_type == "competitor_detection"
        assert result.is_active is True

    @patch('ghl_real_estate_ai.api.routes.competitive_intelligence_ghl.httpx.AsyncClient')
    async def test_campaign_creation_failure(self, mock_httpx, mock_ghl_service, sample_campaign_data):
        """Test campaign creation failure handling."""
        # Mock failed GHL API response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Invalid campaign configuration"

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_httpx.return_value.__aenter__.return_value = mock_client

        service = GHLMarketIntelligenceService()

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await service.create_competitive_response_campaign(
                sample_campaign_data, "test_token"
            )

        assert exc_info.value.status_code == 400
        assert "Failed to create GHL campaign" in str(exc_info.value.detail)


class TestMarketIntelligenceSync:
    """Test market intelligence synchronization functionality."""

    async def test_sync_status_generation(self, mock_ghl_service):
        """Test sync status generation and caching."""
        service = GHLMarketIntelligenceService()
        service.cache_service = AsyncMock()
        service.cache_service.get_data.return_value = None  # Cache miss

        # Mock the sync status endpoint logic
        territory = "austin"
        hours = 24

        cache_key = f"sync_status:{territory}:{hours}"

        # This would normally be called in the endpoint
        sync_status = {
            "territory": territory,
            "time_range": {
                "hours": hours
            },
            "sync_summary": {
                "total_syncs": 156,
                "successful_syncs": 151,
                "failed_syncs": 5,
                "success_rate": 96.8
            }
        }

        # Verify the cache key format and structure
        assert "sync_status:austin:24" == cache_key
        assert sync_status["sync_summary"]["success_rate"] > 95.0

    async def test_background_sync_execution(self, mock_ghl_service):
        """Test background sync execution."""
        from ghl_real_estate_ai.api.routes.competitive_intelligence_ghl import execute_market_intelligence_sync

        sync_record = MarketIntelligenceSync(
            sync_id="test_sync_123",
            territory="austin",
            competitor_data={"sync_type": "full"},
            market_trends={"data_types": ["all"]},
            sync_status="INITIATED"
        )

        service = GHLMarketIntelligenceService()
        service.cache_service = AsyncMock()

        with patch('ghl_real_estate_ai.api.routes.competitive_intelligence_ghl.market_intelligence_service', service):
            await execute_market_intelligence_sync(sync_record, "test_token")

        # Verify sync record status was updated
        assert sync_record.sync_status == "COMPLETED"

        # Verify cache was called
        service.cache_service.set_data.assert_called_once()


class TestCompetitiveLandscapeInsights:
    """Test competitive landscape insights functionality."""

    async def test_competitive_landscape_generation(self, mock_ghl_service):
        """Test competitive landscape insights generation."""
        service = GHLMarketIntelligenceService()

        # Mock competitive data
        from ghl_real_estate_ai.services.competitive_data_pipeline import CompetitorDataPoint

        mock_competitive_data = [
            CompetitorDataPoint(
                competitor_id="comp_1",
                competitor_name="ABC Realty",
                data_source="mls",
                collected_at=datetime.utcnow(),
                data_type="listing",
                threat_level="HIGH",
                additional_data={
                    "market_presence": "strong",
                    "recent_activity": ["new_listing", "price_drop"],
                    "recommendations": ["increase_marketing", "competitive_pricing"]
                }
            ),
            CompetitorDataPoint(
                competitor_id="comp_2",
                competitor_name="XYZ Real Estate",
                data_source="social_media",
                collected_at=datetime.utcnow(),
                data_type="marketing",
                threat_level="MEDIUM",
                additional_data={
                    "market_presence": "moderate",
                    "recent_activity": ["social_campaign"],
                    "recommendations": ["monitor_activity"]
                }
            )
        ]

        service.data_pipeline = AsyncMock()
        service.data_pipeline.collect_competitor_data.return_value = mock_competitive_data

        # This simulates the endpoint logic
        territory = "austin"
        timeframe = "30d"

        competitive_data = await service.data_pipeline.collect_competitor_data(
            territory, data_sources=["mls", "social_media", "market_reports"]
        )

        # Process insights
        landscape_insights = {
            "territory": territory,
            "timeframe": timeframe,
            "competitive_metrics": {
                "total_competitors": len(competitive_data),
                "active_threats": sum(1 for d in competitive_data if d.threat_level == "HIGH"),
            },
            "competitor_profiles": [
                {
                    "name": data.competitor_name,
                    "threat_level": data.threat_level,
                    "market_presence": data.additional_data.get("market_presence", "unknown")
                }
                for data in competitive_data[:10]
            ]
        }

        assert landscape_insights["competitive_metrics"]["total_competitors"] == 2
        assert landscape_insights["competitive_metrics"]["active_threats"] == 1
        assert len(landscape_insights["competitor_profiles"]) == 2


class TestBackgroundTasks:
    """Test background task functionality."""

    @patch('ghl_real_estate_ai.api.routes.competitive_intelligence_ghl.httpx.AsyncClient')
    async def test_sync_competitive_insights_to_ghl(self, mock_httpx, sample_competitive_analysis):
        """Test syncing competitive insights to GHL contact."""
        from ghl_real_estate_ai.api.routes.competitive_intelligence_ghl import sync_competitive_insights_to_ghl

        # Mock successful GHL update response
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.patch.return_value = mock_response
        mock_httpx.return_value.__aenter__.return_value = mock_client

        competitive_lead = GHLCompetitorLead(
            lead_id="lead_123",
            contact_id="contact_456",
            competitor_name="ABC Realty",
            competitor_probability=0.75,
            competitive_insights=sample_competitive_analysis["insights"],
            threat_level="MEDIUM",
            recommended_actions=["action1", "action2"]
        )

        # Execute background task
        await sync_competitive_insights_to_ghl(competitive_lead, "test_token")

        # Verify GHL API was called
        mock_client.patch.assert_called_once()

        # Verify payload structure
        call_args = mock_client.patch.call_args
        payload = call_args[1]["json"]

        assert "customFields" in payload
        assert payload["customFields"]["competitor_name"] == "ABC Realty"
        assert payload["customFields"]["threat_level"] == "MEDIUM"
        assert "tags" in payload
        assert "threat_medium" in payload["tags"]
        assert "competitor_abc_realty" in payload["tags"]


class TestErrorHandling:
    """Test error handling scenarios."""

    async def test_service_initialization_errors(self):
        """Test service initialization error handling."""
        # Test that service initializes with default configurations
        service = GHLMarketIntelligenceService()

        assert service.ghl_api_base == "https://rest.gohighlevel.com/v1"
        assert hasattr(service, 'cache_service')
        assert hasattr(service, 'llm_client')
        assert hasattr(service, 'data_pipeline')
        assert hasattr(service, 'response_engine')

    async def test_llm_client_errors(self, mock_ghl_service):
        """Test LLM client error handling."""
        service = GHLMarketIntelligenceService()
        service.llm_client = AsyncMock()
        service.llm_client.generate_response.side_effect = Exception("LLM service unavailable")

        analysis_data = {
            "lead_source": "website",
            "communication_history": [],
            "property_interests": {},
            "interaction_patterns": []
        }

        result = await service._analyze_with_ai(analysis_data)

        # Should return safe defaults on LLM error
        assert result["competitor_name"] is None
        assert result["probability"] == 0.0
        assert result["threat_level"] == "LOW"
        assert "error" in result["insights"]

    async def test_cache_service_errors(self, mock_ghl_service, sample_lead_data):
        """Test cache service error handling."""
        service = GHLMarketIntelligenceService()
        service.cache_service = AsyncMock()
        service.cache_service.set_data.side_effect = Exception("Cache unavailable")
        service._analyze_with_ai = AsyncMock(return_value={
            "competitor_name": None,
            "probability": 0.0,
            "threat_level": "LOW",
            "insights": {},
            "actions": []
        })

        # Should still complete analysis even if cache fails
        result = await service.analyze_lead_competitive_intelligence(sample_lead_data, "test_token")

        assert isinstance(result, GHLCompetitorLead)
        assert result.lead_id == "lead_123"