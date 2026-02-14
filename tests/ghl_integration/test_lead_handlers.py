"""
Test Lead Bot Handlers
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from ghl_integration.handlers.lead_handlers import (
    handle_new_lead,
    handle_lead_response,
    handle_lead_update,
    get_handler,
)


class TestLeadHandlers:
    """Test suite for lead bot webhook handlers"""

    @pytest.mark.asyncio
    async def test_handle_new_lead_success(self, contact_create_payload, mock_ghl_client):
        """Test successful new lead processing"""
        with patch("ghl_integration.handlers.lead_handlers.GHLAPIClient", return_value=mock_ghl_client):
            with patch("ghl_integration.handlers.lead_handlers._analyze_lead", new_callable=AsyncMock) as mock_analyze:
                mock_analyze.return_value = {
                    "temperature": "hot",
                    "score": 85,
                    "qualified": True,
                    "urgency": "high"
                }
                
                result = await handle_new_lead(contact_create_payload)
                
                assert result["success"] is True
                assert "contact_id" in result
                assert "analysis" in result

    @pytest.mark.asyncio
    async def test_handle_new_lead_extracts_contact_data(self, contact_create_payload):
        """Test that new lead handler extracts contact information correctly"""
        with patch("ghl_integration.handlers.lead_handlers._analyze_lead", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {"temperature": "warm", "score": 50}
            with patch("ghl_integration.handlers.lead_handlers._update_ghl_lead_fields", new_callable=AsyncMock):
                with patch("ghl_integration.handlers.lead_handlers._emit_lead_event", new_callable=AsyncMock):
                    
                    result = await handle_new_lead(contact_create_payload)
                    
                    # Verify contact data was extracted
                    call_args = mock_analyze.call_args[0][0]
                    assert call_args.get("email") == "john.smith@example.com"
                    assert call_args.get("name") == "John Smith"

    @pytest.mark.asyncio
    async def test_handle_new_lead_error(self):
        """Test error handling in new lead processing"""
        result = await handle_new_lead({"invalid": "payload"})
        
        assert result["success"] is False
        assert "retry_eligible" in result

    @pytest.mark.asyncio
    async def test_handle_lead_response_success(self, conversation_message_payload, mock_ghl_client):
        """Test successful lead response processing"""
        with patch("ghl_integration.handlers.lead_handlers._get_conversation_history", new_callable=AsyncMock) as mock_hist:
            mock_hist.return_value = []
            with patch("ghl_integration.handlers.lead_handlers._analyze_response_intent", new_callable=AsyncMock) as mock_intent:
                mock_intent.return_value = {
                    "intent": "purchase_interest",
                    "temperature": "hot",
                    "temperature_change": True,
                    "urgency": "high"
                }
                with patch("ghl_integration.handlers.lead_handlers._update_lead_temperature", new_callable=AsyncMock):
                    with patch("ghl_integration.handlers.lead_handlers._determine_follow_up", return_value="priority_follow_up"):
                        with patch("ghl_integration.handlers.lead_handlers._emit_lead_event", new_callable=AsyncMock):
                            
                            result = await handle_lead_response(conversation_message_payload)
                            
                            assert result["success"] is True
                            assert result["intent_analysis"]["intent"] == "purchase_interest"

    @pytest.mark.asyncio
    async def test_handle_lead_response_outbound_message(self):
        """Test that outbound messages are skipped"""
        payload = {"data": {"direction": "outbound"}}
        
        result = await handle_lead_response(payload)
        
        assert result["success"] is True
        assert "Outbound message" in result["message"]

    @pytest.mark.asyncio
    async def test_handle_lead_update_success(self, contact_update_payload):
        """Test successful lead update processing"""
        with patch("ghl_integration.handlers.lead_handlers._sync_contact_to_local", new_callable=AsyncMock):
            with patch("ghl_integration.handlers.lead_handlers._trigger_reanalysis", new_callable=AsyncMock) as mock_reanalysis:
                
                result = await handle_lead_update(contact_update_payload)
                
                assert result["success"] is True
                assert result["changes_synced"] == ["email", "tags"]
                assert result["reanalysis_triggered"] is True
                mock_reanalysis.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_lead_update_no_significant_changes(self):
        """Test update handling when no significant fields changed"""
        payload = {
            "data": {
                "id": "contact_123",
                "changes": {
                    "lastName": {"old": "Smith", "new": "Johnson"}
                }
            }
        }
        
        with patch("ghl_integration.handlers.lead_handlers._sync_contact_to_local", new_callable=AsyncMock):
            with patch("ghl_integration.handlers.lead_handlers._trigger_reanalysis") as mock_reanalysis:
                
                result = await handle_lead_update(payload)
                
                assert result["reanalysis_triggered"] is False
                mock_reanalysis.assert_not_called()

    def test_get_handler_returns_correct_handler(self):
        """Test that get_handler returns the correct handler function"""
        handler = get_handler("contact.create")
        assert handler is not None
        assert handler.__name__ == "handle_new_lead"

    def test_get_handler_unknown_event(self):
        """Test that get_handler returns None for unknown events"""
        handler = get_handler("unknown.event")
        assert handler is None


class TestLeadHelperFunctions:
    """Test helper functions for lead handlers"""

    def test_extract_address_from_custom_fields(self):
        """Test address extraction from custom fields"""
        from ghl_integration.handlers.lead_handlers import _extract_address
        
        data = {
            "customFields": {
                "property_address": "123 Main St, Rancho Cucamonga, CA"
            }
        }
        
        address = _extract_address(data)
        assert address == "123 Main St, Rancho Cucamonga, CA"

    def test_extract_address_from_message(self):
        """Test address extraction from message text"""
        from ghl_integration.handlers.lead_handlers import _extract_address
        
        data = {
            "message": "I'm interested in 456 Oak Avenue, Claremont"
        }
        
        address = _extract_address(data)
        assert "456 Oak Avenue" in address

    def test_extract_address_not_found(self):
        """Test address extraction when no address present"""
        from ghl_integration.handlers.lead_handlers import _extract_address
        
        data = {"message": "Just saying hello"}
        
        address = _extract_address(data)
        assert address is None

    @pytest.mark.asyncio
    async def test_analyze_response_intent_purchase(self):
        """Test intent analysis for purchase interest"""
        from ghl_integration.handlers.lead_handlers import _analyze_response_intent
        
        message = "I'm looking to buy a house with 3 bedrooms in Rancho Cucamonga"
        
        result = await _analyze_response_intent(message, [])
        
        assert result["intent"] == "purchase_interest"
        assert "purchase_interest" in result["intents"]

    @pytest.mark.asyncio
    async def test_analyze_response_intent_selling(self):
        """Test intent analysis for selling interest"""
        from ghl_integration.handlers.lead_handlers import _analyze_response_intent
        
        message = "I'm thinking about selling my home. What's it worth?"
        
        result = await _analyze_response_intent(message, [])
        
        assert "selling_interest" in result["intents"]

    @pytest.mark.asyncio
    async def test_analyze_response_intent_scheduling(self):
        """Test intent analysis for scheduling interest"""
        from ghl_integration.handlers.lead_handlers import _analyze_response_intent
        
        message = "Can I schedule a tour of the property this weekend?"
        
        result = await _analyze_response_intent(message, [])
        
        assert "scheduling_interest" in result["intents"]
        assert result["temperature"] == "hot"

    @pytest.mark.asyncio
    async def test_analyze_response_intent_opt_out(self):
        """Test intent analysis for opt-out"""
        from ghl_integration.handlers.lead_handlers import _analyze_response_intent
        
        message = "Please stop texting me. I'm not interested."
        
        result = await _analyze_response_intent(message, [])
        
        assert "opt_out" in result["intents"]
        assert result["temperature"] == "cold"

    def test_determine_follow_up_hot_lead(self):
        """Test follow-up determination for hot leads"""
        from ghl_integration.handlers.lead_handlers import _determine_follow_up
        
        analysis = {
            "intent": "general_inquiry",
            "temperature": "hot"
        }
        
        follow_up = _determine_follow_up("contact_123", analysis)
        assert follow_up == "priority_follow_up"

    def test_determine_follow_up_selling(self):
        """Test follow-up determination for selling interest"""
        from ghl_integration.handlers.lead_handlers import _determine_follow_up
        
        analysis = {
            "intent": "selling_interest",
            "temperature": "warm"
        }
        
        follow_up = _determine_follow_up("contact_123", analysis)
        assert follow_up == "handoff_to_seller_bot"

    def test_determine_follow_up_opt_out(self):
        """Test follow-up determination for opt-out"""
        from ghl_integration.handlers.lead_handlers import _determine_follow_up
        
        analysis = {
            "intent": "opt_out",
            "temperature": "cold"
        }
        
        follow_up = _determine_follow_up("contact_123", analysis)
        assert follow_up == "unsubscribe_workflow"
