"""
Neighborhood Intelligence API Usage Examples

Demonstrates real-world usage patterns for the Neighborhood Intelligence API
including property matching integration, lead preferences, and optimization strategies.
"""

import asyncio
from typing import Dict, List, Any

from ghl_real_estate_ai.services.neighborhood_intelligence_api import (
    NeighborhoodIntelligenceAPI,
    TransportMode,
    NeighborhoodIntelligence,
)


# ============================================================================
# Example 1: Basic Neighborhood Analysis
# ============================================================================


async def example_basic_analysis():
    """Basic neighborhood analysis for a single property."""
    print("\n=== Example 1: Basic Neighborhood Analysis ===\n")

    # Initialize service
    intelligence_api = NeighborhoodIntelligenceAPI()
    await intelligence_api.initialize()

    try:
        # Analyze neighborhood
        analysis = await intelligence_api.analyze_neighborhood(
            property_address="123 Main St, Austin, TX 78701",
            lat=30.2672,
            lng=-97.7431,
            city="Austin",
            state="TX",
            zipcode="78701",
            commute_destinations=["Downtown Austin", "Tech Ridge"]
        )

        # Display results
        print(f"Property: {analysis.property_address}")
        print(f"Overall Neighborhood Score: {analysis.overall_score}/100")
        print()

        if analysis.walkability:
            print("Walkability Analysis:")
            print(f"  Walk Score: {analysis.walkability.walk_score}/100 - {analysis.walkability.walk_description}")
            print(f"  Transit Score: {analysis.walkability.transit_score}/100")
            print(f"  Bike Score: {analysis.walkability.bike_score}/100")
            print()

        if analysis.schools:
            print("School Ratings:")
            print(f"  Average Rating: {analysis.schools.average_rating}/10")
            print(f"  Elementary Schools: {len(analysis.schools.elementary_schools)}")
            print(f"  Middle Schools: {len(analysis.schools.middle_schools)}")
            print(f"  High Schools: {len(analysis.schools.high_schools)}")
            print()

        if analysis.commute:
            print("Commute Analysis:")
            print(f"  Overall Score: {analysis.commute.overall_commute_score}/100")
            print(f"  Average Commute Time: {analysis.commute.average_commute_time} minutes")
            print(f"  Destinations within 30min: {analysis.commute.employment_centers_within_30min}")
            print(f"  Transit Accessible: {analysis.commute.public_transit_accessible}")
            print()

    finally:
        await intelligence_api.cleanup()


# ============================================================================
# Example 2: Property Matching with Lead Preferences
# ============================================================================


async def example_property_matching():
    """Match properties to lead preferences using neighborhood intelligence."""
    print("\n=== Example 2: Property Matching with Lead Preferences ===\n")

    # Initialize service
    intelligence_api = NeighborhoodIntelligenceAPI()
    await intelligence_api.initialize()

    try:
        # Lead preferences
        lead_preferences = {
            "name": "Jane Smith",
            "work_locations": ["Downtown Austin", "Airport"],
            "school_priority": True,
            "min_school_rating": 8,
            "walkability_important": True,
            "min_walk_score": 70,
            "max_commute_minutes": 30,
            "transit_required": False
        }

        # Properties to analyze
        properties = [
            {
                "id": "prop_001",
                "address": "456 Oak Ave, Austin, TX 78701",
                "lat": 30.2800,
                "lng": -97.7400,
                "city": "Austin",
                "state": "TX",
                "zipcode": "78701",
                "price": 450000
            },
            {
                "id": "prop_002",
                "address": "789 Elm St, Austin, TX 78704",
                "lat": 30.2500,
                "lng": -97.7600,
                "city": "Austin",
                "state": "TX",
                "zipcode": "78704",
                "price": 380000
            }
        ]

        # Analyze all properties in parallel
        print(f"Analyzing {len(properties)} properties for {lead_preferences['name']}...\n")

        analysis_tasks = [
            intelligence_api.analyze_neighborhood(
                property_address=prop["address"],
                lat=prop["lat"],
                lng=prop["lng"],
                city=prop["city"],
                state=prop["state"],
                zipcode=prop["zipcode"],
                commute_destinations=lead_preferences["work_locations"]
            )
            for prop in properties
        ]

        analyses = await asyncio.gather(*analysis_tasks)

        # Calculate match scores
        matches = []
        for prop, analysis in zip(properties, analyses):
            match_score = calculate_match_score(analysis, lead_preferences)
            matches.append({
                "property": prop,
                "analysis": analysis,
                "match_score": match_score,
                "recommendations": generate_recommendations(analysis, lead_preferences)
            })

        # Sort by match score
        matches.sort(key=lambda x: x["match_score"], reverse=True)

        # Display results
        print("Property Match Results (sorted by score):\n")
        for i, match in enumerate(matches, 1):
            prop = match["property"]
            analysis = match["analysis"]

            print(f"{i}. {prop['address']}")
            print(f"   Match Score: {match['match_score']}/100")
            print(f"   Price: ${prop['price']:,}")
            print(f"   Overall Neighborhood Score: {analysis.overall_score}/100")

            if analysis.walkability:
                print(f"   Walk Score: {analysis.walkability.walk_score}/100")

            if analysis.schools:
                print(f"   School Rating: {analysis.schools.average_rating}/10")

            if analysis.commute:
                print(f"   Avg Commute: {analysis.commute.average_commute_time} min")

            print(f"   Recommendations: {', '.join(match['recommendations'])}")
            print()

    finally:
        await intelligence_api.cleanup()


def calculate_match_score(
    analysis: NeighborhoodIntelligence,
    preferences: Dict[str, Any]
) -> int:
    """Calculate property match score based on lead preferences."""
    score = 0
    max_score = 0

    # Walkability scoring (0-30 points)
    if preferences.get("walkability_important"):
        max_score += 30
        if analysis.walkability and analysis.walkability.walk_score:
            min_score = preferences.get("min_walk_score", 0)
            if analysis.walkability.walk_score >= min_score:
                score += 30
            else:
                # Partial credit
                score += (analysis.walkability.walk_score / min_score) * 15

    # School quality scoring (0-35 points)
    if preferences.get("school_priority"):
        max_score += 35
        if analysis.schools and analysis.schools.average_rating:
            min_rating = preferences.get("min_school_rating", 0)
            if analysis.schools.average_rating >= min_rating:
                score += 35
            else:
                # Partial credit
                score += (analysis.schools.average_rating / min_rating) * 20

    # Commute scoring (0-25 points)
    max_score += 25
    if analysis.commute:
        max_commute = preferences.get("max_commute_minutes", 60)
        if analysis.commute.average_commute_time <= max_commute:
            score += 25
        else:
            # Partial credit
            ratio = max_commute / analysis.commute.average_commute_time
            score += ratio * 15

    # Transit requirement (0-10 points)
    if preferences.get("transit_required"):
        max_score += 10
        if analysis.commute and analysis.commute.public_transit_accessible:
            score += 10

    # Overall neighborhood score (0-10 points)
    max_score += 10
    if analysis.overall_score:
        score += (analysis.overall_score / 100) * 10

    # Normalize to 0-100 scale
    if max_score > 0:
        return int((score / max_score) * 100)
    return 0


def generate_recommendations(
    analysis: NeighborhoodIntelligence,
    preferences: Dict[str, Any]
) -> List[str]:
    """Generate personalized recommendations."""
    recommendations = []

    # Walkability recommendations
    if analysis.walkability:
        if analysis.walkability.walk_score >= 80:
            recommendations.append("Excellent walkability")
        elif analysis.walkability.walk_score < preferences.get("min_walk_score", 0):
            recommendations.append("Below desired walkability")

        if analysis.walkability.transit_score and analysis.walkability.transit_score >= 70:
            recommendations.append("Great public transit")

    # School recommendations
    if analysis.schools and preferences.get("school_priority"):
        if analysis.schools.average_rating >= 8:
            recommendations.append("Top-rated schools")
        elif analysis.schools.average_rating < preferences.get("min_school_rating", 0):
            recommendations.append("Consider school ratings")

    # Commute recommendations
    if analysis.commute:
        if analysis.commute.average_commute_time <= 20:
            recommendations.append("Short commute")
        elif analysis.commute.average_commute_time > preferences.get("max_commute_minutes", 60):
            recommendations.append("Long commute to work")

        if analysis.commute.employment_centers_within_30min >= 2:
            recommendations.append("Multiple job centers nearby")

    return recommendations or ["Good overall match"]


# ============================================================================
# Example 3: Cost Optimization with Cache Warming
# ============================================================================


async def example_cost_optimization():
    """Demonstrate cost optimization through cache warming."""
    print("\n=== Example 3: Cost Optimization with Cache Warming ===\n")

    # Initialize service
    intelligence_api = NeighborhoodIntelligenceAPI()
    await intelligence_api.initialize()

    try:
        # Popular locations to pre-cache
        popular_locations = [
            (30.2672, -97.7431),  # Downtown Austin
            (30.3922, -97.7278),  # North Austin
            (30.2241, -97.7693),  # South Congress
            (30.3077, -97.7531),  # University Area
            (30.2500, -97.7600),  # East Austin
        ]

        print(f"Warming cache for {len(popular_locations)} popular locations...")

        # Warm cache
        cached_count = await intelligence_api.warm_cache_for_locations(
            popular_locations
        )

        print(f"✓ Cached {cached_count} locations\n")

        # Get initial cost metrics
        initial_metrics = intelligence_api.get_cost_metrics()
        print("Initial Cost Metrics:")
        print(f"  API Calls: {initial_metrics['api_requests']}")
        print(f"  Estimated Cost: ${initial_metrics['estimated_cost_usd']:.2f}")
        print()

        # Simulate 100 property analyses (with cache hits)
        print("Simulating 100 property analyses...")

        for i in range(100):
            # Randomly select from popular locations (high cache hit rate)
            import random
            lat, lng = random.choice(popular_locations)

            # Add small random offset
            lat += random.uniform(-0.001, 0.001)
            lng += random.uniform(-0.001, 0.001)

            await intelligence_api.get_walkability_data(lat, lng)

        # Get final cost metrics
        final_metrics = intelligence_api.get_cost_metrics()

        print("\nFinal Cost Metrics:")
        print(f"  Total Requests: {final_metrics['total_requests']}")
        print(f"  API Requests: {final_metrics['api_requests']}")
        print(f"  Cached Requests: {final_metrics['cached_requests']}")
        print(f"  Cache Hit Rate: {final_metrics['cache_hit_rate']:.1f}%")
        print(f"  Estimated Cost: ${final_metrics['estimated_cost_usd']:.2f}")
        print()

        # Calculate savings
        if final_metrics['total_requests'] > 0:
            potential_cost = final_metrics['total_requests'] * 0.05  # If all were API calls
            actual_cost = final_metrics['estimated_cost_usd']
            savings = potential_cost - actual_cost

            print("Cost Savings:")
            print(f"  Potential Cost (no cache): ${potential_cost:.2f}")
            print(f"  Actual Cost (with cache): ${actual_cost:.2f}")
            print(f"  Total Savings: ${savings:.2f} ({(savings/potential_cost)*100:.1f}%)")

    finally:
        await intelligence_api.cleanup()


# ============================================================================
# Example 4: Detailed Walkability and School Analysis
# ============================================================================


async def example_detailed_analysis():
    """Detailed walkability and school analysis."""
    print("\n=== Example 4: Detailed Walkability and School Analysis ===\n")

    # Initialize service
    intelligence_api = NeighborhoodIntelligenceAPI()
    await intelligence_api.initialize()

    try:
        location = {
            "address": "789 Maple Dr, Austin, TX 78704",
            "lat": 30.2500,
            "lng": -97.7600
        }

        print(f"Analyzing: {location['address']}\n")

        # Get walkability data
        print("Fetching walkability data...")
        walkability = await intelligence_api.get_walkability_data(
            lat=location["lat"],
            lng=location["lng"],
            address=location["address"]
        )

        print("\nWalkability Analysis:")
        print(f"  Walk Score: {walkability.walk_score}/100")
        print(f"    {walkability.walk_description}")
        print()

        if walkability.transit_score:
            print(f"  Transit Score: {walkability.transit_score}/100")
            print(f"    {walkability.transit_description}")
            print()

        if walkability.bike_score:
            print(f"  Bike Score: {walkability.bike_score}/100")
            print(f"    {walkability.bike_description}")
            print()

        # Interpret scores
        print("Interpretation:")
        if walkability.walk_score >= 90:
            print("  • Daily errands do not require a car")
        elif walkability.walk_score >= 70:
            print("  • Most errands can be accomplished on foot")
        elif walkability.walk_score >= 50:
            print("  • Some errands can be accomplished on foot")
        else:
            print("  • Most errands require a car")
        print()

        # Get school ratings
        print("Fetching school ratings...")
        schools = await intelligence_api.get_school_ratings(
            address=location["address"],
            lat=location["lat"],
            lng=location["lng"],
            radius_miles=3.0
        )

        print("\nSchool Analysis:")
        print(f"  Average Rating: {schools.average_rating}/10")
        print()

        if schools.elementary_schools:
            print("  Elementary Schools:")
            for school in sorted(schools.elementary_schools, key=lambda s: s.rating or 0, reverse=True)[:3]:
                print(f"    • {school.name}: {school.rating}/10")
                if school.distance_miles:
                    print(f"      Distance: {school.distance_miles:.1f} miles")

        if schools.middle_schools:
            print("\n  Middle Schools:")
            for school in sorted(schools.middle_schools, key=lambda s: s.rating or 0, reverse=True)[:2]:
                print(f"    • {school.name}: {school.rating}/10")

        if schools.high_schools:
            print("\n  High Schools:")
            for school in sorted(schools.high_schools, key=lambda s: s.rating or 0, reverse=True)[:2]:
                print(f"    • {school.name}: {school.rating}/10")

    finally:
        await intelligence_api.cleanup()


# ============================================================================
# Example 5: Multi-Modal Commute Analysis
# ============================================================================


async def example_commute_analysis():
    """Multi-modal commute analysis."""
    print("\n=== Example 5: Multi-Modal Commute Analysis ===\n")

    # Initialize service
    intelligence_api = NeighborhoodIntelligenceAPI()
    await intelligence_api.initialize()

    try:
        home_location = {
            "address": "321 River Rd, Austin, TX 78701",
            "lat": 30.2672,
            "lng": -97.7431
        }

        destinations = [
            "Downtown Austin, TX",
            "Austin-Bergstrom Airport, TX",
            "Domain Shopping Center, Austin, TX"
        ]

        modes = [
            TransportMode.DRIVING,
            TransportMode.TRANSIT,
            TransportMode.BICYCLING
        ]

        print(f"From: {home_location['address']}")
        print(f"To: {', '.join(destinations)}")
        print(f"Modes: {', '.join(m.value for m in modes)}")
        print()

        # Calculate commute scores
        print("Calculating commute routes...")
        commute = await intelligence_api.calculate_commute_scores(
            from_address=home_location["address"],
            from_lat=home_location["lat"],
            from_lng=home_location["lng"],
            destinations=destinations,
            modes=modes
        )

        print("\nCommute Analysis:")
        print(f"  Overall Commute Score: {commute.overall_commute_score}/100")
        print(f"  Average Commute Time: {commute.average_commute_time} minutes")
        print(f"  Destinations within 30min: {commute.employment_centers_within_30min}")
        print(f"  Public Transit Accessible: {commute.public_transit_accessible}")
        print()

        # Show routes by destination
        print("Routes by Destination:")
        for destination in destinations:
            print(f"\n  {destination}:")
            dest_routes = [r for r in commute.routes if r.destination == destination]

            for route in dest_routes:
                duration = route.duration_in_traffic_minutes or route.duration_minutes
                print(f"    {route.mode.value}: {duration} min ({route.distance_miles:.1f} mi)")

        # Recommendations
        print("\nRecommendations:")
        if commute.average_commute_time <= 20:
            print("  ✓ Excellent location for commuters")
        elif commute.average_commute_time <= 30:
            print("  ✓ Good commute times to major employment centers")
        else:
            print("  ⚠ Consider commute times to work locations")

        if commute.public_transit_accessible:
            print("  ✓ Public transit available")

    finally:
        await intelligence_api.cleanup()


# ============================================================================
# Main Example Runner
# ============================================================================


async def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("Neighborhood Intelligence API - Usage Examples")
    print("="*70)

    # Run examples
    await example_basic_analysis()
    await example_property_matching()
    await example_cost_optimization()
    await example_detailed_analysis()
    await example_commute_analysis()

    print("\n" + "="*70)
    print("All examples completed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
