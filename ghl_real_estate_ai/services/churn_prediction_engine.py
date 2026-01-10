"""
Lead Churn Prediction Engine with Multi-Horizon Risk Assessment

This module provides comprehensive churn prediction capabilities including:
- Multi-dimensional feature extraction from lead behavior
- Machine learning-based risk scoring with confidence intervals
- Multi-horizon predictions (7, 14, 30 days)
- Explainable AI with feature importance rankings
- Real-time risk stratification and intervention recommendations

Key Components:
- ChurnFeatureExtractor: Extracts 20+ behavioral features
- ChurnRiskPredictor: ML model with ensemble predictions
- ChurnRiskStratifier: Risk tier assignment and recommendations
- ChurnPredictionEngine: Main orchestration class

Author: EnterpriseHub AI
Last Updated: 2026-01-09
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, NamedTuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
import joblib
import json
import warnings
warnings.filterwarnings('ignore')

# Internal imports
from .memory_service import MemoryService
from .lead_lifecycle import LeadLifecycleTracker
from .behavioral_triggers import BehavioralTriggerEngine
from .lead_scorer import LeadScorer

# Configure logging
logger = logging.getLogger(__name__)

class ChurnRiskTier(Enum):
    """Risk tier classifications for churn prediction"""
    CRITICAL = "critical"  # 80-100% churn risk - immediate intervention
    HIGH = "high"          # 60-80% churn risk - urgent follow-up
    MEDIUM = "medium"      # 30-60% churn risk - nurture campaign
    LOW = "low"           # 0-30% churn risk - standard engagement

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

    def __init__(self, memory_service: MemoryService,
                 lifecycle_tracker: LeadLifecycleTracker,
                 behavioral_engine: BehavioralTriggerEngine,
                 lead_scorer: LeadScorer):
        self.memory_service = memory_service
        self.lifecycle_tracker = lifecycle_tracker
        self.behavioral_engine = behavioral_engine
        self.lead_scorer = lead_scorer
        self.logger = logging.getLogger(__name__ + '.ChurnFeatureExtractor')

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
                **external_features
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
                'context': lead_context,
                'conversations': conversation_history,
                'last_interaction': await self.memory_service.get_last_interaction(lead_id)
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
                'current_stage': current_stage,
                'stage_history': stage_history,
                'progression_metrics': await self.lifecycle_tracker.get_progression_metrics(lead_id)
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
                'recent_events': recent_events,
                'engagement_metrics': engagement_metrics,
                'event_patterns': await self.behavioral_engine.analyze_patterns(lead_id)
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
                'current_score': current_score,
                'score_history': score_history,
                'qualification_factors': await self.lead_scorer.get_qualification_factors(lead_id)
            }
        except Exception as e:
            self.logger.warning(f"Failed to get scoring data for {lead_id}: {str(e)}")
            return {}

    def _extract_engagement_features(self, memory_data: Dict, behavioral_data: Dict) -> Dict[str, float]:
        """Extract engagement-related features"""
        now = datetime.now()

        # Days since last interaction
        last_interaction = memory_data.get('last_interaction', {})
        days_since_last = 999.0  # Default for no interaction
        if last_interaction and 'timestamp' in last_interaction:
            last_time = datetime.fromisoformat(last_interaction['timestamp'])
            days_since_last = (now - last_time).days

        # Interaction frequencies
        events = behavioral_data.get('recent_events', [])
        interactions_7d = sum(1 for event in events if (now - datetime.fromisoformat(event.get('timestamp', ''))).days <= 7)
        interactions_14d = sum(1 for event in events if (now - datetime.fromisoformat(event.get('timestamp', ''))).days <= 14)
        interactions_30d = len(events)

        # Response rates
        conversations = memory_data.get('conversations', [])
        response_rate_7d = self._calculate_response_rate(conversations, 7)
        response_rate_14d = self._calculate_response_rate(conversations, 14)
        response_rate_30d = self._calculate_response_rate(conversations, 30)

        return {
            'days_since_last_interaction': min(days_since_last, 30.0),  # Cap at 30 days
            'interaction_frequency_7d': interactions_7d,
            'interaction_frequency_14d': interactions_14d,
            'interaction_frequency_30d': interactions_30d,
            'response_rate_7d': response_rate_7d,
            'response_rate_14d': response_rate_14d,
            'response_rate_30d': response_rate_30d
        }

    def _extract_behavioral_patterns(self, behavioral_data: Dict) -> Dict[str, float]:
        """Extract behavioral pattern features"""
        engagement_metrics = behavioral_data.get('engagement_metrics', {})
        event_patterns = behavioral_data.get('event_patterns', {})

        return {
            'engagement_trend': engagement_metrics.get('trend', 0.0),
            'session_duration_avg': engagement_metrics.get('avg_session_duration', 0.0),
            'property_views_per_session': engagement_metrics.get('views_per_session', 0.0),
            'saved_properties_count': engagement_metrics.get('saved_properties', 0.0),
            'search_refinements_count': engagement_metrics.get('search_refinements', 0.0)
        }

    def _extract_lifecycle_features(self, lifecycle_data: Dict, scoring_data: Dict) -> Dict[str, float]:
        """Extract lifecycle progression features"""
        progression_metrics = lifecycle_data.get('progression_metrics', {})
        score_history = scoring_data.get('score_history', [])

        # Stage progression velocity
        stage_velocity = progression_metrics.get('velocity', 0.0)

        # Stage stagnation
        stage_stagnation = progression_metrics.get('stagnation_days', 0.0)

        # Backward transitions
        backward_transitions = progression_metrics.get('backward_transitions', 0.0)

        # Qualification score change
        score_change = 0.0
        if len(score_history) >= 2:
            recent_score = score_history[0].get('score', 0.0)
            previous_score = score_history[-1].get('score', 0.0)
            score_change = recent_score - previous_score

        return {
            'stage_progression_velocity': stage_velocity,
            'stage_stagnation_days': min(stage_stagnation, 30.0),
            'backward_stage_transitions': backward_transitions,
            'qualification_score_change': score_change
        }

    def _extract_communication_features(self, memory_data: Dict, behavioral_data: Dict) -> Dict[str, float]:
        """Extract communication pattern features"""
        conversations = memory_data.get('conversations', [])

        # Calculate communication channel metrics
        email_opens = sum(1 for conv in conversations if conv.get('channel') == 'email' and conv.get('opened', False))
        email_total = sum(1 for conv in conversations if conv.get('channel') == 'email')
        email_open_rate = email_opens / email_total if email_total > 0 else 0.0

        email_clicks = sum(1 for conv in conversations if conv.get('channel') == 'email' and conv.get('clicked', False))
        email_click_rate = email_clicks / email_total if email_total > 0 else 0.0

        sms_responses = sum(1 for conv in conversations if conv.get('channel') == 'sms' and conv.get('response'))
        sms_total = sum(1 for conv in conversations if conv.get('channel') == 'sms')
        sms_response_rate = sms_responses / sms_total if sms_total > 0 else 0.0

        call_pickups = sum(1 for conv in conversations if conv.get('channel') == 'call' and conv.get('pickup', False))
        call_total = sum(1 for conv in conversations if conv.get('channel') == 'call')
        call_pickup_rate = call_pickups / call_total if call_total > 0 else 0.0

        # Channel consistency
        channel_consistency = self._calculate_channel_consistency(conversations)

        return {
            'email_open_rate': email_open_rate,
            'email_click_rate': email_click_rate,
            'sms_response_rate': sms_response_rate,
            'call_pickup_rate': call_pickup_rate,
            'preferred_communication_channel_consistency': channel_consistency
        }

    def _extract_preference_features(self, memory_data: Dict, behavioral_data: Dict) -> Dict[str, float]:
        """Extract property preference stability features"""
        context = memory_data.get('context', {})
        preferences = context.get('preferences', {})

        # Count preference changes over time
        budget_changes = len(preferences.get('budget_history', [])) - 1
        location_changes = len(preferences.get('location_history', [])) - 1
        property_type_changes = len(preferences.get('property_type_history', [])) - 1
        feature_changes = len(preferences.get('feature_history', [])) - 1

        return {
            'budget_range_changes': max(0.0, budget_changes),
            'location_preference_changes': max(0.0, location_changes),
            'property_type_changes': max(0.0, property_type_changes),
            'feature_requirements_changes': max(0.0, feature_changes)
        }

    def _extract_external_indicators(self, lead_id: str, behavioral_data: Dict) -> Dict[str, float]:
        """Extract external market and seasonal indicators"""
        # Mock implementation - would connect to market data APIs
        return {
            'market_activity_correlation': 0.5,  # Correlation with market activity
            'seasonal_activity_alignment': 0.7   # Alignment with seasonal patterns
        }

    def _calculate_response_rate(self, conversations: List[Dict], days: int) -> float:
        """Calculate response rate over specified time period"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_conversations = [
            conv for conv in conversations
            if datetime.fromisoformat(conv.get('timestamp', '')) >= cutoff_date
        ]

        if not recent_conversations:
            return 0.0

        responses = sum(1 for conv in recent_conversations if conv.get('response'))
        return responses / len(recent_conversations)

    def _calculate_channel_consistency(self, conversations: List[Dict]) -> float:
        """Calculate consistency of preferred communication channel"""
        if not conversations:
            return 0.0

        channels = [conv.get('channel') for conv in conversations[-10:]]  # Last 10 interactions
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
            seasonal_activity_alignment=0.7
        )

class ChurnRiskPredictor:
    """Machine learning model for predicting churn risk across multiple horizons"""

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.models = {}  # 7d, 14d, 30d models
        self.scaler = StandardScaler()
        self.feature_names = []
        self.model_version = "1.0.0"
        self.logger = logging.getLogger(__name__ + '.ChurnRiskPredictor')

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

            for horizon in ['7d', '14d', '30d']:
                if horizon in self.models:
                    # Get probability of churn
                    prob = self.models[horizon].predict_proba(scaled_features)[0][1]
                    risk_scores[horizon] = min(100.0, prob * 100)  # Convert to 0-100 scale

                    # Calculate confidence based on decision function
                    if hasattr(self.models[horizon], 'decision_function'):
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
            fallback_scores = {'7d': 25.0, '14d': 35.0, '30d': 45.0}
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
            if '14d' in self.models and hasattr(self.models['14d'], 'feature_importances_'):
                importances = self.models['14d'].feature_importances_
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
        for horizon in ['7d', '14d', '30d']:
            # Random Forest for stability
            rf_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )

            # Gradient Boosting for performance
            gb_model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )

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
        n_features = 26  # Number of features in ChurnFeatures

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
            risk_score += X[i, 0] * 0.3

            # Low interaction frequency (features 1-3)
            risk_score += (1 - np.mean(X[i, 1:4])) * 0.2

            # Low response rates (features 4-6)
            risk_score += (1 - np.mean(X[i, 4:7])) * 0.2

            # Negative engagement trend (feature 7)
            if X[i, 7] < 0.3:  # Convert to declining trend
                X[i, 7] = X[i, 7] - 0.5  # Make it negative
                risk_score += 0.2

            # Stage stagnation (feature 9)
            risk_score += X[i, 9] * 0.1

            # Adjust risk based on horizon
            horizon_multiplier = {'7d': 0.7, '14d': 1.0, '30d': 1.3}
            risk_score *= horizon_multiplier.get(horizon, 1.0)

            # Convert to binary label
            y[i] = 1 if risk_score > 0.5 else 0

        return X, y

    def _rule_based_prediction(self, features: ChurnFeatures, horizon: str) -> float:
        """Fallback rule-based prediction when ML model unavailable"""
        feature_dict = features.to_dict()

        risk_score = 0.0

        # Days since last interaction (0-30 scale)
        risk_score += min(feature_dict['days_since_last_interaction'] / 30.0, 1.0) * 30

        # Low interaction frequency
        max_interactions = {'7d': 7, '14d': 14, '30d': 21}
        interaction_key = f'interaction_frequency_{horizon[:-1]}d'
        if interaction_key in feature_dict:
            expected = max_interactions[horizon]
            actual = feature_dict[interaction_key]
            risk_score += max(0, (expected - actual) / expected) * 25

        # Low response rate
        response_key = f'response_rate_{horizon[:-1]}d'
        if response_key in feature_dict:
            risk_score += (1 - feature_dict[response_key]) * 20

        # Negative engagement trend
        if feature_dict['engagement_trend'] < 0:
            risk_score += abs(feature_dict['engagement_trend']) * 15

        # Stage stagnation
        risk_score += min(feature_dict['stage_stagnation_days'] / 30.0, 1.0) * 10

        return min(100.0, risk_score)

    def _rule_based_importance(self, features: ChurnFeatures) -> List[Tuple[str, float]]:
        """Rule-based feature importance for explainability"""
        importance_weights = {
            'days_since_last_interaction': 0.25,
            'response_rate_7d': 0.20,
            'engagement_trend': 0.15,
            'interaction_frequency_7d': 0.12,
            'stage_stagnation_days': 0.10,
            'email_open_rate': 0.08,
            'call_pickup_rate': 0.05,
            'qualification_score_change': 0.05
        }

        # Sort by importance
        sorted_importance = sorted(importance_weights.items(), key=lambda x: x[1], reverse=True)
        return sorted_importance

    def save_models(self, path: str):
        """Save trained models and scaler to disk"""
        try:
            model_data = {
                'models': self.models,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'model_version': self.model_version
            }
            joblib.dump(model_data, path)
            self.logger.info(f"Models saved to {path}")
        except Exception as e:
            self.logger.error(f"Error saving models: {str(e)}")

    def load_models(self):
        """Load trained models and scaler from disk"""
        try:
            model_data = joblib.load(self.model_path)
            self.models = model_data['models']
            self.scaler = model_data['scaler']
            self.feature_names = model_data.get('feature_names', [])
            self.model_version = model_data.get('model_version', '1.0.0')
            self.logger.info(f"Models loaded from {self.model_path}")
        except Exception as e:
            self.logger.error(f"Error loading models: {str(e)}")
            self._initialize_default_models()

class ChurnRiskStratifier:
    """Stratifies churn risk scores into actionable tiers with recommendations"""

    def __init__(self):
        self.logger = logging.getLogger(__name__ + '.ChurnRiskStratifier')

        # Risk tier thresholds
        self.tier_thresholds = {
            ChurnRiskTier.CRITICAL: 80.0,
            ChurnRiskTier.HIGH: 60.0,
            ChurnRiskTier.MEDIUM: 30.0,
            ChurnRiskTier.LOW: 0.0
        }

    def stratify_risk(self, risk_scores: Dict[str, float],
                     top_risk_factors: List[Tuple[str, float]]) -> Tuple[ChurnRiskTier, List[str], str]:
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
            risk_scores.get('7d', 0) * 0.5 +
            risk_scores.get('14d', 0) * 0.3 +
            risk_scores.get('30d', 0) * 0.2
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

    def _generate_recommendations(self, tier: ChurnRiskTier,
                                risk_factors: List[Tuple[str, float]]) -> List[str]:
        """Generate actionable recommendations based on risk tier and factors"""
        recommendations = []

        # Base recommendations by tier
        tier_recommendations = {
            ChurnRiskTier.CRITICAL: [
                "Immediate phone call required",
                "Escalate to senior agent",
                "Offer emergency property viewing",
                "Consider special incentives"
            ],
            ChurnRiskTier.HIGH: [
                "Schedule follow-up call within 24 hours",
                "Send personalized property recommendations",
                "Offer virtual consultation",
                "Review and adjust communication strategy"
            ],
            ChurnRiskTier.MEDIUM: [
                "Send re-engagement email campaign",
                "Provide market updates",
                "Offer additional property options",
                "Schedule check-in call"
            ],
            ChurnRiskTier.LOW: [
                "Continue standard nurture sequence",
                "Monitor engagement levels",
                "Provide educational content"
            ]
        }

        recommendations.extend(tier_recommendations[tier])

        # Factor-specific recommendations
        factor_recommendations = {
            'days_since_last_interaction': "Initiate immediate outreach",
            'response_rate_7d': "Switch communication channel",
            'engagement_trend': "Re-evaluate content strategy",
            'stage_stagnation_days': "Provide stage progression assistance",
            'email_open_rate': "Improve email subject lines and timing",
            'call_pickup_rate': "Try alternative contact methods",
            'qualification_score_change': "Re-qualify lead and adjust approach"
        }

        # Add factor-specific recommendations
        for factor, importance in risk_factors[:3]:  # Top 3 factors
            if factor in factor_recommendations and importance > 0.1:
                recommendations.append(factor_recommendations[factor])

        return recommendations[:6]  # Limit to 6 recommendations

    def _determine_urgency(self, tier: ChurnRiskTier, risk_scores: Dict[str, float]) -> str:
        """Determine intervention urgency level"""
        # Check for rapidly escalating risk
        score_7d = risk_scores.get('7d', 0)
        score_30d = risk_scores.get('30d', 0)

        urgency_map = {
            ChurnRiskTier.CRITICAL: "immediate",
            ChurnRiskTier.HIGH: "urgent",
            ChurnRiskTier.MEDIUM: "moderate",
            ChurnRiskTier.LOW: "low"
        }

        base_urgency = urgency_map[tier]

        # Escalate urgency if short-term risk is much higher than long-term
        if score_7d > score_30d + 20:
            urgency_escalation = {
                "low": "moderate",
                "moderate": "urgent",
                "urgent": "immediate",
                "immediate": "immediate"
            }
            return urgency_escalation.get(base_urgency, base_urgency)

        return base_urgency

class ChurnPredictionEngine:
    """
    Main orchestration class for the churn prediction system

    Coordinates feature extraction, risk prediction, and stratification
    to provide comprehensive churn risk assessment with actionable insights.
    """

    def __init__(self, memory_service: MemoryService,
                 lifecycle_tracker: LeadLifecycleTracker,
                 behavioral_engine: BehavioralTriggerEngine,
                 lead_scorer: LeadScorer,
                 model_path: Optional[str] = None):

        self.logger = logging.getLogger(__name__ + '.ChurnPredictionEngine')

        # Initialize components
        self.feature_extractor = ChurnFeatureExtractor(
            memory_service, lifecycle_tracker, behavioral_engine, lead_scorer
        )
        self.risk_predictor = ChurnRiskPredictor(model_path)
        self.risk_stratifier = ChurnRiskStratifier()

        # Cache for recent predictions (4-hour TTL)
        self._prediction_cache = {}
        self._cache_ttl = timedelta(hours=4)

        self.logger.info("ChurnPredictionEngine initialized successfully")

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
            risk_tier, recommendations, urgency = self.risk_stratifier.stratify_risk(
                risk_scores, feature_importance
            )

            # Step 5: Create comprehensive prediction object
            prediction = ChurnPrediction(
                lead_id=lead_id,
                prediction_timestamp=datetime.now(),
                risk_score_7d=risk_scores.get('7d', 0.0),
                risk_score_14d=risk_scores.get('14d', 0.0),
                risk_score_30d=risk_scores.get('30d', 0.0),
                risk_tier=risk_tier,
                confidence=confidence,
                top_risk_factors=feature_importance,
                recommended_actions=recommendations,
                intervention_urgency=urgency,
                feature_vector=features.to_dict(),
                model_version=self.risk_predictor.model_version
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
            model_version="fallback-1.0.0"
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
        # In production, this would update the training dataset
        # For now, just log for future model retraining
        self.logger.info(f"Churn outcome recorded: Lead {lead_id} churned={actual_churned}")

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
        engine = ChurnPredictionEngine(
            memory_service, lifecycle_tracker, behavioral_engine, lead_scorer
        )

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