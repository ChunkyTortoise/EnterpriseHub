"""
Predictive Churn Prevention and Lead Retention Optimization Service

This advanced service uses sophisticated ML models and behavioral analytics to predict
lead churn risk in real-time and deploy automated intervention strategies to maximize
lead retention and conversion rates.

Author: AI Assistant
Created: 2026-01-09
Version: 1.0.0
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
from collections import defaultdict, deque
import statistics

# Advanced ML and analytics imports
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import classification_report, roc_auc_score, precision_recall_curve
from sklearn.feature_selection import RFE, SelectFromModel
import xgboost as xgb
import joblib
from pathlib import Path

# Time series analysis
from scipy import stats
from scipy.stats import ks_2samp

# Internal imports
from .enhanced_ml_personalization_engine import (
    EnhancedMLPersonalizationEngine, EmotionalState, ChurnRisk, LearningSignal
)
from models.nurturing_models import (
    LeadType, CommunicationChannel, MessageTone, EngagementType,
    EngagementInteraction
)
from models.evaluation_models import LeadEvaluationResult
from services.claude_semantic_analyzer import ClaudeSemanticAnalyzer

logger = logging.getLogger(__name__)


# Enhanced Churn Prevention Models

class InterventionType(str, Enum):
    """Types of churn prevention interventions."""
    IMMEDIATE_CALL = "immediate_call"
    PERSONALIZED_EMAIL = "personalized_email"
    VIDEO_MESSAGE = "video_message"
    PROPERTY_ALERT = "property_alert"
    MARKET_UPDATE = "market_update"
    INCENTIVE_OFFER = "incentive_offer"
    EDUCATIONAL_CONTENT = "educational_content"
    SOCIAL_PROOF = "social_proof"
    URGENCY_CREATOR = "urgency_creator"
    RELATIONSHIP_BUILDER = "relationship_builder"


class InterventionUrgency(str, Enum):
    """Urgency levels for interventions."""
    IMMEDIATE = "immediate"  # Within 1 hour
    HIGH = "high"            # Within 4 hours
    MODERATE = "moderate"    # Within 24 hours
    LOW = "low"              # Within 72 hours
    SCHEDULED = "scheduled"   # At optimal time


class ChurnIndicator(str, Enum):
    """Specific churn risk indicators."""
    DECLINING_ENGAGEMENT = "declining_engagement"
    NEGATIVE_SENTIMENT = "negative_sentiment"
    DELAYED_RESPONSES = "delayed_responses"
    REDUCED_PROPERTY_VIEWS = "reduced_property_views"
    COMPETITOR_MENTIONS = "competitor_mentions"
    PRICE_OBJECTIONS = "price_objections"
    TIMELINE_DELAYS = "timeline_delays"
    COMMUNICATION_GAPS = "communication_gaps"
    UNREALISTIC_EXPECTATIONS = "unrealistic_expectations"
    EXTERNAL_PRESSURE = "external_pressure"


class RetentionStrategy(str, Enum):
    """High-level retention strategies."""
    VALUE_REINFORCEMENT = "value_reinforcement"
    RELATIONSHIP_DEEPENING = "relationship_deepening"
    PROBLEM_SOLVING = "problem_solving"
    EXPECTATION_MANAGEMENT = "expectation_management"
    COMPETITIVE_DIFFERENTIATION = "competitive_differentiation"
    URGENCY_CREATION = "urgency_creation"
    TRUST_BUILDING = "trust_building"
    EDUCATION_FOCUS = "education_focus"


@dataclass
class ChurnRiskAssessment:
    """Comprehensive churn risk assessment."""
    lead_id: str
    current_risk_level: ChurnRisk
    risk_probability: float
    risk_trend: str  # "increasing", "stable", "decreasing"
    primary_indicators: List[ChurnIndicator]
    risk_score_history: List[Tuple[datetime, float]]
    confidence_score: float
    assessment_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class InterventionRecommendation:
    """Detailed intervention recommendation."""
    intervention_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    lead_id: str
    intervention_type: InterventionType
    urgency_level: InterventionUrgency
    recommended_strategy: RetentionStrategy
    personalized_message: str
    expected_effectiveness: float
    optimal_timing: datetime
    backup_interventions: List[InterventionType]
    success_metrics: List[str]
    implementation_notes: str


@dataclass
class RetentionCampaign:
    """Multi-touch retention campaign."""
    campaign_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    lead_id: str
    strategy: RetentionStrategy
    interventions: List[InterventionRecommendation]
    start_date: datetime
    expected_duration: timedelta
    success_probability: float
    key_milestones: List[Dict[str, Any]]
    performance_tracking: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChurnPreventionResult:
    """Result of churn prevention intervention."""
    lead_id: str
    intervention_id: str
    execution_timestamp: datetime
    success_indicators: List[str]
    engagement_impact: float
    sentiment_change: float
    retention_probability_change: float
    follow_up_required: bool
    next_recommended_action: Optional[str] = None


@dataclass
class LeadRetentionProfile:
    """Comprehensive lead retention profile."""
    lead_id: str
    baseline_retention_probability: float
    current_retention_probability: float
    churn_risk_factors: List[str]
    protective_factors: List[str]
    intervention_history: List[InterventionRecommendation]
    response_patterns: Dict[InterventionType, float]
    optimal_communication_strategy: RetentionStrategy
    last_updated: datetime = field(default_factory=datetime.now)


# Main Churn Prevention Service

class PredictiveChurnPrevention:
    """
    Predictive Churn Prevention Service

    Advanced ML-powered system for:
    - Real-time churn risk prediction
    - Automated intervention deployment
    - Retention campaign orchestration
    - Behavioral pattern analysis
    - Success measurement and optimization
    """

    def __init__(self):
        """Initialize the predictive churn prevention service."""
        self.enhanced_personalization = EnhancedMLPersonalizationEngine()
        self.semantic_analyzer = ClaudeSemanticAnalyzer()

        # Advanced ML models for churn prediction
        self.ensemble_churn_model: Optional[VotingClassifier] = None
        self.risk_progression_model: Optional[GradientBoostingClassifier] = None
        self.intervention_effectiveness_model: Optional[RandomForestClassifier] = None
        self.retention_timeline_model: Optional[xgb.XGBRegressor] = None

        # Feature processing
        self.churn_scaler = StandardScaler()
        self.feature_selector = RFE(RandomForestClassifier(), n_features_to_select=15)
        self.label_encoder = LabelEncoder()

        # Model persistence
        self.models_dir = Path(__file__).parent.parent / "models" / "churn_prevention"
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Real-time tracking
        self.active_assessments: Dict[str, ChurnRiskAssessment] = {}
        self.active_campaigns: Dict[str, RetentionCampaign] = {}
        self.retention_profiles: Dict[str, LeadRetentionProfile] = {}

        # Performance monitoring
        self.intervention_success_rates: Dict[InterventionType, List[float]] = defaultdict(list)
        self.model_performance_metrics: Dict[str, List[float]] = defaultdict(list)

        # Behavioral analytics
        self.engagement_baseline: Dict[str, float] = {}
        self.sentiment_baseline: Dict[str, float] = {}

        # Initialize models and systems
        self._initialize_churn_models()
        self._load_intervention_templates()

        logger.info("Predictive Churn Prevention service initialized")

    def _initialize_churn_models(self):
        """Initialize or load churn prediction models."""
        try:
            self._load_churn_models()
        except FileNotFoundError:
            logger.info("Creating new churn prediction models")
            self._create_churn_models()

    def _load_churn_models(self):
        """Load pre-trained churn models."""
        model_files = {
            'ensemble_churn_model': 'ensemble_churn_model.joblib',
            'risk_progression_model': 'risk_progression_model.joblib',
            'intervention_effectiveness_model': 'intervention_effectiveness_model.joblib',
            'retention_timeline_model': 'retention_timeline_model.joblib',
            'churn_scaler': 'churn_scaler.joblib',
            'feature_selector': 'feature_selector.joblib'
        }

        for attr, filename in model_files.items():
            model_path = self.models_dir / filename
            if model_path.exists():
                setattr(self, attr, joblib.load(model_path))
                logger.info(f"Loaded {attr}")

    def _create_churn_models(self):
        """Create and train initial churn prediction models."""
        # Generate synthetic training data
        X_train, y_churn, y_progression, y_intervention, y_timeline = self._generate_churn_training_data()

        # Create ensemble churn model
        rf_model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
        gb_model = GradientBoostingClassifier(n_estimators=100, random_state=42)
        lr_model = LogisticRegression(random_state=42, class_weight='balanced')

        self.ensemble_churn_model = VotingClassifier(
            estimators=[('rf', rf_model), ('gb', gb_model), ('lr', lr_model)],
            voting='soft'
        )

        # Create other specialized models
        self.risk_progression_model = GradientBoostingClassifier(
            n_estimators=150, learning_rate=0.1, max_depth=6, random_state=42
        )

        self.intervention_effectiveness_model = RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=42
        )

        # Create XGBoost model for timeline prediction
        self.retention_timeline_model = xgb.XGBRegressor(
            n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42
        )

        # Prepare features
        X_scaled = self.churn_scaler.fit_transform(X_train)
        X_selected = self.feature_selector.fit_transform(X_scaled, y_churn)

        # Train models
        self.ensemble_churn_model.fit(X_selected, y_churn)
        self.risk_progression_model.fit(X_selected, y_progression)
        self.intervention_effectiveness_model.fit(X_selected, y_intervention)
        self.retention_timeline_model.fit(X_selected, y_timeline)

        # Save models
        self._save_churn_models()

        logger.info("Churn prediction models created and trained")

    def _generate_churn_training_data(self, n_samples: int = 2000) -> Tuple[np.ndarray, ...]:
        """Generate synthetic training data for churn models."""
        np.random.seed(42)

        # Enhanced feature matrix (20 features)
        X = np.random.randn(n_samples, 20)

        # Churn labels - complex pattern
        churn_score = (
            X[:, 0] * 0.3 +      # Engagement decline
            X[:, 1] * -0.25 +    # Sentiment
            X[:, 2] * 0.2 +      # Response delays
            X[:, 3] * 0.15 +     # Communication gaps
            np.random.normal(0, 0.1, n_samples)
        )
        y_churn = (churn_score > 0.5).astype(int)

        # Risk progression (0=improving, 1=stable, 2=worsening)
        progression_score = X[:, 4] * 0.4 + X[:, 5] * 0.3 + np.random.normal(0, 0.2, n_samples)
        y_progression = np.clip(np.digitize(progression_score, bins=[-0.5, 0.5]) - 1, 0, 2)

        # Intervention effectiveness
        intervention_score = X[:, 6] * 0.3 + X[:, 7] * 0.2 + np.random.normal(0, 0.15, n_samples)
        y_intervention = (intervention_score > 0.3).astype(int)

        # Timeline to churn (in days)
        y_timeline = np.clip(
            30 + X[:, 8] * 15 + X[:, 9] * 10 + np.random.normal(0, 5, n_samples),
            1, 90
        )

        return X, y_churn, y_progression, y_intervention, y_timeline

    def _save_churn_models(self):
        """Save churn prediction models."""
        models_to_save = {
            'ensemble_churn_model': self.ensemble_churn_model,
            'risk_progression_model': self.risk_progression_model,
            'intervention_effectiveness_model': self.intervention_effectiveness_model,
            'retention_timeline_model': self.retention_timeline_model,
            'churn_scaler': self.churn_scaler,
            'feature_selector': self.feature_selector
        }

        for name, model in models_to_save.items():
            if model is not None:
                model_path = self.models_dir / f"{name}.joblib"
                joblib.dump(model, model_path)
                logger.info(f"Saved {name}")

    def _load_intervention_templates(self):
        """Load intervention message templates."""
        self.intervention_templates = {
            InterventionType.IMMEDIATE_CALL: {
                "subject": "Quick check-in about your property search",
                "content": "I wanted to personally reach out to see how your property search is going and address any questions you might have."
            },
            InterventionType.PERSONALIZED_EMAIL: {
                "subject": "Thinking of you and your property goals",
                "content": "I've been thinking about your specific needs and wanted to share some insights that might be helpful."
            },
            InterventionType.VIDEO_MESSAGE: {
                "subject": "Personal message from your agent",
                "content": "I created a quick personal video with some updates specifically for your situation."
            },
            InterventionType.PROPERTY_ALERT: {
                "subject": "🏠 Perfect property match found!",
                "content": "I found a property that matches exactly what you're looking for. This one won't last long."
            },
            InterventionType.MARKET_UPDATE: {
                "subject": "Important market update for your search",
                "content": "Recent market changes are creating unique opportunities in your target area."
            },
            InterventionType.INCENTIVE_OFFER: {
                "subject": "Exclusive opportunity for you",
                "content": "I have an exclusive opportunity that I think would be perfect for your situation."
            }
        }

    # Core Churn Assessment Methods

    async def assess_churn_risk(
        self,
        lead_id: str,
        evaluation_result: LeadEvaluationResult,
        interaction_history: List[EngagementInteraction],
        context: Dict[str, Any]
    ) -> ChurnRiskAssessment:
        """Perform comprehensive churn risk assessment."""
        try:
            # Extract churn-specific features
            churn_features = await self._extract_churn_features(
                lead_id, evaluation_result, interaction_history, context
            )

            # Get current risk prediction
            risk_probability = await self._predict_churn_probability(churn_features)
            risk_level = self._map_probability_to_risk_level(risk_probability)

            # Analyze risk trend
            risk_trend = await self._analyze_risk_trend(lead_id, risk_probability)

            # Identify primary indicators
            primary_indicators = await self._identify_churn_indicators(
                churn_features, interaction_history, context
            )

            # Calculate confidence score
            confidence_score = await self._calculate_assessment_confidence(
                churn_features, len(interaction_history)
            )

            # Update risk history
            risk_history = await self._update_risk_history(lead_id, risk_probability)

            assessment = ChurnRiskAssessment(
                lead_id=lead_id,
                current_risk_level=risk_level,
                risk_probability=risk_probability,
                risk_trend=risk_trend,
                primary_indicators=primary_indicators,
                risk_score_history=risk_history,
                confidence_score=confidence_score
            )

            # Cache assessment
            self.active_assessments[lead_id] = assessment

            logger.info(f"Churn risk assessed for lead {lead_id}: {risk_level.value} ({risk_probability:.2f})")
            return assessment

        except Exception as e:
            logger.error(f"Churn risk assessment failed: {e}")
            return self._default_churn_assessment(lead_id)

    async def _extract_churn_features(
        self,
        lead_id: str,
        evaluation_result: LeadEvaluationResult,
        interaction_history: List[EngagementInteraction],
        context: Dict[str, Any]
    ) -> np.ndarray:
        """Extract features specifically for churn prediction."""
        features = []

        # Engagement trend features
        if interaction_history:
            # Recent vs historical engagement
            recent_interactions = [i for i in interaction_history
                                 if (datetime.now() - i.occurred_at).days <= 7]
            historical_interactions = [i for i in interaction_history
                                     if (datetime.now() - i.occurred_at).days > 7]

            recent_engagement = len(recent_interactions) / max(7, 1)
            historical_engagement = len(historical_interactions) / max(len(interaction_history), 1)

            features.extend([
                recent_engagement,
                historical_engagement,
                recent_engagement / max(historical_engagement, 0.01),  # Engagement ratio
                max((datetime.now() - interaction_history[-1].occurred_at).days, 0) if interaction_history else 30
            ])
        else:
            features.extend([0, 0, 1, 30])

        # Response time analysis
        response_times = []
        for interaction in interaction_history:
            if interaction.response_time:
                response_times.append(interaction.response_time.total_seconds())

        if response_times:
            recent_response_times = response_times[-5:]  # Last 5 responses
            features.extend([
                np.mean(recent_response_times) / 3600,  # Hours
                np.std(recent_response_times) / 3600 if len(recent_response_times) > 1 else 0,
                len([rt for rt in recent_response_times if rt > 86400]) / len(recent_response_times)  # Delayed responses
            ])
        else:
            features.extend([24, 0, 0])  # Default to 24 hour response

        # Communication pattern features
        email_interactions = [i for i in interaction_history if 'email' in str(i.channel).lower()]
        phone_interactions = [i for i in interaction_history if 'phone' in str(i.channel).lower()]

        features.extend([
            len(email_interactions) / max(len(interaction_history), 1),
            len(phone_interactions) / max(len(interaction_history), 1),
            evaluation_result.overall_score / 100,
            1 if evaluation_result.urgency_level in ['high', 'very_high'] else 0
        ])

        # Property engagement features
        property_views = [i for i in interaction_history if i.engagement_type == EngagementType.PROPERTY_VIEWED]
        email_opens = [i for i in interaction_history if i.engagement_type == EngagementType.EMAIL_OPENED]
        email_clicks = [i for i in interaction_history if i.engagement_type == EngagementType.EMAIL_CLICKED]

        features.extend([
            len(property_views) / max(len(interaction_history), 1),
            len(email_opens) / max(len(interaction_history), 1),
            len(email_clicks) / max(len(interaction_history), 1),
            len([i for i in interaction_history if (datetime.now() - i.occurred_at).days <= 3])  # Recent activity
        ])

        # Temporal patterns
        if interaction_history:
            timestamps = [i.occurred_at for i in interaction_history]
            time_intervals = [(timestamps[i] - timestamps[i-1]).total_seconds()
                            for i in range(1, len(timestamps))]

            features.extend([
                np.mean(time_intervals) / 86400 if time_intervals else 7,  # Average days between interactions
                np.std(time_intervals) / 86400 if len(time_intervals) > 1 else 0,  # Interaction consistency
                len(set(t.weekday() for t in timestamps)) / 7  # Day diversity
            ])
        else:
            features.extend([7, 0, 0])

        # Contextual features
        features.extend([
            1 if context.get('budget_specified', False) else 0,
            1 if context.get('timeline_specified', False) else 0,
            len(context.get('viewed_properties', [])),
            1 if context.get('competitor_mentioned', False) else 0
        ])

        # Ensure fixed length (20 features)
        while len(features) < 20:
            features.append(0.0)

        return np.array(features[:20])

    async def _predict_churn_probability(self, features: np.ndarray) -> float:
        """Predict churn probability using ensemble model."""
        try:
            if self.ensemble_churn_model and self.churn_scaler and self.feature_selector:
                features_scaled = self.churn_scaler.transform(features.reshape(1, -1))
                features_selected = self.feature_selector.transform(features_scaled)

                # Get probability from ensemble
                churn_prob = self.ensemble_churn_model.predict_proba(features_selected)[0][1]
                return float(churn_prob)

            else:
                # Fallback heuristic prediction
                return self._heuristic_churn_prediction(features)

        except Exception as e:
            logger.error(f"Churn probability prediction failed: {e}")
            return 0.3  # Default moderate risk

    def _heuristic_churn_prediction(self, features: np.ndarray) -> float:
        """Heuristic churn prediction when ML models unavailable."""
        risk_score = 0.0

        # Recent vs historical engagement (features 0, 1, 2)
        if len(features) > 2:
            engagement_ratio = features[2]
            if engagement_ratio < 0.5:  # Recent engagement much lower
                risk_score += 0.3

        # Days since last interaction (feature 3)
        if len(features) > 3:
            days_since_last = features[3]
            if days_since_last > 14:
                risk_score += 0.25
            elif days_since_last > 7:
                risk_score += 0.15

        # Response time degradation (features 4, 5, 6)
        if len(features) > 6:
            avg_response_time = features[4]
            delayed_response_rate = features[6]

            if avg_response_time > 48:  # More than 48 hours
                risk_score += 0.2
            if delayed_response_rate > 0.5:  # More than half are delayed
                risk_score += 0.15

        # Property engagement decline (features 10, 11, 12)
        if len(features) > 12:
            property_view_rate = features[10]
            email_open_rate = features[11]
            email_click_rate = features[12]

            if property_view_rate < 0.1:
                risk_score += 0.1
            if email_open_rate < 0.3:
                risk_score += 0.1
            if email_click_rate < 0.1:
                risk_score += 0.1

        return min(risk_score, 1.0)

    def _map_probability_to_risk_level(self, probability: float) -> ChurnRisk:
        """Map churn probability to risk level."""
        if probability < 0.15:
            return ChurnRisk.VERY_LOW
        elif probability < 0.3:
            return ChurnRisk.LOW
        elif probability < 0.5:
            return ChurnRisk.MODERATE
        elif probability < 0.75:
            return ChurnRisk.HIGH
        else:
            return ChurnRisk.CRITICAL

    async def _analyze_risk_trend(self, lead_id: str, current_probability: float) -> str:
        """Analyze trend in churn risk over time."""
        if lead_id in self.active_assessments:
            previous_assessment = self.active_assessments[lead_id]
            previous_probability = previous_assessment.risk_probability

            if current_probability > previous_probability + 0.1:
                return "increasing"
            elif current_probability < previous_probability - 0.1:
                return "decreasing"
            else:
                return "stable"
        else:
            return "stable"

    async def _identify_churn_indicators(
        self,
        features: np.ndarray,
        interaction_history: List[EngagementInteraction],
        context: Dict[str, Any]
    ) -> List[ChurnIndicator]:
        """Identify specific churn risk indicators."""
        indicators = []

        # Engagement decline
        if len(features) > 2 and features[2] < 0.5:  # Engagement ratio
            indicators.append(ChurnIndicator.DECLINING_ENGAGEMENT)

        # Response delays
        if len(features) > 6 and features[6] > 0.4:  # Delayed response rate
            indicators.append(ChurnIndicator.DELAYED_RESPONSES)

        # Communication gaps
        if len(features) > 3 and features[3] > 10:  # Days since last interaction
            indicators.append(ChurnIndicator.COMMUNICATION_GAPS)

        # Property view decline
        if len(features) > 10 and features[10] < 0.1:  # Property view rate
            indicators.append(ChurnIndicator.REDUCED_PROPERTY_VIEWS)

        # Context-based indicators
        if context.get('competitor_mentioned', False):
            indicators.append(ChurnIndicator.COMPETITOR_MENTIONS)

        if context.get('price_objections', False):
            indicators.append(ChurnIndicator.PRICE_OBJECTIONS)

        if context.get('timeline_extended', False):
            indicators.append(ChurnIndicator.TIMELINE_DELAYS)

        return indicators

    async def _calculate_assessment_confidence(
        self,
        features: np.ndarray,
        interaction_count: int
    ) -> float:
        """Calculate confidence score for churn assessment."""
        base_confidence = min(interaction_count / 20.0, 1.0)  # More interactions = higher confidence

        # Adjust based on feature completeness
        non_zero_features = np.count_nonzero(features)
        feature_completeness = non_zero_features / len(features)

        # Adjust based on recency of data
        recency_factor = 1.0  # Would be calculated based on interaction recency

        final_confidence = base_confidence * feature_completeness * recency_factor
        return max(0.1, min(1.0, final_confidence))

    async def _update_risk_history(
        self,
        lead_id: str,
        current_probability: float
    ) -> List[Tuple[datetime, float]]:
        """Update and return risk score history."""
        current_entry = (datetime.now(), current_probability)

        if lead_id in self.active_assessments:
            history = self.active_assessments[lead_id].risk_score_history.copy()
            history.append(current_entry)

            # Keep only last 30 entries
            history = history[-30:]
            return history
        else:
            return [current_entry]

    def _default_churn_assessment(self, lead_id: str) -> ChurnRiskAssessment:
        """Return default churn assessment when analysis fails."""
        return ChurnRiskAssessment(
            lead_id=lead_id,
            current_risk_level=ChurnRisk.MODERATE,
            risk_probability=0.4,
            risk_trend="stable",
            primary_indicators=[ChurnIndicator.COMMUNICATION_GAPS],
            risk_score_history=[(datetime.now(), 0.4)],
            confidence_score=0.3
        )

    # Intervention Strategy Methods

    async def recommend_intervention(
        self,
        assessment: ChurnRiskAssessment,
        context: Dict[str, Any]
    ) -> InterventionRecommendation:
        """Generate personalized intervention recommendation."""
        try:
            # Determine intervention urgency
            urgency_level = self._determine_intervention_urgency(assessment.current_risk_level)

            # Select optimal intervention type
            intervention_type = await self._select_optimal_intervention(
                assessment, context
            )

            # Determine retention strategy
            retention_strategy = self._determine_retention_strategy(
                assessment.primary_indicators, context
            )

            # Generate personalized message
            personalized_message = await self._generate_intervention_message(
                assessment, intervention_type, retention_strategy, context
            )

            # Calculate expected effectiveness
            expected_effectiveness = await self._predict_intervention_effectiveness(
                assessment, intervention_type, context
            )

            # Determine optimal timing
            optimal_timing = self._calculate_optimal_intervention_timing(
                urgency_level, context
            )

            # Generate backup interventions
            backup_interventions = await self._generate_backup_interventions(
                intervention_type, assessment
            )

            # Define success metrics
            success_metrics = self._define_intervention_success_metrics(
                intervention_type, assessment.current_risk_level
            )

            # Implementation notes
            implementation_notes = self._generate_implementation_notes(
                intervention_type, retention_strategy, context
            )

            recommendation = InterventionRecommendation(
                lead_id=assessment.lead_id,
                intervention_type=intervention_type,
                urgency_level=urgency_level,
                recommended_strategy=retention_strategy,
                personalized_message=personalized_message,
                expected_effectiveness=expected_effectiveness,
                optimal_timing=optimal_timing,
                backup_interventions=backup_interventions,
                success_metrics=success_metrics,
                implementation_notes=implementation_notes
            )

            logger.info(f"Intervention recommended for lead {assessment.lead_id}: {intervention_type.value}")
            return recommendation

        except Exception as e:
            logger.error(f"Intervention recommendation failed: {e}")
            return self._default_intervention_recommendation(assessment.lead_id)

    def _determine_intervention_urgency(self, risk_level: ChurnRisk) -> InterventionUrgency:
        """Determine intervention urgency based on risk level."""
        urgency_mapping = {
            ChurnRisk.VERY_LOW: InterventionUrgency.SCHEDULED,
            ChurnRisk.LOW: InterventionUrgency.LOW,
            ChurnRisk.MODERATE: InterventionUrgency.MODERATE,
            ChurnRisk.HIGH: InterventionUrgency.HIGH,
            ChurnRisk.CRITICAL: InterventionUrgency.IMMEDIATE
        }
        return urgency_mapping.get(risk_level, InterventionUrgency.MODERATE)

    async def _select_optimal_intervention(
        self,
        assessment: ChurnRiskAssessment,
        context: Dict[str, Any]
    ) -> InterventionType:
        """Select optimal intervention type based on lead profile and risk factors."""

        # Critical risk requires immediate personal contact
        if assessment.current_risk_level == ChurnRisk.CRITICAL:
            return InterventionType.IMMEDIATE_CALL

        # Check specific risk indicators
        primary_indicators = assessment.primary_indicators

        if ChurnIndicator.COMPETITOR_MENTIONS in primary_indicators:
            return InterventionType.SOCIAL_PROOF
        elif ChurnIndicator.PRICE_OBJECTIONS in primary_indicators:
            return InterventionType.INCENTIVE_OFFER
        elif ChurnIndicator.DECLINING_ENGAGEMENT in primary_indicators:
            return InterventionType.VIDEO_MESSAGE
        elif ChurnIndicator.REDUCED_PROPERTY_VIEWS in primary_indicators:
            return InterventionType.PROPERTY_ALERT
        elif ChurnIndicator.COMMUNICATION_GAPS in primary_indicators:
            return InterventionType.PERSONALIZED_EMAIL
        else:
            # Default based on risk level
            default_interventions = {
                ChurnRisk.HIGH: InterventionType.VIDEO_MESSAGE,
                ChurnRisk.MODERATE: InterventionType.MARKET_UPDATE,
                ChurnRisk.LOW: InterventionType.EDUCATIONAL_CONTENT,
                ChurnRisk.VERY_LOW: InterventionType.RELATIONSHIP_BUILDER
            }
            return default_interventions.get(assessment.current_risk_level, InterventionType.PERSONALIZED_EMAIL)

    def _determine_retention_strategy(
        self,
        indicators: List[ChurnIndicator],
        context: Dict[str, Any]
    ) -> RetentionStrategy:
        """Determine high-level retention strategy."""

        # Map indicators to strategies
        if ChurnIndicator.COMPETITOR_MENTIONS in indicators:
            return RetentionStrategy.COMPETITIVE_DIFFERENTIATION
        elif ChurnIndicator.PRICE_OBJECTIONS in indicators:
            return RetentionStrategy.VALUE_REINFORCEMENT
        elif any(ind in indicators for ind in [ChurnIndicator.COMMUNICATION_GAPS, ChurnIndicator.DECLINING_ENGAGEMENT]):
            return RetentionStrategy.RELATIONSHIP_DEEPENING
        elif ChurnIndicator.UNREALISTIC_EXPECTATIONS in indicators:
            return RetentionStrategy.EXPECTATION_MANAGEMENT
        elif ChurnIndicator.TIMELINE_DELAYS in indicators:
            return RetentionStrategy.URGENCY_CREATION
        else:
            return RetentionStrategy.TRUST_BUILDING

    async def _generate_intervention_message(
        self,
        assessment: ChurnRiskAssessment,
        intervention_type: InterventionType,
        strategy: RetentionStrategy,
        context: Dict[str, Any]
    ) -> str:
        """Generate personalized intervention message."""
        try:
            # Get base template
            template = self.intervention_templates.get(intervention_type, {})
            base_message = template.get("content", "I wanted to reach out personally.")

            # Create enhancement prompt
            prompt = f"""
            Create a personalized intervention message for a lead at risk of churning:

            Situation:
            - Churn Risk: {assessment.current_risk_level.value}
            - Risk Indicators: {', '.join([ind.value for ind in assessment.primary_indicators])}
            - Intervention Type: {intervention_type.value}
            - Strategy: {strategy.value}

            Context:
            - Lead preferences: {context.get('preferences', {})}
            - Property interests: {context.get('property_interests', 'General')}
            - Timeline: {context.get('timeline', 'Flexible')}
            - Budget: {context.get('budget_range', 'Not specified')}

            Guidelines:
            1. Address their specific concerns without being pushy
            2. Provide genuine value and assistance
            3. Rebuild confidence and trust
            4. Create positive momentum
            5. Include a clear next step

            Base message: {base_message}

            Return an enhanced, personalized message that feels genuine and helpful.
            """

            # Get AI-enhanced message
            enhanced_message = await self.semantic_analyzer._get_claude_analysis(prompt)
            return enhanced_message

        except Exception as e:
            logger.error(f"Message generation failed: {e}")
            return template.get("content", "I wanted to personally reach out and see how I can better assist you.")

    async def _predict_intervention_effectiveness(
        self,
        assessment: ChurnRiskAssessment,
        intervention_type: InterventionType,
        context: Dict[str, Any]
    ) -> float:
        """Predict effectiveness of proposed intervention."""
        try:
            if self.intervention_effectiveness_model:
                # Would use actual features here
                features = np.random.rand(1, 15)  # Placeholder
                effectiveness = self.intervention_effectiveness_model.predict_proba(features)[0][1]
                return float(effectiveness)
            else:
                # Heuristic effectiveness
                return self._heuristic_intervention_effectiveness(intervention_type, assessment)

        except Exception as e:
            logger.error(f"Intervention effectiveness prediction failed: {e}")
            return 0.6

    def _heuristic_intervention_effectiveness(
        self,
        intervention_type: InterventionType,
        assessment: ChurnRiskAssessment
    ) -> float:
        """Heuristic intervention effectiveness calculation."""
        base_effectiveness = {
            InterventionType.IMMEDIATE_CALL: 0.8,
            InterventionType.VIDEO_MESSAGE: 0.75,
            InterventionType.PROPERTY_ALERT: 0.7,
            InterventionType.PERSONALIZED_EMAIL: 0.6,
            InterventionType.SOCIAL_PROOF: 0.65,
            InterventionType.INCENTIVE_OFFER: 0.7,
            InterventionType.MARKET_UPDATE: 0.55,
            InterventionType.EDUCATIONAL_CONTENT: 0.5,
            InterventionType.RELATIONSHIP_BUILDER: 0.6,
            InterventionType.URGENCY_CREATOR: 0.65
        }

        effectiveness = base_effectiveness.get(intervention_type, 0.6)

        # Adjust based on risk level
        if assessment.current_risk_level == ChurnRisk.CRITICAL:
            effectiveness *= 0.8  # Lower effectiveness for critical risk
        elif assessment.current_risk_level in [ChurnRisk.HIGH, ChurnRisk.MODERATE]:
            effectiveness *= 0.9

        return effectiveness

    def _calculate_optimal_intervention_timing(
        self,
        urgency_level: InterventionUrgency,
        context: Dict[str, Any]
    ) -> datetime:
        """Calculate optimal timing for intervention."""
        base_time = datetime.now()

        timing_delays = {
            InterventionUrgency.IMMEDIATE: timedelta(minutes=30),
            InterventionUrgency.HIGH: timedelta(hours=2),
            InterventionUrgency.MODERATE: timedelta(hours=8),
            InterventionUrgency.LOW: timedelta(hours=24),
            InterventionUrgency.SCHEDULED: timedelta(days=2)
        }

        delay = timing_delays.get(urgency_level, timedelta(hours=8))

        # Adjust for business hours
        optimal_time = base_time + delay

        # Ensure it's during business hours (9 AM - 6 PM)
        if optimal_time.hour < 9:
            optimal_time = optimal_time.replace(hour=9, minute=0)
        elif optimal_time.hour > 18:
            optimal_time = optimal_time.replace(hour=9, minute=0) + timedelta(days=1)

        return optimal_time

    async def _generate_backup_interventions(
        self,
        primary_intervention: InterventionType,
        assessment: ChurnRiskAssessment
    ) -> List[InterventionType]:
        """Generate backup intervention options."""
        all_interventions = list(InterventionType)

        # Remove primary intervention
        backup_options = [i for i in all_interventions if i != primary_intervention]

        # Sort by relevance to risk level
        relevance_score = {}
        for intervention in backup_options:
            # Simple scoring based on intervention type and risk level
            score = self._score_intervention_relevance(intervention, assessment.current_risk_level)
            relevance_score[intervention] = score

        # Return top 3 backup options
        sorted_backups = sorted(backup_options, key=lambda x: relevance_score[x], reverse=True)
        return sorted_backups[:3]

    def _score_intervention_relevance(
        self,
        intervention: InterventionType,
        risk_level: ChurnRisk
    ) -> float:
        """Score intervention relevance for backup selection."""
        # High-touch interventions for high risk
        high_touch = [
            InterventionType.IMMEDIATE_CALL,
            InterventionType.VIDEO_MESSAGE,
            InterventionType.PROPERTY_ALERT
        ]

        # Medium-touch interventions
        medium_touch = [
            InterventionType.PERSONALIZED_EMAIL,
            InterventionType.SOCIAL_PROOF,
            InterventionType.INCENTIVE_OFFER
        ]

        if risk_level in [ChurnRisk.HIGH, ChurnRisk.CRITICAL]:
            if intervention in high_touch:
                return 0.9
            elif intervention in medium_touch:
                return 0.6
            else:
                return 0.3
        elif risk_level == ChurnRisk.MODERATE:
            if intervention in medium_touch:
                return 0.8
            elif intervention in high_touch:
                return 0.7
            else:
                return 0.4
        else:
            return 0.5  # Equal relevance for low risk

    def _define_intervention_success_metrics(
        self,
        intervention_type: InterventionType,
        risk_level: ChurnRisk
    ) -> List[str]:
        """Define success metrics for intervention."""
        base_metrics = [
            "Response within 24 hours",
            "Positive sentiment in response",
            "Engagement increase"
        ]

        intervention_specific = {
            InterventionType.IMMEDIATE_CALL: [
                "Call answered or returned",
                "Appointment scheduled",
                "Concerns addressed"
            ],
            InterventionType.PROPERTY_ALERT: [
                "Property viewed",
                "Showing requested",
                "Interest expressed"
            ],
            InterventionType.VIDEO_MESSAGE: [
                "Video watched",
                "Personal response received",
                "Relationship warmth increased"
            ]
        }

        metrics = base_metrics + intervention_specific.get(intervention_type, [])

        # Add risk-level specific metrics
        if risk_level in [ChurnRisk.HIGH, ChurnRisk.CRITICAL]:
            metrics.append("Immediate re-engagement")
            metrics.append("Churn risk reduction")

        return metrics

    def _generate_implementation_notes(
        self,
        intervention_type: InterventionType,
        strategy: RetentionStrategy,
        context: Dict[str, Any]
    ) -> str:
        """Generate implementation notes for the intervention."""
        notes = []

        # Intervention-specific notes
        if intervention_type == InterventionType.IMMEDIATE_CALL:
            notes.append("Prepare talking points about their specific concerns")
            notes.append("Have relevant properties ready to discuss")
            notes.append("Be prepared to schedule immediate showing if interested")
        elif intervention_type == InterventionType.VIDEO_MESSAGE:
            notes.append("Keep video under 2 minutes")
            notes.append("Include personal elements and their specific situation")
            notes.append("End with clear call to action")

        # Strategy-specific notes
        if strategy == RetentionStrategy.COMPETITIVE_DIFFERENTIATION:
            notes.append("Highlight unique value propositions")
            notes.append("Share client testimonials")
        elif strategy == RetentionStrategy.VALUE_REINFORCEMENT:
            notes.append("Emphasize cost savings and ROI")
            notes.append("Provide market comparison data")

        return "; ".join(notes) if notes else "Execute intervention according to best practices"

    def _default_intervention_recommendation(self, lead_id: str) -> InterventionRecommendation:
        """Return default intervention recommendation."""
        return InterventionRecommendation(
            lead_id=lead_id,
            intervention_type=InterventionType.PERSONALIZED_EMAIL,
            urgency_level=InterventionUrgency.MODERATE,
            recommended_strategy=RetentionStrategy.RELATIONSHIP_DEEPENING,
            personalized_message="I wanted to check in and see how your property search is going.",
            expected_effectiveness=0.6,
            optimal_timing=datetime.now() + timedelta(hours=4),
            backup_interventions=[InterventionType.MARKET_UPDATE, InterventionType.EDUCATIONAL_CONTENT],
            success_metrics=["Response received", "Engagement maintained"],
            implementation_notes="Standard follow-up approach"
        )

    # Retention Campaign Orchestration

    async def create_retention_campaign(
        self,
        assessment: ChurnRiskAssessment,
        primary_intervention: InterventionRecommendation,
        context: Dict[str, Any]
    ) -> RetentionCampaign:
        """Create comprehensive retention campaign."""
        try:
            # Determine campaign strategy
            strategy = primary_intervention.recommended_strategy

            # Generate campaign interventions sequence
            interventions = await self._generate_campaign_sequence(
                assessment, primary_intervention, context
            )

            # Calculate campaign duration
            expected_duration = self._calculate_campaign_duration(
                assessment.current_risk_level, len(interventions)
            )

            # Calculate success probability
            success_probability = await self._calculate_campaign_success_probability(
                assessment, interventions
            )

            # Define campaign milestones
            milestones = self._define_campaign_milestones(interventions, strategy)

            campaign = RetentionCampaign(
                lead_id=assessment.lead_id,
                strategy=strategy,
                interventions=interventions,
                start_date=datetime.now(),
                expected_duration=expected_duration,
                success_probability=success_probability,
                key_milestones=milestones,
                performance_tracking={
                    "interventions_executed": 0,
                    "positive_responses": 0,
                    "engagement_score": 0.0,
                    "risk_reduction": 0.0
                }
            )

            # Cache campaign
            self.active_campaigns[assessment.lead_id] = campaign

            logger.info(f"Retention campaign created for lead {assessment.lead_id}")
            return campaign

        except Exception as e:
            logger.error(f"Retention campaign creation failed: {e}")
            raise

    # Performance Monitoring and Analytics

    async def track_intervention_result(
        self,
        intervention_recommendation: InterventionRecommendation,
        result: ChurnPreventionResult
    ):
        """Track intervention results for learning and optimization."""
        try:
            # Update success rates
            intervention_type = intervention_recommendation.intervention_type
            success_score = (
                result.engagement_impact * 0.4 +
                result.sentiment_change * 0.3 +
                result.retention_probability_change * 0.3
            )

            self.intervention_success_rates[intervention_type].append(success_score)

            # Keep only recent results
            if len(self.intervention_success_rates[intervention_type]) > 100:
                self.intervention_success_rates[intervention_type] = \
                    self.intervention_success_rates[intervention_type][-50:]

            # Update lead retention profile
            await self._update_retention_profile(
                result.lead_id, intervention_recommendation, result
            )

            # Log learning signal for model improvement
            await self.enhanced_personalization._add_learning_signal(
                LearningSignal.POSITIVE_ENGAGEMENT if success_score > 0.5 else LearningSignal.NEGATIVE_FEEDBACK,
                result.lead_id,
                {
                    'intervention_type': intervention_type.value,
                    'expected_effectiveness': intervention_recommendation.expected_effectiveness
                },
                {
                    'actual_effectiveness': success_score,
                    'engagement_impact': result.engagement_impact
                },
                success_score
            )

            logger.info(f"Intervention result tracked for lead {result.lead_id}: score {success_score:.2f}")

        except Exception as e:
            logger.error(f"Intervention result tracking failed: {e}")

    async def _update_retention_profile(
        self,
        lead_id: str,
        intervention: InterventionRecommendation,
        result: ChurnPreventionResult
    ):
        """Update lead retention profile with intervention results."""
        if lead_id not in self.retention_profiles:
            # Create new profile
            self.retention_profiles[lead_id] = LeadRetentionProfile(
                lead_id=lead_id,
                baseline_retention_probability=0.6,
                current_retention_probability=0.6,
                churn_risk_factors=[],
                protective_factors=[],
                intervention_history=[],
                response_patterns={},
                optimal_communication_strategy=RetentionStrategy.RELATIONSHIP_DEEPENING
            )

        profile = self.retention_profiles[lead_id]

        # Update intervention history
        profile.intervention_history.append(intervention)

        # Update response patterns
        intervention_type = intervention.intervention_type
        success_score = (
            result.engagement_impact * 0.4 +
            result.sentiment_change * 0.3 +
            result.retention_probability_change * 0.3
        )

        if intervention_type not in profile.response_patterns:
            profile.response_patterns[intervention_type] = success_score
        else:
            # Weighted average with historical performance
            current_score = profile.response_patterns[intervention_type]
            profile.response_patterns[intervention_type] = (current_score * 0.7 + success_score * 0.3)

        # Update retention probability
        profile.current_retention_probability = min(
            profile.current_retention_probability + result.retention_probability_change,
            1.0
        )

        profile.last_updated = datetime.now()

    async def get_churn_prevention_analytics(self) -> Dict[str, Any]:
        """Get comprehensive churn prevention analytics."""
        try:
            # Calculate intervention success rates
            intervention_analytics = {}
            for intervention_type, scores in self.intervention_success_rates.items():
                if scores:
                    intervention_analytics[intervention_type.value] = {
                        'success_rate': statistics.mean(scores),
                        'total_uses': len(scores),
                        'trend': 'improving' if len(scores) > 5 and scores[-3:] > scores[-6:-3] else 'stable'
                    }

            # Active campaign statistics
            campaign_stats = {
                'active_campaigns': len(self.active_campaigns),
                'total_retention_profiles': len(self.retention_profiles),
                'high_risk_leads': len([a for a in self.active_assessments.values()
                                      if a.current_risk_level in [ChurnRisk.HIGH, ChurnRisk.CRITICAL]])
            }

            # Model performance metrics
            model_metrics = {
                'churn_model_loaded': self.ensemble_churn_model is not None,
                'intervention_model_loaded': self.intervention_effectiveness_model is not None,
                'risk_progression_model_loaded': self.risk_progression_model is not None,
                'retention_timeline_model_loaded': self.retention_timeline_model is not None
            }

            return {
                'intervention_analytics': intervention_analytics,
                'campaign_statistics': campaign_stats,
                'model_performance': model_metrics,
                'system_health': {
                    'assessments_processed': len(self.active_assessments),
                    'avg_intervention_effectiveness': statistics.mean([
                        statistics.mean(scores) for scores in self.intervention_success_rates.values()
                        if scores
                    ]) if any(self.intervention_success_rates.values()) else 0.6
                }
            }

        except Exception as e:
            logger.error(f"Analytics generation failed: {e}")
            return {'error': str(e)}

    # Additional helper methods for campaign sequence, milestones, etc.
    # (Implementation details omitted for brevity)

    async def _generate_campaign_sequence(
        self,
        assessment: ChurnRiskAssessment,
        primary_intervention: InterventionRecommendation,
        context: Dict[str, Any]
    ) -> List[InterventionRecommendation]:
        """Generate sequence of interventions for campaign."""
        # Simplified implementation - would be more sophisticated in production
        return [primary_intervention] + [
            self._default_intervention_recommendation(assessment.lead_id)
            for _ in range(2)  # 3-touch campaign
        ]

    def _calculate_campaign_duration(self, risk_level: ChurnRisk, num_interventions: int) -> timedelta:
        """Calculate expected campaign duration."""
        base_days = 14
        if risk_level in [ChurnRisk.HIGH, ChurnRisk.CRITICAL]:
            base_days = 7
        return timedelta(days=base_days)

    async def _calculate_campaign_success_probability(
        self,
        assessment: ChurnRiskAssessment,
        interventions: List[InterventionRecommendation]
    ) -> float:
        """Calculate overall campaign success probability."""
        individual_probs = [i.expected_effectiveness for i in interventions]
        # Combined probability calculation (simplified)
        return 1.0 - np.prod([1.0 - p for p in individual_probs])

    def _define_campaign_milestones(
        self,
        interventions: List[InterventionRecommendation],
        strategy: RetentionStrategy
    ) -> List[Dict[str, Any]]:
        """Define key milestones for campaign tracking."""
        return [
            {
                'milestone': 'First Intervention Executed',
                'target_date': interventions[0].optimal_timing,
                'success_criteria': 'Response received within 24 hours'
            },
            {
                'milestone': 'Risk Reduction Achieved',
                'target_date': datetime.now() + timedelta(days=7),
                'success_criteria': 'Churn risk reduced by one level'
            },
            {
                'milestone': 'Re-engagement Confirmed',
                'target_date': datetime.now() + timedelta(days=14),
                'success_criteria': 'Sustained positive engagement'
            }
        ]


# Export main classes
__all__ = [
    'PredictiveChurnPrevention',
    'ChurnRiskAssessment',
    'InterventionRecommendation',
    'RetentionCampaign',
    'ChurnPreventionResult',
    'InterventionType',
    'ChurnIndicator',
    'RetentionStrategy'
]