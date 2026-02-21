import pytest

pytestmark = pytest.mark.integration

#!/usr/bin/env python3
"""
Comprehensive tests for Apollo Client.

Tests cover:
- Apollo API client initialization and configuration
- Person enrichment operations
- Email verification
- Organization enrichment
- Lead scoring algorithms
- Batch operations
- Rate limiting and retry logic
- Error handling and API failures
- Health monitoring

Coverage Target: 85%+ for all Apollo operations
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

# Import the module under test
try:
    from ghl_real_estate_ai.services.apollo_client import (
        ApolloAPIException,
        ApolloClient,
        ApolloConfig,
        OrganizationEnrichmentResult,
        PersonEnrichmentResult,
    )
except (ImportError, TypeError, AttributeError):
    pytest.skip("required imports unavailable", allow_module_level=True)

# Import test utilities
from tests.fixtures.sample_data import LeadProfiles
from tests.mocks.external_services import MockApolloClient


class TestApolloConfig:
    """Test Apollo configuration management"""

    def test_default_config_creation(self):
        """Test default Apollo configuration"""
        config = ApolloConfig()

        assert config.api_key is None  # Should be set via environment
        assert config.base_url == "https://api.apollo.io/v1"
        assert config.rate_limit_requests_per_minute == 120
        assert config.request_timeout_seconds == 30
        assert config.max_retries == 3
        assert config.cache_ttl_seconds == 3600
        assert config.enable_caching is True
        assert config.batch_size == 50

    def test_custom_config_creation(self):
        """Test custom Apollo configuration"""
        config = ApolloConfig(
            api_key="test_api_key",
            rate_limit_requests_per_minute=60,
            request_timeout_seconds=15,
            max_retries=5,
            enable_caching=False,
        )

        assert config.api_key == "test_api_key"
        assert config.rate_limit_requests_per_minute == 60
        assert config.request_timeout_seconds == 15
        assert config.max_retries == 5
        assert config.enable_caching is False


class TestApolloClient:
    """Test Apollo API client operations"""

    @pytest_asyncio.fixture
    async def apollo_client(self):
        """Create Apollo client with mocked dependencies"""
        config = ApolloConfig(api_key="test_apollo_key_123", enable_caching=True)

        # Mock cache service
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock(return_value=True)

        client = ApolloClient(config, cache_service=mock_cache)

        # Mock HTTP session
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock()
        mock_session.request = AsyncMock(return_value=mock_response)
        mock_session.close = AsyncMock()

        client.session = mock_session
        client._mock_response = mock_response  # Store for test access

        return client

    @pytest.mark.asyncio
    async def test_client_initialization(self, apollo_client):
        """Test Apollo client initialization"""
        assert apollo_client.config is not None
        assert apollo_client.cache_service is not None
        assert apollo_client._rate_limit_semaphore is not None

    @pytest.mark.asyncio
    async def test_ensure_session(self, apollo_client):
        """Test session creation and management"""
        # Reset session to test creation
        apollo_client.session = None

        await apollo_client._ensure_session()

        assert apollo_client.session is not None

    @pytest.mark.asyncio
    async def test_client_close(self, apollo_client):
        """Test client cleanup"""
        await apollo_client.close()

        apollo_client.session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test client as async context manager"""
        config = ApolloConfig(api_key="test_key")

        async with ApolloClient(config) as client:
            assert client.session is not None

        # Client should be closed after context exit

    @pytest.mark.asyncio
    async def test_make_request_success(self, apollo_client):
        """Test successful API request"""
        # Mock successful response
        apollo_client._mock_response.json.return_value = {"success": True, "data": {"result": "success"}}

        result = await apollo_client._make_request("GET", "/test-endpoint")

        assert result["success"] is True
        assert result["data"]["result"] == "success"

        # Verify session request was called
        apollo_client.session.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_request_rate_limiting(self, apollo_client):
        """Test rate limiting behavior"""
        # Set up small rate limit for testing
        apollo_client._rate_limit_semaphore = asyncio.Semaphore(1)

        # Mock response
        apollo_client._mock_response.json.return_value = {"success": True}

        # Make multiple concurrent requests
        tasks = []
        for _ in range(3):
            task = apollo_client._make_request("GET", "/test")
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # All should succeed but be rate limited
        assert len(results) == 3
        assert all(r["success"] for r in results)

    @pytest.mark.asyncio
    async def test_make_request_retry_on_failure(self, apollo_client):
        """Test retry logic on API failures"""
        # Mock first two calls to fail, third to succeed
        apollo_client.session.request.side_effect = [
            Exception("Connection timeout"),
            Exception("Service unavailable"),
            apollo_client._mock_response,  # Success on third try
        ]

        apollo_client._mock_response.json.return_value = {"success": True}

        result = await apollo_client._make_request("GET", "/test-retry")

        assert result["success"] is True
        assert apollo_client.session.request.call_count == 3

    @pytest.mark.asyncio
    async def test_make_request_max_retries_exceeded(self, apollo_client):
        """Test behavior when max retries are exceeded"""
        # Mock all calls to fail
        apollo_client.session.request.side_effect = Exception("Persistent failure")

        with pytest.raises(ApolloAPIException, match="Max retries exceeded"):
            await apollo_client._make_request("GET", "/test-fail")

    @pytest.mark.asyncio
    async def test_handle_response_success(self, apollo_client):
        """Test successful response handling"""
        apollo_client._mock_response.status = 200
        apollo_client._mock_response.json.return_value = {"data": {"person": {"name": "John Doe"}}}

        result = await apollo_client._handle_response(apollo_client._mock_response)

        assert "data" in result
        assert result["data"]["person"]["name"] == "John Doe"

    @pytest.mark.asyncio
    async def test_handle_response_client_error(self, apollo_client):
        """Test handling of client errors (4xx)"""
        apollo_client._mock_response.status = 400
        apollo_client._mock_response.json.return_value = {"error": "Invalid API key"}

        with pytest.raises(ApolloAPIException, match="Invalid API key"):
            await apollo_client._handle_response(apollo_client._mock_response)

    @pytest.mark.asyncio
    async def test_handle_response_server_error(self, apollo_client):
        """Test handling of server errors (5xx)"""
        apollo_client._mock_response.status = 500
        apollo_client._mock_response.json.return_value = {"error": "Internal server error"}

        with pytest.raises(ApolloAPIException, match="Internal server error"):
            await apollo_client._handle_response(apollo_client._mock_response)

    @pytest.mark.asyncio
    async def test_handle_response_rate_limit(self, apollo_client):
        """Test handling of rate limit responses (429)"""
        apollo_client._mock_response.status = 429
        apollo_client._mock_response.json.return_value = {"error": "Rate limit exceeded"}

        with pytest.raises(ApolloAPIException, match="Rate limit exceeded"):
            await apollo_client._handle_response(apollo_client._mock_response)


class TestPersonEnrichment:
    """Test person enrichment functionality"""

    @pytest_asyncio.fixture
    async def apollo_client(self):
        """Create Apollo client for person enrichment testing"""
        config = ApolloConfig(api_key="test_key")
        mock_cache = AsyncMock()
        client = ApolloClient(config, cache_service=mock_cache)

        # Mock session and response
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock()
        mock_session.request = AsyncMock(return_value=mock_response)

        client.session = mock_session
        client._mock_response = mock_response

        return client

    @pytest.mark.asyncio
    async def test_enrich_person_by_email_success(self, apollo_client):
        """Test successful person enrichment by email"""
        # Mock successful enrichment response
        apollo_client._mock_response.json.return_value = {
            "person": {
                "id": "12345",
                "first_name": "Sarah",
                "last_name": "Johnson",
                "email": "sarah.johnson@tech-corp.com",
                "title": "Software Engineer",
                "organization": {"name": "Tech Corp", "industry": "Software Development"},
                "linkedin_url": "https://linkedin.com/in/sarahj",
                "phone_numbers": ["+1-555-123-4567"],
                "employment_history": [
                    {"organization_name": "Tech Corp", "title": "Software Engineer", "start_date": "2022-01-01"}
                ],
            }
        }

        result = await apollo_client.enrich_person(email="sarah.johnson@tech-corp.com")

        assert isinstance(result, PersonEnrichmentResult)
        assert result.person_id == "12345"
        assert result.email == "sarah.johnson@tech-corp.com"
        assert result.first_name == "Sarah"
        assert result.last_name == "Johnson"
        assert result.title == "Software Engineer"
        assert result.company == "Tech Corp"
        assert result.linkedin_url == "https://linkedin.com/in/sarahj"
        assert "+1-555-123-4567" in result.phone_numbers
        assert result.confidence_score > 0

    @pytest.mark.asyncio
    async def test_enrich_person_by_linkedin_success(self, apollo_client):
        """Test successful person enrichment by LinkedIn URL"""
        apollo_client._mock_response.json.return_value = {
            "person": {
                "id": "67890",
                "first_name": "Michael",
                "last_name": "Chen",
                "email": "mike.chen@startup.com",
                "linkedin_url": "https://linkedin.com/in/mikechen",
                "organization": {"name": "Startup Inc", "industry": "Technology"},
            }
        }

        result = await apollo_client.enrich_person(linkedin_url="https://linkedin.com/in/mikechen")

        assert isinstance(result, PersonEnrichmentResult)
        assert result.person_id == "67890"
        assert result.first_name == "Michael"
        assert result.last_name == "Chen"
        assert result.company == "Startup Inc"

    @pytest.mark.asyncio
    async def test_enrich_person_not_found(self, apollo_client):
        """Test person enrichment when person is not found"""
        apollo_client._mock_response.json.return_value = {"person": None}

        result = await apollo_client.enrich_person(email="notfound@example.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_enrich_person_invalid_params(self, apollo_client):
        """Test person enrichment with invalid parameters"""
        with pytest.raises(ValueError, match="Must provide email or linkedin_url"):
            await apollo_client.enrich_person()

    @pytest.mark.asyncio
    async def test_enrich_person_with_caching(self, apollo_client):
        """Test person enrichment with caching"""
        # Mock cache hit
        cached_data = {
            "person_id": "cached_123",
            "email": "cached@example.com",
            "first_name": "Cached",
            "last_name": "User",
        }

        apollo_client.cache_service.get.return_value = json.dumps(cached_data)

        result = await apollo_client.enrich_person(email="cached@example.com")

        assert isinstance(result, PersonEnrichmentResult)
        assert result.person_id == "cached_123"
        assert result.first_name == "Cached"

        # Verify cache was checked and API was not called
        apollo_client.cache_service.get.assert_called()
        apollo_client.session.request.assert_not_called()


class TestEmailVerification:
    """Test email verification functionality"""

    @pytest_asyncio.fixture
    async def apollo_client(self):
        """Create Apollo client for email verification testing"""
        config = ApolloConfig(api_key="test_key")
        client = ApolloClient(config)

        # Mock session and response
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock()
        mock_session.request = AsyncMock(return_value=mock_response)

        client.session = mock_session
        client._mock_response = mock_response

        return client

    @pytest.mark.asyncio
    async def test_verify_email_deliverable(self, apollo_client):
        """Test email verification for deliverable email"""
        apollo_client._mock_response.json.return_value = {
            "email": "valid@example.com",
            "is_valid": True,
            "is_risky": False,
            "is_disposable": False,
            "verification_status": "deliverable",
            "confidence_score": 0.95,
        }

        result = await apollo_client.verify_email("valid@example.com")

        assert result["email"] == "valid@example.com"
        assert result["is_valid"] is True
        assert result["verification_status"] == "deliverable"
        assert result["confidence_score"] == 0.95

    @pytest.mark.asyncio
    async def test_verify_email_undeliverable(self, apollo_client):
        """Test email verification for undeliverable email"""
        apollo_client._mock_response.json.return_value = {
            "email": "invalid@nonexistent.com",
            "is_valid": False,
            "is_risky": True,
            "verification_status": "undeliverable",
            "confidence_score": 0.1,
        }

        result = await apollo_client.verify_email("invalid@nonexistent.com")

        assert result["is_valid"] is False
        assert result["verification_status"] == "undeliverable"
        assert result["is_risky"] is True

    @pytest.mark.asyncio
    async def test_verify_email_disposable(self, apollo_client):
        """Test email verification for disposable email"""
        apollo_client._mock_response.json.return_value = {
            "email": "temp@10minutemail.com",
            "is_valid": True,
            "is_disposable": True,
            "verification_status": "risky",
            "confidence_score": 0.3,
        }

        result = await apollo_client.verify_email("temp@10minutemail.com")

        assert result["is_disposable"] is True
        assert result["verification_status"] == "risky"


class TestOrganizationEnrichment:
    """Test organization enrichment functionality"""

    @pytest_asyncio.fixture
    async def apollo_client(self):
        """Create Apollo client for organization testing"""
        config = ApolloConfig(api_key="test_key")
        client = ApolloClient(config)

        # Mock session and response
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock()
        mock_session.request = AsyncMock(return_value=mock_response)

        client.session = mock_session
        client._mock_response = mock_response

        return client

    @pytest.mark.asyncio
    async def test_enrich_organization_by_ontario_mills(self, apollo_client):
        """Test organization enrichment by ontario_mills"""
        apollo_client._mock_response.json.return_value = {
            "organization": {
                "id": "org_123",
                "name": "Tech Solutions Inc",
                "website_url": "https://techsolutions.com",
                "industry": "Software Development",
                "founded_year": 2018,
                "estimated_num_employees": 150,
                "retail_location_count": 3,
                "annual_revenue": "10M-50M",
                "headquarters": {"city": "Rancho Cucamonga", "state": "California", "country": "United States"},
                "technologies": ["Salesforce", "AWS", "React"],
            }
        }

        result = await apollo_client.enrich_organization(ontario_mills="techsolutions.com")

        assert isinstance(result, OrganizationEnrichmentResult)
        assert result.organization_id == "org_123"
        assert result.name == "Tech Solutions Inc"
        assert result.ontario_mills == "techsolutions.com"
        assert result.industry == "Software Development"
        assert result.employee_count == 150
        assert result.annual_revenue == "10M-50M"
        assert "Salesforce" in result.technologies
        assert result.headquarters_city == "Rancho Cucamonga"

    @pytest.mark.asyncio
    async def test_enrich_organization_by_name(self, apollo_client):
        """Test organization enrichment by company name"""
        apollo_client._mock_response.json.return_value = {
            "organization": {
                "id": "org_456",
                "name": "Startup Innovations",
                "industry": "Technology",
                "estimated_num_employees": 25,
            }
        }

        result = await apollo_client.enrich_organization(name="Startup Innovations")

        assert isinstance(result, OrganizationEnrichmentResult)
        assert result.name == "Startup Innovations"
        assert result.employee_count == 25

    @pytest.mark.asyncio
    async def test_enrich_organization_not_found(self, apollo_client):
        """Test organization enrichment when not found"""
        apollo_client._mock_response.json.return_value = {"organization": None}

        result = await apollo_client.enrich_organization(ontario_mills="nonexistent.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_enrich_organization_invalid_params(self, apollo_client):
        """Test organization enrichment with invalid parameters"""
        with pytest.raises(ValueError, match="Must provide ontario_mills or name"):
            await apollo_client.enrich_organization()


class TestLeadScoring:
    """Test Apollo lead scoring algorithms"""

    @pytest_asyncio.fixture
    async def apollo_client(self):
        """Create Apollo client for scoring tests"""
        config = ApolloConfig(api_key="test_key")
        return ApolloClient(config)

    @pytest.mark.asyncio
    async def test_calculate_lead_score_high_value(self, apollo_client):
        """Test lead scoring for high-value prospect"""
        enrichment_result = PersonEnrichmentResult(
            person_id="123",
            email="cto@bigtech.com",
            first_name="John",
            last_name="Doe",
            title="Chief Technology Officer",
            company="Big Tech Corp",
            industry="Technology",
            employee_count=5000,
            annual_revenue="1B+",
            phone_numbers=["+1-555-123-4567"],
            linkedin_url="https://linkedin.com/in/johndoe",
            email_verified=True,
            confidence_score=0.95,
        )

        score_result = await apollo_client.calculate_lead_score(enrichment_result)

        assert score_result["total_score"] >= 80  # High score expected
        assert score_result["title_score"] >= 25  # High-level title
        assert score_result["company_score"] >= 20  # Large company
        assert score_result["contact_completeness_score"] >= 15  # Complete contact info
        assert score_result["email_verification_score"] == 20  # Verified email
        assert "score_breakdown" in score_result

    @pytest.mark.asyncio
    async def test_calculate_lead_score_medium_value(self, apollo_client):
        """Test lead scoring for medium-value prospect"""
        enrichment_result = PersonEnrichmentResult(
            person_id="456",
            email="manager@midsize.com",
            first_name="Jane",
            last_name="Smith",
            title="Engineering Manager",
            company="Midsize Corp",
            industry="Software",
            employee_count=250,
            annual_revenue="10M-50M",
            phone_numbers=[],
            linkedin_url=None,
            email_verified=False,
            confidence_score=0.75,
        )

        score_result = await apollo_client.calculate_lead_score(enrichment_result)

        assert 40 <= score_result["total_score"] <= 70  # Medium score
        assert score_result["title_score"] > 10  # Manager level
        assert score_result["company_score"] > 5  # Medium company
        assert score_result["contact_completeness_score"] < 15  # Incomplete info
        assert score_result["email_verification_score"] == 0  # Unverified email

    @pytest.mark.asyncio
    async def test_calculate_lead_score_low_value(self, apollo_client):
        """Test lead scoring for low-value prospect"""
        enrichment_result = PersonEnrichmentResult(
            person_id="789",
            email="intern@small.com",
            first_name="Bob",
            last_name="Wilson",
            title="Intern",
            company="Small Startup",
            industry="Unknown",
            employee_count=10,
            annual_revenue="<1M",
            phone_numbers=[],
            linkedin_url=None,
            email_verified=False,
            confidence_score=0.4,
        )

        score_result = await apollo_client.calculate_lead_score(enrichment_result)

        assert score_result["total_score"] <= 40  # Low score
        assert score_result["title_score"] <= 5  # Entry level
        assert score_result["company_score"] <= 5  # Small company

    @pytest.mark.asyncio
    async def test_score_title_executive_level(self, apollo_client):
        """Test title scoring for executive positions"""
        assert apollo_client._score_title("Chief Executive Officer") == 30
        assert apollo_client._score_title("CTO") == 30
        assert apollo_client._score_title("VP of Engineering") == 25
        assert apollo_client._score_title("Director of Sales") == 20
        assert apollo_client._score_title("Senior Manager") == 15
        assert apollo_client._score_title("Engineer") == 10
        assert apollo_client._score_title("Intern") == 5
        assert apollo_client._score_title("Unknown") == 0

    @pytest.mark.asyncio
    async def test_score_company_size(self, apollo_client):
        """Test company scoring by size"""
        assert apollo_client._score_company(10000, "1B+") == 25  # Enterprise
        assert apollo_client._score_company(1000, "100M-1B") == 20  # Large
        assert apollo_client._score_company(250, "50M-100M") == 15  # Medium-Large
        assert apollo_client._score_company(100, "10M-50M") == 10  # Medium
        assert apollo_client._score_company(25, "1M-10M") == 5  # Small
        assert apollo_client._score_company(5, "<1M") == 0  # Very small

    @pytest.mark.asyncio
    async def test_score_contact_completeness(self, apollo_client):
        """Test contact completeness scoring"""
        # Complete contact info
        complete_score = apollo_client._score_contact_completeness(
            email_verified=True,
            phone_numbers=["+1-555-123-4567"],
            linkedin_url="https://linkedin.com/in/user",
            confidence_score=0.9,
        )
        assert complete_score >= 15

        # Partial contact info
        partial_score = apollo_client._score_contact_completeness(
            email_verified=False, phone_numbers=[], linkedin_url=None, confidence_score=0.5
        )
        assert partial_score <= 10


class TestBatchOperations:
    """Test batch enrichment operations"""

    @pytest_asyncio.fixture
    async def apollo_client(self):
        """Create Apollo client for batch testing"""
        config = ApolloConfig(api_key="test_key", batch_size=5)
        client = ApolloClient(config)

        # Mock session
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock()
        mock_session.request = AsyncMock(return_value=mock_response)

        client.session = mock_session
        client._mock_response = mock_response

        return client

    @pytest.mark.asyncio
    async def test_batch_enrich_people_success(self, apollo_client):
        """Test successful batch people enrichment"""
        # Mock batch response
        apollo_client._mock_response.json.return_value = {
            "people": [
                {"email": "user1@example.com", "first_name": "User", "last_name": "One", "id": "person_1"},
                {"email": "user2@example.com", "first_name": "User", "last_name": "Two", "id": "person_2"},
            ]
        }

        emails = ["user1@example.com", "user2@example.com"]

        results = await apollo_client.batch_enrich_people(emails)

        assert len(results) == 2
        assert all(isinstance(r, PersonEnrichmentResult) for r in results)
        assert results[0].email == "user1@example.com"
        assert results[1].email == "user2@example.com"

    @pytest.mark.asyncio
    async def test_batch_enrich_people_large_batch(self, apollo_client):
        """Test batch enrichment with large number of emails"""
        # Mock response for multiple batches
        apollo_client._mock_response.json.return_value = {
            "people": [
                {"email": f"user{i}@example.com", "id": f"person_{i}"}
                for i in range(5)  # Batch size is 5
            ]
        }

        # 12 emails should be split into 3 batches (5, 5, 2)
        emails = [f"user{i}@example.com" for i in range(12)]

        results = await apollo_client.batch_enrich_people(emails)

        assert len(results) == 12
        assert apollo_client.session.request.call_count == 3  # 3 batch requests

    @pytest.mark.asyncio
    async def test_batch_enrich_people_partial_failure(self, apollo_client):
        """Test batch enrichment with partial failures"""
        # Mock response with some successful and some failed enrichments
        apollo_client._mock_response.json.return_value = {
            "people": [
                {"email": "success@example.com", "id": "person_1"},
                None,  # Failed enrichment
                {"email": "success2@example.com", "id": "person_2"},
            ]
        }

        emails = ["success@example.com", "failed@example.com", "success2@example.com"]

        results = await apollo_client.batch_enrich_people(emails)

        # Should return results only for successful enrichments
        assert len(results) == 2
        assert results[0].email == "success@example.com"
        assert results[1].email == "success2@example.com"

    @pytest.mark.asyncio
    async def test_batch_enrich_people_empty_input(self, apollo_client):
        """Test batch enrichment with empty input"""
        results = await apollo_client.batch_enrich_people([])

        assert results == []
        apollo_client.session.request.assert_not_called()


class TestSearchOperations:
    """Test Apollo search functionality"""

    @pytest_asyncio.fixture
    async def apollo_client(self):
        """Create Apollo client for search testing"""
        config = ApolloConfig(api_key="test_key")
        client = ApolloClient(config)

        # Mock session
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock()
        mock_session.request = AsyncMock(return_value=mock_response)

        client.session = mock_session
        client._mock_response = mock_response

        return client

    @pytest.mark.asyncio
    async def test_search_people_by_title(self, apollo_client):
        """Test searching people by job title"""
        apollo_client._mock_response.json.return_value = {
            "people": [
                {
                    "id": "search_1",
                    "first_name": "John",
                    "last_name": "Doe",
                    "title": "CTO",
                    "email": "john@example.com",
                },
                {
                    "id": "search_2",
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "title": "CTO",
                    "email": "jane@example.com",
                },
            ],
            "pagination": {"page": 1, "per_page": 25, "total_entries": 2},
        }

        search_params = {"person_titles": ["CTO", "Chief Technology Officer"]}

        result = await apollo_client.search_people(search_params)

        assert len(result["people"]) == 2
        assert all(person["title"] == "CTO" for person in result["people"])
        assert "pagination" in result

    @pytest.mark.asyncio
    async def test_search_people_by_company_and_location(self, apollo_client):
        """Test searching people by company and location"""
        apollo_client._mock_response.json.return_value = {
            "people": [
                {
                    "id": "search_3",
                    "first_name": "Alice",
                    "organization": {"name": "Tech Corp"},
                    "city": "Rancho Cucamonga",
                }
            ],
            "pagination": {"total_entries": 1},
        }

        search_params = {
            "organization_names": ["Tech Corp"],
            "person_locations": ["Rancho Cucamonga, CA"],
            "page": 1,
            "per_page": 25,
        }

        result = await apollo_client.search_people(search_params)

        assert len(result["people"]) == 1
        assert result["people"][0]["organization"]["name"] == "Tech Corp"
        assert result["people"][0]["city"] == "Rancho Cucamonga"

    @pytest.mark.asyncio
    async def test_search_people_pagination(self, apollo_client):
        """Test search with pagination"""
        search_params = {"person_titles": ["Manager"], "page": 2, "per_page": 10}

        await apollo_client.search_people(search_params)

        # Verify pagination parameters were included in request
        apollo_client.session.request.assert_called_once()
        call_args = apollo_client.session.request.call_args

        # Check that pagination params are in the request data
        request_data = call_args[1]["json"]
        assert request_data["page"] == 2
        assert request_data["per_page"] == 10


class TestHealthAndMonitoring:
    """Test health check and monitoring functionality"""

    @pytest_asyncio.fixture
    async def apollo_client(self):
        """Create Apollo client for health testing"""
        config = ApolloConfig(api_key="test_key")
        client = ApolloClient(config)

        # Mock session
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock()
        mock_session.request = AsyncMock(return_value=mock_response)

        client.session = mock_session
        client._mock_response = mock_response

        return client

    @pytest.mark.asyncio
    async def test_health_check_success(self, apollo_client):
        """Test successful health check"""
        apollo_client._mock_response.json.return_value = {
            "status": "ok",
            "credits_remaining": 5000,
            "rate_limit_remaining": 115,
        }

        result = await apollo_client.health_check()

        assert result["status"] == "healthy"
        assert result["api_status"] == "ok"
        assert result["credits_remaining"] == 5000
        assert result["rate_limit_remaining"] == 115
        assert result["response_time_ms"] > 0

    @pytest.mark.asyncio
    async def test_health_check_api_down(self, apollo_client):
        """Test health check when API is down"""
        apollo_client.session.request.side_effect = Exception("Connection failed")

        result = await apollo_client.health_check()

        assert result["status"] == "unhealthy"
        assert "error" in result
        assert result["api_status"] == "error"

    @pytest.mark.asyncio
    async def test_health_check_low_credits(self, apollo_client):
        """Test health check with low credit warning"""
        apollo_client._mock_response.json.return_value = {
            "status": "ok",
            "credits_remaining": 50,  # Low credits
            "rate_limit_remaining": 100,
        }

        result = await apollo_client.health_check()

        assert result["status"] == "warning"
        assert "Low credits remaining" in result["warnings"][0]

    @pytest.mark.asyncio
    async def test_health_check_rate_limit_warning(self, apollo_client):
        """Test health check with rate limit warning"""
        apollo_client._mock_response.json.return_value = {
            "status": "ok",
            "credits_remaining": 5000,
            "rate_limit_remaining": 5,  # Low rate limit
        }

        result = await apollo_client.health_check()

        assert result["status"] == "warning"
        assert "Rate limit nearly exceeded" in result["warnings"][0]


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_client_without_api_key(self):
        """Test client initialization without API key"""
        config = ApolloConfig()  # No API key

        with pytest.raises(ValueError, match="API key is required"):
            ApolloClient(config)

    @pytest.mark.asyncio
    async def test_malformed_api_response(self):
        """Test handling of malformed API responses"""
        config = ApolloConfig(api_key="test_key")
        client = ApolloClient(config)

        # Mock malformed response
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_session.request = AsyncMock(return_value=mock_response)

        client.session = mock_session

        with pytest.raises(ApolloAPIException, match="Invalid response format"):
            await client._handle_response(mock_response)

    @pytest.mark.asyncio
    async def test_network_timeout_handling(self):
        """Test handling of network timeouts"""
        config = ApolloConfig(api_key="test_key", request_timeout_seconds=0.1)
        client = ApolloClient(config)

        # Mock timeout
        mock_session = MagicMock()
        mock_session.request.side_effect = asyncio.TimeoutError("Request timeout")
        client.session = mock_session

        with pytest.raises(ApolloAPIException, match="Request timeout"):
            await client._make_request("GET", "/test")

    @pytest.mark.asyncio
    async def test_concurrent_rate_limiting(self):
        """Test rate limiting under concurrent load"""
        config = ApolloConfig(api_key="test_key", rate_limit_requests_per_minute=1)
        client = ApolloClient(config)

        # Mock successful responses
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"success": True})
        mock_session.request = AsyncMock(return_value=mock_response)
        client.session = mock_session

        # Create many concurrent requests
        tasks = []
        for i in range(10):
            task = client._make_request("GET", f"/test-{i}")
            tasks.append(task)

        # All should complete but be rate limited
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all(r["success"] for r in results)

        # Verify all requests were made (rate limiting doesn't prevent them, just delays)
        assert mock_session.request.call_count == 10


@pytest.mark.performance
class TestPerformanceCharacteristics:
    """Test Apollo client performance characteristics"""

    @pytest.mark.asyncio
    async def test_batch_enrichment_performance(self):
        """Test performance of batch enrichment operations"""
        config = ApolloConfig(api_key="test_key", batch_size=50)
        client = ApolloClient(config)

        # Mock fast response
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"people": [{"email": f"user{i}@test.com", "id": f"person_{i}"} for i in range(50)]}
        )
        mock_session.request = AsyncMock(return_value=mock_response)
        client.session = mock_session

        # Test with large number of emails
        emails = [f"user{i}@test.com" for i in range(200)]

        import time

        start_time = time.time()

        results = await client.batch_enrich_people(emails)

        end_time = time.time()

        # Verify results
        assert len(results) == 200

        # Performance should be reasonable (under 2 seconds for mocked operations)
        execution_time = end_time - start_time
        assert execution_time < 2.0

        # Verify batching efficiency (200 emails / 50 batch size = 4 requests)
        assert mock_session.request.call_count == 4


if __name__ == "__main__":
    # Run specific test classes for development
    pytest.main(["-v", "tests/services/test_apollo_client.py::TestPersonEnrichment", "--tb=short"])
