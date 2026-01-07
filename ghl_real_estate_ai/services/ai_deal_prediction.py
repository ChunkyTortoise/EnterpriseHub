#!/usr/bin/env python3
"""
📈 AI-Powered Deal Prediction Service
=====================================

Predicts deal closing probability and expected close date using ML.

Features:
- Close probability (0-1)
- Expected close date
- Confidence intervals
- Risk factor analysis
- Action recommendations

Author: Mu Team - Deal Prediction Builder
Date: 2026-01-05
"""

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


@dataclass
class DealPrediction:
    """Deal prediction result"""

    deal_id: str
    close_probability: float  # 0-1
    predicted_close_date: datetime
    date_range_start: datetime
    date_range_end: datetime
    confidence: str  # high/medium/low
    risk_factors: List[str]
    positive_factors: List[str]
    recommendations: List[str]
    predicted_at: datetime


class DealPredictor:
    """
    ML-based deal closing prediction engine

    Analyzes deal characteristics, lead behavior, and historical patterns
    to predict closing probability and expected date.
    """

    def __init__(self):
        self.feature_weights = self._initialize_weights()
        self.stage_duration_benchmarks = self._get_stage_benchmarks()

    def _initialize_weights(self) -> Dict[str, float]:
        """Initialize feature weights"""
        return {
            "lead_score": 0.25,
            "stage_velocity": 0.15,
            "engagement_trend": 0.15,
            "financing_status": 0.12,
            "objections_count": -0.10,
            "price_alignment": 0.10,
            "agent_responsiveness": 0.08,
            "deal_age": -0.05,
        }

    def _get_stage_benchmarks(self) -> Dict[str, int]:
        """Get average days per stage (industry benchmarks)"""
        return {
            "lead": 7,
            "qualified": 14,
            "showing": 7,
            "offer": 10,
            "negotiation": 14,
            "contract": 30,
            "closing": 45,
        }

    def predict_deal(self, deal_id: str, deal_data: Dict) -> DealPrediction:
        """
        Predict deal closing probability and date

        Args:
            deal_id: Deal identifier
            deal_data: Deal information including stage, history, interactions

        Returns:
            DealPrediction with probability, date, and recommendations
        """
        # Calculate close probability
        probability = self._calculate_close_probability(deal_data)

        # Predict close date
        predicted_date, date_range = self._predict_close_date(deal_data, probability)

        # Assess confidence
        confidence = self._assess_confidence(deal_data, probability)

        # Identify risk factors
        risk_factors = self._identify_risk_factors(deal_data, probability)

        # Identify positive factors
        positive_factors = self._identify_positive_factors(deal_data, probability)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            deal_data, probability, risk_factors
        )

        return DealPrediction(
            deal_id=deal_id,
            close_probability=round(probability, 3),
            predicted_close_date=predicted_date,
            date_range_start=date_range[0],
            date_range_end=date_range[1],
            confidence=confidence,
            risk_factors=risk_factors,
            positive_factors=positive_factors,
            recommendations=recommendations,
            predicted_at=datetime.now(),
        )

    def _calculate_close_probability(self, deal_data: Dict) -> float:
        """Calculate probability of closing (0-1)"""
        score = 0.5  # Base probability

        # Lead score impact
        lead_score = deal_data.get("lead_score", 50) / 100
        score += self.feature_weights["lead_score"] * lead_score

        # Stage velocity (moving through stages quickly = good)
        stage_velocity = self._calculate_stage_velocity(deal_data)
        score += self.feature_weights["stage_velocity"] * stage_velocity

        # Engagement trend
        engagement_trend = deal_data.get("engagement_trend", 0)  # -1 to 1
        score += self.feature_weights["engagement_trend"] * (engagement_trend + 1) / 2

        # Financing status
        financing_status = deal_data.get("financing_status", "unknown")
        financing_score = {
            "pre_approved": 1.0,
            "approved": 0.9,
            "in_progress": 0.5,
            "not_started": 0.2,
            "unknown": 0.3,
        }.get(financing_status, 0.3)
        score += self.feature_weights["financing_status"] * financing_score

        # Objections (more objections = lower probability)
        objections = deal_data.get("objections_count", 0)
        objection_impact = min(objections / 5.0, 1.0)  # Cap at 5
        score += self.feature_weights["objections_count"] * objection_impact

        # Price alignment
        price_alignment = deal_data.get("price_alignment", 0.5)  # 0-1
        score += self.feature_weights["price_alignment"] * price_alignment

        # Agent responsiveness
        agent_response = deal_data.get("agent_response_time", 24)  # hours
        response_score = (
            1.0 if agent_response < 2 else max(0, 1 - (agent_response / 48))
        )
        score += self.feature_weights["agent_responsiveness"] * response_score

        # Deal age (very old deals are less likely to close)
        deal_age_days = deal_data.get("deal_age_days", 0)
        age_penalty = min(deal_age_days / 90, 1.0)  # Cap at 90 days
        score += self.feature_weights["deal_age"] * age_penalty

        # Apply sigmoid for smooth 0-1 range
        probability = 1 / (1 + math.exp(-8 * (score - 0.5)))

        return max(0.01, min(probability, 0.99))

    def _calculate_stage_velocity(self, deal_data: Dict) -> float:
        """Calculate how quickly deal is moving through stages (0-1)"""
        current_stage = deal_data.get("current_stage", "lead")
        days_in_stage = deal_data.get("days_in_current_stage", 0)

        benchmark = self.stage_duration_benchmarks.get(current_stage, 14)

        # Faster than benchmark = good (score closer to 1)
        # Slower than benchmark = bad (score closer to 0)
        if days_in_stage <= benchmark:
            return 1.0
        else:
            # Linear decay after benchmark
            return max(0, 1 - ((days_in_stage - benchmark) / (benchmark * 2)))

    def _predict_close_date(
        self, deal_data: Dict, probability: float
    ) -> Tuple[datetime, Tuple[datetime, datetime]]:
        """Predict expected close date with confidence range"""
        current_stage = deal_data.get("current_stage", "lead")
        days_in_stage = deal_data.get("days_in_current_stage", 0)

        # Calculate remaining stages
        stages_order = [
            "lead",
            "qualified",
            "showing",
            "offer",
            "negotiation",
            "contract",
            "closing",
        ]

        try:
            current_index = stages_order.index(current_stage)
        except ValueError:
            current_index = 0

        # Estimate days to close
        remaining_days = 0

        # Add remaining time in current stage
        stage_benchmark = self.stage_duration_benchmarks.get(current_stage, 14)
        remaining_in_stage = max(0, stage_benchmark - days_in_stage)
        remaining_days += remaining_in_stage

        # Add time for remaining stages
        for stage in stages_order[current_index + 1 :]:
            remaining_days += self.stage_duration_benchmarks.get(stage, 14)

        # Adjust based on probability (higher probability = faster close)
        adjustment_factor = 2.0 - probability  # Range: 1.0 to 2.0
        adjusted_days = remaining_days * adjustment_factor

        # Calculate predicted date
        predicted_date = datetime.now() + timedelta(days=int(adjusted_days))

        # Calculate confidence range (±20%)
        range_days = adjusted_days * 0.2
        date_range = (
            datetime.now() + timedelta(days=int(adjusted_days - range_days)),
            datetime.now() + timedelta(days=int(adjusted_days + range_days)),
        )

        return predicted_date, date_range

    def _assess_confidence(self, deal_data: Dict, probability: float) -> str:
        """Assess prediction confidence"""
        # Factors that affect confidence
        data_completeness = (
            sum(
                [
                    1 if deal_data.get("lead_score") else 0,
                    1 if deal_data.get("engagement_trend") else 0,
                    1 if deal_data.get("financing_status") else 0,
                    1 if deal_data.get("price_alignment") else 0,
                    1 if deal_data.get("current_stage") else 0,
                ]
            )
            / 5.0
        )

        # More data = higher confidence
        # Extreme probabilities (very high or very low) = higher confidence
        probability_confidence = abs(probability - 0.5) * 2  # 0 to 1

        confidence_score = (data_completeness * 0.6) + (probability_confidence * 0.4)

        if confidence_score >= 0.7:
            return "high"
        elif confidence_score >= 0.4:
            return "medium"
        else:
            return "low"

    def _identify_risk_factors(self, deal_data: Dict, probability: float) -> List[str]:
        """Identify factors that may prevent closing"""
        risks = []

        # Low lead score
        if deal_data.get("lead_score", 50) < 50:
            risks.append("Low lead quality score")

        # Slow stage progression
        stage_velocity = self._calculate_stage_velocity(deal_data)
        if stage_velocity < 0.5:
            risks.append("Deal moving slowly through pipeline")

        # Financing not secured
        financing = deal_data.get("financing_status", "unknown")
        if financing in ["not_started", "unknown"]:
            risks.append("Financing not yet secured")

        # Multiple objections
        objections = deal_data.get("objections_count", 0)
        if objections >= 3:
            risks.append(f"{objections} unresolved objections")

        # Price misalignment
        price_alignment = deal_data.get("price_alignment", 1.0)
        if price_alignment < 0.7:
            risks.append("Significant price misalignment")

        # Poor engagement
        engagement = deal_data.get("engagement_trend", 0)
        if engagement < -0.3:
            risks.append("Declining engagement trend")

        # Deal age
        age = deal_data.get("deal_age_days", 0)
        if age > 60:
            risks.append(f"Deal has been open for {age} days")

        # Competitor mentions
        if deal_data.get("competitor_mentions", 0) > 2:
            risks.append("Competing offers mentioned")

        return risks[:5]  # Top 5 risks

    def _identify_positive_factors(
        self, deal_data: Dict, probability: float
    ) -> List[str]:
        """Identify positive factors supporting close"""
        positives = []

        # High lead score
        if deal_data.get("lead_score", 50) >= 80:
            positives.append("Excellent lead quality")

        # Fast progression
        stage_velocity = self._calculate_stage_velocity(deal_data)
        if stage_velocity >= 0.8:
            positives.append("Moving quickly through pipeline")

        # Financing approved
        if deal_data.get("financing_status") in ["pre_approved", "approved"]:
            positives.append("Financing secured")

        # Good price alignment
        if deal_data.get("price_alignment", 0) >= 0.9:
            positives.append("Strong price alignment")

        # High engagement
        if deal_data.get("engagement_trend", 0) > 0.3:
            positives.append("Increasing engagement")

        # Fast agent response
        if deal_data.get("agent_response_time", 24) < 4:
            positives.append("Excellent agent responsiveness")

        # Few objections
        if deal_data.get("objections_count", 99) <= 1:
            positives.append("Minimal objections")

        return positives[:5]

    def _generate_recommendations(
        self, deal_data: Dict, probability: float, risk_factors: List[str]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        if probability >= 0.7:
            recommendations.append(
                "🎯 High close probability - prepare closing documents"
            )
            recommendations.append("Schedule final walkthrough")
        elif probability >= 0.5:
            recommendations.append("📈 Good potential - maintain momentum")
            recommendations.append("Address any outstanding questions promptly")
        else:
            recommendations.append("⚠️  Low close probability - identify blockers")
            recommendations.append("Consider re-qualification conversation")

        # Specific recommendations based on risk factors
        for risk in risk_factors:
            if "financing" in risk.lower():
                recommendations.append("🏦 Expedite financing approval process")
            elif "objection" in risk.lower():
                recommendations.append("📋 Schedule objection-handling meeting")
            elif "engagement" in risk.lower():
                recommendations.append("📞 Increase touchpoint frequency")
            elif "price" in risk.lower():
                recommendations.append("💰 Discuss pricing and value proposition")
            elif "slowly" in risk.lower():
                recommendations.append("⏱️  Add urgency - limited-time incentives")

        # Stage-specific recommendations
        stage = deal_data.get("current_stage", "lead")
        if stage in ["offer", "negotiation"]:
            recommendations.append("🤝 Be prepared to negotiate terms")
        elif stage == "contract":
            recommendations.append("📝 Ensure all contingencies are addressed")

        return recommendations[:6]


# Example usage
if __name__ == "__main__":
    predictor = DealPredictor()

    # Example deal
    deal_data = {
        "lead_score": 85,
        "current_stage": "offer",
        "days_in_current_stage": 5,
        "engagement_trend": 0.6,
        "financing_status": "pre_approved",
        "objections_count": 1,
        "price_alignment": 0.92,
        "agent_response_time": 2.5,
        "deal_age_days": 28,
        "competitor_mentions": 0,
    }

    prediction = predictor.predict_deal("deal_789", deal_data)

    print(f"\n📈 Deal Prediction for deal_789")
    print(f"   Close Probability: {prediction.close_probability*100:.1f}%")
    print(f"   Predicted Close: {prediction.predicted_close_date.strftime('%Y-%m-%d')}")
    print(
        f"   Date Range: {prediction.date_range_start.strftime('%Y-%m-%d')} to {prediction.date_range_end.strftime('%Y-%m-%d')}"
    )
    print(f"   Confidence: {prediction.confidence.upper()}")

    print(f"\n   ✅ Positive Factors:")
    for factor in prediction.positive_factors:
        print(f"   • {factor}")

    if prediction.risk_factors:
        print(f"\n   ⚠️  Risk Factors:")
        for risk in prediction.risk_factors:
            print(f"   • {risk}")

    print(f"\n   💡 Recommendations:")
    for rec in prediction.recommendations[:3]:
        print(f"   • {rec}")
