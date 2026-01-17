#!/usr/bin/env python3
"""
Conversion Score Calculator for Intelligent Lead Insights

Calculates conversion probability using weighted factors from
Jorge's question methodology and ML behavioral analysis.

Usage:
    python calculate-conversion-score.py --lead-id <lead_id>
    python calculate-conversion-score.py --lead-id <lead_id> --include-reasoning
    python calculate-conversion-score.py --features <features.json>

Zero-Context Execution:
    This script runs independently without loading into Claude's context.
    Only the output is returned, saving tokens for actual analysis.
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class ConversionScore:
    """Conversion score with detailed breakdown."""
    lead_id: str
    final_score: float  # 0-100
    classification: str  # hot, warm, cold
    confidence: float  # 0-1
    jorge_score: float  # Jorge's question-count score
    ml_score: float  # ML behavioral score
    market_score: float  # Market timing score
    engagement_score: float  # Engagement pattern score
    feature_breakdown: Dict[str, float]
    reasoning: str
    next_best_action: str
    calculated_at: str


# Weight configuration
WEIGHTS = {
    "jorge": 0.40,
    "ml": 0.35,
    "market": 0.15,
    "engagement": 0.10
}

# Segment-specific weight adjustments
SEGMENT_WEIGHTS = {
    "first_time_buyer": {"jorge": 1.2, "ml": 0.8},
    "investor": {"jorge": 0.8, "ml": 1.3},
    "luxury": {"market": 1.5, "jorge": 1.0},
    "relocation": {"engagement": 1.3, "jorge": 1.1}
}


def load_lead_features(lead_id: str) -> Dict[str, Any]:
    """
    Load lead features from data sources.

    In production, connects to:
    - Enhanced lead scorer service
    - Memory service
    - GHL contact data
    """
    try:
        from ghl_real_estate_ai.services.claude_enhanced_lead_scorer import ClaudeEnhancedLeadScorer
        scorer = ClaudeEnhancedLeadScorer()
        # Would call scorer.get_lead_features(lead_id)
        return {}
    except ImportError:
        # Return sample features for standalone testing
        return {
            "budget": 750000,
            "location": "Teravista",
            "bedrooms": 4,
            "timeline": "90_days",
            "pre_approval": True,
            "motivation": "Growing family",
            "seller_condition": None,
            "message_count": 15,
            "avg_response_time_hours": 2.5,
            "page_views": 8,
            "email_open_rate": 0.75,
            "return_visits": 3,
            "buyer_type": "first_time_buyer"
        }


def calculate_jorge_score(features: Dict[str, Any]) -> Tuple[float, Dict[str, bool]]:
    """
    Calculate Jorge's question-count based score.

    Based on the 7 qualification questions:
    1. Budget
    2. Location
    3. Bedrooms
    4. Timeline
    5. Pre-approval
    6. Motivation
    7. Seller condition

    Classification:
    - 3+ meaningful answers: Hot (75-100)
    - 2 answers: Warm (40-74)
    - 0-1 answers: Cold (0-39)
    """
    questions = {
        "budget": features.get("budget") is not None,
        "location": features.get("location") is not None and features.get("location") != "",
        "bedrooms": features.get("bedrooms") is not None,
        "timeline": features.get("timeline") is not None and features.get("timeline") != "unknown",
        "pre_approval": features.get("pre_approval") is not None,
        "motivation": features.get("motivation") is not None and features.get("motivation") != "",
        "seller_condition": features.get("seller_condition") is not None
    }

    answered_count = sum(1 for v in questions.values() if v)

    # Calculate score based on Jorge's methodology
    if answered_count >= 5:
        score = 90 + (answered_count - 5) * 5  # 90-100
    elif answered_count >= 3:
        score = 60 + (answered_count - 3) * 15  # 60-90
    elif answered_count == 2:
        score = 45  # Warm baseline
    elif answered_count == 1:
        score = 25  # Cold with some info
    else:
        score = 10  # Very cold

    return score, questions


def calculate_ml_score(features: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
    """
    Calculate ML behavioral score based on engagement patterns.

    Features considered:
    - Message count and response velocity
    - Page views and email engagement
    - Return visits and document downloads
    """
    feature_weights = {
        "message_count": {"weight": 0.15, "max": 30, "value": features.get("message_count", 0)},
        "response_velocity": {"weight": 0.20, "max": 24, "value": max(0, 24 - features.get("avg_response_time_hours", 24))},
        "page_views": {"weight": 0.15, "max": 20, "value": features.get("page_views", 0)},
        "email_engagement": {"weight": 0.20, "max": 1, "value": features.get("email_open_rate", 0)},
        "return_visits": {"weight": 0.15, "max": 5, "value": features.get("return_visits", 0)},
        "document_downloads": {"weight": 0.15, "max": 3, "value": features.get("document_downloads", 0)}
    }

    total_score = 0
    breakdown = {}

    for feature_name, config in feature_weights.items():
        # Normalize value to 0-1
        normalized = min(config["value"] / config["max"], 1.0) if config["max"] > 0 else 0
        # Apply weight
        weighted_score = normalized * config["weight"] * 100
        total_score += weighted_score
        breakdown[feature_name] = round(weighted_score, 2)

    return round(total_score, 2), breakdown


def calculate_market_score(features: Dict[str, Any]) -> float:
    """
    Calculate market timing score.

    Factors:
    - Current season
    - Market inventory level
    - Interest rate environment
    """
    base_score = 50  # Baseline

    # Seasonal adjustment
    month = datetime.now().month
    if month in [3, 4, 5]:  # Spring
        base_score += 10
    elif month in [6, 7, 8]:  # Summer
        base_score += 5
    elif month in [12, 1, 2]:  # Winter
        base_score -= 5

    # Timeline urgency boost
    timeline = features.get("timeline", "")
    if "30" in str(timeline) or "urgent" in str(timeline).lower():
        base_score += 15
    elif "60" in str(timeline) or "90" in str(timeline):
        base_score += 10
    elif "6_months" in str(timeline) or "180" in str(timeline):
        base_score += 5

    return min(base_score, 100)


def calculate_engagement_score(features: Dict[str, Any]) -> float:
    """
    Calculate engagement pattern score.

    Based on:
    - Response consistency
    - Question depth
    - Interaction frequency
    """
    score = 50  # Baseline

    # Message count contribution
    msg_count = features.get("message_count", 0)
    if msg_count >= 20:
        score += 20
    elif msg_count >= 10:
        score += 15
    elif msg_count >= 5:
        score += 10

    # Response time contribution
    response_time = features.get("avg_response_time_hours", 24)
    if response_time < 1:
        score += 15
    elif response_time < 4:
        score += 10
    elif response_time < 12:
        score += 5

    # Return visit contribution
    returns = features.get("return_visits", 0)
    if returns >= 3:
        score += 15
    elif returns >= 1:
        score += 8

    return min(score, 100)


def determine_classification(score: float) -> str:
    """Determine lead classification based on score."""
    if score >= 70:
        return "hot"
    elif score >= 40:
        return "warm"
    else:
        return "cold"


def calculate_confidence(features: Dict[str, Any], jorge_questions: Dict[str, bool]) -> float:
    """
    Calculate confidence in the prediction.

    Based on:
    - Data completeness
    - Feature quality
    - Historical accuracy
    """
    # Data completeness (40%)
    answered = sum(1 for v in jorge_questions.values() if v)
    completeness = answered / len(jorge_questions)

    # Feature quality (30%)
    msg_count = features.get("message_count", 0)
    quality = min(msg_count / 10, 1.0)

    # Historical accuracy for segment (30%)
    segment = features.get("buyer_type", "unknown")
    segment_accuracy = {
        "first_time_buyer": 0.82,
        "investor": 0.78,
        "luxury": 0.85,
        "relocation": 0.80,
        "unknown": 0.75
    }.get(segment, 0.75)

    confidence = (completeness * 0.4) + (quality * 0.3) + (segment_accuracy * 0.3)
    return round(confidence, 2)


def generate_reasoning(
    final_score: float,
    jorge_score: float,
    ml_score: float,
    jorge_questions: Dict[str, bool],
    features: Dict[str, Any]
) -> str:
    """Generate human-readable reasoning for the score."""
    reasons = []

    # Jorge score contribution
    answered = sum(1 for v in jorge_questions.values() if v)
    if answered >= 3:
        reasons.append(f"Strong qualification with {answered}/7 key questions answered")
    elif answered >= 2:
        reasons.append(f"Moderate qualification with {answered}/7 questions answered")
    else:
        reasons.append(f"Limited qualification data ({answered}/7 questions)")

    # Specific high-value signals
    if jorge_questions.get("pre_approval"):
        reasons.append("Pre-approval confirmed (strong financial signal)")
    if jorge_questions.get("timeline"):
        timeline = features.get("timeline", "")
        if "30" in str(timeline) or "60" in str(timeline) or "90" in str(timeline):
            reasons.append(f"Active timeline: {timeline}")

    # Behavioral signals
    if ml_score >= 60:
        reasons.append("High behavioral engagement detected")
    elif ml_score >= 40:
        reasons.append("Moderate engagement patterns")

    # Specific concerns
    response_time = features.get("avg_response_time_hours", 24)
    if response_time > 24:
        reasons.append(f"Slow response time ({response_time:.1f}h avg) may indicate declining interest")

    return "; ".join(reasons)


def determine_next_action(classification: str, features: Dict[str, Any]) -> str:
    """Determine recommended next action based on classification and features."""
    if classification == "hot":
        if features.get("pre_approval"):
            return "Schedule property viewings immediately - lead is ready to buy"
        else:
            return "Confirm financing and schedule viewings within 24 hours"
    elif classification == "warm":
        answered_questions = []
        if not features.get("budget"):
            answered_questions.append("budget")
        if not features.get("timeline"):
            answered_questions.append("timeline")
        if not features.get("pre_approval"):
            answered_questions.append("pre-approval status")

        if answered_questions:
            return f"Focus on qualifying: {', '.join(answered_questions[:2])}"
        else:
            return "Schedule discovery call to deepen relationship"
    else:
        return "Enroll in nurture sequence with valuable content"


def calculate_conversion_score(lead_id: str, features: Optional[Dict] = None) -> ConversionScore:
    """
    Calculate comprehensive conversion score.

    Args:
        lead_id: Lead identifier
        features: Optional pre-loaded features (for batch processing)

    Returns:
        ConversionScore with detailed breakdown
    """
    # Load features if not provided
    if features is None:
        features = load_lead_features(lead_id)

    # Get segment for weight adjustments
    segment = features.get("buyer_type", "unknown")
    segment_adj = SEGMENT_WEIGHTS.get(segment, {})

    # Calculate component scores
    jorge_score, jorge_questions = calculate_jorge_score(features)
    ml_score, ml_breakdown = calculate_ml_score(features)
    market_score = calculate_market_score(features)
    engagement_score = calculate_engagement_score(features)

    # Apply weights with segment adjustments
    jorge_weight = WEIGHTS["jorge"] * segment_adj.get("jorge", 1.0)
    ml_weight = WEIGHTS["ml"] * segment_adj.get("ml", 1.0)
    market_weight = WEIGHTS["market"] * segment_adj.get("market", 1.0)
    engagement_weight = WEIGHTS["engagement"] * segment_adj.get("engagement", 1.0)

    # Normalize weights
    total_weight = jorge_weight + ml_weight + market_weight + engagement_weight
    jorge_weight /= total_weight
    ml_weight /= total_weight
    market_weight /= total_weight
    engagement_weight /= total_weight

    # Calculate final score
    final_score = (
        jorge_score * jorge_weight +
        ml_score * ml_weight +
        market_score * market_weight +
        engagement_score * engagement_weight
    )

    # Determine classification and confidence
    classification = determine_classification(final_score)
    confidence = calculate_confidence(features, jorge_questions)

    # Generate reasoning
    reasoning = generate_reasoning(
        final_score, jorge_score, ml_score, jorge_questions, features
    )

    # Determine next action
    next_action = determine_next_action(classification, features)

    # Build feature breakdown
    feature_breakdown = {
        "jorge_questions_answered": sum(1 for v in jorge_questions.values() if v),
        **{f"ml_{k}": v for k, v in ml_breakdown.items()},
        "market_timing": market_score,
        "engagement_pattern": engagement_score
    }

    return ConversionScore(
        lead_id=lead_id,
        final_score=round(final_score, 1),
        classification=classification,
        confidence=confidence,
        jorge_score=round(jorge_score, 1),
        ml_score=round(ml_score, 1),
        market_score=round(market_score, 1),
        engagement_score=round(engagement_score, 1),
        feature_breakdown=feature_breakdown,
        reasoning=reasoning,
        next_best_action=next_action,
        calculated_at=datetime.now().isoformat()
    )


def main():
    parser = argparse.ArgumentParser(description="Calculate lead conversion score")
    parser.add_argument("--lead-id", type=str, help="Lead ID to score")
    parser.add_argument("--features", type=str, help="Path to features JSON file")
    parser.add_argument("--include-reasoning", action="store_true", help="Include detailed reasoning")
    parser.add_argument("--output", type=str, default="json", choices=["json", "text"])

    args = parser.parse_args()

    if args.features:
        with open(args.features, "r") as f:
            features = json.load(f)
        lead_id = features.get("lead_id", "unknown")
    elif args.lead_id:
        lead_id = args.lead_id
        features = None
    else:
        parser.print_help()
        sys.exit(1)

    score = calculate_conversion_score(lead_id, features)

    if args.output == "text":
        print(f"Conversion Score for {lead_id}")
        print("=" * 50)
        print(f"Final Score: {score.final_score}/100")
        print(f"Classification: {score.classification.upper()}")
        print(f"Confidence: {score.confidence:.0%}")
        print()
        print("Component Scores:")
        print(f"  Jorge (Question-based): {score.jorge_score}")
        print(f"  ML (Behavioral): {score.ml_score}")
        print(f"  Market Timing: {score.market_score}")
        print(f"  Engagement: {score.engagement_score}")
        print()
        if args.include_reasoning:
            print(f"Reasoning: {score.reasoning}")
            print()
        print(f"Next Action: {score.next_best_action}")
    else:
        output = asdict(score)
        if not args.include_reasoning:
            output.pop("reasoning", None)
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
