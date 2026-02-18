import pytest
pytestmark = pytest.mark.integration

"""Tests for Unified Channel Router."""

from unittest.mock import AsyncMock, patch

import pytest

from ghl_real_estate_ai.services.unified_channel_router import (

    ChannelType,
    DeliveryResult,
    DeliveryStatus,
    MessagePriority,
    UnifiedChannelRouter,
)


@pytest.fixture
def router():
    return UnifiedChannelRouter()


# -------------------------------------------------------------------------
# Basic delivery
# -------------------------------------------------------------------------


class TestBasicDelivery:
    @pytest.mark.asyncio
    async def test_send_sms_succeeds(self, router):
        result = await router.send_message(
            contact_id="c_1",
            message="Hi Sarah!",
            preferred_channel="sms",
        )
        assert result.delivery_status == DeliveryStatus.SENT
        assert result.channel_used == ChannelType.SMS
        assert result.compliance_status != "BLOCKED"

    @pytest.mark.asyncio
    async def test_send_email(self, router):
        result = await router.send_message(
            contact_id="c_2",
            message="Detailed property report...",
            preferred_channel="email",
        )
        assert result.channel_used == ChannelType.EMAIL

    @pytest.mark.asyncio
    async def test_unknown_channel_defaults_sms(self, router):
        result = await router.send_message(
            contact_id="c_3",
            message="Hello",
            preferred_channel="carrier_pigeon",
        )
        assert result.channel_used == ChannelType.SMS

    @pytest.mark.asyncio
    async def test_each_message_gets_unique_id(self, router):
        r1 = await router.send_message("c_a", "msg1")
        r2 = await router.send_message("c_b", "msg2")
        assert r1.message_id != r2.message_id


# -------------------------------------------------------------------------
# Compliance blocking
# -------------------------------------------------------------------------


class TestCompliance:
    @pytest.mark.asyncio
    async def test_blocked_message_not_delivered(self, router):
        with patch(
            "ghl_real_estate_ai.services.unified_channel_router.UnifiedChannelRouter._check_compliance",
            new_callable=AsyncMock,
            return_value="BLOCKED",
        ):
            result = await router.send_message("c_4", "This is a safe neighborhood")
            assert result.delivery_status == DeliveryStatus.BLOCKED
            assert result.compliance_status == "BLOCKED"
            assert result.error is not None

    @pytest.mark.asyncio
    async def test_passed_message_delivered(self, router):
        with patch(
            "ghl_real_estate_ai.services.unified_channel_router.UnifiedChannelRouter._check_compliance",
            new_callable=AsyncMock,
            return_value="PASSED",
        ):
            result = await router.send_message("c_5", "Normal message")
            assert result.delivery_status == DeliveryStatus.SENT


# -------------------------------------------------------------------------
# SMS formatting
# -------------------------------------------------------------------------


class TestSMSFormatting:
    @pytest.mark.asyncio
    async def test_long_sms_truncated(self, router):
        long_msg = "A" * 400
        result = await router.send_message("c_6", long_msg, preferred_channel="sms")
        assert result.delivery_status == DeliveryStatus.SENT

    def test_format_sms_under_limit(self, router):
        formatted = router._format_for_channel("Short msg", ChannelType.SMS)
        assert formatted == "Short msg"

    def test_format_sms_over_limit(self, router):
        long_msg = "X" * 400
        formatted = router._format_for_channel(long_msg, ChannelType.SMS)
        assert len(formatted) <= 320

    def test_format_voice_strips_markdown(self, router):
        formatted = router._format_for_channel("**Bold** and *italic*", ChannelType.VOICE)
        assert "**" not in formatted
        assert "*" not in formatted


# -------------------------------------------------------------------------
# Fallback routing
# -------------------------------------------------------------------------


class TestFallback:
    @pytest.mark.asyncio
    async def test_fallback_on_handler_failure(self, router):
        async def failing_handler(cid, msg, ch):
            raise ConnectionError("SMS gateway down")

        async def success_handler(cid, msg, ch):
            pass

        router.register_channel_handler("sms", failing_handler)
        router.register_channel_handler("email", success_handler)

        result = await router.send_message("c_7", "Please deliver this")
        assert result.delivery_status == DeliveryStatus.FALLBACK
        assert result.fallback_channel == ChannelType.EMAIL

    @pytest.mark.asyncio
    async def test_all_fallbacks_fail(self, router):
        async def failing_handler(cid, msg, ch):
            raise ConnectionError("All down")

        router.register_channel_handler("sms", failing_handler)
        router.register_channel_handler("email", failing_handler)
        router.register_channel_handler("chat", failing_handler)

        result = await router.send_message("c_8", "No delivery possible")
        assert result.delivery_status == DeliveryStatus.FAILED


# -------------------------------------------------------------------------
# Channel preference learning
# -------------------------------------------------------------------------


class TestPreferenceLearning:
    @pytest.mark.asyncio
    async def test_preference_updated_on_delivery(self, router):
        await router.send_message("c_9", "First", preferred_channel="sms")
        await router.send_message("c_9", "Second", preferred_channel="sms")
        pref = await router.get_channel_preference("c_9")
        assert pref == ChannelType.SMS

    @pytest.mark.asyncio
    async def test_no_preference_for_unknown_contact(self, router):
        pref = await router.get_channel_preference("unknown")
        assert pref is None

    @pytest.mark.asyncio
    async def test_urgent_overrides_preference(self, router):
        # Build preference for email
        for _ in range(5):
            await router.send_message("c_10", "Email pref", preferred_channel="email")

        result = await router.send_message("c_10", "Urgent!", preferred_channel="sms", priority="urgent")
        assert result.channel_used == ChannelType.SMS


# -------------------------------------------------------------------------
# Analytics
# -------------------------------------------------------------------------


class TestAnalytics:
    @pytest.mark.asyncio
    async def test_analytics_counts(self, router):
        await router.send_message("c_11", "M1", preferred_channel="sms")
        await router.send_message("c_12", "M2", preferred_channel="email")
        analytics = await router.get_analytics()
        assert analytics.total_messages == 2
        assert analytics.messages_by_channel.get("sms", 0) == 1
        assert analytics.messages_by_channel.get("email", 0) == 1

    @pytest.mark.asyncio
    async def test_delivery_rate(self, router):
        await router.send_message("c_13", "M1")
        await router.send_message("c_14", "M2")
        analytics = await router.get_analytics()
        assert analytics.delivery_rate == 1.0

    @pytest.mark.asyncio
    async def test_compliance_block_rate(self, router):
        with patch(
            "ghl_real_estate_ai.services.unified_channel_router.UnifiedChannelRouter._check_compliance",
            new_callable=AsyncMock,
            return_value="BLOCKED",
        ):
            await router.send_message("c_15", "Blocked msg")
        await router.send_message("c_16", "Normal msg")
        analytics = await router.get_analytics()
        assert analytics.compliance_block_rate == 0.5

    @pytest.mark.asyncio
    async def test_clear_analytics(self, router):
        await router.send_message("c_17", "M1")
        router.clear_analytics()
        analytics = await router.get_analytics()
        assert analytics.total_messages == 0

    @pytest.mark.asyncio
    async def test_empty_analytics(self, router):
        analytics = await router.get_analytics()
        assert analytics.total_messages == 0


# -------------------------------------------------------------------------
# Channel handler registration
# -------------------------------------------------------------------------


class TestHandlerRegistration:
    @pytest.mark.asyncio
    async def test_custom_handler_called(self, router):
        called = []

        async def track_handler(cid, msg, ch):
            called.append((cid, msg, ch))

        router.register_channel_handler("sms", track_handler)
        await router.send_message("c_18", "Track me")
        assert len(called) == 1
        assert called[0][0] == "c_18"