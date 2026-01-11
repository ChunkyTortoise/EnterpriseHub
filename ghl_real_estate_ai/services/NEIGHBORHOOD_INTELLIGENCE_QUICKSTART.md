# Neighborhood Intelligence API - Quick Start Guide

Get up and running with the Neighborhood Intelligence API in 5 minutes.

## Installation and Setup

### 1. Install Dependencies

```bash
pip install aiohttp redis
```

### 2. Configure API Keys

Set environment variables for API access:

```bash
# Required APIs
export WALK_SCORE_API_KEY=your_walkscore_key
export GOOGLE_MAPS_API_KEY=your_google_maps_key

# Optional APIs
export GREATSCHOOLS_API_KEY=your_greatschools_key
export MAPBOX_API_KEY=your_mapbox_key

# Redis (for caching)
export REDIS_URL=redis://localhost:6379/0
```

### 3. Initialize Redis

Ensure Redis is running for caching:

```bash
redis-server
```

## Basic Usage

### Simple Property Analysis

```python
import asyncio
from ghl_real_estate_ai.services.neighborhood_intelligence_api import (
    NeighborhoodIntelligenceAPI
)

async def analyze_property():
    # Initialize service
    api = NeighborhoodIntelligenceAPI()
    await api.initialize()

    # Analyze neighborhood
    analysis = await api.analyze_neighborhood(
        property_address="123 Main St, Austin, TX 78701",
        lat=30.2672,
        lng=-97.7431,
        city="Austin",
        state="TX",
        zipcode="78701",
        commute_destinations=["Downtown Austin"]
    )

    # Display results
    print(f"Overall Score: {analysis.overall_score}/100")
    print(f"Walk Score: {analysis.walkability.walk_score}")
    print(f"School Rating: {analysis.schools.average_rating}")
    print(f"Avg Commute: {analysis.commute.average_commute_time} min")

    # Cleanup
    await api.cleanup()

# Run
asyncio.run(analyze_property())
```

## Common Use Cases

### 1. Property Matching

```python
async def match_properties_to_lead(lead_preferences, properties):
    api = NeighborhoodIntelligenceAPI()
    await api.initialize()

    matches = []
    for prop in properties:
        analysis = await api.analyze_neighborhood(
            property_address=prop["address"],
            lat=prop["lat"],
            lng=prop["lng"],
            city=prop["city"],
            state=prop["state"],
            zipcode=prop["zipcode"],
            commute_destinations=lead_preferences["work_locations"]
        )

        # Calculate match score
        score = 0
        if analysis.walkability.walk_score >= lead_preferences["min_walk_score"]:
            score += 30
        if analysis.schools.average_rating >= lead_preferences["min_school_rating"]:
            score += 40
        if analysis.commute.average_commute_time <= lead_preferences["max_commute"]:
            score += 30

        matches.append({"property": prop, "score": score, "analysis": analysis})

    # Sort by score
    matches.sort(key=lambda x: x["score"], reverse=True)

    await api.cleanup()
    return matches
```

### 2. Walkability Only

```python
async def check_walkability(lat, lng):
    api = NeighborhoodIntelligenceAPI()
    await api.initialize()

    walkability = await api.get_walkability_data(lat, lng)

    print(f"Walk Score: {walkability.walk_score}/100")
    print(f"Description: {walkability.walk_description}")

    await api.cleanup()
```

### 3. School Research

```python
async def research_schools(address, lat, lng):
    api = NeighborhoodIntelligenceAPI()
    await api.initialize()

    schools = await api.get_school_ratings(address, lat, lng, radius_miles=5.0)

    print(f"Average Rating: {schools.average_rating}/10")

    # Show best elementary school
    if schools.elementary_schools:
        best = max(schools.elementary_schools, key=lambda s: s.rating or 0)
        print(f"Best Elementary: {best.name} ({best.rating}/10)")

    await api.cleanup()
```

### 4. Commute Analysis

```python
async def analyze_commute(from_address, from_lat, from_lng, work_locations):
    api = NeighborhoodIntelligenceAPI()
    await api.initialize()

    commute = await api.calculate_commute_scores(
        from_address=from_address,
        from_lat=from_lat,
        from_lng=from_lng,
        destinations=work_locations
    )

    print(f"Commute Score: {commute.overall_commute_score}/100")
    print(f"Average Time: {commute.average_commute_time} min")

    for route in commute.routes:
        print(f"{route.destination}: {route.duration_minutes} min")

    await api.cleanup()
```

## Performance Optimization

### Cache Warming

Pre-cache popular locations for better performance:

```python
async def warm_cache():
    api = NeighborhoodIntelligenceAPI()
    await api.initialize()

    # Popular locations
    locations = [
        (30.2672, -97.7431),  # Downtown
        (30.3922, -97.7278),  # North
        (30.2241, -97.7693),  # South
    ]

    cached_count = await api.warm_cache_for_locations(locations)
    print(f"Cached {cached_count} locations")

    await api.cleanup()
```

### Monitor Costs

Track API costs and cache performance:

```python
async def check_costs():
    api = NeighborhoodIntelligenceAPI()
    await api.initialize()

    # Use the API...
    # ...

    # Get cost metrics
    metrics = api.get_cost_metrics()
    print(f"Cache Hit Rate: {metrics['cache_hit_rate']}%")
    print(f"Total Cost: ${metrics['estimated_cost_usd']:.2f}")

    await api.cleanup()
```

## Error Handling

The service includes automatic fallbacks:

```python
async def safe_analysis(address, lat, lng):
    api = NeighborhoodIntelligenceAPI()
    await api.initialize()

    try:
        analysis = await api.analyze_neighborhood(
            property_address=address,
            lat=lat,
            lng=lng,
            city="City",
            state="ST",
            zipcode="00000"
        )

        # Check if data is from fallback
        if analysis.walkability.data_source == "fallback":
            print("⚠ Using fallback walkability data")

        return analysis

    except Exception as e:
        print(f"Error: {e}")
        return None

    finally:
        await api.cleanup()
```

## Testing

### Run Unit Tests

```bash
pytest ghl_real_estate_ai/tests/unit/test_neighborhood_intelligence_api.py -v
```

### Run Integration Tests

```bash
# Requires real API keys
pytest ghl_real_estate_ai/tests/unit/test_neighborhood_intelligence_api.py -v -m integration
```

## Next Steps

1. **Read Full Documentation**: See `docs/NEIGHBORHOOD_INTELLIGENCE_API.md`
2. **Review Examples**: Check `examples/neighborhood_intelligence_usage.py`
3. **Configure Production**: Set up proper API keys and Redis
4. **Monitor Performance**: Track cache hit rates and costs
5. **Integrate with Property Matching**: Use in enhanced matching models

## Support

- **Documentation**: `/docs/NEIGHBORHOOD_INTELLIGENCE_API.md`
- **Examples**: `/examples/neighborhood_intelligence_usage.py`
- **Tests**: `/tests/unit/test_neighborhood_intelligence_api.py`
- **Service Code**: `/services/neighborhood_intelligence_api.py`

## Quick Reference

### Data Models

- `WalkabilityData` - Walk/Transit/Bike scores
- `SchoolRatings` - School quality data
- `CommuteScores` - Route analysis
- `NeighborhoodIntelligence` - Complete analysis

### Key Methods

- `analyze_neighborhood()` - Full analysis
- `get_walkability_data()` - Walkability only
- `get_school_ratings()` - Schools only
- `calculate_commute_scores()` - Commute only
- `get_cost_metrics()` - Cost tracking
- `warm_cache_for_locations()` - Cache warming

### Score Ranges

- **Walk Score**: 0-100 (higher = more walkable)
- **School Rating**: 1-10 (higher = better quality)
- **Commute Score**: 0-100 (higher = shorter commutes)
- **Overall Score**: 0-100 (weighted composite)
