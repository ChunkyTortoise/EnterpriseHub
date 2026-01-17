#!/usr/bin/env python3
"""
Update Preference Weights Script

Zero-context execution script for updating preference weights based on
showing feedback. Implements feedback learning algorithm.

Usage:
    python update-preference-weights.py --lead-id <id> --feedback <feedback.json>
    python update-preference-weights.py --lead-id <id> --property-id <id> --liked
"""

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


@dataclass
class FeedbackInput:
    """Feedback data for a property showing."""
    property_id: str
    property_features: List[str]
    property_details: Dict  # bedrooms, bathrooms, sqft, price, etc.
    viewed: bool = False
    liked: bool = False
    offer_made: bool = False
    offer_accepted: bool = False
    objections: List[str] = None
    interests: List[str] = None
    rating: Optional[int] = None  # 1-5
    comments: Optional[str] = None


@dataclass
class WeightUpdate:
    """Result of weight update operation."""
    lead_id: str
    previous_weights: Dict[str, float]
    updated_weights: Dict[str, float]
    changes: Dict[str, float]
    learning_rate_used: float
    signal_type: str
    feedback_summary: str
    updated_at: str


# Default weights for new leads
DEFAULT_WEIGHTS = {
    "budget_fit": 0.25,
    "location_match": 0.25,
    "features_match": 0.30,
    "lifestyle_match": 0.20,

    # Sub-weights
    "bedrooms": 0.15,
    "bathrooms": 0.10,
    "sqft": 0.15,
    "pool": 0.10,
    "garage": 0.08,
    "yard": 0.08,
    "updated_kitchen": 0.10,
    "school_rating": 0.12,
    "commute_time": 0.12,
}

# Learning rates by signal type
LEARNING_RATES = {
    "implicit_view": 0.02,
    "implicit_no_view": 0.01,
    "explicit_liked": 0.10,
    "explicit_disliked": 0.05,
    "offer_made": 0.20,
    "offer_accepted": 0.25,
    "offer_rejected": 0.15,
}

# Feature keywords for categorization
FEATURE_CATEGORIES = {
    "size": ["sqft", "square feet", "space", "room", "small", "big", "large"],
    "bedrooms": ["bedroom", "bed", "br"],
    "bathrooms": ["bathroom", "bath", "ba"],
    "kitchen": ["kitchen", "appliances", "countertop", "cabinets"],
    "outdoor": ["yard", "pool", "patio", "deck", "garden", "outdoor"],
    "location": ["location", "neighborhood", "area", "commute", "schools"],
    "condition": ["condition", "old", "dated", "new", "renovated", "updated"],
    "price": ["price", "expensive", "cheap", "value", "cost", "afford"],
}


def load_current_weights(lead_id: str, weights_file: Optional[str] = None) -> Dict[str, float]:
    """Load current preference weights for lead."""
    if weights_file:
        try:
            with open(weights_file, 'r') as f:
                data = json.load(f)
                if lead_id in data:
                    return data[lead_id]
        except FileNotFoundError:
            pass

    # Return copy of defaults for new leads
    return DEFAULT_WEIGHTS.copy()


def save_weights(lead_id: str, weights: Dict[str, float], weights_file: Optional[str] = None):
    """Save updated weights."""
    if not weights_file:
        return

    try:
        with open(weights_file, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    data[lead_id] = weights

    with open(weights_file, 'w') as f:
        json.dump(data, f, indent=2)


def determine_signal_type(feedback: FeedbackInput) -> Tuple[str, float]:
    """Determine signal type and learning rate from feedback."""
    if feedback.offer_accepted:
        return "offer_accepted", LEARNING_RATES["offer_accepted"]

    if feedback.offer_made:
        return "offer_made", LEARNING_RATES["offer_made"]

    if feedback.liked:
        return "explicit_liked", LEARNING_RATES["explicit_liked"]

    if feedback.viewed and not feedback.liked:
        return "explicit_disliked", LEARNING_RATES["explicit_disliked"]

    if feedback.viewed:
        return "implicit_view", LEARNING_RATES["implicit_view"]

    return "implicit_no_view", LEARNING_RATES["implicit_no_view"]


def categorize_objection(objection: str) -> Optional[str]:
    """Categorize an objection into a feature category."""
    objection_lower = objection.lower()

    for category, keywords in FEATURE_CATEGORIES.items():
        if any(kw in objection_lower for kw in keywords):
            return category

    return None


def categorize_interest(interest: str) -> Optional[str]:
    """Categorize an interest into a feature category."""
    interest_lower = interest.lower()

    for category, keywords in FEATURE_CATEGORIES.items():
        if any(kw in interest_lower for kw in keywords):
            return category

    return None


def apply_feature_updates(
    weights: Dict[str, float],
    feedback: FeedbackInput,
    learning_rate: float,
    is_positive: bool
) -> Dict[str, float]:
    """Apply updates based on property features."""
    updated = weights.copy()
    direction = 1.0 if is_positive else -1.0

    # Update based on property features
    for feature in feedback.property_features:
        feature_lower = feature.lower()

        # Map feature to weight key
        weight_key = None
        for key in updated.keys():
            if key.lower() in feature_lower or feature_lower in key.lower():
                weight_key = key
                break

        if weight_key:
            current = updated[weight_key]
            adjustment = learning_rate * direction

            if is_positive:
                # Increase weight, bounded by 0.5
                updated[weight_key] = min(0.5, current * (1 + adjustment))
            else:
                # Decrease weight, bounded by 0.05
                updated[weight_key] = max(0.05, current * (1 - adjustment))

    return updated


def apply_objection_updates(
    weights: Dict[str, float],
    objections: List[str],
    learning_rate: float
) -> Dict[str, float]:
    """Apply weight updates based on objections."""
    updated = weights.copy()

    for objection in objections:
        category = categorize_objection(objection)

        if category:
            # Find related weight keys
            for key in updated.keys():
                if category in key.lower() or key.lower() in category:
                    # Increase weight for this factor (more important to match)
                    current = updated[key]
                    updated[key] = min(0.5, current * (1 + learning_rate * 2))

    return updated


def apply_interest_updates(
    weights: Dict[str, float],
    interests: List[str],
    learning_rate: float
) -> Dict[str, float]:
    """Apply weight updates based on stated interests."""
    updated = weights.copy()

    for interest in interests:
        category = categorize_interest(interest)

        if category:
            # Find related weight keys
            for key in updated.keys():
                if category in key.lower() or key.lower() in category:
                    # Increase weight for this factor
                    current = updated[key]
                    updated[key] = min(0.5, current * (1 + learning_rate * 1.5))

    return updated


def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """Normalize weights to maintain reasonable proportions."""
    # Separate main category weights and sub-weights
    main_categories = ["budget_fit", "location_match", "features_match", "lifestyle_match"]
    main_weights = {k: v for k, v in weights.items() if k in main_categories}
    sub_weights = {k: v for k, v in weights.items() if k not in main_categories}

    # Normalize main categories to sum to 1.0
    main_total = sum(main_weights.values())
    if main_total > 0:
        main_weights = {k: v / main_total for k, v in main_weights.items()}

    # Apply regularization to sub-weights (pull toward mean)
    if sub_weights:
        mean_sub = sum(sub_weights.values()) / len(sub_weights)
        regularization = 0.05  # Pull 5% toward mean

        for key in sub_weights:
            sub_weights[key] += regularization * (mean_sub - sub_weights[key])

    # Combine and return
    return {**main_weights, **sub_weights}


def calculate_changes(
    previous: Dict[str, float],
    updated: Dict[str, float]
) -> Dict[str, float]:
    """Calculate changes between weight sets."""
    changes = {}

    for key in updated:
        if key in previous:
            change = updated[key] - previous[key]
            if abs(change) > 0.001:  # Only report meaningful changes
                changes[key] = round(change, 4)

    return changes


def generate_feedback_summary(feedback: FeedbackInput, signal_type: str) -> str:
    """Generate human-readable feedback summary."""
    parts = []

    if feedback.viewed:
        parts.append("Viewed in person")

    if signal_type == "offer_accepted":
        parts.append("OFFER ACCEPTED - strong positive signal")
    elif signal_type == "offer_made":
        parts.append("Offer made - strong interest")
    elif feedback.liked:
        parts.append("Liked the property")
    elif feedback.viewed:
        parts.append("Viewed but not interested")

    if feedback.rating:
        parts.append(f"Rating: {feedback.rating}/5")

    if feedback.objections:
        parts.append(f"Objections: {', '.join(feedback.objections[:3])}")

    if feedback.interests:
        parts.append(f"Interests: {', '.join(feedback.interests[:3])}")

    return " | ".join(parts) if parts else "Minimal feedback"


def update_weights(
    lead_id: str,
    feedback: FeedbackInput,
    current_weights: Dict[str, float]
) -> WeightUpdate:
    """Main weight update function."""
    previous_weights = current_weights.copy()

    # Determine signal type and learning rate
    signal_type, learning_rate = determine_signal_type(feedback)

    # Determine if positive or negative signal
    is_positive = signal_type in ["offer_accepted", "offer_made", "explicit_liked", "implicit_view"]

    # Apply feature-based updates
    updated_weights = apply_feature_updates(
        current_weights, feedback, learning_rate, is_positive
    )

    # Apply objection-based updates (if any)
    if feedback.objections:
        updated_weights = apply_objection_updates(
            updated_weights, feedback.objections, learning_rate
        )

    # Apply interest-based updates (if any)
    if feedback.interests:
        updated_weights = apply_interest_updates(
            updated_weights, feedback.interests, learning_rate
        )

    # Normalize weights
    updated_weights = normalize_weights(updated_weights)

    # Round for cleaner output
    updated_weights = {k: round(v, 4) for k, v in updated_weights.items()}

    # Calculate changes
    changes = calculate_changes(previous_weights, updated_weights)

    # Generate summary
    summary = generate_feedback_summary(feedback, signal_type)

    return WeightUpdate(
        lead_id=lead_id,
        previous_weights=previous_weights,
        updated_weights=updated_weights,
        changes=changes,
        learning_rate_used=learning_rate,
        signal_type=signal_type,
        feedback_summary=summary,
        updated_at=datetime.now().isoformat()
    )


def load_feedback(feedback_file: str) -> FeedbackInput:
    """Load feedback from JSON file."""
    with open(feedback_file, 'r') as f:
        data = json.load(f)

    return FeedbackInput(
        property_id=data.get("property_id", "unknown"),
        property_features=data.get("property_features", []),
        property_details=data.get("property_details", {}),
        viewed=data.get("viewed", False),
        liked=data.get("liked", False),
        offer_made=data.get("offer_made", False),
        offer_accepted=data.get("offer_accepted", False),
        objections=data.get("objections", []),
        interests=data.get("interests", []),
        rating=data.get("rating"),
        comments=data.get("comments")
    )


def create_mock_feedback(
    property_id: str,
    liked: bool,
    offer_made: bool = False
) -> FeedbackInput:
    """Create mock feedback for demonstration."""
    mock_features = ["pool", "updated kitchen", "3 car garage", "large yard"]
    mock_details = {
        "bedrooms": 4,
        "bathrooms": 3,
        "sqft": 2800,
        "price": 650000
    }

    objections = []
    interests = []

    if liked:
        interests = ["loved the open floor plan", "great backyard for kids"]
    else:
        objections = ["kitchen too small", "location not ideal", "needs too much work"]

    return FeedbackInput(
        property_id=property_id,
        property_features=mock_features,
        property_details=mock_details,
        viewed=True,
        liked=liked,
        offer_made=offer_made,
        offer_accepted=False,
        objections=objections,
        interests=interests,
        rating=4 if liked else 2,
        comments="Nice property overall" if liked else "Not quite right for us"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Update preference weights based on feedback"
    )
    parser.add_argument(
        "--lead-id",
        required=True,
        help="Lead ID to update weights for"
    )
    parser.add_argument(
        "--feedback",
        help="JSON file with feedback data"
    )
    parser.add_argument(
        "--property-id",
        help="Property ID for manual feedback"
    )
    parser.add_argument(
        "--liked",
        action="store_true",
        help="Mark as liked (for manual feedback)"
    )
    parser.add_argument(
        "--offer-made",
        action="store_true",
        help="Mark as offer made (for manual feedback)"
    )
    parser.add_argument(
        "--weights-file",
        help="JSON file to load/save weights"
    )
    parser.add_argument(
        "--output",
        choices=["json", "text"],
        default="text",
        help="Output format"
    )

    args = parser.parse_args()

    # Load feedback
    if args.feedback:
        try:
            feedback = load_feedback(args.feedback)
        except FileNotFoundError:
            print(f"Error: Feedback file not found: {args.feedback}")
            sys.exit(1)
    elif args.property_id:
        feedback = create_mock_feedback(
            args.property_id,
            args.liked,
            args.offer_made
        )
    else:
        # Use default mock feedback
        feedback = create_mock_feedback("mock_property", True, False)

    # Load current weights
    current_weights = load_current_weights(args.lead_id, args.weights_file)

    # Update weights
    result = update_weights(args.lead_id, feedback, current_weights)

    # Save updated weights
    if args.weights_file:
        save_weights(args.lead_id, result.updated_weights, args.weights_file)

    # Output
    if args.output == "json":
        output = {
            "lead_id": result.lead_id,
            "previous_weights": result.previous_weights,
            "updated_weights": result.updated_weights,
            "changes": result.changes,
            "learning_rate_used": result.learning_rate_used,
            "signal_type": result.signal_type,
            "feedback_summary": result.feedback_summary,
            "updated_at": result.updated_at
        }
        print(json.dumps(output, indent=2))
    else:
        print("\n" + "=" * 60)
        print("PREFERENCE WEIGHT UPDATE")
        print("=" * 60)
        print(f"\nLead ID: {result.lead_id}")
        print(f"Signal Type: {result.signal_type}")
        print(f"Learning Rate: {result.learning_rate_used}")
        print(f"Updated At: {result.updated_at}")

        print("\n" + "-" * 60)
        print("FEEDBACK SUMMARY")
        print("-" * 60)
        print(f"  {result.feedback_summary}")

        print("\n" + "-" * 60)
        print("WEIGHT CHANGES")
        print("-" * 60)
        if result.changes:
            for key, change in sorted(result.changes.items(), key=lambda x: abs(x[1]), reverse=True):
                direction = "+" if change > 0 else ""
                print(f"  {key}: {direction}{change:.4f}")
        else:
            print("  No significant changes")

        print("\n" + "-" * 60)
        print("UPDATED WEIGHTS (Main Categories)")
        print("-" * 60)
        main_cats = ["budget_fit", "location_match", "features_match", "lifestyle_match"]
        for key in main_cats:
            if key in result.updated_weights:
                prev = result.previous_weights.get(key, 0)
                curr = result.updated_weights[key]
                change = curr - prev
                indicator = " (+)" if change > 0.001 else " (-)" if change < -0.001 else ""
                print(f"  {key}: {curr:.2%}{indicator}")

        print("\n" + "-" * 60)
        print("UPDATED WEIGHTS (Features)")
        print("-" * 60)
        for key, value in sorted(result.updated_weights.items()):
            if key not in main_cats:
                prev = result.previous_weights.get(key, 0)
                change = value - prev
                indicator = " (+)" if change > 0.001 else " (-)" if change < -0.001 else ""
                print(f"  {key}: {value:.2%}{indicator}")

        print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
