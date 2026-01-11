# Advanced Personalization Engine Guide

## Overview

The Advanced Personalization Engine is a Phase 5 feature that provides ML-driven personalization achieving 92%+ accuracy through behavioral learning, communication style adaptation, and intelligent profile generation.

## Key Features

### 🎯 Core Capabilities
- **ML-driven personalized profile generation** (>92% accuracy)
- **Real-time communication style adaptation** (<100ms)
- **Personality-based engagement strategies**
- **Multi-language communication support**
- **Industry vertical specialization patterns**
- **Mobile-optimized personalization delivery**

### 📊 Performance Targets
- **Profile Generation**: <200ms
- **Recommendation Latency**: <150ms
- **Personalization Accuracy**: >92%
- **Real-time Adaptation**: <100ms
- **Communication Matching**: >88% satisfaction

## Quick Start

### Basic Usage

```python
from ghl_real_estate_ai.services.claude.advanced.advanced_personalization_engine import (
    get_advanced_personalization_engine
)

# Get the personalization engine
engine = await get_advanced_personalization_engine()

# Create a personalized profile
profile = await engine.create_personalized_profile(
    lead_id="lead_123",
    conversation_history=conversation_data,
    behavioral_data=behavioral_metrics,
    property_interactions=property_data
)

# Generate personalized recommendations
recommendations = await engine.generate_personalized_recommendations(
    lead_id="lead_123",
    current_context={"stage": "consideration"}
)

# Adapt communication style
adaptation = await engine.adapt_communication_style(
    original_message="Hello, I have some properties to show you.",
    lead_id="lead_123"
)
```

## Detailed Usage Examples

### 1. Creating Personalized Profiles

```python
# Sample conversation history
conversation_history = [
    {
        "content": "I'm looking for luxury properties with high-end amenities",
        "timestamp": datetime.now() - timedelta(hours=2),
        "speaker": "lead"
    },
    {
        "content": "I need detailed market analysis and ROI data",
        "timestamp": datetime.now() - timedelta(hours=1),
        "speaker": "lead"
    }
]

# Sample behavioral data
behavioral_data = {
    "engagement_score": 0.85,
    "avg_response_time": 1.2,  # hours
    "mobile_usage_ratio": 0.7,
    "sessions_per_week": 4.5,
    "peak_activity_hours": [10, 14, 19]
}

# Sample property interactions
property_interactions = [
    {
        "property_type": "luxury_condo",
        "price": 850000,
        "features_viewed": ["location", "amenities", "investment_potential"],
        "view_duration": 240  # seconds
    }
]

# Create comprehensive profile
profile = await engine.create_personalized_profile(
    lead_id="analytical_luxury_lead",
    conversation_history=conversation_history,
    behavioral_data=behavioral_data,
    property_interactions=property_interactions
)

print(f"Detected Personality: {profile.personality_type.value}")
print(f"Communication Style: {profile.communication_style.value}")
print(f"Industry Vertical: {profile.industry_vertical.value}")
print(f"Accuracy: {profile.accuracy_metrics['overall_accuracy']:.2%}")
```

### 2. Generating Personalized Recommendations

```python
# Generate specific recommendation types
recommendation_types = [
    'next_message',
    'property_suggestion',
    'engagement_strategy',
    'objection_handling',
    'follow_up_timing'
]

recommendations = await engine.generate_personalized_recommendations(
    lead_id="analytical_luxury_lead",
    current_context={
        "recent_inquiry": "luxury_condos",
        "conversation_stage": "consideration",
        "last_interaction": datetime.now() - timedelta(hours=6)
    },
    recommendation_types=recommendation_types
)

for rec in recommendations:
    print(f"\n{rec.recommendation_type.upper()}:")
    print(f"Message: {rec.recommendation_text}")
    print(f"Confidence: {rec.confidence_score:.2%}")
    print(f"Expected Response: {rec.expected_response_probability:.2%}")
    print(f"Optimal Timing: {rec.optimal_timing}")
    print(f"Preferred Channel: {rec.preferred_channel.value}")
```

### 3. Communication Style Adaptation

```python
# Original formal message
original_message = """
Dear Valued Client,
I would like to respectfully inform you that we have identified
several exceptional properties that may be suitable for your
consideration. These properties feature numerous high-end amenities
and are located in prestigious neighborhoods.
"""

# Adapt for different personalities
personalities = [
    "analytical_luxury_lead",    # Analytical + Luxury
    "driver_commercial_lead",    # Driver + Commercial
    "expressive_residential_lead" # Expressive + Residential
]

for lead_id in personalities:
    adaptation = await engine.adapt_communication_style(
        original_message=original_message,
        lead_id=lead_id
    )

    print(f"\n{lead_id.upper()}:")
    print(f"Adapted: {adaptation.adapted_message}")
    print(f"Tone Changes: {adaptation.tone_adjustments}")
    print(f"Style Match: {adaptation.style_match_score:.2%}")
```

### 4. Multi-Language Support

```python
# Create profile with language preferences
spanish_profile = await engine.create_personalized_profile(
    lead_id="spanish_speaking_lead",
    conversation_history=[
        {
            "content": "Hola, estoy buscando una casa para mi familia",
            "timestamp": datetime.now(),
            "speaker": "lead"
        }
    ],
    behavioral_data={"engagement_score": 0.8},
    property_interactions=[],
    demographic_data={"language": "es"}
)

# Adapt message for Spanish-speaking client
english_message = "Hello, I have some family-friendly properties to show you."

spanish_adaptation = await engine.adapt_communication_style(
    original_message=english_message,
    lead_id="spanish_speaking_lead"
)

print(f"Original: {english_message}")
print(f"Adapted: {spanish_adaptation.adapted_message}")
print(f"Cultural Considerations: {spanish_adaptation.additional_context}")
```

### 5. Channel-Specific Optimization

```python
# Adapt same message for different channels
message = "I have 3 luxury properties that perfectly match your criteria. Each offers exceptional amenities, prime location, and strong investment potential."

channels = [
    PersonalizationChannel.SMS,
    PersonalizationChannel.EMAIL,
    PersonalizationChannel.WHATSAPP
]

for channel in channels:
    adaptation = await engine.adapt_communication_style(
        original_message=message,
        lead_id="luxury_lead",
        target_channel=channel
    )

    print(f"\n{channel.value.upper()}:")
    print(f"Adapted: {adaptation.adapted_message}")
    print(f"Length: {len(adaptation.adapted_message)} chars")
```

## Personality Types and Communication Styles

### Supported Personality Types

| Personality | Characteristics | Optimal Approach |
|-------------|----------------|------------------|
| **Analytical** | Data-driven, detail-oriented | Provide statistics, market analysis, detailed comparisons |
| **Driver** | Results-focused, time-sensitive | Quick decisions, direct communication, efficiency focus |
| **Expressive** | Enthusiastic, relationship-oriented | Emotional connection, visual presentations, excitement |
| **Amiable** | Patient, relationship-focused | Personal attention, consultative approach, patience |
| **Technical** | Feature-focused, specification-oriented | Technical details, feature comparisons, specifications |
| **Relationship-Focused** | Trust-building, consultation-oriented | Personal service, relationship building, consultation |

### Communication Style Adaptations

| Style | Message Tone | Complexity | Preferred Content |
|-------|-------------|------------|-------------------|
| **Formal Professional** | Professional, respectful | Moderate-High | Market reports, formal presentations |
| **Casual Friendly** | Warm, approachable | Moderate | Personal stories, casual conversation |
| **Technical Detailed** | Informative, precise | High | Specifications, detailed analysis |
| **Concise Direct** | Straight-forward, brief | Low | Key points, quick summaries |
| **Consultative** | Advisory, helpful | Moderate | Guidance, recommendations |
| **Educational** | Informative, teaching | High | Market education, explanations |

## Industry Vertical Specialization

### Luxury Real Estate
```python
# Luxury vertical characteristics
luxury_profile = {
    "personality_adaptations": {
        "privacy_importance": 0.9,
        "exclusivity_preference": 0.8,
        "quality_focus": 0.9,
        "service_expectations": 0.9
    },
    "communication_style": "formal_professional",
    "preferred_channels": ["email", "phone", "in_person"],
    "content_focus": ["exclusive_access", "premium_amenities", "prestige"]
}
```

### Commercial Real Estate
```python
# Commercial vertical characteristics
commercial_profile = {
    "personality_adaptations": {
        "roi_focus": 0.9,
        "location_importance": 0.8,
        "growth_potential": 0.8,
        "business_factors": 0.9
    },
    "communication_style": "technical_detailed",
    "preferred_channels": ["email", "phone"],
    "content_focus": ["roi_analysis", "market_data", "business_impact"]
}
```

### Investment Properties
```python
# Investment vertical characteristics
investment_profile = {
    "personality_adaptations": {
        "financial_analysis": 0.9,
        "market_data": 0.8,
        "rental_potential": 0.9,
        "long_term_perspective": 0.8
    },
    "communication_style": "analytical",
    "preferred_channels": ["email", "phone"],
    "content_focus": ["financial_returns", "market_trends", "investment_strategy"]
}
```

## Performance Optimization

### Caching Strategy
```python
# Profile caching (automatic)
# Profiles are cached for 1 hour by default
profile = await engine.create_personalized_profile(lead_id="test")  # Creates and caches
profile = await engine.create_personalized_profile(lead_id="test")  # Uses cache

# Recommendation caching (automatic)
# Recommendations are cached until context changes
recommendations = await engine.generate_personalized_recommendations(lead_id="test")

# Manual cache management
engine.profile_cache.clear()  # Clear all cached profiles
del engine.profile_cache["specific_lead"]  # Clear specific profile
```

### Performance Monitoring
```python
# Get performance metrics
metrics = await engine.get_personalization_metrics()

print(f"Performance Targets:")
print(f"  Profile Generation: {metrics['performance_targets']['profile_generation_ms']}ms")
print(f"  Recommendation Latency: {metrics['performance_targets']['recommendation_latency_ms']}ms")
print(f"  Adaptation Latency: {metrics['performance_targets']['adaptation_latency_ms']}ms")

print(f"\nCache Status:")
print(f"  Cached Profiles: {metrics['cache_status']['cached_profiles']}")
print(f"  Cached Recommendations: {metrics['cache_status']['cached_recommendations']}")

print(f"\nModel Status:")
print(f"  Dependencies Available: {metrics['dependencies_available']}")
print(f"  Language Support: {len(metrics['language_support']['supported_languages'])} languages")
```

## Integration Examples

### With Existing Services

```python
# Integration with Behavioral Analyzer
from ghl_real_estate_ai.services.claude.advanced.predictive_behavior_analyzer import (
    get_advanced_behavior_analyzer
)

# Get both services
behavior_analyzer = await get_advanced_behavior_analyzer()
personalization_engine = await get_advanced_personalization_engine()

# Use behavioral predictions for personalization
behavioral_predictions = await behavior_analyzer.predict_advanced_behavior(
    lead_id="integration_test",
    conversation_history=conversation_data,
    interaction_data=interaction_data,
    prediction_types=[AdvancedPredictionType.CONVERSION_LIKELIHOOD_ADVANCED]
)

# Create personalized profile with enhanced behavioral context
enhanced_profile = await personalization_engine.create_personalized_profile(
    lead_id="integration_test",
    conversation_history=conversation_data,
    behavioral_data={
        **behavioral_data,
        "behavioral_predictions": [asdict(p) for p in behavioral_predictions]
    },
    property_interactions=property_data
)
```

### With GHL Webhook Processing

```python
# Enhanced webhook processing with personalization
async def process_ghl_webhook_with_personalization(contact_data: dict):
    lead_id = contact_data["id"]

    # Get conversation history from GHL
    conversation_history = await get_ghl_conversation_history(lead_id)

    # Extract behavioral data from GHL
    behavioral_data = await extract_ghl_behavioral_data(contact_data)

    # Get property interactions
    property_interactions = await get_ghl_property_interactions(lead_id)

    # Create personalized profile
    profile = await engine.create_personalized_profile(
        lead_id=lead_id,
        conversation_history=conversation_history,
        behavioral_data=behavioral_data,
        property_interactions=property_interactions
    )

    # Generate personalized follow-up
    recommendations = await engine.generate_personalized_recommendations(
        lead_id=lead_id,
        current_context={"source": "ghl_webhook", "contact_data": contact_data}
    )

    # Adapt follow-up message
    follow_up_message = "Thank you for your interest. I have some properties that might be perfect for you."

    adapted_message = await engine.adapt_communication_style(
        original_message=follow_up_message,
        lead_id=lead_id,
        target_channel=PersonalizationChannel.EMAIL
    )

    # Update GHL with personalized insights
    await update_ghl_contact_with_personalization(lead_id, profile, recommendations)

    # Send personalized follow-up
    await send_personalized_follow_up(lead_id, adapted_message.adapted_message)
```

## Error Handling and Fallbacks

### Graceful Degradation
```python
try:
    # Attempt advanced personalization
    profile = await engine.create_personalized_profile(
        lead_id=lead_id,
        conversation_history=conversation_history,
        behavioral_data=behavioral_data,
        property_interactions=property_interactions
    )
except Exception as e:
    logger.warning(f"Advanced personalization failed: {e}")

    # Fallback to basic profile
    profile = PersonalizationProfile(
        lead_id=lead_id,
        personality_type=PersonalityType.AMIABLE,
        communication_style=CommunicationStyle.CONSULTATIVE,
        # ... minimal default values
    )

# Always validate profile before use
if profile.accuracy_metrics.get("overall_accuracy", 0) < 0.7:
    logger.warning(f"Low accuracy profile for {lead_id}")
    # Use conservative personalization approaches
```

### Monitoring and Alerts
```python
# Monitor performance and accuracy
async def monitor_personalization_performance():
    metrics = await engine.get_personalization_metrics()

    # Check cache hit rates
    cache_efficiency = metrics["cache_status"]["cached_profiles"] / max(total_requests, 1)
    if cache_efficiency < 0.6:
        logger.warning("Low cache efficiency detected")

    # Check accuracy trends
    recent_accuracy = np.mean([
        profile.accuracy_metrics.get("overall_accuracy", 0.7)
        for profile in recent_profiles
    ])

    if recent_accuracy < 0.85:
        logger.warning(f"Accuracy below target: {recent_accuracy:.2%}")

    # Monitor latency
    avg_latency = np.mean([
        h["processing_time"] for h in recent_processing_times
    ])

    if avg_latency > 200:  # ms
        logger.warning(f"Latency above target: {avg_latency:.1f}ms")
```

## Best Practices

### 1. Data Quality
- **Ensure rich conversation history** for better personality detection
- **Collect comprehensive behavioral metrics** for accurate preference prediction
- **Track property interaction patterns** for vertical specialization
- **Validate data quality** before profile creation

### 2. Performance Optimization
- **Use caching effectively** - profiles cache for 1 hour
- **Batch profile creation** for multiple leads when possible
- **Monitor performance metrics** regularly
- **Implement fallback strategies** for degraded performance

### 3. Accuracy Improvement
- **Collect feedback** on personalization effectiveness
- **A/B test** different personalization approaches
- **Update profiles regularly** with new interaction data
- **Validate recommendations** against actual outcomes

### 4. User Experience
- **Start with conservative personalization** and increase sophistication
- **Provide transparency** about personalization features
- **Allow user preferences** to override automated detection
- **Test across different cultures** and languages

## Troubleshooting

### Common Issues

#### Low Accuracy Profiles
```python
# Diagnose low accuracy
if profile.accuracy_metrics["overall_accuracy"] < 0.8:
    print("Potential issues:")
    print(f"- Conversation length: {len(conversation_history)} messages")
    print(f"- Data completeness: {profile.accuracy_metrics.get('data_completeness', 0):.2%}")
    print(f"- Feature richness: {profile.accuracy_metrics.get('feature_richness', 0):.2%}")

    # Recommendations for improvement
    if len(conversation_history) < 5:
        print("Recommendation: Collect more conversation data")
    if profile.accuracy_metrics.get("data_completeness", 0) < 0.5:
        print("Recommendation: Enhance behavioral data collection")
```

#### Performance Issues
```python
# Monitor and optimize performance
async def optimize_performance():
    metrics = await engine.get_personalization_metrics()

    # Clear old cache entries
    current_time = datetime.now()
    for lead_id, profile in list(engine.profile_cache.items()):
        if (current_time - profile.last_updated).total_seconds() > 3600:
            del engine.profile_cache[lead_id]

    # Check model initialization
    if not metrics["model_status"]["personality_classifier"]:
        logger.warning("Personality classifier not initialized - limited functionality")
```

#### Integration Problems
```python
# Validate integration points
async def validate_integration():
    try:
        # Test behavioral analyzer integration
        behavior_analyzer = await get_advanced_behavior_analyzer()
        assert behavior_analyzer is not None

        # Test Claude analyzer integration
        engine = await get_advanced_personalization_engine()
        assert engine.claude_analyzer is not None

        # Test settings integration
        from ghl_real_estate_ai.config.settings import settings
        assert settings.anthropic_api_key

        logger.info("All integrations validated successfully")

    except Exception as e:
        logger.error(f"Integration validation failed: {e}")
```

## API Reference

### Core Classes

#### PersonalizationProfile
```python
@dataclass
class PersonalizationProfile:
    lead_id: str
    personality_type: PersonalityType
    personality_confidence: float
    communication_style: CommunicationStyle
    style_confidence: float
    preferred_channels: List[PersonalizationChannel]
    optimal_contact_times: List[Tuple[str, int]]
    # ... additional fields
```

#### PersonalizedRecommendation
```python
@dataclass
class PersonalizedRecommendation:
    lead_id: str
    recommendation_type: str
    recommendation_text: str
    confidence_score: float
    adapted_communication_style: CommunicationStyle
    optimal_timing: datetime
    preferred_channel: PersonalizationChannel
    # ... additional fields
```

#### CommunicationAdaptation
```python
@dataclass
class CommunicationAdaptation:
    original_message: str
    adapted_message: str
    adaptation_factors: List[str]
    tone_adjustments: Dict[str, str]
    complexity_adjustments: Dict[str, str]
    adaptation_confidence: float
    expected_engagement_improvement: float
    style_match_score: float
```

### Main Methods

#### create_personalized_profile()
```python
async def create_personalized_profile(
    self,
    lead_id: str,
    conversation_history: List[Dict[str, Any]],
    behavioral_data: Dict[str, Any],
    property_interactions: List[Dict[str, Any]],
    demographic_data: Optional[Dict[str, Any]] = None
) -> PersonalizationProfile
```

#### generate_personalized_recommendations()
```python
async def generate_personalized_recommendations(
    self,
    lead_id: str,
    current_context: Dict[str, Any],
    recommendation_types: List[str] = None
) -> List[PersonalizedRecommendation]
```

#### adapt_communication_style()
```python
async def adapt_communication_style(
    self,
    original_message: str,
    lead_id: str,
    target_channel: Optional[PersonalizationChannel] = None
) -> CommunicationAdaptation
```

---

## Conclusion

The Advanced Personalization Engine provides sophisticated ML-driven personalization capabilities that significantly improve lead engagement and conversion rates through intelligent communication adaptation and behavioral understanding.

For questions or support, refer to the comprehensive test suite and integration examples provided in the codebase.