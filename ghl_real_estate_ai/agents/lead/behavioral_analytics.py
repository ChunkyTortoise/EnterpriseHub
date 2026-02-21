"""
Behavioral Analytics Engine for analyzing lead behavior patterns.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List

from ghl_real_estate_ai.agents.lead.cache import TTLLRUCache
from ghl_real_estate_ai.agents.lead.config import ResponsePattern, SequenceOptimization
from ghl_real_estate_ai.agents.lead.constants import (
    DEFAULT_BEST_CONTACT_TIMES,
    DEFAULT_CHANNEL_PREFS,
)
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class BehavioralAnalyticsEngine:
    """
    Analyzes lead behavior patterns for predictive optimization.

    Uses TTL-aware LRU cache to prevent unbounded memory growth:
    - Max 1000 entries to limit memory usage
    - 60 minute TTL to ensure fresh analysis
    - LRU eviction when capacity reached
    """

    # Class-level cache configuration constants
    CACHE_MAX_ENTRIES = 1000
    CACHE_TTL_SECONDS = 3600  # 60 minutes

    def __init__(self):
        self._patterns_cache = TTLLRUCache(max_entries=self.CACHE_MAX_ENTRIES, ttl_seconds=self.CACHE_TTL_SECONDS)
        logger.info(
            f"BehavioralAnalyticsEngine initialized with TTL cache "
            f"(max_entries={self.CACHE_MAX_ENTRIES}, ttl={self.CACHE_TTL_SECONDS}s)"
        )

    async def analyze_response_patterns(self, lead_id: str, conversation_history: List[Dict]) -> ResponsePattern:
        """
        Analyze lead's response patterns for optimization.

        Uses TTL-aware LRU cache to:
        - Return cached patterns if available and fresh (< 60 min)
        - Evict stale patterns automatically
        - Prevent unbounded memory growth
        """
        # Check cache first (handles TTL expiration automatically)
        cached_pattern = self._patterns_cache.get(lead_id)
        if cached_pattern is not None:
            logger.debug(f"Cache hit for lead {lead_id} response pattern")
            return cached_pattern

        logger.debug(f"Cache miss for lead {lead_id}, computing response pattern")

        # Calculate response velocity using actual timestamps
        response_times = []
        for i in range(1, len(conversation_history)):
            current_msg = conversation_history[i]
            prev_msg = conversation_history[i - 1]

            # Real timestamp analysis using conversation timestamps
            if current_msg.get("role") == "user" and prev_msg.get("role") == "assistant":
                current_ts = current_msg.get("timestamp")
                prev_ts = prev_msg.get("timestamp")

                if current_ts and prev_ts:
                    try:
                        # Parse timestamps (support ISO format and Unix timestamps)
                        if isinstance(current_ts, (int, float)):
                            current_dt = datetime.fromtimestamp(current_ts, tz=timezone.utc)
                        else:
                            current_dt = datetime.fromisoformat(str(current_ts).replace("Z", "+00:00"))

                        if isinstance(prev_ts, (int, float)):
                            prev_dt = datetime.fromtimestamp(prev_ts, tz=timezone.utc)
                        else:
                            prev_dt = datetime.fromisoformat(str(prev_ts).replace("Z", "+00:00"))

                        # Calculate hours between messages
                        delta_hours = (current_dt - prev_dt).total_seconds() / 3600
                        if delta_hours > 0:  # Only count positive deltas
                            response_times.append(delta_hours)
                    except (ValueError, TypeError) as e:
                        logger.debug(f"Could not parse timestamps for lead {lead_id}: {e}")
                        # Fallback to default if timestamp parsing fails
                        response_times.append(4.5)

        avg_response_hours = sum(response_times) / len(response_times) if response_times else 24.0

        # Determine engagement velocity
        if avg_response_hours < 2:
            velocity = "fast"
        elif avg_response_hours < 12:
            velocity = "moderate"
        else:
            velocity = "slow"

        # Analyze channel preferences from GHL contact data
        channel_prefs = await self._get_channel_preferences(lead_id, conversation_history)

        # Analyze message length preference
        avg_msg_length = sum(len(m.get("content", "").split()) for m in conversation_history if m.get("role") == "user")
        avg_msg_length = avg_msg_length / max(1, len([m for m in conversation_history if m.get("role") == "user"]))

        length_pref = "brief" if avg_msg_length < 10 else "detailed"

        # Calculate best contact times from engagement patterns
        best_times = self._calculate_best_contact_times(conversation_history)

        pattern = ResponsePattern(
            avg_response_hours=avg_response_hours,
            response_count=len([m for m in conversation_history if m.get("role") == "user"]),
            channel_preferences=channel_prefs,
            engagement_velocity=velocity,
            best_contact_times=best_times,
            message_length_preference=length_pref,
        )

        # Store in cache (handles LRU eviction automatically)
        self._patterns_cache.set(lead_id, pattern)
        return pattern

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        return self._patterns_cache.get_stats()

    def cleanup_stale_patterns(self) -> int:
        """Manually trigger cleanup of expired patterns."""
        return self._patterns_cache.cleanup_expired()

    async def _get_channel_preferences(self, lead_id: str, conversation_history: List[Dict]) -> Dict[str, float]:
        """
        Get channel preferences from GHL contact data or infer from conversation history.

        Returns:
            Dict mapping channel names to preference scores (0.0-1.0)
        """
        channel_prefs = DEFAULT_CHANNEL_PREFS.copy()

        try:
            # Try to fetch contact preferences from GHL
            from ghl_real_estate_ai.services.enhanced_ghl_client import EnhancedGHLClient

            async with EnhancedGHLClient() as ghl_client:
                contact = await ghl_client.get_contact(lead_id)
                if contact:
                    # Extract channel preferences from contact custom fields
                    custom_fields = getattr(contact, "custom_fields", {}) or {}

                    # Check for explicit channel preferences
                    if custom_fields.get("preferred_channel"):
                        preferred = custom_fields["preferred_channel"].upper()
                        if preferred in channel_prefs:
                            channel_prefs[preferred] = 0.9

                    # Check DND (Do Not Disturb) settings
                    if getattr(contact, "dnd", False):
                        channel_prefs["Voice"] = 0.1

                    # Check email opt-out
                    if getattr(contact, "email_opt_out", False):
                        channel_prefs["Email"] = 0.0

                    # Check SMS opt-out
                    if getattr(contact, "sms_opt_out", False):
                        channel_prefs["SMS"] = 0.0

        except Exception as e:
            logger.debug(f"Could not fetch GHL contact preferences for {lead_id}: {e}")

        # Infer preferences from conversation history
        channel_counts = {"SMS": 0, "Email": 0, "Voice": 0, "WhatsApp": 0}
        for msg in conversation_history:
            channel = msg.get("channel", "").upper()
            if channel in channel_counts:
                channel_counts[channel] += 1

        total_messages = sum(channel_counts.values())
        if total_messages > 0:
            for channel, count in channel_counts.items():
                # Blend GHL preferences with observed behavior (70% observed, 30% GHL)
                observed_pref = count / total_messages
                channel_prefs[channel] = 0.7 * observed_pref + 0.3 * channel_prefs[channel]

        return channel_prefs

    def _calculate_best_contact_times(self, conversation_history: List[Dict]) -> List[int]:
        """
        Calculate best contact times based on engagement patterns.

        Analyzes when the lead typically responds to determine optimal contact hours.

        Returns:
            List of hours (0-23) when lead is most responsive
        """
        hour_engagement = {}  # hour -> response count

        for msg in conversation_history:
            if msg.get("role") == "user":
                timestamp = msg.get("timestamp")
                if timestamp:
                    try:
                        if isinstance(timestamp, (int, float)):
                            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                        else:
                            dt = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))

                        hour = dt.hour
                        hour_engagement[hour] = hour_engagement.get(hour, 0) + 1
                    except (ValueError, TypeError):
                        continue

        if hour_engagement:
            # Sort hours by engagement count and return top 3
            sorted_hours = sorted(hour_engagement.items(), key=lambda x: x[1], reverse=True)
            best_times = [hour for hour, _ in sorted_hours[:3]]

            # Ensure we have at least 3 times, pad with business hours defaults
            default_times = [9, 14, 18]
            while len(best_times) < 3:
                for default in default_times:
                    if default not in best_times:
                        best_times.append(default)
                        break

            return best_times[:3]

        # Default to standard business hours if no engagement data
        return DEFAULT_BEST_CONTACT_TIMES

    async def predict_optimal_sequence(self, pattern: ResponsePattern) -> SequenceOptimization:
        """Predict optimal sequence timing based on behavioral patterns"""

        # Optimize intervals based on response velocity
        if pattern.engagement_velocity == "fast":
            # Accelerate sequence for fast responders
            optimization = SequenceOptimization(
                day_3=1,  # Contact tomorrow
                day_7=3,  # Contact in 3 days
                day_14=7,  # Contact in 1 week
                day_30=14,  # Contact in 2 weeks
                channel_sequence=["SMS", "Voice", "SMS", "Email"],
            )
        elif pattern.engagement_velocity == "slow":
            # Extend intervals for slow responders
            optimization = SequenceOptimization(
                day_3=5,  # Wait 5 days
                day_7=14,  # Wait 2 weeks
                day_14=21,  # Wait 3 weeks
                day_30=45,  # Wait 6+ weeks
                channel_sequence=["Email", "SMS", "Voice", "SMS"],
            )
        else:
            # Standard intervals for moderate responders
            optimization = SequenceOptimization(
                day_3=3, day_7=7, day_14=14, day_30=30, channel_sequence=["SMS", "Email", "Voice", "SMS"]
            )

        # Adjust channel sequence based on preferences
        sorted_channels = sorted(pattern.channel_preferences.items(), key=lambda x: x[1], reverse=True)
        optimization.channel_sequence = [ch[0] for ch in sorted_channels]

        return optimization
