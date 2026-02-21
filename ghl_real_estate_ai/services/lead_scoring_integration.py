"""
Lead Scoring v2 Integration Module

This module provides helper functions for integrating composite lead scoring
and ML ensemble lead scoring into the Lead, Buyer, and Seller bots.
"""

from typing import Any, Dict, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.ensemble_lead_scoring import (
    EnsembleLeadScoringService,
    LeadScorePrediction,
    get_ensemble_lead_scoring_service,
)
from ghl_real_estate_ai.services.lead_scoring_v2 import (
    CompositeScore,
    LeadScoringServiceV2,
)
from ghl_real_estate_ai.services.sentiment_analysis_service import (
    ConversationSentiment,
    SentimentAnalysisService,
    SentimentType,
)

logger = get_logger(__name__)


class LeadScoringIntegration:
    """
    Integration helper for composite and ML ensemble lead scoring in bots.

    This class provides methods to:
    - Calculate composite scores from bot state
    - Predict lead scores using ML ensemble
    - Normalize sentiment scores
    - Sync composite scores to GHL
    - Update bot state with composite score information
    """

    def __init__(
        self,
        scoring_service: Optional[LeadScoringServiceV2] = None,
        sentiment_service: Optional[SentimentAnalysisService] = None,
        ensemble_service: Optional[EnsembleLeadScoringService] = None,
        enable_ml_ensemble: bool = True,
    ):
        """
        Initialize the lead scoring integration.

        Args:
            scoring_service: Composite scoring service
            sentiment_service: Sentiment analysis service
            ensemble_service: ML ensemble scoring service
            enable_ml_ensemble: Enable ML ensemble predictions
        """
        self.scoring_service = scoring_service or LeadScoringServiceV2()
        self.sentiment_service = sentiment_service or SentimentAnalysisService()
        self.ensemble_service = ensemble_service
        self.enable_ml_ensemble = enable_ml_ensemble

        # Try to load ensemble service if enabled
        if self.enable_ml_ensemble and self.ensemble_service is None:
            try:
                self.ensemble_service = get_ensemble_lead_scoring_service()
                logger.info("ML ensemble lead scoring enabled")
            except Exception as e:
                logger.warning(f"Failed to load ensemble service: {e}. Using rule-based scoring only.")
                self.enable_ml_ensemble = False

    async def calculate_and_store_composite_score(
        self,
        state: Dict[str, Any],
        contact_id: str,
        use_ml_ensemble: bool = True,
    ) -> Dict[str, Any]:
        """
        Calculate composite score from bot state and store it.
        Optionally uses ML ensemble for enhanced predictions.

        Args:
            state: Bot state dictionary
            contact_id: Contact ID
            use_ml_ensemble: Use ML ensemble if available

        Returns:
            Updated state with composite score information
        """
        try:
            # Extract component scores from state
            frs_score = state.get("frs_score", 0.0)
            pcs_score = state.get("pcs_score", 0.0)

            # Get or calculate sentiment score
            sentiment_score = await self._get_sentiment_score(state)

            # Calculate engagement score
            engagement_score = self._calculate_engagement_score(state)

            # Calculate data completeness
            data_completeness = self._calculate_data_completeness(state)

            # Calculate conversation depth
            conversation_history = state.get("conversation_history", [])
            conversation_depth = min(100.0, len(conversation_history) * 10.0)

            # Calculate composite score
            composite_score = await self.scoring_service.calculate_composite_score(
                frs_score=frs_score,
                pcs_score=pcs_score,
                sentiment_score=sentiment_score,
                engagement_score=engagement_score,
                data_completeness=data_completeness,
                conversation_depth=conversation_depth,
            )

            # Update state with composite score information
            state["composite_score"] = composite_score.total_score
            state["composite_classification"] = composite_score.classification.value
            state["composite_confidence"] = composite_score.confidence_level
            state["composite_confidence_interval"] = composite_score.confidence_interval
            state["composite_component_scores"] = composite_score.component_scores

            # Try ML ensemble prediction if enabled
            if use_ml_ensemble and self.enable_ml_ensemble and self.ensemble_service:
                try:
                    ml_prediction = await self._get_ml_ensemble_prediction(state, contact_id)
                    if ml_prediction:
                        state["ml_ensemble_score"] = ml_prediction.predicted_score * 100  # Scale to 0-100
                        state["ml_ensemble_class"] = ml_prediction.predicted_class
                        state["ml_model_agreement"] = ml_prediction.model_agreement
                        state["ml_confidence_interval"] = ml_prediction.confidence_interval
                        state["ml_feature_contributions"] = ml_prediction.feature_contributions

                        logger.info(
                            f"ML ensemble prediction for {contact_id}: "
                            f"{ml_prediction.predicted_score:.3f} ({ml_prediction.predicted_class}), "
                            f"agreement: {ml_prediction.model_agreement:.3f}"
                        )
                except Exception as e:
                    logger.warning(f"ML ensemble prediction failed for {contact_id}: {e}")

            logger.info(
                f"Composite score calculated for {contact_id}: "
                f"{composite_score.total_score:.2f} ({composite_score.classification.value})"
            )

            return state

        except Exception as e:
            logger.error(f"Error calculating composite score for {contact_id}: {e}")
            # Set default values on error
            state["composite_score"] = 0.0
            state["composite_classification"] = "unqualified"
            state["composite_confidence"] = 0.0
            state["composite_confidence_interval"] = (0.0, 0.0)
            state["composite_component_scores"] = {}
            return state

    async def _get_sentiment_score(self, state: Dict[str, Any]) -> float:
        """
        Get or calculate sentiment score from state.

        Args:
            state: Bot state dictionary

        Returns:
            Normalized sentiment score (0-100)
        """
        # Check if sentiment score is already in state
        if "sentiment_score" in state:
            return state["sentiment_score"]

        # Check if conversation sentiment is available
        conversation_sentiment = state.get("conversation_sentiment")
        if conversation_sentiment and isinstance(conversation_sentiment, ConversationSentiment):
            return self._normalize_sentiment(conversation_sentiment.overall_sentiment)

        # Calculate sentiment from conversation history
        conversation_history = state.get("conversation_history", [])
        if conversation_history:
            try:
                sentiment_result = await self.sentiment_service.analyze_conversation(conversation_history)
                return self._normalize_sentiment(sentiment_result.overall_sentiment)
            except Exception as e:
                logger.warning(f"Error analyzing sentiment: {e}")

        # Default to neutral (50)
        return 50.0

    def _normalize_sentiment(self, sentiment: SentimentType) -> float:
        """
        Normalize sentiment type to score (0-100).

        Args:
            sentiment: Sentiment type

        Returns:
            Normalized score (0-100)
        """
        sentiment_mapping = {
            SentimentType.POSITIVE: 100.0,
            SentimentType.NEUTRAL: 50.0,
            SentimentType.ANXIOUS: 30.0,
            SentimentType.FRUSTRATED: 20.0,
            SentimentType.ANGRY: 0.0,
            SentimentType.DISAPPOINTED: 25.0,
            SentimentType.CONFUSED: 35.0,
        }
        return sentiment_mapping.get(sentiment, 50.0)

    def _calculate_engagement_score(self, state: Dict[str, Any]) -> float:
        """
        Calculate engagement score from state.

        Args:
            state: Bot state dictionary

        Returns:
            Engagement score (0-100)
        """
        conversation_history = state.get("conversation_history", [])

        if not conversation_history:
            return 0.0

        # Calculate based on message patterns
        message_count = len(conversation_history)

        # Base score from message count (max 50 points)
        message_score = min(50.0, message_count * 5.0)

        # Additional score from message length (max 30 points)
        total_length = sum(len(msg.get("content", "")) for msg in conversation_history)
        length_score = min(30.0, total_length / 100.0)

        # Additional score from questions (max 20 points)
        question_count = sum(1 for msg in conversation_history if "?" in msg.get("content", ""))
        question_score = min(20.0, question_count * 5.0)

        return message_score + length_score + question_score

    def _calculate_data_completeness(self, state: Dict[str, Any]) -> float:
        """
        Calculate data completeness percentage from state.

        Args:
            state: Bot state dictionary

        Returns:
            Data completeness percentage (0-100)
        """
        required_fields = [
            "frs_score",
            "pcs_score",
            "sentiment_score",
            "budget",
            "timeline",
            "preferences",
        ]

        populated_fields = sum(
            1 for field in required_fields if state.get(field) is not None and state.get(field) != ""
        )

        return (populated_fields / len(required_fields)) * 100.0

    async def sync_composite_score_to_ghl(
        self,
        contact_id: str,
        composite_score: CompositeScore,
        ghl_client: Any,
    ) -> bool:
        """
        Sync composite score to GHL custom field.

        Args:
            contact_id: Contact ID
            composite_score: Composite score object
            ghl_client: GHL client instance

        Returns:
            True if sync was successful, False otherwise
        """
        try:
            # Map classification to GHL tag
            classification_tag = f"Composite-{composite_score.classification.value.capitalize()}"

            # Add tags to contact
            await ghl_client.add_contact_tags(contact_id=contact_id, tags=[classification_tag])

            # Update custom field with composite score
            await ghl_client.update_contact(
                contact_id=contact_id,
                custom_fields={
                    "composite_score": composite_score.total_score,
                    "composite_classification": composite_score.classification.value,
                    "composite_confidence": composite_score.confidence_level,
                },
            )

            logger.info(f"Synced composite score to GHL for {contact_id}")
            return True

        except Exception as e:
            logger.error(f"Error syncing composite score to GHL for {contact_id}: {e}")
            return False

    def get_classification_priority(self, classification: str) -> int:
        """
        Get priority level for lead classification.

        Args:
            classification: Lead classification string

        Returns:
            Priority level (higher = more priority)
        """
        priority_mapping = {
            "hot": 5,
            "warm": 4,
            "lukewarm": 3,
            "cold": 2,
            "unqualified": 1,
        }
        return priority_mapping.get(classification, 0)

    async def _get_ml_ensemble_prediction(
        self,
        state: Dict[str, Any],
        contact_id: str,
    ) -> Optional[LeadScorePrediction]:
        """
        Get ML ensemble prediction from bot state.

        Args:
            state: Bot state dictionary
            contact_id: Contact ID

        Returns:
            LeadScorePrediction or None if prediction fails
        """
        try:
            # Extract features from state for ML prediction
            features = {
                "property_data": state.get("property_data", {}),
                "market_data": state.get("market_data", {}),
                "psychology_profile": {
                    "psychological_commitment_score": state.get("pcs_score", 50.0),
                    "urgency_level": state.get("urgency_level", "medium"),
                    "motivation_type": state.get("motivation_type", "unknown"),
                    "negotiation_flexibility": 0.5,
                },
                "conversation_data": {
                    "message_count": len(state.get("conversation_history", [])),
                    "avg_response_time_seconds": 1800,
                },
            }

            # Get prediction
            prediction = await self.ensemble_service.predict_lead_score(
                contact_id=contact_id,
                features=features,
            )

            return prediction

        except Exception as e:
            logger.error(f"Error getting ML ensemble prediction for {contact_id}: {e}")
            return None

    def should_prioritize(self, state: Dict[str, Any]) -> bool:
        """
        Determine if a lead should be prioritized based on composite score.
        Uses ML ensemble score if available.

        Args:
            state: Bot state dictionary

        Returns:
            True if lead should be prioritized, False otherwise
        """
        # Check ML ensemble score first if available
        ml_score = state.get("ml_ensemble_score")
        if ml_score is not None:
            ml_class = state.get("ml_ensemble_class", "")
            if ml_class in ["hot", "warm"]:
                return True
            if ml_score >= 70.0:
                return True

        # Fall back to composite score
        composite_score = state.get("composite_score", 0.0)
        classification = state.get("composite_classification", "unqualified")

        # Prioritize hot and warm leads
        if classification in ["hot", "warm"]:
            return True

        # Prioritize leads with score above 70
        if composite_score >= 70.0:
            return True

        return False


# Singleton instance for easy access
_lead_scoring_integration: Optional[LeadScoringIntegration] = None


def get_lead_scoring_integration() -> LeadScoringIntegration:
    """Get or create the singleton lead scoring integration instance."""
    global _lead_scoring_integration
    if _lead_scoring_integration is None:
        _lead_scoring_integration = LeadScoringIntegration()
    return _lead_scoring_integration
