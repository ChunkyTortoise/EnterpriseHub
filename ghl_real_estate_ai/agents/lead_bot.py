import asyncio
import json
import uuid
import threading
from typing import Dict, Any, Literal, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from collections import OrderedDict
from langgraph.graph import StateGraph, END

from ghl_real_estate_ai.models.workflows import LeadFollowUpState
from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder
from ghl_real_estate_ai.agents.cma_generator import CMAGenerator
from ghl_real_estate_ai.services.ghost_followup_engine import get_ghost_followup_engine, GhostState
from ghl_real_estate_ai.utils.pdf_renderer import PDFRenderer
from ghl_real_estate_ai.integrations.retell import RetellClient
from ghl_real_estate_ai.integrations.lyrio import LyrioClient
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.agent_state_sync import sync_service
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.services.lead_sequence_state_service import get_sequence_service, SequenceDay, LeadSequenceState, SequenceStatus
from ghl_real_estate_ai.services.lead_sequence_scheduler import get_lead_scheduler
from ghl_real_estate_ai.api.schemas.ghl import MessageType

# Enhanced Features (Track 3.1 Integration)
try:
    from bots.shared.ml_analytics_engine import (
        MLAnalyticsEngine,
        LeadJourneyPrediction,
        ConversionProbabilityAnalysis,
        TouchpointOptimization
    )
    TRACK3_ML_AVAILABLE = True
except ImportError:
    TRACK3_ML_AVAILABLE = False

logger = get_logger(__name__)

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
                key for key, (_, timestamp) in self._cache.items()
                if current_time - timestamp > self._ttl_seconds
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
        self._patterns_cache = TTLLRUCache(
            max_entries=self.CACHE_MAX_ENTRIES,
            ttl_seconds=self.CACHE_TTL_SECONDS
        )
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

        # Calculate response velocity
        response_times = []
        for i in range(1, len(conversation_history)):
            current_msg = conversation_history[i]
            prev_msg = conversation_history[i-1]

            # Mock timestamp analysis (in production, use actual timestamps)
            if current_msg.get('role') == 'user' and prev_msg.get('role') == 'assistant':
                response_times.append(4.5)  # Mock: 4.5 hours average

        avg_response_hours = sum(response_times) / len(response_times) if response_times else 24.0

        # Determine engagement velocity
        if avg_response_hours < 2:
            velocity = "fast"
        elif avg_response_hours < 12:
            velocity = "moderate"
        else:
            velocity = "slow"

        # Analyze channel preferences (mock implementation)
        channel_prefs = {
            "SMS": 0.8,
            "Email": 0.3,
            "Voice": 0.6,
            "WhatsApp": 0.2
        }

        # Analyze message length preference
        avg_msg_length = sum(len(m.get('content', '').split()) for m in conversation_history if m.get('role') == 'user')
        avg_msg_length = avg_msg_length / max(1, len([m for m in conversation_history if m.get('role') == 'user']))

        length_pref = "brief" if avg_msg_length < 10 else "detailed"

        pattern = ResponsePattern(
            avg_response_hours=avg_response_hours,
            response_count=len([m for m in conversation_history if m.get('role') == 'user']),
            channel_preferences=channel_prefs,
            engagement_velocity=velocity,
            best_contact_times=[9, 14, 18],  # Mock: 9 AM, 2 PM, 6 PM
            message_length_preference=length_pref
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

    async def predict_optimal_sequence(self, pattern: ResponsePattern) -> SequenceOptimization:
        """Predict optimal sequence timing based on behavioral patterns"""

        # Optimize intervals based on response velocity
        if pattern.engagement_velocity == "fast":
            # Accelerate sequence for fast responders
            optimization = SequenceOptimization(
                day_3=1,    # Contact tomorrow
                day_7=3,    # Contact in 3 days
                day_14=7,   # Contact in 1 week
                day_30=14,  # Contact in 2 weeks
                channel_sequence=["SMS", "Voice", "SMS", "Email"]
            )
        elif pattern.engagement_velocity == "slow":
            # Extend intervals for slow responders
            optimization = SequenceOptimization(
                day_3=5,    # Wait 5 days
                day_7=14,   # Wait 2 weeks
                day_14=21,  # Wait 3 weeks
                day_30=45,  # Wait 6+ weeks
                channel_sequence=["Email", "SMS", "Voice", "SMS"]
            )
        else:
            # Standard intervals for moderate responders
            optimization = SequenceOptimization(
                day_3=3,
                day_7=7,
                day_14=14,
                day_30=30,
                channel_sequence=["SMS", "Email", "Voice", "SMS"]
            )

        # Adjust channel sequence based on preferences
        sorted_channels = sorted(
            pattern.channel_preferences.items(),
            key=lambda x: x[1],
            reverse=True
        )
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
                "keywords": ["analysis", "data", "research", "comparison"]
            },
            "relationship": {
                "style": "personal",
                "tone": "warm",
                "format": "conversational",
                "keywords": ["understand", "help", "partnership", "together"]
            },
            "results": {
                "style": "direct",
                "tone": "urgent",
                "format": "brief",
                "keywords": ["action", "results", "quickly", "efficiently"]
            },
            "security": {
                "style": "cautious",
                "tone": "reassuring",
                "format": "detailed",
                "keywords": ["safe", "secure", "guaranteed", "protected"]
            }
        }

    async def detect_personality(self, conversation_history: List[Dict]) -> str:
        """Detect lead personality type from conversation patterns"""
        all_text = " ".join([m.get("content", "").lower() for m in conversation_history])

        personality_scores = {}
        for personality, profile in self.personality_profiles.items():
            score = sum(1 for keyword in profile["keywords"] if keyword in all_text)
            personality_scores[personality] = score

        # Return highest scoring personality or default to 'relationship'
        return max(personality_scores, key=personality_scores.get) if any(personality_scores.values()) else "relationship"

    async def adapt_message(self, base_message: str, personality_type: str, pattern: ResponsePattern) -> str:
        """Adapt message based on personality type and response patterns"""
        profile = self.personality_profiles.get(personality_type, self.personality_profiles["relationship"])

        # Adjust message length based on preference
        if pattern.message_length_preference == "brief" and profile["format"] != "brief":
            # Shorten message for brief preference
            sentences = base_message.split('. ')
            adapted_message = '. '.join(sentences[:2]) + '.'
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
        current_temp = (current_scores.get('frs_score', 0) + current_scores.get('pcs_score', 0)) / 2

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
                "suggested_action": "Schedule call within 24 hours"
            }

        return {
            "current_temperature": current_temp,
            "trend": trend,
            "confidence": confidence,
            "early_warning": early_warning,
            "prediction_next_interaction": max(0, current_temp + (diff * 1.5))
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

    def __init__(self, ghl_client=None, config: Optional[LeadBotConfig] = None):
        # Core components (always initialized)
        self.config = config or LeadBotConfig()
        self.intent_decoder = LeadIntentDecoder()
        self.retell_client = RetellClient()
        self.cma_generator = CMAGenerator()
        self.ghost_engine = get_ghost_followup_engine()
        self.ghl_client = ghl_client
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

        # Performance tracking
        self.workflow_stats = {
            "total_sequences": 0,
            "behavioral_optimizations": 0,
            "personality_adaptations": 0,
            "track3_enhancements": 0,
            "jorge_handoffs": 0
        }

        # Build workflow based on enabled features
        self.workflow = self._build_unified_graph()

    def _build_unified_graph(self) -> StateGraph:
        """Build workflow graph based on enabled features"""
        if (self.config.enable_predictive_analytics or
            self.config.enable_behavioral_optimization or
            self.config.enable_track3_intelligence):
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
                "nurture": END
            }
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
                "nurture": END
            }
        )

        # All actions end
        for node in ["generate_cma", "send_optimized_day_3", "initiate_predictive_day_7",
                    "send_adaptive_day_14", "send_intelligent_day_30", "schedule_showing",
                    "post_showing_survey", "facilitate_offer", "contract_to_close_nurture"]:
            workflow.add_edge(node, END)

        return workflow.compile()

    # ================================
    # ENHANCED FEATURE METHODS
    # ================================

    async def analyze_behavioral_patterns(self, state: LeadFollowUpState) -> Dict:
        """Analyze lead behavioral patterns for optimization"""
        logger.info(f"Analyzing behavioral patterns for lead {state['lead_id']}")

        await self.event_publisher.publish_bot_status_update(
            bot_type="enhanced-lead-bot",
            contact_id=state["lead_id"],
            status="processing",
            current_step="behavioral_analysis"
        )

        # Initialize defaults
        pattern = None
        personality = "relationship"
        temperature_prediction = None

        # Analyze response patterns if engine available
        if self.analytics_engine:
            pattern = await self.analytics_engine.analyze_response_patterns(
                state['lead_id'],
                state['conversation_history']
            )
            self.workflow_stats["behavioral_optimizations"] += 1

        # Detect personality type if adapter available
        if self.personality_adapter:
            personality = await self.personality_adapter.detect_personality(state['conversation_history'])
            self.workflow_stats["personality_adaptations"] += 1

        # Predict temperature trend if engine available
        if self.temperature_engine:
            current_scores = {
                'frs_score': state['intent_profile'].frs.total_score,
                'pcs_score': state['intent_profile'].pcs.total_score
            }
            temperature_prediction = await self.temperature_engine.predict_temperature_trend(
                state['lead_id'],
                current_scores
            )

        # Emit behavioral analysis event
        await self.event_publisher.publish_behavioral_prediction(
            lead_id=state["lead_id"],
            location_id="national",
            behavior_category=personality,
            churn_risk_score=0.1,  # Mocked for now
            engagement_score=0.8,  # Mocked for now
            next_actions=[],
            prediction_latency_ms=0.0
        )

        return {
            "response_pattern": pattern,
            "personality_type": personality,
            "temperature_prediction": temperature_prediction
        }

    async def predict_sequence_optimization(self, state: LeadFollowUpState) -> Dict:
        """Predict optimal sequence timing and channels"""
        logger.info(f"Optimizing sequence for lead {state['lead_id']}")

        if not self.analytics_engine or not state.get('response_pattern'):
            # Return default optimization
            default_optimization = SequenceOptimization(
                day_3=3, day_7=7, day_14=14, day_30=30,
                channel_sequence=["SMS", "Email", "Voice", "SMS"]
            )
            return {"sequence_optimization": default_optimization}

        pattern = state['response_pattern']
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
            current_step="track3_market_analysis"
        )

        try:
            if not self.ml_analytics:
                logger.warning("Track 3.1 ML analytics not available")
                return {"track3_applied": False, "fallback_reason": "ML analytics not available"}

            # Track 3.1 enhancement: Get comprehensive predictive analysis
            journey_analysis = await self.ml_analytics.predict_lead_journey(state['lead_id'])
            conversion_analysis = await self.ml_analytics.predict_conversion_probability(
                state['lead_id'],
                state.get('current_journey_stage', 'nurture')
            )
            touchpoint_analysis = await self.ml_analytics.predict_optimal_touchpoints(state['lead_id'])

            # Apply market timing enhancements
            enhanced_optimization = await self._apply_market_timing_intelligence(
                state.get('sequence_optimization'),
                journey_analysis,
                conversion_analysis,
                touchpoint_analysis
            )

            # Detect critical scenarios
            critical_scenario = await self._detect_critical_scenarios(
                journey_analysis, conversion_analysis, state
            )

            self.workflow_stats["track3_enhancements"] += 1

            return {
                "journey_analysis": journey_analysis,
                "conversion_analysis": conversion_analysis,
                "touchpoint_analysis": touchpoint_analysis,
                "enhanced_optimization": enhanced_optimization,
                "critical_scenario": critical_scenario,
                "track3_applied": True
            }

        except Exception as e:
            logger.error(f"Track 3.1 market intelligence failed for {state['lead_id']}: {e}")
            return {"track3_applied": False, "fallback_reason": str(e)}

    async def send_optimized_day_3(self, state: LeadFollowUpState) -> Dict:
        """Day 3 with enhanced timing and personalization"""
        # Use enhanced optimization if available
        optimization = state.get('enhanced_optimization', state.get('sequence_optimization'))
        pattern = state.get('response_pattern')
        personality = state.get('personality_type', 'relationship')

        # Use optimized timing if available
        actual_day = optimization.day_3 if optimization else 3
        preferred_channel = optimization.channel_sequence[0] if optimization and optimization.channel_sequence else "SMS"

        # Check for critical scenarios
        critical_scenario = state.get('critical_scenario')
        if critical_scenario and critical_scenario.get('urgency') == 'critical':
            logger.warning(f"CRITICAL SCENARIO: {critical_scenario['type']} - {critical_scenario['recommendation']}")
            actual_day = 0  # Contact immediately
            preferred_channel = "Voice"  # Use most direct channel

        # Base message
        if critical_scenario:
            base_msg = f"Hi {state['lead_name']}, following up on your property search. I have some time-sensitive information that could be valuable."
        else:
            base_msg = f"Hi {state['lead_name']}, checking in about your property search. Any questions about the market?"

        # Adapt message for personality if adapter available
        adapted_msg = base_msg
        if self.personality_adapter and pattern:
            adapted_msg = await self.personality_adapter.adapt_message(base_msg, personality, pattern)

        logger.info(f"Enhanced Day {actual_day} {preferred_channel} to {state['lead_name']}: {adapted_msg}")

        return {
            "engagement_status": "enhanced_nurture",
            "current_step": "day_7_call",
            "response_content": adapted_msg,
            "optimized_timing_applied": bool(optimization),
            "personalization_applied": bool(self.personality_adapter),
            "track3_enhancement_applied": state.get('track3_applied', False),
            "critical_scenario_handled": bool(critical_scenario)
        }

    async def initiate_predictive_day_7(self, state: LeadFollowUpState) -> Dict:
        """Day 7 with predictive timing and channel optimization"""
        optimization = state.get('enhanced_optimization', state.get('sequence_optimization'))
        temperature_pred = state.get('temperature_prediction')
        journey_analysis = state.get('journey_analysis')
        conversion_analysis = state.get('conversion_analysis')

        # Check conversion probability for Jorge handoff consideration
        if (conversion_analysis and
            conversion_analysis.stage_conversion_probability > 0.7 and
            journey_analysis and
            journey_analysis.conversion_probability > 0.6):

            logger.info(f"High conversion indicators for {state['lead_name']} - consider Jorge handoff")
            if self.config.jorge_handoff_enabled:
                await self._publish_jorge_handoff_recommendation(state, journey_analysis, conversion_analysis)

        # Check for temperature early warning
        if temperature_pred and temperature_pred.get('early_warning'):
            logger.warning(f"Temperature early warning for {state['lead_name']}: {temperature_pred['early_warning']['recommendation']}")

        preferred_channel = optimization.channel_sequence[1] if optimization and len(optimization.channel_sequence) > 1 else "Voice"
        actual_day = optimization.day_7 if optimization else 7

        msg = f"Predictive Day {actual_day} {preferred_channel} call for {state['lead_name']}"
        logger.info(msg)

        return {
            "engagement_status": "enhanced_nurture",
            "current_step": "day_14_email",
            "response_content": msg,
            "jorge_handoff_eligible": (
                conversion_analysis and conversion_analysis.stage_conversion_probability > 0.7
            ) if conversion_analysis else False
        }

    async def send_adaptive_day_14(self, state: LeadFollowUpState) -> Dict:
        """Day 14 with adaptive messaging and channel selection"""
        optimization = state.get('enhanced_optimization', state.get('sequence_optimization'))
        personality = state.get('personality_type', 'relationship')
        journey_analysis = state.get('journey_analysis')
        conversion_analysis = state.get('conversion_analysis')

        preferred_channel = optimization.channel_sequence[2] if optimization and len(optimization.channel_sequence) > 2 else "Email"
        actual_day = optimization.day_14 if optimization else 14

        # Check for bottlenecks requiring intervention
        intervention_needed = False
        if (journey_analysis and journey_analysis.stage_bottlenecks and
            conversion_analysis and conversion_analysis.urgency_score > 0.6):

            intervention_needed = True
            logger.warning(f"Stage bottlenecks detected for {state['lead_name']}: {journey_analysis.stage_bottlenecks}")
            preferred_channel = "Voice"  # Override to voice call for bottleneck resolution

        msg = f"Adaptive Day {actual_day} {preferred_channel} for {state['lead_name']}"
        logger.info(msg)

        return {
            "engagement_status": "enhanced_nurture",
            "current_step": "day_30_nudge",
            "response_content": msg,
            "bottleneck_intervention": intervention_needed,
            "channel_escalated": intervention_needed
        }

    async def send_intelligent_day_30(self, state: LeadFollowUpState) -> Dict:
        """Day 30 with intelligent re-engagement strategy"""
        optimization = state.get('enhanced_optimization', state.get('sequence_optimization'))
        temperature_pred = state.get('temperature_prediction')
        journey_analysis = state.get('journey_analysis')
        conversion_analysis = state.get('conversion_analysis')

        actual_day = optimization.day_30 if optimization else 30

        # Final decision point - nurture vs qualify vs disengage
        final_strategy = "nurture"  # Default

        if journey_analysis and conversion_analysis:
            # High potential - recommend Jorge qualification
            if (journey_analysis.conversion_probability > 0.5 and
                conversion_analysis.stage_conversion_probability > 0.4):
                final_strategy = "jorge_qualification"

                if self.config.jorge_handoff_enabled:
                    await self._publish_jorge_handoff_request(state, journey_analysis, conversion_analysis)
                    self.workflow_stats["jorge_handoffs"] += 1

            # Low potential with cooling trend - disengage gracefully
            elif (journey_analysis.conversion_probability < 0.2 and
                  conversion_analysis.drop_off_risk > 0.8):
                final_strategy = "graceful_disengage"

        msg = f"Intelligent Day {actual_day} final engagement for {state['lead_name']} - Strategy: {final_strategy}"
        logger.info(msg)

        return {
            "engagement_status": "enhanced_final",
            "current_step": final_strategy,
            "response_content": msg,
            "jorge_handoff_recommended": final_strategy == "jorge_qualification",
            "sequence_complete": True,
            "final_strategy": final_strategy
        }

    def _route_enhanced_step(self, state: LeadFollowUpState) -> Literal["generate_cma", "day_3", "day_7", "day_14", "day_30", "schedule_showing", "post_showing", "facilitate_offer", "closing_nurture", "qualified", "nurture"]:
        """Enhanced routing with predictive logic"""
        # Check for early warnings that require immediate action
        if state.get('temperature_prediction', {}).get('early_warning'):
            warning = state['temperature_prediction']['early_warning']
            if warning.get('urgency') == 'high':
                return "schedule_showing"  # Immediate escalation

        # Use parent routing logic with enhancements
        return self._route_next_step(state)

    # --- Track 3.1 Enhancement Helper Methods ---

    async def _apply_market_timing_intelligence(self, base_optimization: Optional[SequenceOptimization],
                                              journey_analysis, conversion_analysis, touchpoint_analysis) -> SequenceOptimization:
        """Apply Track 3.1 market timing intelligence to enhance sequence optimization"""
        if not base_optimization:
            base_optimization = SequenceOptimization(
                day_3=3, day_7=7, day_14=14, day_30=30,
                channel_sequence=["SMS", "Email", "Voice", "SMS"]
            )

        enhanced_optimization = SequenceOptimization(
            day_3=base_optimization.day_3,
            day_7=base_optimization.day_7,
            day_14=base_optimization.day_14,
            day_30=base_optimization.day_30,
            channel_sequence=base_optimization.channel_sequence.copy()
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
            optimal_channels = sorted(
                touchpoint_analysis.channel_preferences.items(),
                key=lambda x: x[1],
                reverse=True
            )
            enhanced_optimization.channel_sequence = [ch[0] for ch in optimal_channels[:4]]
            logger.info(f"Updated channel sequence based on ML preferences: {enhanced_optimization.channel_sequence}")

        return enhanced_optimization

    async def _detect_critical_scenarios(self, journey_analysis, conversion_analysis, state: LeadFollowUpState) -> Optional[Dict[str, Any]]:
        """Detect critical scenarios requiring immediate intervention or Jorge Bot handoff"""
        # Scenario 1: High value lead cooling down rapidly
        if (journey_analysis.conversion_probability > 0.6 and
            conversion_analysis.drop_off_risk > 0.7):
            return {
                "type": "high_value_cooling",
                "urgency": "critical",
                "recommendation": "immediate_jorge_handoff",
                "reason": f"High conversion probability ({journey_analysis.conversion_probability:.2f}) but high drop-off risk ({conversion_analysis.drop_off_risk:.2f})",
                "suggested_action": "Deploy Jorge Seller Bot for confrontational re-engagement within 2 hours"
            }

        # Scenario 2: Ready for qualification
        if (journey_analysis.conversion_probability > 0.75 and
            conversion_analysis.stage_conversion_probability > 0.8):
            return {
                "type": "qualification_ready",
                "urgency": "medium",
                "recommendation": "jorge_qualification",
                "reason": f"High conversion indicators suggest readiness for Jorge's qualification process",
                "suggested_action": "Schedule Jorge Bot consultation within 24 hours"
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
                "recommendation": "Consider Jorge Seller Bot engagement for qualification"
            }
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
                    "lead_temperature": state.get('temperature_prediction', {}).get('current_temperature', 0),
                    "sequence_completion": "day_30_reached",
                    "recommendation": "Jorge confrontational qualification recommended"
                }
            }
        )

    # --- Node Implementations ---

    async def analyze_intent(self, state: LeadFollowUpState) -> Dict:
        """Score the lead using the Phase 1 Intent Decoder."""
        logger.info(f"Analyzing intent for lead {state['lead_id']}")

        # Emit bot status update
        await self.event_publisher.publish_bot_status_update(
            bot_type="lead-bot",
            contact_id=state["lead_id"],
            status="processing",
            current_step="analyze_intent"
        )

        await sync_service.record_lead_event(state['lead_id'], "AI", "Analyzing lead intent profile.", "thought")

        profile = self.intent_decoder.analyze_lead(
            state['lead_id'], 
            state['conversation_history']
        )
        
        # Sync to Lyrio (Phase 4)
        lyrio = LyrioClient()
        
        # Run sync in background
        asyncio.create_task(lyrio.sync_lead_score(
            state['lead_id'],
            profile.frs.total_score,
            profile.pcs.total_score,
            [profile.frs.classification]
        ))
        
        await sync_service.record_lead_event(
            state['lead_id'],
            "AI",
            f"Intent Decoded: {profile.frs.classification} (Score: {profile.frs.total_score})",
            "thought"
        )

        # Initialize or restore sequence state
        sequence_state = await self.sequence_service.get_state(state['lead_id'])
        if not sequence_state:
            # Create new sequence for new lead
            logger.info(f"Creating new sequence for lead {state['lead_id']}")
            sequence_state = await self.sequence_service.create_sequence(
                state['lead_id'],
                initial_day=SequenceDay.DAY_3
            )

            # Schedule the initial sequence start (immediate or slight delay)
            await self.scheduler.schedule_sequence_start(state['lead_id'], delay_minutes=1)
        else:
            logger.info(f"Restored sequence state for lead {state['lead_id']}: {sequence_state.current_day.value}")

        # Emit intent analysis complete event
        await self.event_publisher.publish_intent_analysis_complete(
            contact_id=state["lead_id"],
            processing_time_ms=42.3,  # Placeholder - would be actual timing
            confidence_score=0.95,    # Placeholder - would be actual confidence
            intent_category=profile.frs.classification,
            frs_score=profile.frs.total_score,
            pcs_score=profile.pcs.total_score,
            recommendations=[f"Sequence day: {sequence_state.current_day.value}"]
        )

        return {
            "intent_profile": profile,
            "sequence_state": sequence_state.to_dict()
        }

    async def determine_path(self, state: LeadFollowUpState) -> Dict:
        """Decide the next step based on engagement and timeline."""

        # 1. Check for Price Objection / CMA Request (Phase 3)
        last_msg = state['conversation_history'][-1]['content'].lower() if state['conversation_history'] else ""
        price_keywords = ["price", "value", "worth", "zestimate", "comps", "market analysis"]

        is_price_aware = state['intent_profile'].frs.price.category == "Price-Aware"
        has_keyword = any(k in last_msg for k in price_keywords)
        
        logger.info(f"DEBUG: determine_path - last_msg: '{last_msg}'")
        logger.info(f"DEBUG: determine_path - is_price_aware: {is_price_aware}, has_keyword: {has_keyword}")
        logger.info(f"DEBUG: determine_path - cma_generated: {state.get('cma_generated')}")

        if (is_price_aware or has_keyword) and not state.get('cma_generated'):
            logger.info("DEBUG: determine_path - Routing to generate_cma")
            await sync_service.record_lead_event(state['lead_id'], "AI", "Price awareness detected. Routing to CMA generation.", "node")
            return {"current_step": "generate_cma", "engagement_status": "responsive"}

        # 2. Check for immediate qualification (High Intent)
        if state['intent_profile'].frs.classification == "Hot Lead":
            await sync_service.record_lead_event(state['lead_id'], "AI", "High intent lead detected. Routing to qualified state.", "thought")
            return {"current_step": "qualified", "engagement_status": "qualified"}
            
        # 3. Use sequence state to determine next step
        sequence_data = state.get('sequence_state', {})
        sequence_day_val = state.get('sequence_day')
        
        if sequence_day_val is not None:
            # Simulation/Direct mode: create temporary sequence state from sequence_day
            # Map numeric day to SequenceDay enum
            day_enum = SequenceDay.DAY_3
            if sequence_day_val == 7: day_enum = SequenceDay.DAY_7
            elif sequence_day_val == 14: day_enum = SequenceDay.DAY_14
            elif sequence_day_val == 30: day_enum = SequenceDay.DAY_30
            
            sequence_state = LeadSequenceState(
                lead_id=state['lead_id'],
                current_day=day_enum,
                sequence_status=SequenceStatus.IN_PROGRESS,
                sequence_started_at=datetime.now(timezone.utc),
                engagement_status="responsive"
            )
        elif sequence_data:
            sequence_state = LeadSequenceState.from_dict(sequence_data)
        else:
            # Fallback: get from service if not in state
            sequence_state = await self.sequence_service.get_state(state['lead_id'])
            if not sequence_state:
                # Create new sequence
                sequence_state = await self.sequence_service.create_sequence(state['lead_id'])

        logger.info(f"DEBUG: determine_path - sequence state: {sequence_state.current_day.value}, status: {sequence_state.sequence_status}")

        # Determine routing based on sequence day
        current_day = sequence_state.current_day
        if sequence_day_val is not None:
            if sequence_day_val == 3: current_day = SequenceDay.DAY_3
            elif sequence_day_val == 7: current_day = SequenceDay.DAY_7
            elif sequence_day_val == 14: current_day = SequenceDay.DAY_14
            elif sequence_day_val == 30: current_day = SequenceDay.DAY_30

        if current_day == SequenceDay.DAY_3:
            logger.info("DEBUG: determine_path - Routing to day_3")
            await sync_service.record_lead_event(state['lead_id'], "AI", "Executing Day 3 SMS sequence.", "sequence")
            return {"current_step": "day_3", "engagement_status": sequence_state.engagement_status}

        elif current_day == SequenceDay.DAY_7:
            logger.info("DEBUG: determine_path - Routing to day_7")
            await sync_service.record_lead_event(state['lead_id'], "AI", "Executing Day 7 call sequence.", "sequence")
            return {"current_step": "day_7", "engagement_status": sequence_state.engagement_status}

        elif current_day == SequenceDay.DAY_14:
            logger.info("DEBUG: determine_path - Routing to day_14")
            await sync_service.record_lead_event(state['lead_id'], "AI", "Executing Day 14 email sequence.", "sequence")
            return {"current_step": "day_14", "engagement_status": sequence_state.engagement_status}

        elif current_day == SequenceDay.DAY_30:
            logger.info("DEBUG: determine_path - Routing to day_30")
            await sync_service.record_lead_event(state['lead_id'], "AI", "Executing Day 30 final nudge.", "sequence")
            return {"current_step": "day_30", "engagement_status": sequence_state.engagement_status}

        elif current_day == SequenceDay.QUALIFIED:
            logger.info("DEBUG: determine_path - Lead is qualified")
            await sync_service.record_lead_event(state['lead_id'], "AI", "Lead qualified, exiting sequence.", "sequence")
            return {"current_step": "qualified", "engagement_status": "qualified"}

        else:  # NURTURE or other
            logger.info("DEBUG: determine_path - Moving to nurture")
            await sync_service.record_lead_event(state['lead_id'], "AI", "Lead in nurture status.", "sequence")
            return {"current_step": "nurture", "engagement_status": "nurture"}

    async def generate_cma(self, state: LeadFollowUpState) -> Dict:
        """Generate Zillow-Defense CMA and inject into conversation."""
        logger.info(f"Generating CMA for {state['lead_name']}")
        
        address = state.get('property_address', '123 Main St, Austin, TX') # Fallback if missing
        
        await sync_service.record_lead_event(state['lead_id'], "AI", f"Generating CMA for {address}", "thought")

        # Generate Report
        report = await self.cma_generator.generate_report(address)
        
        # Render PDF URL (Mock)
        pdf_url = PDFRenderer.generate_pdf_url(report)
        
        # Phase 8: Digital Twin Association
        lyrio = LyrioClient()
        # Mock URL for digital twin
        digital_twin_url = f"https://enterprise-hub.ai/visualize/{address.replace(' ', '-').lower()}"
        
        # Sync Digital Twin URL to Lyrio in background
        asyncio.create_task(lyrio.sync_digital_twin_url(
            state['lead_id'],
            address,
            digital_twin_url
        ))
        
        # Construct Response
        response_msg = (
            f"I ran the numbers for {address}. Zillow's estimate is off by ${report.zillow_variance_abs:,.0f}. "
            f"Here is the real market analysis based on actual comps from the last 45 days: \n\n"
            f"[View CMA Report]({pdf_url})\n\n"
            f"I've also prepared a 3D Digital Twin of your property: {digital_twin_url}"
        )
        
        # In a real system, we'd send this via GHL API here
        logger.info(f"CMA Injection: {response_msg}")
        
        await sync_service.record_lead_event(state['lead_id'], "AI", f"CMA Generated with ${report.zillow_variance_abs:,.0f} variance.", "thought")

        # Mark CMA as generated in sequence state
        await self.sequence_service.set_cma_generated(state['lead_id'])

        # Emit lead bot sequence update for CMA generation
        await self.event_publisher.publish_lead_bot_sequence_update(
            contact_id=state["lead_id"],
            sequence_day=0,  # CMA can be generated at any time
            action_type="cma_generated",
            success=True,
            message_sent=response_msg
        )

        return {
            "cma_generated": True,
            "current_step": "nurture", # Return to nurture or wait for reply
            "last_interaction_time": datetime.now(timezone.utc)
        }

    async def send_day_3_sms(self, state: LeadFollowUpState) -> Dict:
        """Day 3: Soft Check-in with FRS-aware logic via GhostEngine."""
        # Emit lead bot sequence update - starting Day 3
        await self.event_publisher.publish_lead_bot_sequence_update(
            contact_id=state["lead_id"],
            sequence_day=3,
            action_type="analysis_started",
            success=True
        )

        ghost_state = GhostState(
            contact_id=state['lead_id'],
            current_day=3,
            frs_score=state['intent_profile'].frs.total_score
        )

        action = await self.ghost_engine.process_lead_step(ghost_state, state['conversation_history'])
        msg = action['content']

        logger.info(f"Day 3 SMS to {state['contact_phone']}: {msg} (Logic: {action.get('logic')})")
        await sync_service.record_lead_event(state['lead_id'], "AI", f"Sent Day 3 SMS: {msg[:50]}...", "sms")

        # Emit lead bot sequence update - message sent
        await self.event_publisher.publish_lead_bot_sequence_update(
            contact_id=state["lead_id"],
            sequence_day=3,
            action_type="message_sent",
            success=True,
            next_action_date=(datetime.now(timezone.utc) + timedelta(days=4)).isoformat(),  # Day 7
            message_sent=msg
        )

        # Mark Day 3 as completed in sequence state
        await self.sequence_service.mark_action_completed(state['lead_id'], SequenceDay.DAY_3, "sms_sent")

        # Schedule next sequence action (Day 7 call)
        await self.scheduler.schedule_next_action(state['lead_id'], SequenceDay.DAY_3)

        # Advance sequence to next day
        await self.sequence_service.advance_to_next_day(state['lead_id'])

        # Send SMS via GHL API
        if self.ghl_client:
            try:
                await self.ghl_client.send_message(
                    contact_id=state['lead_id'],
                    message=msg,
                    channel=MessageType.SMS
                )
                logger.info(f"SMS sent successfully to contact {state['lead_id']}")
            except Exception as e:
                logger.error(f"Failed to send SMS via GHL: {e}")

        return {
            "engagement_status": "ghosted", 
            "current_step": "day_7_call",
            "response_content": msg
        }

    async def initiate_day_7_call(self, state: LeadFollowUpState) -> Dict:
        """Day 7: Initiate Retell AI Call with Stall-Breaker logic."""
        logger.info(f"Initiating Day 7 Call for {state['lead_name']}")
        
        # Prepare context for the AI agent
        stall_breaker = self._select_stall_breaker(state)
        context = {
            "lead_name": state['lead_name'],
            "property": state.get('property_address'),
            "stall_breaker_script": stall_breaker,
            "frs_score": state['intent_profile'].frs.total_score
        }
        
        await sync_service.record_lead_event(state['lead_id'], "AI", "Initiating Day 7 Retell AI Call.", "action")

        # Trigger Retell Call (Fire-and-forget for Dashboard UI performance)
        def _call_finished(fut):
            try:
                fut.result()
                logger.info(f"Background Retell call initiated successfully for {state['lead_name']}")
            except Exception as e:
                logger.error(f"Background Retell call failed for {state['lead_name']}: {e}")

        task = asyncio.create_task(self.retell_client.create_call(
            to_number=state['contact_phone'],
            lead_name=state['lead_name'],
            lead_context=context,
            metadata={"contact_id": state['lead_id']}
        ))
        task.add_done_callback(_call_finished)

        # Mark Day 7 as completed in sequence state
        await self.sequence_service.mark_action_completed(state['lead_id'], SequenceDay.DAY_7, "call_initiated")

        # Schedule next sequence action (Day 14 email)
        await self.scheduler.schedule_next_action(state['lead_id'], SequenceDay.DAY_7)

        # Advance sequence to next day
        await self.sequence_service.advance_to_next_day(state['lead_id'])

        return {
            "engagement_status": "ghosted", 
            "current_step": "day_14_email",
            "response_content": f"Initiating Day 7 Call with stall breaker: {stall_breaker}"
        }

    async def send_day_14_email(self, state: LeadFollowUpState) -> Dict:
        """Day 14: Value Injection (CMA) via GhostEngine."""
        ghost_state = GhostState(
            contact_id=state['lead_id'],
            current_day=14,
            frs_score=state['intent_profile'].frs.total_score
        )
        action = await self.ghost_engine.process_lead_step(ghost_state, state['conversation_history'])
        
        logger.info(f"Sending Day 14 Email to {state['contact_email']}: {action['content']}")
        await sync_service.record_lead_event(state['lead_id'], "AI", "Sent Day 14 Email with value injection.", "email")

        # Mark Day 14 as completed in sequence state
        await self.sequence_service.mark_action_completed(state['lead_id'], SequenceDay.DAY_14, "email_sent")

        # Schedule next sequence action (Day 30 SMS)
        await self.scheduler.schedule_next_action(state['lead_id'], SequenceDay.DAY_14)

        # Advance sequence to next day
        await self.sequence_service.advance_to_next_day(state['lead_id'])

        # Send email via GHL API
        if self.ghl_client:
            try:
                await self.ghl_client.send_message(
                    contact_id=state['lead_id'],
                    message=action['content'],
                    channel=MessageType.EMAIL
                )
                logger.info(f"Email sent successfully to contact {state['lead_id']}")
            except Exception as e:
                logger.error(f"Failed to send email via GHL: {e}")

        # TODO: Generate and attach CMA PDF

        return {
            "engagement_status": "ghosted", 
            "current_step": "day_30_nudge",
            "response_content": action['content']
        }

    async def send_day_30_nudge(self, state: LeadFollowUpState) -> Dict:
        """Day 30: Final qualification attempt via GhostEngine."""
        ghost_state = GhostState(
            contact_id=state['lead_id'],
            current_day=30,
            frs_score=state['intent_profile'].frs.total_score
        )
        action = await self.ghost_engine.process_lead_step(ghost_state, state['conversation_history'])
        
        logger.info(f"Sending Day 30 SMS to {state['contact_phone']}: {action['content']}")
        await sync_service.record_lead_event(state['lead_id'], "AI", "Sent Day 30 final nudge SMS.", "sms")

        # Mark Day 30 as completed in sequence state
        await self.sequence_service.mark_action_completed(state['lead_id'], SequenceDay.DAY_30, "sms_sent")

        # Complete the sequence - move to nurture
        await self.sequence_service.complete_sequence(state['lead_id'], "nurture")

        # Send SMS via GHL API
        if self.ghl_client:
            try:
                await self.ghl_client.send_message(
                    contact_id=state['lead_id'],
                    message=action['content'],
                    channel=MessageType.SMS
                )
                logger.info(f"Day 30 SMS sent successfully to contact {state['lead_id']}")
            except Exception as e:
                logger.error(f"Failed to send Day 30 SMS via GHL: {e}")

        return {
            "engagement_status": "nurture", 
            "current_step": "nurture",
            "response_content": action['content']
        }

    async def schedule_showing(self, state: LeadFollowUpState) -> Dict:
        """Handle showing coordination with market-aware scheduling."""
        logger.info(f"Scheduling showing for {state['lead_name']} at {state['property_address']}")
        
        await sync_service.record_lead_event(state['lead_id'], "AI", "Coordinating showing with market-aware scheduling.", "thought")

        # Phase 7: Use Smart Scheduler
        from ghl_real_estate_ai.services.calendar_scheduler import get_smart_scheduler
        scheduler = get_smart_scheduler(self.ghl_client)
        
        address = state.get('property_address', 'the property')
        market_metrics = await self.market_intel.get_market_metrics(address)
        
        # Inject urgency if market is hot
        urgency_msg = ""
        if market_metrics and market_metrics.inventory_days < 15:
            urgency_msg = f" This market is moving fast ({market_metrics.inventory_days} days avg), so we should see it soon."
            
        msg = f"Great choice! I'm coordinating with the listing agent for {address}.{urgency_msg} Does tomorrow afternoon work for a tour?"
        
        await sync_service.record_lead_event(state['lead_id'], "AI", f"Showing inquiry sent for {address}.", "sms")

        # In a real system, trigger GHL SMS here
        return {"engagement_status": "showing_booked", "current_step": "post_showing"}

    async def post_showing_survey(self, state: LeadFollowUpState) -> Dict:
        """Collect feedback after a showing with behavioral intent capture."""
        logger.info(f"Collecting post-showing feedback from {state['lead_name']}")
        
        await sync_service.record_lead_event(state['lead_id'], "AI", "Collecting post-showing behavioral feedback.", "thought")

        # Use Tone Engine (Jorge style if applicable, or standard)
        msg = "How was the tour? On a scale of 1-10, how well does this home fit what you're looking for?"
        
        await sync_service.record_lead_event(state['lead_id'], "AI", "Post-showing survey sent.", "sms")

        return {"current_step": "facilitate_offer", "engagement_status": "qualified"}

    async def facilitate_offer(self, state: LeadFollowUpState) -> Dict:
        """Guide the lead through the offer submission process using NationalMarketIntelligence."""
        logger.info(f"Facilitating offer for {state['lead_name']}")
        
        address = state.get('property_address', 'the property')
        await sync_service.record_lead_event(state['lead_id'], "AI", f"Facilitating offer strategy for {address}", "thought")

        metrics = await self.market_intel.get_market_metrics(address)
        
        # Generate offer strategy advice
        strategy = "We should look at recent comps to find the right number."
        if metrics:
            if metrics.price_appreciation_1y > 10:
                strategy = "Given the 10%+ appreciation in this area, we might need to be aggressive with the terms."
            else:
                strategy = "Market is stable here, so we have some room to negotiate on repairs."
                
        msg = f"I've prepared an offer strategy for {address}. {strategy} Ready to review the numbers?"
        
        await sync_service.record_lead_event(state['lead_id'], "AI", "Offer strategy sent to lead.", "sms")

        return {"engagement_status": "offer_sent", "current_step": "closing_nurture"}

    async def contract_to_close_nurture(self, state: LeadFollowUpState) -> Dict:
        """Automated touchpoints during the escrow period with milestone tracking."""
        logger.info(f"Escrow nurture for {state['lead_name']}")
        
        await sync_service.record_lead_event(state['lead_id'], "AI", "Starting escrow nurture and milestone tracking.", "node")

        # Milestone logic (mocked for now, but structure is there)
        msg = "Congrats again on being under contract! The next major milestone is the inspection. I'll be there to make sure everything is handled."
        
        await sync_service.record_lead_event(state['lead_id'], "AI", "Escrow update: Inspection milestone tracked.", "thought")

        return {"engagement_status": "under_contract", "current_step": "closed"}

    # --- Helper Logic ---

    def _route_next_step(self, state: LeadFollowUpState) -> Literal["generate_cma", "day_3", "day_7", "day_14", "day_30", "schedule_showing", "post_showing", "facilitate_offer", "closing_nurture", "qualified", "nurture"]:
        """Conditional routing logic."""
        # Fix for phase 3: check for generate_cma first
        if state.get('current_step') == 'generate_cma':
            return "generate_cma"

        # Check for lifecycle transitions
        engagement = state['engagement_status']
        if engagement == "showing_booked":
            return "post_showing"
        if engagement == "offer_sent":
            return "closing_nurture"
        if engagement == "under_contract":
            return "qualified" # Or specific closing node
            
        # Logic for booking showings if score is high
        if state['intent_profile'] and state['intent_profile'].frs.classification == "Hot Lead":
            if engagement != "showing_booked":
                return "schedule_showing"

        if state['engagement_status'] == "qualified":
            return "qualified"
        if state['engagement_status'] == "nurture":
            return "nurture"
            
        # Valid steps mapping
        step = state.get('current_step', 'initial')
        if step in ["day_3", "day_7", "day_14", "day_30"]:
            return step
        
        # Default fallback
        return "nurture"

    def _select_stall_breaker(self, state: LeadFollowUpState) -> str:
        """Select the appropriate stall-breaking script based on intent profile via GhostEngine."""
        last_msg = state['conversation_history'][-1]['content'].lower() if state['conversation_history'] else ""

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

    # ================================
    # UNIFIED PROCESSING METHODS
    # ================================

    async def process_enhanced_lead_sequence(self, lead_id: str, sequence_day: int,
                                           conversation_history: List[Dict]) -> Dict[str, Any]:
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
            "track3_applied": False
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
                "jorge_handoff": self.config.jorge_handoff_enabled
            }
        }

        # Behavioral optimization metrics
        if self.config.enable_behavioral_optimization and self.workflow_stats["total_sequences"] > 0:
            metrics["behavioral_optimization"] = {
                "optimizations_applied": self.workflow_stats["behavioral_optimizations"],
                "optimization_rate": self.workflow_stats["behavioral_optimizations"] / self.workflow_stats["total_sequences"]
            }

        # Personality adaptation metrics
        if self.config.enable_personality_adaptation:
            metrics["personality_adaptation"] = {
                "adaptations_applied": self.workflow_stats["personality_adaptations"],
                "adaptation_rate": self.workflow_stats["personality_adaptations"] / max(self.workflow_stats["total_sequences"], 1)
            }

        # Track 3.1 metrics
        if self.config.enable_track3_intelligence:
            metrics["track3_intelligence"] = {
                "enhancements_applied": self.workflow_stats["track3_enhancements"],
                "enhancement_rate": self.workflow_stats["track3_enhancements"] / max(self.workflow_stats["total_sequences"], 1)
            }

        # Jorge handoff metrics
        if self.config.jorge_handoff_enabled:
            metrics["jorge_handoffs"] = {
                "total_handoffs": self.workflow_stats["jorge_handoffs"],
                "handoff_rate": self.workflow_stats["jorge_handoffs"] / max(self.workflow_stats["total_sequences"], 1)
            }

        return metrics

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check of all enabled systems"""
        health_status = {
            "lead_bot": "healthy",
            "predictive_analytics": "disabled",
            "behavioral_optimization": "disabled",
            "personality_adaptation": "disabled",
            "track3_intelligence": "disabled",
            "overall_status": "healthy"
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

        return health_status

    # ================================
    # FACTORY METHODS
    # ================================

    @classmethod
    def create_standard_lead_bot(cls, ghl_client=None) -> 'LeadBotWorkflow':
        """Factory method: Create standard lead bot (3-7-30 sequence only)"""
        config = LeadBotConfig()
        return cls(ghl_client=ghl_client, config=config)

    @classmethod
    def create_enhanced_lead_bot(cls, ghl_client=None) -> 'LeadBotWorkflow':
        """Factory method: Create lead bot with behavioral optimization"""
        config = LeadBotConfig(
            enable_behavioral_optimization=True,
            enable_personality_adaptation=True,
            enable_predictive_analytics=True
        )
        return cls(ghl_client=ghl_client, config=config)

    @classmethod
    def create_enterprise_lead_bot(cls, ghl_client=None) -> 'LeadBotWorkflow':
        """Factory method: Create fully-enhanced enterprise lead bot"""
        config = LeadBotConfig(
            enable_predictive_analytics=True,
            enable_behavioral_optimization=True,
            enable_personality_adaptation=True,
            enable_track3_intelligence=True,
            jorge_handoff_enabled=True
        )
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

    