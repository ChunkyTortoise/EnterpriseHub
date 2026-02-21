"""Per-contact conversation rate limiter to prevent spam/abuse."""

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Optional


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""

    allowed: bool
    retry_after_seconds: Optional[int] = None
    limit_type: Optional[str] = None  # "minute", "hour", "day"


class ConversationRateLimiter:
    """Thread-safe per-contact rate limiter using sliding window counters.

    Uses deques of timestamps to track interactions per contact.
    Cleanup runs automatically on each check to prevent memory growth.
    """

    def __init__(
        self,
        max_per_minute: int = 5,
        max_per_hour: int = 30,
        max_per_day: int = 200,
    ):
        self.max_per_minute = max_per_minute
        self.max_per_hour = max_per_hour
        self.max_per_day = max_per_day
        self._interactions: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def check_rate_limit(self, contact_id: str) -> RateLimitResult:
        """Check if a contact is within rate limits. Does NOT record the interaction."""
        now = time.time()
        with self._lock:
            self._cleanup_expired(contact_id, now)
            timestamps = self._interactions.get(contact_id)

            # No interactions recorded (or all expired) — always allowed
            if not timestamps:
                return RateLimitResult(allowed=True)

            # Check minute limit
            minute_ago = now - 60
            minute_count = sum(1 for t in timestamps if t > minute_ago)
            if minute_count >= self.max_per_minute:
                oldest_in_window = min((t for t in timestamps if t > minute_ago), default=now)
                retry_after = int(oldest_in_window + 60 - now) + 1
                return RateLimitResult(
                    allowed=False,
                    retry_after_seconds=max(1, retry_after),
                    limit_type="minute",
                )

            # Check hour limit
            hour_ago = now - 3600
            hour_count = sum(1 for t in timestamps if t > hour_ago)
            if hour_count >= self.max_per_hour:
                oldest_in_window = min((t for t in timestamps if t > hour_ago), default=now)
                retry_after = int(oldest_in_window + 3600 - now) + 1
                return RateLimitResult(
                    allowed=False,
                    retry_after_seconds=max(1, retry_after),
                    limit_type="hour",
                )

            # Check day limit
            day_ago = now - 86400
            day_count = sum(1 for t in timestamps if t > day_ago)
            if day_count >= self.max_per_day:
                oldest_in_window = min((t for t in timestamps if t > day_ago), default=now)
                retry_after = int(oldest_in_window + 86400 - now) + 1
                return RateLimitResult(
                    allowed=False,
                    retry_after_seconds=max(1, retry_after),
                    limit_type="day",
                )

            return RateLimitResult(allowed=True)

    def record_interaction(self, contact_id: str) -> None:
        """Record a new interaction timestamp for a contact."""
        now = time.time()
        with self._lock:
            self._interactions[contact_id].append(now)

    def _cleanup_expired(self, contact_id: str, now: float) -> None:
        """Remove timestamps older than 24 hours for a contact."""
        cutoff = now - 86400
        timestamps = self._interactions[contact_id]
        while timestamps and timestamps[0] < cutoff:
            timestamps.popleft()
        # Remove empty entries
        if not timestamps and contact_id in self._interactions:
            del self._interactions[contact_id]
