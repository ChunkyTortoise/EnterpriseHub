"""
Real-time Intent Decoder - Streaming Analysis Engine
Streaming intent analysis with contextual awareness and incremental updates.
Extends the base LeadIntentDecoder with Track 1 enhancements.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import re

from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder
from ghl_real_estate_ai.models.lead_scoring import (
    LeadIntentProfile,
    FinancialReadinessScore,
    PsychologicalCommitmentScore,
    MotivationSignals,
    TimelineCommitment,
    ConditionRealism,
    PriceResponsiveness
)
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

class IntentSignal(Enum):
    """Types of intent signals detected in real-time."""
    MOTIVATION_INCREASE = "motivation_increase"
    MOTIVATION_DECREASE = "motivation_decrease"
    TIMELINE_URGENCY = "timeline_urgency"
    PRICE_SENSITIVITY = "price_sensitivity"
    CONDITION_FLEXIBILITY = "condition_flexibility"
    ENGAGEMENT_SPIKE = "engagement_spike"
    DISENGAGEMENT_WARNING = "disengagement_warning"

@dataclass
class IntentUpdate:
    """Real-time intent score update."""
    frs_delta: float
    pcs_delta: float
    confidence: float
    recommended_action: str
    signals_detected: List[IntentSignal]
    timestamp: datetime
    message_trigger: str

@dataclass
class ConversationContext:
    """Maintains conversation state across interactions."""
    conversation_id: str
    last_scores: Optional[LeadIntentProfile]
    message_count: int
    session_start: datetime
    last_interaction: datetime
    score_history: List[Dict]
    detected_patterns: Dict[str, Any]
    semantic_markers: List[str]

class SemanticIntentEngine:
    """Advanced semantic analysis for deeper intent understanding."""

    def __init__(self):
        # Enhanced semantic patterns
        self.semantic_patterns = {
            "urgency_markers": {
                "immediate": ["asap", "immediately", "urgent", "right away", "today"],
                "forced_timeline": ["have to", "need to", "must", "deadline", "by [date]"],
                "life_events": ["divorce", "death", "job loss", "moving", "relocation", "baby"]
            },
            "commitment_signals": {
                "strong": ["definitely", "absolutely", "committed", "ready", "let's do it"],
                "medium": ["probably", "likely", "thinking about", "considering"],
                "weak": ["maybe", "possibly", "not sure", "if", "depends"]
            },
            "financial_indicators": {
                "cash_ready": ["cash", "liquid", "available funds", "ready to buy"],
                "financing_dependent": ["loan", "mortgage", "financing", "bank approval"],
                "budget_conscious": ["budget", "afford", "payment", "monthly", "price range"]
            },
            "emotional_states": {
                "excited": ["excited", "love", "perfect", "dream home", "amazing"],
                "frustrated": ["frustrated", "tired", "difficult", "problem", "stressed"],
                "skeptical": ["not sure", "doubt", "concerned", "worried", "hesitant"]
            }
        }

        # Contextual relationship patterns
        self.context_patterns = {
            "price_negotiation": ["negotiate", "lower", "reduce", "best price", "deal"],
            "comparison_shopping": ["compare", "other options", "looking at", "versus"],
            "decision_factors": ["important", "priority", "must have", "deal breaker"]
        }

    async def analyze(self, message: str, context: ConversationContext) -> Dict[str, Any]:
        """Perform semantic analysis on message with contextual awareness."""
        message_lower = message.lower()

        # Detect semantic signals
        detected_signals = []
        confidence_factors = []

        # Analyze urgency patterns
        for urgency_type, patterns in self.semantic_patterns["urgency_markers"].items():
            if any(pattern in message_lower for pattern in patterns):
                detected_signals.append(f"urgency_{urgency_type}")
                confidence_factors.append(0.8)

        # Analyze commitment patterns
        for commitment_level, patterns in self.semantic_patterns["commitment_signals"].items():
            if any(pattern in message_lower for pattern in patterns):
                detected_signals.append(f"commitment_{commitment_level}")
                confidence_factors.append(0.7)

        # Analyze financial indicators
        for financial_type, patterns in self.semantic_patterns["financial_indicators"].items():
            if any(pattern in message_lower for pattern in patterns):
                detected_signals.append(f"financial_{financial_type}")
                confidence_factors.append(0.75)

        # Analyze emotional state
        for emotion, patterns in self.semantic_patterns["emotional_states"].items():
            if any(pattern in message_lower for pattern in patterns):
                detected_signals.append(f"emotion_{emotion}")
                confidence_factors.append(0.6)

        # Calculate overall confidence
        overall_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5

        # Contextual analysis - compare with conversation history
        context_insights = self._analyze_context_shifts(message_lower, context)

        return {
            "semantic_signals": detected_signals,
            "confidence": overall_confidence,
            "context_insights": context_insights,
            "raw_patterns": {
                "urgency_detected": any("urgency" in signal for signal in detected_signals),
                "commitment_shift": any("commitment" in signal for signal in detected_signals),
                "financial_readiness": any("financial" in signal for signal in detected_signals),
                "emotional_state": [s for s in detected_signals if "emotion" in s]
            }
        }

    def _analyze_context_shifts(self, message: str, context: ConversationContext) -> Dict[str, Any]:
        """Analyze how current message shifts from previous context."""
        if not context.detected_patterns or not isinstance(context.detected_patterns, dict):
            return {"shift_type": "initial", "magnitude": 0.0}

        # Compare current message patterns with historical patterns
        previous_urgency = context.detected_patterns.get("urgency_level", 0)
        if not isinstance(previous_urgency, (int, float)):
            previous_urgency = 0
        current_urgency = self._calculate_urgency_level(message)

        urgency_shift = current_urgency - previous_urgency

        return {
            "shift_type": "urgency_increase" if urgency_shift > 0.2 else "urgency_decrease" if urgency_shift < -0.2 else "stable",
            "magnitude": abs(urgency_shift),
            "urgency_delta": urgency_shift
        }

    def _calculate_urgency_level(self, message: str) -> float:
        """Calculate urgency level from 0-1."""
        urgency_keywords = ["urgent", "asap", "immediately", "quickly", "soon"]
        urgency_score = sum(1 for keyword in urgency_keywords if keyword in message)
        return min(1.0, urgency_score * 0.25)

class ConversationMemory:
    """Advanced conversation memory with pattern recognition."""

    def __init__(self):
        self._memory: Dict[str, ConversationContext] = {}

    async def get_context(self, conversation_id: str) -> ConversationContext:
        """Get or create conversation context."""
        if conversation_id not in self._memory:
            self._memory[conversation_id] = ConversationContext(
                conversation_id=conversation_id,
                last_scores=None,
                message_count=0,
                session_start=datetime.now(),
                last_interaction=datetime.now(),
                score_history=[],
                detected_patterns={},
                semantic_markers=[]
            )
        return self._memory[conversation_id]

    async def update_context(self, conversation_id: str, update_data: Dict):
        """Update conversation context with new data."""
        context = await self.get_context(conversation_id)

        # Update fields
        for key, value in update_data.items():
            if hasattr(context, key):
                setattr(context, key, value)

        # Update interaction timestamp
        context.last_interaction = datetime.now()
        context.message_count += 1

        # Maintain score history (keep last 20 interactions)
        if 'score_snapshot' in update_data:
            context.score_history.append({
                'timestamp': datetime.now().isoformat(),
                'scores': update_data['score_snapshot']
            })
            if len(context.score_history) > 20:
                context.score_history = context.score_history[-20:]

class RealTimeIntentDecoder(LeadIntentDecoder):
    """
    Enhanced Intent Decoder with real-time streaming analysis.
    Provides incremental updates and contextual awareness.
    """

    def __init__(self):
        super().__init__()
        self.context_memory = ConversationMemory()
        self.semantic_analyzer = SemanticIntentEngine()
        self.event_publisher = get_event_publisher()

    async def stream_intent_analysis(self, message: str, conversation_id: str, lead_id: str) -> IntentUpdate:
        """Process single message for real-time intent updates."""
        logger.info(f"Streaming intent analysis for lead {lead_id}, conversation {conversation_id}")

        # Get conversation context
        context = await self.context_memory.get_context(conversation_id)

        # Semantic analysis for deeper understanding
        semantic_signals = await self.semantic_analyzer.analyze(message, context)

        # Calculate incremental score updates
        updated_scores = await self._update_incremental_scores(
            current_scores=context.last_scores,
            new_message=message,
            semantic_signals=semantic_signals,
            context=context
        )

        # Determine recommended action
        recommended_action = self._determine_streaming_action(updated_scores, semantic_signals)

        # Detect intent signals
        detected_signals = self._detect_intent_signals(updated_scores, semantic_signals, context)

        # Create intent update
        intent_update = IntentUpdate(
            frs_delta=updated_scores.get('frs_delta', 0.0),
            pcs_delta=updated_scores.get('pcs_delta', 0.0),
            confidence=semantic_signals.get('confidence', 0.5),
            recommended_action=recommended_action,
            signals_detected=detected_signals,
            timestamp=datetime.now(),
            message_trigger=message[:100]  # Truncate for storage
        )

        # Update context memory
        await self._update_memory_with_analysis(conversation_id, updated_scores, semantic_signals)

        # Emit real-time event
        await self.event_publisher.publish_realtime_intent_update(
            contact_id=lead_id,
            conversation_id=conversation_id,
            intent_update=asdict(intent_update),
            semantic_analysis=semantic_signals
        )

        return intent_update

    async def _update_incremental_scores(self,
                                       current_scores: Optional[LeadIntentProfile],
                                       new_message: str,
                                       semantic_signals: Dict[str, Any],
                                       context: ConversationContext) -> Dict[str, Any]:
        """Update scores incrementally based on new message."""

        # Initialize baseline scores
        if current_scores is None:
            # First message - use full analysis
            conversation_history = [{"role": "user", "content": new_message}]
            full_analysis = self.analyze_lead("temp", conversation_history)

            return {
                "frs_total": full_analysis.frs.total_score,
                "pcs_total": full_analysis.pcs.total_score,
                "frs_delta": 0.0,  # No delta for first message
                "pcs_delta": 0.0,
                "full_profile": full_analysis
            }

        # Calculate incremental changes
        frs_delta = 0.0
        pcs_delta = 0.0

        # FRS adjustments based on semantic signals
        for signal in semantic_signals.get('semantic_signals', []):
            if signal.startswith('urgency_'):
                frs_delta += 5.0  # Boost timeline score
            elif signal.startswith('financial_cash'):
                frs_delta += 8.0  # Strong financial readiness
            elif signal.startswith('commitment_strong'):
                pcs_delta += 10.0
                frs_delta += 3.0
            elif signal.startswith('commitment_weak'):
                pcs_delta -= 5.0
                frs_delta -= 2.0

        # Context-based adjustments
        context_insights = semantic_signals.get('context_insights', {})
        if context_insights.get('shift_type') == 'urgency_increase':
            frs_delta += context_insights.get('magnitude', 0) * 10
            pcs_delta += context_insights.get('magnitude', 0) * 8

        # Message length and engagement signals for PCS
        message_length = len(new_message.split())
        if message_length > 20:  # Detailed response indicates engagement
            pcs_delta += 3.0
        elif message_length < 5:  # Very short might indicate disengagement
            pcs_delta -= 2.0

        # Calculate new totals (with bounds checking)
        new_frs = max(0, min(100, current_scores.frs.total_score + frs_delta))
        new_pcs = max(0, min(100, current_scores.pcs.total_score + pcs_delta))

        return {
            "frs_total": new_frs,
            "pcs_total": new_pcs,
            "frs_delta": frs_delta,
            "pcs_delta": pcs_delta,
            "confidence": semantic_signals.get('confidence', 0.5)
        }

    def _determine_streaming_action(self, scores: Dict[str, Any], semantic_signals: Dict[str, Any]) -> str:
        """Determine recommended action based on streaming analysis."""
        frs = scores.get('frs_total', 0)
        pcs = scores.get('pcs_total', 0)

        # High urgency signals - immediate action
        if any('urgency_immediate' in signal for signal in semantic_signals.get('semantic_signals', [])):
            return "IMMEDIATE_CALL"

        # Strong positive momentum
        if scores.get('frs_delta', 0) > 10 and scores.get('pcs_delta', 0) > 10:
            return "ACCELERATE_SEQUENCE"

        # Declining engagement
        if scores.get('frs_delta', 0) < -5 and scores.get('pcs_delta', 0) < -5:
            return "RE_ENGAGEMENT_REQUIRED"

        # Standard qualification thresholds
        if frs >= 75 and pcs >= 70:
            return "SCHEDULE_SHOWING"
        elif frs >= 50 or pcs >= 60:
            return "SOFT_FOLLOWUP"
        else:
            return "CONTINUE_NURTURE"

    def _detect_intent_signals(self, scores: Dict[str, Any], semantic_signals: Dict[str, Any], context: ConversationContext) -> List[IntentSignal]:
        """Detect specific intent signals from analysis."""
        signals = []

        # Motivation changes
        if scores.get('frs_delta', 0) > 8:
            signals.append(IntentSignal.MOTIVATION_INCREASE)
        elif scores.get('frs_delta', 0) < -5:
            signals.append(IntentSignal.MOTIVATION_DECREASE)

        # Timeline urgency
        if any('urgency_' in signal for signal in semantic_signals.get('semantic_signals', [])):
            signals.append(IntentSignal.TIMELINE_URGENCY)

        # Price sensitivity
        if any('financial_' in signal for signal in semantic_signals.get('semantic_signals', [])):
            signals.append(IntentSignal.PRICE_SENSITIVITY)

        # Engagement patterns
        if scores.get('pcs_delta', 0) > 15:
            signals.append(IntentSignal.ENGAGEMENT_SPIKE)
        elif scores.get('pcs_delta', 0) < -10:
            signals.append(IntentSignal.DISENGAGEMENT_WARNING)

        return signals

    async def _update_memory_with_analysis(self, conversation_id: str, scores: Dict[str, Any], semantic_signals: Dict[str, Any]):
        """Update conversation memory with latest analysis."""
        await self.context_memory.update_context(conversation_id, {
            'score_snapshot': {
                'frs_total': scores.get('frs_total'),
                'pcs_total': scores.get('pcs_total'),
                'frs_delta': scores.get('frs_delta'),
                'pcs_delta': scores.get('pcs_delta')
            },
            'detected_patterns': {
                'semantic_signals': semantic_signals.get('semantic_signals', []),
                'confidence': semantic_signals.get('confidence', 0.5),
                'urgency_level': semantic_signals.get('context_insights', {}).get('urgency_delta', 0)
            },
            'semantic_markers': semantic_signals.get('semantic_signals', [])
        })

    async def forecast_intent_trajectory(self, conversation_id: str, lead_id: str) -> Dict[str, Any]:
        """Forecast likely intent trajectory based on conversation patterns."""
        context = await self.context_memory.get_context(conversation_id)

        if len(context.score_history) < 3:
            return {"forecast": "insufficient_data", "confidence": 0.0}

        # Analyze score trends
        recent_scores = context.score_history[-3:]
        frs_trend = [score['scores']['frs_total'] for score in recent_scores]
        pcs_trend = [score['scores']['pcs_total'] for score in recent_scores]

        # Simple linear extrapolation
        frs_change_rate = (frs_trend[-1] - frs_trend[0]) / len(frs_trend)
        pcs_change_rate = (pcs_trend[-1] - pcs_trend[0]) / len(pcs_trend)

        # Predict next interaction scores
        predicted_frs = max(0, min(100, frs_trend[-1] + frs_change_rate))
        predicted_pcs = max(0, min(100, pcs_trend[-1] + pcs_change_rate))

        # Determine trajectory
        if frs_change_rate > 5 and pcs_change_rate > 5:
            trajectory = "accelerating"
        elif frs_change_rate < -3 or pcs_change_rate < -3:
            trajectory = "declining"
        else:
            trajectory = "stable"

        confidence = min(0.9, len(context.score_history) * 0.1)  # Higher confidence with more data

        return {
            "forecast": trajectory,
            "confidence": confidence,
            "predicted_scores": {
                "frs": predicted_frs,
                "pcs": predicted_pcs
            },
            "change_rates": {
                "frs_rate": frs_change_rate,
                "pcs_rate": pcs_change_rate
            },
            "recommendation": self._trajectory_recommendation(trajectory, predicted_frs, predicted_pcs)
        }

    def _trajectory_recommendation(self, trajectory: str, frs: float, pcs: float) -> str:
        """Generate recommendation based on trajectory forecast."""
        if trajectory == "accelerating" and frs > 60:
            return "Capitalize on momentum - schedule immediate follow-up"
        elif trajectory == "declining" and frs > 40:
            return "Intervention needed - risk of losing qualified lead"
        elif trajectory == "stable" and frs > 70:
            return "Maintain current engagement strategy"
        else:
            return "Continue nurture sequence - monitor for changes"

# --- Utility Functions ---

def get_realtime_intent_decoder() -> RealTimeIntentDecoder:
    """Factory function to get singleton real-time intent decoder."""
    if not hasattr(get_realtime_intent_decoder, '_instance'):
        get_realtime_intent_decoder._instance = RealTimeIntentDecoder()
    return get_realtime_intent_decoder._instance

# --- Event Publisher Extensions ---

async def publish_realtime_intent_update(event_publisher, contact_id: str, conversation_id: str, **kwargs):
    """Publish real-time intent update event."""
    await event_publisher.publish_event(
        event_type="realtime_intent_update",
        contact_id=contact_id,
        data={
            "conversation_id": conversation_id,
            **kwargs
        }
    )