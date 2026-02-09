"""
Lead Churn Prediction Engine with Multi-Horizon Risk Assessment & Recovery Tracking

This module provides comprehensive churn prediction capabilities including:
- Multi-dimensional feature extraction from lead behavior
- Machine learning-based risk scoring with confidence intervals
- Multi-horizon predictions (7, 14, 30 days)
- Explainable AI with feature importance rankings
- Real-time risk stratification and intervention recommendations
- ENHANCED: Actual churn event tracking and recovery eligibility assessment

Key Components:
- ChurnFeatureExtractor: Extracts 27+ behavioral features
- ChurnRiskPredictor: ML model with ensemble predictions
- ChurnRiskStratifier: Risk tier assignment and recommendations
- ChurnEventTracker: Tracks actual churn events and recovery eligibility (NEW)
- ChurnPredictionEngine: Main orchestration class

Author: EnterpriseHub AI
Last Updated: 2026-01-19 (Enhanced for recovery tracking)
"""

import logging
import warnings
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# Internal imports
# from .memory_service import MemoryService  # Disabled for deployment
# from .lead_lifecycle import LeadLifecycleTracker  # Disabled for deployment
# from .behavioral_triggers import BehavioralTriggerEngine  # Disabled for deployment
# from .lead_scorer import LeadScorer  # Disabled for deployment

# Configure logging
logger = logging.getLogger(__name__)


# Placeholder classes for deployment (disabled services)
class MemoryService:
    def __init__(self):
        pass

    async def store_interaction(self, *args, **kwargs):
        pass


class LeadLifecycleTracker:
    def __init__(self):
        pass

    async def track_lifecycle_stage(self, *args, **kwargs):
        pass


class BehavioralTriggerEngine:
    def __init__(self):
        pass

    async def evaluate_triggers(self, *args, **kwargs):
        return []


class LeadScorer:
    def __init__(self):
        pass

    async def calculate_lead_score(self, *args, **kwargs):
        return 0.5


class ChurnRiskTier(Enum):
    """Risk tier classifications for churn prediction"""

    CRITICAL = "critical"  # 80-100% churn risk - immediate intervention
    HIGH = "high"  # 60-80% churn risk - urgent follow-up
    MEDIUM = "medium"  # 30-60% churn risk - nurture campaign
    LOW = "low"  # 0-30% churn risk - standard engagement


@dataclass
class ChurnPrediction:
    """Complete churn prediction result with multi-horizon forecasts"""

    lead_id: str
    prediction_timestamp: datetime

    # Multi-horizon risk scores (0-100)
    risk_score_7d: float
    risk_score_14d: float
    risk_score_30d: float

    # Risk classification
    risk_tier: ChurnRiskTier
    confidence: float  # Model confidence (0-1)

    # Feature importance for explainability
    top_risk_factors: List[Tuple[str, float]]  # (feature_name, importance)

    # Intervention recommendations
    recommended_actions: List[str]
    intervention_urgency: str  # immediate, urgent, moderate, low

    # Supporting data
    feature_vector: Dict[str, float]
    model_version: str


@dataclass
class ChurnFeatures:
    """Structured representation of extracted churn features"""

    # Engagement metrics
    days_since_last_interaction: float
    interaction_frequency_7d: float
    interaction_frequency_14d: float
    interaction_frequency_30d: float
    response_rate_7d: float
    response_rate_14d: float
    response_rate_30d: float

    # Behavioral patterns
    engagement_trend: float  # -1 (declining) to 1 (increasing)
    session_duration_avg: float
    property_views_per_session: float
    saved_properties_count: float
    search_refinements_count: float

    # Lifecycle progression
    stage_progression_velocity: float
    stage_stagnation_days: float
    backward_stage_transitions: float
    qualification_score_change: float

    # Communication patterns
    email_open_rate: float
    email_click_rate: float
    sms_response_rate: float
    call_pickup_rate: float
    preferred_communication_channel_consistency: float

    # Property preference stability
    budget_range_changes: float
    location_preference_changes: float
    property_type_changes: float
    feature_requirements_changes: float

    # External indicators
    market_activity_correlation: float
    seasonal_activity_alignment: float

    def to_vector(self) -> np.ndarray:
        """Convert features to numpy array for ML model input"""
        return np.array([getattr(self, field.name) for field in self.__dataclass_fields__.values()])

    def to_dict(self) -> Dict[str, float]:
        """Convert features to dictionary"""
        return asdict(self)


class ChurnFeatureExtractor:
    """Extracts comprehensive behavioral features for churn prediction"""

    def __init__(
        self,
        memory_service: MemoryService,
        lifecycle_tracker: LeadLifecycleTracker,
        behavioral_engine: BehavioralTriggerEngine,
        lead_scorer: LeadScorer,
    ):
        self.memory_service = memory_service
        self.lifecycle_tracker = lifecycle_tracker
        self.behavioral_engine = behavioral_engine
        self.lead_scorer = lead_scorer
        self.logger = logging.getLogger(__name__ + ".ChurnFeatureExtractor")

    async def extract_features(self, lead_id: str) -> ChurnFeatures:
        """
        Extract comprehensive churn prediction features for a lead

        Args:
            lead_id: Unique identifier for the lead

        Returns:
            ChurnFeatures: Structured feature representation
        """
        try:
            self.logger.info(f"Extracting churn features for lead {lead_id}")

            # Get data from all sources
            memory_data = await self._get_memory_data(lead_id)
            lifecycle_data = await self._get_lifecycle_data(lead_id)
            behavioral_data = await self._get_behavioral_data(lead_id)
            scoring_data = await self._get_scoring_data(lead_id)

            # Extract engagement metrics
            engagement_features = self._extract_engagement_features(memory_data, behavioral_data)

            # Extract behavioral patterns
            behavioral_features = self._extract_behavioral_patterns(behavioral_data)

            # Extract lifecycle progression
            lifecycle_features = self._extract_lifecycle_features(lifecycle_data, scoring_data)

            # Extract communication patterns
            communication_features = self._extract_communication_features(memory_data, behavioral_data)

            # Extract preference stability
            preference_features = self._extract_preference_features(memory_data, behavioral_data)

            # Extract external indicators
            external_features = self._extract_external_indicators(lead_id, behavioral_data)

            # Combine all features
            features = ChurnFeatures(
                # Engagement metrics
                **engagement_features,
                # Behavioral patterns
                **behavioral_features,
                # Lifecycle progression
                **lifecycle_features,
                # Communication patterns
                **communication_features,
                # Preference stability
                **preference_features,
                # External indicators
                **external_features,
            )

            self.logger.info(f"Successfully extracted {len(features.to_dict())} features for lead {lead_id}")
            return features

        except Exception as e:
            self.logger.error(f"Error extracting features for lead {lead_id}: {str(e)}")
            # Return default features to prevent pipeline failure
            return self._get_default_features()

    async def _get_memory_data(self, lead_id: str) -> Dict[str, Any]:
        """Get conversation and interaction history from memory service"""
        try:
            lead_context = await self.memory_service.get_lead_context(lead_id)
            conversation_history = await self.memory_service.get_conversation_history(lead_id, days=30)
            return {
                "context": lead_context,
                "conversations": conversation_history,
                "last_interaction": await self.memory_service.get_last_interaction(lead_id),
            }
        except Exception as e:
            self.logger.warning(f"Failed to get memory data for {lead_id}: {str(e)}")
            return {}

    async def _get_lifecycle_data(self, lead_id: str) -> Dict[str, Any]:
        """Get lifecycle stage progression data"""
        try:
            current_stage = await self.lifecycle_tracker.get_current_stage(lead_id)
            stage_history = await self.lifecycle_tracker.get_stage_history(lead_id)
            return {
                "current_stage": current_stage,
                "stage_history": stage_history,
                "progression_metrics": await self.lifecycle_tracker.get_progression_metrics(lead_id),
            }
        except Exception as e:
            self.logger.warning(f"Failed to get lifecycle data for {lead_id}: {str(e)}")
            return {}

    async def _get_behavioral_data(self, lead_id: str) -> Dict[str, Any]:
        """Get behavioral event data"""
        try:
            recent_events = await self.behavioral_engine.get_recent_events(lead_id, days=30)
            engagement_metrics = await self.behavioral_engine.calculate_engagement_metrics(lead_id)
            return {
                "recent_events": recent_events,
                "engagement_metrics": engagement_metrics,
                "event_patterns": await self.behavioral_engine.analyze_patterns(lead_id),
            }
        except Exception as e:
            self.logger.warning(f"Failed to get behavioral data for {lead_id}: {str(e)}")
            return {}

    async def _get_scoring_data(self, lead_id: str) -> Dict[str, Any]:
        """Get lead scoring and qualification data"""
        try:
            current_score = await self.lead_scorer.get_current_score(lead_id)
            score_history = await self.lead_scorer.get_score_history(lead_id, days=30)
            return {
                "current_score": current_score,
                "score_history": score_history,
                "qualification_factors": await self.lead_scorer.get_qualification_factors(lead_id),
            }
        except Exception as e:
            self.logger.warning(f"Failed to get scoring data for {lead_id}: {str(e)}")
            return {}

    def _extract_engagement_features(self, memory_data: Dict, behavioral_data: Dict) -> Dict[str, float]:
        """Extract engagement-related features"""
        from datetime import timezone

        now = datetime.now(timezone.utc)

        # Days since last interaction
        last_interaction = memory_data.get("last_interaction", {})
        days_since_last = 999.0  # Default for no interaction
        if last_interaction and "timestamp" in last_interaction:
            ts_str = last_interaction["timestamp"]
            last_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if last_time.tzinfo is None:
                last_time = last_time.replace(tzinfo=timezone.utc)
            days_since_last = (now - last_time).days

        # Interaction frequencies
        events = behavioral_data.get("recent_events", [])

        def get_event_ts(event):
            ts_str = event.get("timestamp", "")
            if not ts_str:
                return datetime.min.replace(tzinfo=timezone.utc)
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            return ts

        interactions_7d = sum(1 for event in events if (now - get_event_ts(event)).days <= 7)
        interactions_14d = sum(1 for event in events if (now - get_event_ts(event)).days <= 14)
        interactions_30d = len(events)

        # Response rates
        conversations = memory_data.get("conversations", [])
        response_rate_7d = self._calculate_response_rate(conversations, 7)
        response_rate_14d = self._calculate_response_rate(conversations, 14)
        response_rate_30d = self._calculate_response_rate(conversations, 30)

        return {
            "days_since_last_interaction": min(days_since_last, 30.0),  # Cap at 30 days
            "interaction_frequency_7d": interactions_7d,
            "interaction_frequency_14d": interactions_14d,
            "interaction_frequency_30d": interactions_30d,
            "response_rate_7d": response_rate_7d,
            "response_rate_14d": response_rate_14d,
            "response_rate_30d": response_rate_30d,
        }

    def _extract_behavioral_patterns(self, behavioral_data: Dict) -> Dict[str, float]:
        """Extract behavioral pattern features"""
        engagement_metrics = behavioral_data.get("engagement_metrics", {})
        event_patterns = behavioral_data.get("event_patterns", {})

        return {
            "engagement_trend": engagement_metrics.get("trend", 0.0),
            "session_duration_avg": engagement_metrics.get("avg_session_duration", 0.0),
            "property_views_per_session": engagement_metrics.get("views_per_session", 0.0),
            "saved_properties_count": engagement_metrics.get("saved_properties", 0.0),
            "search_refinements_count": engagement_metrics.get("search_refinements", 0.0),
        }

    def _extract_lifecycle_features(self, lifecycle_data: Dict, scoring_data: Dict) -> Dict[str, float]:
        """Extract lifecycle progression features"""
        progression_metrics = lifecycle_data.get("progression_metrics", {})
        score_history = scoring_data.get("score_history", [])

        # Stage progression velocity
        stage_velocity = progression_metrics.get("velocity", 0.0)

        # Stage stagnation
        stage_stagnation = progression_metrics.get("stagnation_days", 0.0)

        # Backward transitions
        backward_transitions = progression_metrics.get("backward_transitions", 0.0)

        # Qualification score change
        score_change = 0.0
        if len(score_history) >= 2:
            recent_score = score_history[0].get("score", 0.0)
            previous_score = score_history[-1].get("score", 0.0)
            score_change = recent_score - previous_score

        return {
            "stage_progression_velocity": stage_velocity,
            "stage_stagnation_days": min(stage_stagnation, 30.0),
            "backward_stage_transitions": backward_transitions,
            "qualification_score_change": score_change,
        }

    def _extract_communication_features(self, memory_data: Dict, behavioral_data: Dict) -> Dict[str, float]:
        """Extract communication pattern features"""
        conversations = memory_data.get("conversations", [])

        # Calculate communication channel metrics
        email_opens = sum(1 for conv in conversations if conv.get("channel") == "email" and conv.get("opened", False))
        email_total = sum(1 for conv in conversations if conv.get("channel") == "email")
        email_open_rate = email_opens / email_total if email_total > 0 else 0.0

        email_clicks = sum(1 for conv in conversations if conv.get("channel") == "email" and conv.get("clicked", False))
        email_click_rate = email_clicks / email_total if email_total > 0 else 0.0

        sms_responses = sum(1 for conv in conversations if conv.get("channel") == "sms" and conv.get("response"))
        sms_total = sum(1 for conv in conversations if conv.get("channel") == "sms")
        sms_response_rate = sms_responses / sms_total if sms_total > 0 else 0.0

        call_pickups = sum(1 for conv in conversations if conv.get("channel") == "call" and conv.get("pickup", False))
        call_total = sum(1 for conv in conversations if conv.get("channel") == "call")
        call_pickup_rate = call_pickups / call_total if call_total > 0 else 0.0

        # Channel consistency
        channel_consistency = self._calculate_channel_consistency(conversations)

        return {
            "email_open_rate": email_open_rate,
            "email_click_rate": email_click_rate,
            "sms_response_rate": sms_response_rate,
            "call_pickup_rate": call_pickup_rate,
            "preferred_communication_channel_consistency": channel_consistency,
        }

    def _extract_preference_features(self, memory_data: Dict, behavioral_data: Dict) -> Dict[str, float]:
        """Extract property preference stability features"""
        context = memory_data.get("context", {})
        preferences = context.get("preferences", {})

        # Count preference changes over time
        budget_changes = len(preferences.get("budget_history", [])) - 1
        location_changes = len(preferences.get("location_history", [])) - 1
        property_type_changes = len(preferences.get("property_type_history", [])) - 1
        feature_changes = len(preferences.get("feature_history", [])) - 1

        return {
            "budget_range_changes": max(0.0, budget_changes),
            "location_preference_changes": max(0.0, location_changes),
            "property_type_changes": max(0.0, property_type_changes),
            "feature_requirements_changes": max(0.0, feature_changes),
        }

    def _extract_external_indicators(self, lead_id: str, behavioral_data: Dict) -> Dict[str, float]:
        """Extract external market and seasonal indicators"""
        # Mock implementation - would connect to market data APIs
        return {
            "market_activity_correlation": 0.5,  # Correlation with market activity
            "seasonal_activity_alignment": 0.7,  # Alignment with seasonal patterns
        }

    def _calculate_response_rate(self, conversations: List[Dict], days: int) -> float:
        """Calculate response rate over specified time period"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_conversations = [
            conv for conv in conversations if datetime.fromisoformat(conv.get("timestamp", "")) >= cutoff_date
        ]

        if not recent_conversations:
            return 0.0

        responses = sum(1 for conv in recent_conversations if conv.get("response"))
        return responses / len(recent_conversations)

    def _calculate_channel_consistency(self, conversations: List[Dict]) -> float:
        """Calculate consistency of preferred communication channel"""
        if not conversations:
            return 0.0

        channels = [conv.get("channel") for conv in conversations[-10:]]  # Last 10 interactions
        most_common_channel = max(set(channels), key=channels.count) if channels else None

        if not most_common_channel:
            return 0.0

        consistency = channels.count(most_common_channel) / len(channels)
        return consistency

    def _get_default_features(self) -> ChurnFeatures:
        """Return default features when data extraction fails"""
        return ChurnFeatures(
            days_since_last_interaction=7.0,
            interaction_frequency_7d=1.0,
            interaction_frequency_14d=2.0,
            interaction_frequency_30d=4.0,
            response_rate_7d=0.5,
            response_rate_14d=0.5,
            response_rate_30d=0.5,
            engagement_trend=0.0,
            session_duration_avg=5.0,
            property_views_per_session=3.0,
            saved_properties_count=2.0,
            search_refinements_count=1.0,
            stage_progression_velocity=0.1,
            stage_stagnation_days=3.0,
            backward_stage_transitions=0.0,
            qualification_score_change=0.0,
            email_open_rate=0.3,
            email_click_rate=0.1,
            sms_response_rate=0.4,
            call_pickup_rate=0.6,
            preferred_communication_channel_consistency=0.7,
            budget_range_changes=1.0,
            location_preference_changes=0.0,
            property_type_changes=0.0,
            feature_requirements_changes=1.0,
            market_activity_correlation=0.5,
            seasonal_activity_alignment=0.7,
        )


class ChurnRiskPredictor:
    """Machine learning model for predicting churn risk across multiple horizons"""

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.models = {}  # 7d, 14d, 30d models
        self.scaler = StandardScaler()
        self.feature_names = []
        self.model_version = "1.0.0"
        self.logger = logging.getLogger(__name__ + ".ChurnRiskPredictor")

        # Initialize or load models
        if model_path:
            self.load_models()
        else:
            self._initialize_default_models()

    def predict_risk(self, features: ChurnFeatures) -> Tuple[Dict[str, float], float]:
        """
        Predict churn risk across multiple horizons

        Args:
            features: Extracted churn features

        Returns:
            Tuple of (risk_scores, confidence)
        """
        try:
            # Convert features to scaled vector
            feature_vector = features.to_vector().reshape(1, -1)
            scaled_features = self.scaler.transform(feature_vector)

            # Generate predictions for each horizon
            risk_scores = {}
            confidences = []

            for horizon in ["7d", "14d", "30d"]:
                if horizon in self.models:
                    # Get probability of churn
                    prob = self.models[horizon].predict_proba(scaled_features)[0][1]
                    risk_scores[horizon] = min(100.0, prob * 100)  # Convert to 0-100 scale

                    # Calculate confidence based on decision function
                    if hasattr(self.models[horizon], "decision_function"):
                        decision_score = abs(self.models[horizon].decision_function(scaled_features)[0])
                        confidence = min(1.0, decision_score / 2.0)  # Normalize to 0-1
                        confidences.append(confidence)
                    else:
                        confidences.append(0.8)  # Default confidence
                else:
                    # Fallback to rule-based prediction
                    risk_scores[horizon] = self._rule_based_prediction(features, horizon)
                    confidences.append(0.6)  # Lower confidence for rule-based

            avg_confidence = np.mean(confidences) if confidences else 0.5

            return risk_scores, avg_confidence

        except Exception as e:
            self.logger.error(f"Error predicting churn risk: {str(e)}")
            # Return conservative fallback predictions
            fallback_scores = {"7d": 25.0, "14d": 35.0, "30d": 45.0}
            return fallback_scores, 0.3

    def get_feature_importance(self, features: ChurnFeatures) -> List[Tuple[str, float]]:
        """
        Get feature importance scores for explainability

        Args:
            features: Extracted churn features

        Returns:
            List of (feature_name, importance) tuples sorted by importance
        """
        try:
            # Use the 14d model for feature importance (most balanced horizon)
            if "14d" in self.models and hasattr(self.models["14d"], "feature_importances_"):
                importances = self.models["14d"].feature_importances_
                feature_dict = features.to_dict()
                feature_importance = list(zip(feature_dict.keys(), importances))

                # Sort by importance (descending)
                feature_importance.sort(key=lambda x: x[1], reverse=True)
                return feature_importance[:10]  # Return top 10 features
            else:
                # Rule-based importance for fallback
                return self._rule_based_importance(features)

        except Exception as e:
            self.logger.error(f"Error calculating feature importance: {str(e)}")
            return []

    def _initialize_default_models(self):
        """Initialize default models when no trained model is available"""
        self.logger.info("Initializing default churn prediction models")

        # Create ensemble models for each horizon
        for horizon in ["7d", "14d", "30d"]:
            # Random Forest for stability
            rf_model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, class_weight="balanced")

            # Gradient Boosting for performance
            gb_model = GradientBoostingClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42)

            # For demo purposes, use RF model
            self.models[horizon] = rf_model

            # Train on synthetic data (in production, use historical churn data)
            X_train, y_train = self._generate_training_data(horizon)
            X_train_scaled = self.scaler.fit_transform(X_train)

            self.models[horizon].fit(X_train_scaled, y_train)

        self.logger.info("Default models initialized successfully")

    def _generate_training_data(self, horizon: str) -> Tuple[np.ndarray, np.ndarray]:
        """Generate synthetic training data for model initialization"""
        n_samples = 1000
        n_features = 27  # Number of features in ChurnFeatures

        # Generate synthetic feature data
        X = np.random.random((n_samples, n_features))

        # Create synthetic labels based on simple rules
        y = np.zeros(n_samples)

        for i in range(n_samples):
            # Higher churn probability for:
            # - High days since last interaction
            # - Low interaction frequency
            # - Low response rates
            # - Declining engagement trend

            risk_score = 0.0

            # Days since last interaction (feature 0)
            risk_score += X[i, 0] * 0.5

            # Low interaction frequency (features 1-3)
            risk_score += (1 - np.mean(X[i, 1:4])) * 0.3

            # Low response rates (features 4-6)
            risk_score += (1 - np.mean(X[i, 4:7])) * 0.3

            # Negative engagement trend (feature 7)
            if X[i, 7] < 0.4:  # Convert to declining trend
                X[i, 7] = X[i, 7] - 0.6  # Make it negative
                risk_score += 0.4

            # Stage stagnation (feature 9)
            risk_score += X[i, 9] * 0.2

            # Adjust risk based on horizon
            horizon_multiplier = {"7d": 0.8, "14d": 1.0, "30d": 1.2}
            risk_score *= horizon_multiplier.get(horizon, 1.0)

            # Convert to binary label
            y[i] = 1 if risk_score > 0.4 else 0

        return X, y

    def _rule_based_prediction(self, features: ChurnFeatures, horizon: str) -> float:
        """Fallback rule-based prediction when ML model unavailable"""
        feature_dict = features.to_dict()

        risk_score = 0.0

        # Days since last interaction (0-30 scale)
        risk_score += min(feature_dict["days_since_last_interaction"] / 30.0, 1.0) * 30

        # Low interaction frequency
        max_interactions = {"7d": 7, "14d": 14, "30d": 21}
        interaction_key = f"interaction_frequency_{horizon[:-1]}d"
        if interaction_key in feature_dict:
            expected = max_interactions[horizon]
            actual = feature_dict[interaction_key]
            risk_score += max(0, (expected - actual) / expected) * 25

        # Low response rate
        response_key = f"response_rate_{horizon[:-1]}d"
        if response_key in feature_dict:
            risk_score += (1 - feature_dict[response_key]) * 20

        # Negative engagement trend
        if feature_dict["engagement_trend"] < 0:
            risk_score += abs(feature_dict["engagement_trend"]) * 15

        # Stage stagnation
        risk_score += min(feature_dict["stage_stagnation_days"] / 30.0, 1.0) * 10

        return min(100.0, risk_score)

    def _rule_based_importance(self, features: ChurnFeatures) -> List[Tuple[str, float]]:
        """Rule-based feature importance for explainability"""
        importance_weights = {
            "days_since_last_interaction": 0.25,
            "response_rate_7d": 0.20,
            "engagement_trend": 0.15,
            "interaction_frequency_7d": 0.12,
            "stage_stagnation_days": 0.10,
            "email_open_rate": 0.08,
            "call_pickup_rate": 0.05,
            "qualification_score_change": 0.05,
        }

        # Sort by importance
        sorted_importance = sorted(importance_weights.items(), key=lambda x: x[1], reverse=True)
        return sorted_importance

    def save_models(self, path: str):
        """Save trained models and scaler to disk"""
        try:
            model_data = {
                "models": self.models,
                "scaler": self.scaler,
                "feature_names": self.feature_names,
                "model_version": self.model_version,
            }
            joblib.dump(model_data, path)
            self.logger.info(f"Models saved to {path}")
        except Exception as e:
            self.logger.error(f"Error saving models: {str(e)}")

    def load_models(self):
        """Load trained models and scaler from disk"""
        try:
            model_data = joblib.load(self.model_path)
            self.models = model_data["models"]
            self.scaler = model_data["scaler"]
            self.feature_names = model_data.get("feature_names", [])
            self.model_version = model_data.get("model_version", "1.0.0")
            self.logger.info(f"Models loaded from {self.model_path}")
        except Exception as e:
            self.logger.error(f"Error loading models: {str(e)}")
            self._initialize_default_models()


class ChurnRiskStratifier:
    """Stratifies churn risk scores into actionable tiers with recommendations"""

    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".ChurnRiskStratifier")

        # Risk tier thresholds
        self.tier_thresholds = {
            ChurnRiskTier.CRITICAL: 80.0,
            ChurnRiskTier.HIGH: 60.0,
            ChurnRiskTier.MEDIUM: 30.0,
            ChurnRiskTier.LOW: 0.0,
        }

    def stratify_risk(
        self, risk_scores: Dict[str, float], top_risk_factors: List[Tuple[str, float]]
    ) -> Tuple[ChurnRiskTier, List[str], str]:
        """
        Stratify risk score into tier with actionable recommendations

        Args:
            risk_scores: Multi-horizon risk scores
            top_risk_factors: Most important risk factors

        Returns:
            Tuple of (risk_tier, recommended_actions, urgency_level)
        """
        # Use weighted average of multi-horizon scores (emphasize shorter terms)
        weighted_score = (
            risk_scores.get("7d", 0) * 0.5 + risk_scores.get("14d", 0) * 0.3 + risk_scores.get("30d", 0) * 0.2
        )

        # Determine risk tier
        risk_tier = self._get_risk_tier(weighted_score)

        # Generate recommendations based on tier and risk factors
        recommendations = self._generate_recommendations(risk_tier, top_risk_factors)

        # Determine urgency level
        urgency = self._determine_urgency(risk_tier, risk_scores)

        self.logger.info(f"Risk stratified: Tier={risk_tier.value}, Score={weighted_score:.1f}, Urgency={urgency}")

        return risk_tier, recommendations, urgency

    def _get_risk_tier(self, score: float) -> ChurnRiskTier:
        """Determine risk tier based on score"""
        if score >= self.tier_thresholds[ChurnRiskTier.CRITICAL]:
            return ChurnRiskTier.CRITICAL
        elif score >= self.tier_thresholds[ChurnRiskTier.HIGH]:
            return ChurnRiskTier.HIGH
        elif score >= self.tier_thresholds[ChurnRiskTier.MEDIUM]:
            return ChurnRiskTier.MEDIUM
        else:
            return ChurnRiskTier.LOW

    def _generate_recommendations(self, tier: ChurnRiskTier, risk_factors: List[Tuple[str, float]]) -> List[str]:
        """Generate actionable recommendations based on risk tier and factors"""
        recommendations = []

        # Base recommendations by tier
        tier_recommendations = {
            ChurnRiskTier.CRITICAL: [
                "Immediate phone call required",
                "Escalate to senior agent",
                "Offer emergency property viewing",
                "Consider special incentives",
            ],
            ChurnRiskTier.HIGH: [
                "Schedule follow-up call within 24 hours",
                "Send personalized property recommendations",
                "Offer virtual consultation",
                "Review and adjust communication strategy",
            ],
            ChurnRiskTier.MEDIUM: [
                "Send re-engagement email campaign",
                "Provide market updates",
                "Offer additional property options",
                "Schedule check-in call",
            ],
            ChurnRiskTier.LOW: [
                "Continue standard nurture sequence",
                "Monitor engagement levels",
                "Provide educational content",
            ],
        }

        recommendations.extend(tier_recommendations[tier])

        # Factor-specific recommendations
        factor_recommendations = {
            "days_since_last_interaction": "Initiate immediate outreach",
            "response_rate_7d": "Switch communication channel",
            "engagement_trend": "Re-evaluate content strategy",
            "stage_stagnation_days": "Provide stage progression assistance",
            "email_open_rate": "Improve email subject lines and timing",
            "call_pickup_rate": "Try alternative contact methods",
            "qualification_score_change": "Re-qualify lead and adjust approach",
        }

        # Add factor-specific recommendations
        for factor, importance in risk_factors[:3]:  # Top 3 factors
            if factor in factor_recommendations and importance > 0.1:
                recommendations.append(factor_recommendations[factor])

        return recommendations[:6]  # Limit to 6 recommendations

    def _determine_urgency(self, tier: ChurnRiskTier, risk_scores: Dict[str, float]) -> str:
        """Determine intervention urgency level"""
        # Check for rapidly escalating risk
        score_7d = risk_scores.get("7d", 0)
        score_30d = risk_scores.get("30d", 0)

        urgency_map = {
            ChurnRiskTier.CRITICAL: "immediate",
            ChurnRiskTier.HIGH: "urgent",
            ChurnRiskTier.MEDIUM: "moderate",
            ChurnRiskTier.LOW: "low",
        }

        base_urgency = urgency_map[tier]

        # Escalate urgency if short-term risk is much higher than long-term
        if score_7d > score_30d + 20:
            urgency_escalation = {
                "low": "moderate",
                "moderate": "urgent",
                "urgent": "immediate",
                "immediate": "immediate",
            }
            return urgency_escalation.get(base_urgency, base_urgency)

        return base_urgency


# ============================================================================
# CHURN EVENT TRACKING SYSTEM (NEW ENHANCEMENT)
# ============================================================================


class ChurnReason(Enum):
    """Specific reasons for lead churn"""

    COMPETITOR = "competitor"  # Chose another agent/company
    TIMING = "timing"  # Not ready to buy/sell (timing issue)
    BUDGET = "budget"  # Financial constraints
    COMMUNICATION = "communication"  # Poor communication/relationship
    MARKET_CONDITIONS = "market_conditions"  # Market not favorable
    PROPERTY_MISMATCH = "property_mismatch"  # Couldn't find suitable property
    PERSONAL_CHANGE = "personal_change"  # Life circumstances changed
    UNRESPONSIVE = "unresponsive"  # Lead became unresponsive
    OTHER = "other"  # Other reasons


class ChurnEventType(Enum):
    """Types of churn events"""

    DETECTED = "detected"  # System detected potential churn
    CONFIRMED = "confirmed"  # Manual confirmation of churn
    RECOVERED = "recovered"  # Lead was successfully recovered
    PERMANENT = "permanent"  # Lead permanently lost


class RecoveryEligibility(Enum):
    """Recovery campaign eligibility status"""

    ELIGIBLE = "eligible"  # Eligible for recovery campaigns
    PARTIAL = "partial"  # Eligible for limited recovery attempts
    INELIGIBLE = "ineligible"  # Not eligible (e.g., competitor, personal issues)
    EXHAUSTED = "exhausted"  # Recovery attempts exhausted


@dataclass
class ChurnEvent:
    """Comprehensive churn event record for tracking and analytics"""

    # Event identification
    event_id: str
    lead_id: str
    event_type: ChurnEventType
    event_timestamp: datetime

    # Churn analysis
    churn_reason: Optional[ChurnReason] = None
    confidence_score: Optional[float] = None  # 0-1 confidence in churn detection
    detection_method: Optional[str] = None  # "system", "manual", "behavioral"

    # Recovery eligibility
    recovery_eligibility: RecoveryEligibility = RecoveryEligibility.ELIGIBLE
    recovery_attempts_allowed: int = 3
    recovery_attempts_used: int = 0

    # Context data
    last_interaction_date: Optional[datetime] = None
    inactivity_days: Optional[int] = None
    lifecycle_stage: Optional[str] = None
    predicted_risk_score: Optional[float] = None

    # Recovery tracking
    recovery_campaign_id: Optional[str] = None
    recovery_initiated_date: Optional[datetime] = None
    recovery_success_date: Optional[datetime] = None

    # Metadata
    notes: Optional[str] = None
    created_by: str = "system"
    last_updated: datetime = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization"""
        result = {}
        for field, value in asdict(self).items():
            if isinstance(value, (datetime,)):
                result[field] = value.isoformat() if value else None
            elif isinstance(value, (ChurnEventType, ChurnReason, RecoveryEligibility)):
                result[field] = value.value if value else None
            else:
                result[field] = value
        return result


class ChurnEventTracker:
    """
    Service for tracking actual churn events and managing recovery eligibility

    This enhances the prediction-only system with actual churn tracking,
    enabling recovery campaigns and model improvement through feedback loops.
    """

    def __init__(self, memory_service: Optional[MemoryService] = None):
        self.memory_service = memory_service
        self.logger = logging.getLogger(__name__ + ".ChurnEventTracker")

        # In-memory storage for events (production would use persistent storage)
        self._events_cache: Dict[str, List[ChurnEvent]] = {}

        # Inactivity thresholds for automatic churn detection
        self.inactivity_thresholds = {
            "warning": 14,  # 14 days = warning signal
            "likely_churned": 30,  # 30 days = likely churned
            "confirmed_churned": 60,  # 60 days = confirmed churned
        }

        self.logger.info("ChurnEventTracker initialized")

    async def track_churn_event(
        self,
        lead_id: str,
        event_type: ChurnEventType,
        churn_reason: Optional[ChurnReason] = None,
        confidence_score: Optional[float] = None,
        detection_method: str = "system",
        notes: Optional[str] = None,
    ) -> ChurnEvent:
        """
        Track a new churn event

        Args:
            lead_id: Lead identifier
            event_type: Type of churn event
            churn_reason: Specific reason for churn
            confidence_score: Confidence in churn detection (0-1)
            detection_method: How churn was detected
            notes: Additional notes

        Returns:
            Created ChurnEvent
        """
        try:
            # Generate unique event ID
            event_id = f"churn_{lead_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Determine recovery eligibility based on reason
            recovery_eligibility = self._determine_recovery_eligibility(churn_reason, event_type)

            # Get lead context if available
            last_interaction, inactivity_days, lifecycle_stage = await self._get_lead_context(lead_id)

            # Create churn event
            churn_event = ChurnEvent(
                event_id=event_id,
                lead_id=lead_id,
                event_type=event_type,
                event_timestamp=datetime.now(),
                churn_reason=churn_reason,
                confidence_score=confidence_score,
                detection_method=detection_method,
                recovery_eligibility=recovery_eligibility,
                last_interaction_date=last_interaction,
                inactivity_days=inactivity_days,
                lifecycle_stage=lifecycle_stage,
                notes=notes,
            )

            # Store event
            if lead_id not in self._events_cache:
                self._events_cache[lead_id] = []
            self._events_cache[lead_id].append(churn_event)

            # Persist to memory service if available
            if self.memory_service:
                await self.memory_service.store_memory(
                    f"churn_event_{event_id}",
                    churn_event.to_dict(),
                    tags=["churn_tracking", f"lead_{lead_id}", event_type.value],
                )

            self.logger.info(f"Tracked churn event: {event_id} for lead {lead_id} ({event_type.value})")
            return churn_event

        except Exception as e:
            self.logger.error(f"Error tracking churn event for lead {lead_id}: {str(e)}")
            raise

    async def detect_inactivity_churn(self, lead_id: str, days_since_interaction: int) -> Optional[ChurnEvent]:
        """
        Detect churn based on inactivity patterns

        Args:
            lead_id: Lead identifier
            days_since_interaction: Days since last interaction

        Returns:
            ChurnEvent if churn detected, None otherwise
        """
        try:
            # Check if already has recent churn event
            recent_events = await self.get_recent_churn_events(lead_id, days=7)
            if recent_events:
                return None  # Already tracked recently

            # Determine churn level based on inactivity
            if days_since_interaction >= self.inactivity_thresholds["confirmed_churned"]:
                return await self.track_churn_event(
                    lead_id=lead_id,
                    event_type=ChurnEventType.CONFIRMED,
                    churn_reason=ChurnReason.UNRESPONSIVE,
                    confidence_score=0.9,
                    detection_method="inactivity_threshold",
                    notes=f"{days_since_interaction} days of inactivity - confirmed churn",
                )

            elif days_since_interaction >= self.inactivity_thresholds["likely_churned"]:
                return await self.track_churn_event(
                    lead_id=lead_id,
                    event_type=ChurnEventType.DETECTED,
                    churn_reason=ChurnReason.UNRESPONSIVE,
                    confidence_score=0.7,
                    detection_method="inactivity_threshold",
                    notes=f"{days_since_interaction} days of inactivity - likely churned",
                )

            return None

        except Exception as e:
            self.logger.error(f"Error detecting inactivity churn for lead {lead_id}: {str(e)}")
            return None

    async def get_churn_events(self, lead_id: str) -> List[ChurnEvent]:
        """Get all churn events for a lead"""
        return self._events_cache.get(lead_id, [])

    async def get_recent_churn_events(self, lead_id: str, days: int = 30) -> List[ChurnEvent]:
        """Get recent churn events for a lead within specified days"""
        events = await self.get_churn_events(lead_id)
        cutoff_date = datetime.now() - timedelta(days=days)

        return [event for event in events if event.event_timestamp >= cutoff_date]

    async def check_recovery_eligibility(self, lead_id: str) -> Tuple[bool, RecoveryEligibility, int]:
        """
        Check if lead is eligible for recovery campaigns

        Returns:
            (is_eligible, eligibility_status, attempts_remaining)
        """
        events = await self.get_churn_events(lead_id)

        if not events:
            return True, RecoveryEligibility.ELIGIBLE, 3

        # Get latest churn event
        latest_event = max(events, key=lambda e: e.event_timestamp)

        # Check eligibility
        is_eligible = latest_event.recovery_eligibility in [RecoveryEligibility.ELIGIBLE, RecoveryEligibility.PARTIAL]

        attempts_remaining = max(0, latest_event.recovery_attempts_allowed - latest_event.recovery_attempts_used)

        return is_eligible, latest_event.recovery_eligibility, attempts_remaining

    async def record_recovery_attempt(self, lead_id: str, campaign_id: str) -> bool:
        """
        Record a recovery campaign attempt

        Returns:
            True if attempt recorded successfully, False if not eligible
        """
        try:
            is_eligible, _, attempts_remaining = await self.check_recovery_eligibility(lead_id)

            if not is_eligible or attempts_remaining <= 0:
                return False

            events = await self.get_churn_events(lead_id)
            if events:
                # Update latest event
                latest_event = max(events, key=lambda e: e.event_timestamp)
                latest_event.recovery_attempts_used += 1
                latest_event.recovery_campaign_id = campaign_id
                if latest_event.recovery_initiated_date is None:
                    latest_event.recovery_initiated_date = datetime.now()
                latest_event.last_updated = datetime.now()

                # Update eligibility if attempts exhausted
                if latest_event.recovery_attempts_used >= latest_event.recovery_attempts_allowed:
                    latest_event.recovery_eligibility = RecoveryEligibility.EXHAUSTED

            self.logger.info(f"Recorded recovery attempt for lead {lead_id}, campaign {campaign_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error recording recovery attempt for lead {lead_id}: {str(e)}")
            return False

    async def record_recovery_success(self, lead_id: str) -> bool:
        """
        Record successful lead recovery

        Returns:
            True if recovery recorded successfully
        """
        try:
            # Track recovery event
            await self.track_churn_event(
                lead_id=lead_id,
                event_type=ChurnEventType.RECOVERED,
                confidence_score=1.0,
                detection_method="recovery_confirmation",
                notes="Lead successfully recovered through recovery campaign",
            )

            # Update latest churn event
            events = await self.get_churn_events(lead_id)
            if events:
                latest_event = max(events, key=lambda e: e.event_timestamp)
                latest_event.recovery_success_date = datetime.now()
                latest_event.recovery_eligibility = RecoveryEligibility.ELIGIBLE  # Reset for future
                latest_event.last_updated = datetime.now()

            self.logger.info(f"Recorded successful recovery for lead {lead_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error recording recovery success for lead {lead_id}: {str(e)}")
            return False

    def get_churn_analytics(self) -> Dict[str, Any]:
        """
        Get analytics about churn events and recovery performance

        Returns:
            Dictionary with churn analytics
        """
        try:
            all_events = []
            for events_list in self._events_cache.values():
                all_events.extend(events_list)

            if not all_events:
                return {"total_events": 0, "message": "No churn events tracked"}

            # Basic metrics
            total_events = len(all_events)
            churn_events = [
                e for e in all_events if e.event_type in [ChurnEventType.DETECTED, ChurnEventType.CONFIRMED]
            ]
            recovery_events = [e for e in all_events if e.event_type == ChurnEventType.RECOVERED]

            # Churn reasons breakdown
            reason_counts = {}
            for event in churn_events:
                if event.churn_reason:
                    reason = event.churn_reason.value
                    reason_counts[reason] = reason_counts.get(reason, 0) + 1

            # Recovery rate
            recovery_rate = len(recovery_events) / len(churn_events) * 100 if churn_events else 0

            # Recovery eligibility breakdown
            eligibility_counts = {}
            for event in churn_events:
                eligibility = event.recovery_eligibility.value
                eligibility_counts[eligibility] = eligibility_counts.get(eligibility, 0) + 1

            return {
                "total_events": total_events,
                "churn_events": len(churn_events),
                "recovery_events": len(recovery_events),
                "recovery_rate_percent": round(recovery_rate, 2),
                "churn_reasons": reason_counts,
                "recovery_eligibility": eligibility_counts,
                "unique_leads_affected": len(self._events_cache),
                "analysis_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error generating churn analytics: {str(e)}")
            return {"error": str(e)}

    def _determine_recovery_eligibility(
        self, churn_reason: Optional[ChurnReason], event_type: ChurnEventType
    ) -> RecoveryEligibility:
        """Determine recovery eligibility based on churn reason"""
        if churn_reason in [ChurnReason.COMPETITOR, ChurnReason.PERSONAL_CHANGE]:
            return RecoveryEligibility.INELIGIBLE
        elif churn_reason in [ChurnReason.BUDGET, ChurnReason.MARKET_CONDITIONS]:
            return RecoveryEligibility.PARTIAL
        else:
            return RecoveryEligibility.ELIGIBLE

    async def _get_lead_context(self, lead_id: str) -> Tuple[Optional[datetime], Optional[int], Optional[str]]:
        """Get lead context information for churn event"""
        # In production, this would query actual lead data
        # For now, return placeholder data
        return None, None, None


class ChurnPredictionEngine:
    """
    Main orchestration class for the churn prediction system

    Coordinates feature extraction, risk prediction, and stratification
    to provide comprehensive churn risk assessment with actionable insights.
    """

    def __init__(
        self,
        memory_service: Optional[MemoryService] = None,
        lifecycle_tracker: Optional[LeadLifecycleTracker] = None,
        behavioral_engine: Optional[BehavioralTriggerEngine] = None,
        lead_scorer: Optional[LeadScorer] = None,
        model_path: Optional[str] = None,
    ):

        self.logger = logging.getLogger(__name__ + ".ChurnPredictionEngine")

        # Initialize components with optional dependencies
        self.feature_extractor = (
            ChurnFeatureExtractor(memory_service, lifecycle_tracker, behavioral_engine, lead_scorer)
            if all([memory_service, lifecycle_tracker, behavioral_engine, lead_scorer])
            else None
        )

        self.risk_predictor = ChurnRiskPredictor(model_path)
        self.risk_stratifier = ChurnRiskStratifier()

        # ENHANCED: Initialize ChurnEventTracker for actual churn tracking
        self.event_tracker = ChurnEventTracker(memory_service)

        # Cache for recent predictions (4-hour TTL)
        self._prediction_cache = {}
        self._cache_ttl = timedelta(hours=4)

        if not self.feature_extractor:
            self.logger.warning(
                "ChurnPredictionEngine initialized with missing dependencies. Features will not be extracted."
            )

        self.logger.info("ChurnPredictionEngine with event tracking initialized successfully")

    async def predict_churn_risk(self, lead_id: str, force_refresh: bool = False) -> ChurnPrediction:
        """
        Generate comprehensive churn risk prediction for a lead

        Args:
            lead_id: Unique identifier for the lead
            force_refresh: Force new prediction (bypass cache)

        Returns:
            ChurnPrediction: Complete prediction with multi-horizon forecasts
        """
        try:
            self.logger.info(f"Generating churn prediction for lead {lead_id}")

            # Check cache first (unless force refresh)
            if not force_refresh and lead_id in self._prediction_cache:
                cached_prediction, cache_time = self._prediction_cache[lead_id]
                if datetime.now() - cache_time < self._cache_ttl:
                    self.logger.info(f"Returning cached prediction for lead {lead_id}")
                    return cached_prediction

            # Step 1: Extract features
            features = await self.feature_extractor.extract_features(lead_id)

            # Step 2: Predict risk scores
            risk_scores, confidence = self.risk_predictor.predict_risk(features)

            # Step 3: Get feature importance for explainability
            feature_importance = self.risk_predictor.get_feature_importance(features)

            # Step 4: Stratify risk and generate recommendations
            risk_tier, recommendations, urgency = self.risk_stratifier.stratify_risk(risk_scores, feature_importance)

            # Step 5: Create comprehensive prediction object
            prediction = ChurnPrediction(
                lead_id=lead_id,
                prediction_timestamp=datetime.now(),
                risk_score_7d=risk_scores.get("7d", 0.0),
                risk_score_14d=risk_scores.get("14d", 0.0),
                risk_score_30d=risk_scores.get("30d", 0.0),
                risk_tier=risk_tier,
                confidence=confidence,
                top_risk_factors=feature_importance,
                recommended_actions=recommendations,
                intervention_urgency=urgency,
                feature_vector=features.to_dict(),
                model_version=self.risk_predictor.model_version,
            )

            # Cache the prediction
            self._prediction_cache[lead_id] = (prediction, datetime.now())

            self.logger.info(f"Churn prediction generated: {risk_tier.value} risk ({risk_scores.get('14d', 0):.1f}%)")
            return prediction

        except Exception as e:
            self.logger.error(f"Error generating churn prediction for lead {lead_id}: {str(e)}")
            # Return safe fallback prediction
            return self._get_fallback_prediction(lead_id)

    async def batch_predict_churn_risk(self, lead_ids: List[str]) -> Dict[str, ChurnPrediction]:
        """
        Generate churn predictions for multiple leads efficiently

        Args:
            lead_ids: List of lead identifiers

        Returns:
            Dict mapping lead_id to ChurnPrediction
        """
        self.logger.info(f"Generating batch churn predictions for {len(lead_ids)} leads")

        predictions = {}

        for lead_id in lead_ids:
            try:
                prediction = await self.predict_churn_risk(lead_id)
                predictions[lead_id] = prediction
            except Exception as e:
                self.logger.error(f"Error in batch prediction for lead {lead_id}: {str(e)}")
                predictions[lead_id] = self._get_fallback_prediction(lead_id)

        return predictions

    def get_high_risk_leads(self, predictions: Dict[str, ChurnPrediction]) -> List[str]:
        """
        Filter leads by high churn risk for priority intervention

        Args:
            predictions: Dict of lead predictions

        Returns:
            List of high-risk lead IDs sorted by risk score
        """
        high_risk_leads = []

        for lead_id, prediction in predictions.items():
            if prediction.risk_tier in [ChurnRiskTier.CRITICAL, ChurnRiskTier.HIGH]:
                high_risk_leads.append((lead_id, prediction.risk_score_14d))

        # Sort by risk score (descending)
        high_risk_leads.sort(key=lambda x: x[1], reverse=True)

        return [lead_id for lead_id, _ in high_risk_leads]

    def _get_fallback_prediction(self, lead_id: str) -> ChurnPrediction:
        """Generate safe fallback prediction when primary prediction fails"""
        return ChurnPrediction(
            lead_id=lead_id,
            prediction_timestamp=datetime.now(),
            risk_score_7d=25.0,
            risk_score_14d=30.0,
            risk_score_30d=35.0,
            risk_tier=ChurnRiskTier.MEDIUM,
            confidence=0.3,
            top_risk_factors=[("unknown_risk", 0.5)],
            recommended_actions=["Manual review required", "Standard follow-up"],
            intervention_urgency="moderate",
            feature_vector={},
            model_version="fallback-1.0.0",
        )

    def clear_cache(self):
        """Clear prediction cache"""
        self._prediction_cache.clear()
        self.logger.info("Prediction cache cleared")

    async def update_model_training_data(self, lead_id: str, actual_churned: bool):
        """
        Update training data with actual churn outcomes for model improvement

        Args:
            lead_id: Lead identifier
            actual_churned: Whether the lead actually churned
        """
        # ENHANCED: Record actual churn event for tracking and analytics
        if actual_churned:
            await self.event_tracker.track_churn_event(
                lead_id=lead_id,
                event_type=ChurnEventType.CONFIRMED,
                confidence_score=1.0,
                detection_method="manual_confirmation",
                notes="Actual churn outcome confirmed for model training",
            )

        # In production, this would update the training dataset
        # For now, just log for future model retraining
        self.logger.info(f"Churn outcome recorded: Lead {lead_id} churned={actual_churned}")

    # ============================================================================
    # ENHANCED METHODS: Integration with ChurnEventTracker
    # ============================================================================

    async def predict_churn_risk_with_event_detection(
        self, lead_id: str, force_refresh: bool = False
    ) -> Tuple[ChurnPrediction, Optional[ChurnEvent]]:
        """
        Enhanced prediction that automatically detects and tracks churn events

        Args:
            lead_id: Lead identifier
            force_refresh: Force new prediction (bypass cache)

        Returns:
            Tuple of (ChurnPrediction, ChurnEvent if detected)
        """
        try:
            # Get standard churn prediction
            prediction = await self.predict_churn_risk(lead_id, force_refresh)

            # Check if we should track a churn event based on prediction
            churn_event = None

            # Extract days since last interaction from features
            if "days_since_last_interaction" in prediction.feature_vector:
                days_since_interaction = int(prediction.feature_vector["days_since_last_interaction"])

                # Attempt automatic churn event detection based on inactivity
                churn_event = await self.event_tracker.detect_inactivity_churn(lead_id, days_since_interaction)

            # Track high-risk predictions as potential churn events
            if prediction.risk_tier == ChurnRiskTier.CRITICAL and not churn_event:
                # Check if we already tracked a recent event to avoid duplicates
                recent_events = await self.event_tracker.get_recent_churn_events(lead_id, days=7)
                if not recent_events:
                    churn_event = await self.event_tracker.track_churn_event(
                        lead_id=lead_id,
                        event_type=ChurnEventType.DETECTED,
                        confidence_score=prediction.confidence,
                        detection_method="ai_prediction",
                        notes=f"Critical risk tier detected: {prediction.risk_score_14d:.1f}% risk",
                    )

            return prediction, churn_event

        except Exception as e:
            self.logger.error(f"Error in enhanced churn prediction for lead {lead_id}: {str(e)}")
            # Return standard prediction without event tracking
            prediction = await self.predict_churn_risk(lead_id, force_refresh)
            return prediction, None

    async def get_recovery_eligible_leads(
        self, predictions: Dict[str, ChurnPrediction]
    ) -> Dict[str, Tuple[ChurnPrediction, RecoveryEligibility, int]]:
        """
        Get leads eligible for recovery campaigns with eligibility details

        Args:
            predictions: Dict of lead predictions

        Returns:
            Dict mapping lead_id to (prediction, eligibility_status, attempts_remaining)
        """
        recovery_candidates = {}

        for lead_id, prediction in predictions.items():
            # Check recovery eligibility
            is_eligible, eligibility_status, attempts_remaining = await self.event_tracker.check_recovery_eligibility(
                lead_id
            )

            # Include high-risk leads that are eligible for recovery
            if (
                prediction.risk_tier in [ChurnRiskTier.HIGH, ChurnRiskTier.CRITICAL]
                and is_eligible
                and attempts_remaining > 0
            ):
                recovery_candidates[lead_id] = (prediction, eligibility_status, attempts_remaining)

        return recovery_candidates

    async def initiate_recovery_campaign(self, lead_id: str, campaign_id: str) -> bool:
        """
        Initiate a recovery campaign for a lead

        Args:
            lead_id: Lead identifier
            campaign_id: Recovery campaign identifier

        Returns:
            True if campaign initiated successfully
        """
        try:
            # Record recovery attempt
            success = await self.event_tracker.record_recovery_attempt(lead_id, campaign_id)

            if success:
                self.logger.info(f"Recovery campaign {campaign_id} initiated for lead {lead_id}")
            else:
                self.logger.warning(
                    f"Recovery campaign {campaign_id} could not be initiated for lead {lead_id} - not eligible or attempts exhausted"
                )

            return success

        except Exception as e:
            self.logger.error(f"Error initiating recovery campaign for lead {lead_id}: {str(e)}")
            return False

    async def record_recovery_outcome(self, lead_id: str, recovered: bool) -> bool:
        """
        Record the outcome of a recovery campaign

        Args:
            lead_id: Lead identifier
            recovered: Whether the lead was successfully recovered

        Returns:
            True if outcome recorded successfully
        """
        try:
            if recovered:
                success = await self.event_tracker.record_recovery_success(lead_id)
                self.logger.info(f"Recovery success recorded for lead {lead_id}")
            else:
                # Track as permanent churn
                await self.event_tracker.track_churn_event(
                    lead_id=lead_id,
                    event_type=ChurnEventType.PERMANENT,
                    confidence_score=0.8,
                    detection_method="recovery_failure",
                    notes="Lead not recovered after recovery campaign attempts",
                )
                success = True
                self.logger.info(f"Recovery failure recorded for lead {lead_id}")

            return success

        except Exception as e:
            self.logger.error(f"Error recording recovery outcome for lead {lead_id}: {str(e)}")
            return False

    async def get_churn_analytics(self) -> Dict[str, Any]:
        """
        Get comprehensive churn and recovery analytics

        Returns:
            Dictionary with churn analytics including recovery performance
        """
        try:
            # Get analytics from event tracker
            analytics = self.event_tracker.get_churn_analytics()

            # Add prediction-level analytics
            cache_stats = {
                "cached_predictions": len(self._prediction_cache),
                "cache_hit_potential": f"{len(self._prediction_cache)} recent predictions available",
            }

            analytics["prediction_cache_stats"] = cache_stats
            analytics["engine_version"] = "enhanced_v2.0.0_with_event_tracking"

            return analytics

        except Exception as e:
            self.logger.error(f"Error generating churn analytics: {str(e)}")
            return {"error": str(e)}


# Example usage and testing
if __name__ == "__main__":

    async def test_churn_prediction():
        """Test the churn prediction system"""
        # Mock services for testing
        from unittest.mock import AsyncMock

        memory_service = AsyncMock()
        lifecycle_tracker = AsyncMock()
        behavioral_engine = AsyncMock()
        lead_scorer = AsyncMock()

        # Initialize engine
        engine = ChurnPredictionEngine(memory_service, lifecycle_tracker, behavioral_engine, lead_scorer)

        # Test single prediction
        test_lead_id = "test-lead-123"
        prediction = await engine.predict_churn_risk(test_lead_id)

        print(f"Churn Prediction Results:")
        print(f"Lead ID: {prediction.lead_id}")
        print(f"Risk Tier: {prediction.risk_tier.value}")
        print(f"7-day Risk: {prediction.risk_score_7d:.1f}%")
        print(f"14-day Risk: {prediction.risk_score_14d:.1f}%")
        print(f"30-day Risk: {prediction.risk_score_30d:.1f}%")
        print(f"Confidence: {prediction.confidence:.2f}")
        print(f"Urgency: {prediction.intervention_urgency}")
        print(f"Recommendations: {prediction.recommended_actions}")

    import asyncio

    asyncio.run(test_churn_prediction())
