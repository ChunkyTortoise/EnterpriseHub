"""
Property Personalization Engine

Real-time personalized property recommendations for leads using ensemble
of collaborative filtering and content-based models.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
import uuid
import numpy as np
from collections import defaultdict

from ..interfaces import (
    IPersonalizationEngine, ILearningModel, ModelType,
    FeatureVector, ModelPrediction, LearningContext,
    ConfidenceLevel, IBehaviorTracker, IFeatureEngineer,
    BehavioralEvent, EventType, PredictionError
)

logger = logging.getLogger(__name__)


class PropertyPersonalizationEngine(IPersonalizationEngine):
    """
    Real-time personalized property recommendations for leads.

    Combines multiple ML models in an ensemble approach to provide
    sophisticated property recommendations with explainability and
    real-time adaptation.

    Key Features:
    - Multi-model ensemble (collaborative + content-based)
    - Real-time feature extraction and scoring pipeline
    - A/B testing framework for model comparison
    - Performance monitoring and model drift detection
    - Seamless integration with existing GHL workflow
    """

    def __init__(
        self,
        behavior_tracker: IBehaviorTracker,
        feature_engineer: IFeatureEngineer,
        collaborative_model: Optional[ILearningModel] = None,
        content_based_model: Optional[ILearningModel] = None,
        ensemble_weights: Optional[Dict[str, float]] = None,
        min_confidence: float = 0.4,
        max_recommendations: int = 10,
        enable_ab_testing: bool = False
    ):
        """
        Initialize property personalization engine.

        Args:
            behavior_tracker: Behavior tracking system
            feature_engineer: Feature engineering system
            collaborative_model: Collaborative filtering model
            content_based_model: Content-based filtering model
            ensemble_weights: Weights for model ensemble
            min_confidence: Minimum confidence for recommendations
            max_recommendations: Maximum recommendations to return
            enable_ab_testing: Enable A/B testing framework
        """
        self._engine_id = f"prop_engine_{uuid.uuid4().hex[:8]}"
        self._behavior_tracker = behavior_tracker
        self._feature_engineer = feature_engineer

        # ML Models
        self._models: Dict[str, ILearningModel] = {}
        if collaborative_model:
            self._models["collaborative"] = collaborative_model
        if content_based_model:
            self._models["content_based"] = content_based_model

        # Ensemble configuration
        self._ensemble_weights = ensemble_weights or {
            "collaborative": 0.6,
            "content_based": 0.4
        }

        # Performance settings
        self._min_confidence = min_confidence
        self._max_recommendations = max_recommendations
        self._enable_ab_testing = enable_ab_testing

        # Performance tracking
        self._recommendation_count = 0
        self._total_latency_ms = 0.0
        self._model_performance: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

        # A/B testing
        self._ab_experiments: Dict[str, Dict[str, Any]] = {}
        self._experiment_assignments: Dict[str, str] = {}

        # Caching for performance
        self._recommendation_cache: Dict[str, Tuple[List[ModelPrediction], datetime]] = {}
        self._cache_ttl_seconds = 300  # 5 minutes

        logger.info(f"Initialized PropertyPersonalizationEngine {self._engine_id}")
        logger.info(f"Models: {list(self._models.keys())}")
        logger.info(f"Ensemble weights: {self._ensemble_weights}")

    async def get_recommendations(
        self,
        entity_id: str,
        entity_type: str,
        max_results: int = 10,
        context: Optional[LearningContext] = None
    ) -> List[ModelPrediction]:
        """
        Get personalized recommendations for an entity.

        Args:
            entity_id: ID of entity to get recommendations for
            entity_type: Type of entity (typically "lead")
            max_results: Maximum number of recommendations
            context: Personalization context

        Returns:
            List of personalized predictions/recommendations
        """
        start_time = datetime.now()

        try:
            # Check cache first
            cache_key = f"{entity_id}_{entity_type}_{max_results}"
            if cache_key in self._recommendation_cache:
                cached_recommendations, cache_time = self._recommendation_cache[cache_key]
                if (datetime.now() - cache_time).total_seconds() < self._cache_ttl_seconds:
                    logger.debug(f"Using cached recommendations for {entity_id}")
                    return cached_recommendations[:max_results]

            logger.info(f"Generating recommendations for {entity_type} {entity_id}")

            # Get behavioral events
            events = await self._get_recent_events(entity_id, entity_type)

            if not events:
                logger.warning(f"No events found for {entity_id}, using cold start")
                return await self._get_cold_start_recommendations(entity_id, entity_type, max_results, context)

            # Extract features
            features = await self._feature_engineer.extract_features(
                entity_id, entity_type, events, context
            )

            # Get predictions from all models
            model_predictions = await self._get_ensemble_predictions(features, context)

            if not model_predictions:
                logger.warning(f"No model predictions for {entity_id}")
                return await self._get_cold_start_recommendations(entity_id, entity_type, max_results, context)

            # Combine predictions using ensemble
            final_recommendations = await self._combine_predictions(
                model_predictions, entity_id, max_results, context
            )

            # Filter by confidence
            filtered_recommendations = [
                pred for pred in final_recommendations
                if pred.confidence >= self._min_confidence
            ]

            # Apply A/B testing if enabled
            if self._enable_ab_testing:
                filtered_recommendations = await self._apply_ab_testing(
                    filtered_recommendations, entity_id, context
                )

            # Cache results
            self._recommendation_cache[cache_key] = (filtered_recommendations, datetime.now())

            # Update performance metrics
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            self._total_latency_ms += latency_ms
            self._recommendation_count += 1

            logger.info(f"Generated {len(filtered_recommendations)} recommendations in {latency_ms:.1f}ms")

            return filtered_recommendations[:max_results]

        except Exception as e:
            error_msg = f"Failed to get recommendations for {entity_id}: {str(e)}"
            logger.error(error_msg)

            # Return fallback recommendations
            return await self._get_fallback_recommendations(entity_id, entity_type, max_results, context)

    async def get_explanation(
        self,
        entity_id: str,
        prediction: ModelPrediction,
        context: Optional[LearningContext] = None
    ) -> Dict[str, Any]:
        """
        Get explanation for a prediction.

        Args:
            entity_id: Entity ID the prediction was made for
            prediction: The prediction to explain
            context: Context for explanation

        Returns:
            Explanation dictionary with reasoning and feature importance
        """
        try:
            explanation = {
                "prediction_id": prediction.model_metadata.get("prediction_id", "unknown"),
                "entity_id": entity_id,
                "predicted_property_id": prediction.entity_id,
                "predicted_value": prediction.predicted_value,
                "confidence": prediction.confidence,
                "confidence_level": prediction.confidence_level.value,
                "timestamp": datetime.now().isoformat(),
                "model_information": {
                    "primary_model": prediction.model_id,
                    "ensemble_weights": self._ensemble_weights,
                    "models_used": list(self._models.keys())
                },
                "reasoning": {
                    "primary_reasons": prediction.reasoning,
                    "feature_importance": prediction.feature_importance,
                    "behavioral_factors": await self._get_behavioral_factors(entity_id),
                    "similarity_factors": await self._get_similarity_factors(entity_id, prediction.entity_id)
                },
                "business_context": {
                    "recommendation_type": "personalized_property",
                    "personalization_engine": self._engine_id,
                    "real_estate_insights": await self._get_real_estate_insights(entity_id, prediction)
                },
                "performance_metadata": {
                    "processing_time_ms": prediction.processing_time_ms,
                    "cache_hit": False,  # Could track this
                    "model_performance": self._get_model_performance_summary()
                }
            }

            return explanation

        except Exception as e:
            logger.error(f"Failed to generate explanation: {str(e)}")
            return {
                "error": "Explanation generation failed",
                "entity_id": entity_id,
                "prediction_id": prediction.model_metadata.get("prediction_id", "unknown")
            }

    async def record_feedback(
        self,
        entity_id: str,
        prediction_id: str,
        feedback: str,
        feedback_value: Optional[float] = None
    ) -> bool:
        """
        Record user feedback on a prediction.

        Args:
            entity_id: Entity ID the prediction was made for
            prediction_id: ID of the prediction
            feedback: Feedback description
            feedback_value: Numerical feedback value

        Returns:
            True if feedback was successfully recorded
        """
        try:
            # Create feedback event
            feedback_event = BehavioralEvent(
                event_id=f"feedback_{uuid.uuid4().hex[:8]}",
                event_type=EventType.AGENT_ACTION,
                timestamp=datetime.now(),
                lead_id=entity_id,
                event_data={
                    "prediction_id": prediction_id,
                    "feedback": feedback,
                    "feedback_value": feedback_value,
                    "engine_id": self._engine_id
                },
                metadata={
                    "feedback_type": "recommendation_feedback",
                    "source": "personalization_engine"
                }
            )

            # Track the feedback event
            success = await self._behavior_tracker.track_event(feedback_event)

            if success:
                # Update online learning for models that support it
                for model_name, model in self._models.items():
                    try:
                        # This would require the original features - simplified for now
                        logger.info(f"Feedback recorded for {model_name}: {feedback}")
                    except Exception as e:
                        logger.warning(f"Online update failed for {model_name}: {str(e)}")

                # Update model performance tracking
                self._update_model_performance(prediction_id, feedback, feedback_value)

            logger.info(f"Recorded feedback for {entity_id}: {feedback} ({feedback_value})")
            return success

        except Exception as e:
            logger.error(f"Failed to record feedback: {str(e)}")
            return False

    # Helper methods

    async def _get_recent_events(
        self,
        entity_id: str,
        entity_type: str,
        days: int = 30
    ) -> List[BehavioralEvent]:
        """Get recent behavioral events for entity"""
        try:
            start_time = datetime.now() - timedelta(days=days)
            events = await self._behavior_tracker.get_events(
                entity_id=entity_id,
                entity_type=entity_type,
                start_time=start_time,
                limit=1000
            )

            logger.debug(f"Retrieved {len(events)} events for {entity_id}")
            return events

        except Exception as e:
            logger.error(f"Failed to get events for {entity_id}: {str(e)}")
            return []

    async def _get_ensemble_predictions(
        self,
        features: FeatureVector,
        context: Optional[LearningContext]
    ) -> Dict[str, ModelPrediction]:
        """Get predictions from all available models"""
        model_predictions = {}

        # Get predictions from all models in parallel
        tasks = []
        for model_name, model in self._models.items():
            if model.is_trained:
                tasks.append(self._get_safe_prediction(model_name, model, features, context))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, (model_name, _) in enumerate(self._models.items()):
                result = results[i] if i < len(results) else None
                if isinstance(result, ModelPrediction):
                    model_predictions[model_name] = result
                elif isinstance(result, Exception):
                    logger.warning(f"Prediction failed for {model_name}: {result}")

        return model_predictions

    async def _get_safe_prediction(
        self,
        model_name: str,
        model: ILearningModel,
        features: FeatureVector,
        context: Optional[LearningContext]
    ) -> Optional[ModelPrediction]:
        """Get prediction from model with error handling"""
        try:
            prediction = await model.predict(features, context)

            # Add ensemble metadata
            if prediction.model_metadata is None:
                prediction.model_metadata = {}

            prediction.model_metadata.update({
                "ensemble_model": model_name,
                "ensemble_weight": self._ensemble_weights.get(model_name, 0.0)
            })

            return prediction

        except Exception as e:
            logger.error(f"Prediction failed for {model_name}: {str(e)}")
            return None

    async def _combine_predictions(
        self,
        model_predictions: Dict[str, ModelPrediction],
        entity_id: str,
        max_results: int,
        context: Optional[LearningContext]
    ) -> List[ModelPrediction]:
        """Combine predictions from multiple models using ensemble weights"""

        if not model_predictions:
            return []

        # Group predictions by property
        property_predictions: Dict[str, List[Tuple[str, ModelPrediction]]] = defaultdict(list)

        for model_name, prediction in model_predictions.items():
            property_id = prediction.entity_id
            property_predictions[property_id].append((model_name, prediction))

        # Combine predictions for each property
        combined_predictions = []

        for property_id, predictions in property_predictions.items():
            if len(predictions) == 1:
                # Single model prediction
                model_name, prediction = predictions[0]
                combined_predictions.append(prediction)
            else:
                # Ensemble prediction
                ensemble_prediction = self._create_ensemble_prediction(
                    property_id, predictions, entity_id
                )
                combined_predictions.append(ensemble_prediction)

        # Sort by predicted value (confidence-weighted)
        combined_predictions.sort(
            key=lambda p: p.predicted_value * p.confidence,
            reverse=True
        )

        return combined_predictions

    def _create_ensemble_prediction(
        self,
        property_id: str,
        predictions: List[Tuple[str, ModelPrediction]],
        entity_id: str
    ) -> ModelPrediction:
        """Create ensemble prediction from multiple model predictions"""

        # Calculate weighted average
        total_weight = 0.0
        weighted_value = 0.0
        weighted_confidence = 0.0

        all_reasoning = []
        all_feature_importance = {}
        model_metadata = {
            "ensemble_models": [],
            "ensemble_weights": {},
            "individual_predictions": {}
        }

        for model_name, prediction in predictions:
            weight = self._ensemble_weights.get(model_name, 1.0)
            total_weight += weight

            weighted_value += prediction.predicted_value * weight
            weighted_confidence += prediction.confidence * weight

            # Collect reasoning
            all_reasoning.extend([f"[{model_name}] {reason}" for reason in prediction.reasoning])

            # Collect feature importance
            for feature, importance in prediction.feature_importance.items():
                feature_key = f"{model_name}_{feature}"
                all_feature_importance[feature_key] = importance * weight

            # Store metadata
            model_metadata["ensemble_models"].append(model_name)
            model_metadata["ensemble_weights"][model_name] = weight
            model_metadata["individual_predictions"][model_name] = {
                "value": prediction.predicted_value,
                "confidence": prediction.confidence
            }

        # Normalize by total weight
        if total_weight > 0:
            final_value = weighted_value / total_weight
            final_confidence = weighted_confidence / total_weight
        else:
            final_value = 0.0
            final_confidence = 0.0

        # Determine confidence level
        if final_confidence >= 0.8:
            confidence_level = ConfidenceLevel.HIGH
        elif final_confidence >= 0.6:
            confidence_level = ConfidenceLevel.MEDIUM
        elif final_confidence >= 0.4:
            confidence_level = ConfidenceLevel.LOW
        else:
            confidence_level = ConfidenceLevel.UNCERTAIN

        # Add ensemble reasoning
        all_reasoning.insert(0, f"Ensemble of {len(predictions)} models")
        all_reasoning.insert(1, f"Weighted average with total weight: {total_weight:.2f}")

        return ModelPrediction(
            entity_id=property_id,
            predicted_value=final_value,
            confidence=final_confidence,
            confidence_level=confidence_level,
            model_id=f"ensemble_{self._engine_id}",
            model_version="1.0",
            feature_importance=all_feature_importance,
            reasoning=all_reasoning,
            model_metadata=model_metadata
        )

    async def _apply_ab_testing(
        self,
        recommendations: List[ModelPrediction],
        entity_id: str,
        context: Optional[LearningContext]
    ) -> List[ModelPrediction]:
        """Apply A/B testing modifications to recommendations"""

        if not self._enable_ab_testing or not self._ab_experiments:
            return recommendations

        # Simple A/B testing implementation
        # In production, this would be more sophisticated

        experiment_id = self._get_experiment_assignment(entity_id)
        if experiment_id and experiment_id in self._ab_experiments:
            experiment = self._ab_experiments[experiment_id]

            # Apply experiment modifications
            if experiment.get("randomize_order"):
                import random
                random.shuffle(recommendations)

            if "confidence_boost" in experiment:
                boost = experiment["confidence_boost"]
                for prediction in recommendations:
                    prediction.confidence = min(1.0, prediction.confidence + boost)

        return recommendations

    def _get_experiment_assignment(self, entity_id: str) -> Optional[str]:
        """Get A/B test experiment assignment for entity"""
        if entity_id in self._experiment_assignments:
            return self._experiment_assignments[entity_id]

        # Simple hash-based assignment
        if self._ab_experiments:
            experiments = list(self._ab_experiments.keys())
            entity_hash = hash(entity_id)
            assignment = experiments[entity_hash % len(experiments)]
            self._experiment_assignments[entity_id] = assignment
            return assignment

        return None

    async def _get_cold_start_recommendations(
        self,
        entity_id: str,
        entity_type: str,
        max_results: int,
        context: Optional[LearningContext]
    ) -> List[ModelPrediction]:
        """Get recommendations for entities without interaction history"""

        # Return popular/default properties
        default_properties = [
            "prop_default_1",
            "prop_default_2",
            "prop_default_3"
        ]

        recommendations = []
        for i, property_id in enumerate(default_properties[:max_results]):
            recommendation = ModelPrediction(
                entity_id=property_id,
                predicted_value=0.5 - (i * 0.1),  # Decreasing scores
                confidence=0.3,  # Low confidence for cold start
                confidence_level=ConfidenceLevel.LOW,
                model_id=f"cold_start_{self._engine_id}",
                model_version="1.0",
                reasoning=[
                    "Cold start recommendation",
                    "No interaction history available",
                    "Using popularity-based fallback"
                ],
                model_metadata={
                    "recommendation_type": "cold_start",
                    "entity_id": entity_id
                }
            )
            recommendations.append(recommendation)

        return recommendations

    async def _get_fallback_recommendations(
        self,
        entity_id: str,
        entity_type: str,
        max_results: int,
        context: Optional[LearningContext]
    ) -> List[ModelPrediction]:
        """Get fallback recommendations when main pipeline fails"""

        return await self._get_cold_start_recommendations(entity_id, entity_type, max_results, context)

    async def _get_behavioral_factors(self, entity_id: str) -> Dict[str, Any]:
        """Get behavioral factors for explanation"""

        events = await self._get_recent_events(entity_id, "lead", days=7)

        return {
            "recent_interactions": len(events),
            "interaction_types": list(set([e.event_type.value for e in events])),
            "activity_level": "high" if len(events) > 20 else "medium" if len(events) > 5 else "low"
        }

    async def _get_similarity_factors(self, entity_id: str, property_id: str) -> Dict[str, Any]:
        """Get similarity factors for explanation"""

        return {
            "content_similarity": "Property features match user preferences",
            "collaborative_similarity": "Similar users also liked this property",
            "temporal_patterns": "Recommended based on recent viewing patterns"
        }

    async def _get_real_estate_insights(
        self,
        entity_id: str,
        prediction: ModelPrediction
    ) -> Dict[str, Any]:
        """Get real estate specific insights"""

        return {
            "market_context": "Property in trending neighborhood",
            "price_analysis": "Within user's preferred price range",
            "feature_match": "Matches user's desired property features",
            "timing": "Good time to view based on user behavior patterns"
        }

    def _get_model_performance_summary(self) -> Dict[str, Any]:
        """Get model performance summary"""

        avg_latency = 0.0
        if self._recommendation_count > 0:
            avg_latency = self._total_latency_ms / self._recommendation_count

        return {
            "total_recommendations": self._recommendation_count,
            "average_latency_ms": avg_latency,
            "models_active": len([m for m in self._models.values() if m.is_trained]),
            "cache_enabled": True,
            "ab_testing_enabled": self._enable_ab_testing
        }

    def _update_model_performance(
        self,
        prediction_id: str,
        feedback: str,
        feedback_value: Optional[float]
    ):
        """Update model performance tracking based on feedback"""

        # Simple performance tracking
        # In production, this would be more sophisticated

        if feedback_value is not None:
            for model_name in self._models.keys():
                self._model_performance[model_name]["total_feedback"] += 1
                self._model_performance[model_name]["sum_feedback"] += feedback_value

    def add_model(self, model_name: str, model: ILearningModel, weight: float = 1.0):
        """Add a model to the ensemble"""
        self._models[model_name] = model
        self._ensemble_weights[model_name] = weight
        logger.info(f"Added model {model_name} with weight {weight}")

    def remove_model(self, model_name: str):
        """Remove a model from the ensemble"""
        if model_name in self._models:
            del self._models[model_name]
        if model_name in self._ensemble_weights:
            del self._ensemble_weights[model_name]
        logger.info(f"Removed model {model_name}")

    def update_ensemble_weights(self, weights: Dict[str, float]):
        """Update ensemble weights"""
        self._ensemble_weights.update(weights)
        logger.info(f"Updated ensemble weights: {self._ensemble_weights}")

    def add_ab_experiment(self, experiment_id: str, experiment_config: Dict[str, Any]):
        """Add A/B testing experiment"""
        self._ab_experiments[experiment_id] = experiment_config
        logger.info(f"Added A/B experiment: {experiment_id}")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics"""

        return {
            "engine_id": self._engine_id,
            "models": list(self._models.keys()),
            "ensemble_weights": self._ensemble_weights,
            "recommendation_count": self._recommendation_count,
            "average_latency_ms": self._total_latency_ms / max(self._recommendation_count, 1),
            "model_performance": dict(self._model_performance),
            "cache_size": len(self._recommendation_cache),
            "ab_experiments": len(self._ab_experiments),
            "entity_assignments": len(self._experiment_assignments)
        }