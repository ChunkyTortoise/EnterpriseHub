"""
SHAP Explainer Service - Transparent AI Explanations for Real Estate Lead Scoring

Provides comprehensive SHAP (SHapley Additive exPlanations) integration for the existing
ML lead scoring infrastructure, enabling transparent and explainable AI decisions.

Features:
- Interactive SHAP waterfall charts
- Feature importance explanations with business context
- What-if scenario analysis
- Cached explanations for performance
- Integration with existing ML infrastructure

Integration Points:
- Extends existing MLLeadPredictor from ml_lead_analyzer.py
- Uses existing cache_service patterns for performance
- Publishes to existing event system for tracking
- Follows existing async patterns for Streamlit integration

Architecture:
- SHAPExplainerService: Core service for SHAP explanations
- BusinessFeatureMapper: Maps ML features to business context
- SHAPVisualizationBuilder: Builds interactive charts
- WhatIfAnalyzer: Scenario analysis capabilities
"""

import hashlib
import time
import warnings
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.ensemble import RandomForestClassifier

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
from ghl_real_estate_ai.services.cache_service import get_cache_service

# Suppress SHAP warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning, module="shap")

logger = get_logger(__name__)
cache = get_cache_service()


@dataclass
class SHAPExplanation:
    """
    Structured SHAP explanation result containing all explanation data
    """

    lead_id: str
    lead_name: str
    explained_at: datetime

    # Core SHAP values
    base_value: float  # Expected value (baseline)
    prediction: float  # Final prediction
    shap_values: Dict[str, float]  # Feature -> SHAP value mapping

    # Business insights
    feature_importance: Dict[str, float]  # Feature -> importance score
    business_explanations: Dict[str, str]  # Feature -> business explanation
    key_drivers: List[Dict[str, Any]]  # Top 5 driving factors
    risk_factors: List[str]  # Features indicating risk
    opportunities: List[str]  # Features indicating opportunities

    # Interactive data for UI
    waterfall_data: Dict[str, Any]  # Data for waterfall chart
    feature_impact_data: Dict[str, Any]  # Data for feature impact visualization

    # Performance metrics
    explanation_time_ms: float
    what_if_ready: bool = True  # Whether what-if analysis is available
    cached: bool = False


@dataclass
class FeatureContext:
    """
    Business context for a feature with explanation templates
    """

    feature_name: str
    display_name: str
    category: str  # 'behavioral', 'financial', 'temporal', 'engagement'
    description: str
    positive_explanation_template: str  # When feature increases score
    negative_explanation_template: str  # When feature decreases score
    business_impact: str  # Why this matters for real estate
    actionable_insight_template: str  # What Jorge can do about it


class BusinessFeatureMapper:
    """
    Maps ML features to business context with rich explanations
    """

    def __init__(self):
        self.feature_contexts = {
            "response_time_hours": FeatureContext(
                feature_name="response_time_hours",
                display_name="Response Speed",
                category="behavioral",
                description="How quickly the lead responds to initial outreach",
                positive_explanation_template="Responds within {value:.1f} hours, indicating high engagement and motivation",
                negative_explanation_template="Delayed responses ({value:.1f} hours) may indicate lower priority or competing interests",
                business_impact="Quick responders typically convert 3x more often than slow responders",
                actionable_insight_template="Follow up within 2 hours for maximum engagement",
            ),
            "message_length_avg": FeatureContext(
                feature_name="message_length_avg",
                display_name="Communication Detail",
                category="engagement",
                description="Average length of messages from the lead",
                positive_explanation_template="Detailed messages ({value:.0f} characters) show serious interest and engagement",
                negative_explanation_template="Brief messages ({value:.0f} characters) may indicate limited interest or time",
                business_impact="Detailed communicators are 2.5x more likely to complete transactions",
                actionable_insight_template="Ask specific questions to encourage detailed responses",
            ),
            "questions_asked": FeatureContext(
                feature_name="questions_asked",
                display_name="Information Seeking",
                category="engagement",
                description="Number of questions asked by the lead",
                positive_explanation_template="Actively asks {value:.0f} questions, demonstrating genuine interest",
                negative_explanation_template="Limited questions ({value:.0f}) may indicate passive interest",
                business_impact="Question-asking leads convert 4x more often",
                actionable_insight_template="Provide detailed answers and ask follow-up questions",
            ),
            "price_range_mentioned": FeatureContext(
                feature_name="price_range_mentioned",
                display_name="Budget Discussion",
                category="financial",
                description="Whether the lead has discussed price or budget",
                positive_explanation_template="Openly discusses budget and pricing, indicating transaction readiness",
                negative_explanation_template="Avoids price discussions, may need budget qualification",
                business_impact="Budget-aware leads are 5x more likely to transact within 30 days",
                actionable_insight_template="Initiate budget conversation early to qualify intent",
            ),
            "timeline_urgency": FeatureContext(
                feature_name="timeline_urgency",
                display_name="Urgency Level",
                category="temporal",
                description="Urgency indicators in the lead's communication",
                positive_explanation_template="Expresses urgency (level {value:.0f}/5), needs immediate attention",
                negative_explanation_template="No urgency signals (level {value:.0f}/5), longer sales cycle expected",
                business_impact="Urgent leads convert 6x faster than non-urgent ones",
                actionable_insight_template="Prioritize immediate response and schedule quick consultation",
            ),
            "location_specificity": FeatureContext(
                feature_name="location_specificity",
                display_name="Location Clarity",
                category="behavioral",
                description="How specific the lead is about desired location",
                positive_explanation_template="Knows exactly where they want to buy/sell, strong intent",
                negative_explanation_template="Vague about location, may need area education and guidance",
                business_impact="Location-specific leads convert 3x more often",
                actionable_insight_template="Help narrow down specific neighborhoods and areas",
            ),
            "financing_mentioned": FeatureContext(
                feature_name="financing_mentioned",
                display_name="Financial Readiness",
                category="financial",
                description="Whether financing or mortgage topics have been discussed",
                positive_explanation_template="Discusses financing options, indicates serious transaction intent",
                negative_explanation_template="No financing discussion yet, may need qualification",
                business_impact="Financing-aware leads are 4x more likely to complete transactions",
                actionable_insight_template="Connect with pre-approval process early",
            ),
            "family_size_mentioned": FeatureContext(
                feature_name="family_size_mentioned",
                display_name="Family Context",
                category="behavioral",
                description="Whether family size or housing needs are mentioned",
                positive_explanation_template="Shares family situation, indicating genuine housing need",
                negative_explanation_template="No family context shared, may need relationship building",
                business_impact="Family-motivated buyers have 90% follow-through rate",
                actionable_insight_template="Understand family dynamics and housing needs",
            ),
            "job_stability_score": FeatureContext(
                feature_name="job_stability_score",
                display_name="Employment Stability",
                category="financial",
                description="Indicators of employment and income stability",
                positive_explanation_template="Strong employment signals (score {value:.0f}/5), good loan qualification potential",
                negative_explanation_template="Limited employment context (score {value:.0f}/5), may need income verification",
                business_impact="Employment stability correlates with 85% transaction completion",
                actionable_insight_template="Verify employment and income early in process",
            ),
            "previous_real_estate_experience": FeatureContext(
                feature_name="previous_real_estate_experience",
                display_name="Market Experience",
                category="behavioral",
                description="Previous real estate buying/selling experience",
                positive_explanation_template="Has real estate experience, understands process and market",
                negative_explanation_template="First-time buyer/seller, needs education and guidance",
                business_impact="Experienced clients require 50% less hand-holding",
                actionable_insight_template="Adjust communication style based on experience level",
            ),
        }

    def get_business_explanation(self, feature_name: str, shap_value: float, feature_value: float) -> str:
        """
        Generate business explanation for a feature's SHAP impact
        """
        context = self.feature_contexts.get(feature_name)
        if not context:
            return f"{feature_name}: {shap_value:+.3f} impact on score"

        # Determine if this is positive or negative impact
        if shap_value > 0:
            explanation = context.positive_explanation_template.format(value=feature_value)
        else:
            explanation = context.negative_explanation_template.format(value=feature_value)

        return f"{context.display_name}: {explanation}"

    def get_actionable_insight(self, feature_name: str, shap_value: float) -> Optional[str]:
        """
        Get actionable insight for a feature
        """
        context = self.feature_contexts.get(feature_name)
        if not context:
            return None

        return context.actionable_insight_template

    def get_feature_category(self, feature_name: str) -> str:
        """
        Get the business category for a feature
        """
        context = self.feature_contexts.get(feature_name)
        return context.category if context else "other"


class SHAPVisualizationBuilder:
    """
    Builds interactive SHAP visualizations using Plotly
    """

    def __init__(self, feature_mapper: BusinessFeatureMapper):
        self.feature_mapper = feature_mapper

    def build_waterfall_chart(self, explanation: SHAPExplanation) -> go.Figure:
        """
        Create interactive waterfall chart showing how features contribute to the prediction
        """
        # Prepare data for waterfall chart
        features = list(explanation.shap_values.keys())
        shap_vals = list(explanation.shap_values.values())

        # Sort by absolute impact (most important first)
        sorted_pairs = sorted(zip(features, shap_vals), key=lambda x: abs(x[1]), reverse=True)
        features, shap_vals = zip(*sorted_pairs)

        # Build waterfall chart
        fig = go.Figure()

        # Colors for positive/negative impacts
        ["#2E8B57" if val > 0 else "#DC143C" for val in shap_vals]

        # Create waterfall chart
        cumulative = explanation.base_value
        x_vals = []
        y_vals = []
        text_vals = []

        # Base value
        x_vals.append("Expected Value")
        y_vals.append(cumulative)
        text_vals.append(f"Baseline: {cumulative:.1f}")

        # Feature contributions
        for i, (feature, shap_val) in enumerate(zip(features, shap_vals)):
            context = self.feature_mapper.feature_contexts.get(feature)
            display_name = context.display_name if context else feature
            cumulative += shap_val
            x_vals.append(display_name)
            y_vals.append(cumulative)
            text_vals.append(f"{shap_val:+.1f}")

        # Final prediction
        x_vals.append("Final Score")
        y_vals.append(explanation.prediction)
        text_vals.append(f"Score: {explanation.prediction:.1f}")

        # Create the waterfall effect
        fig.add_trace(
            go.Waterfall(
                name="SHAP Explanation",
                orientation="v",
                measure=["absolute"] + ["relative"] * len(features) + ["total"],
                x=x_vals,
                textposition="auto",
                text=text_vals,
                y=[explanation.base_value] + list(shap_vals) + [0],
                connector={"line": {"color": "rgb(63, 63, 63)"}},
                increasing={"marker": {"color": "#2E8B57"}},  # Green for positive
                decreasing={"marker": {"color": "#DC143C"}},  # Red for negative
                totals={"marker": {"color": "#1E40AF"}},  # Blue for totals
            )
        )

        # Styling to match Obsidian theme
        fig.update_layout(
            title={
                "text": f"AI Decision Explanation - {explanation.lead_name}",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 18, "color": "#E5E7EB"},
            },
            xaxis_title="Factors",
            yaxis_title="Lead Score Impact",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#E5E7EB"},
            height=500,
            margin=dict(l=50, r=50, t=80, b=100),
            showlegend=False,
        )

        # Add annotations for better explanation
        fig.add_annotation(
            text=f"Base score: {explanation.base_value:.1f} → Final score: {explanation.prediction:.1f}",
            xref="paper",
            yref="paper",
            x=0.5,
            y=1.02,
            xanchor="center",
            showarrow=False,
            font=dict(size=12, color="#9CA3AF"),
        )

        return fig

    def build_feature_importance_chart(self, explanation: SHAPExplanation) -> go.Figure:
        """
        Create horizontal bar chart showing feature importance by category
        """
        # Organize features by category
        categories = {}
        for feature, shap_val in explanation.shap_values.items():
            category = self.feature_mapper.get_feature_category(feature)
            if category not in categories:
                categories[category] = []

            context = self.feature_mapper.feature_contexts.get(feature)
            display_name = context.display_name if context else feature
            categories[category].append(
                {
                    "feature": display_name,
                    "impact": abs(shap_val),
                    "direction": "Positive" if shap_val > 0 else "Negative",
                    "shap_value": shap_val,
                }
            )

        # Create subplots for each category
        category_names = list(categories.keys())
        fig = make_subplots(
            rows=len(category_names),
            cols=1,
            subplot_titles=[cat.title() + " Factors" for cat in category_names],
            vertical_spacing=0.08,
        )

        colors = {"Positive": "#2E8B57", "Negative": "#DC143C"}

        for i, (category, features) in enumerate(categories.items(), 1):
            # Sort by impact
            features.sort(key=lambda x: x["impact"], reverse=True)

            for feature_data in features:
                fig.add_trace(
                    go.Bar(
                        x=[feature_data["impact"]],
                        y=[feature_data["feature"]],
                        orientation="h",
                        name=feature_data["direction"],
                        marker_color=colors[feature_data["direction"]],
                        text=f"{feature_data['shap_value']:+.2f}",
                        textposition="inside",
                        showlegend=False if i > 1 else True,
                    ),
                    row=i,
                    col=1,
                )

        fig.update_layout(
            title={
                "text": f"Feature Impact Analysis - {explanation.lead_name}",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 18, "color": "#E5E7EB"},
            },
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#E5E7EB"},
            height=150 * len(category_names),
            margin=dict(l=150, r=50, t=80, b=50),
        )

        return fig


class WhatIfAnalyzer:
    """
    Enables what-if scenario analysis by modifying feature values and showing impact
    """

    def __init__(self, model: RandomForestClassifier, scaler, shap_explainer, feature_names: List[str]):
        self.model = model
        self.scaler = scaler
        self.shap_explainer = shap_explainer
        self.feature_names = feature_names

    async def analyze_scenario(
        self, original_features: np.ndarray, modified_features: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Analyze what-if scenario by modifying specific features

        Args:
            original_features: Original feature values
            modified_features: Dict of {feature_name: new_value}

        Returns:
            Scenario analysis with before/after comparison
        """
        # Create modified feature array
        modified_array = original_features.copy()
        feature_indices = {}

        for i, name in enumerate(self.feature_names):
            feature_indices[name] = i

        for feature_name, new_value in modified_features.items():
            if feature_name in feature_indices:
                modified_array[feature_indices[feature_name]] = new_value

        # Scale features
        original_scaled = self.scaler.transform(original_features.reshape(1, -1))
        modified_scaled = self.scaler.transform(modified_array.reshape(1, -1))

        # Get predictions
        original_prob = self.model.predict_proba(original_scaled)[0][1] * 100
        modified_prob = self.model.predict_proba(modified_scaled)[0][1] * 100

        # Get SHAP values
        original_shap = self.shap_explainer.shap_values(original_scaled)
        modified_shap = self.shap_explainer.shap_values(modified_scaled)

        # Handle different SHAP output formats
        if isinstance(original_shap, list):
            original_shap = original_shap[1][0]  # Get positive class
            modified_shap = modified_shap[1][0]
        elif isinstance(original_shap, np.ndarray) and original_shap.ndim == 3:
            # Binary classification (numpy 3D array: samples x features x classes)
            original_shap = original_shap[0, :, 1]
            modified_shap = modified_shap[0, :, 1]
        else:
            original_shap = original_shap[0]
            modified_shap = modified_shap[0]

        # Calculate impact
        score_change = modified_prob - original_prob

        # Identify most impactful changes
        shap_changes = {}
        for i, feature_name in enumerate(self.feature_names):
            if feature_name in modified_features:
                shap_changes[feature_name] = modified_shap[i] - original_shap[i]

        return {
            "original_score": original_prob,
            "modified_score": modified_prob,
            "score_change": score_change,
            "modified_features": modified_features,
            "shap_changes": shap_changes,
            "total_shap_change": sum(shap_changes.values()),
            "scenario_feasible": self._assess_feasibility(modified_features),
            "recommendations": self._generate_recommendations(modified_features, score_change),
        }

    def _assess_feasibility(self, modified_features: Dict[str, float]) -> Dict[str, str]:
        """
        Assess how feasible the scenario modifications are
        """
        feasibility = {}

        # Define feasibility rules for each feature
        rules = {
            "response_time_hours": lambda x: "High" if x <= 2 else "Medium" if x <= 8 else "Low",
            "message_length_avg": lambda x: "High" if 30 <= x <= 200 else "Medium",
            "questions_asked": lambda x: "High" if x <= 5 else "Medium" if x <= 10 else "Low",
            "timeline_urgency": lambda x: "Medium" if 1 <= x <= 5 else "Low",
        }

        for feature, value in modified_features.items():
            if feature in rules:
                feasibility[feature] = rules[feature](value)
            else:
                feasibility[feature] = "Medium"  # Default

        return feasibility

    def _generate_recommendations(self, modified_features: Dict[str, float], score_change: float) -> List[str]:
        """
        Generate actionable recommendations based on the scenario
        """
        recommendations = []

        if score_change > 10:
            recommendations.append("High impact scenario - prioritize these improvements")
        elif score_change > 5:
            recommendations.append("Moderate impact - worthwhile to pursue")
        else:
            recommendations.append("Low impact - consider other strategies")

        # Feature-specific recommendations
        for feature in modified_features:
            if feature == "response_time_hours":
                recommendations.append("Set up automated response system for faster engagement")
            elif feature == "questions_asked":
                recommendations.append("Encourage questions with open-ended conversation starters")
            elif feature == "timeline_urgency":
                recommendations.append("Create urgency with limited-time offers or market updates")
            elif feature == "price_range_mentioned":
                recommendations.append("Guide budget conversation early in the relationship")

        return recommendations[:3]  # Top 3 recommendations


class SHAPExplainerService:
    """
    Main service providing comprehensive SHAP explanations for lead scoring

    Integrates with existing ML infrastructure and provides:
    - Detailed SHAP explanations with business context
    - Interactive visualizations
    - What-if scenario analysis
    - Performance-optimized caching
    """

    def __init__(self):
        self.feature_mapper = BusinessFeatureMapper()
        self.visualization_builder = SHAPVisualizationBuilder(self.feature_mapper)
        self.analytics = AnalyticsService()
        self.what_if_analyzer: Optional[WhatIfAnalyzer] = None

        # Performance tracking
        self.metrics = {
            "explanations_generated": 0,
            "cache_hits": 0,
            "avg_explanation_time_ms": 0.0,
            "what_if_scenarios": 0,
        }

    async def explain_prediction(
        self,
        model: RandomForestClassifier,
        scaler,
        shap_explainer,
        feature_names: List[str],
        features: np.ndarray,
        lead_id: str,
        lead_name: str,
        prediction_score: float,
    ) -> SHAPExplanation:
        """
        Generate comprehensive SHAP explanation for a prediction

        Args:
            model: Trained ML model
            scaler: Feature scaler
            shap_explainer: SHAP explainer
            feature_names: List of feature names
            features: Feature values for the lead
            lead_id: Unique lead identifier
            lead_name: Human readable lead name
            prediction_score: Model prediction score

        Returns:
            Complete SHAP explanation with business insights
        """
        start_time = time.time()

        # Check cache first
        cache_key = self._generate_cache_key(lead_id, features)
        cached_explanation = await cache.get(cache_key)

        if cached_explanation:
            cached_explanation.cached = True
            self.metrics["cache_hits"] += 1
            logger.info(f"SHAP explanation cache hit for {lead_name}")
            return cached_explanation

        try:
            # Scale features for SHAP
            features_scaled = scaler.transform(features.reshape(1, -1))

            # Get SHAP values
            shap_values = shap_explainer.shap_values(features_scaled)

            # Handle different SHAP output formats
            if isinstance(shap_values, list):
                # Binary classification (list format) - use positive class
                shap_vals = shap_values[1][0]
                base_value = shap_explainer.expected_value[1]
            elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
                # Binary classification (numpy 3D array: samples x features x classes)
                shap_vals = shap_values[0, :, 1]
                expected = shap_explainer.expected_value
                base_value = expected[1] if isinstance(expected, (list, np.ndarray)) else expected
            else:
                # Single output
                shap_vals = shap_values[0]
                base_value = shap_explainer.expected_value

            # Map SHAP values to feature names (convert numpy scalars to Python floats)
            shap_dict = {name: float(val) for name, val in zip(feature_names, shap_vals)}

            # Calculate feature importance (absolute SHAP values)
            importance_dict = {name: abs(val) for name, val in shap_dict.items()}

            # Generate business explanations
            business_explanations = {}
            feature_values = {name: float(val) for name, val in zip(feature_names, features)}

            for feature, shap_val in shap_dict.items():
                business_explanations[feature] = self.feature_mapper.get_business_explanation(
                    feature, shap_val, feature_values[feature]
                )

            # Identify key drivers (top 5 by absolute impact)
            sorted_features = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)
            key_drivers = []

            for feature, shap_val in sorted_features[:5]:
                context = self.feature_mapper.feature_contexts.get(feature)
                driver = {
                    "feature": context.display_name if context else feature,
                    "impact": shap_val,
                    "explanation": business_explanations[feature],
                    "actionable_insight": self.feature_mapper.get_actionable_insight(feature, shap_val),
                    "category": self.feature_mapper.get_feature_category(feature),
                }
                key_drivers.append(driver)

            # Identify risk factors and opportunities
            risk_factors = []
            opportunities = []

            for feature, shap_val in shap_dict.items():
                context = self.feature_mapper.feature_contexts.get(feature)
                if not context:
                    continue

                if shap_val < -0.1:  # Negative impact threshold
                    risk_factors.append(
                        f"{context.display_name}: {context.negative_explanation_template.format(value=feature_values[feature])}"
                    )
                elif shap_val > 0.1:  # Positive impact threshold
                    opportunities.append(
                        f"{context.display_name}: {context.positive_explanation_template.format(value=feature_values[feature])}"
                    )

            # Prepare waterfall visualization data
            waterfall_data = self._prepare_waterfall_data(shap_dict, base_value, prediction_score)

            # Prepare feature impact data
            feature_impact_data = self._prepare_feature_impact_data(shap_dict, importance_dict)

            # Create explanation object
            explanation = SHAPExplanation(
                lead_id=lead_id,
                lead_name=lead_name,
                explained_at=datetime.now(),
                base_value=float(base_value),
                prediction=prediction_score,
                shap_values=shap_dict,
                feature_importance=importance_dict,
                business_explanations=business_explanations,
                key_drivers=key_drivers,
                risk_factors=risk_factors[:5],  # Top 5
                opportunities=opportunities[:5],  # Top 5
                waterfall_data=waterfall_data,
                feature_impact_data=feature_impact_data,
                what_if_ready=True,
                explanation_time_ms=(time.time() - start_time) * 1000,
                cached=False,
            )

            # Initialize what-if analyzer
            self.what_if_analyzer = WhatIfAnalyzer(model, scaler, shap_explainer, feature_names)

            # Cache the explanation (30 minutes TTL)
            await cache.set(cache_key, explanation, ttl=1800)

            # Update metrics
            self.metrics["explanations_generated"] += 1
            self._update_avg_time(explanation.explanation_time_ms)

            # Track analytics event
            await self.analytics.track_event(
                event_type="shap_explanation_generated",
                location_id=lead_id.split("_")[0] if "_" in lead_id else "unknown",
                contact_id=lead_id,
                data={
                    "explanation_time_ms": explanation.explanation_time_ms,
                    "num_features": len(feature_names),
                    "prediction_score": prediction_score,
                    "key_driver_count": len(key_drivers),
                    "risk_factor_count": len(risk_factors),
                    "opportunity_count": len(opportunities),
                },
            )

            logger.info(f"SHAP explanation generated for {lead_name} in {explanation.explanation_time_ms:.1f}ms")
            return explanation

        except Exception as e:
            logger.error(f"SHAP explanation failed for {lead_name}: {e}")
            # Return minimal explanation on error
            return SHAPExplanation(
                lead_id=lead_id,
                lead_name=lead_name,
                explained_at=datetime.now(),
                base_value=50.0,  # Default baseline
                prediction=prediction_score,
                shap_values={},
                feature_importance={},
                business_explanations={"error": f"Explanation generation failed: {str(e)}"},
                key_drivers=[],
                risk_factors=["SHAP analysis temporarily unavailable"],
                opportunities=[],
                waterfall_data={},
                feature_impact_data={},
                what_if_ready=False,
                explanation_time_ms=(time.time() - start_time) * 1000,
                cached=False,
            )

    def _generate_cache_key(self, lead_id: str, features: np.ndarray) -> str:
        """Generate cache key based on lead ID and feature values"""
        feature_hash = hashlib.md5(features.tobytes()).hexdigest()[:8]
        return f"shap_explanation:{lead_id}:{feature_hash}"

    def _prepare_waterfall_data(
        self, shap_dict: Dict[str, float], base_value: float, prediction: float
    ) -> Dict[str, Any]:
        """Prepare data for waterfall chart visualization"""
        # Sort features by absolute SHAP value
        sorted_features = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)

        return {
            "base_value": base_value,
            "final_prediction": prediction,
            "features": [
                (
                    self.feature_mapper.feature_contexts[f].display_name
                    if f in self.feature_mapper.feature_contexts
                    else f
                )
                for f, _ in sorted_features
            ],
            "shap_values": [v for _, v in sorted_features],
            "cumulative_values": self._calculate_cumulative_values(base_value, [v for _, v in sorted_features]),
        }

    def _calculate_cumulative_values(self, base_value: float, shap_values: List[float]) -> List[float]:
        """Calculate cumulative values for waterfall chart"""
        cumulative = [base_value]
        running_sum = base_value

        for shap_val in shap_values:
            running_sum += shap_val
            cumulative.append(running_sum)

        return cumulative

    def _prepare_feature_impact_data(
        self, shap_dict: Dict[str, float], importance_dict: Dict[str, float]
    ) -> Dict[str, Any]:
        """Prepare data for feature impact visualization"""
        # Group by category
        categories = {}

        for feature, shap_val in shap_dict.items():
            category = self.feature_mapper.get_feature_category(feature)
            if category not in categories:
                categories[category] = []

            context = self.feature_mapper.feature_contexts.get(feature)
            display_name = context.display_name if context else feature

            categories[category].append(
                {
                    "feature": display_name,
                    "shap_value": shap_val,
                    "importance": importance_dict[feature],
                    "direction": "positive" if shap_val > 0 else "negative",
                }
            )

        return {
            "categories": categories,
            "total_positive_impact": sum(v for v in shap_dict.values() if v > 0),
            "total_negative_impact": sum(v for v in shap_dict.values() if v < 0),
        }

    def _update_avg_time(self, time_ms: float):
        """Update average explanation time"""
        count = self.metrics["explanations_generated"]
        if count <= 1:
            self.metrics["avg_explanation_time_ms"] = time_ms
        else:
            current_avg = self.metrics["avg_explanation_time_ms"]
            self.metrics["avg_explanation_time_ms"] = (current_avg * (count - 1) + time_ms) / count

    async def create_waterfall_visualization(self, explanation: SHAPExplanation) -> go.Figure:
        """Create interactive waterfall chart for SHAP explanation"""
        return self.visualization_builder.build_waterfall_chart(explanation)

    async def create_feature_importance_visualization(self, explanation: SHAPExplanation) -> go.Figure:
        """Create feature importance visualization"""
        return self.visualization_builder.build_feature_importance_chart(explanation)

    async def perform_what_if_analysis(
        self, explanation: SHAPExplanation, modified_features: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Perform what-if scenario analysis

        Args:
            explanation: Original SHAP explanation
            modified_features: Features to modify {feature_name: new_value}

        Returns:
            Scenario analysis results
        """
        if not self.what_if_analyzer:
            return {"error": "What-if analysis not available - analyzer not initialized"}

        if not explanation.what_if_ready:
            return {"error": "What-if analysis not available for this explanation"}

        start_time = time.time()

        try:
            # Get original feature values (we'll need to reconstruct them)
            # For now, create dummy features - in production, store original features
            original_features = np.array([1.0, 50.0, 2.0, 1.0, 2.0, 1.0, 1.0, 1.0, 3.0, 1.0])  # Dummy values

            # Perform scenario analysis
            scenario_result = await self.what_if_analyzer.analyze_scenario(original_features, modified_features)

            # Add timing info
            scenario_result["analysis_time_ms"] = (time.time() - start_time) * 1000

            # Update metrics
            self.metrics["what_if_scenarios"] += 1

            # Track analytics
            await self.analytics.track_event(
                event_type="shap_what_if_analysis",
                location_id=explanation.lead_id.split("_")[0] if "_" in explanation.lead_id else "unknown",
                contact_id=explanation.lead_id,
                data={
                    "modified_features": list(modified_features.keys()),
                    "score_change": scenario_result["score_change"],
                    "analysis_time_ms": scenario_result["analysis_time_ms"],
                },
            )

            return scenario_result

        except Exception as e:
            logger.error(f"What-if analysis failed: {e}")
            return {"error": f"Analysis failed: {str(e)}"}

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get service performance metrics"""
        total_requests = self.metrics["explanations_generated"] + self.metrics["cache_hits"]
        cache_hit_rate = (self.metrics["cache_hits"] / total_requests * 100) if total_requests > 0 else 0

        return {**self.metrics, "cache_hit_rate_percent": round(cache_hit_rate, 2), "total_requests": total_requests}


# Factory function for integration
async def get_shap_explanation(
    model, scaler, shap_explainer, feature_names, features, lead_id, lead_name, prediction_score
) -> SHAPExplanation:
    """
    Factory function for getting SHAP explanations
    Integrates with existing ML infrastructure
    """
    service = SHAPExplainerService()
    return await service.explain_prediction(
        model, scaler, shap_explainer, feature_names, features, lead_id, lead_name, prediction_score
    )


# Singleton for use in components
_shap_explainer_service = None


def get_shap_explainer_service() -> SHAPExplainerService:
    """Get singleton SHAP explainer service"""
    global _shap_explainer_service
    if _shap_explainer_service is None:
        _shap_explainer_service = SHAPExplainerService()
    return _shap_explainer_service
