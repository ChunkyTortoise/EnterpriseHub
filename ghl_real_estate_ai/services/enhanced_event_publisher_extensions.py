"""
Enhanced Event Publisher Extensions - Track 1 Bot Intelligence
Additional event types for AdaptiveJorgeBot, PredictiveLeadBot, and RealTimeIntentDecoder.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.services.event_publisher import get_event_publisher


class EnhancedEventTypes:
    """Event types for enhanced bot intelligence features."""

    # Adaptive Jorge Bot Events
    JORGE_QUALIFICATION_PROGRESS = "jorge_qualification_progress"
    ADAPTIVE_STRATEGY_SELECTED = "adaptive_strategy_selected"
    ADAPTIVE_RESPONSE_GENERATED = "adaptive_response_generated"
    CONVERSATION_MEMORY_UPDATED = "conversation_memory_updated"

    # Predictive Lead Bot Events
    BEHAVIORAL_ANALYSIS_COMPLETE = "behavioral_analysis_complete"
    SEQUENCE_OPTIMIZATION_APPLIED = "sequence_optimization_applied"
    PERSONALITY_ADAPTATION = "personality_adaptation"
    TEMPERATURE_PREDICTION_UPDATE = "temperature_prediction_update"
    LEAD_BOT_SEQUENCE_UPDATE = "lead_bot_sequence_update"

    # Real-time Intent Decoder Events
    REALTIME_INTENT_UPDATE = "realtime_intent_update"
    SEMANTIC_ANALYSIS_COMPLETE = "semantic_analysis_complete"
    INTENT_TRAJECTORY_FORECAST = "intent_trajectory_forecast"
    EARLY_WARNING_TRIGGERED = "early_warning_triggered"

    # Bot Orchestration Events
    BOT_ORCHESTRATION_EVENT = "bot_orchestration_event"
    ENHANCEMENT_PERFORMANCE_METRICS = "enhancement_performance_metrics"
    FALLBACK_TRIGGERED = "fallback_triggered"


class EnhancedEventPublisher:
    """Enhanced event publisher with Track 1 intelligence capabilities."""

    def __init__(self):
        self.base_publisher = get_event_publisher()

    # --- Adaptive Jorge Bot Events ---

    async def publish_jorge_qualification_progress(
        self,
        contact_id: str,
        current_question: int,
        questions_answered: int,
        seller_temperature: str,
        qualification_scores: Dict[str, float],
        next_action: str,
        adaptive_mode: Optional[str] = None,
        adaptation_count: Optional[int] = None,
    ) -> None:
        """Publish Jorge qualification progress with adaptive enhancements."""
        await self.base_publisher.publish_event(
            event_type=EnhancedEventTypes.JORGE_QUALIFICATION_PROGRESS,
            contact_id=contact_id,
            data={
                "current_question": current_question,
                "questions_answered": questions_answered,
                "seller_temperature": seller_temperature,
                "qualification_scores": qualification_scores,
                "next_action": next_action,
                "adaptive_mode": adaptive_mode,
                "adaptation_count": adaptation_count,
                "timestamp": datetime.now().isoformat(),
                "enhancement_level": "adaptive" if adaptive_mode else "standard",
            },
        )

    async def publish_adaptive_strategy_selected(
        self,
        contact_id: str,
        conversation_id: str,
        strategy_type: str,
        tone: str,
        pcs_score: float,
        adaptation_count: int,
        reasoning: str,
    ) -> None:
        """Publish adaptive strategy selection."""
        await self.base_publisher.publish_event(
            event_type=EnhancedEventTypes.ADAPTIVE_STRATEGY_SELECTED,
            contact_id=contact_id,
            data={
                "conversation_id": conversation_id,
                "strategy_type": strategy_type,
                "tone": tone,
                "pcs_score": pcs_score,
                "adaptation_count": adaptation_count,
                "reasoning": reasoning,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def publish_adaptive_response_generated(
        self,
        contact_id: str,
        question_used: str,
        adaptive_mode: str,
        personalization_applied: bool,
        confidence_score: float,
    ) -> None:
        """Publish adaptive response generation."""
        await self.base_publisher.publish_event(
            event_type=EnhancedEventTypes.ADAPTIVE_RESPONSE_GENERATED,
            contact_id=contact_id,
            data={
                "question_used": question_used,
                "adaptive_mode": adaptive_mode,
                "personalization_applied": personalization_applied,
                "confidence_score": confidence_score,
                "timestamp": datetime.now().isoformat(),
            },
        )

    # --- Predictive Lead Bot Events ---

    async def publish_behavioral_analysis_complete(
        self,
        contact_id: str,
        response_velocity: str,
        personality_type: str,
        temperature_trend: str,
        early_warning: Optional[Dict],
        channel_preferences: Dict[str, float],
        processing_time_ms: Optional[float] = None,
    ) -> None:
        """Publish behavioral analysis completion."""
        await self.base_publisher.publish_event(
            event_type=EnhancedEventTypes.BEHAVIORAL_ANALYSIS_COMPLETE,
            contact_id=contact_id,
            data={
                "response_velocity": response_velocity,
                "personality_type": personality_type,
                "temperature_trend": temperature_trend,
                "early_warning": early_warning,
                "channel_preferences": channel_preferences,
                "processing_time_ms": processing_time_ms,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def publish_sequence_optimization_applied(
        self,
        contact_id: str,
        original_sequence: Dict[str, int],
        optimized_sequence: Dict[str, int],
        optimization_factor: str,
        channel_sequence: List[str],
        confidence: float,
    ) -> None:
        """Publish sequence timing optimization."""
        await self.base_publisher.publish_event(
            event_type=EnhancedEventTypes.SEQUENCE_OPTIMIZATION_APPLIED,
            contact_id=contact_id,
            data={
                "original_sequence": original_sequence,
                "optimized_sequence": optimized_sequence,
                "optimization_factor": optimization_factor,
                "channel_sequence": channel_sequence,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def publish_personality_adaptation(
        self,
        contact_id: str,
        detected_personality: str,
        adaptation_applied: str,
        message_before: str,
        message_after: str,
        confidence: float,
    ) -> None:
        """Publish personality-based message adaptation."""
        await self.base_publisher.publish_event(
            event_type=EnhancedEventTypes.PERSONALITY_ADAPTATION,
            contact_id=contact_id,
            data={
                "detected_personality": detected_personality,
                "adaptation_applied": adaptation_applied,
                "message_before": message_before,
                "message_after": message_after,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def publish_temperature_prediction_update(
        self,
        contact_id: str,
        current_temperature: float,
        predicted_trend: str,
        confidence: float,
        early_warning: Optional[Dict],
        recommended_action: str,
    ) -> None:
        """Publish lead temperature prediction update."""
        await self.base_publisher.publish_event(
            event_type=EnhancedEventTypes.TEMPERATURE_PREDICTION_UPDATE,
            contact_id=contact_id,
            data={
                "current_temperature": current_temperature,
                "predicted_trend": predicted_trend,
                "confidence": confidence,
                "early_warning": early_warning,
                "recommended_action": recommended_action,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def publish_lead_bot_sequence_update(
        self,
        contact_id: str,
        sequence_day: int,
        action_type: str,
        success: bool,
        channel: Optional[str] = None,
        personalization_applied: Optional[bool] = None,
        next_action_date: Optional[str] = None,
        message_sent: Optional[str] = None,
    ) -> None:
        """Publish lead bot sequence update with enhancements."""
        await self.base_publisher.publish_event(
            event_type=EnhancedEventTypes.LEAD_BOT_SEQUENCE_UPDATE,
            contact_id=contact_id,
            data={
                "sequence_day": sequence_day,
                "action_type": action_type,
                "success": success,
                "channel": channel,
                "personalization_applied": personalization_applied,
                "next_action_date": next_action_date,
                "message_sent": message_sent,
                "timestamp": datetime.now().isoformat(),
            },
        )

    # --- Real-time Intent Decoder Events ---

    async def publish_realtime_intent_update(
        self,
        contact_id: str,
        conversation_id: str,
        intent_update: Dict[str, Any],
        semantic_analysis: Dict[str, Any],
        processing_time_ms: Optional[float] = None,
    ) -> None:
        """Publish real-time intent analysis update."""
        await self.base_publisher.publish_event(
            event_type=EnhancedEventTypes.REALTIME_INTENT_UPDATE,
            contact_id=contact_id,
            data={
                "conversation_id": conversation_id,
                "intent_update": intent_update,
                "semantic_analysis": semantic_analysis,
                "processing_time_ms": processing_time_ms,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def publish_semantic_analysis_complete(
        self,
        contact_id: str,
        message_analyzed: str,
        semantic_signals: List[str],
        confidence: float,
        context_insights: Dict[str, Any],
        urgency_detected: bool,
    ) -> None:
        """Publish semantic analysis completion."""
        await self.base_publisher.publish_event(
            event_type=EnhancedEventTypes.SEMANTIC_ANALYSIS_COMPLETE,
            contact_id=contact_id,
            data={
                "message_analyzed": message_analyzed[:100],  # Truncate for privacy
                "semantic_signals": semantic_signals,
                "confidence": confidence,
                "context_insights": context_insights,
                "urgency_detected": urgency_detected,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def publish_intent_trajectory_forecast(
        self,
        contact_id: str,
        conversation_id: str,
        forecast: str,
        confidence: float,
        predicted_scores: Dict[str, float],
        recommendation: str,
    ) -> None:
        """Publish intent trajectory forecast."""
        await self.base_publisher.publish_event(
            event_type=EnhancedEventTypes.INTENT_TRAJECTORY_FORECAST,
            contact_id=contact_id,
            data={
                "conversation_id": conversation_id,
                "forecast": forecast,
                "confidence": confidence,
                "predicted_scores": predicted_scores,
                "recommendation": recommendation,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def publish_early_warning_triggered(
        self,
        contact_id: str,
        warning_type: str,
        urgency: str,
        recommendation: str,
        current_scores: Dict[str, float],
        trigger_reason: str,
    ) -> None:
        """Publish early warning for lead intervention."""
        await self.base_publisher.publish_event(
            event_type=EnhancedEventTypes.EARLY_WARNING_TRIGGERED,
            contact_id=contact_id,
            data={
                "warning_type": warning_type,
                "urgency": urgency,
                "recommendation": recommendation,
                "current_scores": current_scores,
                "trigger_reason": trigger_reason,
                "timestamp": datetime.now().isoformat(),
                "requires_immediate_attention": urgency == "high",
            },
        )

    # --- Bot Orchestration Events ---

    async def publish_bot_orchestration_event(
        self,
        session_id: str,
        contact_id: str,
        bot_type: str,
        enhancement_level: str,
        realtime_analysis_applied: bool,
        adaptive_features_used: bool,
        predictive_features_used: bool,
        session_duration_minutes: float,
    ) -> None:
        """Publish bot orchestration event."""
        await self.base_publisher.publish_event(
            event_type=EnhancedEventTypes.BOT_ORCHESTRATION_EVENT,
            contact_id=contact_id,
            data={
                "session_id": session_id,
                "bot_type": bot_type,
                "enhancement_level": enhancement_level,
                "realtime_analysis_applied": realtime_analysis_applied,
                "adaptive_features_used": adaptive_features_used,
                "predictive_features_used": predictive_features_used,
                "session_duration_minutes": session_duration_minutes,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def publish_enhancement_performance_metrics(
        self,
        total_sessions: int,
        adaptive_decisions: int,
        predictive_optimizations: int,
        realtime_interventions: int,
        fallbacks_triggered: int,
        average_response_time_ms: float,
        enhancement_adoption_rate: float,
    ) -> None:
        """Publish enhancement performance metrics."""
        await self.base_publisher.publish_event(
            event_type=EnhancedEventTypes.ENHANCEMENT_PERFORMANCE_METRICS,
            data={
                "total_sessions": total_sessions,
                "adaptive_decisions": adaptive_decisions,
                "predictive_optimizations": predictive_optimizations,
                "realtime_interventions": realtime_interventions,
                "fallbacks_triggered": fallbacks_triggered,
                "average_response_time_ms": average_response_time_ms,
                "enhancement_adoption_rate": enhancement_adoption_rate,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def publish_fallback_triggered(
        self, contact_id: str, original_bot_type: str, fallback_bot_type: str, failure_reason: str, session_id: str
    ) -> None:
        """Publish fallback mechanism activation."""
        await self.base_publisher.publish_event(
            event_type=EnhancedEventTypes.FALLBACK_TRIGGERED,
            contact_id=contact_id,
            data={
                "original_bot_type": original_bot_type,
                "fallback_bot_type": fallback_bot_type,
                "failure_reason": failure_reason,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
            },
        )

    # --- Convenience Methods ---

    async def publish_conversation_update(
        self, conversation_id: str, lead_id: str, stage: str, message: str, enhancement_context: Optional[Dict] = None
    ) -> None:
        """Enhanced conversation update with enhancement context."""
        data = {
            "conversation_id": conversation_id,
            "lead_id": lead_id,
            "stage": stage,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }

        if enhancement_context:
            data["enhancement_context"] = enhancement_context

        await self.base_publisher.publish_conversation_update(
            conversation_id=conversation_id, lead_id=lead_id, stage=stage, message=message
        )

    async def publish_bot_status_update(
        self, bot_type: str, contact_id: str, status: str, current_step: str, enhancement_level: Optional[str] = None
    ) -> None:
        """Enhanced bot status update."""
        await self.base_publisher.publish_bot_status_update(
            bot_type=bot_type, contact_id=contact_id, status=status, current_step=current_step
        )

        # Additional enhanced status tracking
        if enhancement_level:
            await self.base_publisher.publish_event(
                event_type="enhanced_bot_status",
                contact_id=contact_id,
                data={
                    "bot_type": bot_type,
                    "status": status,
                    "current_step": current_step,
                    "enhancement_level": enhancement_level,
                    "timestamp": datetime.now().isoformat(),
                },
            )


# --- Singleton Factory ---

_enhanced_publisher_instance: Optional[EnhancedEventPublisher] = None


def get_enhanced_event_publisher() -> EnhancedEventPublisher:
    """Get singleton enhanced event publisher instance."""
    global _enhanced_publisher_instance

    if _enhanced_publisher_instance is None:
        _enhanced_publisher_instance = EnhancedEventPublisher()

    return _enhanced_publisher_instance


# --- Event Monitoring Utilities ---


class EnhancedEventMonitor:
    """Monitor and analyze enhanced bot events for performance insights."""

    def __init__(self):
        self.event_counts: Dict[str, int] = {}
        self.performance_metrics: Dict[str, List[float]] = {}

    async def record_event(self, event_type: str, processing_time_ms: Optional[float] = None):
        """Record event for monitoring."""
        self.event_counts[event_type] = self.event_counts.get(event_type, 0) + 1

        if processing_time_ms:
            if event_type not in self.performance_metrics:
                self.performance_metrics[event_type] = []
            self.performance_metrics[event_type].append(processing_time_ms)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary of enhanced events."""
        summary = {"total_events": sum(self.event_counts.values()), "event_breakdown": self.event_counts.copy()}

        # Calculate average processing times
        avg_times = {}
        for event_type, times in self.performance_metrics.items():
            avg_times[event_type] = sum(times) / len(times) if times else 0

        summary["average_processing_times_ms"] = avg_times

        return summary


# Global monitor instance
enhanced_event_monitor = EnhancedEventMonitor()
