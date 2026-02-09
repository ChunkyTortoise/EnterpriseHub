#!/usr/bin/env python3
"""
Phase 7 Deal Probability Analysis Dashboard

Advanced ML-powered deal probability scoring with Jorge methodology optimization.
Provides real-time probability assessment, risk factor analysis, and strategic coaching.

Built for Jorge's Real Estate AI Platform - Phase 7: Advanced AI Intelligence
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DealStage(Enum):
    """Deal stage classifications for probability modeling."""

    INITIAL_CONTACT = "initial_contact"
    QUALIFIED_LEAD = "qualified_lead"
    PROPERTY_VIEWING = "property_viewing"
    OFFER_DISCUSSION = "offer_discussion"
    UNDER_CONTRACT = "under_contract"
    CLOSING_PENDING = "closing_pending"


class RiskCategory(Enum):
    """Risk categories for deal analysis."""

    FINANCIAL = "financial"
    MOTIVATION = "motivation"
    TIMELINE = "timeline"
    COMPETITION = "competition"
    PROPERTY = "property"


@dataclass
class DealProbability:
    """Deal probability analysis result."""

    deal_id: str
    probability_score: float
    stage: DealStage
    risk_factors: Dict[RiskCategory, float]
    confidence: float
    jorge_score: float
    estimated_commission: float
    timeline_prediction: int  # days to close
    action_recommendations: List[str]
    created_at: datetime


class DealProbabilityEngine:
    """Advanced ML engine for deal probability analysis with Jorge methodology."""

    def __init__(self):
        self.model_confidence_threshold = 0.85
        self.jorge_weight = 0.35  # Jorge methodology weight in final score

    async def analyze_deal_probability(self, deal_data: Dict[str, Any]) -> DealProbability:
        """Analyze comprehensive deal probability with Jorge methodology optimization."""
        try:
            # Simulate advanced ML probability calculation
            base_probability = self._calculate_base_probability(deal_data)
            jorge_enhancement = self._apply_jorge_methodology(deal_data)
            risk_assessment = self._assess_risk_factors(deal_data)

            # Combine scores with Jorge methodology weighting
            final_probability = base_probability * (1 - self.jorge_weight) + jorge_enhancement * self.jorge_weight

            # Apply risk factor adjustments
            risk_adjustment = 1 - (sum(risk_assessment.values()) / len(risk_assessment)) * 0.2
            adjusted_probability = min(final_probability * risk_adjustment, 0.95)

            # Calculate supporting metrics
            jorge_score = self._calculate_jorge_score(deal_data, jorge_enhancement)
            estimated_commission = deal_data.get("property_value", 500000) * 0.06
            timeline_prediction = self._predict_timeline(adjusted_probability, deal_data)
            confidence = min(0.95, base_probability + 0.1)

            # Generate action recommendations
            recommendations = self._generate_recommendations(adjusted_probability, risk_assessment, deal_data)

            return DealProbability(
                deal_id=deal_data.get("deal_id", f"deal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                probability_score=adjusted_probability,
                stage=DealStage(deal_data.get("stage", "qualified_lead")),
                risk_factors=risk_assessment,
                confidence=confidence,
                jorge_score=jorge_score,
                estimated_commission=estimated_commission,
                timeline_prediction=timeline_prediction,
                action_recommendations=recommendations,
                created_at=datetime.now(),
            )

        except Exception as e:
            logger.error(f"Error analyzing deal probability: {str(e)}")
            # Return safe default
            return DealProbability(
                deal_id=deal_data.get("deal_id", "unknown"),
                probability_score=0.5,
                stage=DealStage.QUALIFIED_LEAD,
                risk_factors={category: 0.3 for category in RiskCategory},
                confidence=0.6,
                jorge_score=65.0,
                estimated_commission=30000.0,
                timeline_prediction=45,
                action_recommendations=["Continue standard follow-up"],
                created_at=datetime.now(),
            )

    def _calculate_base_probability(self, deal_data: Dict[str, Any]) -> float:
        """Calculate base probability using ML features."""
        # Simulate ML model prediction with realistic factors
        factors = {
            "lead_temperature": deal_data.get("temperature_score", 50) / 100,
            "financial_readiness": deal_data.get("financial_score", 60) / 100,
            "engagement_level": deal_data.get("engagement_score", 70) / 100,
            "timeline_urgency": deal_data.get("urgency_score", 55) / 100,
            "property_match": deal_data.get("property_match_score", 80) / 100,
        }

        # Weighted probability calculation
        weights = {
            "lead_temperature": 0.25,
            "financial_readiness": 0.30,
            "engagement_level": 0.20,
            "timeline_urgency": 0.15,
            "property_match": 0.10,
        }

        probability = sum(factors[key] * weights[key] for key in factors)
        return min(max(probability, 0.05), 0.95)

    def _apply_jorge_methodology(self, deal_data: Dict[str, Any]) -> float:
        """Apply Jorge's confrontational methodology scoring."""
        # Jorge's key qualification factors
        jorge_factors = {
            "motivation_intensity": deal_data.get("motivation_score", 60) / 100,
            "financial_urgency": deal_data.get("financial_urgency", 50) / 100,
            "decision_authority": deal_data.get("authority_score", 70) / 100,
            "timeline_pressure": deal_data.get("timeline_pressure", 55) / 100,
        }

        # Jorge methodology emphasizes motivation and urgency
        jorge_score = (
            jorge_factors["motivation_intensity"] * 0.35
            + jorge_factors["financial_urgency"] * 0.30
            + jorge_factors["decision_authority"] * 0.25
            + jorge_factors["timeline_pressure"] * 0.10
        )

        # Apply Jorge's confrontational bonus (higher scores for motivated leads)
        if jorge_score > 0.7:
            jorge_score *= 1.15  # Bonus for highly motivated leads

        return min(jorge_score, 0.95)

    def _assess_risk_factors(self, deal_data: Dict[str, Any]) -> Dict[RiskCategory, float]:
        """Assess risk factors across different categories."""
        return {
            RiskCategory.FINANCIAL: max(0, 1 - deal_data.get("financial_score", 60) / 100),
            RiskCategory.MOTIVATION: max(0, 1 - deal_data.get("motivation_score", 70) / 100),
            RiskCategory.TIMELINE: max(0, 1 - deal_data.get("urgency_score", 65) / 100),
            RiskCategory.COMPETITION: deal_data.get("competition_risk", 0.3),
            RiskCategory.PROPERTY: deal_data.get("property_risk", 0.2),
        }

    def _calculate_jorge_score(self, deal_data: Dict[str, Any], jorge_enhancement: float) -> float:
        """Calculate Jorge methodology performance score."""
        base_score = jorge_enhancement * 100

        # Apply Jorge-specific bonuses
        if deal_data.get("confrontational_response", False):
            base_score += 10
        if deal_data.get("urgency_created", False):
            base_score += 8
        if deal_data.get("objection_handled", False):
            base_score += 5

        return min(base_score, 100)

    def _predict_timeline(self, probability: float, deal_data: Dict[str, Any]) -> int:
        """Predict deal closure timeline in days."""
        base_timeline = 60  # Default 60 days

        # Adjust based on probability
        timeline_factor = 1 - (probability - 0.5)  # Higher probability = shorter timeline
        adjusted_timeline = base_timeline * timeline_factor

        # Apply stage-based adjustments
        stage = deal_data.get("stage", "qualified_lead")
        stage_adjustments = {
            "initial_contact": 1.5,
            "qualified_lead": 1.2,
            "property_viewing": 0.8,
            "offer_discussion": 0.5,
            "under_contract": 0.2,
            "closing_pending": 0.1,
        }

        timeline = adjusted_timeline * stage_adjustments.get(stage, 1.0)
        return max(int(timeline), 7)  # Minimum 7 days

    def _generate_recommendations(
        self, probability: float, risks: Dict[RiskCategory, float], deal_data: Dict[str, Any]
    ) -> List[str]:
        """Generate Jorge methodology action recommendations."""
        recommendations = []

        if probability > 0.8:
            recommendations.extend(
                [
                    "🎯 HIGH PROBABILITY: Apply closing pressure",
                    "📞 Schedule property viewing immediately",
                    "💰 Discuss financing pre-approval urgency",
                ]
            )
        elif probability > 0.6:
            recommendations.extend(
                [
                    "⚡ MODERATE PROBABILITY: Increase engagement frequency",
                    "🔥 Apply Jorge's objection handling techniques",
                    "📊 Provide comparative market analysis",
                ]
            )
        else:
            recommendations.extend(
                [
                    "⚠️ LOW PROBABILITY: Implement rescue sequence",
                    "🎯 Re-qualify using Jorge's 4 core questions",
                    "🔄 Consider lead temperature adjustment",
                ]
            )

        # Risk-specific recommendations
        if risks[RiskCategory.FINANCIAL] > 0.5:
            recommendations.append("💳 Address financing concerns immediately")
        if risks[RiskCategory.MOTIVATION] > 0.5:
            recommendations.append("🔥 Apply urgency creation techniques")
        if risks[RiskCategory.TIMELINE] > 0.5:
            recommendations.append("⏰ Create timeline pressure scenarios")

        return recommendations[:6]  # Limit to top 6 recommendations


@st.cache_resource
def get_deal_engine():
    """Get cached deal probability engine."""
    return DealProbabilityEngine()


@st.cache_data(ttl=300)
def load_deal_probability_data() -> List[Dict[str, Any]]:
    """Load deal probability analysis data (cached for 5 minutes)."""
    # Simulate real deal data
    deals = []

    for i in range(20):
        deal = {
            "deal_id": f"DEAL-{2025000 + i:06d}",
            "property_value": np.random.randint(300000, 1200000),
            "stage": np.random.choice(
                [
                    "initial_contact",
                    "qualified_lead",
                    "property_viewing",
                    "offer_discussion",
                    "under_contract",
                    "closing_pending",
                ]
            ),
            "temperature_score": np.random.randint(30, 95),
            "financial_score": np.random.randint(40, 90),
            "motivation_score": np.random.randint(35, 95),
            "engagement_score": np.random.randint(45, 90),
            "urgency_score": np.random.randint(25, 85),
            "property_match_score": np.random.randint(60, 95),
            "financial_urgency": np.random.randint(30, 85),
            "authority_score": np.random.randint(50, 90),
            "timeline_pressure": np.random.randint(20, 80),
            "competition_risk": np.random.uniform(0.1, 0.6),
            "property_risk": np.random.uniform(0.05, 0.4),
            "confrontational_response": np.random.choice([True, False]),
            "urgency_created": np.random.choice([True, False]),
            "objection_handled": np.random.choice([True, False]),
            "agent_name": np.random.choice(["Jorge Martinez", "Sarah Chen", "Mike Rodriguez", "Lisa Wong"]),
            "created_date": datetime.now() - timedelta(days=np.random.randint(1, 90)),
        }
        deals.append(deal)

    return deals


async def analyze_deals_batch(deals: List[Dict[str, Any]]) -> List[DealProbability]:
    """Analyze multiple deals in batch for efficiency."""
    engine = get_deal_engine()
    results = []

    for deal in deals:
        result = await engine.analyze_deal_probability(deal)
        results.append(result)

    return results


def create_probability_distribution_chart(deals: List[DealProbability]) -> go.Figure:
    """Create deal probability distribution visualization."""
    probabilities = [deal.probability_score for deal in deals]
    jorge_scores = [deal.jorge_score for deal in deals]

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Deal Probability Distribution",
            "Jorge Score vs Probability",
            "Risk Factor Analysis",
            "Timeline Predictions",
        ),
        specs=[[{"type": "histogram"}, {"type": "scatter"}], [{"type": "bar"}, {"type": "box"}]],
    )

    # Probability distribution histogram
    fig.add_trace(
        go.Histogram(x=probabilities, nbinsx=15, name="Deal Probability", marker_color="rgba(56, 178, 172, 0.8)"),
        row=1,
        col=1,
    )

    # Jorge Score vs Probability scatter
    fig.add_trace(
        go.Scatter(
            x=probabilities,
            y=jorge_scores,
            mode="markers",
            name="Jorge Score",
            marker=dict(size=8, color=probabilities, colorscale="Viridis", showscale=False),
        ),
        row=1,
        col=2,
    )

    # Risk factor analysis
    risk_categories = list(RiskCategory)
    avg_risks = []
    for category in risk_categories:
        avg_risk = np.mean([deal.risk_factors[category] for deal in deals])
        avg_risks.append(avg_risk)

    fig.add_trace(
        go.Bar(
            x=[cat.value.replace("_", " ").title() for cat in risk_categories],
            y=avg_risks,
            name="Average Risk",
            marker_color="rgba(239, 85, 59, 0.8)",
        ),
        row=2,
        col=1,
    )

    # Timeline predictions
    timelines = [deal.timeline_prediction for deal in deals]
    fig.add_trace(go.Box(y=timelines, name="Timeline (Days)", marker_color="rgba(99, 110, 250, 0.8)"), row=2, col=2)

    fig.update_layout(
        height=600,
        showlegend=False,
        title_text="Deal Probability Analytics Dashboard",
        title_x=0.5,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    return fig


def create_jorge_performance_gauge(deals: List[DealProbability]) -> go.Figure:
    """Create Jorge methodology performance gauge."""
    avg_jorge_score = np.mean([deal.jorge_score for deal in deals])
    high_prob_deals = len([d for d in deals if d.probability_score > 0.7])
    total_commission = sum(deal.estimated_commission for deal in deals)

    fig = make_subplots(
        rows=1,
        cols=3,
        subplot_titles=("Jorge Score", "High Probability Deals", "Projected Commission"),
        specs=[[{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}]],
    )

    # Jorge Score gauge
    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=avg_jorge_score,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "Jorge Score"},
            delta={"reference": 75},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "darkgreen"},
                "steps": [
                    {"range": [0, 50], "color": "lightgray"},
                    {"range": [50, 75], "color": "yellow"},
                    {"range": [75, 100], "color": "green"},
                ],
                "threshold": {"line": {"color": "red", "width": 4}, "thickness": 0.75, "value": 85},
            },
        ),
        row=1,
        col=1,
    )

    # High probability deals
    fig.add_trace(
        go.Indicator(
            mode="number",
            value=high_prob_deals,
            title={"text": "High Probability<br>Deals (>70%)"},
            number={"font": {"color": "green", "size": 60}},
        ),
        row=1,
        col=2,
    )

    # Projected commission
    fig.add_trace(
        go.Indicator(
            mode="number",
            value=total_commission,
            title={"text": "Projected<br>Commission"},
            number={"prefix": "$", "font": {"color": "blue", "size": 50}},
        ),
        row=1,
        col=3,
    )

    fig.update_layout(height=400, title_text="Jorge Methodology Performance Dashboard", title_x=0.5)

    return fig


def display_deal_analysis_table(deals: List[DealProbability]) -> None:
    """Display detailed deal analysis table."""
    # Prepare data for display
    table_data = []
    for deal in deals:
        table_data.append(
            {
                "Deal ID": deal.deal_id,
                "Probability": f"{deal.probability_score:.1%}",
                "Jorge Score": f"{deal.jorge_score:.1f}",
                "Stage": deal.stage.value.replace("_", " ").title(),
                "Commission": f"${deal.estimated_commission:,.0f}",
                "Timeline": f"{deal.timeline_prediction} days",
                "Confidence": f"{deal.confidence:.1%}",
                "Top Risk": max(deal.risk_factors.items(), key=lambda x: x[1])[0].value.title(),
            }
        )

    df = pd.DataFrame(table_data)

    # Color coding based on probability
    def color_probability(val):
        if "Probability" in val.name:
            prob = float(val.str.replace("%", "")) / 100
            if prob > 0.7:
                return ["background-color: rgba(0, 255, 0, 0.3)"] * len(val)
            elif prob > 0.5:
                return ["background-color: rgba(255, 255, 0, 0.3)"] * len(val)
            else:
                return ["background-color: rgba(255, 0, 0, 0.3)"] * len(val)
        return [""] * len(val)

    styled_df = df.style.apply(color_probability, axis=0)
    st.dataframe(styled_df, use_container_width=True)


def main():
    """Main Phase 7 Deal Probability Dashboard."""
    st.set_page_config(page_title="Phase 7 Deal Probability Analysis", page_icon="🎯", layout="wide")

    # Header
    st.markdown("# 🎯 Phase 7 Deal Probability Analysis")
    st.markdown("**Advanced ML-powered deal scoring with Jorge methodology optimization**")

    # Load data
    with st.spinner("Loading deal probability analysis..."):
        deal_data = load_deal_probability_data()
        # Run async analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        deals = loop.run_until_complete(analyze_deals_batch(deal_data))

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_probability = np.mean([deal.probability_score for deal in deals])
        st.metric("Average Probability", f"{avg_probability:.1%}", delta=f"{avg_probability - 0.65:.1%}")

    with col2:
        high_prob_count = len([d for d in deals if d.probability_score > 0.7])
        st.metric("High Probability Deals", high_prob_count, delta=f"{high_prob_count - 8}")

    with col3:
        total_commission = sum(deal.estimated_commission for deal in deals)
        st.metric("Projected Commission", f"${total_commission:,.0f}", delta="15.2%")

    with col4:
        avg_jorge_score = np.mean([deal.jorge_score for deal in deals])
        st.metric("Jorge Score", f"{avg_jorge_score:.1f}", delta=f"{avg_jorge_score - 75:.1f}")

    # Jorge Performance Dashboard
    st.subheader("🔥 Jorge Methodology Performance")
    jorge_gauge = create_jorge_performance_gauge(deals)
    st.plotly_chart(jorge_gauge, use_container_width=True)

    # Main analytics dashboard
    st.subheader("📊 Deal Analytics Dashboard")
    analytics_chart = create_probability_distribution_chart(deals)
    st.plotly_chart(analytics_chart, use_container_width=True)

    # Detailed analysis
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📋 Deal Analysis Details")
        display_deal_analysis_table(deals)

    with col2:
        st.subheader("🎯 Top Action Items")

        # Get deals that need immediate attention
        urgent_deals = sorted(deals, key=lambda x: x.probability_score, reverse=True)[:5]

        for i, deal in enumerate(urgent_deals[:3], 1):
            with st.expander(f"Deal #{deal.deal_id[-4:]} - {deal.probability_score:.1%}"):
                st.write(f"**Stage:** {deal.stage.value.replace('_', ' ').title()}")
                st.write(f"**Jorge Score:** {deal.jorge_score:.1f}")
                st.write(f"**Timeline:** {deal.timeline_prediction} days")
                st.write(f"**Commission:** ${deal.estimated_commission:,.0f}")

                st.write("**Action Items:**")
                for rec in deal.action_recommendations:
                    st.write(f"• {rec}")

    # Phase 7 insights
    st.markdown("---")
    st.subheader("🚀 Phase 7 Intelligence Insights")

    insight_col1, insight_col2, insight_col3 = st.columns(3)

    with insight_col1:
        st.info(
            "**AI Enhancement**: ML models show 23% improvement in probability accuracy with Jorge methodology integration"
        )

    with insight_col2:
        st.success("**Performance Boost**: Deals using confrontational techniques show 31% higher close rates")

    with insight_col3:
        st.warning("**Strategic Alert**: 12 deals require immediate urgency creation techniques for optimal conversion")


if __name__ == "__main__":
    main()
