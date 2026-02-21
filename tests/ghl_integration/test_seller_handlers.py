"""
Test Seller Bot Handlers
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from ghl_integration.handlers.seller_handlers import (
    _extract_address,
    _get_seller_pipeline_ids,
    get_handler,
    handle_listing_created,
    handle_seller_inquiry,
    handle_seller_response,
)


class TestSellerHandlers:
    """Test suite for seller bot webhook handlers"""

    @pytest.mark.asyncio
    async def test_handle_seller_inquiry_with_seller_tag(self):
        """Test handling seller inquiry with seller tag"""
        payload = {
            "data": {
                "id": "contact_seller_001",
                "name": "Jane Seller",
                "email": "jane@example.com",
                "tags": ["seller", "listing_inquiry"],
                "customFields": {"property_address": "456 Oak St, Rancho Cucamonga"},
            }
        }

        with patch("ghl_integration.handlers.seller_handlers._generate_cma", new_callable=AsyncMock) as mock_cma:
            mock_cma.return_value = {"success": True, "estimated_value": 750000}
            with patch("ghl_integration.handlers.seller_handlers._send_seller_greeting", new_callable=AsyncMock):
                with patch(
                    "ghl_integration.handlers.seller_handlers._update_ghl_seller_fields", new_callable=AsyncMock
                ):
                    with patch("ghl_integration.handlers.seller_handlers._store_seller_state", new_callable=AsyncMock):
                        with patch(
                            "ghl_integration.handlers.seller_handlers._emit_seller_event", new_callable=AsyncMock
                        ):
                            result = await handle_seller_inquiry(payload)

                            assert result["success"] is True
                            assert result["seller_state"]["cma_requested"] is True
                            mock_cma.assert_called_once_with("456 Oak St, Rancho Cucamonga", "contact_seller_001")

    @pytest.mark.asyncio
    async def test_handle_seller_inquiry_no_seller_tag(self):
        """Test that non-seller inquiries are skipped"""
        payload = {"data": {"id": "contact_001", "name": "John Buyer", "tags": ["buyer", "lead"]}}

        result = await handle_seller_inquiry(payload)

        assert result["success"] is True
        assert "Not a seller inquiry" in result["message"]

    @pytest.mark.asyncio
    async def test_handle_seller_inquiry_without_address(self):
        """Test handling seller inquiry without address"""
        payload = {
            "data": {
                "id": "contact_seller_002",
                "name": "Bob Seller",
                "email": "bob@example.com",
                "tags": ["seller"],
                "message": "I'm thinking about selling my home.",
            }
        }

        with patch(
            "ghl_integration.handlers.seller_handlers._send_seller_greeting", new_callable=AsyncMock
        ) as mock_greeting:
            with patch("ghl_integration.handlers.seller_handlers._store_seller_state", new_callable=AsyncMock):
                with patch("ghl_integration.handlers.seller_handlers._emit_seller_event", new_callable=AsyncMock):
                    result = await handle_seller_inquiry(payload)

                    assert result["success"] is True
                    assert result["seller_state"]["cma_requested"] is False
                    mock_greeting.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_listing_created_seller_pipeline(self, opportunity_create_payload):
        """Test handling listing creation in seller pipeline"""
        with patch(
            "ghl_integration.handlers.seller_handlers._get_seller_pipeline_ids", return_value=["pipeline_seller_001"]
        ):
            with patch(
                "ghl_integration.handlers.seller_handlers._get_contact_details", new_callable=AsyncMock
            ) as mock_contact:
                mock_contact.return_value = {"name": "Jane Doe", "email": "jane@example.com"}
                with patch(
                    "ghl_integration.handlers.seller_handlers._send_listing_confirmation", new_callable=AsyncMock
                ):
                    with patch("ghl_integration.handlers.seller_handlers._store_seller_state", new_callable=AsyncMock):
                        with patch(
                            "ghl_integration.handlers.seller_handlers._update_ghl_seller_fields", new_callable=AsyncMock
                        ):
                            with patch(
                                "ghl_integration.handlers.seller_handlers._emit_seller_event", new_callable=AsyncMock
                            ):
                                result = await handle_listing_created(opportunity_create_payload)

                                assert result["success"] is True
                                assert result["contact_id"] == "contact_seller_123"
                                assert result["opportunity_id"] == "opp_seller_55555"

    @pytest.mark.asyncio
    async def test_handle_listing_created_non_seller_pipeline(self):
        """Test that non-seller pipeline opportunities are skipped"""
        with patch(
            "ghl_integration.handlers.seller_handlers._get_seller_pipeline_ids", return_value=["pipeline_other"]
        ):
            payload = {
                "data": {
                    "pipelineId": "pipeline_seller_001"  # Not in the list
                }
            }

            result = await handle_listing_created(payload)

            assert result["success"] is True
            assert "Not a seller pipeline" in result["message"]

    @pytest.mark.asyncio
    async def test_handle_seller_response_success(self):
        """Test handling seller response message"""
        payload = {
            "data": {
                "contactId": "contact_seller_001",
                "message": "I need to sell within 60 days. The house is in good condition.",
                "direction": "inbound",
            }
        }

        mock_state = {"contact_id": "contact_seller_001", "qualification_stage": "Q0", "name": "Jane Seller"}

        with patch(
            "ghl_integration.handlers.seller_handlers._get_seller_state", new_callable=AsyncMock
        ) as mock_get_state:
            mock_get_state.return_value = mock_state
            with patch(
                "ghl_integration.handlers.seller_handlers._process_qualification_message", new_callable=AsyncMock
            ) as mock_process:
                mock_process.return_value = ("Q1", "Thank you! That's helpful information.", {})
                with patch("ghl_integration.handlers.seller_handlers._send_seller_message", new_callable=AsyncMock):
                    with patch(
                        "ghl_integration.handlers.seller_handlers._store_seller_state", new_callable=AsyncMock
                    ) as mock_store:
                        with patch(
                            "ghl_integration.handlers.seller_handlers._update_ghl_seller_fields", new_callable=AsyncMock
                        ):
                            with patch(
                                "ghl_integration.handlers.seller_handlers._emit_seller_event", new_callable=AsyncMock
                            ):
                                result = await handle_seller_response(payload)

                                assert result["success"] is True
                                assert result["stage"] == "Q1"
                                mock_process.assert_called_once()
                                mock_store.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_seller_response_no_state(self):
        """Test handling response when no state exists (initializes new)"""
        payload = {
            "data": {
                "contactId": "contact_seller_new",
                "message": "Hi, I'm interested in selling.",
                "direction": "inbound",
            }
        }

        with patch("ghl_integration.handlers.seller_handlers._get_seller_state", return_value=None):
            with patch(
                "ghl_integration.handlers.seller_handlers._initialize_seller_from_contact", new_callable=AsyncMock
            ) as mock_init:
                mock_init.return_value = {"contact_id": "contact_seller_new", "qualification_stage": "Q0"}
                with patch(
                    "ghl_integration.handlers.seller_handlers._process_qualification_message", new_callable=AsyncMock
                ) as mock_process:
                    mock_process.return_value = ("Q0", "Hello! I'd be happy to help you sell your home.", {})
                    with patch("ghl_integration.handlers.seller_handlers._send_seller_message", new_callable=AsyncMock):
                        with patch(
                            "ghl_integration.handlers.seller_handlers._store_seller_state", new_callable=AsyncMock
                        ):
                            with patch(
                                "ghl_integration.handlers.seller_handlers._update_ghl_seller_fields",
                                new_callable=AsyncMock,
                            ):
                                result = await handle_seller_response(payload)

                                assert result["success"] is True
                                mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_seller_response_outbound(self):
        """Test that outbound messages are skipped"""
        payload = {
            "data": {"contactId": "contact_seller_001", "message": "Thanks for your message!", "direction": "outbound"}
        }

        result = await handle_seller_response(payload)

        assert result["success"] is True
        assert "Outbound message" in result["message"]

    def test_get_handler_returns_correct_handler(self):
        """Test that get_handler returns correct functions"""
        inquiry_handler = get_handler("contact.create")
        listing_handler = get_handler("opportunity.create")
        response_handler = get_handler("conversation.message.created")

        assert inquiry_handler is not None
        assert inquiry_handler.__name__ == "handle_seller_inquiry"
        assert listing_handler.__name__ == "handle_listing_created"
        assert response_handler.__name__ == "handle_seller_response"


class TestSellerHelperFunctions:
    """Test helper functions for seller handlers"""

    def test_extract_address_from_custom_fields(self):
        """Test address extraction from custom fields"""
        data = {"customFields": {"property_address": "123 Main St"}}

        address = _extract_address(data)
        assert address == "123 Main St"

    def test_extract_address_from_message(self):
        """Test address extraction from message text"""
        data = {"message": "I live at 456 Oak Avenue in Rancho Cucamonga"}

        address = _extract_address(data)
        assert "456 Oak Avenue" in address

    def test_extract_address_not_found(self):
        """Test address extraction when not found"""
        data = {"customFields": {}}

        address = _extract_address(data)
        assert address is None

    def test_get_seller_pipeline_ids_from_env(self):
        """Test getting seller pipeline IDs from environment"""
        import os

        with patch.dict(os.environ, {"GHL_SELLER_PIPELINE_IDS": "pipe1,pipe2,pipe3"}):
            ids = _get_seller_pipeline_ids()
            assert ids == ["pipe1", "pipe2", "pipe3"]

    def test_get_seller_pipeline_ids_empty(self):
        """Test getting seller pipeline IDs when not configured"""
        import os

        with patch.dict(os.environ, {}, clear=True):
            ids = _get_seller_pipeline_ids()
            assert ids == []
