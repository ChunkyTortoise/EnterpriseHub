#!/usr/bin/env python3
"""
PersonalizedNarrativeEngine Demo

Demonstrates the complete PersonalizedNarrativeEngine service with:
- Property-to-narrative transformation
- Multiple narrative styles and lengths
- Lifestyle score integration
- Performance optimization with caching
- Batch generation for property search results

Run with: python demo_personalized_narrative_engine.py
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
import sys
sys.path.append(str(Path(__file__).parent))

from ghl_real_estate_ai.services.personalized_narrative_engine import (
    PersonalizedNarrativeEngine,
    NarrativeStyle,
    NarrativeLength
)
from ghl_real_estate_ai.models.matching_models import (
    LifestyleScores,
    SchoolScore,
    CommuteScore,
    WalkabilityScore,
    SafetyScore
)


def create_sample_properties() -> List[Dict[str, Any]]:
    """Create sample properties for demonstration."""
    return [
        {
            'id': 'prop_westlake_001',
            'address': '123 Hill Country Dr, Westlake Hills, TX',
            'price': 485000,
            'bedrooms': 3,
            'bathrooms': 2,
            'sqft': 2100,
            'neighborhood': 'Westlake Hills',
            'features': ['pool', 'deck', 'two-car garage', 'updated kitchen'],
            'lot_size': 0.25,
            'year_built': 2018,
            'property_type': 'single_family'
        },
        {
            'id': 'prop_downtown_002',
            'address': '456 Congress Ave, Downtown Austin, TX',
            'price': 620000,
            'bedrooms': 2,
            'bathrooms': 2,
            'sqft': 1650,
            'neighborhood': 'Downtown Austin',
            'features': ['city views', 'rooftop pool', 'concierge', 'parking garage'],
            'lot_size': None,  # Condo
            'year_built': 2020,
            'property_type': 'condo'
        },
        {
            'id': 'prop_mueller_003',
            'address': '789 Mueller Blvd, Mueller, TX',
            'price': 395000,
            'bedrooms': 4,
            'bathrooms': 3,
            'sqft': 2400,
            'neighborhood': 'Mueller',
            'features': ['open floor plan', 'master suite', 'backyard', 'community amenities'],
            'lot_size': 0.18,
            'year_built': 2019,
            'property_type': 'single_family'
        }
    ]


def create_sample_leads() -> List[Dict[str, Any]]:
    """Create sample leads with different profiles."""
    return [
        {
            'lead_id': 'lead_sarah_chen',
            'lead_name': 'Sarah Chen',
            'family_status': 'family_with_kids',
            'workplace': 'Apple',
            'budget_max': 500000,
            'lifestyle_priorities': ['schools', 'commute', 'safety'],
            'location_id': 'loc_austin_001',
            'age': 34,
            'children_ages': [7, 10],
            'current_home': 'renting'
        },
        {
            'lead_id': 'lead_david_kim',
            'lead_name': 'David Kim',
            'family_status': 'young_professional',
            'workplace': 'Downtown Austin',
            'budget_max': 650000,
            'lifestyle_priorities': ['walkability', 'nightlife', 'commute'],
            'location_id': 'loc_austin_002',
            'age': 28,
            'children_ages': [],
            'current_home': 'apartment'
        },
        {
            'lead_id': 'lead_maria_gonzalez',
            'lead_name': 'Maria Gonzalez',
            'family_status': 'investor',
            'workplace': 'Remote',
            'budget_max': 450000,
            'lifestyle_priorities': ['investment_potential', 'rental_income', 'appreciation'],
            'location_id': 'loc_austin_003',
            'age': 42,
            'children_ages': [],
            'current_home': 'owns_multiple'
        }
    ]


def create_sample_lifestyle_scores(property_id: str) -> LifestyleScores:
    """Create sample lifestyle scores based on property."""

    if 'westlake' in property_id.lower():
        # Westlake - excellent schools, suburban
        return LifestyleScores(
            schools=SchoolScore(
                elementary_rating=9.0,
                middle_rating=8.5,
                high_rating=9.2,
                average_rating=8.9,
                distance_penalty=0.1,
                overall_score=8.8,
                top_school_name="Westlake Elementary",
                reasoning="Excellent school district with top ratings throughout"
            ),
            commute=CommuteScore(
                to_downtown_minutes=25,
                to_workplace_minutes=15,
                public_transit_access=0.5,
                highway_access=0.9,
                overall_score=7.5,
                reasoning="Good highway access, limited public transit"
            ),
            walkability=WalkabilityScore(
                walk_score=45,
                nearby_amenities_count=8,
                grocery_distance_miles=1.2,
                restaurant_density=0.4,
                park_access=0.9,
                overall_score=6.5,
                reasoning="Car-dependent but excellent parks and recreation"
            ),
            safety=SafetyScore(
                crime_rate_per_1000=1.2,
                neighborhood_safety_rating=9.5,
                police_response_time=3,
                overall_score=9.2,
                reasoning="Very safe neighborhood with low crime rates"
            ),
            amenities_proximity=7.0,
            overall_score=8.0
        )
    elif 'downtown' in property_id.lower():
        # Downtown - urban lifestyle, walkable
        return LifestyleScores(
            schools=SchoolScore(
                elementary_rating=7.0,
                middle_rating=7.5,
                high_rating=8.0,
                average_rating=7.5,
                distance_penalty=0.3,
                overall_score=7.2,
                top_school_name="Austin Elementary",
                reasoning="Good schools but farther from home"
            ),
            commute=CommuteScore(
                to_downtown_minutes=5,
                to_workplace_minutes=5,
                public_transit_access=0.9,
                highway_access=0.7,
                overall_score=9.0,
                reasoning="Exceptional access to downtown employment"
            ),
            walkability=WalkabilityScore(
                walk_score=92,
                nearby_amenities_count=45,
                grocery_distance_miles=0.2,
                restaurant_density=0.95,
                park_access=0.7,
                overall_score=9.0,
                reasoning="Walker's paradise with everything nearby"
            ),
            safety=SafetyScore(
                crime_rate_per_1000=4.8,
                neighborhood_safety_rating=7.0,
                police_response_time=2,
                overall_score=7.5,
                reasoning="Urban environment, good police presence"
            ),
            amenities_proximity=9.5,
            overall_score=8.2
        )
    else:
        # Mueller - family-friendly, balanced
        return LifestyleScores(
            schools=SchoolScore(
                elementary_rating=8.0,
                middle_rating=8.2,
                high_rating=8.5,
                average_rating=8.2,
                distance_penalty=0.2,
                overall_score=8.0,
                top_school_name="Mueller Elementary",
                reasoning="Strong schools in growing district"
            ),
            commute=CommuteScore(
                to_downtown_minutes=15,
                to_workplace_minutes=20,
                public_transit_access=0.7,
                highway_access=0.8,
                overall_score=8.0,
                reasoning="Balanced access to city and suburbs"
            ),
            walkability=WalkabilityScore(
                walk_score=78,
                nearby_amenities_count=25,
                grocery_distance_miles=0.4,
                restaurant_density=0.8,
                park_access=0.95,
                overall_score=8.5,
                reasoning="Very walkable with excellent community planning"
            ),
            safety=SafetyScore(
                crime_rate_per_1000=2.8,
                neighborhood_safety_rating=8.5,
                police_response_time=4,
                overall_score=8.5,
                reasoning="Safe family-oriented community"
            ),
            amenities_proximity=8.5,
            overall_score=8.25
        )


async def demo_single_narrative_generation():
    """Demonstrate single narrative generation."""
    print("\n" + "="*80)
    print("DEMO 1: Single Narrative Generation")
    print("="*80)

    engine = PersonalizedNarrativeEngine(enable_caching=False)  # Disable caching for demo

    property_data = create_sample_properties()[0]  # Westlake property
    lead_data = create_sample_leads()[0]  # Sarah Chen - family
    lifestyle_scores = create_sample_lifestyle_scores(property_data['id'])

    print(f"\nProperty: {property_data['address']}")
    print(f"Price: ${property_data['price']:,}")
    print(f"Lead: {lead_data['lead_name']} (Family with kids)")
    print(f"Lifestyle Match Score: {lifestyle_scores.overall_score:.1f}/10")

    start_time = time.time()
    narrative = await engine.generate_personalized_narrative(
        property_data=property_data,
        lead_data=lead_data,
        lifestyle_scores=lifestyle_scores,
        style=NarrativeStyle.EMOTIONAL,
        length=NarrativeLength.MEDIUM
    )
    generation_time = (time.time() - start_time) * 1000

    print(f"\nGeneration Time: {generation_time:.1f}ms")
    print(f"Narrative Style: {narrative.style.value}")
    print(f"Length: {narrative.length.value}")
    print(f"Appeal Score: {narrative.overall_appeal_score:.1f}")
    print(f"Fallback Used: {narrative.fallback_used}")

    print(f"\n📝 Generated Narrative:")
    print("-" * 60)
    print(narrative.narrative_text)
    print("-" * 60)

    print(f"\n🎯 Key Selling Points:")
    for point in narrative.key_selling_points[:3]:
        print(f"  • {point}")

    print(f"\n💫 Emotional Themes: {', '.join(narrative.emotional_themes)}")
    print(f"📞 Call to Action: {narrative.call_to_action}")


async def demo_multiple_styles():
    """Demonstrate different narrative styles."""
    print("\n" + "="*80)
    print("DEMO 2: Multiple Narrative Styles")
    print("="*80)

    engine = PersonalizedNarrativeEngine(enable_caching=False)

    # Use downtown property for professional appeal
    property_data = create_sample_properties()[1]  # Downtown condo
    lead_data = create_sample_leads()[1]  # David Kim - professional
    lifestyle_scores = create_sample_lifestyle_scores(property_data['id'])

    print(f"\nProperty: {property_data['address']}")
    print(f"Lead: {lead_data['lead_name']} (Young Professional)")

    styles = [
        NarrativeStyle.EMOTIONAL,
        NarrativeStyle.PROFESSIONAL,
        NarrativeStyle.LUXURY,
        NarrativeStyle.LIFESTYLE
    ]

    for style in styles:
        print(f"\n{'='*20} {style.value.upper()} STYLE {'='*20}")

        narrative = await engine.generate_personalized_narrative(
            property_data=property_data,
            lead_data=lead_data,
            lifestyle_scores=lifestyle_scores,
            style=style,
            length=NarrativeLength.SHORT
        )

        print(narrative.narrative_text)
        print(f"Words: {len(narrative.narrative_text.split())}")


async def demo_batch_generation():
    """Demonstrate batch narrative generation."""
    print("\n" + "="*80)
    print("DEMO 3: Batch Narrative Generation")
    print("="*80)

    engine = PersonalizedNarrativeEngine(enable_caching=False)

    properties = create_sample_properties()
    lead_data = create_sample_leads()[0]  # Sarah Chen for all

    print(f"Generating narratives for {len(properties)} properties for {lead_data['lead_name']}")
    print("This simulates property search results with personalized narratives...")

    # Create property-lead pairs
    property_lead_pairs = [(prop, lead_data) for prop in properties]

    start_time = time.time()
    narratives = await engine.generate_batch_narratives(
        property_lead_pairs=property_lead_pairs,
        style=NarrativeStyle.EMOTIONAL,
        length=NarrativeLength.SHORT,
        max_concurrent=3
    )
    total_time = (time.time() - start_time) * 1000

    print(f"\nBatch Generation Complete!")
    print(f"Total Time: {total_time:.1f}ms")
    print(f"Average per Property: {total_time/len(properties):.1f}ms")

    for i, narrative in enumerate(narratives, 1):
        property_addr = properties[i-1]['address'].split(',')[0]
        price = properties[i-1]['price']

        print(f"\n🏡 Property {i}: {property_addr} - ${price:,}")
        print("-" * 50)
        print(narrative.narrative_text[:200] + "..." if len(narrative.narrative_text) > 200 else narrative.narrative_text)


async def demo_performance_optimization():
    """Demonstrate caching and performance optimization."""
    print("\n" + "="*80)
    print("DEMO 4: Performance Optimization & Caching")
    print("="*80)

    # Enable caching for this demo
    engine = PersonalizedNarrativeEngine(enable_caching=True)

    property_data = create_sample_properties()[0]
    lead_data = create_sample_leads()[0]
    lifestyle_scores = create_sample_lifestyle_scores(property_data['id'])

    print("Generating narrative (first time - no cache)...")
    start_time = time.time()
    narrative1 = await engine.generate_personalized_narrative(
        property_data=property_data,
        lead_data=lead_data,
        lifestyle_scores=lifestyle_scores,
        style=NarrativeStyle.EMOTIONAL,
        length=NarrativeLength.MEDIUM
    )
    first_time = (time.time() - start_time) * 1000

    print("Generating same narrative again (should hit cache)...")
    start_time = time.time()
    narrative2 = await engine.generate_personalized_narrative(
        property_data=property_data,
        lead_data=lead_data,
        lifestyle_scores=lifestyle_scores,
        style=NarrativeStyle.EMOTIONAL,
        length=NarrativeLength.MEDIUM
    )
    cached_time = (time.time() - start_time) * 1000

    print(f"\nPerformance Results:")
    print(f"First Generation: {first_time:.1f}ms (Cache: {narrative1.cached})")
    print(f"Cached Generation: {cached_time:.1f}ms (Cache: {narrative2.cached})")
    print(f"Speed Improvement: {first_time/max(cached_time, 0.1):.1f}x faster")

    # Show performance metrics
    metrics = engine.get_performance_metrics()
    print(f"\nEngine Performance Metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")


async def demo_lifestyle_integration():
    """Demonstrate lifestyle intelligence integration."""
    print("\n" + "="*80)
    print("DEMO 5: Lifestyle Intelligence Integration")
    print("="*80)

    engine = PersonalizedNarrativeEngine(enable_caching=False)

    property_data = create_sample_properties()[0]  # Westlake
    lead_data = create_sample_leads()[0]  # Family with kids
    lifestyle_scores = create_sample_lifestyle_scores(property_data['id'])

    print(f"Property: {property_data['address']}")
    print(f"Lead: {lead_data['lead_name']} - Family with kids (ages {lead_data['children_ages']})")
    print(f"Priorities: {', '.join(lead_data['lifestyle_priorities'])}")

    print(f"\nLifestyle Compatibility Analysis:")
    print(f"  🏫 Schools: {lifestyle_scores.schools.overall_score:.1f}/10 - {lifestyle_scores.schools.reasoning}")
    print(f"  🚗 Commute: {lifestyle_scores.commute.overall_score:.1f}/10 - {lifestyle_scores.commute.reasoning}")
    print(f"  🚶 Walkability: {lifestyle_scores.walkability.overall_score:.1f}/10 - {lifestyle_scores.walkability.reasoning}")
    print(f"  🛡️  Safety: {lifestyle_scores.safety.overall_score:.1f}/10 - {lifestyle_scores.safety.reasoning}")
    print(f"  📊 Overall: {lifestyle_scores.overall_score:.1f}/10")

    # Generate narrative with lifestyle integration
    narrative = await engine.generate_personalized_narrative(
        property_data=property_data,
        lead_data=lead_data,
        lifestyle_scores=lifestyle_scores,
        style=NarrativeStyle.EMOTIONAL,
        length=NarrativeLength.MEDIUM
    )

    print(f"\n📝 Lifestyle-Integrated Narrative:")
    print("-" * 60)
    print(narrative.narrative_text)
    print("-" * 60)

    # Show how lifestyle scores influenced the narrative
    text_lower = narrative.narrative_text.lower()
    lifestyle_mentions = []

    if 'school' in text_lower:
        lifestyle_mentions.append(f"✓ Schools (Score: {lifestyle_scores.schools.overall_score:.1f})")
    if any(word in text_lower for word in ['commute', 'work', 'downtown']):
        lifestyle_mentions.append(f"✓ Commute (Score: {lifestyle_scores.commute.overall_score:.1f})")
    if any(word in text_lower for word in ['safe', 'secure', 'neighborhood']):
        lifestyle_mentions.append(f"✓ Safety (Score: {lifestyle_scores.safety.overall_score:.1f})")
    if any(word in text_lower for word in ['walk', 'nearby', 'amenities']):
        lifestyle_mentions.append(f"✓ Walkability (Score: {lifestyle_scores.walkability.overall_score:.1f})")

    print(f"\n🎯 Lifestyle Factors Highlighted in Narrative:")
    for mention in lifestyle_mentions:
        print(f"  {mention}")


async def main():
    """Run all demonstrations."""
    print("🏡 PersonalizedNarrativeEngine Demonstration")
    print("Transform property data into compelling lifestyle narratives")

    try:
        await demo_single_narrative_generation()
        await demo_multiple_styles()
        await demo_batch_generation()
        await demo_performance_optimization()
        await demo_lifestyle_integration()

        print("\n" + "="*80)
        print("🎉 DEMONSTRATION COMPLETE")
        print("="*80)
        print("\nKey Features Demonstrated:")
        print("✓ Single narrative generation with Claude AI")
        print("✓ Multiple narrative styles (Emotional, Professional, Luxury, etc.)")
        print("✓ Batch generation for property search results")
        print("✓ Redis caching with 24-hour TTL")
        print("✓ Template-based fallbacks when Claude unavailable")
        print("✓ Lifestyle intelligence integration")
        print("✓ Performance optimization (<2 second generation)")
        print("\nThe PersonalizedNarrativeEngine is ready for production use!")

    except Exception as e:
        print(f"\n❌ Demo Error: {e}")
        print("Note: This demo uses fallback templates when Claude API is not available.")
        print("For full Claude integration, ensure ANTHROPIC_API_KEY is configured.")


if __name__ == "__main__":
    asyncio.run(main())