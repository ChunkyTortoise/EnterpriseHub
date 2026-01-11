"""
Mobile Coaching Service (Phase 4: Mobile Optimization)

Mobile-optimized coaching service that provides real-time Claude AI insights
specifically designed for agents using mobile devices during client interactions.

Features:
- Touch-optimized coaching interface
- Reduced bandwidth coaching suggestions
- Offline coaching cache for common scenarios
- Battery-optimized API calls
- Quick action suggestions for mobile workflows
- Contextual mobile notifications
- One-tap coaching responses

Performance Targets:
- Mobile coaching response: <150ms
- Battery consumption: 50% reduction vs desktop
- Data usage: 70% reduction vs full coaching
- Touch interaction time: <3 taps for any action
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field
import time

# Local imports
from ghl_real_estate_ai.services.claude_semantic_analyzer import ClaudeSemanticAnalyzer
from ghl_real_estate_ai.config.mobile.settings import (
    MOBILE_PERFORMANCE_TARGETS,
    MOBILE_CLAUDE_CONFIG,
    MOBILE_UI_CONFIG
)

logger = logging.getLogger(__name__)


class MobileCoachingMode(Enum):
    """Mobile coaching operation modes"""
    FULL_COACHING = "full_coaching"          # Complete coaching with all features
    QUICK_INSIGHTS = "quick_insights"        # Essential insights only
    SILENT_MONITORING = "silent_monitoring"  # Background analysis, no notifications
    BATTERY_SAVER = "battery_saver"         # Minimal processing for battery conservation
    OFFLINE_MODE = "offline_mode"           # Cached responses only


class CoachingPriority(Enum):
    """Priority levels for mobile coaching alerts"""
    CRITICAL = "critical"     # Immediate attention needed (objection, decision point)
    HIGH = "high"            # Important insight (opportunity, rapport building)
    MEDIUM = "medium"        # Helpful suggestion (next question, timing)
    LOW = "low"             # Background information (context, notes)


class MobileActionType(Enum):
    """Quick action types for mobile interface"""
    RESPOND_TO_OBJECTION = "respond_to_objection"
    ASK_QUALIFYING_QUESTION = "ask_qualifying_question"
    SCHEDULE_FOLLOWUP = "schedule_followup"
    SHARE_PROPERTY_INFO = "share_property_info"
    REQUEST_REFERRAL = "request_referral"
    CLOSE_FOR_SHOWING = "close_for_showing"
    TAKE_NOTES = "take_notes"
    END_CONVERSATION = "end_conversation"


@dataclass
class MobileCoachingSuggestion:
    """Mobile-optimized coaching suggestion"""
    id: str
    priority: CoachingPriority
    title: str                    # Brief title for mobile display
    message: str                  # Concise coaching message
    suggested_response: Optional[str] = None  # Pre-written response option
    quick_actions: List[MobileActionType] = field(default_factory=list)
    timing_sensitive: bool = False
    expires_at: Optional[datetime] = None
    confidence: float = 0.0
    tap_to_action: Optional[str] = None  # One-tap action


@dataclass
class MobileCoachingContext:
    """Context for mobile coaching session"""
    agent_id: str
    session_id: str
    mode: MobileCoachingMode
    client_info: Dict[str, Any]
    property_context: Optional[Dict[str, Any]] = None
    location_context: Optional[Dict[str, Any]] = None
    device_info: Optional[Dict[str, Any]] = None
    network_status: str = "wifi"  # wifi, cellular, offline
    battery_level: Optional[float] = None


@dataclass
class MobileCoachingSession:
    """Mobile coaching session tracking"""
    session_id: str
    agent_id: str
    mode: MobileCoachingMode
    start_time: datetime
    context: MobileCoachingContext
    suggestions_delivered: List[MobileCoachingSuggestion] = field(default_factory=list)
    actions_taken: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    is_active: bool = True


class MobileCoachingService:
    """
    📱 Mobile Coaching Service for Claude AI

    Provides optimized coaching experience for agents using mobile devices,
    with focus on battery life, data efficiency, and touch-friendly interactions.
    """

    def __init__(self):
        self.claude_analyzer = ClaudeSemanticAnalyzer()
        self.active_sessions: Dict[str, MobileCoachingSession] = {}

        # Performance configuration
        self.performance_targets = MOBILE_PERFORMANCE_TARGETS
        self.claude_config = MOBILE_CLAUDE_CONFIG
        self.ui_config = MOBILE_UI_CONFIG

        # Initialize offline coaching cache
        self.offline_coaching_cache = self._initialize_offline_cache()

        # Initialize quick action templates
        self.quick_action_templates = self._initialize_quick_actions()

        # Performance tracking
        self.response_times: List[float] = []
        self.cache_hit_rate = 0.0

    def _initialize_offline_cache(self) -> Dict[str, Dict[str, Any]]:
        """Initialize offline coaching suggestions for common scenarios"""
        return {
            "first_meeting": {
                "title": "Build Rapport",
                "message": "Focus on learning about their needs and timeline",
                "suggested_response": "What's most important to you in your next home?",
                "priority": "medium"
            },
            "price_objection": {
                "title": "Address Price Concern",
                "message": "Acknowledge concern, then focus on value",
                "suggested_response": "I understand price is important. Let's look at the value this property offers...",
                "priority": "critical"
            },
            "showing_hesitation": {
                "title": "Overcome Hesitation",
                "message": "Ask specific questions about their concerns",
                "suggested_response": "What specific aspects would you like to know more about?",
                "priority": "high"
            },
            "decision_point": {
                "title": "Close for Next Step",
                "message": "Client is ready - ask for commitment",
                "suggested_response": "Based on what we've discussed, what would you like to do next?",
                "priority": "critical"
            },
            "positive_feedback": {
                "title": "Capitalize on Interest",
                "message": "They're engaged - provide more specifics",
                "suggested_response": "I can see you're interested in this feature. Let me show you more...",
                "priority": "high"
            },
            "timeline_urgency": {
                "title": "Create Urgency",
                "message": "Highlight market timing or availability",
                "suggested_response": "Given your timeline, we should move quickly on properties like this...",
                "priority": "medium"
            },
            "referral_opportunity": {
                "title": "Request Referral",
                "message": "Great time to ask for referrals",
                "suggested_response": "Do you know anyone else who might benefit from our services?",
                "priority": "low"
            }
        }

    def _initialize_quick_actions(self) -> Dict[MobileActionType, Dict[str, Any]]:
        """Initialize quick action templates for mobile interface"""
        return {
            MobileActionType.RESPOND_TO_OBJECTION: {
                "icon": "💬",
                "label": "Address Concern",
                "templates": [
                    "I understand your concern about [concern]. Let me explain...",
                    "That's a great question. Here's what I recommend...",
                    "Many clients have similar concerns. Here's how we handle that..."
                ]
            },
            MobileActionType.ASK_QUALIFYING_QUESTION: {
                "icon": "❓",
                "label": "Ask Question",
                "templates": [
                    "What's your timeline for making a decision?",
                    "What's most important to you in this price range?",
                    "Have you been pre-approved for financing?"
                ]
            },
            MobileActionType.SCHEDULE_FOLLOWUP: {
                "icon": "📅",
                "label": "Schedule",
                "templates": [
                    "I'll follow up with you tomorrow about...",
                    "Let's schedule a time to discuss next steps",
                    "I'll send you the information we discussed"
                ]
            },
            MobileActionType.SHARE_PROPERTY_INFO: {
                "icon": "🏠",
                "label": "Share Info",
                "templates": [
                    "I'll send you the property details",
                    "Let me show you similar properties",
                    "I'll email you the neighborhood information"
                ]
            },
            MobileActionType.CLOSE_FOR_SHOWING: {
                "icon": "🔑",
                "label": "Book Showing",
                "templates": [
                    "Would you like to see this property in person?",
                    "When would be a good time for a private showing?",
                    "I can arrange a showing for this weekend"
                ]
            }
        }

    async def start_mobile_coaching_session(
        self,
        agent_id: str,
        context: MobileCoachingContext
    ) -> MobileCoachingSession:
        """
        Start a new mobile coaching session

        Args:
            agent_id: Agent identifier
            context: Mobile coaching context with device and situation info

        Returns:
            MobileCoachingSession object
        """
        session_id = f"mobile_{agent_id}_{int(time.time())}"

        session = MobileCoachingSession(
            session_id=session_id,
            agent_id=agent_id,
            mode=context.mode,
            start_time=datetime.now(),
            context=context
        )

        self.active_sessions[session_id] = session

        # Optimize for device capabilities
        await self._optimize_for_device(session)

        logger.info(f"Mobile coaching session started: {session_id} in {context.mode.value} mode")
        return session

    async def get_mobile_coaching_suggestion(
        self,
        session_id: str,
        conversation_context: str,
        client_message: str,
        urgency_level: str = "normal"
    ) -> Optional[MobileCoachingSuggestion]:
        """
        Get mobile-optimized coaching suggestion

        Args:
            session_id: Mobile coaching session ID
            conversation_context: Current conversation context
            client_message: Latest client message
            urgency_level: Response urgency (normal, urgent, critical)

        Returns:
            MobileCoachingSuggestion optimized for mobile display
        """
        start_time = time.time()

        try:
            session = self.active_sessions.get(session_id)
            if not session or not session.is_active:
                return None

            # Check if we should use offline mode
            if self._should_use_offline_mode(session):
                suggestion = await self._get_offline_coaching_suggestion(
                    conversation_context, client_message
                )
            else:
                # Get Claude analysis with mobile optimizations
                suggestion = await self._get_claude_mobile_suggestion(
                    session, conversation_context, client_message, urgency_level
                )

            if suggestion:
                session.suggestions_delivered.append(suggestion)

                # Track performance
                processing_time = (time.time() - start_time) * 1000
                self.response_times.append(processing_time)
                session.performance_metrics["last_response_time_ms"] = processing_time

                # Check performance targets
                if processing_time > self.performance_targets["claude_integration_time"]:
                    logger.warning(f"Mobile coaching exceeded target: {processing_time:.1f}ms")

            return suggestion

        except Exception as e:
            logger.error(f"Error getting mobile coaching suggestion: {e}")
            return self._get_fallback_suggestion(urgency_level)

    async def execute_quick_action(
        self,
        session_id: str,
        action_type: MobileActionType,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a quick action from mobile interface

        Args:
            session_id: Mobile coaching session ID
            action_type: Type of quick action to execute
            context: Optional context for the action

        Returns:
            Action result with suggested text or next steps
        """
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return {"error": "Session not found"}

            action_template = self.quick_action_templates.get(action_type)
            if not action_template:
                return {"error": "Action type not supported"}

            # Execute the action
            result = await self._execute_action(action_type, action_template, context)

            # Track action
            action_record = {
                "action_type": action_type.value,
                "timestamp": datetime.now().isoformat(),
                "context": context,
                "result": result
            }
            session.actions_taken.append(action_record)

            logger.info(f"Quick action executed: {action_type.value} in session {session_id}")
            return result

        except Exception as e:
            logger.error(f"Error executing quick action: {e}")
            return {"error": str(e)}

    def _should_use_offline_mode(self, session: MobileCoachingSession) -> bool:
        """Determine if we should use offline mode based on context"""
        context = session.context

        # Use offline mode if explicitly set
        if session.mode == MobileCoachingMode.OFFLINE_MODE:
            return True

        # Use offline mode for battery conservation
        if session.mode == MobileCoachingMode.BATTERY_SAVER:
            return True

        # Use offline mode if poor network conditions
        if context.network_status == "offline":
            return True

        # Use offline mode if low battery
        if context.battery_level and context.battery_level < 0.20:  # Below 20%
            return True

        return False

    async def _get_offline_coaching_suggestion(
        self,
        conversation_context: str,
        client_message: str
    ) -> Optional[MobileCoachingSuggestion]:
        """Get coaching suggestion from offline cache"""
        try:
            # Simple keyword matching for offline suggestions
            message_lower = client_message.lower()

            # Check for common scenarios
            if any(word in message_lower for word in ["price", "expensive", "cost", "budget"]):
                cached_suggestion = self.offline_coaching_cache["price_objection"]
                self.cache_hit_rate += 1  # Track cache usage

            elif any(word in message_lower for word in ["think", "consider", "maybe", "unsure"]):
                cached_suggestion = self.offline_coaching_cache["showing_hesitation"]
                self.cache_hit_rate += 1

            elif any(word in message_lower for word in ["love", "perfect", "great", "amazing"]):
                cached_suggestion = self.offline_coaching_cache["positive_feedback"]
                self.cache_hit_rate += 1

            else:
                # Default to first meeting guidance
                cached_suggestion = self.offline_coaching_cache["first_meeting"]

            # Convert cached suggestion to MobileCoachingSuggestion
            suggestion = MobileCoachingSuggestion(
                id=f"offline_{int(time.time())}",
                priority=CoachingPriority(cached_suggestion["priority"]),
                title=cached_suggestion["title"],
                message=cached_suggestion["message"],
                suggested_response=cached_suggestion.get("suggested_response"),
                quick_actions=[MobileActionType.RESPOND_TO_OBJECTION],  # Default action
                confidence=0.8  # Offline suggestions have good confidence
            )

            return suggestion

        except Exception as e:
            logger.error(f"Error getting offline suggestion: {e}")
            return None

    async def _get_claude_mobile_suggestion(
        self,
        session: MobileCoachingSession,
        conversation_context: str,
        client_message: str,
        urgency_level: str
    ) -> Optional[MobileCoachingSuggestion]:
        """Get coaching suggestion from Claude AI with mobile optimizations"""
        try:
            # Analyze with Claude (mobile-optimized)
            analysis = await self.claude_analyzer.analyze_lead_intent([
                {"speaker": "client", "message": client_message, "context": conversation_context}
            ])

            # Generate mobile-optimized suggestion
            suggestion = await self._create_mobile_suggestion_from_analysis(
                analysis, urgency_level, session.context
            )

            return suggestion

        except Exception as e:
            logger.error(f"Error getting Claude mobile suggestion: {e}")
            return None

    async def _create_mobile_suggestion_from_analysis(
        self,
        analysis: Dict[str, Any],
        urgency_level: str,
        context: MobileCoachingContext
    ) -> MobileCoachingSuggestion:
        """Create mobile coaching suggestion from Claude analysis"""
        intent = analysis.get("primary_intent", "general_inquiry")
        sentiment = analysis.get("sentiment", "neutral")
        urgency = analysis.get("urgency_level", urgency_level)

        # Map analysis to mobile-friendly coaching
        if intent == "objection":
            priority = CoachingPriority.CRITICAL
            title = "Handle Objection"
            message = "Client raised a concern - address it directly"
            quick_actions = [MobileActionType.RESPOND_TO_OBJECTION]
            suggested_response = "I understand your concern. Let me address that..."

        elif intent == "interest" or sentiment == "positive":
            priority = CoachingPriority.HIGH
            title = "Build on Interest"
            message = "Client is engaged - provide more details"
            quick_actions = [MobileActionType.SHARE_PROPERTY_INFO, MobileActionType.CLOSE_FOR_SHOWING]
            suggested_response = "I can see this interests you. Would you like to know more about..."

        elif intent == "ready_to_decide":
            priority = CoachingPriority.CRITICAL
            title = "Close Opportunity"
            message = "Perfect time to ask for next step"
            quick_actions = [MobileActionType.CLOSE_FOR_SHOWING, MobileActionType.SCHEDULE_FOLLOWUP]
            suggested_response = "Based on our discussion, what would you like to do next?"

        else:
            priority = CoachingPriority.MEDIUM
            title = "Continue Discovery"
            message = "Keep learning about their needs"
            quick_actions = [MobileActionType.ASK_QUALIFYING_QUESTION]
            suggested_response = "Tell me more about what you're looking for..."

        # Set timing for urgent suggestions
        expires_at = None
        timing_sensitive = False
        if priority == CoachingPriority.CRITICAL:
            expires_at = datetime.now() + timedelta(minutes=2)
            timing_sensitive = True

        suggestion = MobileCoachingSuggestion(
            id=f"claude_{int(time.time())}",
            priority=priority,
            title=title,
            message=message,
            suggested_response=suggested_response,
            quick_actions=quick_actions,
            timing_sensitive=timing_sensitive,
            expires_at=expires_at,
            confidence=analysis.get("confidence", 0.7),
            tap_to_action="Use Suggestion"  # One-tap action
        )

        return suggestion

    def _get_fallback_suggestion(self, urgency_level: str) -> MobileCoachingSuggestion:
        """Get fallback suggestion when analysis fails"""
        if urgency_level == "critical":
            cached = self.offline_coaching_cache["decision_point"]
            priority = CoachingPriority.CRITICAL
        else:
            cached = self.offline_coaching_cache["first_meeting"]
            priority = CoachingPriority.MEDIUM

        return MobileCoachingSuggestion(
            id=f"fallback_{int(time.time())}",
            priority=priority,
            title=cached["title"],
            message=cached["message"],
            suggested_response=cached.get("suggested_response"),
            confidence=0.5
        )

    async def _execute_action(
        self,
        action_type: MobileActionType,
        action_template: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a specific mobile action"""
        try:
            templates = action_template.get("templates", [])
            icon = action_template.get("icon", "📱")
            label = action_template.get("label", "Action")

            # Select appropriate template based on context
            if context and "scenario" in context:
                # Could add more sophisticated template selection logic here
                suggested_text = templates[0] if templates else "Continue the conversation..."
            else:
                suggested_text = templates[0] if templates else "Continue the conversation..."

            return {
                "action_type": action_type.value,
                "icon": icon,
                "label": label,
                "suggested_text": suggested_text,
                "templates": templates,
                "success": True
            }

        except Exception as e:
            logger.error(f"Error executing action: {e}")
            return {"error": str(e), "success": False}

    async def _optimize_for_device(self, session: MobileCoachingSession):
        """Optimize coaching session for specific device capabilities"""
        context = session.context
        device_info = context.device_info or {}

        # Adjust coaching frequency based on battery level
        if context.battery_level and context.battery_level < 0.30:
            session.mode = MobileCoachingMode.BATTERY_SAVER
            logger.info(f"Switched to battery saver mode: {context.battery_level:.0%} battery")

        # Adjust for network conditions
        if context.network_status == "cellular":
            # Reduce data usage on cellular
            session.performance_metrics["data_optimization"] = True

        # Optimize for screen size
        screen_size = device_info.get("screen_size", "medium")
        if screen_size == "small":
            session.performance_metrics["compact_ui"] = True

    async def end_mobile_coaching_session(self, session_id: str) -> Dict[str, Any]:
        """End mobile coaching session and provide summary"""
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        session.is_active = False
        session_duration = (datetime.now() - session.start_time).total_seconds()

        # Calculate session metrics
        avg_response_time = sum(self.response_times[-10:]) / max(len(self.response_times[-10:]), 1)

        summary = {
            "session_id": session_id,
            "agent_id": session.agent_id,
            "mode": session.mode.value,
            "duration_seconds": session_duration,
            "suggestions_delivered": len(session.suggestions_delivered),
            "actions_taken": len(session.actions_taken),
            "average_response_time_ms": avg_response_time,
            "cache_hit_rate": self.cache_hit_rate,
            "performance_metrics": session.performance_metrics
        }

        # Clean up completed session
        del self.active_sessions[session_id]

        logger.info(f"Mobile coaching session completed: {session_id}")
        return summary

    def get_mobile_performance_metrics(self) -> Dict[str, Any]:
        """Get mobile coaching performance metrics"""
        active_sessions = len(self.active_sessions)
        avg_response_time = sum(self.response_times[-50:]) / max(len(self.response_times[-50:]), 1)

        target_met = avg_response_time <= self.performance_targets["claude_integration_time"]

        return {
            "active_mobile_sessions": active_sessions,
            "average_response_time_ms": avg_response_time,
            "claude_integration_target_ms": self.performance_targets["claude_integration_time"],
            "performance_target_met": target_met,
            "cache_hit_rate": self.cache_hit_rate,
            "offline_mode_ready": True
        }