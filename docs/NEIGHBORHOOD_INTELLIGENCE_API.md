# Neighborhood Intelligence API Integration

**Status**: ✅ Production Ready
**Phase**: 3 - Enhanced Property Matching
**Business Impact**: Contributes to 88% → 93%+ property match satisfaction
**Last Updated**: January 2026

## Overview

The Neighborhood Intelligence API Integration Service provides comprehensive multimodal property intelligence through integration with multiple specialized APIs. This service powers enhanced property matching by analyzing walkability, school quality, commute times, and neighborhood characteristics.

### Key Capabilities

1. **Walk Score Integration**
   - Walkability scores (0-100)
   - Transit accessibility scores
   - Bike infrastructure scores
   - Nearby amenities analysis

2. **GreatSchools Integration**
   - School ratings (1-10 scale)
   - Elementary, middle, and high school data
   - District information and boundaries
   - School quality metrics

3. **Commute Optimization**
   - Multi-destination route analysis
   - Multiple transport modes (driving, transit, walking, biking)
   - Traffic pattern consideration
   - Employment center accessibility

4. **Cost Optimization**
   - 24-hour intelligent caching
   - >85% cache hit rate target
   - Strategic API quota management
   - Real-time cost tracking

## Architecture

### Service Design

```
NeighborhoodIntelligenceAPI
├── Walk Score API Client
│   ├── Walkability scoring
│   ├── Transit score analysis
│   └── Bike score calculation
│
├── GreatSchools API Client
│   ├── School ratings retrieval
│   ├── District boundary queries
│   └── Quality metrics aggregation
│
├── Google Maps / Mapbox Client
│   ├── Directions API integration
│   ├── Multi-modal route planning
│   └── Traffic data integration
│
├── Intelligent Caching Layer
│   ├── Redis-backed 24-hour cache
│   ├── Location-based cache keys
│   └── Automatic cache warming
│
└── Cost Optimization Engine
    ├── API call tracking
    ├── Cost estimation
    └── Quota management
```

### Data Flow

```
Property Analysis Request
    ↓
Cache Check (24-hour TTL)
    ↓ (miss)
Parallel API Calls
    ├── Walk Score API
    ├── GreatSchools API
    └── Google Maps API
    ↓
Data Aggregation
    ↓
Composite Score Calculation
    ↓
Cache Storage
    ↓
Response (< 200ms)
```

## Data Models

### WalkabilityData

Comprehensive walkability analysis for property location.

```python
@dataclass
class WalkabilityData:
    address: str
    lat: float
    lng: float
    walk_score: Optional[int] = None  # 0-100
    walk_description: Optional[str] = None
    transit_score: Optional[int] = None  # 0-100
    transit_description: Optional[str] = None
    bike_score: Optional[int] = None  # 0-100
    bike_description: Optional[str] = None
    nearby_amenities: List[Dict[str, Any]] = field(default_factory=list)
```

**Score Ranges**:
- **90-100**: Walker's Paradise (daily errands don't require a car)
- **70-89**: Very Walkable (most errands on foot)
- **50-69**: Somewhat Walkable (some errands on foot)
- **25-49**: Car-Dependent (most errands require a car)
- **0-24**: Car-Dependent (almost all errands require a car)

### SchoolRatings

Comprehensive school quality data for property area.

```python
@dataclass
class SchoolRatings:
    address: str
    elementary_schools: List[SchoolData] = field(default_factory=list)
    middle_schools: List[SchoolData] = field(default_factory=list)
    high_schools: List[SchoolData] = field(default_factory=list)
    district_name: Optional[str] = None
    district_rating: Optional[int] = None
    average_rating: Optional[float] = None
```

**Individual School Data**:
```python
@dataclass
class SchoolData:
    school_id: str
    name: str
    school_type: SchoolType  # PUBLIC, PRIVATE, CHARTER
    level: SchoolLevel  # ELEMENTARY, MIDDLE, HIGH
    rating: Optional[int] = None  # 1-10
    district: Optional[str] = None
    distance_miles: Optional[float] = None
    enrollment: Optional[int] = None
    student_teacher_ratio: Optional[float] = None
```

### CommuteScores

Multi-destination commute analysis with multiple transport modes.

```python
@dataclass
class CommuteScores:
    from_address: str
    routes: List[CommuteData] = field(default_factory=list)
    overall_commute_score: Optional[int] = None  # 0-100
    average_commute_time: Optional[int] = None  # Minutes
    employment_centers_within_30min: int = 0
    public_transit_accessible: bool = False
```

**Route Data**:
```python
@dataclass
class CommuteData:
    destination: str
    mode: TransportMode  # DRIVING, TRANSIT, WALKING, BICYCLING
    distance_miles: float
    duration_minutes: int
    duration_in_traffic_minutes: Optional[int] = None
```

### NeighborhoodIntelligence

Composite analysis combining all data sources.

```python
@dataclass
class NeighborhoodIntelligence:
    property_address: str
    location: LocationData
    walkability: Optional[WalkabilityData] = None
    schools: Optional[SchoolRatings] = None
    commute: Optional[CommuteScores] = None
    overall_score: Optional[int] = None  # 0-100 composite
```

**Overall Score Calculation**:
- **30%** - Walk Score
- **35%** - School Ratings
- **25%** - Commute Score
- **10%** - Safety (inverse crime index)

## Usage Examples

### Basic Neighborhood Analysis

```python
from ghl_real_estate_ai.services.neighborhood_intelligence_api import (
    NeighborhoodIntelligenceAPI
)

# Initialize service
intelligence_api = NeighborhoodIntelligenceAPI()
await intelligence_api.initialize()

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

print(f"Overall Score: {analysis.overall_score}/100")
print(f"Walk Score: {analysis.walkability.walk_score}")
print(f"Average School Rating: {analysis.schools.average_rating}")
print(f"Average Commute: {analysis.commute.average_commute_time} min")
```

### Walkability Analysis Only

```python
# Get walkability data
walkability = await intelligence_api.get_walkability_data(
    lat=30.2672,
    lng=-97.7431,
    address="123 Main St, Austin, TX 78701"
)

print(f"Walk Score: {walkability.walk_score} - {walkability.walk_description}")
print(f"Transit Score: {walkability.transit_score}")
print(f"Bike Score: {walkability.bike_score}")
```

### School Ratings Analysis

```python
# Get school ratings
schools = await intelligence_api.get_school_ratings(
    address="123 Main St, Austin, TX 78701",
    lat=30.2672,
    lng=-97.7431,
    radius_miles=3.0
)

print(f"Average Rating: {schools.average_rating}/10")
print(f"Elementary Schools: {len(schools.elementary_schools)}")
print(f"High Schools: {len(schools.high_schools)}")

# Show best school
if schools.elementary_schools:
    best_school = max(schools.elementary_schools, key=lambda s: s.rating or 0)
    print(f"Best Elementary: {best_school.name} ({best_school.rating}/10)")
```

### Commute Optimization

```python
# Calculate commute scores
commute = await intelligence_api.calculate_commute_scores(
    from_address="123 Main St, Austin, TX 78701",
    from_lat=30.2672,
    from_lng=-97.7431,
    destinations=["Downtown Austin", "Airport", "Tech Ridge"],
    modes=[TransportMode.DRIVING, TransportMode.TRANSIT]
)

print(f"Overall Commute Score: {commute.overall_commute_score}/100")
print(f"Average Commute Time: {commute.average_commute_time} min")
print(f"Destinations within 30min: {commute.employment_centers_within_30min}")
print(f"Transit Accessible: {commute.public_transit_accessible}")

# Show routes
for route in commute.routes:
    print(f"{route.destination} ({route.mode.value}): {route.duration_minutes} min")
```

### Property Matching Integration

```python
async def match_property_to_lead(property_data, lead_preferences):
    """Match property using neighborhood intelligence."""

    # Get comprehensive analysis
    analysis = await intelligence_api.analyze_neighborhood(
        property_address=property_data["address"],
        lat=property_data["lat"],
        lng=property_data["lng"],
        city=property_data["city"],
        state=property_data["state"],
        zipcode=property_data["zipcode"],
        commute_destinations=lead_preferences.get("work_locations", [])
    )

    # Calculate match score based on lead preferences
    match_score = 0

    # Walkability preference
    if lead_preferences.get("walkability_important") and analysis.walkability:
        if analysis.walkability.walk_score >= 70:
            match_score += 20

    # School quality preference
    if lead_preferences.get("school_priority") and analysis.schools:
        if analysis.schools.average_rating >= 8:
            match_score += 30

    # Commute preference
    if analysis.commute:
        if analysis.commute.average_commute_time <= 30:
            match_score += 25

    # Overall neighborhood score
    match_score += (analysis.overall_score or 0) * 0.25

    return {
        "property": property_data,
        "match_score": min(100, match_score),
        "analysis": analysis,
        "recommendations": generate_recommendations(analysis, lead_preferences)
    }
```

## Caching Strategy

### 24-Hour Intelligent Caching

**Cache Key Structure**:
```
neighborhood_intelligence:{type}:{location_hash}
```

**Cache Types**:
- `walkability` - Walk/Transit/Bike scores
- `schools` - School ratings and data
- `commute` - Route and commute analysis
- `full_analysis` - Complete neighborhood analysis

**Cache TTL**:
- Default: 24 hours (86,400 seconds)
- Walkability: 24 hours (stable data)
- Schools: 24 hours (annual updates)
- Commute: 24 hours (traffic patterns stable daily)

### Cache Warming

Pre-cache popular locations to improve performance:

```python
# Warm cache for top locations
popular_locations = [
    (30.2672, -97.7431),  # Downtown Austin
    (30.3922, -97.7278),  # North Austin
    (30.2241, -97.7693),  # South Congress
]

cached_count = await intelligence_api.warm_cache_for_locations(
    popular_locations
)

print(f"Warmed cache for {cached_count} locations")
```

### Cache Invalidation

Invalidate cache when data needs refresh:

```python
# Invalidate specific location
deleted_count = await intelligence_api.invalidate_cache_for_location(
    lat=30.2672,
    lng=-97.7431
)

print(f"Invalidated {deleted_count} cache entries")
```

## Cost Optimization

### API Cost Tracking

Track API costs for optimization:

```python
# Get cost metrics
metrics = intelligence_api.get_cost_metrics()

print(f"Total Requests: {metrics['total_requests']}")
print(f"Cache Hit Rate: {metrics['cache_hit_rate']}%")
print(f"Estimated Cost: ${metrics['estimated_cost_usd']:.2f}")
print(f"Walk Score Calls: {metrics['walk_score_calls']}")
print(f"Google Maps Calls: {metrics['google_maps_calls']}")
```

**API Cost Estimates** (per call):
- Walk Score: ~$0.05
- GreatSchools: Free tier
- Google Maps: ~$0.005
- Mapbox: ~$0.001

### Optimization Strategies

1. **Aggressive Caching**
   - 24-hour TTL for all data
   - Location-based cache keys
   - Pre-warming for popular areas

2. **Batch Requests**
   - Parallel API calls for speed
   - Minimize redundant requests
   - Smart retry logic

3. **Fallback Data**
   - Cached stale data when API fails
   - Demo data for development
   - Graceful degradation

4. **Quota Management**
   - Rate limiting per API
   - Usage monitoring
   - Alert on quota thresholds

## Performance Targets

### Response Times

- **API Response**: < 200ms (95th percentile)
- **Cached Response**: < 50ms
- **Full Analysis**: < 500ms (parallel APIs)
- **Cache Miss**: < 1s (with 3 API calls)

### Cache Performance

- **Hit Rate**: > 85% (production target)
- **Storage**: ~1KB per location
- **TTL**: 24 hours (86,400s)
- **Eviction**: LRU policy

### Cost Efficiency

- **Daily API Budget**: < $50/day (5,000 properties)
- **Cost per Analysis**: < $0.10
- **Cache Savings**: 85%+ (compared to no cache)
- **Monthly Cost**: ~$1,500 (50,000 analyses)

## Configuration

### Environment Variables

```bash
# Walk Score API
WALK_SCORE_API_KEY=your_walkscore_api_key

# GreatSchools API
GREATSCHOOLS_API_KEY=your_greatschools_api_key

# Google Maps API
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# Mapbox API (alternative to Google Maps)
MAPBOX_API_KEY=your_mapbox_api_key

# Census API (demographics)
CENSUS_API_KEY=your_census_api_key

# Redis (caching)
REDIS_URL=redis://localhost:6379/0

# Performance Tuning
NEIGHBORHOOD_CACHE_TTL=86400  # 24 hours
NEIGHBORHOOD_PARALLEL_REQUESTS=3
```

### Service Configuration

```python
# config/neighborhood_intelligence.py

NEIGHBORHOOD_CONFIG = {
    # API Configuration
    "walk_score_timeout": 10,  # seconds
    "greatschools_timeout": 10,
    "google_maps_timeout": 15,

    # Cache Configuration
    "cache_ttl": 86400,  # 24 hours
    "cache_prefix": "neighborhood_intelligence",

    # Search Radii
    "school_search_radius_miles": 5.0,
    "amenity_search_radius_miles": 2.0,

    # Score Weights
    "overall_score_weights": {
        "walkability": 0.30,
        "schools": 0.35,
        "commute": 0.25,
        "safety": 0.10
    },

    # Rate Limits
    "walk_score_concurrent": 10,
    "greatschools_concurrent": 5,
    "google_maps_concurrent": 20
}
```

## Error Handling

### Fallback Strategies

1. **API Unavailable**
   ```python
   # Returns fallback data with data_source="fallback"
   walkability = await intelligence_api.get_walkability_data(lat, lng)
   if walkability.data_source == "fallback":
       logger.warning("Using fallback walkability data")
   ```

2. **Timeout Errors**
   ```python
   # Automatic retry with exponential backoff
   # Falls back to cached/demo data after 3 attempts
   ```

3. **Rate Limiting**
   ```python
   # Semaphore-based rate limiting per API
   # Queues requests when limit reached
   ```

4. **Malformed Responses**
   ```python
   # Validates response structure
   # Returns None for invalid fields
   # Logs error for debugging
   ```

## Monitoring and Alerting

### Health Checks

```python
# Service health check
health = await intelligence_api.check_health()

if health["status"] != "healthy":
    logger.error(f"Service unhealthy: {health}")
    alert_ops_team(health)
```

### Key Metrics

Monitor these metrics in production:

1. **API Performance**
   - Response time (p50, p95, p99)
   - Error rate per API
   - Timeout rate

2. **Cache Performance**
   - Hit rate (target > 85%)
   - Miss rate
   - Eviction rate
   - Memory usage

3. **Cost Metrics**
   - API calls per hour
   - Estimated daily cost
   - Cost per analysis

4. **Business Metrics**
   - Properties analyzed per day
   - Average overall score
   - Score distribution

## Integration with Property Matching

### Enhanced Matching Models

The Neighborhood Intelligence API integrates with property matching models:

```python
# Integration in enhanced_matching_models.py

async def calculate_neighborhood_match_score(
    property_data: Dict,
    lead_preferences: Dict
) -> float:
    """Calculate neighborhood match score."""

    analysis = await neighborhood_api.analyze_neighborhood(
        property_address=property_data["address"],
        lat=property_data["lat"],
        lng=property_data["lng"],
        city=property_data["city"],
        state=property_data["state"],
        zipcode=property_data["zipcode"],
        commute_destinations=lead_preferences.get("work_locations", [])
    )

    # Weight factors based on lead preferences
    weights = {
        "walkability": lead_preferences.get("walkability_weight", 0.3),
        "schools": lead_preferences.get("school_weight", 0.35),
        "commute": lead_preferences.get("commute_weight", 0.25),
        "safety": lead_preferences.get("safety_weight", 0.10)
    }

    # Calculate weighted score
    score = 0

    if analysis.walkability and analysis.walkability.walk_score:
        score += (analysis.walkability.walk_score / 100) * weights["walkability"]

    if analysis.schools and analysis.schools.average_rating:
        score += (analysis.schools.average_rating / 10) * weights["schools"]

    if analysis.commute and analysis.commute.overall_commute_score:
        score += (analysis.commute.overall_commute_score / 100) * weights["commute"]

    return score * 100  # 0-100 scale
```

## Testing

### Unit Tests

Run comprehensive unit tests:

```bash
pytest ghl_real_estate_ai/tests/unit/test_neighborhood_intelligence_api.py -v
```

**Test Coverage**:
- Data model serialization/deserialization
- API integration and error handling
- Caching logic and cache key generation
- Cost tracking and metrics
- Parallel API coordination
- Fallback strategies

### Integration Tests

```python
@pytest.mark.integration
async def test_full_neighborhood_analysis_integration():
    """Test complete workflow with real APIs."""

    service = NeighborhoodIntelligenceAPI()
    await service.initialize()

    analysis = await service.analyze_neighborhood(
        property_address="123 Main St, Austin, TX 78701",
        lat=30.2672,
        lng=-97.7431,
        city="Austin",
        state="TX",
        zipcode="78701",
        commute_destinations=["Downtown Austin"]
    )

    assert analysis.overall_score is not None
    assert analysis.walkability is not None
    assert analysis.schools is not None

    await service.cleanup()
```

## Future Enhancements

### Phase 4 Roadmap

1. **Advanced Demographics**
   - Household income distribution
   - Age demographics
   - Education levels
   - Employment sectors

2. **Crime Data Integration**
   - Crime index by category
   - Historical trend analysis
   - Safety scoring improvements

3. **Amenities Analysis**
   - Grocery stores
   - Restaurants and entertainment
   - Parks and recreation
   - Healthcare facilities

4. **Predictive Analytics**
   - Neighborhood appreciation forecasts
   - School rating trends
   - Transit development plans
   - Investment potential scoring

5. **Custom Scoring Models**
   - Lead-specific weighting
   - Demographic-based scoring
   - Lifestyle matching algorithms

## Business Impact

### Property Match Satisfaction

- **Current**: 88% satisfaction
- **Target**: 93%+ with neighborhood intelligence
- **Improvement**: +5 percentage points

### Key Value Drivers

1. **Better Matches**
   - Comprehensive neighborhood data
   - Multi-factor scoring
   - Personalized recommendations

2. **Faster Decisions**
   - All data in single analysis
   - Pre-cached popular locations
   - <500ms response times

3. **Cost Efficiency**
   - 85%+ cache hit rate
   - Strategic API usage
   - Optimized quota management

4. **Agent Productivity**
   - Automated neighborhood research
   - Data-driven recommendations
   - Reduced manual analysis time

## Support and Troubleshooting

### Common Issues

1. **High API Costs**
   - Check cache hit rate (should be >85%)
   - Review cache TTL settings
   - Verify cache warming strategy

2. **Slow Responses**
   - Check Redis connection
   - Verify parallel API calls
   - Review API timeout settings

3. **Missing Data**
   - Verify API keys configured
   - Check API quota limits
   - Review fallback data usage

### Debug Mode

Enable detailed logging:

```python
import logging

logging.getLogger("ghl_real_estate_ai.services.neighborhood_intelligence_api").setLevel(
    logging.DEBUG
)
```

---

**Documentation Version**: 1.0.0
**Service Version**: 1.0.0
**Last Updated**: January 2026
**Maintained By**: EnterpriseHub Engineering Team
