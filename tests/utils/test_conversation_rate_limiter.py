"""Tests for per-contact conversation rate limiter."""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch

import pytest

from ghl_real_estate_ai.utils.conversation_rate_limiter import (
    ConversationRateLimiter,
    RateLimitResult,
)


@pytest.fixture
def limiter():
    """Create a limiter with small limits for testing."""
    return ConversationRateLimiter(
        max_per_minute=2,
        max_per_hour=5,
        max_per_day=10,
    )


class TestConversationRateLimiter:
    """Tests for ConversationRateLimiter."""

    def test_under_limit_allowed(self, limiter: ConversationRateLimiter):
        """First message for a contact should always be allowed."""
        result = limiter.check_rate_limit("contact_1")

        assert result.allowed is True
        assert result.retry_after_seconds is None
        assert result.limit_type is None

    def test_minute_limit_blocks(self, limiter: ConversationRateLimiter):
        """Exceeding max_per_minute should block the contact."""
        # Record 2 interactions (the limit)
        limiter.record_interaction("contact_1")
        limiter.record_interaction("contact_1")

        # Third check should be blocked
        result = limiter.check_rate_limit("contact_1")

        assert result.allowed is False
        assert result.limit_type == "minute"
        assert result.retry_after_seconds is not None
        assert result.retry_after_seconds > 0

    def test_hour_limit_blocks(self, limiter: ConversationRateLimiter):
        """Exceeding max_per_hour should block the contact."""
        now = time.time()

        # Place 5 interactions spread across the last hour (outside the minute window)
        with patch("time.time") as mock_time:
            for i in range(5):
                # Space them 5 minutes apart, starting 25 min ago
                mock_time.return_value = now - (25 * 60) + (i * 5 * 60)
                limiter.record_interaction("contact_1")

        # Now check at current time -- minute window has 0, hour window has 5
        result = limiter.check_rate_limit("contact_1")

        assert result.allowed is False
        assert result.limit_type == "hour"

    def test_different_contacts_independent(self, limiter: ConversationRateLimiter):
        """Contact A's rate limit should not affect contact B."""
        # Max out contact A
        limiter.record_interaction("contact_a")
        limiter.record_interaction("contact_a")

        # Contact A should be blocked
        result_a = limiter.check_rate_limit("contact_a")
        assert result_a.allowed is False

        # Contact B should still be allowed
        result_b = limiter.check_rate_limit("contact_b")
        assert result_b.allowed is True

    def test_expired_entries_cleaned(self, limiter: ConversationRateLimiter):
        """Timestamps older than 24 hours should be cleaned up and not count."""
        now = time.time()

        # Directly inject old timestamps (>24h ago) into the deque
        old_time = now - 90000  # ~25 hours ago
        limiter._interactions["contact_1"].append(old_time)
        limiter._interactions["contact_1"].append(old_time + 1)

        # Check should clean up old entries and allow
        result = limiter.check_rate_limit("contact_1")

        assert result.allowed is True
        # The old entries should have been cleaned out
        assert "contact_1" not in limiter._interactions

    def test_retry_after_seconds(self, limiter: ConversationRateLimiter):
        """retry_after_seconds should be a positive integer when rate limited."""
        limiter.record_interaction("contact_1")
        limiter.record_interaction("contact_1")

        result = limiter.check_rate_limit("contact_1")

        assert result.allowed is False
        assert isinstance(result.retry_after_seconds, int)
        assert result.retry_after_seconds >= 1
        # Should be no more than 61 seconds for a minute-level limit
        assert result.retry_after_seconds <= 61

    def test_thread_safety(self, limiter: ConversationRateLimiter):
        """Concurrent access from multiple threads should not raise exceptions."""
        errors = []

        def worker(thread_id: int):
            try:
                contact = f"contact_{thread_id % 3}"
                for _ in range(20):
                    limiter.check_rate_limit(contact)
                    limiter.record_interaction(contact)
            except Exception as exc:
                errors.append(exc)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker, i) for i in range(10)]
            for future in as_completed(futures):
                future.result()  # Re-raises any exception from the thread

        assert len(errors) == 0, f"Thread safety errors: {errors}"