"""
Test Buyer Bot Handlers
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from ghl_integration.handlers.buyer_handlers import (
    handle_buyer_inquiry,
    handle_buyer_response,
    handle_pipeline_change,
    get_handler,
    _extract_buyer_preferences,
    _parse_budget,
    _extract_preferences_from_message,
    _calculate_buyer_score,
    _get_buyer_pipeline_ids,
)


class TestBuyerHandlers:
    """Test suite for buyer bot webhook handlers"""

    @pytest.mark.asyncio
    async def test_handle_buyer_inquiry_with_buyer_tag(self):
        """Test handling buyer inquiry with buyer tag"""
        payload = {
            "data": {
                "id": "contact_buyer_001",
                "name": "Mike Buyer",
                "email": "mike@example.com",
                "tags": ["buyer", "home_buyer"],
                "message": "Looking for a 3 bed 2 bath home around $600k in Rancho Cucamonga",
                "customFields": {}
            }
        }
        
        with patch("ghl_integration.handlers.buyer_handlers._send_buyer_greeting", new_callable=AsyncMock) as mock_greeting:
            with patch("ghl_integration.handlers.buyer_handlers._store_buyer_state", new_callable=AsyncMock) as mock_store:
                with patch("ghl_integration.handlers.buyer_handlers._update_ghl_buyer_fields", new_callable=AsyncMock):
                    with patch("ghl_integration.handlers.buyer_handlers._emit_buyer_event", new_callable=AsyncMock):
                        
                        result = await handle_buyer_inquiry(payload)
                        
                        assert result["success"] is True
                        assert result["buyer_state"]["contact_id"] == "contact_buyer_001"
                        assert result["buyer_state"]["qualification_stage"] == "Q0"
                        mock_greeting.assert_called_once()
                        mock_store.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_buyer_inquiry_no_buyer_tag(self):
        """Test that non-buyer inquiries are skipped"""
        payload = {
            "data": {
                "id": "contact_001",
                "name": "John Seller",
                "tags": ["seller"]
            }
        }
        
        result = await handle_buyer_inquiry(payload)
        
        assert result["success"] is True
        assert "Not a buyer inquiry" in result["message"]

    @pytest.mark.asyncio
    async def test_handle_buyer_response_success(self):
        """Test handling buyer response message"""
        payload = {
            "data": {
                "contactId": "contact_buyer_001",
                "message": "I'm pre-approved for $650k and want to see homes this weekend.",
                "direction": "inbound"
            }
        }
        
        mock_state = {
            "contact_id": "contact_buyer_001",
            "qualification_stage": "Q2",
            "preferences": {
                "budget_max": 600000,
                "bedrooms": 3
            },
            "buyer_score": 40
        }
        
        with patch("ghl_integration.handlers.buyer_handlers._get_buyer_state", new_callable=AsyncMock) as mock_get_state:
            mock_get_state.return_value = mock_state
            with patch("ghl_integration.handlers.buyer_handlers._process_buyer_message", new_callable=AsyncMock) as mock_process:
                mock_process.return_value = ("Q3", "Great! Let me find some properties for you.", {})
                with patch("ghl_integration.handlers.buyer_handlers._send_buyer_message", new_callable=AsyncMock):
                    with patch("ghl_integration.handlers.buyer_handlers._store_buyer_state", new_callable=AsyncMock) as mock_store:
                        with patch("ghl_integration.handlers.buyer_handlers._update_ghl_buyer_fields", new_callable=AsyncMock):
                            with patch("ghl_integration.handlers.buyer_handlers._match_properties", new_callable=AsyncMock) as mock_match:
                                mock_match.return_value = []  # Don't trigger matching yet
                                with patch("ghl_integration.handlers.buyer_handlers._emit_buyer_event", new_callable=AsyncMock):
                                    
                                    result = await handle_buyer_response(payload)
                                    
                                    assert result["success"] is True
                                    assert result["stage"] == "Q3"
                                    assert result["buyer_score"] > 40  # Score should increase
                                    mock_process.assert_called_once()
                                    mock_store.assert_called()

    @pytest.mark.asyncio
    async def test_handle_buyer_response_triggers_matching(self):
        """Test that qualified buyers get property matches"""
        payload = {
            "data": {
                "contactId": "contact_buyer_002",
                "message": "I'm ready to buy now!",
                "direction": "inbound"
            }
        }
        
        mock_state = {
            "contact_id": "contact_buyer_002",
            "qualification_stage": "Q4",
            "preferences": {"budget_max": 600000, "bedrooms": 3, "location_preferences": ["rancho cucamonga"]},
            "buyer_score": 85
        }
        
        mock_properties = [
            {"address": "123 Main St", "price": 580000, "bedrooms": 3},
            {"address": "456 Oak Ave", "price": 595000, "bedrooms": 3}
        ]
        
        with patch("ghl_integration.handlers.buyer_handlers._get_buyer_state", new_callable=AsyncMock) as mock_get_state:
            mock_get_state.return_value = mock_state
            with patch("ghl_integration.handlers.buyer_handlers._process_buyer_message", new_callable=AsyncMock) as mock_process:
                mock_process.return_value = ("Q4", "Here are some properties!", {})
                with patch("ghl_integration.handlers.buyer_handlers._send_buyer_message", new_callable=AsyncMock):
                    with patch("ghl_integration.handlers.buyer_handlers._store_buyer_state", new_callable=AsyncMock) as mock_store:
                        with patch("ghl_integration.handlers.buyer_handlers._update_ghl_buyer_fields", new_callable=AsyncMock):
                            with patch("ghl_integration.handlers.buyer_handlers._match_properties", new_callable=AsyncMock) as mock_match:
                                mock_match.return_value = mock_properties
                                with patch("ghl_integration.handlers.buyer_handlers._send_property_recommendations", new_callable=AsyncMock) as mock_send_props:
                                    with patch("ghl_integration.handlers.buyer_handlers._emit_buyer_event", new_callable=AsyncMock):
                                        
                                        result = await handle_buyer_response(payload)
                                        
                                        assert result["success"] is True
                                        mock_match.assert_called_once()
                                        mock_send_props.assert_called_once()
                                        # Verify properties_matched was updated
                                        store_calls = mock_store.call_args_list
                                        assert len(store_calls) > 0

    @pytest.mark.asyncio
    async def test_handle_pipeline_change_buyer_pipeline(self):
        """Test handling pipeline stage change for buyer pipeline"""
        with patch("ghl_integration.handlers.buyer_handlers._get_buyer_pipeline_ids", return_value=["pipeline_buyer_001"]):
            payload = {
                "data": {
                    "contactId": "contact_buyer_001",
                    "pipelineId": "pipeline_buyer_001",
                    "newStageId": "stage_qualified",
                    "oldStageId": "stage_new_lead"
                }
            }
            
            mock_state = {
                "contact_id": "contact_buyer_001",
                "qualification_stage": "Q0"
            }
            
            with patch("ghl_integration.handlers.buyer_handlers._get_buyer_state", new_callable=AsyncMock) as mock_get_state:
                mock_get_state.return_value = mock_state
                with patch("ghl_integration.handlers.buyer_handlers._store_buyer_state", new_callable=AsyncMock):
                    with patch("ghl_integration.handlers.buyer_handlers._update_ghl_buyer_fields", new_callable=AsyncMock):
                        with patch("ghl_integration.handlers.buyer_handlers._emit_buyer_event", new_callable=AsyncMock):
                            with patch("ghl_integration.handlers.buyer_handlers._get_stage_qualification_mapping") as mock_mapping:
                                mock_mapping.return_value = {"stage_qualified": "Q2"}
                                
                                result = await handle_pipeline_change(payload)
                                
                                assert result["success"] is True
                                assert result["pipeline_stage"] == "stage_qualified"

    @pytest.mark.asyncio
    async def test_handle_pipeline_change_non_buyer_pipeline(self):
        """Test that non-buyer pipeline changes are skipped"""
        with patch("ghl_integration.handlers.buyer_handlers._get_buyer_pipeline_ids", return_value=["pipeline_other"]):
            payload = {
                "data": {
                    "pipelineId": "pipeline_buyer_001"  # Not in list
                }
            }
            
            result = await handle_pipeline_change(payload)
            
            assert result["success"] is True
            assert "Not a buyer pipeline" in result["message"]

    def test_get_handler_returns_correct_handler(self):
        """Test that get_handler returns correct functions"""
        inquiry_handler = get_handler("contact.create")
        response_handler = get_handler("conversation.message.created")
        pipeline_handler = get_handler("pipeline.stage.changed")
        
        assert inquiry_handler is not None
        assert inquiry_handler.__name__ == "handle_buyer_inquiry"
        assert response_handler.__name__ == "handle_buyer_response"
        assert pipeline_handler.__name__ == "handle_pipeline_change"


class TestBuyerHelperFunctions:
    """Test helper functions for buyer handlers"""

    def test_extract_buyer_preferences_from_custom_fields(self):
        """Test preference extraction from custom fields"""
        data = {
            "customFields": {
                "budget_max": 750000,
                "bedrooms": 4,
                "bathrooms": 2.5
            }
        }
        
        prefs = _extract_buyer_preferences(data)
        
        assert prefs["budget_max"] == 750000
        assert prefs["bedrooms"] == 4
        assert prefs["bathrooms"] == 2.5

    def test_extract_buyer_preferences_from_message(self):
        """Test preference extraction from message text"""
        data = {
            "message": "Looking for a 3 bed 2 bath home around $650k in Rancho Cucamonga"
        }
        
        prefs = _extract_buyer_preferences(data)
        
        assert prefs["bedrooms"] == 3
        assert prefs["bathrooms"] == 2
        assert prefs["budget_max"] == 650000
        assert "rancho cucamonga" in prefs["location_preferences"]

    def test_parse_budget_numeric(self):
        """Test parsing numeric budget"""
        assert _parse_budget(500000) == 500000.0
        assert _parse_budget(750000.50) == 750000.50

    def test_parse_budget_string(self):
        """Test parsing budget from string"""
        assert _parse_budget("$650,000") == 650000.0
        assert _parse_budget("800k") == 800000.0
        assert _parse_budget("1.2M") == 1200000.0

    def test_parse_budget_invalid(self):
        """Test parsing invalid budget values"""
        assert _parse_budget("not a number") is None
        assert _parse_budget("") is None
        assert _parse_budget(None) is None

    def test_extract_preferences_budget(self):
        """Test budget extraction from message"""
        message = "My budget is around $750,000"
        
        prefs = _extract_preferences_from_message(message)
        
        assert prefs["budget_max"] == 750000

    def test_extract_preferences_rooms(self):
        """Test room count extraction from message"""
        message = "Need at least 4 bedrooms and 2.5 bathrooms"
        
        prefs = _extract_preferences_from_message(message)
        
        assert prefs["bedrooms"] == 4
        assert prefs["bathrooms"] == 2.5

    def test_extract_preferences_location(self):
        """Test location extraction from message"""
        message = "I want to live in Rancho Cucamonga or Ontario"
        
        prefs = _extract_preferences_from_message(message)
        
        assert "rancho cucamonga" in prefs["location_preferences"]
        assert "ontario" in prefs["location_preferences"]

    def test_extract_preferences_timeline(self):
        """Test timeline extraction from message"""
        assert _extract_preferences_from_message("I need to buy ASAP")["timeline"] == "ASAP"
        assert _extract_preferences_from_message("Looking to buy in 30 days")["timeline"] == "30_days"
        assert _extract_preferences_from_message("Planning for next month")["timeline"] == "30_days"
        assert _extract_preferences_from_message("Just browsing for now")["timeline"] == "exploring"

    def test_calculate_buyer_score_stage_based(self):
        """Test score calculation based on qualification stage"""
        state_q0 = {"qualification_stage": "Q0", "preferences": {}}
        state_q2 = {"qualification_stage": "Q2", "preferences": {}}
        state_q4 = {"qualification_stage": "Q4", "preferences": {}}
        
        assert _calculate_buyer_score(state_q0) == 10
        assert _calculate_buyer_score(state_q2) == 40
        assert _calculate_buyer_score(state_q4) == 80

    def test_calculate_buyer_score_with_preferences(self):
        """Test score calculation with preferences"""
        state = {
            "qualification_stage": "Q2",
            "preferences": {
                "budget_min": 400000,
                "budget_max": 600000,
                "location_preferences": ["rancho cucamonga"],
                "timeline": "30_days"
            }
        }
        
        score = _calculate_buyer_score(state)
        
        assert score > 40  # Base Q2 score + preference bonuses
        assert score <= 100

    def test_calculate_buyer_score_capped_at_100(self):
        """Test that score is capped at 100"""
        state = {
            "qualification_stage": "QUALIFIED",
            "preferences": {
                "budget_min": 400000,
                "budget_max": 600000,
                "location_preferences": ["city1", "city2"],
                "timeline": "ASAP"
            }
        }
        
        score = _calculate_buyer_score(state)
        
        assert score == 100

    def test_get_buyer_pipeline_ids_from_env(self):
        """Test getting buyer pipeline IDs from environment"""
        import os
        with patch.dict(os.environ, {"GHL_BUYER_PIPELINE_IDS": "pipe1,pipe2"}):
            ids = _get_buyer_pipeline_ids()
            assert ids == ["pipe1", "pipe2"]
