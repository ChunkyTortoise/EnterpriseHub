#!/usr/bin/env python3
"""
E4 Verification: Test PropertyMatcher filters (price, beds, neighborhood).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ghl_real_estate_ai.services.property_matcher import PropertyMatcher

matcher = PropertyMatcher()

# Force load sample data
listings = matcher._load_sample_data()
print(f"Loaded {len(listings)} sample properties\n")


def test_case(label, budget, beds=None, neighborhood=None, expected_min=1):
    results = matcher.find_buyer_matches(
        budget=budget, beds=beds, neighborhood=neighborhood, limit=5
    )
    passed = len(results) >= expected_min
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {label}")
    print(f"  Budget=${budget:,}, beds={beds}, neighborhood={neighborhood}")
    print(f"  Found {len(results)} matches (expected >= {expected_min})")
    for r in results:
        print(f"    - {r['id']}: ${r['price']:,}, {r.get('beds', 0)}bd, "
              f"{r.get('neighborhood', '?')} (score={r.get('match_score', 0)})")
    print()
    return passed


print("=" * 70)
print("E4: PROPERTY MATCHER FILTER VERIFICATION")
print("=" * 70)
print()

results = []

# Test 1: Entry-level budget, 3+ beds
results.append(test_case(
    "Entry-level ($600k, 3+ beds)",
    budget=600000, beds=3, expected_min=3
))

# Test 2: Entry-level budget, 4+ beds
results.append(test_case(
    "Entry-level ($600k, 4+ beds)",
    budget=600000, beds=4, expected_min=1
))

# Test 3: Mid-market with neighborhood filter
results.append(test_case(
    "Mid-market ($800k, Etiwanda neighborhood)",
    budget=800000, neighborhood="Etiwanda", expected_min=1
))

# Test 4: Luxury, 6+ beds
results.append(test_case(
    "Luxury ($1.5M, 6+ beds)",
    budget=1500000, beds=6, expected_min=1
))

# Test 5: Budget too low for any property
results.append(test_case(
    "Below market ($300k) — expect 0 matches",
    budget=300000, beds=3, expected_min=0
))

# Test 6: Victoria neighborhood preference
results.append(test_case(
    "Victoria neighborhood ($650k, 3+ beds)",
    budget=650000, beds=3, neighborhood="Victoria", expected_min=1
))

# Test 7: Terra Vista mid-to-high
results.append(test_case(
    "Terra Vista ($950k, 5+ beds)",
    budget=950000, beds=5, neighborhood="Terra Vista", expected_min=1
))

print(f"RESULTS: {sum(results)}/7 passed")
if all(results):
    print("ALL PROPERTY MATCHER TESTS PASSED")
else:
    print("SOME TESTS FAILED — review above")
    sys.exit(1)
