"""
Tests for Seller Acceptance Feature Extraction Pipeline.

Validates:
- Feature extraction accuracy
- Normalization to [0, 1] range
- Missing value handling
- Performance targets (<500ms)
- Edge cases and error handling
"""

import time
from datetime import datetime

import numpy as np
import pytest

from ghl_real_estate_ai.ml.seller_acceptance_features import (
    SellerAcceptanceFeatureExtractor,
    SellerAcceptanceFeatures,
)


class TestSellerAcceptanceFeatures:
    """Test the SellerAcceptanceFeatures dataclass."""

    def test_feature_vector_length(self):
        """Feature vector should contain exactly 20 features."""
        features = SellerAcceptanceFeatures()
        vector = features.to_feature_vector()

        assert len(vector) == 20, "Expected 20 features"
        assert len(features.feature_names()) == 20, "Expected 20 feature names"

    def test_feature_names_match_vector(self):
        """Feature names should match vector ordering."""
        features = SellerAcceptanceFeatures(
            psychological_commitment_score=0.8,
            urgency_score=0.9,
            list_price_ratio=0.95,
        )

        vector = features.to_feature_vector()
        names = features.feature_names()

        assert names[0] == "psychological_commitment_score"
        assert vector[0] == 0.8

        assert names[1] == "urgency_score"
        assert vector[1] == 0.9

        assert names[5] == "list_price_ratio"
        assert vector[5] == 0.95

    def test_default_values_normalized(self):
        """Default feature values should be in [0, 1] range."""
        features = SellerAcceptanceFeatures()
        vector = features.to_feature_vector()

        for i, value in enumerate(vector):
            assert 0.0 <= value <= 1.0, f"Feature {i} ({features.feature_names()[i]}) out of range: {value}"


class TestSellerAcceptanceFeatureExtractor:
    """Test the SellerAcceptanceFeatureExtractor."""

    @pytest.fixture
    def extractor(self):
        """Create a feature extractor instance."""
        return SellerAcceptanceFeatureExtractor()

    @pytest.fixture
    def sample_property_data(self):
        """Sample property data for testing."""
        return {
            "list_price": 650000,
            "estimated_market_value": 625000,
            "beds": 4,
            "baths": 2.5,
            "sqft": 2200,
            "days_on_market": 45,
            "condition": "good",
            "price_drops": [
                {"percentage": 3.0, "date": "2026-01-15"},
                {"percentage": 2.0, "date": "2026-02-01"},
            ],
            "location": {
                "school_rating": 8,
                "walkability_score": 65,
            },
        }

    @pytest.fixture
    def sample_market_data(self):
        """Sample market data for testing."""
        return {
            "average_days_on_market": 30,
            "inventory_level": 4.5,
            "absorption_rate": 0.18,
            "price_trend_pct": 5.0,
            "current_month": 5,  # June (peak season)
            "estimated_value": 625000,
            "comparables": [
                {
                    "sale_price": 620000,
                    "days_on_market": 25,
                    "sqft": 2100,
                },
                {
                    "sale_price": 640000,
                    "days_on_market": 35,
                    "sqft": 2300,
                },
                {
                    "sale_price": 615000,
                    "days_on_market": 30,
                    "sqft": 2150,
                },
            ],
        }

    @pytest.fixture
    def sample_psychology_profile(self):
        """Sample psychology profile for testing."""
        return {
            "psychological_commitment_score": 75.0,
            "urgency_level": "high",
            "motivation_type": "relocation",
            "negotiation_flexibility": 0.7,
        }

    @pytest.fixture
    def sample_conversation_data(self):
        """Sample conversation data for testing."""
        return {
            "message_count": 25,
            "avg_response_time_seconds": 1800,  # 30 minutes
        }

    def test_extract_all_features(
        self,
        extractor,
        sample_property_data,
        sample_market_data,
        sample_psychology_profile,
        sample_conversation_data,
    ):
        """Test extraction of all 20 features."""
        features = extractor.extract_features(
            seller_id="test-seller-001",
            property_data=sample_property_data,
            market_data=sample_market_data,
            psychology_profile=sample_psychology_profile,
            conversation_data=sample_conversation_data,
        )

        # Verify all features are present
        vector = features.to_feature_vector()
        assert len(vector) == 20

        # Verify all features are normalized [0, 1]
        for i, value in enumerate(vector):
            assert 0.0 <= value <= 1.0, (
                f"Feature {i} ({features.feature_names()[i]}) out of range: {value}"
            )

        # Verify no missing fields when all data provided
        assert len(features.missing_fields) == 0

    def test_psychology_feature_extraction(
        self,
        extractor,
        sample_property_data,
        sample_market_data,
        sample_psychology_profile,
        sample_conversation_data,
    ):
        """Test seller psychology feature extraction."""
        features = extractor.extract_features(
            seller_id="test-seller-002",
            property_data=sample_property_data,
            market_data=sample_market_data,
            psychology_profile=sample_psychology_profile,
            conversation_data=sample_conversation_data,
        )

        # PCS should be normalized from 75/100 = 0.75
        assert features.psychological_commitment_score == 0.75

        # High urgency should map to 0.8
        assert features.urgency_score == 0.8

        # Relocation motivation should map to 0.8
        assert features.motivation_intensity == 0.8

        # Flexibility should be 0.7 (already normalized)
        assert features.negotiation_flexibility == 0.7

        # Communication engagement should be computed
        assert 0.0 < features.communication_engagement <= 1.0

    def test_pricing_feature_extraction(
        self,
        extractor,
        sample_property_data,
        sample_market_data,
    ):
        """Test pricing metrics feature extraction."""
        features = extractor.extract_features(
            seller_id="test-seller-003",
            property_data=sample_property_data,
            market_data=sample_market_data,
        )

        # List price ratio: 650k/625k = 1.04 (slightly overpriced)
        # Normalized: (1.04 - 0.8) / (1.2 - 0.8) = 0.6
        assert 0.5 < features.list_price_ratio < 0.7

        # Price reduction: 5% total
        assert 0.15 < features.price_reduction_history < 0.2

        # Days on market: 45/30 = 1.5x market average
        assert 0.4 < features.days_on_market_ratio < 0.6

        # Overpricing penalty: (1.04 - 1.0) * 5 = 0.2
        assert 0.15 < features.overpricing_penalty < 0.25

    def test_market_feature_extraction(
        self,
        extractor,
        sample_property_data,
        sample_market_data,
    ):
        """Test market context feature extraction."""
        features = extractor.extract_features(
            seller_id="test-seller-004",
            property_data=sample_property_data,
            market_data=sample_market_data,
        )

        # Inventory pressure: 4.5 months (moderate)
        # Normalized inverted: 1 - (4.5-2)/(12-2) = 0.75
        assert 0.7 < features.inventory_pressure < 0.8

        # Absorption rate: 0.18 (healthy market)
        assert 0.4 < features.absorption_rate < 0.6

        # Price trend: 5% (positive momentum)
        assert 0.5 < features.price_trend_momentum < 0.7

        # Seasonal factor: June = peak (1.0)
        assert features.seasonal_factor == 1.0

    def test_property_feature_extraction(
        self,
        extractor,
        sample_property_data,
        sample_market_data,
    ):
        """Test property characteristics feature extraction."""
        features = extractor.extract_features(
            seller_id="test-seller-005",
            property_data=sample_property_data,
            market_data=sample_market_data,
        )

        # Property appeal: 4 bed, 2.5 bath, 2200 sqft (excellent)
        assert features.property_appeal_score > 0.8

        # Condition: "good" = 0.8
        assert features.condition_score == 0.8

        # Location: school 8/10, walkability 65/100 = avg 0.725
        assert 0.7 < features.location_desirability < 0.8

    def test_comparable_feature_extraction(
        self,
        extractor,
        sample_property_data,
        sample_market_data,
    ):
        """Test comparables analysis feature extraction."""
        features = extractor.extract_features(
            seller_id="test-seller-006",
            property_data=sample_property_data,
            market_data=sample_market_data,
        )

        # Comp count: 3 comps
        assert 0.1 < features.comp_count_confidence < 0.2

        # Comp price variance: should be relatively low
        assert features.comp_price_variance > 0.8

        # Comp market time: avg ~30 days
        assert 0.7 < features.comp_market_time < 0.8

    def test_missing_psychology_data(
        self,
        extractor,
        sample_property_data,
        sample_market_data,
    ):
        """Test handling of missing psychology data."""
        features = extractor.extract_features(
            seller_id="test-seller-007",
            property_data=sample_property_data,
            market_data=sample_market_data,
            psychology_profile=None,
            conversation_data=None,
        )

        # Should use defaults
        assert features.psychological_commitment_score == 0.5
        assert features.urgency_score == 0.5
        assert features.motivation_intensity == 0.5
        assert features.negotiation_flexibility == 0.5
        assert features.communication_engagement == 0.5

        # Should track missing fields
        assert "psychology_profile" in features.missing_fields
        assert "conversation_data" in features.missing_fields

    def test_missing_comparables(
        self,
        extractor,
        sample_property_data,
    ):
        """Test handling of missing comparables data."""
        market_data_no_comps = {
            "average_days_on_market": 30,
            "inventory_level": 5.0,
            "absorption_rate": 0.15,
            "price_trend_pct": 3.0,
            "current_month": 4,
            "comparables": [],
        }

        features = extractor.extract_features(
            seller_id="test-seller-008",
            property_data=sample_property_data,
            market_data=market_data_no_comps,
        )

        # Should use defaults for comp features
        assert features.comp_count_confidence == 0.5
        assert features.comp_price_variance == 0.5
        assert features.comp_market_time == 0.5

        # Should track missing fields
        assert any("comp" in field for field in features.missing_fields)

    def test_performance_target(
        self,
        extractor,
        sample_property_data,
        sample_market_data,
        sample_psychology_profile,
        sample_conversation_data,
    ):
        """Test that extraction meets <500ms performance target."""
        start_time = time.perf_counter()

        features = extractor.extract_features(
            seller_id="test-seller-009",
            property_data=sample_property_data,
            market_data=sample_market_data,
            psychology_profile=sample_psychology_profile,
            conversation_data=sample_conversation_data,
        )

        extraction_time_ms = (time.perf_counter() - start_time) * 1000

        assert extraction_time_ms < 500, (
            f"Extraction took {extraction_time_ms:.2f}ms, exceeds 500ms target"
        )

        # Verify extraction time is recorded
        assert features.extraction_time_ms > 0
        assert features.extraction_time_ms < 500

    def test_normalization_edge_cases(self, extractor):
        """Test normalization with edge case values."""
        # Test at boundaries
        assert extractor._normalize_feature(0.0, 0.0, 1.0) == 0.0
        assert extractor._normalize_feature(1.0, 0.0, 1.0) == 1.0
        assert extractor._normalize_feature(0.5, 0.0, 1.0) == 0.5

        # Test clipping
        assert extractor._normalize_feature(-0.5, 0.0, 1.0, clip=True) == 0.0
        assert extractor._normalize_feature(1.5, 0.0, 1.0, clip=True) == 1.0

        # Test same min/max (should return 0.5)
        assert extractor._normalize_feature(5.0, 5.0, 5.0) == 0.5

    def test_extreme_property_values(self, extractor):
        """Test with extreme property values."""
        extreme_property = {
            "list_price": 10_000_000,  # Very expensive
            "estimated_market_value": 9_500_000,
            "beds": 10,  # Many beds
            "baths": 8.0,
            "sqft": 15000,  # Very large
            "days_on_market": 365,  # Long time
            "condition": "excellent",
            "price_drops": [],
            "location": {
                "school_rating": 10,
                "walkability_score": 100,
            },
        }

        market_data = {
            "average_days_on_market": 30,
            "inventory_level": 10.0,
            "absorption_rate": 0.05,
            "price_trend_pct": -5.0,
            "current_month": 11,  # December (low season)
            "comparables": [],
        }

        features = extractor.extract_features(
            seller_id="test-seller-010",
            property_data=extreme_property,
            market_data=market_data,
        )

        # All features should still be normalized
        vector = features.to_feature_vector()
        for i, value in enumerate(vector):
            assert 0.0 <= value <= 1.0, (
                f"Feature {i} ({features.feature_names()[i]}) out of range: {value}"
            )

    def test_urgency_level_mapping(self, extractor):
        """Test all urgency level mappings."""
        urgency_tests = [
            ("low", 0.2),
            ("medium", 0.5),
            ("high", 0.8),
            ("critical", 1.0),
            ("unknown", 0.5),  # Default
        ]

        for urgency_level, expected_score in urgency_tests:
            psychology = {
                "psychological_commitment_score": 50.0,
                "urgency_level": urgency_level,
                "motivation_type": "investment",
                "negotiation_flexibility": 0.5,
            }

            features = extractor.extract_features(
                seller_id=f"test-seller-{urgency_level}",
                property_data={"list_price": 500000, "beds": 3, "baths": 2, "sqft": 1500},
                market_data={"average_days_on_market": 30, "current_month": 5},
                psychology_profile=psychology,
            )

            assert features.urgency_score == expected_score, (
                f"Urgency level {urgency_level} should map to {expected_score}"
            )

    def test_motivation_type_mapping(self, extractor):
        """Test all motivation type mappings."""
        motivation_tests = [
            ("upsizing", 0.7),
            ("downsizing", 0.6),
            ("relocation", 0.8),
            ("financial", 0.9),
            ("divorce", 0.95),
            ("estate", 0.85),
            ("investment", 0.5),
            ("unknown", 0.5),  # Default
        ]

        for motivation_type, expected_score in motivation_tests:
            psychology = {
                "psychological_commitment_score": 50.0,
                "urgency_level": "medium",
                "motivation_type": motivation_type,
                "negotiation_flexibility": 0.5,
            }

            features = extractor.extract_features(
                seller_id=f"test-seller-{motivation_type}",
                property_data={"list_price": 500000, "beds": 3, "baths": 2, "sqft": 1500},
                market_data={"average_days_on_market": 30, "current_month": 5},
                psychology_profile=psychology,
            )

            assert features.motivation_intensity == expected_score, (
                f"Motivation type {motivation_type} should map to {expected_score}"
            )

    def test_seasonal_factors(self, extractor):
        """Test seasonal factor calculations for all months."""
        expected_factors = [
            0.4, 0.5, 0.7, 0.85, 0.95, 1.0,  # Jan-Jun
            1.0, 0.95, 0.85, 0.7, 0.5, 0.4   # Jul-Dec
        ]

        for month, expected_factor in enumerate(expected_factors):
            market_data = {
                "average_days_on_market": 30,
                "current_month": month,
            }

            features = extractor.extract_features(
                seller_id=f"test-seller-month-{month}",
                property_data={"list_price": 500000, "beds": 3, "baths": 2, "sqft": 1500},
                market_data=market_data,
            )

            assert features.seasonal_factor == expected_factor, (
                f"Month {month} should have seasonal factor {expected_factor}"
            )

    def test_statistics_tracking(
        self,
        extractor,
        sample_property_data,
        sample_market_data,
    ):
        """Test extraction statistics tracking."""
        # Perform multiple extractions
        for i in range(5):
            extractor.extract_features(
                seller_id=f"test-seller-stats-{i}",
                property_data=sample_property_data,
                market_data=sample_market_data,
            )

        stats = extractor.get_statistics()

        assert stats["total_extractions"] == 5
        assert stats["avg_extraction_time_ms"] > 0
        assert stats["avg_extraction_time_ms"] < 500  # Should meet target
        assert stats["target_time_ms"] == 500.0
        assert 0 < stats["performance_ratio"] < 1.0  # Should be under target

    def test_error_handling(self, extractor):
        """Test error handling with invalid data."""
        # Invalid property data (missing required fields)
        features = extractor.extract_features(
            seller_id="test-seller-error",
            property_data={},
            market_data={},
        )

        # Should return features with defaults and record missing fields
        assert len(features.to_feature_vector()) == 20
        assert len(features.missing_fields) > 0
        assert features.extraction_time_ms > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
