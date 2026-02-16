"""Unit tests for GHLSyncService — temperature tagging, contact creation."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voice_ai.services.ghl_sync import GHLSyncService


@pytest.fixture
def service():
    return GHLSyncService(api_key="test_key", location_id="loc_123")


class TestTemperatureTagging:
    def test_hot_lead_score_80(self, service):
        assert service._get_temperature_tag(80) == "Hot-Lead"

    def test_hot_lead_score_100(self, service):
        assert service._get_temperature_tag(100) == "Hot-Lead"

    def test_warm_lead_score_40(self, service):
        assert service._get_temperature_tag(40) == "Warm-Lead"

    def test_warm_lead_score_79(self, service):
        assert service._get_temperature_tag(79) == "Warm-Lead"

    def test_cold_lead_score_39(self, service):
        assert service._get_temperature_tag(39) == "Cold-Lead"

    def test_cold_lead_score_0(self, service):
        assert service._get_temperature_tag(0) == "Cold-Lead"

    def test_none_score(self, service):
        assert service._get_temperature_tag(None) == "Unknown-Lead"


class TestSyncCallResult:
    @pytest.mark.asyncio
    async def test_sync_posts_tags_and_note(self, service):
        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await service.sync_call_result(
                "contact_1",
                {"lead_score": 85, "bot_type": "lead", "duration_seconds": 120},
            )

            assert result["contact_id"] == "contact_1"
            assert "Hot-Lead" in result["tags_added"]
            assert "voice-lead" in result["tags_added"]
            assert result["note_added"] is True
            assert mock_client.post.call_count == 2  # tags + note


class TestCreateContact:
    @pytest.mark.asyncio
    async def test_creates_contact_with_phone(self, service):
        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {"contact": {"id": "new_contact_123"}}
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            contact_id = await service.create_contact("+15551234567")

            assert contact_id == "new_contact_123"
            call_kwargs = mock_client.post.call_args
            payload = call_kwargs.kwargs["json"]
            assert payload["phone"] == "+15551234567"
            assert payload["source"] == "Voice AI Platform"

    @pytest.mark.asyncio
    async def test_creates_contact_with_name_and_email(self, service):
        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {"contact": {"id": "c_456"}}
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await service.create_contact("+15551234567", name="John", email="john@test.com")

            payload = mock_client.post.call_args.kwargs["json"]
            assert payload["name"] == "John"
            assert payload["email"] == "john@test.com"
