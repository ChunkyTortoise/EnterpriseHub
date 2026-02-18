import pytest
pytestmark = pytest.mark.integration

"""Tests for multi-property comparison service."""

import pytest

from ghl_real_estate_ai.services.property_comparison import (

    ComparisonMatrix,
    PropertyComparator,
    RankedProperty,
)


@pytest.fixture
def comparator():
    return PropertyComparator()


@pytest.fixture
def sample_properties():
    return [
        {
            "address": "123 Oak St",
            "price": 599000,
            "bedrooms": 4,
            "bathrooms": 2,
            "sqft": 2200,
            "lot_size": 7500,
            "year_built": 2021,
            "features": ["pool", "garage"],
        },
        {
            "address": "456 Elm Dr",
            "price": 549000,
            "bedrooms": 3,
            "bathrooms": 2,
            "sqft": 2400,
            "lot_size": 8000,
            "year_built": 2015,
            "features": ["garage"],
        },
        {
            "address": "789 Pine Ln",
            "price": 575000,
            "bedrooms": 4,
            "bathrooms": 3,
            "sqft": 2100,
            "lot_size": 6500,
            "year_built": 1975,
            "features": ["pool", "fireplace"],
        },
    ]


@pytest.fixture
def buyer_preferences():
    return {
        "budget_min": 500000,
        "budget_max": 600000,
        "bedrooms": 4,
        "bathrooms": 2,
        "features": ["pool", "garage"],
    }


class TestPropertyComparator:
    """Tests for PropertyComparator."""

    def test_compare_ranks_by_fit_score(
        self, comparator, sample_properties, buyer_preferences
    ):
        """Higher fit properties should be ranked first."""
        matrix = comparator.compare(sample_properties, buyer_preferences)

        assert len(matrix.properties) == 3
        scores = [p.fit_score for p in matrix.properties]
        # Scores must be sorted descending
        assert scores == sorted(scores, reverse=True)
        # All scores in valid range
        for s in scores:
            assert 0.0 <= s <= 100.0

    def test_best_overall_selected_correctly(
        self, comparator, sample_properties, buyer_preferences
    ):
        """best_overall should be the property with the highest fit_score."""
        matrix = comparator.compare(sample_properties, buyer_preferences)

        assert matrix.best_overall is not None
        assert matrix.best_overall is matrix.properties[0]
        # Verify it truly has the highest score
        for prop in matrix.properties[1:]:
            assert matrix.best_overall.fit_score >= prop.fit_score

    def test_best_value_lowest_price_per_sqft(
        self, comparator, sample_properties, buyer_preferences
    ):
        """best_value should have the lowest price-per-sqft ratio."""
        matrix = comparator.compare(sample_properties, buyer_preferences)

        assert matrix.best_value is not None

        # Calculate expected best value
        best_ratio = float("inf")
        expected_best = None
        for prop_data in sample_properties:
            price = prop_data.get("price", 0)
            sqft = prop_data.get("sqft", 0)
            if price > 0 and sqft > 0:
                ratio = price / sqft
                if ratio < best_ratio:
                    best_ratio = ratio
                    expected_best = prop_data

        # 456 Elm Dr: 549000/2400 = 228.75 is the lowest
        assert matrix.best_value.property_data["address"] == expected_best["address"]
        assert expected_best["address"] == "456 Elm Dr"

    def test_closest_to_budget_calculation(
        self, comparator, sample_properties, buyer_preferences
    ):
        """closest_to_budget should be under but nearest to budget_max."""
        matrix = comparator.compare(sample_properties, buyer_preferences)

        assert matrix.closest_to_budget is not None
        budget_max = buyer_preferences["budget_max"]  # 600000

        # Must be at or under budget
        closest_price = matrix.closest_to_budget.property_data["price"]
        assert closest_price <= budget_max

        # Must be the highest price that's still under budget
        # All properties are under 600K, so the closest should be 599K (123 Oak St)
        assert matrix.closest_to_budget.property_data["address"] == "123 Oak St"

    def test_pros_cons_generated(
        self, comparator, buyer_preferences
    ):
        """Under-budget property should have pros; over-budget should have cons."""
        under_budget_prop = {
            "address": "100 Under Rd",
            "price": 550000,
            "bedrooms": 5,
            "bathrooms": 3,
            "sqft": 2000,
            "year_built": 2022,
            "features": ["pool"],
        }
        over_budget_prop = {
            "address": "200 Over Ave",
            "price": 650000,
            "bedrooms": 3,
            "bathrooms": 1,
            "sqft": 1800,
            "year_built": 1970,
            "features": [],
        }

        matrix = comparator.compare(
            [under_budget_prop, over_budget_prop], buyer_preferences
        )

        # Find each property in ranked list
        under_ranked = next(
            p for p in matrix.properties
            if p.property_data["address"] == "100 Under Rd"
        )
        over_ranked = next(
            p for p in matrix.properties
            if p.property_data["address"] == "200 Over Ave"
        )

        # Under-budget property should have pros
        assert len(under_ranked.pros) > 0
        assert any("under budget" in pro for pro in under_ranked.pros)
        assert any("Extra bedroom" in pro for pro in under_ranked.pros)
        assert any("Newer construction" in pro for pro in under_ranked.pros)

        # Over-budget property should have cons
        assert len(over_ranked.cons) > 0
        assert any("over budget" in con for con in over_ranked.cons)
        assert any("Fewer bedrooms" in con for con in over_ranked.cons)
        assert any("Older construction" in con for con in over_ranked.cons)

    def test_sms_summary_under_320_chars(
        self, comparator, sample_properties, buyer_preferences
    ):
        """SMS summary must be under 320 characters."""
        matrix = comparator.compare(sample_properties, buyer_preferences)
        summary = comparator.generate_summary(matrix)

        assert len(summary) <= 320
        assert "Top 3 matches:" in summary
        assert "Reply # for details!" in summary

    def test_single_property_comparison(self, comparator, buyer_preferences):
        """Comparison should work with just 1 property."""
        single = [
            {
                "address": "999 Solo Way",
                "price": 580000,
                "bedrooms": 4,
                "bathrooms": 2,
                "sqft": 2000,
                "year_built": 2018,
                "features": ["garage"],
            }
        ]

        matrix = comparator.compare(single, buyer_preferences)

        assert len(matrix.properties) == 1
        assert matrix.best_overall is not None
        assert matrix.best_value is not None
        assert matrix.closest_to_budget is not None
        assert matrix.best_overall is matrix.properties[0]
        assert matrix.properties[0].fit_score > 0

        # Summary should work too
        summary = comparator.generate_summary(matrix)
        assert "Top 1 matches:" in summary
        assert len(summary) <= 320

    def test_empty_properties_handled(self, comparator, buyer_preferences):
        """Empty list should return an empty ComparisonMatrix."""
        matrix = comparator.compare([], buyer_preferences)

        assert isinstance(matrix, ComparisonMatrix)
        assert len(matrix.properties) == 0
        assert matrix.best_overall is None
        assert matrix.best_value is None
        assert matrix.closest_to_budget is None

        # Summary should handle empty gracefully
        summary = comparator.generate_summary(matrix)
        assert "No properties to compare" in summary