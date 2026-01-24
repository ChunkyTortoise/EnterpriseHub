#!/usr/bin/env python3
"""
Test budget detection for Jorge's lead intelligence
"""

import sys
import re
from lead_intelligence_optimized import get_enhanced_lead_intelligence, PredictiveLeadScorerV2Optimized

def test_budget_detection():
    """Test budget detection with the failing test case"""

    # Test case that's failing
    test_message = "Sarah Martinez, VP at Tesla, $750k budget, Westlake Hills, pre-approved, 45 days"

    print("=== JORGE LEAD INTELLIGENCE DEBUG ===")
    print(f"Input: {test_message}")
    print()

    # Test the enhanced lead intelligence
    result = get_enhanced_lead_intelligence(test_message)

    print("=== CURRENT RESULTS ===")
    for key, value in result.items():
        print(f"{key}: {value}")
    print()

    # Test individual components
    scorer = PredictiveLeadScorerV2Optimized()
    profile = scorer.analyze_lead_message(test_message)

    print("=== DETAILED PROFILE ANALYSIS ===")
    print(f"Budget Min: {profile.budget_min}")
    print(f"Budget Max: {profile.budget_max}")
    print(f"Timeline: {profile.timeline}")
    print(f"Location Preferences: {profile.location_preferences}")
    print(f"Financing Status: {profile.financing_status}")
    print(f"Has Specific Budget: {profile.has_specific_budget}")
    print(f"Has Clear Timeline: {profile.has_clear_timeline}")
    print(f"Is Pre-Approved: {profile.is_pre_approved}")
    print(f"Urgency Score: {profile.urgency_score}")
    print(f"Qualification Score: {profile.qualification_score}")
    print(f"Intent Confidence: {profile.intent_confidence}")
    print(f"Parsing Errors: {profile.parsing_errors}")
    print()

    # Test budget patterns manually
    print("=== MANUAL BUDGET PATTERN TESTING ===")
    message_clean = test_message.lower()

    budget_patterns = [
        r'\$([0-9]{1,3}(?:,?[0-9]{3})*?)k\b',  # $500k, $1,000k
        r'\$([0-9]{1,3}(?:,?[0-9]{3})*?),?000\b',  # $500,000
        r'([0-9]{1,3}(?:,?[0-9]{3})*?)k budget',  # 500k budget
        r'under \$([0-9]{1,3}(?:,?[0-9]{3})*?)k?',  # under $500k
        r'up to \$([0-9]{1,3}(?:,?[0-9]{3})*?)k?',  # up to $500
        r'around \$([0-9]{1,3}(?:,?[0-9]{3})*?)k?',  # around $500k
        r'budget.*?\$([0-9]{1,3}(?:,?[0-9]{3})*?)k?',  # budget of $500k
    ]

    for i, pattern in enumerate(budget_patterns):
        matches = re.findall(pattern, message_clean, re.IGNORECASE)
        print(f"Pattern {i+1} ({pattern}): {matches}")

    print()
    print("=== EXPECTED RESULTS FOR HIGH-QUALITY LEAD ===")
    print("Lead Score: 90+ (currently getting:", result.get('lead_score', 'unknown'), ")")
    print("Budget Max: $750,000 (currently getting:", result.get('budget_max', 'unknown'), ")")
    print("Timeline: 2_months (currently getting:", result.get('timeline_analysis', 'unknown'), ")")
    print("Pre-approved: True (currently getting:", result.get('is_pre_approved', 'unknown'), ")")
    print("Temperature: Should be HOT")

if __name__ == "__main__":
    test_budget_detection()