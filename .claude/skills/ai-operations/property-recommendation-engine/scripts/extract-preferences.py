#!/usr/bin/env python3
"""
Extract Preferences Script

Zero-context execution script for extracting buyer preferences from
conversation history and behavioral data.

Usage:
    python extract-preferences.py --lead-id <id> --output json
    python extract-preferences.py --lead-id <id> --conversations <file.json>
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
from collections import defaultdict


@dataclass
class BudgetPreference:
    """Extracted budget preferences."""
    min_price: Optional[int] = None
    target_price: Optional[int] = None
    max_price: Optional[int] = None
    flexibility: str = "moderate"  # firm, moderate, flexible
    confidence: float = 0.5
    source: str = "inferred"


@dataclass
class LocationPreference:
    """Extracted location preference."""
    area: str
    priority: int  # 1-5, 1 being highest
    confidence: float
    source: str


@dataclass
class FeaturePreferences:
    """Extracted feature preferences."""
    bedrooms_min: Optional[int] = None
    bedrooms_ideal: Optional[int] = None
    bathrooms_min: Optional[int] = None
    bathrooms_ideal: Optional[int] = None
    sqft_min: Optional[int] = None
    sqft_ideal: Optional[int] = None
    required_features: List[str] = field(default_factory=list)
    preferred_features: List[str] = field(default_factory=list)
    avoided_features: List[str] = field(default_factory=list)


@dataclass
class LifestylePreferences:
    """Extracted lifestyle preferences."""
    school_importance: float = 0.5
    commute_sensitivity: float = 0.5
    investment_focus: float = 0.0
    neighborhood_type: str = "suburban"
    commute_to: Optional[str] = None
    commute_max_minutes: Optional[int] = None


@dataclass
class ExtractedPreferences:
    """Complete extracted preferences."""
    lead_id: str
    budget: BudgetPreference
    locations: List[LocationPreference]
    features: FeaturePreferences
    lifestyle: LifestylePreferences
    property_types: List[str]
    overall_confidence: float
    extraction_sources: List[str]
    extracted_at: str


# Pattern definitions for extraction
BUDGET_PATTERNS = {
    "explicit_max": [
        r"budget\s*(?:is|of)?\s*\$?([\d,]+)k?",
        r"(?:max|maximum)\s*\$?([\d,]+)k?",
        r"(?:up to|under)\s*\$?([\d,]+)k?",
        r"(?:can't|cannot)\s*(?:go over|exceed)\s*\$?([\d,]+)k?",
    ],
    "explicit_range": [
        r"\$?([\d,]+)k?\s*(?:to|-)\s*\$?([\d,]+)k?",
        r"(?:between|from)\s*\$?([\d,]+)k?\s*(?:to|and|-)\s*\$?([\d,]+)k?",
    ],
    "flexible": [
        r"(?:could|might|can)\s*stretch",
        r"flexible\s*(?:on|with)?\s*(?:budget|price)",
        r"if.*right\s*(?:property|home)",
    ],
    "firm": [
        r"(?:firm|strict)\s*budget",
        r"(?:can't|cannot|won't)\s*go\s*(?:over|above)",
        r"absolute\s*max",
    ]
}

LOCATION_PATTERNS = {
    "explicit": [
        r"(?:looking|want|interested)\s*(?:in|at|to live in)\s+([A-Z][a-zA-Z\s]+)",
        r"(?:area|neighborhood|location):\s*([A-Z][a-zA-Z\s]+)",
        r"(?:near|close to)\s+([A-Z][a-zA-Z\s]+)",
    ],
    "negative": [
        r"(?:not|don't want)\s+([A-Z][a-zA-Z\s]+)",
        r"(?:avoid|stay away from)\s+([A-Z][a-zA-Z\s]+)",
    ]
}

FEATURE_PATTERNS = {
    "bedrooms": [
        r"(\d+)\s*(?:bed|bedroom|br)",
        r"(?:need|want|at least)\s*(\d+)\s*(?:bed|bedroom|br)",
    ],
    "bathrooms": [
        r"(\d+(?:\.\d)?)\s*(?:bath|bathroom|ba)",
        r"(?:need|want|at least)\s*(\d+(?:\.\d)?)\s*(?:bath|bathroom|ba)",
    ],
    "sqft": [
        r"(\d{3,4})\s*(?:sq\s*ft|sqft|square\s*feet)",
        r"(?:at least|minimum)\s*(\d{3,4})\s*(?:sq|square)",
    ],
    "required": [
        r"(?:must|need|require|have to have)\s+(?:a\s+)?([a-zA-Z\s]+)",
        r"(?:essential|non-negotiable):\s*([a-zA-Z\s]+)",
    ],
    "preferred": [
        r"(?:would like|prefer|nice to have)\s+(?:a\s+)?([a-zA-Z\s]+)",
        r"(?:ideally|hopefully)\s+(?:a\s+)?([a-zA-Z\s]+)",
    ],
    "avoided": [
        r"(?:no|don't want|avoid)\s+([a-zA-Z\s]+)",
        r"(?:hate|dislike)\s+([a-zA-Z\s]+)",
    ]
}

LIFESTYLE_PATTERNS = {
    "schools": [
        r"school\s*(?:rating|score|district)",
        r"(?:good|great|top)\s*schools",
        r"(?:kids|children)\s*(?:school|education)",
    ],
    "commute": [
        r"commute\s*(?:to|time)",
        r"work\s*(?:in|at|near)\s+([A-Z][a-zA-Z\s]+)",
        r"(?:close|near)\s*(?:to)?\s*(?:downtown|work|office)",
    ],
    "investment": [
        r"(?:investment|rental|income)\s*property",
        r"(?:appreciation|equity|value)",
        r"(?:rent|lease)\s*(?:out|it)",
    ]
}


def parse_price(price_str: str) -> int:
    """Parse price string to integer."""
    # Remove commas and dollar signs
    cleaned = re.sub(r'[$,]', '', price_str)

    # Handle 'k' suffix
    if cleaned.lower().endswith('k'):
        return int(float(cleaned[:-1]) * 1000)

    return int(float(cleaned))


def extract_budget(messages: List[Dict]) -> BudgetPreference:
    """Extract budget preferences from messages."""
    budget = BudgetPreference()
    found_prices = []

    for msg in messages:
        text = msg.get("content", "").lower()

        # Check for explicit max
        for pattern in BUDGET_PATTERNS["explicit_max"]:
            matches = re.findall(pattern, text)
            for match in matches:
                price = parse_price(match)
                found_prices.append(("max", price))
                budget.max_price = price
                budget.confidence = 0.9
                budget.source = "explicit"

        # Check for ranges
        for pattern in BUDGET_PATTERNS["explicit_range"]:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) == 2:
                    min_p = parse_price(match[0])
                    max_p = parse_price(match[1])
                    budget.min_price = min_p
                    budget.max_price = max_p
                    budget.target_price = int((min_p + max_p) / 2)
                    budget.confidence = 0.95
                    budget.source = "explicit"

        # Check flexibility
        for pattern in BUDGET_PATTERNS["flexible"]:
            if re.search(pattern, text):
                budget.flexibility = "flexible"

        for pattern in BUDGET_PATTERNS["firm"]:
            if re.search(pattern, text):
                budget.flexibility = "firm"

    # If only max found, estimate target
    if budget.max_price and not budget.target_price:
        budget.target_price = int(budget.max_price * 0.9)

    return budget


def extract_locations(messages: List[Dict]) -> List[LocationPreference]:
    """Extract location preferences from messages."""
    locations = []
    location_counts = defaultdict(int)
    avoided_locations = set()

    for msg in messages:
        text = msg.get("content", "")

        # Find explicit locations
        for pattern in LOCATION_PATTERNS["explicit"]:
            matches = re.findall(pattern, text)
            for match in matches:
                area = match.strip()
                if len(area) > 2 and area not in avoided_locations:
                    location_counts[area] += 1

        # Find avoided locations
        for pattern in LOCATION_PATTERNS["negative"]:
            matches = re.findall(pattern, text)
            for match in matches:
                avoided_locations.add(match.strip())

    # Sort by mention count and create preferences
    sorted_locations = sorted(
        location_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )

    for priority, (area, count) in enumerate(sorted_locations[:5], 1):
        confidence = min(0.9, 0.5 + count * 0.1)
        locations.append(LocationPreference(
            area=area,
            priority=priority,
            confidence=confidence,
            source="explicit" if count > 1 else "inferred"
        ))

    return locations


def extract_features(messages: List[Dict]) -> FeaturePreferences:
    """Extract feature preferences from messages."""
    features = FeaturePreferences()

    for msg in messages:
        text = msg.get("content", "").lower()

        # Extract bedrooms
        for pattern in FEATURE_PATTERNS["bedrooms"]:
            matches = re.findall(pattern, text)
            for match in matches:
                beds = int(match)
                if features.bedrooms_min is None or beds > features.bedrooms_min:
                    features.bedrooms_min = beds
                    features.bedrooms_ideal = beds

        # Extract bathrooms
        for pattern in FEATURE_PATTERNS["bathrooms"]:
            matches = re.findall(pattern, text)
            for match in matches:
                baths = float(match)
                if features.bathrooms_min is None or baths > features.bathrooms_min:
                    features.bathrooms_min = baths
                    features.bathrooms_ideal = baths

        # Extract square footage
        for pattern in FEATURE_PATTERNS["sqft"]:
            matches = re.findall(pattern, text)
            for match in matches:
                sqft = int(match)
                if features.sqft_min is None or sqft > features.sqft_min:
                    features.sqft_min = sqft
                    features.sqft_ideal = sqft

        # Extract required features
        for pattern in FEATURE_PATTERNS["required"]:
            matches = re.findall(pattern, text)
            for match in matches:
                feature = match.strip().lower()
                if len(feature) > 2 and feature not in features.required_features:
                    features.required_features.append(feature)

        # Extract preferred features
        for pattern in FEATURE_PATTERNS["preferred"]:
            matches = re.findall(pattern, text)
            for match in matches:
                feature = match.strip().lower()
                if len(feature) > 2 and feature not in features.preferred_features:
                    features.preferred_features.append(feature)

        # Extract avoided features
        for pattern in FEATURE_PATTERNS["avoided"]:
            matches = re.findall(pattern, text)
            for match in matches:
                feature = match.strip().lower()
                if len(feature) > 2 and feature not in features.avoided_features:
                    features.avoided_features.append(feature)

    return features


def extract_lifestyle(messages: List[Dict]) -> LifestylePreferences:
    """Extract lifestyle preferences from messages."""
    lifestyle = LifestylePreferences()
    school_mentions = 0
    commute_mentions = 0
    investment_mentions = 0

    for msg in messages:
        text = msg.get("content", "").lower()

        # Count school mentions
        for pattern in LIFESTYLE_PATTERNS["schools"]:
            if re.search(pattern, text):
                school_mentions += 1

        # Count commute mentions
        for pattern in LIFESTYLE_PATTERNS["commute"]:
            if re.search(pattern, text):
                commute_mentions += 1

            # Try to extract work location
            match = re.search(r"work\s*(?:in|at|near)\s+([A-Z][a-zA-Z\s]+)", msg.get("content", ""))
            if match:
                lifestyle.commute_to = match.group(1).strip()

        # Count investment mentions
        for pattern in LIFESTYLE_PATTERNS["investment"]:
            if re.search(pattern, text):
                investment_mentions += 1

    # Calculate importance scores
    total_mentions = school_mentions + commute_mentions + investment_mentions + 1  # +1 to avoid div/0

    lifestyle.school_importance = min(1.0, school_mentions / 3)
    lifestyle.commute_sensitivity = min(1.0, commute_mentions / 3)
    lifestyle.investment_focus = min(1.0, investment_mentions / 3)

    # Determine neighborhood type from context
    # (simplified - would use more sophisticated analysis in production)
    if lifestyle.investment_focus > 0.5:
        lifestyle.neighborhood_type = "urban"
    elif lifestyle.school_importance > 0.5:
        lifestyle.neighborhood_type = "suburban"

    return lifestyle


def infer_property_types(features: FeaturePreferences, lifestyle: LifestylePreferences) -> List[str]:
    """Infer preferred property types from other preferences."""
    types = []

    # Default to single family
    types.append("single_family")

    # Add condo if investment or urban
    if lifestyle.investment_focus > 0.3 or lifestyle.neighborhood_type == "urban":
        types.append("condo")

    # Add townhouse as middle ground
    if features.bedrooms_min and features.bedrooms_min >= 3:
        types.append("townhouse")

    return types


def calculate_overall_confidence(
    budget: BudgetPreference,
    locations: List[LocationPreference],
    features: FeaturePreferences
) -> float:
    """Calculate overall confidence in extracted preferences."""
    scores = []

    # Budget confidence
    if budget.max_price:
        scores.append(budget.confidence)
    else:
        scores.append(0.3)

    # Location confidence
    if locations:
        scores.append(max(loc.confidence for loc in locations))
    else:
        scores.append(0.3)

    # Features confidence
    feature_score = 0.3
    if features.bedrooms_min:
        feature_score += 0.2
    if features.bathrooms_min:
        feature_score += 0.1
    if features.sqft_min:
        feature_score += 0.1
    if features.required_features:
        feature_score += 0.2
    scores.append(min(1.0, feature_score))

    return sum(scores) / len(scores)


def load_messages(lead_id: str, conversations_file: Optional[str] = None) -> List[Dict]:
    """Load conversation messages."""
    if conversations_file:
        try:
            with open(conversations_file, 'r') as f:
                data = json.load(f)
                return data.get("messages", data) if isinstance(data, dict) else data
        except FileNotFoundError:
            pass

    # Return mock data for demonstration
    return [
        {"role": "lead", "content": "Hi, we're looking for a home in Round Rock or Cedar Park area."},
        {"role": "agent", "content": "Great! What's your budget range?"},
        {"role": "lead", "content": "Our budget is around $650,000, but we could stretch to $700k for the right place."},
        {"role": "agent", "content": "And how many bedrooms do you need?"},
        {"role": "lead", "content": "We need at least 4 bedrooms and 3 bathrooms. Must have a pool - that's non-negotiable."},
        {"role": "agent", "content": "Any other must-haves?"},
        {"role": "lead", "content": "Good schools are really important - we have two kids. I work in downtown Rancho Cucamonga so commute matters too."},
        {"role": "lead", "content": "Also, we'd prefer at least 2500 square feet. No HOA if possible."},
    ]


def extract_preferences(lead_id: str, messages: List[Dict]) -> ExtractedPreferences:
    """Main extraction function."""
    budget = extract_budget(messages)
    locations = extract_locations(messages)
    features = extract_features(messages)
    lifestyle = extract_lifestyle(messages)
    property_types = infer_property_types(features, lifestyle)
    confidence = calculate_overall_confidence(budget, locations, features)

    sources = ["conversations"]
    if budget.source == "explicit":
        sources.append("explicit_budget")
    if any(loc.source == "explicit" for loc in locations):
        sources.append("explicit_locations")

    return ExtractedPreferences(
        lead_id=lead_id,
        budget=budget,
        locations=locations,
        features=features,
        lifestyle=lifestyle,
        property_types=property_types,
        overall_confidence=confidence,
        extraction_sources=sources,
        extracted_at=datetime.now().isoformat()
    )


def preferences_to_dict(prefs: ExtractedPreferences) -> Dict[str, Any]:
    """Convert ExtractedPreferences to dict for JSON serialization."""
    return {
        "lead_id": prefs.lead_id,
        "budget": {
            "min": prefs.budget.min_price,
            "target": prefs.budget.target_price,
            "max": prefs.budget.max_price,
            "flexibility": prefs.budget.flexibility,
            "confidence": prefs.budget.confidence,
            "source": prefs.budget.source
        },
        "locations": [
            {
                "area": loc.area,
                "priority": loc.priority,
                "confidence": loc.confidence,
                "source": loc.source
            }
            for loc in prefs.locations
        ],
        "features": {
            "bedrooms": {
                "min": prefs.features.bedrooms_min,
                "ideal": prefs.features.bedrooms_ideal
            },
            "bathrooms": {
                "min": prefs.features.bathrooms_min,
                "ideal": prefs.features.bathrooms_ideal
            },
            "sqft": {
                "min": prefs.features.sqft_min,
                "ideal": prefs.features.sqft_ideal
            },
            "required": prefs.features.required_features,
            "preferred": prefs.features.preferred_features,
            "avoid": prefs.features.avoided_features
        },
        "lifestyle": {
            "school_importance": prefs.lifestyle.school_importance,
            "commute_sensitivity": prefs.lifestyle.commute_sensitivity,
            "investment_focus": prefs.lifestyle.investment_focus,
            "neighborhood_type": prefs.lifestyle.neighborhood_type,
            "commute_to": prefs.lifestyle.commute_to,
            "commute_max_minutes": prefs.lifestyle.commute_max_minutes
        },
        "property_types": prefs.property_types,
        "overall_confidence": prefs.overall_confidence,
        "extraction_sources": prefs.extraction_sources,
        "extracted_at": prefs.extracted_at
    }


def main():
    parser = argparse.ArgumentParser(
        description="Extract buyer preferences from conversations"
    )
    parser.add_argument(
        "--lead-id",
        required=True,
        help="Lead ID to extract preferences for"
    )
    parser.add_argument(
        "--conversations",
        help="JSON file with conversation messages"
    )
    parser.add_argument(
        "--output",
        choices=["json", "text"],
        default="text",
        help="Output format"
    )

    args = parser.parse_args()

    # Load messages
    messages = load_messages(args.lead_id, args.conversations)

    if not messages:
        print("Error: No conversation messages found")
        sys.exit(1)

    # Extract preferences
    preferences = extract_preferences(args.lead_id, messages)

    # Output
    if args.output == "json":
        print(json.dumps(preferences_to_dict(preferences), indent=2))
    else:
        print("\n" + "=" * 60)
        print("EXTRACTED PREFERENCES")
        print("=" * 60)
        print(f"\nLead ID: {preferences.lead_id}")
        print(f"Overall Confidence: {preferences.overall_confidence:.0%}")
        print(f"Extracted At: {preferences.extracted_at}")

        print("\n" + "-" * 60)
        print("BUDGET")
        print("-" * 60)
        b = preferences.budget
        if b.max_price:
            print(f"  Target: ${b.target_price:,}" if b.target_price else "  Target: Unknown")
            print(f"  Maximum: ${b.max_price:,}")
            if b.min_price:
                print(f"  Minimum: ${b.min_price:,}")
            print(f"  Flexibility: {b.flexibility.title()}")
            print(f"  Confidence: {b.confidence:.0%}")
        else:
            print("  No budget extracted")

        print("\n" + "-" * 60)
        print("LOCATIONS (Priority Order)")
        print("-" * 60)
        if preferences.locations:
            for loc in preferences.locations:
                print(f"  {loc.priority}. {loc.area}")
                print(f"     Confidence: {loc.confidence:.0%} | Source: {loc.source}")
        else:
            print("  No locations extracted")

        print("\n" + "-" * 60)
        print("FEATURES")
        print("-" * 60)
        f = preferences.features
        if f.bedrooms_min:
            print(f"  Bedrooms: {f.bedrooms_min}+ (ideal: {f.bedrooms_ideal})")
        if f.bathrooms_min:
            print(f"  Bathrooms: {f.bathrooms_min}+ (ideal: {f.bathrooms_ideal})")
        if f.sqft_min:
            print(f"  Square Feet: {f.sqft_min}+ (ideal: {f.sqft_ideal})")

        if f.required_features:
            print(f"\n  Required: {', '.join(f.required_features)}")
        if f.preferred_features:
            print(f"  Preferred: {', '.join(f.preferred_features)}")
        if f.avoided_features:
            print(f"  Avoid: {', '.join(f.avoided_features)}")

        print("\n" + "-" * 60)
        print("LIFESTYLE")
        print("-" * 60)
        l = preferences.lifestyle
        print(f"  School Importance: {l.school_importance:.0%}")
        print(f"  Commute Sensitivity: {l.commute_sensitivity:.0%}")
        print(f"  Investment Focus: {l.investment_focus:.0%}")
        print(f"  Neighborhood Type: {l.neighborhood_type.title()}")
        if l.commute_to:
            print(f"  Commute To: {l.commute_to}")

        print("\n" + "-" * 60)
        print("PROPERTY TYPES")
        print("-" * 60)
        print(f"  {', '.join(preferences.property_types)}")

        print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
