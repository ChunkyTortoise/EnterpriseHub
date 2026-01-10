"""
Chat-ML Integration Module

Integrates chatbot system with the Behavioral Learning Engine for
real-time personalization and intelligent conversation management.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

from .chatbot_manager import ChatbotManager, UserType, ChatMessage
from .session_manager import SessionManager

logger = logging.getLogger(__name__)


class ChatMLIntegration:
    """
    Integration layer between chatbot system and ML pipeline.

    Features:
    - Real-time behavioral event tracking from conversations
    - ML-powered response personalization
    - Conversation insights and recommendations
    - Lead scoring and conversion prediction
    """

    def __init__(
        self,
        chatbot_manager: ChatbotManager,
        session_manager: SessionManager,
        behavior_tracker=None,
        feature_engineer=None,
        personalization_engine=None
    ):
        """Initialize chat-ML integration"""
        self.chatbot_manager = chatbot_manager
        self.session_manager = session_manager

        # ML components (may be None if ML not available)
        self.behavior_tracker = behavior_tracker
        self.feature_engineer = feature_engineer
        self.personalization_engine = personalization_engine

        self.ml_enabled = all([behavior_tracker, feature_engineer])

        logger.info(f"ChatMLIntegration initialized (ML enabled: {self.ml_enabled})")

    async def enhanced_process_message(
        self,
        user_id: str,
        tenant_id: str,
        message_content: str,
        session_id: Optional[str] = None,
        user_type: Optional[UserType] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Process message with ML enhancement"""

        try:
            # Process message through standard chatbot
            response_content, response_metadata = await self.chatbot_manager.process_message(
                user_id, tenant_id, message_content, session_id, user_type
            )

            # Enhance with ML insights if available
            if self.ml_enabled:
                enhanced_response, ml_insights = await self._enhance_with_ml(
                    user_id, tenant_id, message_content, response_content, context
                )

                response_metadata["ml_insights"] = ml_insights

                # Use enhanced response if it's significantly better
                if enhanced_response and len(enhanced_response) > len(response_content) * 0.8:
                    response_content = enhanced_response

            # Update session with ML insights
            await self._update_session_with_ml(user_id, tenant_id, response_metadata)

            return response_content, response_metadata

        except Exception as e:
            logger.error(f"Enhanced message processing failed: {str(e)}")
            # Fallback to standard processing
            return await self.chatbot_manager.process_message(
                user_id, tenant_id, message_content, session_id, user_type
            )

    async def get_conversation_insights(
        self,
        user_id: str,
        tenant_id: str,
        include_predictions: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive conversation insights with ML analysis"""

        # Get base insights from chatbot manager
        base_insights = await self.chatbot_manager.get_user_insights(user_id, tenant_id)

        if not self.ml_enabled:
            return base_insights

        try:
            # Add ML-powered insights
            ml_insights = await self._generate_ml_insights(user_id, tenant_id)

            # Combine insights
            enhanced_insights = {
                **base_insights,
                "ml_analysis": ml_insights,
                "timestamp": datetime.now().isoformat()
            }

            # Add predictions if requested
            if include_predictions and self.personalization_engine:
                predictions = await self._get_conversation_predictions(user_id, tenant_id)
                enhanced_insights["predictions"] = predictions

            return enhanced_insights

        except Exception as e:
            logger.error(f"Failed to generate ML insights: {str(e)}")
            return base_insights

    async def get_personalized_recommendations(
        self,
        user_id: str,
        tenant_id: str,
        max_results: int = 5,
        recommendation_type: str = "property"
    ) -> List[Dict[str, Any]]:
        """Get ML-powered personalized recommendations"""

        if not self.personalization_engine:
            return []

        try:
            # Get user type from conversation context
            conversation_key = f"{tenant_id}:{user_id}"
            context = self.chatbot_manager.conversations.get(conversation_key)

            if not context:
                return []

            # Get recommendations from ML engine
            predictions = await self.personalization_engine.get_recommendations(
                entity_id=user_id,
                entity_type=context.user_type.value,
                max_results=max_results
            )

            # Convert to chat-friendly format
            recommendations = []
            for pred in predictions:
                recommendation = {
                    "id": pred.entity_id,
                    "score": pred.predicted_value,
                    "confidence": pred.confidence,
                    "confidence_level": pred.confidence_level.value,
                    "type": recommendation_type,
                    "reasoning": pred.reasoning,
                    "metadata": pred.model_metadata
                }

                # Add explanation
                if self.personalization_engine:
                    explanation = await self.personalization_engine.get_explanation(
                        user_id, pred
                    )
                    recommendation["explanation"] = explanation

                recommendations.append(recommendation)

            return recommendations

        except Exception as e:
            logger.error(f"Failed to get recommendations: {str(e)}")
            return []

    async def track_conversation_outcome(
        self,
        user_id: str,
        tenant_id: str,
        outcome_type: str,
        outcome_value: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track conversation outcomes for ML learning"""

        if not self.behavior_tracker:
            return False

        try:
            # Create outcome event
            from services.learning.interfaces import BehavioralEvent, EventType

            event = BehavioralEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.LEAD_INTERACTION,
                timestamp=datetime.now(),
                lead_id=user_id,
                event_data={
                    "outcome_type": outcome_type,
                    "outcome_value": outcome_value,
                    "conversation_outcome": True
                },
                outcome=outcome_type,
                outcome_value=outcome_value,
                outcome_timestamp=datetime.now(),
                metadata=metadata or {}
            )

            # Track the outcome
            success = await self.behavior_tracker.track_event(event)

            if success:
                # Record feedback with personalization engine
                if self.personalization_engine:
                    await self.personalization_engine.record_feedback(
                        user_id, f"conversation_{tenant_id}", outcome_type, outcome_value
                    )

            return success

        except Exception as e:
            logger.error(f"Failed to track outcome: {str(e)}")
            return False

    # Private helper methods

    async def _enhance_with_ml(
        self,
        user_id: str,
        tenant_id: str,
        user_message: str,
        base_response: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """Enhance response with ML insights"""

        ml_insights = {}

        try:
            # Get recent behavioral events
            if self.behavior_tracker:
                events = await self.behavior_tracker.get_events(
                    entity_id=user_id,
                    start_time=datetime.now() - timedelta(days=7),
                    limit=50
                )

                if events and self.feature_engineer:
                    # Extract features
                    features = await self.feature_engineer.extract_features(
                        user_id, "lead", events
                    )

                    ml_insights["feature_count"] = len(features.numerical_features)
                    ml_insights["engagement_score"] = features.numerical_features.get("engagement_score", 0.5)

                    # Get personalization insights
                    if self.personalization_engine:
                        recommendations = await self.personalization_engine.get_recommendations(
                            entity_id=user_id,
                            entity_type="lead",
                            max_results=3
                        )

                        if recommendations:
                            ml_insights["recommendations_available"] = len(recommendations)
                            ml_insights["top_recommendation_score"] = recommendations[0].predicted_value
                            ml_insights["avg_confidence"] = sum(r.confidence for r in recommendations) / len(recommendations)

                            # Enhance response with recommendation context
                            enhanced_response = self._add_recommendation_context(
                                base_response, recommendations, user_message
                            )

                            return enhanced_response, ml_insights

        except Exception as e:
            logger.warning(f"ML enhancement failed: {str(e)}")

        return None, ml_insights

    def _add_recommendation_context(
        self,
        base_response: str,
        recommendations: List[Any],
        user_message: str
    ) -> str:
        """Add personalized recommendation context to response"""

        if not recommendations:
            return base_response

        # Check if user is asking about properties
        user_lower = user_message.lower()
        property_keywords = ["property", "house", "home", "listing", "show me"]

        if any(keyword in user_lower for keyword in property_keywords):
            # Add property recommendations
            rec_text = "\n\nBased on your preferences, I have some properties you might like:"

            for i, rec in enumerate(recommendations[:2]):  # Top 2 recommendations
                confidence_text = "high" if rec.confidence > 0.8 else "good" if rec.confidence > 0.6 else "moderate"
                rec_text += f"\n• Property {rec.entity_id[-6:]} ({confidence_text} match)"

            rec_text += "\n\nWould you like me to share the details?"

            return base_response + rec_text

        # Check if user is asking about budget or preferences
        elif any(keyword in user_lower for keyword in ["budget", "price", "afford", "looking for"]):
            # Add budget-relevant context
            if recommendations[0].confidence > 0.7:
                return base_response + f"\n\nBased on what you've shared, I think I have a good understanding of what you're looking for. Would you like me to show you some options?"

        return base_response

    async def _generate_ml_insights(
        self,
        user_id: str,
        tenant_id: str
    ) -> Dict[str, Any]:
        """Generate comprehensive ML insights"""

        insights = {}

        try:
            if self.behavior_tracker and self.feature_engineer:
                # Get events and extract features
                events = await self.behavior_tracker.get_events(
                    entity_id=user_id,
                    limit=100
                )

                if events:
                    features = await self.feature_engineer.extract_features(
                        user_id, "lead", events
                    )

                    insights["behavioral_analysis"] = {
                        "total_events": len(events),
                        "engagement_score": features.numerical_features.get("engagement_score", 0),
                        "interaction_velocity": features.numerical_features.get("interaction_velocity", 0),
                        "feature_extraction_time": datetime.now().isoformat()
                    }

                    # Property insights
                    insights["property_insights"] = {
                        "avg_price_viewed": features.numerical_features.get("avg_price_viewed", 0),
                        "property_type_diversity": features.numerical_features.get("property_type_diversity", 0),
                        "preferred_property_type": features.categorical_features.get("preferred_property_type", "unknown")
                    }

            # Session insights
            session = await self.session_manager.get_user_session(user_id, tenant_id)
            if session:
                insights["session_analysis"] = {
                    "session_duration_hours": (datetime.now() - session.created_at).total_seconds() / 3600,
                    "messages_in_session": session.message_count,
                    "current_stage": session.current_stage,
                    "user_profile_completeness": len(session.user_profile)
                }

        except Exception as e:
            logger.warning(f"Failed to generate ML insights: {str(e)}")

        return insights

    async def _get_conversation_predictions(
        self,
        user_id: str,
        tenant_id: str
    ) -> Dict[str, Any]:
        """Get ML predictions for conversation outcomes"""

        if not self.personalization_engine:
            return {}

        try:
            # Get conversation context
            conversation_key = f"{tenant_id}:{user_id}"
            context = self.chatbot_manager.conversations.get(conversation_key)

            if not context:
                return {}

            # Simple prediction mockup (would use actual ML models in production)
            predictions = {
                "conversion_probability": min(1.0, context.lead_score / 100 if context.lead_score else 0.5),
                "next_best_action": self._predict_next_action(context),
                "engagement_prediction": "high" if len(context.messages) > 5 else "medium",
                "timeline_prediction": self._predict_timeline(context)
            }

            return predictions

        except Exception as e:
            logger.warning(f"Failed to generate predictions: {str(e)}")
            return {}

    def _predict_next_action(self, context) -> str:
        """Predict the next best action for conversation"""

        if context.current_stage.value == "initial_contact":
            return "qualification_questions"
        elif context.current_stage.value == "qualification":
            return "property_recommendations"
        elif context.current_stage.value == "needs_assessment":
            return "schedule_showing"
        elif context.current_stage.value == "property_discussion":
            return "schedule_visit"
        else:
            return "follow_up"

    def _predict_timeline(self, context) -> str:
        """Predict conversation timeline"""

        message_count = len(context.messages)
        engagement = context.lead_score or 50

        if message_count > 10 and engagement > 70:
            return "ready_soon"
        elif message_count > 5 and engagement > 50:
            return "active_consideration"
        else:
            return "early_exploration"

    async def _update_session_with_ml(
        self,
        user_id: str,
        tenant_id: str,
        response_metadata: Dict[str, Any]
    ):
        """Update session with ML insights"""

        try:
            ml_insights = response_metadata.get("ml_insights", {})

            if ml_insights:
                session_update = {
                    "behavioral_data": {
                        "last_ml_update": datetime.now().isoformat(),
                        "engagement_score": ml_insights.get("engagement_score"),
                        "feature_count": ml_insights.get("feature_count"),
                        "recommendations_available": ml_insights.get("recommendations_available", 0)
                    }
                }

                await self.session_manager.update_session_activity(
                    user_id, session_update
                )

        except Exception as e:
            logger.warning(f"Failed to update session with ML data: {str(e)}")

    def get_integration_status(self) -> Dict[str, Any]:
        """Get integration status and health metrics"""

        return {
            "ml_enabled": self.ml_enabled,
            "components": {
                "behavior_tracker": self.behavior_tracker is not None,
                "feature_engineer": self.feature_engineer is not None,
                "personalization_engine": self.personalization_engine is not None
            },
            "chatbot_conversations": len(self.chatbot_manager.conversations),
            "active_sessions": len(self.session_manager.active_sessions),
            "status": "healthy" if self.ml_enabled else "limited_functionality"
        }