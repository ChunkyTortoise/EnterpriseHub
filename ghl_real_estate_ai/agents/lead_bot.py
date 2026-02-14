import asyncio
import threading
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple
from uuid import uuid4

from langgraph.graph import END, StateGraph

from ghl_real_estate_ai.agents.cma_generator import CMAGenerator
from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder
from ghl_real_estate_ai.api.schemas.ghl import MessageType
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.integrations.lyrio import LyrioClient
from ghl_real_estate_ai.integrations.retell import RetellClient
from ghl_real_estate_ai.models.bot_context_types import (
    BotMetadata,
    ConversationMessage,
)
from ghl_real_estate_ai.models.workflows import LeadFollowUpState
from ghl_real_estate_ai.services.agent_state_sync import sync_service
from ghl_real_estate_ai.services.cache_service import CacheService
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.services.ghost_followup_engine import GhostState, get_ghost_followup_engine
from ghl_real_estate_ai.services.jorge.ab_testing_service import ABTestingService
from ghl_real_estate_ai.services.jorge.alerting_service import AlertingService
from ghl_real_estate_ai.services.jorge.bot_metrics_collector import BotMetricsCollector
from ghl_real_estate_ai.services.jorge.performance_tracker import PerformanceTracker
from ghl_real_estate_ai.services.lead_sequence_scheduler import get_lead_scheduler
from ghl_real_estate_ai.services.lead_sequence_state_service import (
    LeadSequenceState,
    SequenceDay,
    SequenceStatus,
    get_sequence_service,
)
from ghl_real_estate_ai.utils.pdf_renderer import PDFGenerationError, PDFRenderer

# Enhanced Features (Track 3.1 Integration)
try:
    from bots.shared.ml_analytics_engine import (
        ConversionProbabilityAnalysis,
        LeadJourneyPrediction,
        MLAnalyticsEngine,
        TouchpointOptimization,
    )

    TRACK3_ML_AVAILABLE = True
except ImportError:
    TRACK3_ML_AVAILABLE = False

logger = get_logger(__name__)

# Phase 3.3 Bot Intelligence Middleware Integration
try:
    from ghl_real_estate_ai.models.intelligence_context import BotIntelligenceContext
    from ghl_real_estate_ai.services.bot_intelligence_middleware import get_bot_intelligence_middleware

    BOT_INTELLIGENCE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Bot Intelligence Middleware unavailable: {e}")
    BOT_INTELLIGENCE_AVAILABLE = False

# ================================
# ENHANCED FEATURES DATACLASSES
# ================================


@dataclass
class ResponsePattern:
    """Tracks lead response patterns for optimization"""

    avg_response_hours: float
    response_count: int
    channel_preferences: Dict[str, float]  # SMS, Email, Voice, WhatsApp
    engagement_velocity: str  # "fast", "moderate", "slow"
    best_contact_times: List[int]  # Hours of day (0-23)
    message_length_preference: str  # "brief", "detailed"


@dataclass
class SequenceOptimization:
    """Optimized sequence timing based on behavioral patterns"""

    day_3: int
    day_7: int
    day_14: int
    day_30: int
    channel_sequence: List[str]  # Ordered list of channels to use


@dataclass
class LeadBotConfig:
    """Configuration for Lead Bot enhanced features"""

    enable_predictive_analytics: bool = False
    enable_behavioral_optimization: bool = False
    enable_personality_adaptation: bool = False
    enable_track3_intelligence: bool = False
    enable_bot_intelligence: bool = False

    # Performance settings
    default_sequence_timing: bool = True
    personality_detection_enabled: bool = True
    jorge_handoff_enabled: bool = True


class TTLLRUCache:
    """
    Thread-safe LRU cache with TTL (Time-To-Live) support.

    Features:
    - Maximum entry limit to prevent unbounded memory growth
    - TTL-based expiration for stale data eviction
    - LRU eviction when max entries reached
    - Thread-safe operations
    """

    def __init__(self, max_entries: int = 1000, ttl_seconds: int = 3600):
        """
        Initialize TTL-aware LRU cache.

        Args:
            max_entries: Maximum number of entries (default: 1000)
            ttl_seconds: Time-to-live in seconds (default: 3600 = 60 minutes)
        """
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._max_entries = max_entries
        self._ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions_ttl": 0,
            "evictions_lru": 0,
        }

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if exists and not expired.

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return None

            value, timestamp = self._cache[key]
            current_time = datetime.now().timestamp()

            # Check if expired
            if current_time - timestamp > self._ttl_seconds:
                del self._cache[key]
                self._stats["evictions_ttl"] += 1
                self._stats["misses"] += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._stats["hits"] += 1
            return value

    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache with current timestamp.

        Evicts LRU entries if max_entries exceeded.
        """
        with self._lock:
            current_time = datetime.now().timestamp()

            # If key exists, update and move to end
            if key in self._cache:
                self._cache[key] = (value, current_time)
                self._cache.move_to_end(key)
                return

            # Evict oldest entries if at capacity
            while len(self._cache) >= self._max_entries:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats["evictions_lru"] += 1
                logger.debug(f"LRU eviction: {oldest_key} (cache size: {len(self._cache)})")

            # Add new entry
            self._cache[key] = (value, current_time)

    def contains(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None

    def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all entries from cache."""
        with self._lock:
            self._cache.clear()

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        with self._lock:
            current_time = datetime.now().timestamp()
            expired_keys = [
                key for key, (_, timestamp) in self._cache.items() if current_time - timestamp > self._ttl_seconds
            ]
            for key in expired_keys:
                del self._cache[key]
                self._stats["evictions_ttl"] += 1

            if expired_keys:
                logger.debug(f"TTL cleanup: removed {len(expired_keys)} expired entries")

            return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0.0
            return {
                "size": len(self._cache),
                "max_entries": self._max_entries,
                "ttl_seconds": self._ttl_seconds,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "hit_rate": hit_rate,
                "evictions_ttl": self._stats["evictions_ttl"],
                "evictions_lru": self._stats["evictions_lru"],
            }

    def __len__(self) -> int:
        """Return number of entries in cache."""
        with self._lock:
            return len(self._cache)


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
        channel_prefs = {"SMS": 0.5, "Email": 0.5, "Voice": 0.5, "WhatsApp": 0.3}

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
        return [9, 14, 18]

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


class PersonalityAdapter:
    """Adapts messaging based on lead personality and preferences"""

    def __init__(self):
        self.personality_profiles = {
            "analytical": {
                "style": "data-driven",
                "tone": "professional",
                "format": "bullet points",
                "keywords": ["analysis", "data", "research", "comparison"],
            },
            "relationship": {
                "style": "personal",
                "tone": "warm",
                "format": "conversational",
                "keywords": ["understand", "help", "partnership", "together"],
            },
            "results": {
                "style": "direct",
                "tone": "urgent",
                "format": "brief",
                "keywords": ["action", "results", "quickly", "efficiently"],
            },
            "security": {
                "style": "cautious",
                "tone": "reassuring",
                "format": "detailed",
                "keywords": ["safe", "secure", "guaranteed", "protected"],
            },
        }

    async def detect_personality(self, conversation_history: List[Dict]) -> str:
        """Detect lead personality type from conversation patterns"""
        all_text = " ".join([m.get("content", "").lower() for m in conversation_history])

        personality_scores = {}
        for personality, profile in self.personality_profiles.items():
            score = sum(1 for keyword in profile["keywords"] if keyword in all_text)
            personality_scores[personality] = score

        # Return highest scoring personality or default to 'relationship'
        return (
            max(personality_scores, key=personality_scores.get) if any(personality_scores.values()) else "relationship"
        )

    async def adapt_message(self, base_message: str, personality_type: str, pattern: ResponsePattern) -> str:
        """Adapt message based on personality type and response patterns"""
        profile = self.personality_profiles.get(personality_type, self.personality_profiles["relationship"])

        # Adjust message length based on preference
        if pattern.message_length_preference == "brief" and profile["format"] != "brief":
            # Shorten message for brief preference
            sentences = base_message.split(". ")
            adapted_message = ". ".join(sentences[:2]) + "."
        else:
            adapted_message = base_message

        # Add personality-specific elements
        if personality_type == "analytical":
            adapted_message = f"Based on market data: {adapted_message}"
        elif personality_type == "relationship":
            adapted_message = f"I wanted to personally reach out: {adapted_message}"
        elif personality_type == "results":
            adapted_message = f"Quick update: {adapted_message}"
        elif personality_type == "security":
            adapted_message = f"To ensure we're on the right track: {adapted_message}"

        return adapted_message


class TemperaturePredictionEngine:
    """Predicts lead temperature changes and provides early warnings"""

    def __init__(self):
        self.temperature_history: Dict[str, List[float]] = {}

    async def predict_temperature_trend(self, lead_id: str, current_scores: Dict[str, float]) -> Dict:
        """Predict lead temperature trend and provide early warnings"""

        # Store current temperature score
        current_temp = (current_scores.get("frs_score", 0) + current_scores.get("pcs_score", 0)) / 2

        if lead_id not in self.temperature_history:
            self.temperature_history[lead_id] = []

        self.temperature_history[lead_id].append(current_temp)

        # Keep only last 10 interactions for trend analysis
        if len(self.temperature_history[lead_id]) > 10:
            self.temperature_history[lead_id] = self.temperature_history[lead_id][-10:]

        history = self.temperature_history[lead_id]

        # Predict trend
        diff = 0
        if len(history) < 2:
            trend = "stable"
            confidence = 0.5
        else:
            # Simple linear trend analysis
            recent_avg = sum(history[-3:]) / min(3, len(history))
            older_avg = sum(history[:-3]) / max(1, len(history) - 3) if len(history) > 3 else recent_avg

            diff = recent_avg - older_avg

            if abs(diff) < 5:
                trend = "stable"
                confidence = 0.8
            elif diff > 0:
                trend = "heating_up"
                confidence = 0.7
            else:
                trend = "cooling_down"
                confidence = 0.7

        # Generate early warning if cooling
        early_warning = None
        if trend == "cooling_down" and current_temp > 40:
            early_warning = {
                "type": "temperature_declining",
                "urgency": "medium",
                "recommendation": "Immediate engagement recommended - lead showing signs of disengagement",
                "suggested_action": "Schedule call within 24 hours",
            }

        return {
            "current_temperature": current_temp,
            "trend": trend,
            "confidence": confidence,
            "early_warning": early_warning,
            "prediction_next_interaction": max(0, current_temp + (diff * 1.5)),
        }


class LeadBotWorkflow:
    """
    Enhanced Lead Bot - Orchestrates the 3-7-30 Day Follow-Up Sequence using LangGraph.
    Implements the 'Ghost-in-the-Machine' Re-engagement Strategy with optional enhancements.

    CORE FEATURES (always enabled):
    - LangGraph 3-7-30 day follow-up sequence
    - Ghost-in-the-machine re-engagement
    - CMA generation and property intelligence

    OPTIONAL ENHANCEMENTS (configurable):
    - Predictive Analytics (behavioral pattern analysis)
    - Personality Adaptation (customized messaging)
    - Track 3.1 ML Intelligence (market timing optimization)
    - Jorge Bot handoff coordination
    """

    MAX_CONVERSATION_HISTORY = 50
    SMS_MAX_LENGTH = 160

    def __init__(
        self,
        ghl_client=None,
        config: Optional[LeadBotConfig] = None,
        sendgrid_client=None,
        industry_config: Optional["IndustryConfig"] = None,
    ):
        # Industry-agnostic configuration layer (backward compatible)
        from ghl_real_estate_ai.config.industry_config import IndustryConfig

        self.industry_config: IndustryConfig = industry_config or IndustryConfig.default_real_estate()

        # Core components (always initialized)
        self.config = config or LeadBotConfig()
        self.intent_decoder = LeadIntentDecoder(industry_config=self.industry_config)
        self.retell_client = RetellClient()
        self.cma_generator = CMAGenerator()
        self.ghost_engine = get_ghost_followup_engine()
        self.ghl_client = ghl_client
        self.sendgrid_client = sendgrid_client
        self.event_publisher = get_event_publisher()
        self.sequence_service = get_sequence_service()
        self.scheduler = get_lead_scheduler()
        from ghl_real_estate_ai.services.national_market_intelligence import get_national_market_intelligence

        self.market_intel = get_national_market_intelligence()

        # Enhanced components (optional)
        self.analytics_engine = None
        self.personality_adapter = None
        self.temperature_engine = None
        self.ml_analytics = None

        if self.config.enable_behavioral_optimization:
            self.analytics_engine = BehavioralAnalyticsEngine()
            logger.info("Lead Bot: Behavioral analytics enabled")

        if self.config.enable_personality_adaptation:
            self.personality_adapter = PersonalityAdapter()
            logger.info("Lead Bot: Personality adaptation enabled")

        if self.config.enable_predictive_analytics:
            self.temperature_engine = TemperaturePredictionEngine()
            logger.info("Lead Bot: Predictive analytics enabled")

        # Track 3.1 ML Analytics Engine (optional)
        if self.config.enable_track3_intelligence and TRACK3_ML_AVAILABLE:
            self.ml_analytics = MLAnalyticsEngine(tenant_id="jorge_lead_bot")
            logger.info("Lead Bot: Track 3.1 ML intelligence enabled")
        elif self.config.enable_track3_intelligence:
            logger.warning("Lead Bot: Track 3.1 requested but dependencies not available")

        # Phase 3.3 Bot Intelligence Middleware Integration
        self.intelligence_middleware = None
        if self.config.enable_bot_intelligence and BOT_INTELLIGENCE_AVAILABLE:
            self.intelligence_middleware = get_bot_intelligence_middleware()
            logger.info("Lead Bot: Phase 3.3 Bot Intelligence Middleware enabled")
        elif self.config.enable_bot_intelligence:
            logger.warning("Lead Bot: Phase 3.3 Bot Intelligence requested but dependencies not available")

        # Monitoring services (singletons — cheap to instantiate)
        self.performance_tracker = PerformanceTracker()
        self.metrics_collector = BotMetricsCollector()
        self.alerting_service = AlertingService()
        self.ab_testing = ABTestingService()
        self.cache_service = CacheService()
        self._init_ab_experiments()

        # Performance tracking
        self.workflow_stats = {
            "total_sequences": 0,
            "total_interactions": 0,
            "behavioral_optimizations": 0,
            "personality_adaptations": 0,
            "track3_enhancements": 0,
            "jorge_handoffs": 0,
            "intelligence_gathering_operations": 0,
        }

        # Build workflow based on enabled features
        self.workflow = self._build_unified_graph()

    async def check_voice_call_data(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """
        Check if lead has recent voice call qualification data.

        Returns voice call data if found and recent (<7 days), otherwise None.
        This allows bots to skip re-qualification after voice calls.
        """
        try:
            bot_state_key = f"bot_state:{lead_id}"
            bot_state = await self.cache_service.get(bot_state_key)

            if not bot_state or "voice_call_data" not in bot_state:
                return None

            voice_data = bot_state["voice_call_data"]

            # Check if data is recent (within 7 days)
            synced_at = datetime.fromisoformat(voice_data.get("synced_at", ""))
            age_days = (datetime.now() - synced_at).days

            if age_days > 7:
                logger.debug(f"Voice call data for {lead_id} is stale ({age_days} days old)")
                return None

            logger.info(
                f"Found voice call qualification data for {lead_id} "
                f"(qualified: {voice_data.get('qualification_complete')}, "
                f"status: {voice_data.get('qualified_status')})"
            )

            return voice_data

        except Exception as e:
            logger.debug(f"Failed to check voice call data for {lead_id}: {e}")
            return None

    def _init_ab_experiments(self) -> None:
        """Create default A/B experiments if not already registered."""
        try:
            self.ab_testing.create_experiment(
                ABTestingService.RESPONSE_TONE_EXPERIMENT,
                ["formal", "casual", "empathetic"],
            )
        except ValueError:
            pass  # Already exists

    def _build_unified_graph(self) -> StateGraph:
        """Build workflow graph based on enabled features"""
        if (
            self.config.enable_predictive_analytics
            or self.config.enable_behavioral_optimization
            or self.config.enable_track3_intelligence
            or self.config.enable_bot_intelligence
        ):
            return self._build_enhanced_graph()
        else:
            return self._build_standard_graph()

    def _build_standard_graph(self) -> StateGraph:
        workflow = StateGraph(LeadFollowUpState)

        # Define Nodes
        workflow.add_node("analyze_intent", self.analyze_intent)
        workflow.add_node("determine_path", self.determine_path)
        workflow.add_node("generate_cma", self.generate_cma)

        # Follow-up Nodes
        workflow.add_node("send_day_3_sms", self.send_day_3_sms)
        workflow.add_node("initiate_day_7_call", self.initiate_day_7_call)
        workflow.add_node("send_day_14_email", self.send_day_14_email)
        workflow.add_node("send_day_30_nudge", self.send_day_30_nudge)

        # Full Lifecycle Nodes
        workflow.add_node("schedule_showing", self.schedule_showing)
        workflow.add_node("post_showing_survey", self.post_showing_survey)
        workflow.add_node("facilitate_offer", self.facilitate_offer)
        workflow.add_node("contract_to_close_nurture", self.contract_to_close_nurture)

        # Define Edges
        workflow.set_entry_point("analyze_intent")
        workflow.add_edge("analyze_intent", "determine_path")

        # Conditional Routing based on 'current_step' and 'engagement_status'
        workflow.add_conditional_edges(
            "determine_path",
            self._route_next_step,
            {
                "generate_cma": "generate_cma",
                "day_3": "send_day_3_sms",
                "day_7": "initiate_day_7_call",
                "day_14": "send_day_14_email",
                "day_30": "send_day_30_nudge",
                "schedule_showing": "schedule_showing",
                "post_showing": "post_showing_survey",
                "facilitate_offer": "facilitate_offer",
                "closing_nurture": "contract_to_close_nurture",
                "qualified": END,
                "nurture": END,
            },
        )

        # All actions end for this single-turn execution
        workflow.add_edge("generate_cma", END)
        workflow.add_edge("send_day_3_sms", END)
        workflow.add_edge("initiate_day_7_call", END)
        workflow.add_edge("send_day_14_email", END)
        workflow.add_edge("send_day_30_nudge", END)
        workflow.add_edge("schedule_showing", END)
        workflow.add_edge("post_showing_survey", END)
        workflow.add_edge("facilitate_offer", END)
        workflow.add_edge("contract_to_close_nurture", END)

        return workflow.compile()

    def _build_enhanced_graph(self) -> StateGraph:
        """Build enhanced workflow with predictive analytics and optimization"""
        workflow = StateGraph(LeadFollowUpState)

        # Enhanced nodes
        workflow.add_node("analyze_intent", self.analyze_intent)
        if self.config.enable_bot_intelligence and self.intelligence_middleware:
            workflow.add_node("gather_lead_intelligence", self.gather_lead_intelligence)
        if self.config.enable_behavioral_optimization or self.config.enable_predictive_analytics:
            workflow.add_node("behavioral_analysis", self.analyze_behavioral_patterns)
        if self.config.enable_behavioral_optimization:
            workflow.add_node("predict_optimization", self.predict_sequence_optimization)
        if self.config.enable_track3_intelligence:
            workflow.add_node("track3_market_intelligence", self.apply_track3_market_intelligence)

        workflow.add_node("determine_path", self.determine_path)
        workflow.add_node("generate_cma", self.generate_cma)

        # Enhanced follow-up nodes
        workflow.add_node("send_optimized_day_3", self.send_optimized_day_3)
        workflow.add_node("initiate_predictive_day_7", self.initiate_predictive_day_7)
        workflow.add_node("send_adaptive_day_14", self.send_adaptive_day_14)
        workflow.add_node("send_intelligent_day_30", self.send_intelligent_day_30)

        # Lifecycle nodes (unchanged)
        workflow.add_node("schedule_showing", self.schedule_showing)
        workflow.add_node("post_showing_survey", self.post_showing_survey)
        workflow.add_node("facilitate_offer", self.facilitate_offer)
        workflow.add_node("contract_to_close_nurture", self.contract_to_close_nurture)

        # Enhanced flow
        workflow.set_entry_point("analyze_intent")

        # Build flow based on enabled features
        current_node = "analyze_intent"

        if self.config.enable_bot_intelligence and self.intelligence_middleware:
            workflow.add_edge(current_node, "gather_lead_intelligence")
            current_node = "gather_lead_intelligence"

        if self.config.enable_behavioral_optimization or self.config.enable_predictive_analytics:
            workflow.add_edge(current_node, "behavioral_analysis")
            current_node = "behavioral_analysis"

        if self.config.enable_behavioral_optimization:
            workflow.add_edge(current_node, "predict_optimization")
            current_node = "predict_optimization"

        if self.config.enable_track3_intelligence:
            workflow.add_edge(current_node, "track3_market_intelligence")
            current_node = "track3_market_intelligence"

        workflow.add_edge(current_node, "determine_path")

        # Enhanced conditional routing
        workflow.add_conditional_edges(
            "determine_path",
            self._route_enhanced_step,
            {
                "generate_cma": "generate_cma",
                "day_3": "send_optimized_day_3",
                "day_7": "initiate_predictive_day_7",
                "day_14": "send_adaptive_day_14",
                "day_30": "send_intelligent_day_30",
                "schedule_showing": "schedule_showing",
                "post_showing": "post_showing_survey",
                "facilitate_offer": "facilitate_offer",
                "closing_nurture": "contract_to_close_nurture",
                "qualified": END,
                "nurture": END,
            },
        )

        # All actions end
        for node in [
            "generate_cma",
            "send_optimized_day_3",
            "initiate_predictive_day_7",
            "send_adaptive_day_14",
            "send_intelligent_day_30",
            "schedule_showing",
            "post_showing_survey",
            "facilitate_offer",
            "contract_to_close_nurture",
        ]:
            workflow.add_edge(node, END)

        return workflow.compile()

    # ================================
    # ENHANCED FEATURE METHODS
    # ================================

    async def gather_lead_intelligence(self, state: LeadFollowUpState) -> Dict:
        """
        Gather comprehensive intelligence context for Lead Bot nurture sequence optimization.

        Focuses on nurture-specific intelligence:
        - Lead preference extraction and persistence
        - Churn risk prediction for proactive engagement
        - Cross-bot context sharing capabilities
        - Timing optimization for sequence effectiveness
        """
        logger.info(f"Gathering lead intelligence for nurture optimization: {state['lead_id']}")

        # Emit bot status update
        await self.event_publisher.publish_bot_status_update(
            bot_type="enhanced-lead-bot",
            contact_id=state["lead_id"],
            status="processing",
            current_step="gather_lead_intelligence",
        )

        # Initialize performance tracking
        intelligence_start_time = time.time()
        intelligence_context = None

        try:
            if self.intelligence_middleware:
                # Use Lead Bot specific context for nurture-focused intelligence
                intelligence_context = await self.intelligence_middleware.enhance_bot_context(
                    lead_id=state["lead_id"],
                    location_id="national",  # Default for lead bot
                    bot_type="lead-bot",
                    conversation_history=state["conversation_history"],
                    current_context={
                        "sequence_day": state.get("sequence_day"),
                        "engagement_status": state.get("engagement_status"),
                        "nurture_focus": True,
                        "intent_profile": state.get("intent_profile").to_dict() if state.get("intent_profile") else {},
                    },
                )

                intelligence_performance_ms = (time.time() - intelligence_start_time) * 1000
                logger.info(
                    f"Lead intelligence gathered for {state['lead_id']} in {intelligence_performance_ms:.1f}ms "
                    f"(engagement: {intelligence_context.composite_engagement_score:.2f}, "
                    f"approach: {intelligence_context.recommended_approach})"
                )

                self.workflow_stats["intelligence_gathering_operations"] += 1

                # Emit lead intelligence gathered event
                await self.event_publisher.publish_bot_status_update(
                    bot_type="enhanced-lead-bot",
                    contact_id=state["lead_id"],
                    status="processing",
                    current_step="lead_intelligence_gathered",
                    message=f"Lead intelligence gathered: {intelligence_context.property_intelligence.match_count} properties, "
                    f"engagement score: {intelligence_context.composite_engagement_score:.2f}",
                )

                return {
                    "intelligence_context": intelligence_context,
                    "intelligence_performance_ms": intelligence_performance_ms,
                }
            else:
                logger.warning(f"Intelligence middleware not available for lead {state['lead_id']}")
                return {"intelligence_context": None, "intelligence_performance_ms": 0.0}

        except Exception as e:
            intelligence_performance_ms = (time.time() - intelligence_start_time) * 1000
            logger.error(f"Failed to gather lead intelligence for {state['lead_id']}: {e}")

            # Create fallback intelligence context for graceful degradation
            fallback_context = BotIntelligenceContext.create_fallback(
                lead_id=state["lead_id"],
                location_id="national",
                bot_type="lead-bot",
                error_context=f"intelligence_gathering_failed: {str(e)}",
            )

            return {
                "intelligence_context": fallback_context,
                "intelligence_performance_ms": intelligence_performance_ms,
            }

    async def analyze_behavioral_patterns(self, state: LeadFollowUpState) -> Dict:
        """Analyze lead behavioral patterns for optimization"""
        logger.info(f"Analyzing behavioral patterns for lead {state['lead_id']}")

        await self.event_publisher.publish_bot_status_update(
            bot_type="enhanced-lead-bot",
            contact_id=state["lead_id"],
            status="processing",
            current_step="behavioral_analysis",
        )

        # Initialize defaults
        pattern = None
        personality = "relationship"
        temperature_prediction = None

        # Analyze response patterns if engine available
        if self.analytics_engine:
            pattern = await self.analytics_engine.analyze_response_patterns(
                state["lead_id"], state["conversation_history"]
            )
            self.workflow_stats["behavioral_optimizations"] += 1

        # Detect personality type if adapter available
        if self.personality_adapter:
            personality = await self.personality_adapter.detect_personality(state["conversation_history"])
            self.workflow_stats["personality_adaptations"] += 1

        # Predict temperature trend if engine available
        if self.temperature_engine:
            current_scores = {
                "frs_score": state["intent_profile"].frs.total_score,
                "pcs_score": state["intent_profile"].pcs.total_score,
            }
            temperature_prediction = await self.temperature_engine.predict_temperature_trend(
                state["lead_id"], current_scores
            )

        # Emit behavioral analysis event
        await self.event_publisher.publish_behavioral_prediction(
            lead_id=state["lead_id"],
            location_id="national",
            behavior_category=personality,
            churn_risk_score=0.1,  # Mocked for now
            engagement_score=0.8,  # Mocked for now
            next_actions=[],
            prediction_latency_ms=0.0,
        )

        return {
            "response_pattern": pattern,
            "personality_type": personality,
            "temperature_prediction": temperature_prediction,
        }

    async def predict_sequence_optimization(self, state: LeadFollowUpState) -> Dict:
        """Predict optimal sequence timing and channels"""
        logger.info(f"Optimizing sequence for lead {state['lead_id']}")

        if not self.analytics_engine or not state.get("response_pattern"):
            # Return default optimization
            default_optimization = SequenceOptimization(
                day_3=3, day_7=7, day_14=14, day_30=30, channel_sequence=["SMS", "Email", "Voice", "SMS"]
            )
            return {"sequence_optimization": default_optimization}

        pattern = state["response_pattern"]
        optimization = await self.analytics_engine.predict_optimal_sequence(pattern)

        logger.info(f"Sequence optimization: {optimization}")

        return {"sequence_optimization": optimization}

    async def apply_track3_market_intelligence(self, state: LeadFollowUpState) -> Dict:
        """Apply Track 3.1 market timing intelligence to enhance nurture sequence"""
        logger.info(f"Applying Track 3.1 market intelligence for lead {state['lead_id']}")

        await self.event_publisher.publish_bot_status_update(
            bot_type="enhanced-lead-bot",
            contact_id=state["lead_id"],
            status="processing",
            current_step="track3_market_analysis",
        )

        try:
            if not self.ml_analytics:
                logger.warning("Track 3.1 ML analytics not available")
                return {"track3_applied": False, "fallback_reason": "ML analytics not available"}

            # Track 3.1 enhancement: Get comprehensive predictive analysis
            journey_analysis = await self.ml_analytics.predict_lead_journey(state["lead_id"])
            conversion_analysis = await self.ml_analytics.predict_conversion_probability(
                state["lead_id"], state.get("current_journey_stage", "nurture")
            )
            touchpoint_analysis = await self.ml_analytics.predict_optimal_touchpoints(state["lead_id"])

            # Apply market timing enhancements
            enhanced_optimization = await self._apply_market_timing_intelligence(
                state.get("sequence_optimization"), journey_analysis, conversion_analysis, touchpoint_analysis
            )

            # Detect critical scenarios
            critical_scenario = await self._detect_critical_scenarios(journey_analysis, conversion_analysis, state)

            self.workflow_stats["track3_enhancements"] += 1

            return {
                "journey_analysis": journey_analysis,
                "conversion_analysis": conversion_analysis,
                "touchpoint_analysis": touchpoint_analysis,
                "enhanced_optimization": enhanced_optimization,
                "critical_scenario": critical_scenario,
                "track3_applied": True,
            }

        except Exception as e:
            logger.error(f"Track 3.1 market intelligence failed for {state['lead_id']}: {e}")
            return {"track3_applied": False, "fallback_reason": str(e)}

    async def send_optimized_day_3(self, state: LeadFollowUpState) -> Dict:
        """Day 3 with enhanced timing and personalization using intelligence context"""
        logger.info(f"Sending intelligence-optimized Day 3 SMS for {state['lead_name']}")

        # Use enhanced optimization if available
        optimization = state.get("enhanced_optimization", state.get("sequence_optimization"))
        pattern = state.get("response_pattern")
        personality = state.get("personality_type", "relationship")

        # Phase 3.3 Intelligence Enhancement: Use intelligence context for nurture optimization
        intelligence_context = state.get("intelligence_context")
        churn_risk = 0.5  # Default
        preferred_timing = None
        personalized_insights = []

        if intelligence_context:
            # Extract nurture-specific intelligence
            churn_risk = self._extract_churn_risk_from_intelligence(intelligence_context)
            preferred_timing = self._extract_preferred_engagement_timing(intelligence_context)
            personalized_insights = intelligence_context.priority_insights or []

            logger.info(
                f"Intelligence context applied - churn risk: {churn_risk:.2f}, insights: {len(personalized_insights)}"
            )

        # Use optimized timing if available
        actual_day = optimization.day_3 if optimization else 3
        preferred_channel = (
            optimization.channel_sequence[0] if optimization and optimization.channel_sequence else "SMS"
        )

        # Intelligence-driven timing adjustment for nurture sequences
        if churn_risk > 0.7:
            actual_day = max(1, actual_day - 1)  # Accelerate for high churn risk
            logger.info(f"High churn risk detected ({churn_risk:.2f}) - accelerating contact to day {actual_day}")
        elif churn_risk < 0.3:
            actual_day = min(5, actual_day + 1)  # Extend for low churn risk to avoid over-communication
            logger.info(f"Low churn risk ({churn_risk:.2f}) - extending to day {actual_day} to avoid fatigue")

        # Check for critical scenarios
        critical_scenario = state.get("critical_scenario")
        if critical_scenario and critical_scenario.get("urgency") == "critical":
            logger.warning(f"CRITICAL SCENARIO: {critical_scenario['type']} - {critical_scenario['recommendation']}")
            actual_day = 0  # Contact immediately
            preferred_channel = "Voice"  # Use most direct channel

        # Enhanced message construction using intelligence insights
        base_msg = self._construct_intelligent_day3_message(
            state, intelligence_context, personalized_insights, critical_scenario
        )

        # Adapt message for personality if adapter available
        adapted_msg = base_msg
        if self.personality_adapter and pattern:
            adapted_msg = await self.personality_adapter.adapt_message(base_msg, personality, pattern)

        logger.info(f"Enhanced Day {actual_day} {preferred_channel} to {state['lead_name']}: {adapted_msg}")

        # Store intelligence-driven optimizations in state for tracking
        return {
            "engagement_status": "enhanced_nurture",
            "current_step": "day_7_call",
            "response_content": adapted_msg,
            "optimized_timing_applied": bool(optimization),
            "personalization_applied": bool(self.personality_adapter),
            "track3_enhancement_applied": state.get("track3_applied", False),
            "critical_scenario_handled": bool(critical_scenario),
            "intelligence_enhancement_applied": bool(intelligence_context),
            "churn_risk_score": churn_risk,
            "sequence_optimization_applied": True,
            "preferred_engagement_timing": preferred_timing,
        }

    async def initiate_predictive_day_7(self, state: LeadFollowUpState) -> Dict:
        """Day 7 with predictive timing and channel optimization using intelligence context"""
        logger.info(f"Initiating intelligence-enhanced Day 7 call for {state['lead_name']}")

        optimization = state.get("enhanced_optimization", state.get("sequence_optimization"))
        temperature_pred = state.get("temperature_prediction")
        journey_analysis = state.get("journey_analysis")
        conversion_analysis = state.get("conversion_analysis")

        # Phase 3.3 Intelligence Enhancement: Use intelligence context for call optimization
        intelligence_context = state.get("intelligence_context")
        churn_risk = state.get("churn_risk_score", 0.5)
        cross_bot_handoff_eligible = False

        if intelligence_context:
            # Intelligence-driven handoff decision
            engagement_score = intelligence_context.composite_engagement_score
            objections_detected = len(intelligence_context.conversation_intelligence.objections_detected)

            # Enhanced Jorge handoff logic using comprehensive intelligence
            if engagement_score > 0.7 and churn_risk < 0.4 and objections_detected < 2:
                cross_bot_handoff_eligible = True
                logger.info(
                    f"Intelligence suggests Jorge handoff eligibility for {state['lead_name']} "
                    f"(engagement: {engagement_score:.2f}, churn_risk: {churn_risk:.2f})"
                )

        # Check conversion probability for Jorge handoff consideration
        if (
            conversion_analysis
            and conversion_analysis.stage_conversion_probability > 0.7
            and journey_analysis
            and journey_analysis.conversion_probability > 0.6
        ):
            logger.info(f"High conversion indicators for {state['lead_name']} - consider Jorge handoff")
            cross_bot_handoff_eligible = True
            if self.config.jorge_handoff_enabled:
                await self._publish_jorge_handoff_recommendation(state, journey_analysis, conversion_analysis)

        # Intelligence-driven urgency detection
        urgency_detected = False
        if intelligence_context:
            urgency_indicators = intelligence_context.conversation_intelligence.urgency_indicators
            if urgency_indicators or churn_risk > 0.8:
                urgency_detected = True
                logger.warning(
                    f"Urgency detected for {state['lead_name']}: "
                    f"indicators={len(urgency_indicators)}, churn_risk={churn_risk:.2f}"
                )

        # Check for temperature early warning
        if temperature_pred and temperature_pred.get("early_warning"):
            logger.warning(
                f"Temperature early warning for {state['lead_name']}: {temperature_pred['early_warning']['recommendation']}"
            )

        preferred_channel = (
            optimization.channel_sequence[1] if optimization and len(optimization.channel_sequence) > 1 else "Voice"
        )
        actual_day = optimization.day_7 if optimization else 7

        # Intelligence-driven timing adjustment
        if urgency_detected or churn_risk > 0.7:
            actual_day = max(5, actual_day - 1)  # Accelerate call
            logger.info(f"Accelerating Day 7 call to Day {actual_day} due to urgency/churn risk")

        msg = f"Intelligence-enhanced Day {actual_day} {preferred_channel} call for {state['lead_name']}"
        if cross_bot_handoff_eligible:
            msg += " (Jorge handoff candidate)"

        logger.info(msg)

        return {
            "engagement_status": "enhanced_nurture",
            "current_step": "day_14_email",
            "response_content": msg,
            "jorge_handoff_eligible": cross_bot_handoff_eligible,
            "intelligence_enhancement_applied": bool(intelligence_context),
            "urgency_detected": urgency_detected,
            "churn_risk_score": churn_risk,
        }

    async def send_adaptive_day_14(self, state: LeadFollowUpState) -> Dict:
        """Day 14 with adaptive messaging and channel selection using intelligence context"""
        logger.info(f"Sending intelligence-adaptive Day 14 message for {state['lead_name']}")

        optimization = state.get("enhanced_optimization", state.get("sequence_optimization"))
        state.get("personality_type", "relationship")
        journey_analysis = state.get("journey_analysis")
        conversion_analysis = state.get("conversion_analysis")

        # Phase 3.3 Intelligence Enhancement: Adaptive messaging based on intelligence
        intelligence_context = state.get("intelligence_context")
        churn_risk = state.get("churn_risk_score", 0.5)
        content_adaptation_applied = False

        preferred_channel = (
            optimization.channel_sequence[2] if optimization and len(optimization.channel_sequence) > 2 else "Email"
        )
        actual_day = optimization.day_14 if optimization else 14

        # Intelligence-driven content and channel adaptation
        if intelligence_context:
            # Analyze conversation intelligence for adaptive messaging
            objections = intelligence_context.conversation_intelligence.objections_detected
            sentiment = intelligence_context.conversation_intelligence.overall_sentiment

            # Adapt channel based on engagement patterns and objections
            if objections and sentiment < 0:
                preferred_channel = "Voice"  # Personal call for objection handling
                content_adaptation_applied = True
                logger.info(f"Adapting to Voice call due to {len(objections)} objections and negative sentiment")

            # Property intelligence-driven content
            if intelligence_context.property_intelligence.match_count > 0:
                content_adaptation_applied = True
                logger.info(
                    f"Incorporating {intelligence_context.property_intelligence.match_count} property matches into Day 14 message"
                )

        # Check for bottlenecks requiring intervention
        intervention_needed = False
        if (
            journey_analysis
            and journey_analysis.stage_bottlenecks
            and conversion_analysis
            and conversion_analysis.urgency_score > 0.6
        ):
            intervention_needed = True
            logger.warning(f"Stage bottlenecks detected for {state['lead_name']}: {journey_analysis.stage_bottlenecks}")
            preferred_channel = "Voice"  # Override to voice call for bottleneck resolution

        # Intelligence-driven escalation for high churn risk
        if churn_risk > 0.8:
            preferred_channel = "Voice"
            intervention_needed = True
            logger.warning(f"High churn risk ({churn_risk:.2f}) - escalating Day 14 to voice call")

        msg = self._construct_adaptive_day14_message(
            state, intelligence_context, preferred_channel, content_adaptation_applied
        )

        logger.info(f"Adaptive Day {actual_day} {preferred_channel} for {state['lead_name']}: {msg[:100]}...")

        return {
            "engagement_status": "enhanced_nurture",
            "current_step": "day_30_nudge",
            "response_content": msg,
            "bottleneck_intervention": intervention_needed,
            "channel_escalated": intervention_needed,
            "intelligence_enhancement_applied": bool(intelligence_context),
            "content_adaptation_applied": content_adaptation_applied,
            "churn_risk_score": churn_risk,
        }

    async def send_intelligent_day_30(self, state: LeadFollowUpState) -> Dict:
        """Day 30 with intelligent re-engagement strategy using comprehensive intelligence"""
        logger.info(f"Executing intelligent Day 30 final engagement for {state['lead_name']}")

        optimization = state.get("enhanced_optimization", state.get("sequence_optimization"))
        state.get("temperature_prediction")
        journey_analysis = state.get("journey_analysis")
        conversion_analysis = state.get("conversion_analysis")

        # Phase 3.3 Intelligence Enhancement: Comprehensive final decision
        intelligence_context = state.get("intelligence_context")
        churn_risk = state.get("churn_risk_score", 0.5)

        actual_day = optimization.day_30 if optimization else 30

        # Intelligence-driven final decision point - nurture vs qualify vs disengage
        final_strategy = "nurture"  # Default
        intelligence_score = 0.0
        handoff_reasoning = []

        if intelligence_context:
            # Comprehensive intelligence analysis for final strategy
            engagement_score = intelligence_context.composite_engagement_score
            property_matches = intelligence_context.property_intelligence.match_count
            objections_count = len(intelligence_context.conversation_intelligence.objections_detected)
            sentiment = intelligence_context.conversation_intelligence.overall_sentiment
            preference_completeness = intelligence_context.preference_intelligence.profile_completeness

            # Calculate comprehensive intelligence score for handoff decision
            intelligence_score = (
                engagement_score * 0.3
                + min(property_matches / 5.0, 1.0) * 0.2  # Normalize to 0-1
                + max(0, (5 - objections_count) / 5.0) * 0.2  # Fewer objections = better
                + max(0, (sentiment + 1) / 2.0) * 0.15  # Normalize sentiment to 0-1
                + preference_completeness * 0.15
            )

            logger.info(
                f"Intelligence score calculation for {state['lead_name']}: "
                f"engagement={engagement_score:.2f}, properties={property_matches}, "
                f"objections={objections_count}, sentiment={sentiment:.2f}, "
                f"preferences={preference_completeness:.2f} → score={intelligence_score:.2f}"
            )

            # Enhanced decision logic using comprehensive intelligence
            if intelligence_score > 0.7 and churn_risk < 0.4:
                final_strategy = "jorge_qualification"
                handoff_reasoning.append(f"High intelligence score ({intelligence_score:.2f})")
                handoff_reasoning.append(f"Low churn risk ({churn_risk:.2f})")

            elif intelligence_score > 0.5 and property_matches > 2 and sentiment > 0:
                final_strategy = "jorge_consultation"
                handoff_reasoning.append(f"Property matches ({property_matches}) with positive sentiment")

            elif intelligence_score < 0.3 or churn_risk > 0.8:
                final_strategy = "graceful_disengage"
                handoff_reasoning.append(
                    f"Low intelligence score ({intelligence_score:.2f}) or high churn risk ({churn_risk:.2f})"
                )

        # Traditional Track 3.1 logic as backup
        if journey_analysis and conversion_analysis and final_strategy == "nurture":
            # High potential - recommend Jorge qualification
            if journey_analysis.conversion_probability > 0.5 and conversion_analysis.stage_conversion_probability > 0.4:
                final_strategy = "jorge_qualification"
                handoff_reasoning.append("High Track 3.1 conversion probability")

            # Low potential with cooling trend - disengage gracefully
            elif journey_analysis.conversion_probability < 0.2 and conversion_analysis.drop_off_risk > 0.8:
                final_strategy = "graceful_disengage"
                handoff_reasoning.append("Low Track 3.1 conversion probability with high drop-off risk")

        # Execute Jorge handoff if recommended
        if final_strategy in ["jorge_qualification", "jorge_consultation"] and self.config.jorge_handoff_enabled:
            await self._publish_intelligent_jorge_handoff_request(
                state, intelligence_context, final_strategy, intelligence_score, handoff_reasoning
            )
            self.workflow_stats["jorge_handoffs"] += 1

        # Construct final message based on strategy
        msg = self._construct_intelligent_day30_message(state, final_strategy, intelligence_score, handoff_reasoning)

        logger.info(
            f"Intelligent Day {actual_day} final engagement for {state['lead_name']} - "
            f"Strategy: {final_strategy}, Intelligence Score: {intelligence_score:.2f}, "
            f"Reasoning: {'; '.join(handoff_reasoning)}"
        )

        return {
            "engagement_status": "enhanced_final",
            "current_step": final_strategy,
            "response_content": msg,
            "jorge_handoff_recommended": final_strategy in ["jorge_qualification", "jorge_consultation"],
            "sequence_complete": True,
            "final_strategy": final_strategy,
            "intelligence_score": intelligence_score,
            "handoff_reasoning": handoff_reasoning,
            "intelligence_enhancement_applied": bool(intelligence_context),
            "churn_risk_score": churn_risk,
        }

    def _route_enhanced_step(
        self, state: LeadFollowUpState
    ) -> Literal[
        "generate_cma",
        "day_3",
        "day_7",
        "day_14",
        "day_30",
        "schedule_showing",
        "post_showing",
        "facilitate_offer",
        "closing_nurture",
        "qualified",
        "nurture",
    ]:
        """Enhanced routing with predictive logic"""
        # Check for early warnings that require immediate action
        if state.get("temperature_prediction", {}).get("early_warning"):
            warning = state["temperature_prediction"]["early_warning"]
            if warning.get("urgency") == "high":
                return "schedule_showing"  # Immediate escalation

        # Use parent routing logic with enhancements
        return self._route_next_step(state)

    # --- Track 3.1 Enhancement Helper Methods ---

    async def _apply_market_timing_intelligence(
        self,
        base_optimization: Optional[SequenceOptimization],
        journey_analysis,
        conversion_analysis,
        touchpoint_analysis,
    ) -> SequenceOptimization:
        """Apply Track 3.1 market timing intelligence to enhance sequence optimization"""
        if not base_optimization:
            base_optimization = SequenceOptimization(
                day_3=3, day_7=7, day_14=14, day_30=30, channel_sequence=["SMS", "Email", "Voice", "SMS"]
            )

        enhanced_optimization = SequenceOptimization(
            day_3=base_optimization.day_3,
            day_7=base_optimization.day_7,
            day_14=base_optimization.day_14,
            day_30=base_optimization.day_30,
            channel_sequence=base_optimization.channel_sequence.copy(),
        )

        # Timing enhancement: Urgency-based acceleration
        urgency_score = conversion_analysis.urgency_score
        if urgency_score > 0.8:
            # High urgency: Accelerate sequence significantly
            enhanced_optimization.day_3 = max(1, int(base_optimization.day_3 * 0.5))
            enhanced_optimization.day_7 = max(2, int(base_optimization.day_7 * 0.6))
            enhanced_optimization.day_14 = max(5, int(base_optimization.day_14 * 0.7))
            logger.info(f"HIGH URGENCY: Accelerated sequence timing by 30-50%")

        elif urgency_score < 0.3:
            # Low urgency: Extend intervals to avoid over-communication
            enhanced_optimization.day_7 = min(14, int(base_optimization.day_7 * 1.5))
            enhanced_optimization.day_14 = min(30, int(base_optimization.day_14 * 1.3))
            enhanced_optimization.day_30 = min(60, int(base_optimization.day_30 * 1.2))
            logger.info(f"LOW URGENCY: Extended sequence timing to avoid fatigue")

        # Channel enhancement: Use ML-predicted optimal channels
        if touchpoint_analysis.channel_preferences:
            optimal_channels = sorted(touchpoint_analysis.channel_preferences.items(), key=lambda x: x[1], reverse=True)
            enhanced_optimization.channel_sequence = [ch[0] for ch in optimal_channels[:4]]
            logger.info(f"Updated channel sequence based on ML preferences: {enhanced_optimization.channel_sequence}")

        return enhanced_optimization

    async def _detect_critical_scenarios(
        self, journey_analysis, conversion_analysis, state: LeadFollowUpState
    ) -> Optional[Dict[str, Any]]:
        """Detect critical scenarios requiring immediate intervention or Jorge Bot handoff"""
        # Scenario 1: High value lead cooling down rapidly
        if journey_analysis.conversion_probability > 0.6 and conversion_analysis.drop_off_risk > 0.7:
            return {
                "type": "high_value_cooling",
                "urgency": "critical",
                "recommendation": "immediate_jorge_handoff",
                "reason": f"High conversion probability ({journey_analysis.conversion_probability:.2f}) but high drop-off risk ({conversion_analysis.drop_off_risk:.2f})",
                "suggested_action": "Deploy Jorge Seller Bot for confrontational re-engagement within 2 hours",
            }

        # Scenario 2: Ready for qualification
        if journey_analysis.conversion_probability > 0.75 and conversion_analysis.stage_conversion_probability > 0.8:
            return {
                "type": "qualification_ready",
                "urgency": "medium",
                "recommendation": "jorge_qualification",
                "reason": f"High conversion indicators suggest readiness for Jorge's qualification process",
                "suggested_action": "Schedule Jorge Bot consultation within 24 hours",
            }

        return None

    async def _publish_jorge_handoff_recommendation(self, state, journey_analysis, conversion_analysis):
        """Publish Jorge handoff recommendation event"""
        await self.event_publisher.publish_strategy_recommendation(
            recommendation_id=f"handoff_{state['lead_id']}",
            contact_id=state["lead_id"],
            strategy_type="jorge_seller_handoff",
            data={
                "conversion_probability": journey_analysis.conversion_probability,
                "stage_conversion_probability": conversion_analysis.stage_conversion_probability,
                "recommendation": "Consider Jorge Seller Bot engagement for qualification",
            },
        )

    async def _publish_jorge_handoff_request(self, state, journey_analysis, conversion_analysis):
        """Publish Jorge handoff request event"""
        await self.event_publisher.publish_bot_handoff_request(
            handoff_id=str(uuid.uuid4()),
            from_bot="enhanced-lead-bot",
            to_bot="jorge-seller-bot",
            contact_id=state["lead_id"],
            data={
                "handoff_type": "day_30_qualification",
                "handoff_data": {
                    "conversion_probability": journey_analysis.conversion_probability,
                    "stage_conversion_probability": conversion_analysis.stage_conversion_probability,
                    "lead_temperature": state.get("temperature_prediction", {}).get("current_temperature", 0),
                    "sequence_completion": "day_30_reached",
                    "recommendation": "Jorge confrontational qualification recommended",
                },
            },
        )

    # --- Node Implementations ---

    async def analyze_intent(self, state: LeadFollowUpState) -> Dict:
        """Score the lead using the Phase 1 Intent Decoder."""
        logger.info(f"Analyzing intent for lead {state['lead_id']}")

        # Emit bot status update
        await self.event_publisher.publish_bot_status_update(
            bot_type="lead-bot", contact_id=state["lead_id"], status="processing", current_step="analyze_intent"
        )

        # Phase 1.1: Check for voice call qualification data first
        voice_data = await self.check_voice_call_data(state["lead_id"])

        if voice_data and voice_data.get("qualification_complete"):
            # Voice call already qualified this lead - skip re-qualification
            logger.info(
                f"Skipping re-qualification for {state['lead_id']} - "
                f"using voice call data (status: {voice_data.get('qualified_status')})"
            )

            await sync_service.record_lead_event(
                state["lead_id"],
                "AI",
                f"Using voice call qualification: {voice_data.get('qualified_status')} "
                f"(sentiment: {voice_data.get('sentiment'):.2f}, interest: {voice_data.get('interest_level'):.2f})",
                "thought",
            )

            # Convert voice call data to intent profile format
            # Create a mock profile based on voice call outcomes
            from ghl_real_estate_ai.agents.intent_decoder import LeadProfile

            # Map voice qualification to FRS classification
            voice_status = voice_data.get("qualified_status", "warm")
            classification_map = {"hot": "Hot Lead", "warm": "Warm Lead", "cold": "Cold Lead"}
            classification = classification_map.get(voice_status, "Warm Lead")

            # Estimate FRS score from voice data
            interest = voice_data.get("interest_level", 0.5)
            urgency = voice_data.get("urgency_level", 0.5)
            frs_score = int((interest * 0.6 + urgency * 0.4) * 100)

            # Create simplified profile from voice data
            profile = LeadProfile(
                lead_id=state["lead_id"],
                frs=type(
                    "FRS",
                    (),
                    {
                        "total_score": frs_score,
                        "classification": classification,
                        "price": type("Price", (), {"category": "Price-Aware"})(),
                    },
                )(),
                pcs=type("PCS", (), {"total_score": int(urgency * 100)})(),
            )

            # Store voice qualification metadata
            state["voice_qualified"] = True
            state["voice_call_id"] = voice_data.get("call_id")

            _intent_start_time = time.time()

        else:
            # No recent voice call data - proceed with normal chat qualification
            await sync_service.record_lead_event(state["lead_id"], "AI", "Analyzing lead intent profile.", "thought")

            _intent_start_time = time.time()
            profile = self.intent_decoder.analyze_lead(state["lead_id"], state["conversation_history"])

        # Sync to Lyrio (Phase 4)
        lyrio = LyrioClient()

        # Run sync in background
        asyncio.create_task(
            lyrio.sync_lead_score(
                state["lead_id"], profile.frs.total_score, profile.pcs.total_score, [profile.frs.classification]
            )
        )

        await sync_service.record_lead_event(
            state["lead_id"],
            "AI",
            f"Intent Decoded: {profile.frs.classification} (Score: {profile.frs.total_score})",
            "thought",
        )

        # Initialize or restore sequence state
        sequence_state = await self.sequence_service.get_state(state["lead_id"])
        if not sequence_state:
            # Create new sequence for new lead
            logger.info(f"Creating new sequence for lead {state['lead_id']}")
            sequence_state = await self.sequence_service.create_sequence(
                state["lead_id"], initial_day=SequenceDay.DAY_3
            )

            # Schedule the initial sequence start (immediate or slight delay)
            await self.scheduler.schedule_sequence_start(state["lead_id"], delay_minutes=1)
        else:
            logger.info(f"Restored sequence state for lead {state['lead_id']}: {sequence_state.current_day.value}")

        # Compute actual timing and confidence
        intent_processing_ms = (time.time() - _intent_start_time) * 1000
        intent_confidence = min(0.99, profile.frs.total_score / 100.0)

        # Emit intent analysis complete event
        await self.event_publisher.publish_intent_analysis_complete(
            contact_id=state["lead_id"],
            processing_time_ms=round(intent_processing_ms, 2),
            confidence_score=round(intent_confidence, 3),
            intent_category=profile.frs.classification,
            frs_score=profile.frs.total_score,
            pcs_score=profile.pcs.total_score,
            recommendations=[f"Sequence day: {sequence_state.current_day.value}"],
        )

        return {"intent_profile": profile, "sequence_state": sequence_state.to_dict()}

    async def determine_path(self, state: LeadFollowUpState) -> Dict:
        """Decide the next step based on engagement and timeline."""

        # 1. Check for Price Objection / CMA Request (Phase 3)
        last_msg = state["conversation_history"][-1]["content"].lower() if state["conversation_history"] else ""
        price_keywords = ["price", "value", "worth", "zestimate", "comps", "market analysis"]

        is_price_aware = state["intent_profile"].frs.price.category == "Price-Aware"
        has_keyword = any(k in last_msg for k in price_keywords)

        logger.debug(f"determine_path - last_msg: '{last_msg}'")
        logger.debug(f"determine_path - is_price_aware: {is_price_aware}, has_keyword: {has_keyword}")
        logger.debug(f"determine_path - cma_generated: {state.get('cma_generated')}")

        if (is_price_aware or has_keyword) and not state.get("cma_generated"):
            logger.debug("determine_path - Routing to generate_cma")
            await sync_service.record_lead_event(
                state["lead_id"], "AI", "Price awareness detected. Routing to CMA generation.", "node"
            )
            return {"current_step": "generate_cma", "engagement_status": "responsive"}

        # 2. Check for immediate qualification (High Intent)
        if state["intent_profile"].frs.classification == "Hot Lead":
            await sync_service.record_lead_event(
                state["lead_id"], "AI", "High intent lead detected. Routing to qualified state.", "thought"
            )
            return {"current_step": "qualified", "engagement_status": "qualified"}

        # 3. Use sequence state to determine next step
        sequence_data = state.get("sequence_state", {})
        sequence_day_val = state.get("sequence_day")

        if sequence_day_val is not None:
            # Simulation/Direct mode: create temporary sequence state from sequence_day
            # Map numeric day to SequenceDay enum
            day_enum = SequenceDay.DAY_3
            if sequence_day_val == 7:
                day_enum = SequenceDay.DAY_7
            elif sequence_day_val == 14:
                day_enum = SequenceDay.DAY_14
            elif sequence_day_val == 30:
                day_enum = SequenceDay.DAY_30

            sequence_state = LeadSequenceState(
                lead_id=state["lead_id"],
                current_day=day_enum,
                sequence_status=SequenceStatus.IN_PROGRESS,
                sequence_started_at=datetime.now(timezone.utc),
                engagement_status="responsive",
            )
        elif sequence_data:
            sequence_state = LeadSequenceState.from_dict(sequence_data)
        else:
            # Fallback: get from service if not in state
            sequence_state = await self.sequence_service.get_state(state["lead_id"])
            if not sequence_state:
                # Create new sequence
                sequence_state = await self.sequence_service.create_sequence(state["lead_id"])

        logger.debug(
            f"determine_path - sequence state: {sequence_state.current_day.value}, status: {sequence_state.sequence_status}"
        )

        # Determine routing based on sequence day
        current_day = sequence_state.current_day
        if sequence_day_val is not None:
            if sequence_day_val == 3:
                current_day = SequenceDay.DAY_3
            elif sequence_day_val == 7:
                current_day = SequenceDay.DAY_7
            elif sequence_day_val == 14:
                current_day = SequenceDay.DAY_14
            elif sequence_day_val == 30:
                current_day = SequenceDay.DAY_30

        if current_day == SequenceDay.DAY_3:
            logger.debug("determine_path - Routing to day_3")
            await sync_service.record_lead_event(state["lead_id"], "AI", "Executing Day 3 SMS sequence.", "sequence")
            return {"current_step": "day_3", "engagement_status": sequence_state.engagement_status}

        elif current_day == SequenceDay.DAY_7:
            logger.debug("determine_path - Routing to day_7")
            await sync_service.record_lead_event(state["lead_id"], "AI", "Executing Day 7 call sequence.", "sequence")
            return {"current_step": "day_7", "engagement_status": sequence_state.engagement_status}

        elif current_day == SequenceDay.DAY_14:
            logger.debug("determine_path - Routing to day_14")
            await sync_service.record_lead_event(state["lead_id"], "AI", "Executing Day 14 email sequence.", "sequence")
            return {"current_step": "day_14", "engagement_status": sequence_state.engagement_status}

        elif current_day == SequenceDay.DAY_30:
            logger.debug("determine_path - Routing to day_30")
            await sync_service.record_lead_event(state["lead_id"], "AI", "Executing Day 30 final nudge.", "sequence")
            return {"current_step": "day_30", "engagement_status": sequence_state.engagement_status}

        elif current_day == SequenceDay.QUALIFIED:
            logger.debug("determine_path - Lead is qualified")
            await sync_service.record_lead_event(
                state["lead_id"], "AI", "Lead qualified, exiting sequence.", "sequence"
            )
            return {"current_step": "qualified", "engagement_status": "qualified"}

        else:  # NURTURE or other
            logger.debug("determine_path - Moving to nurture")
            await sync_service.record_lead_event(state["lead_id"], "AI", "Lead in nurture status.", "sequence")
            return {"current_step": "nurture", "engagement_status": "nurture"}

    async def generate_cma(self, state: LeadFollowUpState) -> Dict:
        """Generate Zillow-Defense CMA and inject into conversation."""
        logger.info(f"Generating CMA for {state['lead_name']}")

        address = state.get("property_address", "123 Main St, Rancho Cucamonga, CA")  # Fallback if missing

        await sync_service.record_lead_event(state["lead_id"], "AI", f"Generating CMA for {address}", "thought")

        # Generate Report
        report = await self.cma_generator.generate_report(address)

        # Render PDF URL (Mock)
        pdf_url = PDFRenderer.generate_pdf_url(report)

        # Phase 8: Digital Twin Association
        lyrio = LyrioClient()
        # Mock URL for digital twin
        digital_twin_url = f"https://enterprise-hub.ai/visualize/{address.replace(' ', '-').lower()}"

        # Sync Digital Twin URL to Lyrio in background
        asyncio.create_task(lyrio.sync_digital_twin_url(state["lead_id"], address, digital_twin_url))

        # Construct Response
        response_msg = (
            f"I ran the numbers for {address}. Zillow's estimate is off by ${report.zillow_variance_abs:,.0f}. "
            f"Here is the real market analysis based on actual comps from the last 45 days: \n\n"
            f"[View CMA Report]({pdf_url})\n\n"
            f"I've also prepared a 3D Digital Twin of your property: {digital_twin_url}"
        )

        # In a real system, we'd send this via GHL API here
        logger.info(f"CMA Injection: {response_msg}")

        await sync_service.record_lead_event(
            state["lead_id"], "AI", f"CMA Generated with ${report.zillow_variance_abs:,.0f} variance.", "thought"
        )

        # Mark CMA as generated in sequence state
        await self.sequence_service.set_cma_generated(state["lead_id"])

        # Emit lead bot sequence update for CMA generation
        await self.event_publisher.publish_lead_bot_sequence_update(
            contact_id=state["lead_id"],
            sequence_day=0,  # CMA can be generated at any time
            action_type="cma_generated",
            success=True,
            message_sent=response_msg,
        )

        return {
            "cma_generated": True,
            "current_step": "nurture",  # Return to nurture or wait for reply
            "last_interaction_time": datetime.now(timezone.utc),
        }

    async def send_day_3_sms(self, state: LeadFollowUpState) -> Dict:
        """Day 3: Soft Check-in with FRS-aware logic via GhostEngine."""
        # Emit lead bot sequence update - starting Day 3
        await self.event_publisher.publish_lead_bot_sequence_update(
            contact_id=state["lead_id"], sequence_day=3, action_type="analysis_started", success=True
        )

        ghost_state = GhostState(
            contact_id=state["lead_id"], current_day=3, frs_score=state["intent_profile"].frs.total_score
        )

        action = await self.ghost_engine.process_lead_step(ghost_state, state["conversation_history"])
        msg = action["content"]

        logger.info(f"Day 3 SMS to {state.get('contact_phone', 'Unknown')}: {msg} (Logic: {action.get('logic')})")
        await sync_service.record_lead_event(state["lead_id"], "AI", f"Sent Day 3 SMS: {msg[:50]}...", "sms")

        # Emit lead bot sequence update - message sent
        await self.event_publisher.publish_lead_bot_sequence_update(
            contact_id=state["lead_id"],
            sequence_day=3,
            action_type="message_sent",
            success=True,
            next_action_date=(datetime.now(timezone.utc) + timedelta(days=4)).isoformat(),  # Day 7
            message_sent=msg,
        )

        # Mark Day 3 as completed in sequence state
        await self.sequence_service.mark_action_completed(state["lead_id"], SequenceDay.DAY_3, "sms_sent")

        # Schedule next sequence action (Day 7 call)
        await self.scheduler.schedule_next_action(state["lead_id"], SequenceDay.DAY_3)

        # Advance sequence to next day
        await self.sequence_service.advance_to_next_day(state["lead_id"])

        # Send SMS via GHL API
        if self.ghl_client:
            try:
                await self.ghl_client.send_message(contact_id=state["lead_id"], message=msg, channel=MessageType.SMS)
                logger.info(f"SMS sent successfully to contact {state['lead_id']}")
            except Exception as e:
                logger.error(f"Failed to send SMS via GHL: {e}")

        return {"engagement_status": "ghosted", "current_step": "day_7_call", "response_content": msg}

    async def initiate_day_7_call(self, state: LeadFollowUpState) -> Dict:
        """Day 7: Initiate Retell AI Call with Stall-Breaker logic."""
        logger.info(f"Initiating Day 7 Call for {state['lead_name']}")

        # Prepare context for the AI agent
        stall_breaker = self._select_stall_breaker(state)
        context = {
            "lead_name": state["lead_name"],
            "property": state.get("property_address"),
            "stall_breaker_script": stall_breaker,
            "frs_score": state["intent_profile"].frs.total_score,
        }

        await sync_service.record_lead_event(state["lead_id"], "AI", "Initiating Day 7 Retell AI Call.", "action")

        # Trigger Retell Call (Fire-and-forget for Dashboard UI performance)
        def _call_finished(fut):
            try:
                fut.result()
                logger.info(f"Background Retell call initiated successfully for {state['lead_name']}")
            except Exception as e:
                logger.error(f"Background Retell call failed for {state['lead_name']}: {e}")

        task = asyncio.create_task(
            self.retell_client.create_call(
                to_number=state["contact_phone"],
                lead_name=state["lead_name"],
                lead_context=context,
                metadata={"contact_id": state["lead_id"]},
            )
        )
        task.add_done_callback(_call_finished)

        # Mark Day 7 as completed in sequence state
        await self.sequence_service.mark_action_completed(state["lead_id"], SequenceDay.DAY_7, "call_initiated")

        # Schedule next sequence action (Day 14 email)
        await self.scheduler.schedule_next_action(state["lead_id"], SequenceDay.DAY_7)

        # Advance sequence to next day
        await self.sequence_service.advance_to_next_day(state["lead_id"])

        return {
            "engagement_status": "ghosted",
            "current_step": "day_14_email",
            "response_content": f"Initiating Day 7 Call with stall breaker: {stall_breaker}",
        }

    async def send_day_14_email(self, state: LeadFollowUpState) -> Dict:
        """Day 14: Value Injection (CMA) via GhostEngine."""
        ghost_state = GhostState(
            contact_id=state["lead_id"], current_day=14, frs_score=state["intent_profile"].frs.total_score
        )
        action = await self.ghost_engine.process_lead_step(ghost_state, state["conversation_history"])

        logger.info(f"Sending Day 14 Email to {state['contact_email']}: {action['content']}")
        await sync_service.record_lead_event(state["lead_id"], "AI", "Sent Day 14 Email with value injection.", "email")

        # Mark Day 14 as completed in sequence state
        await self.sequence_service.mark_action_completed(state["lead_id"], SequenceDay.DAY_14, "email_sent")

        # Schedule next sequence action (Day 30 SMS)
        await self.scheduler.schedule_next_action(state["lead_id"], SequenceDay.DAY_14)

        # Advance sequence to next day
        await self.sequence_service.advance_to_next_day(state["lead_id"])

        # Send email via GHL API (CRM tracking copy)
        if self.ghl_client:
            try:
                await self.ghl_client.send_message(
                    contact_id=state["lead_id"], message=action["content"], channel=MessageType.EMAIL
                )
                logger.info(f"Email sent successfully to contact {state['lead_id']}")
            except Exception as e:
                logger.error(f"Failed to send email via GHL: {e}")

        # Generate CMA PDF and send rich email via SendGrid
        cma_attached = False
        contact_email = state.get("contact_email")
        property_address = state.get("property_address")
        if contact_email and property_address and self.sendgrid_client:
            cma_attached = await self._send_cma_email_with_attachment(
                lead_id=state["lead_id"],
                contact_email=contact_email,
                property_address=property_address,
            )

        return {
            "engagement_status": "ghosted",
            "current_step": "day_30_nudge",
            "response_content": action["content"],
            "cma_attached": cma_attached,
        }

    async def _send_cma_email_with_attachment(self, lead_id: str, contact_email: str, property_address: str) -> bool:
        """Generate a CMA PDF and email it as an attachment via SendGrid.

        Returns True on success, False on any failure.  Never raises.
        """
        import re

        try:
            report = await self.cma_generator.generate_report(property_address)
            pdf_bytes = PDFRenderer.generate_pdf_bytes(report)

            import base64

            b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")

            # Build a filesystem-safe filename from the address
            safe_addr = re.sub(r"[^A-Za-z0-9]+", "_", property_address).strip("_")[:60]
            filename = f"CMA_{safe_addr}.pdf"

            email_html = self._build_cma_email_html(property_address)

            await self.sendgrid_client.send_email(
                to_email=contact_email,
                subject=f"Your Personalized CMA for {property_address}",
                html_content=email_html,
                lead_id=lead_id,
                attachments=[
                    {
                        "content": b64_pdf,
                        "filename": filename,
                        "type": "application/pdf",
                    }
                ],
            )

            await sync_service.record_lead_event(lead_id, "AI", f"CMA PDF emailed to {contact_email}", "email")
            await self.sequence_service.set_cma_generated(lead_id)

            logger.info(f"CMA PDF attachment sent to {contact_email} for lead {lead_id}")
            return True

        except PDFGenerationError as exc:
            logger.error(f"PDF generation failed for lead {lead_id}: {exc}")
            return False
        except Exception as exc:
            logger.error(f"CMA email attachment failed for lead {lead_id}: {exc}")
            return False

    @staticmethod
    def _build_cma_email_html(property_address: str) -> str:
        """Return branded HTML email body referencing the attached CMA PDF."""
        return f"""
<html>
<body style="font-family: Arial, sans-serif; color: #2c3e50; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: #2d5a7a; color: white; padding: 20px; text-align: center;">
        <h1 style="margin: 0; font-size: 22px;">Your Personalized Market Analysis</h1>
    </div>
    <div style="padding: 20px;">
        <p>Hey,</p>
        <p>I went through the comps myself and put together a <strong>Comparative Market Analysis (CMA)</strong> for <strong>{property_address}</strong> so you can see exactly how the market stacks up right now.</p>
        <p>The full report is attached as a PDF. Here's what you'll find inside:</p>
        <ul>
            <li>Current estimated market value with confidence range</li>
            <li>Comparable sales analysis with adjustments</li>
            <li>Zillow Zestimate vs. our AI-powered valuation</li>
            <li>Local market narrative and trends</li>
        </ul>
        <p>Have questions about the numbers? Just reply to this email and I'll
        walk you through everything.</p>
        <p style="margin-top: 25px;">Talk soon,<br><strong>Jorge</strong><br>
        EnterpriseHub Real Estate Intelligence</p>
    </div>
    <div style="border-top: 1px solid #e0e0e0; padding-top: 12px; font-size: 11px; color: #999; text-align: center;">
        Powered by EnterpriseHub AI &bull; Rancho Cucamonga, CA
    </div>
</body>
</html>"""

    async def send_day_30_nudge(self, state: LeadFollowUpState) -> Dict:
        """Day 30: Final qualification attempt via GhostEngine."""
        ghost_state = GhostState(
            contact_id=state["lead_id"], current_day=30, frs_score=state["intent_profile"].frs.total_score
        )
        action = await self.ghost_engine.process_lead_step(ghost_state, state["conversation_history"])

        logger.info(f"Sending Day 30 SMS to {state.get('contact_phone', 'Unknown')}: {action['content']}")
        await sync_service.record_lead_event(state["lead_id"], "AI", "Sent Day 30 final nudge SMS.", "sms")

        # Mark Day 30 as completed in sequence state
        await self.sequence_service.mark_action_completed(state["lead_id"], SequenceDay.DAY_30, "sms_sent")

        # Complete the sequence - move to nurture
        await self.sequence_service.complete_sequence(state["lead_id"], "nurture")

        # Send SMS via GHL API
        if self.ghl_client:
            try:
                await self.ghl_client.send_message(
                    contact_id=state["lead_id"], message=action["content"], channel=MessageType.SMS
                )
                logger.info(f"Day 30 SMS sent successfully to contact {state['lead_id']}")
            except Exception as e:
                logger.error(f"Failed to send Day 30 SMS via GHL: {e}")

        return {"engagement_status": "nurture", "current_step": "nurture", "response_content": action["content"]}

    async def schedule_showing(self, state: LeadFollowUpState) -> Dict:
        """Handle showing coordination with market-aware scheduling."""
        logger.info(f"Scheduling showing for {state['lead_name']} at {state['property_address']}")

        await sync_service.record_lead_event(
            state["lead_id"], "AI", "Coordinating showing with market-aware scheduling.", "thought"
        )

        # Phase 7: Use Smart Scheduler
        from ghl_real_estate_ai.services.calendar_scheduler import get_smart_scheduler

        get_smart_scheduler(self.ghl_client)

        address = state.get("property_address", "the property")
        market_metrics = await self.market_intel.get_market_metrics(address)

        # Inject urgency if market is hot
        if market_metrics and market_metrics.inventory_days < 15:
            pass


        await sync_service.record_lead_event(state["lead_id"], "AI", f"Showing inquiry sent for {address}.", "sms")

        # In a real system, trigger GHL SMS here
        return {"engagement_status": "showing_booked", "current_step": "post_showing"}

    async def post_showing_survey(self, state: LeadFollowUpState) -> Dict:
        """Collect feedback after a showing with behavioral intent capture."""
        logger.info(f"Collecting post-showing feedback from {state['lead_name']}")

        await sync_service.record_lead_event(
            state["lead_id"], "AI", "Collecting post-showing behavioral feedback.", "thought"
        )

        # Use Tone Engine (Jorge style if applicable, or standard)

        await sync_service.record_lead_event(state["lead_id"], "AI", "Post-showing survey sent.", "sms")

        return {"current_step": "facilitate_offer", "engagement_status": "qualified"}

    async def facilitate_offer(self, state: LeadFollowUpState) -> Dict:
        """Guide the lead through the offer submission process using NationalMarketIntelligence."""
        logger.info(f"Facilitating offer for {state['lead_name']}")

        address = state.get("property_address", "the property")
        await sync_service.record_lead_event(
            state["lead_id"], "AI", f"Facilitating offer strategy for {address}", "thought"
        )

        metrics = await self.market_intel.get_market_metrics(address)

        # Generate offer strategy advice
        if metrics:
            if metrics.price_appreciation_1y > 10:
                pass
            else:
                pass


        await sync_service.record_lead_event(state["lead_id"], "AI", "Offer strategy sent to lead.", "sms")

        return {"engagement_status": "offer_sent", "current_step": "closing_nurture"}

    async def contract_to_close_nurture(self, state: LeadFollowUpState) -> Dict:
        """Automated touchpoints during the escrow period with milestone tracking."""
        logger.info(f"Escrow nurture for {state['lead_name']}")

        await sync_service.record_lead_event(
            state["lead_id"], "AI", "Starting escrow nurture and milestone tracking.", "node"
        )

        # Real milestone tracking based on lead state and engagement
        milestone = self._determine_escrow_milestone(state)
        self._get_milestone_message(milestone, state["lead_name"])

        await sync_service.record_lead_event(
            state["lead_id"], "AI", f"Escrow update: {milestone} milestone tracked.", "thought"
        )

        return {"engagement_status": "under_contract", "current_step": "closed"}

    # --- Helper Logic ---

    def _route_next_step(
        self, state: LeadFollowUpState
    ) -> Literal[
        "generate_cma",
        "day_3",
        "day_7",
        "day_14",
        "day_30",
        "schedule_showing",
        "post_showing",
        "facilitate_offer",
        "closing_nurture",
        "qualified",
        "nurture",
    ]:
        """Conditional routing logic."""
        # Fix for phase 3: check for generate_cma first
        if state.get("current_step") == "generate_cma":
            return "generate_cma"

        # Check for lifecycle transitions
        engagement = state["engagement_status"]
        if engagement == "showing_booked":
            return "post_showing"
        if engagement == "offer_sent":
            return "closing_nurture"
        if engagement == "under_contract":
            return "qualified"  # Or specific closing node

        # Logic for booking showings if score is high
        if state["intent_profile"] and state["intent_profile"].frs.classification == "Hot Lead":
            if engagement != "showing_booked":
                return "schedule_showing"

        if state["engagement_status"] == "qualified":
            return "qualified"
        if state["engagement_status"] == "nurture":
            return "nurture"

        # Valid steps mapping
        step = state.get("current_step", "initial")
        if step in ["day_3", "day_7", "day_14", "day_30"]:
            return step

        # Intelligent fallback based on lead signals and engagement
        return self._classify_lead_for_routing(state)

    def _select_stall_breaker(self, state: LeadFollowUpState) -> str:
        """Select the appropriate stall-breaking script based on intent profile via GhostEngine."""
        last_msg = state["conversation_history"][-1]["content"].lower() if state["conversation_history"] else ""

        objection_type = "market_shift"  # Default

        if "thinking" in last_msg:
            objection_type = "thinking_about_it"
        elif "get back" in last_msg:
            objection_type = "get_back_to_you"
        elif "zestimate" in last_msg or "zillow" in last_msg:
            objection_type = "zestimate_reference"
        elif "agent" in last_msg or "realtor" in last_msg:
            objection_type = "has_realtor"

        return self.ghost_engine.get_stall_breaker(objection_type)

    def _determine_escrow_milestone(self, state: LeadFollowUpState) -> str:
        """
        Determine current escrow milestone based on lead state and timeline.

        Milestones in order:
        1. contract_signed - Initial contract execution
        2. inspection - Home inspection period
        3. appraisal - Property appraisal
        4. loan_approval - Final loan approval
        5. final_walkthrough - Pre-closing walkthrough
        6. closing - Closing day
        """
        # Check for milestone indicators in conversation history
        conversation_text = " ".join(msg.get("content", "").lower() for msg in state.get("conversation_history", []))

        # Check custom fields or state for milestone tracking
        custom_fields = state.get("custom_fields", {})
        current_milestone = custom_fields.get("escrow_milestone", "")

        if current_milestone:
            return current_milestone

        # Infer milestone from conversation keywords
        milestone_keywords = {
            "closing": ["closing", "close of escrow", "coe", "keys", "final signing"],
            "final_walkthrough": ["walkthrough", "walk-through", "final walk"],
            "loan_approval": ["loan approved", "clear to close", "ctc", "underwriting"],
            "appraisal": ["appraisal", "appraiser", "appraisal value"],
            "inspection": ["inspection", "inspector", "home inspection"],
            "contract_signed": ["contract", "under contract", "accepted offer"],
        }

        # Check in reverse order (most advanced milestone first)
        for milestone, keywords in milestone_keywords.items():
            if any(kw in conversation_text for kw in keywords):
                return milestone

        # Default to inspection as first major milestone after contract
        return "inspection"

    def _get_milestone_message(self, milestone: str, lead_name: str) -> str:
        """
        Get appropriate message for the current escrow milestone.
        """
        milestone_messages = {
            "contract_signed": f"Congrats {lead_name} on getting under contract! The next step is scheduling the home inspection. I'll help coordinate everything.",
            "inspection": f"Great news {lead_name}! The inspection is the next major milestone. I'll be there to make sure everything is handled properly.",
            "appraisal": f"{lead_name}, the appraisal is coming up. This is when the lender confirms the home's value. I'll keep you posted on the results.",
            "loan_approval": f"Exciting progress {lead_name}! We're waiting on final loan approval. Once we get the clear to close, we're almost there!",
            "final_walkthrough": f"{lead_name}, time for the final walkthrough! This is your chance to verify everything is in order before closing.",
            "closing": f"The big day is here {lead_name}! Closing day - you're about to get the keys to your new home!",
        }

        return milestone_messages.get(
            milestone, f"Congrats {lead_name} on being under contract! I'll keep you updated on each milestone."
        )

    def _classify_lead_for_routing(self, state: LeadFollowUpState) -> Literal["qualified", "nurture"]:
        """
        Classify lead for routing based on intent signals, engagement, and temperature.

        Returns:
            'qualified' if lead shows strong buying/selling signals
            'nurture' if lead needs more engagement
        """
        # Check intent profile for classification
        intent_profile = state.get("intent_profile")
        if intent_profile:
            frs = getattr(intent_profile, "frs", None)
            if frs:
                classification = getattr(frs, "classification", "")
                if classification in ["Hot Lead", "Warm Lead"]:
                    return "qualified"

        # Check lead score from state
        lead_score = state.get("lead_score", 0)
        if lead_score >= 70:
            return "qualified"

        # Analyze conversation for buying signals
        conversation_history = state.get("conversation_history", [])
        if conversation_history:
            recent_messages = conversation_history[-5:]  # Last 5 messages
            message_text = " ".join(
                msg.get("content", "").lower() for msg in recent_messages if msg.get("role") == "user"
            )

            # Strong buying signals
            buying_signals = [
                "pre-approved",
                "preapproved",
                "ready to buy",
                "want to make an offer",
                "schedule a showing",
                "see the house",
                "budget is",
                "looking to buy",
                "sell my house",
                "list my home",
                "what's my home worth",
            ]

            if any(signal in message_text for signal in buying_signals):
                return "qualified"

        # Check engagement status
        engagement = state.get("engagement_status", "")
        if engagement in ["showing_booked", "offer_sent", "under_contract"]:
            return "qualified"

        # Default to nurture for leads needing more engagement
        return "nurture"

    # ================================
    # INTELLIGENCE HELPER METHODS
    # ================================

    def _extract_churn_risk_from_intelligence(self, intelligence_context) -> float:
        """Extract churn risk score from intelligence context for nurture optimization."""
        if not intelligence_context:
            return 0.5  # Default neutral risk

        # Combine multiple intelligence signals for churn risk assessment
        risk_factors = []

        # Sentiment-based risk
        sentiment = intelligence_context.conversation_intelligence.overall_sentiment
        if sentiment < -0.3:
            risk_factors.append(0.8)  # High risk for negative sentiment
        elif sentiment > 0.3:
            risk_factors.append(0.2)  # Low risk for positive sentiment
        else:
            risk_factors.append(0.5)  # Neutral

        # Engagement-based risk
        engagement_score = intelligence_context.composite_engagement_score
        risk_factors.append(1.0 - engagement_score)  # Inverse of engagement

        # Preference completeness as indicator of interest
        preference_completeness = intelligence_context.preference_intelligence.profile_completeness
        if preference_completeness < 0.3:
            risk_factors.append(0.7)  # Higher risk for low preference data
        else:
            risk_factors.append(0.3)  # Lower risk for complete preferences

        # Calculate weighted average
        return sum(risk_factors) / len(risk_factors)

    def _extract_preferred_engagement_timing(self, intelligence_context) -> List[int]:
        """Extract preferred engagement times from intelligence context."""
        if not intelligence_context:
            return [9, 14, 18]  # Default: 9 AM, 2 PM, 6 PM

        # Extract from conversation patterns if available
        urgency_level = intelligence_context.preference_intelligence.urgency_level

        if urgency_level > 0.7:
            # High urgency - morning and evening
            return [8, 17, 19]
        elif urgency_level < 0.3:
            # Low urgency - business hours only
            return [10, 14, 16]
        else:
            # Standard timing
            return [9, 14, 18]

    def _construct_intelligent_day3_message(
        self, state, intelligence_context, personalized_insights: List[str], critical_scenario
    ) -> str:
        """Construct Day 3 message using intelligence insights."""
        lead_name = state["lead_name"]

        # Base message logic
        if critical_scenario:
            base_msg = f"Hi {lead_name}, following up on your property search. I have some time-sensitive information that could be valuable."
        else:
            # Standard nurture message with intelligence enhancements
            if intelligence_context and personalized_insights:
                # Use intelligence insights to personalize the message
                if "property matches" in " ".join(personalized_insights).lower():
                    base_msg = f"Hi {lead_name}, I found some properties that match what you're looking for. Any questions about the market?"
                elif "objections" in " ".join(personalized_insights).lower():
                    base_msg = f"Hi {lead_name}, checking in about your property search. Happy to address any concerns you might have."
                elif "positive sentiment" in " ".join(personalized_insights).lower():
                    base_msg = f"Hi {lead_name}, hope you're doing well! Any updates on your property search?"
                else:
                    base_msg = (
                        f"Hi {lead_name}, checking in about your property search. Any questions about the market?"
                    )
            else:
                # Fallback to standard message
                base_msg = f"Hi {lead_name}, checking in about your property search. Any questions about the market?"

        return base_msg

    def _construct_adaptive_day14_message(
        self, state, intelligence_context, preferred_channel: str, content_adaptation_applied: bool
    ) -> str:
        """Construct adaptive Day 14 message using intelligence insights."""
        lead_name = state["lead_name"]

        if intelligence_context and content_adaptation_applied:
            property_matches = intelligence_context.property_intelligence.match_count
            objections = intelligence_context.conversation_intelligence.objections_detected
            sentiment = intelligence_context.conversation_intelligence.overall_sentiment

            if property_matches > 0 and sentiment >= 0:
                if preferred_channel == "Voice":
                    msg = f"Hey {lead_name}, found {property_matches} places matching what you described. Quick call to go over them?"
                else:
                    msg = f"Hey {lead_name}, found {property_matches} places matching what you described. Sending details—let me know your thoughts!"

            elif objections and sentiment < 0:
                if preferred_channel == "Voice":
                    msg = (
                        f"Hey {lead_name}, I hear you on the concerns. Easier to talk it through—open to a quick call?"
                    )
                else:
                    msg = f"Hey {lead_name}, totally understand the hesitation. Happy to answer questions—what's on your mind?"

            else:
                # Standard follow-up with intelligence hints
                msg = f"Hey {lead_name}, been watching the market for you. Anything new on your end?"
        else:
            # Fallback standard message
            msg = f"Hey {lead_name}, checking in on your search. Spotted some good inventory lately—interested?"

        return msg

    def _construct_intelligent_day30_message(
        self, state, final_strategy: str, intelligence_score: float, handoff_reasoning: List[str]
    ) -> str:
        """Construct intelligent Day 30 message based on final strategy."""
        lead_name = state["lead_name"]

        if final_strategy == "jorge_qualification":
            msg = f"Hey {lead_name}, been 30 days—sounds like you're getting serious. Want me to connect you with Jorge for a deeper market breakdown?"

        elif final_strategy == "jorge_consultation":
            msg = f"Hey {lead_name}, market's moving in your area. Jorge can give you the full picture—want me to set up a quick call?"

        elif final_strategy == "graceful_disengage":
            msg = f"Hey {lead_name}, just checking—still looking or should I pause the updates? No pressure either way."

        else:  # nurture
            msg = f"Hey {lead_name}, it's been a month. Anything change with your timeline? I'm here when you're ready."

        return msg

    async def _publish_intelligent_jorge_handoff_request(
        self, state, intelligence_context, handoff_type: str, intelligence_score: float, handoff_reasoning: List[str]
    ):
        """Publish enhanced Jorge handoff request with comprehensive intelligence context."""
        handoff_data = {
            "handoff_type": handoff_type,
            "intelligence_score": intelligence_score,
            "handoff_reasoning": handoff_reasoning,
            "sequence_completion": "day_30_reached",
            "recommendation": f"Jorge {handoff_type} recommended based on comprehensive intelligence analysis",
        }

        # Add intelligence context details if available
        if intelligence_context:
            handoff_data.update(
                {
                    "engagement_score": intelligence_context.composite_engagement_score,
                    "property_matches": intelligence_context.property_intelligence.match_count,
                    "objections_count": len(intelligence_context.conversation_intelligence.objections_detected),
                    "sentiment": intelligence_context.conversation_intelligence.overall_sentiment,
                    "preference_completeness": intelligence_context.preference_intelligence.profile_completeness,
                    "recommended_approach": intelligence_context.recommended_approach,
                    "priority_insights": intelligence_context.priority_insights,
                }
            )

        # Add traditional analytics if available
        churn_risk = state.get("churn_risk_score")
        if churn_risk:
            handoff_data["churn_risk_score"] = churn_risk

        await self.event_publisher.publish_bot_handoff_request(
            handoff_id=str(uuid4()),
            from_bot="enhanced-lead-bot",
            to_bot="jorge-seller-bot",
            contact_id=state["lead_id"],
            data=handoff_data,
        )

        logger.info(
            f"Intelligent Jorge handoff request published for {state['lead_name']} "
            f"(type: {handoff_type}, score: {intelligence_score:.2f})"
        )

    # ================================
    # UNIFIED PROCESSING METHODS
    # ================================

    async def process_lead_conversation(
        self,
        conversation_id: str,
        user_message: str,
        lead_name: Optional[str] = None,
        conversation_history: Optional[List[ConversationMessage]] = None,
        sequence_day: int = 0,
        lead_phone: Optional[str] = None,
        lead_email: Optional[str] = None,
        metadata: Optional[BotMetadata] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point for processing lead conversations.

        This is the primary public API method for the Lead Bot, providing a simple
        interface for processing incoming lead messages through the LangGraph workflow.

        Args:
            conversation_id: Unique identifier for the conversation
            user_message: The incoming message from the lead
            lead_name: Optional name of the lead
            conversation_history: Optional list of previous messages
            sequence_day: Day in the follow-up sequence (0 = initial contact)
            lead_phone: Optional phone number for SMS follow-ups
            lead_email: Optional email for email follow-ups
            metadata: Optional additional metadata

        Returns:
            Dict containing:
                - response_content: Bot's response message
                - lead_id: The conversation/lead identifier
                - current_step: Next action in the workflow
                - engagement_status: Current engagement state
                - temperature: Lead temperature if predicted
                - handoff_signals: Signals for cross-bot handoff
        """
        MAX_MESSAGE_LENGTH = 10_000

        # Input validation
        if not conversation_id or not str(conversation_id).strip():
            raise ValueError("conversation_id must be a non-empty string")
        if not user_message or not str(user_message).strip():
            return {
                "conversation_id": conversation_id,
                "response_content": "I didn't catch that. Could you say more?",
                "current_step": "awaiting_input",
                "engagement_status": "active",
                "handoff_signals": {},
            }
        user_message = str(user_message).strip()[:MAX_MESSAGE_LENGTH]

        try:
            _workflow_start = time.time()

            # Build conversation history if not provided
            if conversation_history is None:
                conversation_history = []

            # Add the user message to history
            conversation_history.append(
                {"role": "user", "content": user_message, "timestamp": datetime.now(timezone.utc).isoformat()}
            )

            # Prune to prevent unbounded memory growth
            if len(conversation_history) > self.MAX_CONVERSATION_HISTORY:
                conversation_history = conversation_history[-self.MAX_CONVERSATION_HISTORY :]

            # Get A/B test variant for response tone
            try:
                _tone_variant = await self.ab_testing.get_variant(
                    ABTestingService.RESPONSE_TONE_EXPERIMENT, conversation_id
                )
            except (KeyError, ValueError):
                _tone_variant = "empathetic"

            # Create initial state for the workflow
            initial_state = {
                "lead_id": conversation_id,
                "lead_name": lead_name or f"Lead {conversation_id}",
                "conversation_history": conversation_history,
                "sequence_day": sequence_day,
                "engagement_status": "responsive",
                "cma_generated": False,
                "user_message": user_message,
                "tone_variant": _tone_variant,
                # Enhanced fields
                "response_pattern": None,
                "personality_type": None,
                "temperature_prediction": None,
                "sequence_optimization": None,
                # Track 3.1 fields
                "journey_analysis": None,
                "conversion_analysis": None,
                "touchpoint_analysis": None,
                "enhanced_optimization": None,
                "critical_scenario": None,
                "track3_applied": False,
                # Phase 3.3 Intelligence Enhancement fields
                "intelligence_context": None,
                "intelligence_performance_ms": 0.0,
                "preferred_engagement_timing": None,
                "churn_risk_score": None,
                "cross_bot_preferences": None,
                "sequence_optimization_applied": False,
            }

            # Add optional metadata
            if lead_phone:
                initial_state["lead_phone"] = lead_phone
            if lead_email:
                initial_state["lead_email"] = lead_email
            if metadata:
                initial_state["metadata"] = metadata

            # Execute the workflow
            result = await self.workflow.ainvoke(initial_state)

            _workflow_duration_ms = (time.time() - _workflow_start) * 1000
            # Update performance statistics
            self.workflow_stats["total_interactions"] += 1

            # Extract handoff signals for cross-bot handoff detection
            handoff_signals = {}
            if self.config.jorge_handoff_enabled:
                from ghl_real_estate_ai.services.jorge.jorge_handoff_service import JorgeHandoffService

                handoff_signals = JorgeHandoffService.extract_intent_signals(user_message)

            result["handoff_signals"] = handoff_signals

            # Tag response with A/B experiment metadata
            result["ab_test"] = {
                "experiment_id": ABTestingService.RESPONSE_TONE_EXPERIMENT,
                "variant": _tone_variant,
            }

            # Record performance metrics
            await self.performance_tracker.track_operation("lead_bot", "process", _workflow_duration_ms, success=True)
            self.metrics_collector.record_bot_interaction("lead", duration_ms=_workflow_duration_ms, success=True)

            # Feed metrics to alerting (non-blocking)
            try:
                self.metrics_collector.feed_to_alerting(self.alerting_service)
            except Exception as e:
                logger.debug(f"Failed to feed metrics to alerting: {str(e)}")

            # Record A/B test outcome
            try:
                await self.ab_testing.record_outcome(
                    ABTestingService.RESPONSE_TONE_EXPERIMENT,
                    conversation_id,
                    _tone_variant,
                    "response",
                )
            except (KeyError, ValueError):
                pass

            # Emit conversation processed event
            await self.event_publisher.publish_bot_status_update(
                bot_type="lead-bot",
                contact_id=conversation_id,
                status="completed",
                current_step=result.get("current_step", "unknown"),
            )

            return result

        except Exception as e:
            # Record failure metrics
            try:
                _fail_duration = (time.time() - _workflow_start) * 1000
                await self.performance_tracker.track_operation("lead_bot", "process", _fail_duration, success=False)
                self.metrics_collector.record_bot_interaction("lead", duration_ms=_fail_duration, success=False)
            except Exception as ex:
                logger.debug(f"Secondary failure in error metrics recording: {str(ex)}")

            logger.error(f"Error processing lead conversation for {conversation_id}: {str(e)}")
            return {
                "conversation_id": conversation_id,
                "error": str(e),
                "response_content": "I apologize, but I encountered an issue processing your message. Please try again.",
                "current_step": "error",
                "engagement_status": "error",
                "handoff_signals": {},
            }

    async def process_enhanced_lead_sequence(
        self, lead_id: str, sequence_day: int, conversation_history: List[Dict]
    ) -> Dict[str, Any]:
        """
        Process lead through enhanced workflow with all enabled enhancements.
        This is the primary entry point for the enhanced Lead Bot.
        """
        self.workflow_stats["total_sequences"] += 1

        initial_state = {
            "lead_id": lead_id,
            "lead_name": f"Lead {lead_id}",
            "conversation_history": conversation_history,
            "sequence_day": sequence_day,
            "engagement_status": "responsive",
            "cma_generated": False,
            # Enhanced fields
            "response_pattern": None,
            "personality_type": None,
            "temperature_prediction": None,
            "sequence_optimization": None,
            # Track 3.1 fields
            "journey_analysis": None,
            "conversion_analysis": None,
            "touchpoint_analysis": None,
            "enhanced_optimization": None,
            "critical_scenario": None,
            "track3_applied": False,
            # Phase 3.3 Intelligence Enhancement fields
            "intelligence_context": None,
            "intelligence_performance_ms": 0.0,
            "preferred_engagement_timing": None,
            "churn_risk_score": None,
            "cross_bot_preferences": None,
            "sequence_optimization_applied": False,
        }

        return await self.workflow.ainvoke(initial_state)

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics for all enabled features"""

        # Base metrics
        metrics = {
            "workflow_statistics": self.workflow_stats,
            "features_enabled": {
                "predictive_analytics": self.config.enable_predictive_analytics,
                "behavioral_optimization": self.config.enable_behavioral_optimization,
                "personality_adaptation": self.config.enable_personality_adaptation,
                "track3_intelligence": self.config.enable_track3_intelligence,
                "jorge_handoff": self.config.jorge_handoff_enabled,
                "bot_intelligence": self.config.enable_bot_intelligence,
            },
        }

        # Behavioral optimization metrics
        if self.config.enable_behavioral_optimization and self.workflow_stats["total_sequences"] > 0:
            metrics["behavioral_optimization"] = {
                "optimizations_applied": self.workflow_stats["behavioral_optimizations"],
                "optimization_rate": self.workflow_stats["behavioral_optimizations"]
                / self.workflow_stats["total_sequences"],
            }

        # Personality adaptation metrics
        if self.config.enable_personality_adaptation:
            metrics["personality_adaptation"] = {
                "adaptations_applied": self.workflow_stats["personality_adaptations"],
                "adaptation_rate": self.workflow_stats["personality_adaptations"]
                / max(self.workflow_stats["total_sequences"], 1),
            }

        # Track 3.1 metrics
        if self.config.enable_track3_intelligence:
            metrics["track3_intelligence"] = {
                "enhancements_applied": self.workflow_stats["track3_enhancements"],
                "enhancement_rate": self.workflow_stats["track3_enhancements"]
                / max(self.workflow_stats["total_sequences"], 1),
            }

        # Jorge handoff metrics
        if self.config.jorge_handoff_enabled:
            metrics["jorge_handoffs"] = {
                "total_handoffs": self.workflow_stats["jorge_handoffs"],
                "handoff_rate": self.workflow_stats["jorge_handoffs"] / max(self.workflow_stats["total_sequences"], 1),
            }

        # Bot Intelligence metrics
        if self.config.enable_bot_intelligence:
            metrics["bot_intelligence"] = {
                "intelligence_operations": self.workflow_stats["intelligence_gathering_operations"],
                "intelligence_rate": self.workflow_stats["intelligence_gathering_operations"]
                / max(self.workflow_stats["total_sequences"], 1),
                "middleware_available": self.intelligence_middleware is not None,
            }

            # Include middleware metrics if available
            if self.intelligence_middleware:
                middleware_metrics = self.intelligence_middleware.get_metrics()
                metrics["bot_intelligence"]["middleware_metrics"] = middleware_metrics

        return metrics

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check of all enabled systems"""
        health_status = {
            "lead_bot": "healthy",
            "predictive_analytics": "disabled",
            "behavioral_optimization": "disabled",
            "personality_adaptation": "disabled",
            "track3_intelligence": "disabled",
            "bot_intelligence": "disabled",
            "overall_status": "healthy",
        }

        # Check predictive analytics
        if self.config.enable_predictive_analytics:
            health_status["predictive_analytics"] = "healthy" if self.temperature_engine else "misconfigured"

        # Check behavioral optimization
        if self.config.enable_behavioral_optimization:
            health_status["behavioral_optimization"] = "healthy" if self.analytics_engine else "misconfigured"

        # Check personality adaptation
        if self.config.enable_personality_adaptation:
            health_status["personality_adaptation"] = "healthy" if self.personality_adapter else "misconfigured"

        # Check Track 3.1 intelligence
        if self.config.enable_track3_intelligence:
            health_status["track3_intelligence"] = "healthy" if self.ml_analytics else "dependencies_missing"
            if not TRACK3_ML_AVAILABLE:
                health_status["track3_intelligence"] = "dependencies_missing"
                health_status["overall_status"] = "degraded"

        # Check Bot Intelligence
        if self.config.enable_bot_intelligence:
            health_status["bot_intelligence"] = "healthy" if self.intelligence_middleware else "dependencies_missing"
            if not BOT_INTELLIGENCE_AVAILABLE:
                health_status["bot_intelligence"] = "dependencies_missing"
                health_status["overall_status"] = "degraded"

        return health_status

    # ================================
    # FACTORY METHODS
    # ================================

    @classmethod
    def create_standard_lead_bot(cls, ghl_client=None) -> "LeadBotWorkflow":
        """Factory method: Create standard lead bot (3-7-30 sequence only)"""
        config = LeadBotConfig()
        return cls(ghl_client=ghl_client, config=config)

    @classmethod
    def create_enhanced_lead_bot(cls, ghl_client=None) -> "LeadBotWorkflow":
        """Factory method: Create lead bot with behavioral optimization"""
        config = LeadBotConfig(
            enable_behavioral_optimization=True, enable_personality_adaptation=True, enable_predictive_analytics=True
        )
        return cls(ghl_client=ghl_client, config=config)

    @classmethod
    def create_enterprise_lead_bot(cls, ghl_client=None) -> "LeadBotWorkflow":
        """Factory method: Create fully-enhanced enterprise lead bot"""
        config = LeadBotConfig(
            enable_predictive_analytics=True,
            enable_behavioral_optimization=True,
            enable_personality_adaptation=True,
            enable_track3_intelligence=True,
            enable_bot_intelligence=True,
            jorge_handoff_enabled=True,
        )
        return cls(ghl_client=ghl_client, config=config)

    @classmethod
    def create_intelligence_enhanced_lead_bot(cls, ghl_client=None) -> "LeadBotWorkflow":
        """Factory method: Create lead bot with Phase 3.3 Intelligence Middleware"""
        config = LeadBotConfig(enable_bot_intelligence=True, jorge_handoff_enabled=True)
        return cls(ghl_client=ghl_client, config=config)


# ================================
# FACTORY FUNCTIONS FOR EASY USE
# ================================


def get_lead_bot(enhancement_level: str = "standard", ghl_client=None) -> LeadBotWorkflow:
    """
    Factory function to get Lead Bot with specified enhancement level

    Args:
        enhancement_level: "standard", "enhanced", or "enterprise"
        ghl_client: Optional GHL client
    """
    if enhancement_level == "enhanced":
        return LeadBotWorkflow.create_enhanced_lead_bot(ghl_client)
    elif enhancement_level == "enterprise":
        return LeadBotWorkflow.create_enterprise_lead_bot(ghl_client)
    else:
        return LeadBotWorkflow.create_standard_lead_bot(ghl_client)


# Backward compatibility
def get_predictive_lead_bot(ghl_client=None) -> LeadBotWorkflow:
    """Factory function for backward compatibility - returns enterprise lead bot"""
    return LeadBotWorkflow.create_enterprise_lead_bot(ghl_client)
