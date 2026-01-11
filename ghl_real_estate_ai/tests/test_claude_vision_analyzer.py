"""
Tests for Claude Vision Property Image Analyzer

Comprehensive test suite validating:
- Image preprocessing and optimization
- Luxury feature detection
- Condition assessment
- Style classification
- Feature extraction
- Performance targets (<1.5s)
- Caching functionality
- Error handling
"""

import pytest
import asyncio
import time
from typing import Dict, List, Any
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from ghl_real_estate_ai.services.claude_vision_analyzer import (
    ClaudeVisionAnalyzer,
    PropertyAnalysis,
    LuxuryFeatures,
    ConditionScore,
    StyleClassification,
    FeatureExtraction,
    PropertyStyle,
    PropertyCondition,
    LuxuryLevel,
    analyze_property_images,
    detect_luxury_features,
    assess_property_condition,
)
from ghl_real_estate_ai.services.base.exceptions import (
    ValidationError,
    PerformanceError,
)


# Fixtures

@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing"""
    client = AsyncMock()

    # Mock response structure
    mock_response = Mock()
    mock_response.content = [Mock(text='{"luxury_score": 8.5}')]

    client.messages.create = AsyncMock(return_value=mock_response)

    return client


@pytest.fixture
def mock_redis_cache():
    """Mock Redis cache for testing"""
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    return cache


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for image downloads"""
    client = AsyncMock()

    # Mock successful image download
    mock_response = Mock()
    mock_response.content = b"\xff\xd8\xff\xe0"  # JPEG magic bytes
    mock_response.headers = {"content-type": "image/jpeg"}
    mock_response.raise_for_status = Mock()

    client.get = AsyncMock(return_value=mock_response)
    client.aclose = AsyncMock()

    return client


@pytest.fixture
async def vision_analyzer(mock_anthropic_client, mock_redis_cache, mock_http_client):
    """Initialized Claude Vision Analyzer for testing"""
    analyzer = ClaudeVisionAnalyzer()

    # Inject mocks
    analyzer.client = mock_anthropic_client
    analyzer.cache_manager = mock_redis_cache
    analyzer.http_client = mock_http_client
    analyzer._initialized = True

    yield analyzer

    # Cleanup
    await analyzer.cleanup()


@pytest.fixture
def sample_image_urls():
    """Sample property image URLs"""
    return [
        "https://example.com/property1/front.jpg",
        "https://example.com/property1/kitchen.jpg",
        "https://example.com/property1/pool.jpg",
    ]


@pytest.fixture
def mock_luxury_response():
    """Mock Claude response for luxury analysis"""
    return {
        "luxury_score": 8.5,
        "luxury_level": "high_end_luxury",
        "high_end_finishes": ["Marble countertops", "Custom cabinetry", "Designer fixtures"],
        "premium_materials": ["Italian marble", "Hardwood floors", "Granite"],
        "architectural_details": ["Crown molding", "Coffered ceilings", "Wainscoting"],
        "designer_elements": ["Chandelier", "Custom lighting", "Premium appliances"],
        "outdoor_luxury": ["Infinity pool", "Outdoor kitchen", "Professional landscaping"],
        "confidence": 0.92,
    }


@pytest.fixture
def mock_condition_response():
    """Mock Claude response for condition analysis"""
    return {
        "condition_score": 9.0,
        "condition": "excellent",
        "maintenance_level": "excellent",
        "visible_issues": [],
        "positive_indicators": ["Recently renovated", "Fresh paint", "Modern fixtures"],
        "renovation_indicators": ["Updated kitchen", "New flooring"],
        "age_indicators": "Recently built or fully renovated",
        "confidence": 0.88,
    }


@pytest.fixture
def mock_style_response():
    """Mock Claude response for style classification"""
    return {
        "primary_style": "modern",
        "secondary_styles": ["contemporary"],
        "style_confidence": 0.9,
        "architectural_features": ["Clean lines", "Large windows", "Open floor plan"],
        "period_indicators": "2020s contemporary design",
        "design_coherence": 9.0,
    }


@pytest.fixture
def mock_features_response():
    """Mock Claude response for feature extraction"""
    return {
        "has_pool": True,
        "pool_type": "infinity",
        "has_outdoor_kitchen": True,
        "has_fireplace": True,
        "fireplace_count": 2,
        "has_high_ceilings": True,
        "has_hardwood_floors": True,
        "has_modern_kitchen": True,
        "kitchen_features": ["Island", "Granite countertops", "Stainless appliances"],
        "has_spa": True,
        "has_wine_cellar": True,
        "has_home_theater": False,
        "has_gym": True,
        "has_garage": True,
        "garage_spaces": 3,
        "outdoor_features": ["Patio", "Deck", "Garden"],
        "smart_home_features": ["Smart thermostat", "Security system"],
        "view_type": "ocean",
        "landscaping_quality": "excellent",
    }


# Test Service Initialization

@pytest.mark.asyncio
async def test_service_initialization():
    """Test service initializes correctly"""
    analyzer = ClaudeVisionAnalyzer()

    assert analyzer.service_name == "ClaudeVisionAnalyzer"
    assert analyzer.enable_metrics is True
    assert analyzer.client is None  # Not initialized yet
    assert analyzer.total_analyses == 0


@pytest.mark.asyncio
async def test_service_initialization_with_api_key():
    """Test service initialization with valid API key"""
    with patch('ghl_real_estate_ai.services.claude_vision_analyzer.settings') as mock_settings:
        mock_settings.anthropic_api_key = "test-api-key"

        analyzer = ClaudeVisionAnalyzer()
        await analyzer.initialize()

        assert analyzer._initialized is True
        assert analyzer.client is not None


@pytest.mark.asyncio
async def test_service_initialization_without_api_key():
    """Test service initialization fails without API key"""
    with patch('ghl_real_estate_api.services.claude_vision_analyzer.settings') as mock_settings:
        mock_settings.anthropic_api_key = None

        analyzer = ClaudeVisionAnalyzer()

        with pytest.raises(ValidationError, match="ANTHROPIC_API_KEY not configured"):
            await analyzer.initialize()


# Test Image Preprocessing

@pytest.mark.asyncio
async def test_image_download_and_preprocessing(vision_analyzer, sample_image_urls):
    """Test image download and preprocessing"""
    processed_images = await vision_analyzer._download_and_preprocess_images(sample_image_urls)

    assert len(processed_images) == 3
    assert all(img["type"] == "image" for img in processed_images)
    assert all("source" in img for img in processed_images)
    assert vision_analyzer.http_client.get.call_count == 3


@pytest.mark.asyncio
async def test_image_size_optimization(vision_analyzer):
    """Test image size optimization"""
    # Create a large test image
    from PIL import Image
    from io import BytesIO

    large_image = Image.new("RGB", (3000, 3000), color="red")
    img_bytes = BytesIO()
    large_image.save(img_bytes, format="JPEG")
    img_bytes = img_bytes.getvalue()

    # Optimize
    optimized = await vision_analyzer._optimize_image_size(img_bytes)

    # Verify size reduction
    optimized_img = Image.open(BytesIO(optimized))
    assert optimized_img.width <= vision_analyzer.OPTIMAL_IMAGE_SIZE[0]
    assert optimized_img.height <= vision_analyzer.OPTIMAL_IMAGE_SIZE[1]


@pytest.mark.asyncio
async def test_image_compression(vision_analyzer):
    """Test image compression for oversized images"""
    from PIL import Image
    from io import BytesIO

    # Create test image
    test_image = Image.new("RGB", (2000, 2000), color="blue")
    img_bytes = BytesIO()
    test_image.save(img_bytes, format="JPEG", quality=95)
    original_bytes = img_bytes.getvalue()

    # Compress
    compressed = await vision_analyzer._compress_image(original_bytes)

    # Verify compression
    assert len(compressed) < len(original_bytes)


def test_media_type_detection(vision_analyzer):
    """Test media type detection from image bytes"""
    # JPEG
    jpeg_bytes = b"\xff\xd8\xff\xe0"
    assert vision_analyzer._detect_media_type(jpeg_bytes) == "image/jpeg"

    # PNG
    png_bytes = b"\x89PNG\r\n\x1a\n"
    assert vision_analyzer._detect_media_type(png_bytes) == "image/png"

    # WEBP
    webp_bytes = b"RIFF\x00\x00\x00\x00WEBP"
    assert vision_analyzer._detect_media_type(webp_bytes) == "image/webp"


# Test Luxury Feature Analysis

@pytest.mark.asyncio
async def test_luxury_feature_detection(vision_analyzer, mock_luxury_response):
    """Test luxury feature detection"""
    # Mock Claude response
    vision_analyzer.client.messages.create = AsyncMock(
        return_value=Mock(content=[Mock(text=f'```json\n{mock_luxury_response}\n```')])
    )

    image_data = [{"type": "image", "source": {"type": "base64", "data": "test"}}]

    luxury_features = await vision_analyzer._analyze_luxury_features(image_data)

    assert luxury_features.luxury_score == 8.5
    assert luxury_features.luxury_level == LuxuryLevel.HIGH_END_LUXURY
    assert len(luxury_features.high_end_finishes) == 3
    assert luxury_features.confidence == 0.92


@pytest.mark.asyncio
async def test_luxury_level_mapping(vision_analyzer):
    """Test luxury level mapping from scores"""
    test_cases = [
        ({"luxury_score": 9.5, "luxury_level": "ultra_luxury"}, LuxuryLevel.ULTRA_LUXURY),
        ({"luxury_score": 7.5, "luxury_level": "high_end_luxury"}, LuxuryLevel.HIGH_END_LUXURY),
        ({"luxury_score": 5.5, "luxury_level": "upper_midrange"}, LuxuryLevel.UPPER_MIDRANGE),
        ({"luxury_score": 3.5, "luxury_level": "midrange"}, LuxuryLevel.MIDRANGE),
        ({"luxury_score": 1.5, "luxury_level": "entry_level"}, LuxuryLevel.ENTRY_LEVEL),
    ]

    for response_data, expected_level in test_cases:
        result = vision_analyzer._parse_luxury_features(response_data)
        assert result.luxury_level == expected_level


# Test Condition Assessment

@pytest.mark.asyncio
async def test_property_condition_assessment(vision_analyzer, mock_condition_response):
    """Test property condition assessment"""
    # Mock Claude response
    import json
    vision_analyzer.client.messages.create = AsyncMock(
        return_value=Mock(content=[Mock(text=json.dumps(mock_condition_response))])
    )

    image_data = [{"type": "image", "source": {"type": "base64", "data": "test"}}]

    condition = await vision_analyzer._analyze_property_condition(image_data)

    assert condition.condition == PropertyCondition.EXCELLENT
    assert condition.condition_score == 9.0
    assert condition.maintenance_level == "excellent"
    assert len(condition.positive_indicators) == 3
    assert condition.confidence == 0.88


@pytest.mark.asyncio
async def test_condition_mapping(vision_analyzer):
    """Test condition enum mapping"""
    test_cases = [
        ({"condition_score": 9.5, "condition": "excellent"}, PropertyCondition.EXCELLENT),
        ({"condition_score": 7.5, "condition": "very_good"}, PropertyCondition.VERY_GOOD),
        ({"condition_score": 5.5, "condition": "good"}, PropertyCondition.GOOD),
        ({"condition_score": 3.5, "condition": "fair"}, PropertyCondition.FAIR),
        ({"condition_score": 1.5, "condition": "poor"}, PropertyCondition.POOR),
    ]

    for response_data, expected_condition in test_cases:
        result = vision_analyzer._parse_condition_score(response_data)
        assert result.condition == expected_condition


# Test Style Classification

@pytest.mark.asyncio
async def test_architectural_style_classification(vision_analyzer, mock_style_response):
    """Test architectural style classification"""
    import json
    vision_analyzer.client.messages.create = AsyncMock(
        return_value=Mock(content=[Mock(text=json.dumps(mock_style_response))])
    )

    image_data = [{"type": "image", "source": {"type": "base64", "data": "test"}}]

    style = await vision_analyzer._classify_architectural_style(image_data)

    assert style.primary_style == PropertyStyle.MODERN
    assert PropertyStyle.CONTEMPORARY in style.secondary_styles
    assert style.style_confidence == 0.9
    assert style.design_coherence == 9.0


@pytest.mark.asyncio
async def test_style_mapping(vision_analyzer):
    """Test style enum mapping"""
    test_cases = [
        "modern", "contemporary", "traditional", "colonial", "craftsman",
        "mediterranean", "victorian", "ranch", "industrial", "farmhouse",
    ]

    for style_name in test_cases:
        response = {"primary_style": style_name, "style_confidence": 0.9}
        result = vision_analyzer._parse_style_classification(response)
        assert result.primary_style != PropertyStyle.UNKNOWN


# Test Feature Extraction

@pytest.mark.asyncio
async def test_feature_extraction(vision_analyzer, mock_features_response):
    """Test property feature extraction"""
    import json
    vision_analyzer.client.messages.create = AsyncMock(
        return_value=Mock(content=[Mock(text=json.dumps(mock_features_response))])
    )

    image_data = [{"type": "image", "source": {"type": "base64", "data": "test"}}]

    features = await vision_analyzer._extract_property_features(image_data)

    assert features.has_pool is True
    assert features.pool_type == "infinity"
    assert features.has_outdoor_kitchen is True
    assert features.fireplace_count == 2
    assert features.garage_spaces == 3
    assert features.view_type == "ocean"
    assert len(features.outdoor_features) == 3


# Test Complete Property Analysis

@pytest.mark.asyncio
async def test_complete_property_analysis(
    vision_analyzer,
    sample_image_urls,
    mock_luxury_response,
    mock_condition_response,
    mock_style_response,
    mock_features_response,
):
    """Test complete property analysis workflow"""
    import json

    # Mock all Claude responses
    responses = [
        json.dumps(mock_luxury_response),
        json.dumps(mock_condition_response),
        json.dumps(mock_style_response),
        json.dumps(mock_features_response),
    ]

    response_iter = iter(responses)

    async def mock_create(*args, **kwargs):
        return Mock(content=[Mock(text=next(response_iter))])

    vision_analyzer.client.messages.create = AsyncMock(side_effect=mock_create)

    # Run analysis
    analysis = await vision_analyzer.analyze_property_images(
        property_id="test_property_123",
        image_urls=sample_image_urls,
        use_cache=False,
    )

    # Verify results
    assert analysis.property_id == "test_property_123"
    assert analysis.images_analyzed == 3
    assert analysis.luxury_features.luxury_score == 8.5
    assert analysis.condition_score.condition_score == 9.0
    assert analysis.style_classification.primary_style == PropertyStyle.MODERN
    assert analysis.feature_extraction.has_pool is True
    assert analysis.overall_appeal_score > 0
    assert analysis.confidence > 0.8


# Test Performance

@pytest.mark.asyncio
async def test_analysis_performance_target(vision_analyzer, sample_image_urls):
    """Test that analysis meets <1.5s performance target"""
    import json

    # Mock fast responses
    mock_response = {
        "luxury_score": 8.0,
        "luxury_level": "high_end_luxury",
        "confidence": 0.9,
    }

    vision_analyzer.client.messages.create = AsyncMock(
        return_value=Mock(content=[Mock(text=json.dumps(mock_response))])
    )

    start_time = time.time()

    analysis = await vision_analyzer.analyze_property_images(
        property_id="perf_test",
        image_urls=sample_image_urls[:1],  # Single image for speed
        use_cache=False,
    )

    elapsed_ms = (time.time() - start_time) * 1000

    # Verify performance target
    assert elapsed_ms < 1500, f"Analysis took {elapsed_ms}ms, target is <1500ms"
    assert analysis.processing_time_ms < 1500


@pytest.mark.asyncio
async def test_concurrent_image_processing(vision_analyzer):
    """Test concurrent image processing"""
    image_urls = [f"https://example.com/img{i}.jpg" for i in range(5)]

    start_time = time.time()
    processed = await vision_analyzer._download_and_preprocess_images(image_urls)
    elapsed = time.time() - start_time

    # Verify all images processed
    assert len(processed) == 5

    # Verify concurrent processing (should be faster than sequential)
    assert elapsed < 5.0  # Should process concurrently in <5s


# Test Caching

@pytest.mark.asyncio
async def test_cache_key_generation(vision_analyzer, sample_image_urls):
    """Test cache key generation"""
    key1 = vision_analyzer._build_cache_key("prop123", sample_image_urls)
    key2 = vision_analyzer._build_cache_key("prop123", sample_image_urls)
    key3 = vision_analyzer._build_cache_key("prop456", sample_image_urls)

    # Same property and images should have same key
    assert key1 == key2

    # Different property should have different key
    assert key1 != key3


@pytest.mark.asyncio
async def test_cache_hit(vision_analyzer, sample_image_urls):
    """Test cache hit returns cached result"""
    cached_analysis = PropertyAnalysis(
        property_id="cached_prop",
        luxury_features=LuxuryFeatures(luxury_level=LuxuryLevel.HIGH_END_LUXURY, luxury_score=8.0),
        condition_score=ConditionScore(condition=PropertyCondition.EXCELLENT, condition_score=9.0),
        style_classification=StyleClassification(primary_style=PropertyStyle.MODERN),
        feature_extraction=FeatureExtraction(),
        processing_time_ms=500.0,
        images_analyzed=3,
    )

    # Mock cache hit
    vision_analyzer.cache_manager.get = AsyncMock(return_value=cached_analysis.to_dict())

    result = await vision_analyzer.analyze_property_images(
        property_id="cached_prop",
        image_urls=sample_image_urls,
        use_cache=True,
    )

    # Verify cache was used (no Claude API call)
    vision_analyzer.client.messages.create.assert_not_called()


@pytest.mark.asyncio
async def test_cache_miss_performs_analysis(vision_analyzer, sample_image_urls):
    """Test cache miss triggers new analysis"""
    import json

    # Mock cache miss
    vision_analyzer.cache_manager.get = AsyncMock(return_value=None)

    # Mock Claude response
    mock_response = {"luxury_score": 8.0, "confidence": 0.9}
    vision_analyzer.client.messages.create = AsyncMock(
        return_value=Mock(content=[Mock(text=json.dumps(mock_response))])
    )

    await vision_analyzer.analyze_property_images(
        property_id="new_prop",
        image_urls=sample_image_urls[:1],
        use_cache=True,
    )

    # Verify Claude API was called
    assert vision_analyzer.client.messages.create.call_count > 0

    # Verify result was cached
    vision_analyzer.cache_manager.set.assert_called()


# Test Error Handling

@pytest.mark.asyncio
async def test_invalid_property_id(vision_analyzer, sample_image_urls):
    """Test validation of property ID"""
    with pytest.raises(ValidationError, match="property_id is required"):
        await vision_analyzer.analyze_property_images(
            property_id="",
            image_urls=sample_image_urls,
        )


@pytest.mark.asyncio
async def test_no_image_urls(vision_analyzer):
    """Test validation of image URLs"""
    with pytest.raises(ValidationError, match="At least one image URL is required"):
        await vision_analyzer.analyze_property_images(
            property_id="test",
            image_urls=[],
        )


@pytest.mark.asyncio
async def test_too_many_images(vision_analyzer):
    """Test limiting of excessive image URLs"""
    many_urls = [f"https://example.com/img{i}.jpg" for i in range(20)]

    import json
    vision_analyzer.client.messages.create = AsyncMock(
        return_value=Mock(content=[Mock(text=json.dumps({"luxury_score": 5.0}))])
    )

    analysis = await vision_analyzer.analyze_property_images(
        property_id="test",
        image_urls=many_urls,
        use_cache=False,
    )

    # Should only process max allowed
    assert analysis.images_analyzed <= vision_analyzer.MAX_IMAGES_PER_PROPERTY


@pytest.mark.asyncio
async def test_analysis_timeout(vision_analyzer, sample_image_urls):
    """Test analysis timeout handling"""
    # Mock slow Claude response
    async def slow_response(*args, **kwargs):
        await asyncio.sleep(15)  # Exceed timeout
        return Mock(content=[Mock(text='{"luxury_score": 5.0}')])

    vision_analyzer.client.messages.create = AsyncMock(side_effect=slow_response)

    with pytest.raises(PerformanceError, match="timed out"):
        await vision_analyzer.analyze_property_images(
            property_id="timeout_test",
            image_urls=sample_image_urls,
            use_cache=False,
        )


@pytest.mark.asyncio
async def test_invalid_json_response(vision_analyzer, sample_image_urls):
    """Test handling of invalid JSON from Claude"""
    # Mock invalid JSON response
    vision_analyzer.client.messages.create = AsyncMock(
        return_value=Mock(content=[Mock(text="This is not valid JSON")])
    )

    with pytest.raises(ValidationError, match="Invalid JSON response"):
        await vision_analyzer.analyze_property_images(
            property_id="test",
            image_urls=sample_image_urls[:1],
            use_cache=False,
        )


# Test Synthesis Methods

def test_overall_appeal_calculation(vision_analyzer):
    """Test overall appeal score calculation"""
    luxury = LuxuryFeatures(luxury_level=LuxuryLevel.HIGH_END_LUXURY, luxury_score=8.5, confidence=0.9)
    condition = ConditionScore(condition=PropertyCondition.EXCELLENT, condition_score=9.0, confidence=0.9)
    style = StyleClassification(primary_style=PropertyStyle.MODERN, design_coherence=8.0, style_confidence=0.9)

    appeal = vision_analyzer._calculate_overall_appeal(luxury, condition, style)

    assert 0 <= appeal <= 10
    assert appeal > 8.0  # High scores should yield high appeal


def test_target_market_determination(vision_analyzer):
    """Test target market segment determination"""
    # Luxury property
    luxury_high = LuxuryFeatures(luxury_level=LuxuryLevel.ULTRA_LUXURY, luxury_score=9.5, confidence=0.9)
    features_basic = FeatureExtraction()

    market = vision_analyzer._determine_target_market(luxury_high, features_basic)
    assert market == "luxury_buyers"

    # Active lifestyle property
    luxury_mid = LuxuryFeatures(luxury_level=LuxuryLevel.UPPER_MIDRANGE, luxury_score=7.5, confidence=0.9)
    features_active = FeatureExtraction(has_pool=True, has_gym=True)

    market = vision_analyzer._determine_target_market(luxury_mid, features_active)
    assert market == "active_lifestyle_buyers"


def test_value_tier_estimation(vision_analyzer):
    """Test value tier estimation"""
    test_cases = [
        (9.0, 9.5, "premium"),
        (7.5, 7.0, "high"),
        (5.5, 5.0, "mid"),
        (3.5, 3.0, "moderate"),
        (1.5, 2.0, "entry"),
    ]

    for luxury_score, condition_score, expected_tier in test_cases:
        luxury = LuxuryFeatures(luxury_level=LuxuryLevel.MIDRANGE, luxury_score=luxury_score, confidence=0.9)
        condition = ConditionScore(condition=PropertyCondition.GOOD, condition_score=condition_score, confidence=0.9)

        tier = vision_analyzer._estimate_value_tier(luxury, condition)
        assert tier == expected_tier


def test_marketing_highlights_generation(vision_analyzer):
    """Test marketing highlights generation"""
    luxury = LuxuryFeatures(
        luxury_level=LuxuryLevel.HIGH_END_LUXURY,
        luxury_score=8.5,
        premium_materials=["Italian marble", "Hardwood", "Granite"],
        confidence=0.9,
    )

    features = FeatureExtraction(
        has_pool=True,
        pool_type="infinity",
        has_outdoor_kitchen=True,
        view_type="ocean",
    )

    style = StyleClassification(
        primary_style=PropertyStyle.MODERN,
        design_coherence=9.0,
        style_confidence=0.9,
    )

    highlights = vision_analyzer._generate_marketing_highlights(luxury, features, style)

    assert len(highlights) <= 5
    assert len(highlights) > 0
    assert any("pool" in h.lower() or "ocean" in h.lower() for h in highlights)


# Test Convenience Functions

@pytest.mark.asyncio
async def test_convenience_function_analyze_property_images(mock_anthropic_client, sample_image_urls):
    """Test convenience function for property analysis"""
    with patch('ghl_real_estate_ai.services.claude_vision_analyzer.claude_vision_analyzer') as mock_analyzer:
        mock_analyzer._initialized = True
        mock_analyzer.analyze_property_images = AsyncMock(
            return_value=PropertyAnalysis(
                property_id="test",
                luxury_features=LuxuryFeatures(luxury_level=LuxuryLevel.MIDRANGE, luxury_score=5.0, confidence=0.8),
                condition_score=ConditionScore(condition=PropertyCondition.GOOD, condition_score=5.0, confidence=0.8),
                style_classification=StyleClassification(primary_style=PropertyStyle.MODERN, style_confidence=0.8),
                feature_extraction=FeatureExtraction(),
                images_analyzed=3,
            )
        )

        result = await analyze_property_images("test", sample_image_urls)

        assert result.property_id == "test"
        mock_analyzer.analyze_property_images.assert_called_once()


# Test Performance Metrics

@pytest.mark.asyncio
async def test_performance_metrics_tracking(vision_analyzer):
    """Test performance metrics are tracked correctly"""
    initial_count = vision_analyzer.total_analyses

    # Mock successful analysis
    import json
    vision_analyzer.client.messages.create = AsyncMock(
        return_value=Mock(content=[Mock(text=json.dumps({"luxury_score": 5.0}))])
    )

    await vision_analyzer.analyze_property_images(
        property_id="metrics_test",
        image_urls=["https://example.com/test.jpg"],
        use_cache=False,
    )

    assert vision_analyzer.total_analyses == initial_count + 1
    assert vision_analyzer.total_images_processed > 0


@pytest.mark.asyncio
async def test_get_performance_stats(vision_analyzer):
    """Test retrieving performance statistics"""
    stats = await vision_analyzer.get_performance_stats()

    assert "total_analyses" in stats
    assert "total_images_processed" in stats
    assert "avg_analysis_time_ms" in stats
    assert "cache_hit_rate" in stats
    assert "avg_images_per_property" in stats


# Integration Tests

@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_integration_with_real_api_key():
    """
    Integration test with real Anthropic API key (requires API key).
    Skipped in CI/CD without API key.
    """
    pytest.skip("Requires real ANTHROPIC_API_KEY - run manually for integration testing")

    # This test would use real API key for end-to-end validation
    analyzer = ClaudeVisionAnalyzer()
    await analyzer.initialize()

    # Test with real property images
    analysis = await analyzer.analyze_property_images(
        property_id="integration_test",
        image_urls=["https://example.com/real_property.jpg"],
    )

    assert analysis.processing_time_ms < 1500
    assert analysis.confidence > 0.7

    await analyzer.cleanup()


# Benchmark Tests

@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_benchmark_single_image_analysis(vision_analyzer):
    """Benchmark single image analysis performance"""
    import json

    vision_analyzer.client.messages.create = AsyncMock(
        return_value=Mock(content=[Mock(text=json.dumps({"luxury_score": 5.0}))])
    )

    times = []

    for i in range(10):
        start = time.time()
        await vision_analyzer.analyze_property_images(
            property_id=f"bench_{i}",
            image_urls=["https://example.com/test.jpg"],
            use_cache=False,
        )
        times.append((time.time() - start) * 1000)

    avg_time = sum(times) / len(times)
    p95_time = sorted(times)[int(len(times) * 0.95)]

    print(f"\nBenchmark Results:")
    print(f"  Average: {avg_time:.2f}ms")
    print(f"  P95: {p95_time:.2f}ms")
    print(f"  Min: {min(times):.2f}ms")
    print(f"  Max: {max(times):.2f}ms")

    # Verify performance targets
    assert avg_time < 1500, f"Average time {avg_time}ms exceeds 1500ms target"
    assert p95_time < 2000, f"P95 time {p95_time}ms exceeds 2000ms tolerance"
