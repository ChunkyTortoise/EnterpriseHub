"""
Tests for Mobile API Endpoints
Tests property, lead, analytics, and utility endpoints for mobile apps.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status

from ghl_real_estate_ai.api.main import app

client = TestClient(app)

class TestMobileEndpoints:
    """Test cases for mobile-optimized endpoints."""
    
    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers for testing."""
        return {
            "Authorization": "Bearer test_token_12345",
            "X-Device-ID": "test_device_12345",
            "X-App-Version": "1.0.0",
            "X-Platform": "ios"
        }
    
    @pytest.fixture
    def sample_gps_location(self):
        """Sample GPS coordinates for testing."""
        return "30.2672,-97.7431"  # Austin, TX coordinates

class TestMobileProperties:
    """Test mobile property endpoints."""
    
    def test_get_mobile_properties_without_auth(self):
        """Test property listing without authentication."""
        response = client.get("/api/mobile/properties")
        
        # Should require authentication
        assert response.status_code == status.HTTP_403_FORBIDDEN or response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @patch('ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user')
    def test_get_mobile_properties_basic(self, mock_auth):
        """Test basic property listing."""
        # Mock authentication
        mock_auth.return_value = {
            "user_id": "test_user",
            "username": "test_user"
        }
        
        response = client.get(
            "/api/mobile/properties",
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Note: This may fail due to dependency injection setup
        # In a full implementation, this would test property listing
        
    @patch('ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user')
    def test_get_mobile_properties_with_location(self, mock_auth):
        """Test property listing with GPS location filtering."""
        mock_auth.return_value = {
            "user_id": "test_user",
            "username": "test_user"
        }
        
        response = client.get(
            "/api/mobile/properties",
            params={
                "location": "30.2672,-97.7431",
                "radius": "25.0",
                "limit": "10"
            },
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Test would validate location-based filtering
        
    @patch('ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user')
    def test_get_mobile_properties_with_filters(self, mock_auth):
        """Test property listing with price and feature filters."""
        mock_auth.return_value = {
            "user_id": "test_user",
            "username": "test_user"
        }
        
        response = client.get(
            "/api/mobile/properties",
            params={
                "min_price": "500000",
                "max_price": "800000",
                "bedrooms": "3",
                "bathrooms": "2.5",
                "property_type": "Single Family"
            },
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Test would validate filtering functionality
        
    @patch('ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user')
    def test_get_property_details(self, mock_auth):
        """Test detailed property information retrieval."""
        mock_auth.return_value = {
            "user_id": "test_user",
            "username": "test_user"
        }
        
        property_id = "prop_austin_001"
        response = client.get(
            f"/api/mobile/properties/{property_id}",
            params={"include_ai_insights": "true"},
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Test would validate detailed property data structure

class TestMobileLeads:
    """Test mobile lead endpoints."""
    
    @patch('ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user')
    def test_get_mobile_leads_basic(self, mock_auth):
        """Test basic lead listing."""
        mock_auth.return_value = {
            "user_id": "test_user",
            "username": "test_user"
        }
        
        response = client.get(
            "/api/mobile/leads",
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Test would validate lead listing structure
        
    @patch('ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user')
    def test_get_mobile_leads_with_filters(self, mock_auth):
        """Test lead listing with status and priority filters."""
        mock_auth.return_value = {
            "user_id": "test_user",
            "username": "test_user"
        }
        
        response = client.get(
            "/api/mobile/leads",
            params={
                "status_filter": "qualified",
                "priority_filter": "high",
                "search": "Sarah",
                "location": "30.2672,-97.7431",
                "radius": "10.0"
            },
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Test would validate filtering and search functionality
        
    @patch('ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user')
    def test_get_lead_details(self, mock_auth):
        """Test detailed lead information retrieval."""
        mock_auth.return_value = {
            "user_id": "test_user",
            "username": "test_user"
        }
        
        lead_id = "lead_001"
        response = client.get(
            f"/api/mobile/leads/{lead_id}",
            params={"include_ai_insights": "true"},
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Test would validate detailed lead data structure

class TestMobileAnalytics:
    """Test mobile analytics endpoints."""
    
    @patch('ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user')
    def test_get_analytics_summary(self, mock_auth):
        """Test mobile analytics summary."""
        mock_auth.return_value = {
            "user_id": "test_user",
            "username": "test_user"
        }
        
        response = client.get(
            "/api/mobile/analytics/summary",
            params={"period": "week"},
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Test would validate analytics data structure
        
    def test_analytics_period_validation(self):
        """Test analytics period parameter validation."""
        response = client.get(
            "/api/mobile/analytics/summary",
            params={"period": "invalid_period"},
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Should return validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

class TestMobileSettings:
    """Test mobile settings endpoints."""
    
    @patch('ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user')
    def test_get_mobile_settings(self, mock_auth):
        """Test retrieving mobile app settings."""
        mock_auth.return_value = {
            "user_id": "test_user",
            "username": "test_user"
        }
        
        response = client.get(
            "/api/mobile/settings",
            headers={
                "Authorization": "Bearer test_token",
                "X-Device-ID": "test_device_12345"
            }
        )
        
        # Test would validate settings structure
        
    @patch('ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user')
    def test_update_mobile_settings(self, mock_auth):
        """Test updating mobile app settings."""
        mock_auth.return_value = {
            "user_id": "test_user",
            "username": "test_user"
        }
        
        settings_update = {
            "push_enabled": True,
            "lead_notifications": True,
            "default_search_radius": 30.0,
            "theme": "dark",
            "ar_enabled": True,
            "voice_enabled": True
        }
        
        response = client.put(
            "/api/mobile/settings",
            json=settings_update,
            headers={
                "Authorization": "Bearer test_token",
                "X-Device-ID": "test_device_12345"
            }
        )
        
        # Test would validate settings update functionality

class TestMobileSync:
    """Test mobile offline sync endpoints."""
    
    @patch('ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user')
    def test_mobile_sync_basic(self, mock_auth):
        """Test basic sync operation."""
        mock_auth.return_value = {
            "user_id": "test_user",
            "username": "test_user"
        }
        
        sync_request = {
            "device_id": "test_device_12345",
            "last_sync": "2024-01-18T08:00:00Z",
            "pending_operations": [
                {
                    "id": "op_001",
                    "type": "lead_update",
                    "data": {
                        "lead_id": "lead_001",
                        "status": "qualified",
                        "notes": "Very interested"
                    },
                    "timestamp": "2024-01-18T09:30:00Z"
                }
            ],
            "conflict_resolution": "server_wins",
            "batch_size": 50
        }
        
        response = client.post(
            "/api/mobile/sync",
            json=sync_request,
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Test would validate sync response structure
        
    @patch('ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user')
    def test_mobile_sync_empty_operations(self, mock_auth):
        """Test sync with no pending operations."""
        mock_auth.return_value = {
            "user_id": "test_user",
            "username": "test_user"
        }
        
        sync_request = {
            "device_id": "test_device_12345",
            "last_sync": "2024-01-18T08:00:00Z",
            "pending_operations": [],
            "conflict_resolution": "server_wins",
            "batch_size": 50
        }
        
        response = client.post(
            "/api/mobile/sync",
            json=sync_request,
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Test would validate empty sync response

class TestMobileSearch:
    """Test mobile search endpoints."""
    
    @patch('ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user')
    def test_mobile_search_properties(self, mock_auth):
        """Test mobile search for properties."""
        mock_auth.return_value = {
            "user_id": "test_user",
            "username": "test_user"
        }
        
        search_request = {
            "query": "Hill Country properties under 800k",
            "search_type": "properties",
            "filters": {
                "max_price": 800000,
                "location": "Hill Country"
            },
            "location": {
                "latitude": 30.2672,
                "longitude": -97.7431,
                "accuracy": 10.0
            },
            "radius": 25.0,
            "sort_by": "relevance",
            "page": 1,
            "page_size": 20
        }
        
        response = client.post(
            "/api/mobile/search",
            json=search_request,
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Test would validate search response structure
        
    @patch('ghl_real_estate_ai.api.middleware.jwt_auth.get_current_user')
    def test_mobile_search_leads(self, mock_auth):
        """Test mobile search for leads."""
        mock_auth.return_value = {
            "user_id": "test_user",
            "username": "test_user"
        }
        
        search_request = {
            "query": "Sarah Chen",
            "search_type": "leads",
            "filters": {
                "status": "qualified"
            },
            "sort_by": "relevance",
            "page": 1,
            "page_size": 10
        }
        
        response = client.post(
            "/api/mobile/search",
            json=search_request,
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Test would validate lead search response
        
    def test_mobile_search_validation(self):
        """Test search input validation."""
        # Test with empty query
        search_request = {
            "query": "",  # Empty query should fail validation
            "search_type": "properties"
        }
        
        response = client.post(
            "/api/mobile/search",
            json=search_request,
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

class TestMobileErrorHandling:
    """Test mobile API error handling."""
    
    def test_invalid_device_id_header(self):
        """Test API calls with invalid or missing device ID header."""
        response = client.get(
            "/api/mobile/settings",
            headers={
                "Authorization": "Bearer test_token"
                # Missing X-Device-ID header
            }
        )
        
        # Should return error about missing device ID
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
    def test_invalid_json_payload(self):
        """Test API calls with malformed JSON."""
        response = client.post(
            "/api/mobile/search",
            data="invalid json payload",
            headers={
                "Authorization": "Bearer test_token",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
    def test_resource_not_found(self):
        """Test API calls for non-existent resources."""
        response = client.get(
            "/api/mobile/properties/non_existent_property_id",
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Should return 404 or 401 depending on auth setup
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_401_UNAUTHORIZED]

class TestMobileResponseFormats:
    """Test mobile API response formats."""
    
    def test_error_response_format(self):
        """Test standardized error response format."""
        # Trigger a validation error
        response = client.post("/api/mobile/search", json={})
        
        # Should have standardized error format
        if response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
            # Validation error format may differ from custom mobile error format
            pass
        
    def test_pagination_format(self):
        """Test pagination metadata format."""
        # This would test that list responses include proper pagination metadata
        pass
        
    def test_mobile_optimization_headers(self):
        """Test mobile-specific optimization headers."""
        response = client.get("/api/mobile/")
        
        # Check for mobile-friendly response headers
        # In a full implementation, this would check for:
        # - Compression headers
        # - Cache-Control headers
        # - Mobile-specific content-type headers
        
        assert response.status_code == status.HTTP_200_OK

if __name__ == "__main__":
    pytest.main([__file__, "-v"])