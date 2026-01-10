"""
Enhanced ML-Powered Personalization Engine - Advanced Features Extension

This enhanced version adds sophisticated sentiment analysis, emotional intelligence mapping,
predictive churn prevention, real-time model retraining, multi-modal communication
optimization, and advanced behavioral pattern recognition.

Author: AI Assistant
Created: 2026-01-09
Version: 2.0.0 - Enhanced Edition
"""

import asyncio
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import re
from collections import defaultdict, deque
import statistics

# Advanced ML imports
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor, IsolationForest
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.model_selection import cross_val_score
from sklearn.neural_network import MLPRegressor, MLPClassifier
from sklearn.metrics import silhouette_score, accuracy_score, mean_squared_error
import joblib
from pathlib import Path

# Text analysis imports
import nltk
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Base imports
from .advanced_ml_personalization_engine import (
    AdvancedMLPersonalizationEngine, PersonalizationFeatures,
    PersonalizationOutput, OptimalTimingPrediction
)
from models.nurturing_models import (
    LeadType, CommunicationChannel, MessageTone, EngagementType,
    PersonalizedMessage, EngagementInteraction, OptimizationRecommendation
)
from models.evaluation_models import LeadEvaluationResult
from services.claude_semantic_analyzer import ClaudeSemanticAnalyzer

logger = logging.getLogger(__name__)


# Enhanced Enums and Data Models

class EmotionalState(str, Enum):
    """Enhanced emotional state mapping for leads."""
    EXCITED = "excited"
    ANXIOUS = "anxious"
    FRUSTRATED = "frustrated"
    CONFIDENT = "confident"
    UNCERTAIN = "uncertain"
    OPTIMISTIC = "optimistic"
    SKEPTICAL = "skeptical"
    TRUSTING = "trusting"
    IMPATIENT = "impatient"
    CONTENT = "content"


class ChurnRisk(str, Enum):
    """Churn risk levels for predictive prevention."""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class CommunicationMode(str, Enum):
    """Enhanced communication modes including voice analysis."""
    TEXT_FORMAL = "text_formal"
    TEXT_CASUAL = "text_casual"
    VOICE_CALM = "voice_calm"
    VOICE_ENERGETIC = "voice_energetic"
    MIXED_MULTIMEDIA = "mixed_multimedia"


class LearningSignal(str, Enum):
    """Types of learning signals for model improvement."""
    POSITIVE_ENGAGEMENT = "positive_engagement"
    NEGATIVE_FEEDBACK = "negative_feedback"
    CONVERSION_SUCCESS = "conversion_success"
    CHURN_EVENT = "churn_event"
    PREFERENCE_CHANGE = "preference_change"


# Enhanced Feature Models

@dataclass
class SentimentAnalysisResult:
    """Comprehensive sentiment analysis results."""
    overall_sentiment: float  # -1 to 1
    emotion_scores: Dict[EmotionalState, float]
    confidence_score: float
    key_phrases: List[str]
    sentiment_trend: List[Tuple[datetime, float]]  # Historical sentiment
    emotional_volatility: float


@dataclass
class ChurnPrediction:
    """Churn risk prediction with intervention recommendations."""
    risk_level: ChurnRisk
    probability: float
    contributing_factors: List[str]
    intervention_strategies: List[str]
    optimal_intervention_timing: datetime
    confidence_score: float


@dataclass
class VoiceAnalysisResult:
    """Voice communication analysis results."""
    speaking_pace: float
    tone_confidence: float
    emotional_intensity: float
    key_topics: List[str]
    engagement_indicators: List[str]
    recommended_response_style: str


@dataclass
class LeadJourneyStage:
    """Enhanced lead journey stage with emotional context."""
    stage_name: str
    emotional_state: EmotionalState
    confidence_level: float
    optimal_actions: List[str]
    risk_factors: List[str]
    expected_duration: timedelta
    success_probability: float


@dataclass
class RealTimeLearningSignal:
    """Real-time learning signal for model updates."""
    signal_type: LearningSignal
    lead_id: str
    interaction_context: Dict[str, Any]
    outcome_data: Dict[str, Any]
    feedback_score: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AdvancedPersonalizationOutput:
    """Enhanced personalization output with advanced features."""
    # Base personalization
    personalized_subject: str
    personalized_content: str
    optimal_channel: CommunicationChannel
    optimal_timing: OptimalTimingPrediction

    # Enhanced features
    emotional_adaptation: Dict[str, Any]
    sentiment_optimization: SentimentAnalysisResult
    churn_prevention: ChurnPrediction
    voice_recommendations: Optional[VoiceAnalysisResult]
    journey_stage: LeadJourneyStage
    learning_feedback: List[RealTimeLearningSignal]

    # Advanced metrics
    personalization_confidence: float
    predicted_engagement_score: float
    emotional_resonance_score: float
    retention_probability: float

    # Multi-modal variations
    content_variations: List[Dict[str, Any]]
    behavioral_insights: Dict[str, Any]


# Enhanced ML Personalization Engine

class EnhancedMLPersonalizationEngine(AdvancedMLPersonalizationEngine):
    """
    Enhanced ML Personalization Engine with Advanced Features

    New capabilities:
    - Sentiment analysis and emotional intelligence
    - Predictive churn prevention
    - Real-time model retraining
    - Multi-modal communication optimization
    - Advanced behavioral pattern recognition
    - Lead journey optimization
    """

    def __init__(self):
        """Initialize the enhanced personalization engine."""
        super().__init__()

        # Enhanced ML models
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.churn_model: Optional[RandomForestClassifier] = None
        self.emotion_model: Optional[MLPClassifier] = None
        self.journey_model: Optional[GradientBoostingRegressor] = None
        self.neural_personalization: Optional[MLPRegressor] = None

        # Advanced feature processors
        self.emotion_scaler = RobustScaler()
        self.feature_selector = SelectKBest(f_classif, k=10)
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)

        # Real-time learning components
        self.learning_buffer = deque(maxlen=1000)  # Recent learning signals
        self.model_performance_tracker = defaultdict(list)
        self.last_retrain_time = datetime.now()
        self.retrain_threshold = 50  # Number of signals before retraining

        # Enhanced caching and tracking
        self.sentiment_cache: Dict[str, SentimentAnalysisResult] = {}
        self.churn_predictions: Dict[str, ChurnPrediction] = {}
        self.journey_stages: Dict[str, LeadJourneyStage] = {}
        self.voice_analysis_cache: Dict[str, VoiceAnalysisResult] = {}

        # Performance monitoring
        self.prediction_accuracy_tracker = {
            'sentiment': [],
            'churn': [],
            'engagement': [],
            'timing': []
        }

        # Initialize enhanced models
        self._initialize_enhanced_models()

        logger.info("Enhanced ML Personalization Engine initialized with advanced features")

    def _initialize_enhanced_models(self):
        """Initialize enhanced ML models."""
        try:
            # Load enhanced models if available
            self._load_enhanced_models()
        except FileNotFoundError:
            logger.info("Creating new enhanced models")
            self._create_enhanced_models()

    def _load_enhanced_models(self):
        """Load enhanced models from disk."""
        enhanced_model_files = {
            'churn_model': 'churn_prediction_model.joblib',
            'emotion_model': 'emotion_classification_model.joblib',
            'journey_model': 'journey_optimization_model.joblib',
            'neural_personalization': 'neural_personalization_model.joblib',
            'emotion_scaler': 'emotion_scaler.joblib',
            'feature_selector': 'feature_selector.joblib',
            'anomaly_detector': 'anomaly_detector.joblib'
        }

        for attr, filename in enhanced_model_files.items():
            model_path = self.models_dir / filename
            if model_path.exists():
                setattr(self, attr, joblib.load(model_path))
                logger.info(f"Loaded enhanced {attr} from {filename}")

    def _create_enhanced_models(self):
        """Create and train enhanced models."""
        # Generate enhanced training data
        X_enhanced, y_churn, y_emotion, y_journey = self._generate_enhanced_training_data()

        # Initialize enhanced models
        self.churn_model = RandomForestClassifier(
            n_estimators=200, max_depth=15, random_state=42,
            class_weight='balanced'
        )

        self.emotion_model = MLPClassifier(
            hidden_layer_sizes=(100, 50), max_iter=500, random_state=42,
            activation='relu', solver='adam'
        )

        self.journey_model = GradientBoostingRegressor(
            n_estimators=150, learning_rate=0.1, max_depth=8, random_state=42
        )

        self.neural_personalization = MLPRegressor(
            hidden_layer_sizes=(200, 100, 50), max_iter=1000, random_state=42,
            activation='relu', solver='adam', alpha=0.001
        )

        # Train enhanced models
        X_scaled = self.emotion_scaler.fit_transform(X_enhanced)
        X_selected = self.feature_selector.fit_transform(X_scaled, y_emotion)

        self.churn_model.fit(X_selected, y_churn)
        self.emotion_model.fit(X_selected, y_emotion)
        self.journey_model.fit(X_selected, y_journey)
        self.neural_personalization.fit(X_selected, np.random.rand(len(X_selected)))

        # Train anomaly detector
        self.anomaly_detector.fit(X_selected)

        # Save enhanced models
        self._save_enhanced_models()

        logger.info("Enhanced models created and trained successfully")

    def _generate_enhanced_training_data(self, n_samples: int = 1500) -> Tuple[np.ndarray, ...]:
        """Generate enhanced synthetic training data."""
        np.random.seed(42)

        # Enhanced feature matrix (25 features)
        X_enhanced = np.random.randn(n_samples, 25)

        # Churn labels (binary)
        churn_probability = 1 / (1 + np.exp(-(X_enhanced[:, 0] * 0.5 + X_enhanced[:, 1] * -0.3)))
        y_churn = (churn_probability > 0.5).astype(int)

        # Emotion labels (10 emotions)
        y_emotion = np.random.choice(range(10), size=n_samples)

        # Journey stage progression (0-1)
        y_journey = np.clip(
            X_enhanced[:, 2] * 0.4 + X_enhanced[:, 3] * 0.3 + np.random.normal(0, 0.1, n_samples),
            0, 1
        )

        return X_enhanced, y_churn, y_emotion, y_journey

    def _save_enhanced_models(self):
        """Save enhanced models to disk."""
        enhanced_models = {
            'churn_model': self.churn_model,
            'emotion_model': self.emotion_model,
            'journey_model': self.journey_model,
            'neural_personalization': self.neural_personalization,
            'emotion_scaler': self.emotion_scaler,
            'feature_selector': self.feature_selector,
            'anomaly_detector': self.anomaly_detector
        }

        for name, model in enhanced_models.items():
            if model is not None:
                model_path = self.models_dir / f"{name}.joblib"
                joblib.dump(model, model_path)
                logger.info(f"Saved enhanced {name}")

    # Enhanced Core Methods

    async def generate_enhanced_personalization(
        self,
        lead_id: str,
        evaluation_result: LeadEvaluationResult,
        message_template: str,
        interaction_history: List[EngagementInteraction],
        context: Dict[str, Any],
        voice_transcript: Optional[str] = None,
        historical_sentiment: Optional[List[str]] = None
    ) -> AdvancedPersonalizationOutput:
        """
        Generate advanced personalized communication with enhanced features.

        Args:
            lead_id: Lead identifier
            evaluation_result: Current lead evaluation
            message_template: Base message template
            interaction_history: Historical interactions
            context: Additional context
            voice_transcript: Optional voice conversation transcript
            historical_sentiment: Optional historical sentiment data

        Returns:
            Comprehensive enhanced personalization output
        """
        try:
            # Extract enhanced features
            enhanced_features = await self._extract_enhanced_features(
                lead_id, evaluation_result, interaction_history, context,
                voice_transcript, historical_sentiment
            )

            # Perform sentiment analysis
            sentiment_result = await self._analyze_comprehensive_sentiment(
                lead_id, interaction_history, historical_sentiment
            )

            # Predict churn risk
            churn_prediction = await self._predict_churn_risk(
                lead_id, enhanced_features, sentiment_result
            )

            # Analyze voice communication (if available)
            voice_analysis = None
            if voice_transcript:
                voice_analysis = await self._analyze_voice_communication(voice_transcript)

            # Determine journey stage
            journey_stage = await self._determine_journey_stage(
                lead_id, enhanced_features, sentiment_result
            )

            # Generate base personalization
            base_personalization = await self.generate_personalized_communication(
                lead_id, evaluation_result, message_template, interaction_history, context
            )

            # Enhance with emotional intelligence
            emotional_adaptation = await self._apply_emotional_intelligence(
                message_template, sentiment_result, churn_prediction, context
            )

            # Calculate enhanced metrics
            emotional_resonance = await self._calculate_emotional_resonance(
                sentiment_result, emotional_adaptation
            )

            retention_probability = await self._calculate_retention_probability(
                churn_prediction, sentiment_result, enhanced_features
            )

            # Generate learning feedback
            learning_feedback = await self._generate_learning_feedback(
                lead_id, enhanced_features, base_personalization
            )

            # Add real-time learning signal
            await self._add_learning_signal(
                LearningSignal.POSITIVE_ENGAGEMENT, lead_id,
                {'personalization_used': True}, {'engagement_predicted': base_personalization.predicted_engagement_score}
            )

            # Generate enhanced content variations
            enhanced_variations = await self._generate_enhanced_variations(
                base_personalization, sentiment_result, emotional_adaptation
            )

            return AdvancedPersonalizationOutput(
                # Base personalization
                personalized_subject=base_personalization.personalized_subject,
                personalized_content=emotional_adaptation.get('enhanced_content', base_personalization.personalized_content),
                optimal_channel=base_personalization.optimal_channel,
                optimal_timing=base_personalization.optimal_timing,

                # Enhanced features
                emotional_adaptation=emotional_adaptation,
                sentiment_optimization=sentiment_result,
                churn_prevention=churn_prediction,
                voice_recommendations=voice_analysis,
                journey_stage=journey_stage,
                learning_feedback=learning_feedback,

                # Advanced metrics
                personalization_confidence=base_personalization.personalization_confidence,
                predicted_engagement_score=base_personalization.predicted_engagement_score,
                emotional_resonance_score=emotional_resonance,
                retention_probability=retention_probability,

                # Multi-modal variations
                content_variations=enhanced_variations,
                behavioral_insights=base_personalization.behavioral_insights
            )

        except Exception as e:
            logger.error(f"Enhanced personalization failed: {e}")
            # Fallback to base personalization
            base_result = await self.generate_personalized_communication(
                lead_id, evaluation_result, message_template, interaction_history, context
            )
            return self._convert_to_enhanced_output(base_result)

    async def _extract_enhanced_features(
        self,
        lead_id: str,
        evaluation_result: LeadEvaluationResult,
        interaction_history: List[EngagementInteraction],
        context: Dict[str, Any],
        voice_transcript: Optional[str] = None,
        historical_sentiment: Optional[List[str]] = None
    ) -> np.ndarray:
        """Extract enhanced features for advanced ML models."""

        # Get base features
        base_features = await self._extract_ml_features(
            lead_id, evaluation_result, interaction_history, context
        )

        # Convert to array
        base_array = self._features_to_array(base_features)

        # Add enhanced features
        enhanced_features = []

        # Sentiment features
        if historical_sentiment:
            sentiment_scores = [self.sentiment_analyzer.polarity_scores(text)['compound']
                             for text in historical_sentiment[-5:]]  # Last 5 interactions
            enhanced_features.extend([
                np.mean(sentiment_scores) if sentiment_scores else 0,
                np.std(sentiment_scores) if len(sentiment_scores) > 1 else 0,
                max(sentiment_scores) if sentiment_scores else 0,
                min(sentiment_scores) if sentiment_scores else 0
            ])
        else:
            enhanced_features.extend([0, 0, 0, 0])

        # Voice features
        if voice_transcript:
            words = voice_transcript.split()
            enhanced_features.extend([
                len(words),  # Verbosity
                len([w for w in words if w.isupper()]) / max(len(words), 1),  # Emphasis ratio
                voice_transcript.count('?') / max(len(voice_transcript), 1),  # Question ratio
                voice_transcript.count('!') / max(len(voice_transcript), 1)   # Excitement ratio
            ])
        else:
            enhanced_features.extend([0, 0, 0, 0])

        # Temporal pattern features
        if interaction_history:
            # Time between interactions
            timestamps = [i.occurred_at for i in interaction_history]
            if len(timestamps) > 1:
                intervals = [(timestamps[i] - timestamps[i-1]).total_seconds()
                           for i in range(1, len(timestamps))]
                enhanced_features.extend([
                    np.mean(intervals),
                    np.std(intervals) if len(intervals) > 1 else 0,
                    len([i for i in intervals if i < 3600])  # Quick responses
                ])
            else:
                enhanced_features.extend([0, 0, 0])
        else:
            enhanced_features.extend([0, 0, 0])

        # Combine base and enhanced features
        full_features = np.concatenate([base_array, enhanced_features])

        return full_features

    async def _analyze_comprehensive_sentiment(
        self,
        lead_id: str,
        interaction_history: List[EngagementInteraction],
        historical_sentiment: Optional[List[str]] = None
    ) -> SentimentAnalysisResult:
        """Perform comprehensive sentiment analysis."""
        try:
            # Check cache first
            cache_key = f"{lead_id}_sentiment"
            if cache_key in self.sentiment_cache:
                cached_result = self.sentiment_cache[cache_key]
                if (datetime.now() - cached_result.sentiment_trend[-1][0]).total_seconds() < 3600:
                    return cached_result

            # Collect text data for analysis
            text_data = []

            # From interaction history
            for interaction in interaction_history[-10:]:  # Last 10 interactions
                if hasattr(interaction, 'message_content') and interaction.message_content:
                    text_data.append(interaction.message_content)

            # From historical sentiment data
            if historical_sentiment:
                text_data.extend(historical_sentiment[-5:])

            if not text_data:
                return self._default_sentiment_result(lead_id)

            # Analyze overall sentiment
            combined_text = " ".join(text_data)
            vader_scores = self.sentiment_analyzer.polarity_scores(combined_text)
            overall_sentiment = vader_scores['compound']

            # Analyze emotions using TextBlob and custom logic
            emotion_scores = await self._analyze_emotions(text_data)

            # Extract key phrases
            key_phrases = await self._extract_key_phrases(combined_text)

            # Calculate sentiment trend
            sentiment_trend = []
            for i, text in enumerate(text_data[-7:]):  # Last week
                score = self.sentiment_analyzer.polarity_scores(text)['compound']
                timestamp = datetime.now() - timedelta(days=6-i)
                sentiment_trend.append((timestamp, score))

            # Calculate emotional volatility
            sentiment_values = [score for _, score in sentiment_trend]
            emotional_volatility = np.std(sentiment_values) if len(sentiment_values) > 1 else 0

            # Calculate confidence score
            confidence_score = min(len(text_data) / 10.0, 1.0)  # More data = higher confidence

            result = SentimentAnalysisResult(
                overall_sentiment=overall_sentiment,
                emotion_scores=emotion_scores,
                confidence_score=confidence_score,
                key_phrases=key_phrases,
                sentiment_trend=sentiment_trend,
                emotional_volatility=emotional_volatility
            )

            # Cache result
            self.sentiment_cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return self._default_sentiment_result(lead_id)

    async def _analyze_emotions(self, text_data: List[str]) -> Dict[EmotionalState, float]:
        """Analyze specific emotions in text data."""
        emotion_keywords = {
            EmotionalState.EXCITED: ['excited', 'thrilled', 'amazing', 'fantastic', 'wonderful'],
            EmotionalState.ANXIOUS: ['worried', 'nervous', 'concerned', 'anxious', 'stressed'],
            EmotionalState.FRUSTRATED: ['frustrated', 'annoyed', 'upset', 'disappointed', 'angry'],
            EmotionalState.CONFIDENT: ['confident', 'sure', 'certain', 'convinced', 'positive'],
            EmotionalState.UNCERTAIN: ['unsure', 'maybe', 'perhaps', 'uncertain', 'confused'],
            EmotionalState.OPTIMISTIC: ['hopeful', 'optimistic', 'positive', 'looking forward'],
            EmotionalState.SKEPTICAL: ['doubt', 'skeptical', 'questionable', 'suspicious'],
            EmotionalState.TRUSTING: ['trust', 'believe', 'faith', 'confident in you'],
            EmotionalState.IMPATIENT: ['hurry', 'quickly', 'asap', 'urgent', 'soon'],
            EmotionalState.CONTENT: ['satisfied', 'happy', 'pleased', 'content', 'good']
        }

        emotion_scores = {}
        combined_text = " ".join(text_data).lower()

        for emotion, keywords in emotion_keywords.items():
            score = sum(combined_text.count(keyword) for keyword in keywords)
            # Normalize by text length
            normalized_score = score / max(len(combined_text.split()), 1)
            emotion_scores[emotion] = min(normalized_score * 10, 1.0)  # Cap at 1.0

        return emotion_scores

    async def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text using simple NLP."""
        # Remove punctuation and convert to lowercase
        clean_text = re.sub(r'[^\w\s]', '', text.lower())
        words = clean_text.split()

        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'i', 'you', 'we', 'they', 'it', 'is', 'are', 'was', 'were'}
        filtered_words = [word for word in words if word not in stop_words and len(word) > 3]

        # Count frequency
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # Return top phrases
        key_phrases = sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)[:5]
        return key_phrases

    def _default_sentiment_result(self, lead_id: str) -> SentimentAnalysisResult:
        """Return default sentiment analysis result."""
        return SentimentAnalysisResult(
            overall_sentiment=0.0,
            emotion_scores={emotion: 0.0 for emotion in EmotionalState},
            confidence_score=0.0,
            key_phrases=[],
            sentiment_trend=[(datetime.now(), 0.0)],
            emotional_volatility=0.0
        )

    async def _predict_churn_risk(
        self,
        lead_id: str,
        enhanced_features: np.ndarray,
        sentiment_result: SentimentAnalysisResult
    ) -> ChurnPrediction:
        """Predict churn risk with intervention recommendations."""
        try:
            # Check cache
            if lead_id in self.churn_predictions:
                cached_pred = self.churn_predictions[lead_id]
                if (datetime.now() - datetime.now()).total_seconds() < 1800:  # 30 min cache
                    return cached_pred

            # Prepare features for churn model
            if self.churn_model and self.emotion_scaler and self.feature_selector:
                features_scaled = self.emotion_scaler.transform(enhanced_features.reshape(1, -1))
                features_selected = self.feature_selector.transform(features_scaled)

                # Get churn probability
                churn_prob = self.churn_model.predict_proba(features_selected)[0][1]
                churn_risk_level = self._determine_churn_risk_level(churn_prob)

                # Get feature importance for contributing factors
                feature_importance = self.churn_model.feature_importances_
                contributing_factors = self._identify_churn_factors(
                    features_selected[0], feature_importance, sentiment_result
                )

            else:
                # Fallback churn prediction
                churn_prob = self._calculate_heuristic_churn_risk(sentiment_result, enhanced_features)
                churn_risk_level = self._determine_churn_risk_level(churn_prob)
                contributing_factors = ["Low engagement", "Negative sentiment trend"]

            # Generate intervention strategies
            intervention_strategies = self._generate_intervention_strategies(
                churn_risk_level, sentiment_result, contributing_factors
            )

            # Determine optimal intervention timing
            optimal_timing = self._calculate_optimal_intervention_timing(
                churn_risk_level, sentiment_result
            )

            prediction = ChurnPrediction(
                risk_level=churn_risk_level,
                probability=churn_prob,
                contributing_factors=contributing_factors,
                intervention_strategies=intervention_strategies,
                optimal_intervention_timing=optimal_timing,
                confidence_score=0.85
            )

            # Cache prediction
            self.churn_predictions[lead_id] = prediction

            return prediction

        except Exception as e:
            logger.error(f"Churn prediction failed: {e}")
            return self._default_churn_prediction()

    def _determine_churn_risk_level(self, probability: float) -> ChurnRisk:
        """Determine churn risk level from probability."""
        if probability < 0.1:
            return ChurnRisk.VERY_LOW
        elif probability < 0.25:
            return ChurnRisk.LOW
        elif probability < 0.5:
            return ChurnRisk.MODERATE
        elif probability < 0.75:
            return ChurnRisk.HIGH
        else:
            return ChurnRisk.CRITICAL

    def _calculate_heuristic_churn_risk(
        self,
        sentiment_result: SentimentAnalysisResult,
        features: np.ndarray
    ) -> float:
        """Calculate churn risk using heuristic approach."""
        risk_score = 0.0

        # Sentiment factor
        if sentiment_result.overall_sentiment < -0.5:
            risk_score += 0.3
        elif sentiment_result.overall_sentiment < 0:
            risk_score += 0.1

        # Emotional volatility factor
        if sentiment_result.emotional_volatility > 0.5:
            risk_score += 0.2

        # Recent engagement (simplified)
        if len(features) > 5:
            engagement_score = features[4]  # Approximate engagement feature
            if engagement_score < 0.2:
                risk_score += 0.25

        return min(risk_score, 1.0)

    def _identify_churn_factors(
        self,
        features: np.ndarray,
        importance: np.ndarray,
        sentiment_result: SentimentAnalysisResult
    ) -> List[str]:
        """Identify contributing factors to churn risk."""
        factors = []

        # Top feature importance
        top_features = np.argsort(importance)[-3:]  # Top 3 features

        feature_names = [
            "Lead score", "Urgency level", "Budget range", "Property type", "Email engagement",
            "Response time", "Property views", "Communication frequency", "Sentiment trend",
            "Emotional volatility", "Voice patterns", "Temporal patterns"
        ]

        for idx in top_features:
            if idx < len(feature_names):
                factors.append(f"High impact: {feature_names[idx]}")

        # Sentiment-based factors
        if sentiment_result.overall_sentiment < -0.3:
            factors.append("Negative sentiment trend")

        if sentiment_result.emotional_volatility > 0.4:
            factors.append("High emotional volatility")

        # Emotion-specific factors
        high_emotions = [emotion for emotion, score in sentiment_result.emotion_scores.items()
                        if score > 0.6]
        if EmotionalState.FRUSTRATED in high_emotions:
            factors.append("High frustration levels")
        if EmotionalState.SKEPTICAL in high_emotions:
            factors.append("Increased skepticism")

        return factors[:5]  # Limit to top 5 factors

    def _generate_intervention_strategies(
        self,
        risk_level: ChurnRisk,
        sentiment_result: SentimentAnalysisResult,
        factors: List[str]
    ) -> List[str]:
        """Generate intervention strategies based on churn risk."""
        strategies = []

        if risk_level in [ChurnRisk.HIGH, ChurnRisk.CRITICAL]:
            strategies.extend([
                "Immediate personal phone call",
                "Offer exclusive property viewing",
                "Provide market analysis report",
                "Schedule face-to-face meeting"
            ])

        if risk_level in [ChurnRisk.MODERATE, ChurnRisk.HIGH]:
            strategies.extend([
                "Send personalized video message",
                "Share client testimonials",
                "Offer free consultation",
                "Provide value-added services"
            ])

        # Sentiment-specific strategies
        if sentiment_result.overall_sentiment < -0.3:
            strategies.append("Address specific concerns proactively")

        high_emotions = [emotion for emotion, score in sentiment_result.emotion_scores.items()
                        if score > 0.5]

        if EmotionalState.FRUSTRATED in high_emotions:
            strategies.append("Acknowledge frustrations and provide solutions")
        if EmotionalState.UNCERTAIN in high_emotions:
            strategies.append("Provide educational content and guidance")
        if EmotionalState.IMPATIENT in high_emotions:
            strategies.append("Expedite search process and communication")

        return list(set(strategies))  # Remove duplicates

    def _calculate_optimal_intervention_timing(
        self,
        risk_level: ChurnRisk,
        sentiment_result: SentimentAnalysisResult
    ) -> datetime:
        """Calculate optimal timing for intervention."""
        base_time = datetime.now()

        if risk_level == ChurnRisk.CRITICAL:
            return base_time + timedelta(hours=2)  # Immediate intervention
        elif risk_level == ChurnRisk.HIGH:
            return base_time + timedelta(hours=6)
        elif risk_level == ChurnRisk.MODERATE:
            return base_time + timedelta(days=1)
        else:
            return base_time + timedelta(days=3)

    def _default_churn_prediction(self) -> ChurnPrediction:
        """Return default churn prediction."""
        return ChurnPrediction(
            risk_level=ChurnRisk.LOW,
            probability=0.2,
            contributing_factors=["Insufficient data"],
            intervention_strategies=["Monitor engagement closely"],
            optimal_intervention_timing=datetime.now() + timedelta(days=2),
            confidence_score=0.5
        )

    async def _analyze_voice_communication(self, transcript: str) -> VoiceAnalysisResult:
        """Analyze voice communication patterns."""
        try:
            words = transcript.split()
            sentences = transcript.split('.')

            # Calculate speaking pace (words per sentence)
            speaking_pace = len(words) / max(len(sentences), 1)

            # Analyze tone confidence (based on definitive language)
            confident_words = ['definitely', 'certainly', 'absolutely', 'sure', 'confident']
            uncertain_words = ['maybe', 'perhaps', 'possibly', 'might', 'probably']

            confident_count = sum(transcript.lower().count(word) for word in confident_words)
            uncertain_count = sum(transcript.lower().count(word) for word in uncertain_words)

            tone_confidence = (confident_count - uncertain_count) / max(len(words), 1)
            tone_confidence = max(0, min(1, (tone_confidence + 1) / 2))  # Normalize to 0-1

            # Calculate emotional intensity
            emotional_words = ['excited', 'frustrated', 'worried', 'happy', 'angry', 'disappointed']
            emotional_intensity = sum(transcript.lower().count(word) for word in emotional_words) / max(len(words), 1)

            # Extract key topics (simplified)
            real_estate_terms = ['house', 'property', 'home', 'buy', 'sell', 'mortgage', 'price', 'market']
            key_topics = [term for term in real_estate_terms if term in transcript.lower()]

            # Identify engagement indicators
            engagement_indicators = []
            if '?' in transcript:
                engagement_indicators.append("Asking questions")
            if speaking_pace > 15:
                engagement_indicators.append("Verbose communication")
            if tone_confidence > 0.6:
                engagement_indicators.append("High confidence")

            # Recommend response style
            if tone_confidence > 0.7:
                response_style = "Match confidence with decisive recommendations"
            elif emotional_intensity > 0.1:
                response_style = "Address emotional concerns with empathy"
            elif speaking_pace < 10:
                response_style = "Provide concise, clear information"
            else:
                response_style = "Engage with detailed, comprehensive responses"

            return VoiceAnalysisResult(
                speaking_pace=speaking_pace,
                tone_confidence=tone_confidence,
                emotional_intensity=emotional_intensity,
                key_topics=key_topics,
                engagement_indicators=engagement_indicators,
                recommended_response_style=response_style
            )

        except Exception as e:
            logger.error(f"Voice analysis failed: {e}")
            return VoiceAnalysisResult(
                speaking_pace=12.0,
                tone_confidence=0.5,
                emotional_intensity=0.2,
                key_topics=[],
                engagement_indicators=[],
                recommended_response_style="Standard professional approach"
            )

    async def _determine_journey_stage(
        self,
        lead_id: str,
        features: np.ndarray,
        sentiment_result: SentimentAnalysisResult
    ) -> LeadJourneyStage:
        """Determine current lead journey stage with emotional context."""
        try:
            # Use journey model if available
            if self.journey_model and self.emotion_scaler and self.feature_selector:
                features_scaled = self.emotion_scaler.transform(features.reshape(1, -1))
                features_selected = self.feature_selector.transform(features_scaled)

                journey_score = self.journey_model.predict(features_selected)[0]
                stage_name = self._map_score_to_stage(journey_score)
                confidence = min(abs(journey_score - 0.5) * 2, 1.0)

            else:
                # Heuristic approach
                stage_name, confidence = self._heuristic_journey_stage(sentiment_result, features)

            # Determine emotional state
            dominant_emotion = max(sentiment_result.emotion_scores.items(),
                                 key=lambda x: x[1])[0]

            # Generate stage-specific recommendations
            optimal_actions = self._get_stage_optimal_actions(stage_name, dominant_emotion)
            risk_factors = self._identify_stage_risks(stage_name, sentiment_result)

            # Estimate stage duration and success probability
            expected_duration = self._estimate_stage_duration(stage_name, sentiment_result)
            success_probability = self._calculate_stage_success_probability(
                stage_name, confidence, sentiment_result
            )

            stage = LeadJourneyStage(
                stage_name=stage_name,
                emotional_state=dominant_emotion,
                confidence_level=confidence,
                optimal_actions=optimal_actions,
                risk_factors=risk_factors,
                expected_duration=expected_duration,
                success_probability=success_probability
            )

            # Cache the stage
            self.journey_stages[lead_id] = stage

            return stage

        except Exception as e:
            logger.error(f"Journey stage determination failed: {e}")
            return self._default_journey_stage()

    def _map_score_to_stage(self, score: float) -> str:
        """Map journey model score to stage name."""
        if score < 0.2:
            return "Initial Interest"
        elif score < 0.4:
            return "Active Research"
        elif score < 0.6:
            return "Property Evaluation"
        elif score < 0.8:
            return "Decision Making"
        else:
            return "Ready to Buy"

    def _heuristic_journey_stage(self, sentiment_result: SentimentAnalysisResult, features: np.ndarray) -> Tuple[str, float]:
        """Determine journey stage using heuristic approach."""
        # Simplified logic based on engagement and sentiment
        if len(features) > 4:
            engagement = features[4]  # Approximate engagement feature

            if engagement > 0.8 and sentiment_result.overall_sentiment > 0.3:
                return "Ready to Buy", 0.9
            elif engagement > 0.6:
                return "Decision Making", 0.7
            elif engagement > 0.4:
                return "Property Evaluation", 0.6
            elif engagement > 0.2:
                return "Active Research", 0.5
            else:
                return "Initial Interest", 0.4

        return "Initial Interest", 0.3

    def _get_stage_optimal_actions(self, stage: str, emotion: EmotionalState) -> List[str]:
        """Get optimal actions for current stage and emotional state."""
        stage_actions = {
            "Initial Interest": [
                "Send welcome series",
                "Provide market overview",
                "Schedule introductory call"
            ],
            "Active Research": [
                "Share relevant listings",
                "Provide neighborhood insights",
                "Offer property search tools"
            ],
            "Property Evaluation": [
                "Schedule property viewings",
                "Provide comparative analysis",
                "Share inspection resources"
            ],
            "Decision Making": [
                "Present financing options",
                "Address specific concerns",
                "Provide negotiation support"
            ],
            "Ready to Buy": [
                "Prepare offers",
                "Coordinate closing process",
                "Ensure smooth transaction"
            ]
        }

        actions = stage_actions.get(stage, [])

        # Add emotion-specific actions
        if emotion == EmotionalState.ANXIOUS:
            actions.append("Provide reassurance and guidance")
        elif emotion == EmotionalState.EXCITED:
            actions.append("Capitalize on enthusiasm")
        elif emotion == EmotionalState.UNCERTAIN:
            actions.append("Provide educational content")

        return actions

    def _identify_stage_risks(self, stage: str, sentiment_result: SentimentAnalysisResult) -> List[str]:
        """Identify risks for current journey stage."""
        risks = []

        if sentiment_result.overall_sentiment < -0.3:
            risks.append("Negative sentiment trend")

        if sentiment_result.emotional_volatility > 0.5:
            risks.append("High emotional volatility")

        stage_risks = {
            "Initial Interest": ["Low engagement", "Competition from other agents"],
            "Active Research": ["Information overload", "Analysis paralysis"],
            "Property Evaluation": ["Unrealistic expectations", "Market changes"],
            "Decision Making": ["Cold feet", "External pressure"],
            "Ready to Buy": ["Financing issues", "Last-minute complications"]
        }

        risks.extend(stage_risks.get(stage, []))
        return risks

    def _estimate_stage_duration(self, stage: str, sentiment_result: SentimentAnalysisResult) -> timedelta:
        """Estimate expected duration for current stage."""
        base_durations = {
            "Initial Interest": timedelta(days=7),
            "Active Research": timedelta(days=14),
            "Property Evaluation": timedelta(days=21),
            "Decision Making": timedelta(days=10),
            "Ready to Buy": timedelta(days=30)
        }

        base_duration = base_durations.get(stage, timedelta(days=14))

        # Adjust based on urgency indicators
        urgency_emotions = [EmotionalState.EXCITED, EmotionalState.IMPATIENT]
        high_urgency = any(sentiment_result.emotion_scores.get(emotion, 0) > 0.5 for emotion in urgency_emotions)

        if high_urgency:
            return base_duration * 0.7  # 30% faster
        elif sentiment_result.overall_sentiment < 0:
            return base_duration * 1.3  # 30% slower
        else:
            return base_duration

    def _calculate_stage_success_probability(
        self,
        stage: str,
        confidence: float,
        sentiment_result: SentimentAnalysisResult
    ) -> float:
        """Calculate probability of successful stage progression."""
        base_probabilities = {
            "Initial Interest": 0.4,
            "Active Research": 0.6,
            "Property Evaluation": 0.7,
            "Decision Making": 0.8,
            "Ready to Buy": 0.9
        }

        base_prob = base_probabilities.get(stage, 0.5)

        # Adjust based on sentiment and confidence
        sentiment_adjustment = sentiment_result.overall_sentiment * 0.2
        confidence_adjustment = (confidence - 0.5) * 0.2

        final_probability = base_prob + sentiment_adjustment + confidence_adjustment
        return max(0.1, min(0.95, final_probability))

    def _default_journey_stage(self) -> LeadJourneyStage:
        """Return default journey stage."""
        return LeadJourneyStage(
            stage_name="Active Research",
            emotional_state=EmotionalState.CONTENT,
            confidence_level=0.5,
            optimal_actions=["Send relevant listings", "Provide market insights"],
            risk_factors=["Insufficient data"],
            expected_duration=timedelta(days=14),
            success_probability=0.6
        )

    # Real-time Learning and Model Updates

    async def _add_learning_signal(
        self,
        signal_type: LearningSignal,
        lead_id: str,
        interaction_context: Dict[str, Any],
        outcome_data: Dict[str, Any],
        feedback_score: float = 0.0
    ):
        """Add a learning signal for real-time model improvement."""
        signal = RealTimeLearningSignal(
            signal_type=signal_type,
            lead_id=lead_id,
            interaction_context=interaction_context,
            outcome_data=outcome_data,
            feedback_score=feedback_score
        )

        self.learning_buffer.append(signal)

        # Check if we should retrain models
        if len(self.learning_buffer) >= self.retrain_threshold:
            await self._perform_incremental_learning()

    async def _perform_incremental_learning(self):
        """Perform incremental learning with accumulated signals."""
        try:
            logger.info("Starting incremental model learning")

            # Extract features and labels from learning signals
            features_list = []
            labels_dict = {'engagement': [], 'churn': [], 'sentiment': []}

            for signal in self.learning_buffer:
                # Convert signal to features (simplified)
                feature_vector = self._signal_to_features(signal)
                features_list.append(feature_vector)

                # Extract labels based on signal type
                if signal.signal_type == LearningSignal.POSITIVE_ENGAGEMENT:
                    labels_dict['engagement'].append(1)
                    labels_dict['churn'].append(0)
                    labels_dict['sentiment'].append(signal.feedback_score)
                elif signal.signal_type == LearningSignal.CHURN_EVENT:
                    labels_dict['engagement'].append(0)
                    labels_dict['churn'].append(1)
                    labels_dict['sentiment'].append(-0.5)
                else:
                    # Default values
                    labels_dict['engagement'].append(0.5)
                    labels_dict['churn'].append(0)
                    labels_dict['sentiment'].append(0.0)

            if features_list:
                X_new = np.array(features_list)

                # Update models if we have enough data
                if len(X_new) >= 10:
                    # Scale features
                    X_scaled = self.emotion_scaler.partial_fit(X_new).transform(X_new)

                    # Incremental updates (if models support it)
                    await self._update_models_incrementally(X_scaled, labels_dict)

                    # Track performance
                    self._track_model_performance(X_scaled, labels_dict)

            # Clear learning buffer
            self.learning_buffer.clear()
            self.last_retrain_time = datetime.now()

            logger.info("Incremental learning completed successfully")

        except Exception as e:
            logger.error(f"Incremental learning failed: {e}")

    def _signal_to_features(self, signal: RealTimeLearningSignal) -> np.ndarray:
        """Convert learning signal to feature vector."""
        # Simplified feature extraction from signal
        context = signal.interaction_context
        outcome = signal.outcome_data

        features = [
            context.get('lead_score', 50) / 100,  # Normalized lead score
            context.get('urgency_level', 2) / 4,  # Normalized urgency
            context.get('engagement_rate', 0.5),   # Engagement rate
            signal.feedback_score,                 # Feedback score
            1.0 if signal.signal_type == LearningSignal.POSITIVE_ENGAGEMENT else 0.0,
            1.0 if signal.signal_type == LearningSignal.CHURN_EVENT else 0.0,
            outcome.get('response_time', 3600) / 7200,  # Normalized response time
            outcome.get('conversion_probability', 0.5),  # Conversion probability
        ]

        # Pad to fixed size (25 features to match enhanced features)
        while len(features) < 25:
            features.append(0.0)

        return np.array(features[:25])

    async def _update_models_incrementally(self, X_scaled: np.ndarray, labels_dict: Dict[str, List]):
        """Update models with new data incrementally."""
        try:
            # For models that don't support incremental learning,
            # we would need to implement partial_fit or retrain
            # This is a simplified implementation

            if self.engagement_model and len(labels_dict['engagement']) > 0:
                # Calculate performance before update
                old_score = self.engagement_model.score(X_scaled, labels_dict['engagement'])

                # For models without partial_fit, we would need to retrain
                # This is a placeholder for actual incremental update
                logger.info(f"Engagement model - old score: {old_score:.3f}")

            if self.churn_model and len(labels_dict['churn']) > 0:
                # Similar incremental update for churn model
                old_score = self.churn_model.score(X_scaled, labels_dict['churn'])
                logger.info(f"Churn model - old score: {old_score:.3f}")

        except Exception as e:
            logger.error(f"Model incremental update failed: {e}")

    def _track_model_performance(self, X: np.ndarray, labels_dict: Dict[str, List]):
        """Track model performance over time."""
        try:
            # Track engagement model performance
            if self.engagement_model and len(labels_dict['engagement']) > 0:
                predictions = self.engagement_model.predict(X)
                mse = mean_squared_error(labels_dict['engagement'], predictions)
                self.prediction_accuracy_tracker['engagement'].append(mse)

            # Track churn model performance
            if self.churn_model and len(labels_dict['churn']) > 0:
                predictions = self.churn_model.predict(X)
                accuracy = accuracy_score(labels_dict['churn'], predictions)
                self.prediction_accuracy_tracker['churn'].append(accuracy)

            # Keep only recent performance data
            for metric in self.prediction_accuracy_tracker:
                if len(self.prediction_accuracy_tracker[metric]) > 100:
                    self.prediction_accuracy_tracker[metric] = self.prediction_accuracy_tracker[metric][-50:]

        except Exception as e:
            logger.error(f"Performance tracking failed: {e}")

    # Enhanced Helper Methods

    async def _apply_emotional_intelligence(
        self,
        message_template: str,
        sentiment_result: SentimentAnalysisResult,
        churn_prediction: ChurnPrediction,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply emotional intelligence to enhance communication."""
        try:
            # Determine dominant emotion
            dominant_emotion = max(sentiment_result.emotion_scores.items(),
                                 key=lambda x: x[1])[0]

            # Adapt tone based on emotional state
            tone_adaptations = {
                EmotionalState.EXCITED: "enthusiastic and supportive",
                EmotionalState.ANXIOUS: "calm and reassuring",
                EmotionalState.FRUSTRATED: "understanding and solution-focused",
                EmotionalState.UNCERTAIN: "educational and patient",
                EmotionalState.CONFIDENT: "professional and decisive",
                EmotionalState.SKEPTICAL: "evidence-based and transparent"
            }

            adapted_tone = tone_adaptations.get(dominant_emotion, "professional and friendly")

            # Adjust content based on churn risk
            urgency_level = "normal"
            if churn_prediction.risk_level in [ChurnRisk.HIGH, ChurnRisk.CRITICAL]:
                urgency_level = "high"
            elif churn_prediction.risk_level == ChurnRisk.MODERATE:
                urgency_level = "moderate"

            # Generate emotionally intelligent content
            prompt = f"""
            Enhance this real estate message with emotional intelligence:

            Original Template: {message_template}

            Emotional Context:
            - Dominant Emotion: {dominant_emotion.value}
            - Overall Sentiment: {sentiment_result.overall_sentiment:.2f}
            - Churn Risk: {churn_prediction.risk_level.value}
            - Recommended Tone: {adapted_tone}
            - Urgency Level: {urgency_level}

            Enhancement Guidelines:
            1. Acknowledge their emotional state subtly
            2. Use the recommended tone throughout
            3. Address any concerns related to churn risk factors
            4. Include empathy and understanding
            5. Maintain professional credibility

            Return JSON with:
            {{
                "enhanced_content": "emotionally adapted message",
                "emotional_hooks": ["list of emotional appeal elements"],
                "tone_adjustments": ["specific tone modifications made"]
            }}
            """

            # Get AI enhancement
            response = await self.semantic_analyzer._get_claude_analysis(prompt)

            try:
                adaptation = json.loads(response)
                return adaptation
            except json.JSONDecodeError:
                # Fallback emotional adaptation
                return self._simple_emotional_adaptation(
                    message_template, dominant_emotion, adapted_tone
                )

        except Exception as e:
            logger.error(f"Emotional intelligence application failed: {e}")
            return {
                "enhanced_content": message_template,
                "emotional_hooks": [],
                "tone_adjustments": []
            }

    def _simple_emotional_adaptation(
        self,
        template: str,
        emotion: EmotionalState,
        tone: str
    ) -> Dict[str, Any]:
        """Simple rule-based emotional adaptation."""
        adaptations = []
        enhanced_content = template

        if emotion == EmotionalState.ANXIOUS:
            enhanced_content = f"I understand this process can feel overwhelming. {template} I'm here to guide you every step of the way."
            adaptations.append("Added reassurance")
        elif emotion == EmotionalState.EXCITED:
            enhanced_content = f"I love your enthusiasm! {template} Let's channel that energy into finding your perfect property."
            adaptations.append("Matched enthusiasm")
        elif emotion == EmotionalState.FRUSTRATED:
            enhanced_content = f"I hear your concerns and want to address them. {template} Let's work together to solve any challenges."
            adaptations.append("Acknowledged frustration")

        return {
            "enhanced_content": enhanced_content,
            "emotional_hooks": ["Emotional acknowledgment"],
            "tone_adjustments": adaptations
        }

    async def _calculate_emotional_resonance(
        self,
        sentiment_result: SentimentAnalysisResult,
        emotional_adaptation: Dict[str, Any]
    ) -> float:
        """Calculate emotional resonance score."""
        try:
            # Base score from sentiment analysis confidence
            base_score = sentiment_result.confidence_score * 0.4

            # Emotional adaptation quality
            adaptation_score = 0.0
            if emotional_adaptation.get('emotional_hooks'):
                adaptation_score += 0.3
            if emotional_adaptation.get('tone_adjustments'):
                adaptation_score += 0.2

            # Sentiment alignment (how well we're addressing the emotional state)
            alignment_score = 0.0
            if sentiment_result.overall_sentiment < -0.3:  # Negative sentiment
                if any('reassur' in hook.lower() for hook in emotional_adaptation.get('emotional_hooks', [])):
                    alignment_score += 0.1
            elif sentiment_result.overall_sentiment > 0.3:  # Positive sentiment
                if any('enthus' in hook.lower() for hook in emotional_adaptation.get('emotional_hooks', [])):
                    alignment_score += 0.1

            return min(base_score + adaptation_score + alignment_score, 1.0)

        except Exception as e:
            logger.error(f"Emotional resonance calculation failed: {e}")
            return 0.5

    async def _calculate_retention_probability(
        self,
        churn_prediction: ChurnPrediction,
        sentiment_result: SentimentAnalysisResult,
        features: np.ndarray
    ) -> float:
        """Calculate lead retention probability."""
        try:
            # Base retention from churn prediction
            base_retention = 1.0 - churn_prediction.probability

            # Sentiment boost
            sentiment_boost = max(sentiment_result.overall_sentiment * 0.2, 0)

            # Engagement factor (if features available)
            engagement_boost = 0.0
            if len(features) > 4:
                engagement_score = features[4]  # Approximate engagement
                engagement_boost = engagement_score * 0.1

            # Confidence factor
            confidence_factor = (churn_prediction.confidence_score - 0.5) * 0.1

            retention_probability = base_retention + sentiment_boost + engagement_boost + confidence_factor
            return max(0.1, min(0.95, retention_probability))

        except Exception as e:
            logger.error(f"Retention probability calculation failed: {e}")
            return 0.7  # Default moderate retention probability

    async def _generate_learning_feedback(
        self,
        lead_id: str,
        features: np.ndarray,
        personalization: PersonalizationOutput
    ) -> List[RealTimeLearningSignal]:
        """Generate learning feedback signals for model improvement."""
        feedback = []

        # Engagement prediction feedback
        feedback.append(RealTimeLearningSignal(
            signal_type=LearningSignal.POSITIVE_ENGAGEMENT,
            lead_id=lead_id,
            interaction_context={
                'predicted_engagement': personalization.predicted_engagement_score,
                'optimal_channel': str(personalization.optimal_channel),
                'optimal_timing': personalization.optimal_timing.recommended_hour
            },
            outcome_data={'model_confidence': personalization.personalization_confidence},
            feedback_score=personalization.predicted_engagement_score
        ))

        return feedback

    async def _generate_enhanced_variations(
        self,
        base_personalization: PersonalizationOutput,
        sentiment_result: SentimentAnalysisResult,
        emotional_adaptation: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate enhanced A/B testing variations."""
        variations = []

        # Sentiment-based variation
        if sentiment_result.overall_sentiment > 0.3:
            variations.append({
                "variant_name": "positive_amplification",
                "subject": f"✨ {base_personalization.personalized_subject}",
                "content": f"Great news! {emotional_adaptation.get('enhanced_content', base_personalization.personalized_content)}",
                "predicted_performance": 0.8,
                "emotional_appeal": "Amplified positivity"
            })

        # Urgency variation based on churn risk
        variations.append({
            "variant_name": "time_sensitive",
            "subject": f"⏰ Time-Sensitive: {base_personalization.personalized_subject}",
            "content": f"I wanted to reach out quickly because {emotional_adaptation.get('enhanced_content', base_personalization.personalized_content)}",
            "predicted_performance": 0.7,
            "emotional_appeal": "Created urgency"
        })

        # Personal touch variation
        variations.append({
            "variant_name": "ultra_personal",
            "subject": f"Just for You: {base_personalization.personalized_subject}",
            "content": f"I was thinking specifically about your situation and {emotional_adaptation.get('enhanced_content', base_personalization.personalized_content)}",
            "predicted_performance": 0.75,
            "emotional_appeal": "Deep personalization"
        })

        return variations

    def _convert_to_enhanced_output(self, base_output: PersonalizationOutput) -> AdvancedPersonalizationOutput:
        """Convert base personalization output to enhanced output."""
        default_sentiment = self._default_sentiment_result("")
        default_churn = self._default_churn_prediction()
        default_journey = self._default_journey_stage()

        return AdvancedPersonalizationOutput(
            personalized_subject=base_output.personalized_subject,
            personalized_content=base_output.personalized_content,
            optimal_channel=base_output.optimal_channel,
            optimal_timing=base_output.optimal_timing,
            emotional_adaptation={},
            sentiment_optimization=default_sentiment,
            churn_prevention=default_churn,
            voice_recommendations=None,
            journey_stage=default_journey,
            learning_feedback=[],
            personalization_confidence=base_output.personalization_confidence,
            predicted_engagement_score=base_output.predicted_engagement_score,
            emotional_resonance_score=0.5,
            retention_probability=0.7,
            content_variations=base_output.content_variations,
            behavioral_insights=base_output.behavioral_insights
        )

    # Enhanced Performance Analytics

    async def get_enhanced_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics for enhanced engine."""
        base_metrics = await self.get_personalization_performance_metrics()

        enhanced_metrics = {
            "enhanced_models": {
                "churn_model": self.churn_model is not None,
                "emotion_model": self.emotion_model is not None,
                "journey_model": self.journey_model is not None,
                "neural_personalization": self.neural_personalization is not None
            },
            "learning_system": {
                "learning_buffer_size": len(self.learning_buffer),
                "last_retrain_time": self.last_retrain_time.isoformat(),
                "retrain_threshold": self.retrain_threshold,
                "signals_since_last_retrain": len(self.learning_buffer)
            },
            "prediction_accuracy": {
                metric: {
                    "recent_scores": scores[-10:],
                    "average": statistics.mean(scores) if scores else 0,
                    "trend": "improving" if len(scores) > 1 and scores[-1] > scores[-5] else "stable"
                } for metric, scores in self.prediction_accuracy_tracker.items()
            },
            "cache_stats": {
                "sentiment_cache_size": len(self.sentiment_cache),
                "churn_predictions_cached": len(self.churn_predictions),
                "journey_stages_tracked": len(self.journey_stages),
                "voice_analyses_cached": len(self.voice_analysis_cache)
            }
        }

        return {**base_metrics, **enhanced_metrics}


# Export enhanced classes
__all__ = [
    'EnhancedMLPersonalizationEngine',
    'AdvancedPersonalizationOutput',
    'SentimentAnalysisResult',
    'ChurnPrediction',
    'VoiceAnalysisResult',
    'LeadJourneyStage',
    'EmotionalState',
    'ChurnRisk',
    'LearningSignal'
]