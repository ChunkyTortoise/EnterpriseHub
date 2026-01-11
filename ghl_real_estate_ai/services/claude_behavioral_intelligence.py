"""
Claude-Enhanced Behavioral Intelligence Engine

Advanced behavioral prediction system that combines ML models with Claude's
semantic understanding to predict lead behavior, conversion likelihood,
and optimal engagement strategies.

Features:
- ML + Claude ensemble predictions
- Behavioral pattern analysis with semantic understanding
- Predictive lead journey mapping
- Dynamic risk assessment
- Personalized engagement optimization
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json

from anthropic import AsyncAnthropic
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
import joblib

from ..ghl_utils.config import settings
from .claude_semantic_analyzer import ClaudeSemanticAnalyzer
from .redis_conversation_service import redis_conversation_service

logger = logging.getLogger(__name__)


class BehaviorPredictionType(Enum):
    """Types of behavioral predictions."""
    CONVERSION_LIKELIHOOD = "conversion_likelihood"
    CHURN_RISK = "churn_risk"
    ENGAGEMENT_RECEPTIVITY = "engagement_receptivity"
    OBJECTION_PROBABILITY = "objection_probability"
    APPOINTMENT_READINESS = "appointment_readiness"
    BUYING_URGENCY = "buying_urgency"


class ConversionStage(Enum):
    """Lead conversion stages."""
    AWARENESS = "awareness"
    INTEREST = "interest"
    CONSIDERATION = "consideration"
    INTENT = "intent"
    EVALUATION = "evaluation"
    PURCHASE = "purchase"


@dataclass
class BehavioralSignal:
    """Individual behavioral signal."""
    signal_type: str
    value: float
    confidence: float
    timestamp: datetime
    source: str  # "ml_model", "claude_analysis", "interaction"
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class BehavioralProfile:
    """Complete behavioral profile for a lead."""
    lead_id: str
    conversion_probability: float
    current_stage: ConversionStage
    churn_risk_score: float
    engagement_score: float
    behavioral_signals: List[BehavioralSignal]
    claude_insights: Dict[str, Any]
    ml_features: Dict[str, float]
    prediction_confidence: float
    last_updated: datetime
    next_optimal_contact: Optional[datetime] = None


@dataclass
class PredictionResult:
    """Result of behavioral prediction."""
    prediction_type: BehaviorPredictionType
    score: float
    confidence: float
    contributing_factors: List[str]
    claude_reasoning: str
    ml_features: Dict[str, float]
    recommended_actions: List[str]
    risk_factors: List[str]
    opportunities: List[str]


class ClaudeBehavioralIntelligence:
    """
    Advanced behavioral intelligence engine combining ML and Claude AI.

    Provides comprehensive lead behavior prediction, conversion forecasting,
    and personalized engagement optimization using ensemble methods.
    """

    def __init__(self):
        self.claude_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.semantic_analyzer = ClaudeSemanticAnalyzer()
        self.redis_service = redis_conversation_service

        # ML Models
        self.conversion_model = None
        self.churn_model = None
        self.engagement_model = None
        self.scaler = StandardScaler()

        # Behavioral pattern templates
        self.behavior_patterns = self._load_behavior_patterns()

        # Initialize models
        asyncio.create_task(self._initialize_ml_models())

    async def _initialize_ml_models(self):
        """Initialize and train ML models for behavioral prediction."""
        try:
            # Generate synthetic training data (in production, use historical data)
            training_data = await self._generate_training_data()

            # Train conversion prediction model
            X_conv, y_conv = training_data['conversion']
            self.conversion_model = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            )
            self.conversion_model.fit(X_conv, y_conv)

            # Train churn prediction model
            X_churn, y_churn = training_data['churn']
            self.churn_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=8,
                random_state=42
            )
            self.churn_model.fit(X_churn, y_churn)

            # Train engagement model
            X_eng, y_eng = training_data['engagement']
            self.engagement_model = GradientBoostingClassifier(
                n_estimators=80,
                learning_rate=0.15,
                max_depth=5,
                random_state=42
            )
            self.engagement_model.fit(X_eng, y_eng)

            logger.info("ML models initialized for behavioral intelligence")

        except Exception as e:
            logger.error(f"Error initializing ML models: {e}")

    async def _generate_training_data(self) -> Dict[str, Tuple]:
        """Generate training data for ML models (replace with real data in production)."""
        # This would be replaced with actual historical data
        np.random.seed(42)
        n_samples = 1000

        # Features: engagement_score, days_since_first_contact, response_rate,
        # qualification_completeness, conversation_sentiment, page_views, property_views
        features = np.random.rand(n_samples, 7)

        # Conversion labels (simulate realistic patterns)
        conversion_labels = (
            (features[:, 0] * 0.3) +  # engagement_score
            (features[:, 3] * 0.4) +  # qualification_completeness
            (features[:, 4] * 0.2) +  # conversation_sentiment
            np.random.normal(0, 0.1, n_samples) > 0.5
        ).astype(int)

        # Churn labels (inverse relationship)
        churn_labels = (
            (1 - features[:, 0] * 0.4) +  # low engagement
            (features[:, 1] * 0.3) +      # long time since contact
            (1 - features[:, 2] * 0.3) +  # low response rate
            np.random.normal(0, 0.1, n_samples) > 0.6
        ).astype(int)

        # Engagement labels
        engagement_labels = (
            (features[:, 0] * 0.5) +      # current engagement
            (features[:, 4] * 0.3) +      # sentiment
            (features[:, 6] * 0.2) +      # property views
            np.random.normal(0, 0.1, n_samples)
        )

        return {
            'conversion': (features, conversion_labels),
            'churn': (features, churn_labels),
            'engagement': (features, engagement_labels)
        }

    def _load_behavior_patterns(self) -> Dict[str, Any]:
        """Load behavioral pattern templates for analysis."""
        return {
            "high_intent_signals": [
                "asking about pricing",
                "scheduling viewing requests",
                "inquiring about financing",
                "asking about neighborhood details",
                "discussing timeline urgency"
            ],
            "low_engagement_patterns": [
                "delayed responses",
                "short answers",
                "avoiding specific questions",
                "not opening property links",
                "canceling appointments"
            ],
            "objection_indicators": [
                "price concerns",
                "location hesitation",
                "timeline conflicts",
                "financing questions",
                "comparison shopping"
            ],
            "buying_readiness_signals": [
                "pre-approval mentioned",
                "urgency in timeline",
                "specific property requirements",
                "asking about next steps",
                "bringing up family/spouse"
            ]
        }

    async def predict_lead_behavior(
        self,
        lead_id: str,
        conversation_history: List[Dict],
        interaction_data: Dict[str, Any],
        prediction_types: List[BehaviorPredictionType]
    ) -> List[PredictionResult]:
        """
        Predict lead behavior using ML + Claude ensemble approach.

        Args:
            lead_id: Unique lead identifier
            conversation_history: Recent conversation messages
            interaction_data: Lead interaction metrics
            prediction_types: Types of predictions to generate

        Returns:
            List of prediction results with ML and Claude insights
        """
        try:
            # Extract ML features from interaction data
            ml_features = await self._extract_ml_features(interaction_data, conversation_history)

            # Get Claude semantic analysis of conversations
            claude_analysis = await self._get_claude_behavioral_analysis(
                conversation_history, interaction_data
            )

            # Generate predictions for each requested type
            predictions = []
            for prediction_type in prediction_types:
                prediction = await self._generate_ensemble_prediction(
                    prediction_type, ml_features, claude_analysis, lead_id
                )
                predictions.append(prediction)

            # Cache results for performance
            await self._cache_behavioral_predictions(lead_id, predictions)

            logger.info(f"Generated {len(predictions)} behavioral predictions for lead {lead_id}")
            return predictions

        except Exception as e:
            logger.error(f"Error predicting lead behavior: {e}")
            return []

    async def _extract_ml_features(
        self,
        interaction_data: Dict[str, Any],
        conversation_history: List[Dict]
    ) -> Dict[str, float]:
        """Extract ML features from interaction data and conversations."""
        try:
            features = {}

            # Basic engagement metrics
            features['engagement_score'] = interaction_data.get('engagement_score', 0.5)
            features['response_rate'] = interaction_data.get('response_rate', 0.0)
            features['days_since_first_contact'] = interaction_data.get('days_since_first_contact', 0)

            # Conversation features
            total_messages = len(conversation_history)
            features['total_messages'] = min(total_messages / 20.0, 1.0)  # Normalize

            if conversation_history:
                # Average message length
                avg_length = np.mean([len(msg.get('content', '')) for msg in conversation_history])
                features['avg_message_length'] = min(avg_length / 200.0, 1.0)

                # Conversation sentiment (simplified)
                positive_words = ['great', 'excellent', 'perfect', 'love', 'interested', 'excited']
                negative_words = ['concerned', 'worried', 'expensive', 'problem', 'difficult']

                sentiment_score = 0.5  # neutral baseline
                for msg in conversation_history:
                    content = msg.get('content', '').lower()
                    positive_count = sum(1 for word in positive_words if word in content)
                    negative_count = sum(1 for word in negative_words if word in content)
                    sentiment_score += (positive_count - negative_count) * 0.1

                features['conversation_sentiment'] = max(0.0, min(1.0, sentiment_score))

            # Property interaction features
            features['property_views'] = min(interaction_data.get('property_views', 0) / 10.0, 1.0)
            features['qualification_completeness'] = interaction_data.get('qualification_score', 0.0) / 100.0

            return features

        except Exception as e:
            logger.warning(f"Error extracting ML features: {e}")
            return {'engagement_score': 0.5, 'response_rate': 0.0, 'days_since_first_contact': 0,
                   'total_messages': 0.0, 'avg_message_length': 0.0, 'conversation_sentiment': 0.5,
                   'property_views': 0.0, 'qualification_completeness': 0.0}

    async def _get_claude_behavioral_analysis(
        self,
        conversation_history: List[Dict],
        interaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get Claude's behavioral analysis of lead interactions."""
        try:
            analysis_prompt = f"""You are an expert real estate behavioral psychologist. Analyze this lead's behavior patterns and provide insights into their buying psychology, conversion likelihood, and engagement patterns.

            Conversation History: {json.dumps(conversation_history[-10:], indent=2)}
            Interaction Data: {json.dumps(interaction_data, indent=2)}

            Please analyze:
            1. Buying motivation and urgency level
            2. Engagement patterns and communication style
            3. Potential objections or concerns
            4. Conversion readiness indicators
            5. Risk factors for churn or disengagement
            6. Optimal engagement strategy recommendations

            Focus on psychological insights that ML models might miss, such as:
            - Emotional state and stress indicators
            - Decision-making style preferences
            - Family dynamics and influences
            - Communication preferences and timing
            - Trust and rapport building needs

            Provide specific, actionable insights based on the conversation content and interaction patterns."""

            response = await self.claude_client.messages.create(
                model=settings.claude_model,
                max_tokens=1000,
                temperature=0.4,
                system="You are an expert behavioral analyst for real estate leads. Provide detailed psychological insights.",
                messages=[{
                    "role": "user",
                    "content": "Analyze this lead's behavioral patterns and provide conversion insights."
                }]
            )

            claude_text = response.content[0].text
            return await self._parse_claude_behavioral_analysis(claude_text)

        except Exception as e:
            logger.error(f"Error getting Claude behavioral analysis: {e}")
            return {"error": str(e), "insights": [], "recommendations": []}

    async def _parse_claude_behavioral_analysis(self, claude_text: str) -> Dict[str, Any]:
        """Parse Claude's behavioral analysis into structured insights."""
        try:
            analysis = {
                "motivation_level": "medium",
                "urgency_score": 0.5,
                "engagement_style": "unknown",
                "conversion_readiness": 0.5,
                "risk_factors": [],
                "opportunities": [],
                "recommendations": [],
                "psychological_profile": {},
                "confidence": 0.7
            }

            lines = claude_text.split('\n')
            current_section = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Detect sections
                if any(keyword in line.lower() for keyword in ["motivation", "urgency"]):
                    current_section = "motivation"
                elif any(keyword in line.lower() for keyword in ["engagement", "communication"]):
                    current_section = "engagement"
                elif any(keyword in line.lower() for keyword in ["risk", "concern", "objection"]):
                    current_section = "risks"
                elif any(keyword in line.lower() for keyword in ["opportunity", "strength"]):
                    current_section = "opportunities"
                elif any(keyword in line.lower() for keyword in ["recommend", "suggest", "strategy"]):
                    current_section = "recommendations"

                # Extract insights based on section
                if current_section == "risks" and (line.startswith('-') or line.startswith('•')):
                    analysis["risk_factors"].append(line.lstrip('-• '))
                elif current_section == "opportunities" and (line.startswith('-') or line.startswith('•')):
                    analysis["opportunities"].append(line.lstrip('-• '))
                elif current_section == "recommendations" and (line.startswith('-') or line.startswith('•')):
                    analysis["recommendations"].append(line.lstrip('-• '))

                # Extract specific scores
                if "high" in line.lower() and "motivation" in line.lower():
                    analysis["motivation_level"] = "high"
                    analysis["urgency_score"] = 0.8
                elif "low" in line.lower() and ("motivation" in line.lower() or "urgency" in line.lower()):
                    analysis["motivation_level"] = "low"
                    analysis["urgency_score"] = 0.3

                if "ready" in line.lower() and ("convert" in line.lower() or "buy" in line.lower()):
                    analysis["conversion_readiness"] = 0.8
                elif "not ready" in line.lower():
                    analysis["conversion_readiness"] = 0.3

            return analysis

        except Exception as e:
            logger.warning(f"Error parsing Claude behavioral analysis: {e}")
            return {
                "motivation_level": "medium",
                "urgency_score": 0.5,
                "risk_factors": ["Analysis parsing error"],
                "opportunities": ["Further conversation needed"],
                "recommendations": ["Schedule follow-up call"],
                "confidence": 0.3
            }

    async def _generate_ensemble_prediction(
        self,
        prediction_type: BehaviorPredictionType,
        ml_features: Dict[str, float],
        claude_analysis: Dict[str, Any],
        lead_id: str
    ) -> PredictionResult:
        """Generate ensemble prediction combining ML and Claude insights."""
        try:
            # Prepare ML feature vector
            feature_vector = np.array([
                ml_features.get('engagement_score', 0.5),
                ml_features.get('days_since_first_contact', 0),
                ml_features.get('response_rate', 0.0),
                ml_features.get('qualification_completeness', 0.0),
                ml_features.get('conversation_sentiment', 0.5),
                ml_features.get('property_views', 0.0),
                ml_features.get('total_messages', 0.0)
            ]).reshape(1, -1)

            # Get ML prediction based on type
            ml_score = 0.5
            ml_confidence = 0.7

            if prediction_type == BehaviorPredictionType.CONVERSION_LIKELIHOOD and self.conversion_model:
                ml_prob = self.conversion_model.predict_proba(feature_vector)[0]
                ml_score = ml_prob[1] if len(ml_prob) > 1 else ml_prob[0]

            elif prediction_type == BehaviorPredictionType.CHURN_RISK and self.churn_model:
                ml_prob = self.churn_model.predict_proba(feature_vector)[0]
                ml_score = ml_prob[1] if len(ml_prob) > 1 else ml_prob[0]

            elif prediction_type == BehaviorPredictionType.ENGAGEMENT_RECEPTIVITY and self.engagement_model:
                ml_score = self.engagement_model.predict(feature_vector)[0]
                ml_score = max(0.0, min(1.0, ml_score))

            # Get Claude-based prediction
            claude_score = claude_analysis.get('conversion_readiness', 0.5)
            claude_confidence = claude_analysis.get('confidence', 0.7)

            if prediction_type == BehaviorPredictionType.CHURN_RISK:
                # Invert for churn (higher risk factors = higher churn probability)
                risk_factor_count = len(claude_analysis.get('risk_factors', []))
                claude_score = min(0.9, risk_factor_count * 0.2)

            elif prediction_type == BehaviorPredictionType.BUYING_URGENCY:
                claude_score = claude_analysis.get('urgency_score', 0.5)

            # Ensemble prediction (weighted average)
            ml_weight = 0.6
            claude_weight = 0.4
            final_score = (ml_score * ml_weight) + (claude_score * claude_weight)
            final_confidence = (ml_confidence * ml_weight) + (claude_confidence * claude_weight)

            # Generate contributing factors
            contributing_factors = []
            if ml_features.get('engagement_score', 0) > 0.7:
                contributing_factors.append("High engagement score")
            if ml_features.get('qualification_completeness', 0) > 0.8:
                contributing_factors.append("Well qualified")
            if claude_analysis.get('motivation_level') == "high":
                contributing_factors.append("High motivation detected")

            # Generate recommendations
            recommendations = claude_analysis.get('recommendations', [])
            if not recommendations:
                recommendations = self._generate_default_recommendations(prediction_type, final_score)

            return PredictionResult(
                prediction_type=prediction_type,
                score=final_score,
                confidence=final_confidence,
                contributing_factors=contributing_factors,
                claude_reasoning=claude_analysis.get('insights', 'Analysis completed'),
                ml_features=ml_features,
                recommended_actions=recommendations,
                risk_factors=claude_analysis.get('risk_factors', []),
                opportunities=claude_analysis.get('opportunities', [])
            )

        except Exception as e:
            logger.error(f"Error generating ensemble prediction: {e}")
            return PredictionResult(
                prediction_type=prediction_type,
                score=0.5,
                confidence=0.3,
                contributing_factors=["Error in prediction"],
                claude_reasoning=f"Error: {str(e)}",
                ml_features=ml_features,
                recommended_actions=["Manual review needed"],
                risk_factors=["Prediction error"],
                opportunities=["Needs analysis"]
            )

    def _generate_default_recommendations(self, prediction_type: BehaviorPredictionType, score: float) -> List[str]:
        """Generate default recommendations based on prediction type and score."""
        if prediction_type == BehaviorPredictionType.CONVERSION_LIKELIHOOD:
            if score > 0.7:
                return ["Schedule property showing", "Prepare purchase agreement", "Connect with lender"]
            elif score > 0.4:
                return ["Qualify budget and timeline", "Share relevant property matches", "Build rapport"]
            else:
                return ["Nurture with market insights", "Educational content", "Long-term follow-up"]

        elif prediction_type == BehaviorPredictionType.CHURN_RISK:
            if score > 0.7:
                return ["Immediate intervention call", "Address concerns", "Personalized attention"]
            else:
                return ["Regular check-ins", "Valuable content sharing", "Maintain engagement"]

        return ["Continue current engagement strategy"]

    async def _cache_behavioral_predictions(self, lead_id: str, predictions: List[PredictionResult]):
        """Cache behavioral predictions for performance."""
        try:
            cache_data = {
                "lead_id": lead_id,
                "predictions": [asdict(pred) for pred in predictions],
                "timestamp": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=2)).isoformat()
            }

            await self.redis_service.store_conversation_message(
                f"behavioral_prediction_{lead_id}",
                "system",
                json.dumps(cache_data),
                lead_id,
                {"type": "behavioral_cache", "ttl": 7200}
            )

        except Exception as e:
            logger.warning(f"Failed to cache behavioral predictions: {e}")

    async def create_behavioral_profile(
        self,
        lead_id: str,
        conversation_history: List[Dict],
        interaction_data: Dict[str, Any]
    ) -> BehavioralProfile:
        """Create comprehensive behavioral profile for a lead."""
        try:
            # Generate all prediction types
            prediction_types = [
                BehaviorPredictionType.CONVERSION_LIKELIHOOD,
                BehaviorPredictionType.CHURN_RISK,
                BehaviorPredictionType.ENGAGEMENT_RECEPTIVITY,
                BehaviorPredictionType.BUYING_URGENCY
            ]

            predictions = await self.predict_lead_behavior(
                lead_id, conversation_history, interaction_data, prediction_types
            )

            # Extract key metrics
            conversion_prob = next(
                (p.score for p in predictions if p.prediction_type == BehaviorPredictionType.CONVERSION_LIKELIHOOD),
                0.5
            )
            churn_risk = next(
                (p.score for p in predictions if p.prediction_type == BehaviorPredictionType.CHURN_RISK),
                0.5
            )
            engagement_score = next(
                (p.score for p in predictions if p.prediction_type == BehaviorPredictionType.ENGAGEMENT_RECEPTIVITY),
                0.5
            )

            # Determine conversion stage
            current_stage = self._determine_conversion_stage(conversion_prob, interaction_data)

            # Generate behavioral signals
            behavioral_signals = []
            for prediction in predictions:
                signal = BehavioralSignal(
                    signal_type=prediction.prediction_type.value,
                    value=prediction.score,
                    confidence=prediction.confidence,
                    timestamp=datetime.now(),
                    source="ensemble_prediction",
                    metadata={
                        "contributing_factors": prediction.contributing_factors,
                        "recommendations": prediction.recommended_actions
                    }
                )
                behavioral_signals.append(signal)

            # Get Claude insights
            claude_insights = await self._get_claude_behavioral_analysis(conversation_history, interaction_data)

            # Calculate next optimal contact time
            next_contact = self._calculate_optimal_contact_time(engagement_score, churn_risk)

            return BehavioralProfile(
                lead_id=lead_id,
                conversion_probability=conversion_prob,
                current_stage=current_stage,
                churn_risk_score=churn_risk,
                engagement_score=engagement_score,
                behavioral_signals=behavioral_signals,
                claude_insights=claude_insights,
                ml_features=await self._extract_ml_features(interaction_data, conversation_history),
                prediction_confidence=np.mean([p.confidence for p in predictions]),
                last_updated=datetime.now(),
                next_optimal_contact=next_contact
            )

        except Exception as e:
            logger.error(f"Error creating behavioral profile: {e}")
            raise

    def _determine_conversion_stage(self, conversion_prob: float, interaction_data: Dict[str, Any]) -> ConversionStage:
        """Determine current conversion stage based on probability and interaction data."""
        qualification_score = interaction_data.get('qualification_score', 0) / 100.0
        engagement_level = interaction_data.get('engagement_score', 0.5)

        if conversion_prob > 0.8 and qualification_score > 0.8:
            return ConversionStage.PURCHASE
        elif conversion_prob > 0.6 and qualification_score > 0.6:
            return ConversionStage.EVALUATION
        elif conversion_prob > 0.4 and engagement_level > 0.5:
            return ConversionStage.INTENT
        elif engagement_level > 0.4:
            return ConversionStage.CONSIDERATION
        elif engagement_level > 0.2:
            return ConversionStage.INTEREST
        else:
            return ConversionStage.AWARENESS

    def _calculate_optimal_contact_time(self, engagement_score: float, churn_risk: float) -> datetime:
        """Calculate optimal next contact time based on behavioral profile."""
        base_hours = 24  # Default 24 hours

        # Higher engagement = sooner contact
        engagement_factor = max(0.5, 2.0 - engagement_score)

        # Higher churn risk = sooner contact
        churn_factor = max(0.3, 1.0 - churn_risk)

        # Calculate final delay
        delay_hours = base_hours * engagement_factor * churn_factor

        return datetime.now() + timedelta(hours=delay_hours)


# Global instance
claude_behavioral_intelligence = ClaudeBehavioralIntelligence()


async def get_behavioral_intelligence() -> ClaudeBehavioralIntelligence:
    """Get global behavioral intelligence service."""
    return claude_behavioral_intelligence