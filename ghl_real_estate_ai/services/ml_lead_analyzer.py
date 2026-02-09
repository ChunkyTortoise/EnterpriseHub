"""
ML Lead Analyzer - Jorge AI Lead Scoring Integration
Integrates ML predictions as a fast tier before Claude AI analysis

Architecture:
- ML prediction (if confidence >0.85) → Direct result
- ML prediction (if confidence <0.85) → Claude AI analysis
- Maintains existing error handling and logging patterns
- Backward compatible with EnhancedLeadIntelligence

Integration Points:
- Extends existing EnhancedLeadIntelligence service
- Uses existing cache_service patterns
- Publishes to existing event system
- Follows Jorge architectural patterns
"""

import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import shap
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from ghl_real_estate_ai.events.ml_event_models import MLEventPublisher
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.claude_enhanced_lead_scorer import UnifiedScoringResult
from ghl_real_estate_ai.services.enhanced_lead_intelligence import EnhancedLeadIntelligence

logger = get_logger(__name__)
cache = get_cache_service()


class MLLeadPredictor:
    """
    Fast ML prediction tier for lead scoring
    Uses pre-trained RandomForest model with feature engineering
    """

    def __init__(self):
        self.model: Optional[RandomForestClassifier] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: List[str] = []
        self.model_version = "v1.0"
        self.confidence_threshold = 0.85
        self.shap_explainer = None
        self._is_loaded = False

    async def load_model(self) -> bool:
        """Load or train ML model for lead scoring"""
        try:
            # Try to load existing model from cache first
            cached_model = await cache.get("ml_lead_model_v1")
            if cached_model:
                self.model = cached_model["model"]
                self.scaler = cached_model["scaler"]
                self.feature_names = cached_model["feature_names"]
                self.shap_explainer = cached_model.get("shap_explainer")
                self._is_loaded = True
                logger.info("ML lead model loaded from cache")
                return True

            # If no cached model, create a simple demo model
            await self._create_demo_model()
            return True

        except Exception as e:
            logger.error(f"Failed to load ML model: {e}")
            return False

    async def _create_demo_model(self):
        """Create a demo ML model with realistic behavior"""

        # Demo feature engineering for real estate leads
        self.feature_names = [
            "response_time_hours",
            "message_length_avg",
            "questions_asked",
            "price_range_mentioned",
            "timeline_urgency",
            "location_specificity",
            "financing_mentioned",
            "family_size_mentioned",
            "job_stability_score",
            "previous_real_estate_experience",
        ]

        # Create demo training data with realistic patterns
        np.random.seed(42)
        n_samples = 1000

        # Generate realistic feature patterns
        X_demo = np.random.randn(n_samples, len(self.feature_names))

        # Add realistic correlations for real estate lead behavior
        # Quick responders with specific questions tend to be hotter leads
        response_time = np.random.exponential(scale=2, size=n_samples)  # Faster response = better
        message_length = np.random.normal(50, 20, n_samples)  # Moderate message length
        questions_asked = np.random.poisson(lam=2, size=n_samples)  # More questions = more engaged

        X_demo[:, 0] = response_time
        X_demo[:, 1] = message_length
        X_demo[:, 2] = questions_asked

        # Generate realistic labels based on features
        # Hot leads: fast response + specific questions + mentioned price/timeline
        hot_score = (
            (response_time < 1) * 0.3  # Fast response
            + (questions_asked > 3) * 0.3  # Many questions
            + (message_length > 30) * 0.2  # Detailed messages
            + np.random.normal(0, 0.2, n_samples)  # Add noise
        )

        y_demo = (hot_score > 0.4).astype(int)  # Binary classification: hot (1) vs not hot (0)

        # Train model
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X_demo)

        self.model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, class_weight="balanced")
        self.model.fit(X_scaled, y_demo)

        # Initialize SHAP explainer for interpretability
        self.shap_explainer = shap.TreeExplainer(self.model)

        # Cache the model
        model_cache = {
            "model": self.model,
            "scaler": self.scaler,
            "feature_names": self.feature_names,
            "shap_explainer": self.shap_explainer,
        }
        await cache.set("ml_lead_model_v1", model_cache, ttl=3600)  # Cache for 1 hour

        self._is_loaded = True
        logger.info("Demo ML lead model created and cached")

    def _extract_features(self, lead_context: Dict[str, Any]) -> np.ndarray:
        """Extract ML features from lead context"""

        # Initialize features with defaults
        features = np.zeros(len(self.feature_names))

        try:
            # Extract conversation metadata
            conversations = lead_context.get("conversations", [])
            if conversations:
                # Response time (hours since first contact)
                first_msg = conversations[0]
                if len(conversations) > 1:
                    response_time = (
                        conversations[1].get("timestamp", time.time()) - first_msg.get("timestamp", time.time())
                    ) / 3600
                    features[0] = max(0.1, min(48, response_time))  # Cap at 48 hours

                # Average message length
                msg_lengths = [len(msg.get("content", "")) for msg in conversations]
                features[1] = np.mean(msg_lengths) if msg_lengths else 20

                # Questions asked (count "?" in messages)
                questions = sum(msg.get("content", "").count("?") for msg in conversations)
                features[2] = min(10, questions)  # Cap at 10

            # Extract preferences and context
            extracted_prefs = lead_context.get("extracted_preferences", {})

            # Price range mentioned (1 if mentioned, 0 otherwise)
            features[3] = 1 if extracted_prefs.get("budget") or "price" in str(lead_context).lower() else 0

            # Timeline urgency (1-5 scale based on keywords)
            timeline_keywords = ["urgent", "asap", "immediately", "soon", "quick"]
            urgency_score = sum(1 for kw in timeline_keywords if kw in str(lead_context).lower())
            features[4] = min(5, urgency_score)

            # Location specificity (1 if specific location mentioned)
            features[5] = 1 if extracted_prefs.get("location") else 0

            # Financing mentioned
            financing_keywords = ["financing", "loan", "mortgage", "cash", "down payment"]
            features[6] = 1 if any(kw in str(lead_context).lower() for kw in financing_keywords) else 0

            # Family size mentioned
            family_keywords = ["family", "kids", "children", "bedrooms", "bed"]
            features[7] = 1 if any(kw in str(lead_context).lower() for kw in family_keywords) else 0

            # Job stability score (estimated from context)
            job_keywords = ["job", "work", "employed", "income", "salary", "career"]
            features[8] = min(5, sum(1 for kw in job_keywords if kw in str(lead_context).lower()))

            # Previous real estate experience
            exp_keywords = ["sold", "bought", "previous", "before", "experience", "realtor"]
            features[9] = 1 if any(kw in str(lead_context).lower() for kw in exp_keywords) else 0

        except Exception as e:
            logger.warning(f"Feature extraction error: {e}")
            # Return zeros if feature extraction fails
            features = np.zeros(len(self.feature_names))

        return features

    async def predict_lead_score(self, lead_context: Dict[str, Any]) -> Tuple[float, float, Dict[str, float]]:
        """
        Predict lead score with ML model

        Returns:
            Tuple of (score, confidence, feature_importance)
        """
        if not self._is_loaded:
            await self.load_model()

        if not self.model or not self.scaler:
            raise ValueError("ML model not loaded")

        # Extract features
        features = self._extract_features(lead_context)
        features_scaled = self.scaler.transform(features.reshape(1, -1))

        # Get prediction and confidence
        prediction_proba = self.model.predict_proba(features_scaled)[0]

        # Score is probability of being a hot lead (class 1) * 100
        score = prediction_proba[1] * 100

        # Confidence is the maximum probability (how certain the model is)
        confidence = max(prediction_proba)

        # Get feature importance using SHAP
        feature_importance = {}
        try:
            if self.shap_explainer:
                shap_values = self.shap_explainer.shap_values(features_scaled)
                # Use SHAP values for hot lead class (index 1)
                shap_hot = shap_values[1][0] if isinstance(shap_values, list) else shap_values[0]

                # Get top 5 features by absolute SHAP value
                feature_impacts = [(name, abs(shap_val)) for name, shap_val in zip(self.feature_names, shap_hot)]
                feature_impacts.sort(key=lambda x: x[1], reverse=True)

                feature_importance = {name: impact for name, impact in feature_impacts[:5]}
            else:
                # Fallback to simple feature importance from RandomForest
                importances = self.model.feature_importances_
                feature_importance = dict(zip(self.feature_names, importances))

        except Exception as e:
            logger.warning(f"Feature importance calculation failed: {e}")
            # Provide fallback importance
            feature_importance = {self.feature_names[0]: 0.3, self.feature_names[1]: 0.2}

        return score, confidence, feature_importance

    async def get_shap_explanation(self, lead_context: Dict[str, Any], lead_name: str) -> Optional[Any]:
        """
        Generate comprehensive SHAP explanation for a lead prediction

        Args:
            lead_context: Lead data for explanation
            lead_name: Human-readable lead name

        Returns:
            SHAPExplanation object or None if not available
        """
        try:
            from ghl_real_estate_ai.services.shap_explainer_service import get_shap_explanation

            if not self._is_loaded:
                await self.load_model()

            if not self.model or not self.scaler or not self.shap_explainer:
                logger.warning("SHAP explanation not available - model components missing")
                return None

            # Extract features
            features = self._extract_features(lead_context)

            # Get prediction score
            score, confidence, _ = await self.predict_lead_score(lead_context)

            # Generate comprehensive SHAP explanation
            lead_id = lead_context.get("lead_id", f"lead_{lead_name.lower().replace(' ', '_')}")

            explanation = await get_shap_explanation(
                model=self.model,
                scaler=self.scaler,
                shap_explainer=self.shap_explainer,
                feature_names=self.feature_names,
                features=features,
                lead_id=lead_id,
                lead_name=lead_name,
                prediction_score=score,
            )

            logger.info(f"SHAP explanation generated for {lead_name}")
            return explanation

        except Exception as e:
            logger.error(f"SHAP explanation generation failed: {e}")
            return None

    def classify_lead(self, score: float) -> str:
        """Classify lead based on ML score"""
        if score >= 75:
            return "hot"
        elif score >= 50:
            return "warm"
        else:
            return "cold"


class MLEnhancedLeadAnalyzer(EnhancedLeadIntelligence):
    """
    Enhanced Lead Intelligence with ML tier integration
    Extends existing EnhancedLeadIntelligence to add ML fast tier
    """

    def __init__(self):
        super().__init__()
        self.ml_predictor = MLLeadPredictor()
        self.ml_event_publisher = MLEventPublisher()
        self.ml_confidence_threshold = 0.85

        # Performance tracking
        self.ml_metrics = {
            "ml_predictions": 0,
            "claude_escalations": 0,
            "cache_hits": 0,
            "ml_avg_time_ms": 0.0,
            "claude_avg_time_ms": 0.0,
        }

    async def initialize(self):
        """Initialize ML components and base service"""
        await super().initialize()

        # Initialize ML components
        await self.ml_predictor.load_model()
        await self.ml_event_publisher.connect()

        logger.info("ML Enhanced Lead Analyzer initialized")

    async def _analyze_with_ml_tier(
        self, lead_name: str, lead_context: Dict[str, Any], force_claude: bool = False
    ) -> UnifiedScoringResult:
        """
        Core ML tier integration - the main modification point

        Pattern: ML prediction (if confidence >0.85) → Claude AI (if confidence <0.85)
        Maintains existing error handling and logging patterns
        """

        lead_id = lead_context.get("lead_id", f"ml_{lead_name.lower().replace(' ', '_')}")
        start_time = datetime.now()

        # Step 1: Check cache first
        cache_key = f"ml_lead_analysis_{lead_id}_{hash(json.dumps(lead_context, sort_keys=True, default=str))}"

        if not force_claude:
            try:
                cached_result = await cache.get(cache_key)
                if cached_result:
                    self.ml_metrics["cache_hits"] += 1

                    # Publish cache hit event
                    await self.ml_event_publisher.publish_ml_cache_hit(
                        lead_id=lead_id,
                        lead_name=lead_name,
                        cache_key=cache_key,
                        cache_age_seconds=cached_result.get("cache_age", 0),
                        cached_ml_score=cached_result.final_score,
                        cached_ml_confidence=cached_result.confidence_score,
                        cached_classification=cached_result.classification,
                    )

                    logger.info(f"ML cache hit for lead {lead_name}")
                    return cached_result

            except Exception as e:
                logger.warning(f"Cache access failed: {e}")

        # Step 2: ML Prediction Tier
        ml_start_time = datetime.now()
        try:
            ml_score, ml_confidence, feature_importance = await self.ml_predictor.predict_lead_score(lead_context)
            ml_classification = self.ml_predictor.classify_lead(ml_score)
            ml_time_ms = (datetime.now() - ml_start_time).total_seconds() * 1000

            self.ml_metrics["ml_predictions"] += 1
            self._update_ml_avg_time(ml_time_ms)

            # Publish ML scoring event
            await self.ml_event_publisher.publish_ml_scored(
                lead_id=lead_id,
                lead_name=lead_name,
                ml_score=ml_score,
                ml_confidence=ml_confidence,
                ml_classification=ml_classification,
                feature_importance=feature_importance,
                prediction_time_ms=ml_time_ms,
            )

            logger.info(f"ML prediction for {lead_name}: score={ml_score:.1f}, confidence={ml_confidence:.3f}")

            # Step 3: Decision Point - Use ML or escalate to Claude?
            if ml_confidence >= self.ml_confidence_threshold and not force_claude:
                # High confidence ML prediction - use it directly
                result = self._create_ml_result(
                    lead_id=lead_id,
                    lead_name=lead_name,
                    lead_context=lead_context,
                    ml_score=ml_score,
                    ml_confidence=ml_confidence,
                    ml_classification=ml_classification,
                    feature_importance=feature_importance,
                    ml_time_ms=ml_time_ms,
                )

                # Cache the result
                await cache.set(cache_key, result, ttl=300)  # 5 minute cache

                logger.info(f"ML high-confidence result for {lead_name} (confidence: {ml_confidence:.3f})")
                return result

            else:
                # Low confidence ML prediction - escalate to Claude
                escalation_reason = f"ML confidence {ml_confidence:.3f} below threshold {self.ml_confidence_threshold}"
                if force_claude:
                    escalation_reason = "Forced Claude analysis requested"

                # Publish escalation event
                await self.ml_event_publisher.publish_ml_escalated(
                    lead_id=lead_id,
                    lead_name=lead_name,
                    ml_score=ml_score,
                    ml_confidence=ml_confidence,
                    escalation_reason=escalation_reason,
                    lead_context=lead_context,
                    ml_processing_time_ms=ml_time_ms,
                )

                self.ml_metrics["claude_escalations"] += 1

                # Enrich lead context with ML insights for Claude
                enriched_context = lead_context.copy()
                enriched_context["ml_insights"] = {
                    "ml_score": ml_score,
                    "ml_confidence": ml_confidence,
                    "ml_classification": ml_classification,
                    "feature_importance": feature_importance,
                    "escalation_reason": escalation_reason,
                }

                # Use existing Claude analysis with enriched context
                claude_start_time = datetime.now()
                claude_result = await super().get_comprehensive_lead_analysis(
                    lead_name=lead_name, lead_context=enriched_context, force_refresh=True
                )
                claude_time_ms = (datetime.now() - claude_start_time).total_seconds() * 1000

                self._update_claude_avg_time(claude_time_ms)

                # Enhance Claude result with ML insights
                claude_result.sources.append("ML_Fast_Tier")
                claude_result.metadata = getattr(claude_result, "metadata", {})
                claude_result.metadata.update(
                    {
                        "ml_score": ml_score,
                        "ml_confidence": ml_confidence,
                        "ml_feature_importance": feature_importance,
                        "escalation_reason": escalation_reason,
                        "ml_time_ms": ml_time_ms,
                        "claude_time_ms": claude_time_ms,
                    }
                )

                # Cache the enriched result
                await cache.set(cache_key, claude_result, ttl=300)

                logger.info(f"Claude analysis completed for {lead_name} after ML escalation")
                return claude_result

        except Exception as e:
            logger.error(f"ML tier analysis failed for {lead_name}: {e}")
            # Fallback to Claude analysis on ML error
            total_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(f"Falling back to Claude analysis due to ML error")
            return await super().get_comprehensive_lead_analysis(
                lead_name=lead_name, lead_context=lead_context, force_refresh=True
            )

    def _create_ml_result(
        self,
        lead_id: str,
        lead_name: str,
        lead_context: Dict[str, Any],
        ml_score: float,
        ml_confidence: float,
        ml_classification: str,
        feature_importance: Dict[str, float],
        ml_time_ms: float,
    ) -> UnifiedScoringResult:
        """Create UnifiedScoringResult from ML predictions"""

        # Generate strategic summary based on ML insights
        top_features = list(feature_importance.keys())[:3]
        strategic_summary = (
            f"ML Fast-Tier Analysis: {ml_classification.upper()} lead with {ml_confidence:.0%} confidence. "
            f"Key drivers: {', '.join(top_features)}. "
            f"Score: {ml_score:.0f}% based on behavioral patterns."
        )

        # Generate behavioral insights from feature importance
        behavioral_insights = self._generate_ml_behavioral_insights(feature_importance, ml_score)

        # Generate recommended actions based on classification
        recommended_actions = self._generate_ml_actions(ml_classification, ml_score)

        # Create unified result
        return UnifiedScoringResult(
            lead_id=lead_id,
            lead_name=lead_name,
            scored_at=datetime.now(),
            final_score=ml_score,
            confidence_score=ml_confidence,
            classification=ml_classification,
            # Jorge-specific scores (estimated from ML score)
            jorge_score=min(100, ml_score * 1.1),  # Slightly boost for Jorge's metrics
            ml_conversion_score=ml_score,
            churn_risk_score=max(0, 100 - ml_score),
            engagement_score=min(100, ml_score * 1.2),
            # Analysis content
            strategic_summary=strategic_summary,
            behavioral_insights=behavioral_insights,
            reasoning=f"ML model prediction with {ml_confidence:.3f} confidence using {len(feature_importance)} features",
            # Recommendations
            risk_factors=self._get_ml_risk_factors(ml_score, feature_importance),
            opportunities=self._get_ml_opportunities(ml_score, feature_importance),
            recommended_actions=recommended_actions,
            next_best_action=recommended_actions[0]["action"] if recommended_actions else "Follow up",
            expected_timeline=self._estimate_timeline(ml_score),
            success_probability=ml_score,
            # Technical details
            feature_breakdown=feature_importance,
            conversation_context=lead_context,
            sources=["ML_RandomForest", "SHAP_Explainer"],
            analysis_time_ms=ml_time_ms,
            claude_reasoning_time_ms=0,  # No Claude involved in this path
        )

    def _generate_ml_behavioral_insights(self, feature_importance: Dict[str, float], score: float) -> str:
        """Generate behavioral insights from ML feature importance"""

        top_feature = (
            max(feature_importance.items(), key=lambda x: x[1]) if feature_importance else ("response_time", 0.3)
        )
        feature_name, importance = top_feature

        insights_map = {
            "response_time_hours": f"Quick response pattern indicates high engagement (impact: {importance:.2f})",
            "message_length_avg": f"Detailed communication style shows serious intent (impact: {importance:.2f})",
            "questions_asked": f"Active question-asking behavior indicates genuine interest (impact: {importance:.2f})",
            "price_range_mentioned": f"Budget discussion shows transaction readiness (impact: {importance:.2f})",
            "timeline_urgency": f"Time-sensitive language indicates motivated buyer (impact: {importance:.2f})",
        }

        primary_insight = insights_map.get(
            feature_name, f"Key behavioral indicator: {feature_name} (impact: {importance:.2f})"
        )

        if score >= 75:
            return f"HIGH ENGAGEMENT PROFILE: {primary_insight}. Multiple positive behavioral signals detected."
        elif score >= 50:
            return f"MODERATE ENGAGEMENT: {primary_insight}. Mixed behavioral indicators require nurturing."
        else:
            return f"EARLY STAGE ENGAGEMENT: {primary_insight}. Requires relationship building."

    def _generate_ml_actions(self, classification: str, score: float) -> List[Dict[str, Any]]:
        """Generate recommended actions based on ML classification"""

        actions_map = {
            "hot": [
                {"action": "Schedule immediate property tour", "priority": "high", "timeline": "24 hours"},
                {"action": "Send personalized property recommendations", "priority": "high", "timeline": "2 hours"},
                {"action": "Connect with mortgage pre-approval", "priority": "medium", "timeline": "48 hours"},
            ],
            "warm": [
                {"action": "Send market updates and new listings", "priority": "medium", "timeline": "1 week"},
                {"action": "Share educational content about home buying", "priority": "medium", "timeline": "3 days"},
                {"action": "Check in with value-added content", "priority": "low", "timeline": "2 weeks"},
            ],
            "cold": [
                {"action": "Add to nurture email sequence", "priority": "low", "timeline": "1 month"},
                {"action": "Share market insights occasionally", "priority": "low", "timeline": "2 weeks"},
                {"action": "Maintain light touch communication", "priority": "low", "timeline": "Monthly"},
            ],
        }

        return actions_map.get(classification, actions_map["warm"])

    def _get_ml_risk_factors(self, score: float, feature_importance: Dict[str, float]) -> List[str]:
        """Identify risk factors based on ML analysis"""
        risks = []

        if score < 30:
            risks.append("Very low engagement score indicates limited interest")

        if "response_time_hours" in feature_importance and feature_importance["response_time_hours"] < 0.1:
            risks.append("Slow response patterns may indicate low priority")

        if "questions_asked" in feature_importance and feature_importance["questions_asked"] < 0.1:
            risks.append("Limited questions suggest passive interest")

        if not risks:
            risks.append("No significant risk factors detected")

        return risks[:3]  # Limit to top 3

    def _get_ml_opportunities(self, score: float, feature_importance: Dict[str, float]) -> List[str]:
        """Identify opportunities based on ML analysis"""
        opportunities = []

        if score >= 70:
            opportunities.append("High score indicates strong conversion potential")

        if "timeline_urgency" in feature_importance and feature_importance["timeline_urgency"] > 0.2:
            opportunities.append("Urgency indicators suggest immediate opportunity")

        if "price_range_mentioned" in feature_importance and feature_importance["price_range_mentioned"] > 0.2:
            opportunities.append("Budget discussions indicate transaction readiness")

        if not opportunities:
            opportunities.append("Relationship building opportunity")

        return opportunities[:3]  # Limit to top 3

    def _estimate_timeline(self, score: float) -> str:
        """Estimate timeline based on ML score"""
        if score >= 75:
            return "1-2 weeks"
        elif score >= 50:
            return "2-4 weeks"
        else:
            return "1-3 months"

    def _update_ml_avg_time(self, time_ms: float):
        """Update ML average processing time"""
        count = self.ml_metrics["ml_predictions"]
        if count <= 1:
            self.ml_metrics["ml_avg_time_ms"] = time_ms
        else:
            current_avg = self.ml_metrics["ml_avg_time_ms"]
            self.ml_metrics["ml_avg_time_ms"] = (current_avg * (count - 1) + time_ms) / count

    def _update_claude_avg_time(self, time_ms: float):
        """Update Claude average processing time"""
        count = self.ml_metrics["claude_escalations"]
        if count <= 1:
            self.ml_metrics["claude_avg_time_ms"] = time_ms
        else:
            current_avg = self.ml_metrics["claude_avg_time_ms"]
            self.ml_metrics["claude_avg_time_ms"] = (current_avg * (count - 1) + time_ms) / count

    # Override the main analysis method to use ML tier
    async def get_comprehensive_lead_analysis(
        self, lead_name: str, lead_context: Dict[str, Any], force_refresh: bool = False
    ) -> UnifiedScoringResult:
        """
        Main analysis method - now with ML tier integration
        This is the key integration point that modifies the existing flow
        """
        return await self._analyze_with_ml_tier(
            lead_name=lead_name,
            lead_context=lead_context,
            force_claude=force_refresh,  # force_refresh now forces Claude analysis
        )

    # Override enterprise version too
    async def get_comprehensive_lead_analysis_enterprise(
        self, lead_name: str, lead_context: Dict[str, Any], force_refresh: bool = False
    ) -> UnifiedScoringResult:
        """Enterprise version with ML tier"""
        return await self._analyze_with_ml_tier(
            lead_name=lead_name, lead_context=lead_context, force_claude=force_refresh
        )

    def get_ml_performance_metrics(self) -> Dict[str, Any]:
        """Get ML tier performance metrics"""
        total_analyses = self.ml_metrics["ml_predictions"] + self.ml_metrics["claude_escalations"]
        ml_usage_rate = (self.ml_metrics["ml_predictions"] / total_analyses * 100) if total_analyses > 0 else 0

        return {
            **self.ml_metrics,
            "ml_usage_rate_percent": round(ml_usage_rate, 2),
            "claude_escalation_rate_percent": round(100 - ml_usage_rate, 2),
            "total_analyses": total_analyses,
            "ml_confidence_threshold": self.ml_confidence_threshold,
            "model_version": self.ml_predictor.model_version,
        }


# Singleton instance for use in components
_ml_enhanced_lead_analyzer = None


def get_ml_enhanced_lead_analyzer() -> MLEnhancedLeadAnalyzer:
    """Get singleton instance of ML Enhanced Lead Analyzer"""
    global _ml_enhanced_lead_analyzer
    if _ml_enhanced_lead_analyzer is None:
        _ml_enhanced_lead_analyzer = MLEnhancedLeadAnalyzer()
    return _ml_enhanced_lead_analyzer


async def get_ml_enhanced_lead_analyzer_async() -> MLEnhancedLeadAnalyzer:
    """Get singleton instance with async initialization"""
    global _ml_enhanced_lead_analyzer
    if _ml_enhanced_lead_analyzer is None:
        _ml_enhanced_lead_analyzer = MLEnhancedLeadAnalyzer()

    # Ensure it's initialized
    await _ml_enhanced_lead_analyzer.initialize()
    return _ml_enhanced_lead_analyzer
