# Phase 3 Neighborhood Intelligence Integration Guide

**Integration Target**: Enhanced Property Matching Models
**Service**: Neighborhood Intelligence API
**Phase**: 3 - Multimodal Property Intelligence
**Status**: Production Ready

## Overview

This guide explains how the Neighborhood Intelligence API integrates with the Phase 3 Enhanced Property Matching system to deliver 88% → 93%+ property match satisfaction.

## Architecture Integration

```
Phase 3 Enhanced Property Matching
├── Enhanced Matching Models (ML)
│   ├── Behavioral Learning Integration
│   ├── Multi-Factor Scoring Engine
│   └── Neighborhood Intelligence API ← NEW
│       ├── Walk Score Integration
│       ├── GreatSchools Integration
│       └── Commute Optimization
│
├── Property Data Sources
│   ├── Zillow Integration Service
│   ├── Redfin Integration Service
│   └── Neighborhood Intelligence API ← NEW
│
└── Lead Intelligence System
    ├── Preference Tracking
    ├── Behavioral Analysis
    └── Neighborhood Preferences ← NEW
```

## Integration Points

### 1. Enhanced Matching Models Integration

**File**: `/ghl_real_estate_ai/services/enhanced_matching_models.py`

Add neighborhood intelligence to property scoring:

```python
from ghl_real_estate_ai.services.neighborhood_intelligence_api import (
    NeighborhoodIntelligenceAPI
)

class EnhancedPropertyMatchingEngine:
    """Enhanced property matching with neighborhood intelligence."""

    def __init__(self):
        self.ml_model = self.load_model()
        self.neighborhood_api = NeighborhoodIntelligenceAPI()

    async def initialize(self):
        """Initialize all services."""
        await self.neighborhood_api.initialize()

    async def calculate_property_score(
        self,
        property_data: Dict,
        lead_preferences: Dict
    ) -> PropertyMatchScore:
        """Calculate comprehensive property match score."""

        # Get neighborhood intelligence
        neighborhood_analysis = await self.neighborhood_api.analyze_neighborhood(
            property_address=property_data["address"],
            lat=property_data["lat"],
            lng=property_data["lng"],
            city=property_data["city"],
            state=property_data["state"],
            zipcode=property_data["zipcode"],
            commute_destinations=lead_preferences.get("work_locations", [])
        )

        # Calculate ML-based property score
        ml_score = self.ml_model.predict(property_data, lead_preferences)

        # Calculate neighborhood match score
        neighborhood_score = self._calculate_neighborhood_score(
            neighborhood_analysis,
            lead_preferences
        )

        # Combine scores (weighted)
        composite_score = (
            ml_score * 0.60 +  # ML model (60%)
            neighborhood_score * 0.40  # Neighborhood (40%)
        )

        return PropertyMatchScore(
            overall_score=composite_score,
            ml_score=ml_score,
            neighborhood_score=neighborhood_score,
            neighborhood_analysis=neighborhood_analysis,
            factors=self._extract_score_factors(
                property_data,
                neighborhood_analysis,
                lead_preferences
            )
        )

    def _calculate_neighborhood_score(
        self,
        analysis: NeighborhoodIntelligence,
        preferences: Dict
    ) -> float:
        """Calculate neighborhood match score based on preferences."""

        score = 0
        weights = self._get_preference_weights(preferences)

        # Walkability scoring
        if analysis.walkability and weights.get("walkability", 0) > 0:
            walk_score = analysis.walkability.walk_score or 0
            min_required = preferences.get("min_walk_score", 0)

            if walk_score >= min_required:
                score += weights["walkability"] * 100
            else:
                # Partial credit
                score += weights["walkability"] * (walk_score / min_required) * 50

        # School quality scoring
        if analysis.schools and weights.get("schools", 0) > 0:
            school_rating = analysis.schools.average_rating or 0
            min_required = preferences.get("min_school_rating", 0)

            if school_rating >= min_required:
                score += weights["schools"] * 100
            else:
                # Partial credit
                score += weights["schools"] * (school_rating / min_required) * 50

        # Commute scoring
        if analysis.commute and weights.get("commute", 0) > 0:
            avg_commute = analysis.commute.average_commute_time or 99
            max_allowed = preferences.get("max_commute_minutes", 60)

            if avg_commute <= max_allowed:
                score += weights["commute"] * 100
            else:
                # Partial credit
                ratio = max_allowed / avg_commute
                score += weights["commute"] * ratio * 50

        # Normalize to 0-100
        total_weight = sum(weights.values())
        if total_weight > 0:
            return score / total_weight

        return 0

    def _get_preference_weights(self, preferences: Dict) -> Dict[str, float]:
        """Extract and normalize preference weights."""

        raw_weights = {
            "walkability": preferences.get("walkability_weight", 0.30),
            "schools": preferences.get("school_weight", 0.35),
            "commute": preferences.get("commute_weight", 0.25),
            "safety": preferences.get("safety_weight", 0.10)
        }

        # Normalize to sum to 1.0
        total = sum(raw_weights.values())
        return {k: v / total for k, v in raw_weights.items()}

    def _extract_score_factors(
        self,
        property_data: Dict,
        analysis: NeighborhoodIntelligence,
        preferences: Dict
    ) -> List[ScoreFactor]:
        """Extract individual scoring factors for explainability."""

        factors = []

        # Property features
        factors.append(ScoreFactor(
            name="Property Features",
            score=self._calculate_property_features_score(property_data, preferences),
            weight=0.30,
            details={
                "price": property_data.get("price"),
                "bedrooms": property_data.get("bedrooms"),
                "bathrooms": property_data.get("bathrooms")
            }
        ))

        # Walkability
        if analysis.walkability:
            factors.append(ScoreFactor(
                name="Walkability",
                score=analysis.walkability.walk_score,
                weight=0.15,
                details={
                    "walk_score": analysis.walkability.walk_score,
                    "transit_score": analysis.walkability.transit_score,
                    "description": analysis.walkability.walk_description
                }
            ))

        # Schools
        if analysis.schools:
            factors.append(ScoreFactor(
                name="School Quality",
                score=(analysis.schools.average_rating or 0) * 10,
                weight=0.20,
                details={
                    "average_rating": analysis.schools.average_rating,
                    "elementary_count": len(analysis.schools.elementary_schools),
                    "high_schools_count": len(analysis.schools.high_schools)
                }
            ))

        # Commute
        if analysis.commute:
            commute_score = 100 - min(analysis.commute.average_commute_time or 60, 100)
            factors.append(ScoreFactor(
                name="Commute",
                score=commute_score,
                weight=0.15,
                details={
                    "average_time": analysis.commute.average_commute_time,
                    "destinations_30min": analysis.commute.employment_centers_within_30min,
                    "transit_accessible": analysis.commute.public_transit_accessible
                }
            ))

        # Overall neighborhood
        factors.append(ScoreFactor(
            name="Overall Neighborhood",
            score=analysis.overall_score or 0,
            weight=0.20,
            details={
                "composite_score": analysis.overall_score
            }
        ))

        return factors
```

### 2. Lead Preference Tracking

**File**: `/ghl_real_estate_ai/services/behavioral_learning_engine.py`

Track neighborhood preferences:

```python
async def track_neighborhood_preference(
    user_id: str,
    property_viewed: Dict,
    neighborhood_analysis: NeighborhoodIntelligence,
    interaction_type: str,  # "view", "save", "inquiry", "reject"
    duration_seconds: int
):
    """Track neighborhood preferences from user interactions."""

    interaction = UserInteraction(
        user_id=user_id,
        action=f"neighborhood_{interaction_type}",
        context={
            # Property context
            "property_id": property_viewed["id"],
            "property_price": property_viewed["price"],

            # Neighborhood features
            "walk_score": neighborhood_analysis.walkability.walk_score if neighborhood_analysis.walkability else None,
            "transit_score": neighborhood_analysis.walkability.transit_score if neighborhood_analysis.walkability else None,
            "school_rating": neighborhood_analysis.schools.average_rating if neighborhood_analysis.schools else None,
            "commute_time": neighborhood_analysis.commute.average_commute_time if neighborhood_analysis.commute else None,
            "overall_neighborhood_score": neighborhood_analysis.overall_score,

            # Interaction metrics
            "duration_seconds": duration_seconds,
            "interaction_type": interaction_type
        },
        outcome=interaction_type,  # "save", "inquiry", etc.
        timestamp=datetime.utcnow()
    )

    await behavioral_engine.record_interaction(interaction)

    # Update learned preferences
    if interaction_type in ["save", "inquiry"]:
        await update_neighborhood_preferences(user_id, neighborhood_analysis)


async def update_neighborhood_preferences(
    user_id: str,
    analysis: NeighborhoodIntelligence
):
    """Update learned neighborhood preferences."""

    preferences = await get_user_preferences(user_id)

    # Learn walkability preference
    if analysis.walkability and analysis.walkability.walk_score:
        preferences["preferred_walk_score"] = max(
            preferences.get("preferred_walk_score", 0),
            analysis.walkability.walk_score
        )

    # Learn school quality preference
    if analysis.schools and analysis.schools.average_rating:
        preferences["preferred_school_rating"] = max(
            preferences.get("preferred_school_rating", 0),
            analysis.schools.average_rating
        )

    # Learn commute preference
    if analysis.commute and analysis.commute.average_commute_time:
        current_max = preferences.get("max_acceptable_commute", 60)
        # Only update if this property was positively engaged with
        if analysis.commute.average_commute_time < current_max:
            preferences["max_acceptable_commute"] = analysis.commute.average_commute_time

    await save_user_preferences(user_id, preferences)
```

### 3. Property Search Filter Integration

**File**: `/ghl_real_estate_ai/services/property_search_service.py`

Add neighborhood filters to search:

```python
async def search_properties_with_neighborhood_filters(
    user_preferences: Dict,
    search_criteria: Dict
) -> List[PropertyMatch]:
    """Search properties with neighborhood intelligence filters."""

    # Get base property results
    properties = await search_properties(search_criteria)

    # Filter by neighborhood criteria
    filtered_properties = []

    for property in properties:
        # Get neighborhood analysis (cached if available)
        analysis = await neighborhood_api.analyze_neighborhood(
            property_address=property["address"],
            lat=property["lat"],
            lng=property["lng"],
            city=property["city"],
            state=property["state"],
            zipcode=property["zipcode"],
            commute_destinations=user_preferences.get("work_locations", [])
        )

        # Apply filters
        if not passes_neighborhood_filters(analysis, user_preferences):
            continue

        # Calculate match score
        match_score = await calculate_property_score(property, user_preferences)

        filtered_properties.append({
            "property": property,
            "match_score": match_score,
            "neighborhood_analysis": analysis
        })

    # Sort by match score
    filtered_properties.sort(key=lambda x: x["match_score"], reverse=True)

    return filtered_properties


def passes_neighborhood_filters(
    analysis: NeighborhoodIntelligence,
    preferences: Dict
) -> bool:
    """Check if property passes neighborhood filters."""

    # Walkability filter
    if preferences.get("min_walk_score"):
        if not analysis.walkability or \
           (analysis.walkability.walk_score or 0) < preferences["min_walk_score"]:
            return False

    # School filter
    if preferences.get("min_school_rating"):
        if not analysis.schools or \
           (analysis.schools.average_rating or 0) < preferences["min_school_rating"]:
            return False

    # Commute filter
    if preferences.get("max_commute_minutes"):
        if not analysis.commute or \
           (analysis.commute.average_commute_time or 999) > preferences["max_commute_minutes"]:
            return False

    # Transit requirement
    if preferences.get("transit_required"):
        if not analysis.commute or not analysis.commute.public_transit_accessible:
            return False

    return True
```

### 4. GHL Webhook Integration

**File**: `/ghl_real_estate_ai/webhooks/ghl_property_webhooks.py`

Pre-cache neighborhood data when properties are added:

```python
@webhook_handler("opportunity.created")
async def handle_new_opportunity(opportunity_data: Dict):
    """Handle new opportunity with neighborhood pre-caching."""

    # Extract property location
    property_location = extract_location(opportunity_data)

    if property_location:
        # Pre-cache neighborhood data in background
        asyncio.create_task(
            pre_cache_neighborhood_data(property_location)
        )

    # Continue with normal opportunity handling
    await process_opportunity(opportunity_data)


async def pre_cache_neighborhood_data(location: Dict):
    """Pre-cache neighborhood data for faster access."""

    try:
        await neighborhood_api.analyze_neighborhood(
            property_address=location["address"],
            lat=location["lat"],
            lng=location["lng"],
            city=location["city"],
            state=location["state"],
            zipcode=location["zipcode"]
        )

        logger.info(f"Pre-cached neighborhood data for {location['address']}")

    except Exception as e:
        logger.error(f"Failed to pre-cache neighborhood data: {e}")
```

### 5. Streamlit Dashboard Integration

**File**: `/ghl_real_estate_ai/streamlit_components/property_details_card.py`

Display neighborhood intelligence in UI:

```python
import streamlit as st
from ghl_real_estate_ai.services.neighborhood_intelligence_api import (
    NeighborhoodIntelligenceAPI
)

async def render_property_with_neighborhood(property_data: Dict):
    """Render property details with neighborhood intelligence."""

    st.header(property_data["address"])

    # Property basics
    col1, col2, col3 = st.columns(3)
    col1.metric("Price", f"${property_data['price']:,}")
    col2.metric("Beds", property_data["bedrooms"])
    col3.metric("Baths", property_data["bathrooms"])

    st.divider()

    # Neighborhood Intelligence
    st.subheader("Neighborhood Intelligence")

    with st.spinner("Analyzing neighborhood..."):
        analysis = await neighborhood_api.analyze_neighborhood(
            property_address=property_data["address"],
            lat=property_data["lat"],
            lng=property_data["lng"],
            city=property_data["city"],
            state=property_data["state"],
            zipcode=property_data["zipcode"]
        )

    # Overall Score
    st.metric(
        "Overall Neighborhood Score",
        f"{analysis.overall_score}/100",
        delta=None,
        help="Composite score based on walkability, schools, commute, and safety"
    )

    # Walkability
    if analysis.walkability:
        st.markdown("### Walkability")
        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Walk Score",
            f"{analysis.walkability.walk_score}/100",
            help=analysis.walkability.walk_description
        )

        if analysis.walkability.transit_score:
            col2.metric(
                "Transit Score",
                f"{analysis.walkability.transit_score}/100",
                help=analysis.walkability.transit_description
            )

        if analysis.walkability.bike_score:
            col3.metric(
                "Bike Score",
                f"{analysis.walkability.bike_score}/100",
                help=analysis.walkability.bike_description
            )

    # Schools
    if analysis.schools:
        st.markdown("### Schools")

        st.metric(
            "Average School Rating",
            f"{analysis.schools.average_rating}/10"
        )

        # Show top schools
        if analysis.schools.elementary_schools:
            with st.expander("Elementary Schools"):
                for school in sorted(
                    analysis.schools.elementary_schools,
                    key=lambda s: s.rating or 0,
                    reverse=True
                )[:3]:
                    st.write(f"**{school.name}** - {school.rating}/10")
                    if school.distance_miles:
                        st.write(f"  ↳ {school.distance_miles:.1f} miles away")

    # Commute
    if analysis.commute:
        st.markdown("### Commute Analysis")

        col1, col2 = st.columns(2)

        col1.metric(
            "Average Commute",
            f"{analysis.commute.average_commute_time} min"
        )

        col2.metric(
            "Destinations within 30min",
            analysis.commute.employment_centers_within_30min
        )

        # Show routes
        if analysis.commute.routes:
            with st.expander("Commute Routes"):
                for route in analysis.commute.routes:
                    duration = route.duration_in_traffic_minutes or route.duration_minutes
                    st.write(
                        f"**{route.destination}** ({route.mode.value}): "
                        f"{duration} min ({route.distance_miles:.1f} mi)"
                    )
```

## Deployment Checklist

### Pre-Deployment

- [ ] **API Keys Configured**
  - Walk Score API key set
  - Google Maps API key set
  - GreatSchools API key set (optional)

- [ ] **Redis Setup**
  - Redis instance deployed
  - Connection tested
  - Cache TTL configured (24 hours)

- [ ] **Service Testing**
  - Unit tests passing (25+ tests)
  - Integration tests passing
  - Real API tests successful

### Integration Testing

- [ ] **Enhanced Matching Models**
  - Neighborhood scoring integrated
  - Weight calculations validated
  - Score factors extraction working

- [ ] **Behavioral Learning**
  - Preference tracking implemented
  - Learning updates working
  - Historical data migration complete

- [ ] **Property Search**
  - Neighborhood filters active
  - Search performance acceptable (<2s)
  - Cache hit rate >85%

- [ ] **GHL Webhooks**
  - Pre-caching on property creation
  - Background processing working
  - Error handling tested

- [ ] **Streamlit UI**
  - Neighborhood data displaying
  - Loading states smooth
  - Error states handled

### Monitoring Setup

- [ ] **Performance Metrics**
  - API response time tracking
  - Cache hit rate monitoring
  - Error rate alerting

- [ ] **Cost Tracking**
  - Daily API cost monitoring
  - Budget alerts configured
  - Cost per analysis tracked

- [ ] **Business Metrics**
  - Property match satisfaction tracking
  - A/B test setup (with/without neighborhood data)
  - User engagement metrics

### Production Rollout

- [ ] **Phase 1: Soft Launch** (10% of users)
  - Enable for small user subset
  - Monitor performance and costs
  - Gather initial feedback

- [ ] **Phase 2: Gradual Rollout** (50% of users)
  - Expand to half of user base
  - Validate cache performance
  - Confirm cost projections

- [ ] **Phase 3: Full Deployment** (100% of users)
  - Enable for all users
  - Monitor satisfaction improvement
  - Optimize based on usage patterns

## Performance Optimization

### Cache Warming Strategy

```python
# Daily cache warming job
async def warm_popular_locations():
    """Warm cache for top 100 locations."""

    # Get top locations from analytics
    popular_locations = await get_popular_locations(limit=100)

    # Warm cache
    await neighborhood_api.warm_cache_for_locations(
        [(loc["lat"], loc["lng"]) for loc in popular_locations]
    )

    logger.info(f"Warmed cache for {len(popular_locations)} locations")


# Schedule daily at 2 AM
schedule_daily(warm_popular_locations, hour=2)
```

### Cost Optimization

```python
# Monitor and alert on costs
async def monitor_api_costs():
    """Monitor API costs and alert if exceeded."""

    metrics = neighborhood_api.get_cost_metrics()

    # Daily budget: $50
    if metrics["estimated_cost_usd"] > 50:
        await send_alert(
            severity="HIGH",
            message=f"Neighborhood API costs exceeded budget: ${metrics['estimated_cost_usd']:.2f}"
        )

    # Cache hit rate below target
    if metrics["cache_hit_rate"] < 85:
        await send_alert(
            severity="MEDIUM",
            message=f"Cache hit rate below target: {metrics['cache_hit_rate']:.1f}%"
        )
```

## Success Metrics

### Technical KPIs

- **API Response Time**: <200ms (95th percentile)
- **Cache Hit Rate**: >85%
- **Error Rate**: <1%
- **Cost per Analysis**: <$0.10

### Business KPIs

- **Property Match Satisfaction**: 88% → 93%+
- **Time to Match**: 20% reduction
- **Agent Productivity**: 5-10 min saved per property
- **Lead Engagement**: 15%+ increase

## Troubleshooting

### Common Issues

1. **Low Cache Hit Rate**
   - Check Redis connection
   - Verify cache TTL settings
   - Review location clustering

2. **High API Costs**
   - Audit cache warming strategy
   - Check for duplicate requests
   - Verify rate limiting

3. **Slow Response Times**
   - Check parallel API coordination
   - Verify Redis latency
   - Review network connectivity

---

**Integration Guide Version**: 1.0.0
**Last Updated**: January 2026
**Maintained By**: EnterpriseHub Engineering Team
