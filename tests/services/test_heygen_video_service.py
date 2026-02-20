import pytest

pytestmark = pytest.mark.integration

"""Tests for HeyGen Video Personalization Service."""

from unittest.mock import patch

import pytest

from ghl_real_estate_ai.services.heygen_video_service import (
    HeyGenVideoService,
    VideoResult,
    VideoStatus,
    VideoTemplate,
)


@pytest.fixture
def service():
    return HeyGenVideoService(api_key=None)  # mock mode


@pytest.fixture
def buyer_profile():
    return {
        "temperature": "warm",
        "area": "Victoria Gardens",
        "bedrooms": "4",
        "budget": "$750,000",
        "persona": "family",
        "features": "open floor plan and large backyard",
    }


# -------------------------------------------------------------------------
# Video creation
# -------------------------------------------------------------------------


class TestVideoCreation:
    @pytest.mark.asyncio
    async def test_create_buyer_welcome(self, service, buyer_profile):
        result = await service.create_personalized_video(
            lead_id="l_1",
            lead_name="Sarah",
            lead_profile=buyer_profile,
            template="buyer_welcome",
        )
        assert isinstance(result, VideoResult)
        assert result.status == VideoStatus.COMPLETED
        assert result.cost == 0.15
        assert "mock.heygen.com" in result.video_url

    @pytest.mark.asyncio
    async def test_create_seller_cma(self, service):
        profile = {"address": "456 Haven Ave", "market_trend": "rising fast", "avg_price": "$820,000"}
        result = await service.create_personalized_video(
            lead_id="l_2",
            lead_name="Mike",
            lead_profile=profile,
            template="seller_cma",
        )
        assert result.status == VideoStatus.COMPLETED
        assert result.lead_id == "l_2"

    @pytest.mark.asyncio
    async def test_unknown_template_defaults_buyer_welcome(self, service, buyer_profile):
        result = await service.create_personalized_video(
            lead_id="l_3",
            lead_name="Tom",
            lead_profile=buyer_profile,
            template="nonexistent_template",
        )
        assert result.status == VideoStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_video_has_unique_request_id(self, service, buyer_profile):
        r1 = await service.create_personalized_video("l_a", "A", buyer_profile)
        r2 = await service.create_personalized_video("l_b", "B", buyer_profile)
        assert r1.request_id != r2.request_id


# -------------------------------------------------------------------------
# Script generation
# -------------------------------------------------------------------------


class TestScriptGeneration:
    def test_buyer_welcome_personalised(self, service, buyer_profile):
        script = service._generate_script(VideoTemplate.BUYER_WELCOME, "Sarah", buyer_profile, {})
        assert "Sarah" in script.personalized_text
        assert "Victoria Gardens" in script.personalized_text

    def test_family_psychographic_hook(self, service):
        profile = {"persona": "family", "bedrooms": "4"}
        script = service._generate_script(VideoTemplate.BUYER_WELCOME, "Jen", profile, {})
        assert "family" in script.personalized_text.lower() or "schools" in script.personalized_text.lower()

    def test_duration_estimate_reasonable(self, service, buyer_profile):
        script = service._generate_script(VideoTemplate.BUYER_WELCOME, "Sarah", buyer_profile, {})
        assert 10 <= script.duration_estimate_sec <= 120

    def test_custom_variables_override(self, service, buyer_profile):
        script = service._generate_script(
            VideoTemplate.BUYER_WELCOME,
            "Sarah",
            buyer_profile,
            {"area": "Etiwanda"},
        )
        assert "Etiwanda" in script.personalized_text


# -------------------------------------------------------------------------
# Cost management
# -------------------------------------------------------------------------


class TestCostManagement:
    @pytest.mark.asyncio
    async def test_cost_tracked(self, service, buyer_profile):
        await service.create_personalized_video("l_c", "Cost Test", buyer_profile)
        summary = service.get_cost_summary()
        assert summary["total_videos"] == 1
        assert summary["total_cost"] == 0.15

    @pytest.mark.asyncio
    async def test_budget_exceeded_blocks_video(self, service, buyer_profile):
        service._cost_tracker.daily_budget = 0.10
        service._cost_tracker.daily_spent = 0.10
        result = await service.create_personalized_video("l_d", "Budget", buyer_profile)
        assert result.status == VideoStatus.FAILED
        assert result.cost == 0.0

    @pytest.mark.asyncio
    async def test_cost_per_video_avg(self, service, buyer_profile):
        for i in range(3):
            await service.create_personalized_video(f"l_{i}", f"Test {i}", buyer_profile)
        summary = service.get_cost_summary()
        assert summary["cost_per_video_avg"] == 0.15


# -------------------------------------------------------------------------
# Delivery tracking
# -------------------------------------------------------------------------


class TestDeliveryTracking:
    @pytest.mark.asyncio
    async def test_mark_delivered(self, service, buyer_profile):
        result = await service.create_personalized_video("l_e", "Del", buyer_profile)
        assert await service.mark_delivered(result.request_id)
        updated = await service.get_video_status(result.request_id)
        assert updated.status == VideoStatus.DELIVERED

    @pytest.mark.asyncio
    async def test_record_view(self, service, buyer_profile):
        result = await service.create_personalized_video("l_f", "View", buyer_profile)
        await service.record_view(result.request_id)
        await service.record_view(result.request_id)
        updated = await service.get_video_status(result.request_id)
        assert updated.view_count == 2
        assert updated.engagement_score > 0

    @pytest.mark.asyncio
    async def test_nonexistent_video_returns_none(self, service):
        assert await service.get_video_status("fake_id") is None

    @pytest.mark.asyncio
    async def test_mark_delivered_fake_returns_false(self, service):
        assert not await service.mark_delivered("fake_id")


# -------------------------------------------------------------------------
# Lead videos
# -------------------------------------------------------------------------


class TestLeadVideos:
    @pytest.mark.asyncio
    async def test_get_lead_videos(self, service, buyer_profile):
        await service.create_personalized_video("l_g", "V1", buyer_profile)
        await service.create_personalized_video("l_g", "V2", buyer_profile)
        await service.create_personalized_video("l_h", "V3", buyer_profile)
        videos = service.get_lead_videos("l_g")
        assert len(videos) == 2