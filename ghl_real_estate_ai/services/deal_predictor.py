"""
Deal Closing Probability Predictor - Wow Factor Feature #4
Uses ML-inspired algorithms to predict likelihood of closing
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple


class DealClosingPredictor:
    """
    🎯 WOW FEATURE: AI Deal Closing Predictor

    Predicts the probability a lead will close within 30/60/90 days
    using behavioral signals, engagement patterns, and market intelligence.

    Features:
    - 30/60/90 day closing probability
    - Revenue forecasting
    - Risk factors identification
    - Win/loss prediction with confidence
    - Recommended next actions to increase probability
    """

    def __init__(self):
        self.model_weights = self._initialize_model_weights()

    def predict_closing_probability(self, lead_data: Dict) -> Dict:
        """
        Predict probability of closing and expected revenue

        Args:
            lead_data: Comprehensive lead information

        Returns:
            Prediction with probabilities, timeline, and recommendations
        """
        # Extract features
        features = self._extract_features(lead_data)

        # Calculate base probability using weighted features
        base_prob = self._calculate_base_probability(features)

        # Apply time decay for different windows
        prob_30_days = base_prob * self._time_decay_factor(features, 30)
        prob_60_days = base_prob * self._time_decay_factor(features, 60)
        prob_90_days = base_prob * self._time_decay_factor(features, 90)

        # Calculate expected revenue
        property_value = features.get("estimated_property_value", 300000)
        commission_rate = 0.03  # 3% average
        expected_revenue_30 = property_value * commission_rate * prob_30_days
        expected_revenue_60 = property_value * commission_rate * prob_60_days
        expected_revenue_90 = property_value * commission_rate * prob_90_days

        # Identify key factors
        positive_factors = self._identify_positive_factors(features)
        risk_factors = self._identify_risk_factors(features)

        # Generate recommendations
        recommendations = self._generate_recommendations(features, prob_30_days)

        return {
            "lead_id": lead_data.get("lead_id"),
            "prediction_date": datetime.now().isoformat(),
            "probabilities": {
                "30_days": round(prob_30_days, 3),
                "60_days": round(prob_60_days, 3),
                "90_days": round(prob_90_days, 3),
            },
            "confidence": self._calculate_confidence(features),
            "expected_revenue": {
                "30_days": f"${expected_revenue_30:,.0f}",
                "60_days": f"${expected_revenue_60:,.0f}",
                "90_days": f"${expected_revenue_90:,.0f}",
            },
            "verdict": self._get_verdict(prob_30_days, prob_60_days, prob_90_days),
            "positive_factors": positive_factors,
            "risk_factors": risk_factors,
            "recommendations": recommendations,
            "model_version": "1.0",
        }

    def _extract_features(self, lead_data: Dict) -> Dict:
        """Extract predictive features from lead data"""
        conversations = lead_data.get("conversations", [])
        metadata = lead_data.get("metadata", {})
        score = lead_data.get("score", 0)

        return {
            # Engagement features
            "lead_score": score,
            "total_conversations": len(conversations),
            "avg_response_time": self._calc_avg_response_time(conversations),
            "engagement_trend": self._calc_engagement_trend(conversations),
            # Qualification features
            "questions_answered": metadata.get("answered_questions", 0),
            "has_budget": metadata.get("budget") is not None,
            "has_location": metadata.get("location") is not None,
            "has_timeline": metadata.get("timeline") is not None,
            "preapproval_status": metadata.get("preapproval", False),
            # Behavioral features
            "urgency_signals": self._count_urgency_signals(conversations),
            "objection_count": self._count_objections(conversations),
            "positive_sentiment": self._measure_sentiment(conversations),
            "appointment_scheduled": metadata.get("appointment_scheduled", False),
            "appointment_kept": metadata.get("appointment_kept", False),
            # Property features
            "estimated_property_value": metadata.get("property_value", 300000),
            "property_condition": metadata.get("condition", "good"),
            "motivation_level": metadata.get("motivation", "medium"),
            # Competition features
            "competing_offers": metadata.get("competing_offers", 0),
            "time_on_market": metadata.get("days_since_first_contact", 0),
            # Contact quality
            "contact_method_variety": self._count_contact_methods(conversations),
            "response_consistency": self._calc_response_consistency(conversations),
        }

    def _calculate_base_probability(self, features: Dict) -> float:
        """Calculate base closing probability using weighted features"""
        weights = self.model_weights
        prob = 0.0

        # Lead score (20% weight)
        prob += (features["lead_score"] / 10) * weights["lead_score"]

        # Qualification (25% weight)
        qualification_score = (
            (1 if features["has_budget"] else 0)
            + (1 if features["has_location"] else 0)
            + (1 if features["has_timeline"] else 0)
            + (features["questions_answered"] / 7)
        ) / 4
        prob += qualification_score * weights["qualification"]

        # Engagement (20% weight)
        engagement_score = min(features["total_conversations"] / 10, 1.0)
        prob += engagement_score * weights["engagement"]

        # Urgency (15% weight)
        urgency_score = min(features["urgency_signals"] / 3, 1.0)
        prob += urgency_score * weights["urgency"]

        # Appointments (20% weight)
        appointment_score = 0
        if features["appointment_scheduled"]:
            appointment_score = 0.5
        if features["appointment_kept"]:
            appointment_score = 1.0
        prob += appointment_score * weights["appointments"]

        return min(prob, 1.0)

    def _time_decay_factor(self, features: Dict, days: int) -> float:
        """Apply time decay - urgency affects probability by timeframe"""
        urgency = features["urgency_signals"]

        if urgency >= 2:  # High urgency
            if days == 30:
                return 1.0
            elif days == 60:
                return 0.7
            else:
                return 0.4
        elif urgency == 1:  # Medium urgency
            if days == 30:
                return 0.6
            elif days == 60:
                return 0.9
            else:
                return 0.8
        else:  # Low urgency
            if days == 30:
                return 0.3
            elif days == 60:
                return 0.7
            else:
                return 1.0

    def _calculate_confidence(self, features: Dict) -> float:
        """Calculate prediction confidence based on data quality"""
        confidence = 0.5  # Base confidence

        # More data = higher confidence
        if features["total_conversations"] > 5:
            confidence += 0.2
        if features["questions_answered"] >= 5:
            confidence += 0.15
        if features["appointment_kept"]:
            confidence += 0.15

        return min(confidence, 1.0)

    def _get_verdict(self, prob_30: float, prob_60: float, prob_90: float) -> str:
        """Get human-readable verdict"""
        if prob_30 > 0.7:
            return "🔥 HOT - Likely to close within 30 days"
        elif prob_60 > 0.6:
            return "🔶 WARM - Good chance within 60 days"
        elif prob_90 > 0.5:
            return "🟡 MODERATE - May close within 90 days"
        else:
            return "❄️ COLD - Low probability, needs nurturing"

    def _identify_positive_factors(self, features: Dict) -> List[str]:
        """Identify factors increasing probability"""
        factors = []

        if features["lead_score"] > 7.5:
            factors.append("High lead score (8+)")
        if features["urgency_signals"] >= 2:
            factors.append("Strong urgency signals")
        if features["appointment_kept"]:
            factors.append("Kept appointment (highly predictive)")
        if features["questions_answered"] >= 5:
            factors.append("Answered 5+ qualifying questions")
        if features["avg_response_time"] < 600:  # < 10 minutes
            factors.append("Fast response times")
        if features["preapproval_status"]:
            factors.append("Pre-approved (buyers)")

        return factors[:5]  # Top 5

    def _identify_risk_factors(self, features: Dict) -> List[str]:
        """Identify factors decreasing probability"""
        risks = []

        if features["competing_offers"] > 0:
            risks.append(f"Considering {features['competing_offers']} other agent(s)")
        if features["objection_count"] > 2:
            risks.append("Multiple objections raised")
        if features["time_on_market"] > 21:
            risks.append("Been looking for 3+ weeks (cooling interest)")
        if not features["has_timeline"]:
            risks.append("No clear timeline provided")
        if features["avg_response_time"] > 14400:  # > 4 hours
            risks.append("Slow to respond")

        return risks[:5]  # Top 5

    def _generate_recommendations(self, features: Dict, prob_30: float) -> List[str]:
        """Generate actions to increase closing probability"""
        recommendations = []

        if prob_30 > 0.7:
            recommendations.append("🎯 Push for contract NOW - iron is hot")
            recommendations.append("Schedule in-person meeting within 48 hours")
        elif prob_30 > 0.4:
            recommendations.append("📞 Call to address any concerns directly")
            recommendations.append("Send personalized property matches")
        else:
            recommendations.append("🔄 Re-engage with Jorge's break-up text")
            recommendations.append("Provide value-add content (market reports, etc.)")

        if not features["appointment_scheduled"]:
            recommendations.append("⚠️ PRIORITY: Get them on phone or in-person")

        if features["objection_count"] > 0:
            recommendations.append("Address objections proactively in next contact")

        return recommendations[:5]

    # Helper methods
    def _calc_avg_response_time(self, conversations: List) -> float:
        """Calculate average response time in seconds"""
        # Simplified - would calculate actual time differences
        return 1800  # 30 minutes default

    def _calc_engagement_trend(self, conversations: List) -> str:
        """Determine if engagement is increasing, stable, or decreasing"""
        if len(conversations) < 4:
            return "insufficient_data"

        recent = len([c for c in conversations[-3:] if c.get("sender") == "lead"])
        older = len([c for c in conversations[-6:-3] if c.get("sender") == "lead"])

        if recent > older:
            return "increasing"
        elif recent < older:
            return "decreasing"
        else:
            return "stable"

    def _count_urgency_signals(self, conversations: List) -> int:
        """Count urgency signals in conversations"""
        urgency_words = ["asap", "urgent", "quickly", "soon", "deadline"]
        count = 0
        for conv in conversations:
            if any(word in conv.get("message", "").lower() for word in urgency_words):
                count += 1
        return count

    def _count_objections(self, conversations: List) -> int:
        """Count objection signals"""
        objection_words = ["but", "however", "expensive", "not sure", "worried"]
        count = 0
        for conv in conversations:
            if conv.get("sender") == "lead":
                if any(word in conv.get("message", "").lower() for word in objection_words):
                    count += 1
        return count

    def _measure_sentiment(self, conversations: List) -> float:
        """Measure positive sentiment (0-1)"""
        # Simplified sentiment analysis
        positive_words = ["great", "perfect", "sounds good", "interested", "excited"]
        positive_count = 0
        total_lead_messages = 0

        for conv in conversations:
            if conv.get("sender") == "lead":
                total_lead_messages += 1
                if any(word in conv.get("message", "").lower() for word in positive_words):
                    positive_count += 1

        return positive_count / total_lead_messages if total_lead_messages > 0 else 0.5

    def _count_contact_methods(self, conversations: List) -> int:
        """Count variety of contact methods used"""
        methods = set()
        for conv in conversations:
            method = conv.get("channel", "sms")
            methods.add(method)
        return len(methods)

    def _calc_response_consistency(self, conversations: List) -> float:
        """Calculate how consistently lead responds (0-1)"""
        # Simplified - percentage of agent messages that got responses
        return 0.75  # Default 75%

    def _initialize_model_weights(self) -> Dict:
        """Initialize feature weights for the model"""
        return {
            "lead_score": 0.20,
            "qualification": 0.25,
            "engagement": 0.20,
            "urgency": 0.15,
            "appointments": 0.20,
        }


# Example usage
if __name__ == "__main__":
    predictor = DealClosingPredictor()

    # Hot lead example
    hot_lead = {
        "lead_id": "L789",
        "score": 8.5,
        "conversations": [
            {"sender": "agent", "message": "Hey! Looking to buy or sell?"},
            {"sender": "lead", "message": "Selling ASAP. Need cash offer."},
            {"sender": "agent", "message": "Perfect! When can we view the property?"},
            {"sender": "lead", "message": "Tomorrow works. This is urgent."},
            {"sender": "agent", "message": "Great! 2pm or 4pm?"},
            {"sender": "lead", "message": "2pm sounds good"},
        ],
        "metadata": {
            "answered_questions": 6,
            "budget": 400000,
            "location": "Miami Beach",
            "timeline": "immediate",
            "appointment_scheduled": True,
            "appointment_kept": True,
            "motivation": "high",
        },
    }

    prediction = predictor.predict_closing_probability(hot_lead)

    print("🎯 Deal Closing Probability Predictor\n")
    print(f"Verdict: {prediction['verdict']}\n")
    print("Closing Probabilities:")
    print(f"  30 days: {prediction['probabilities']['30_days'] * 100:.1f}%")
    print(f"  60 days: {prediction['probabilities']['60_days'] * 100:.1f}%")
    print(f"  90 days: {prediction['probabilities']['90_days'] * 100:.1f}%\n")
    print(f"Expected Revenue (30 days): {prediction['expected_revenue']['30_days']}\n")
    print("Positive Factors:")
    for factor in prediction["positive_factors"]:
        print(f"  ✅ {factor}")
    print("\nRecommendations:")
    for rec in prediction["recommendations"]:
        print(f"  {rec}")
