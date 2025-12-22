"""
Tests for Marketing Analytics Hub module.

Comprehensive test suite covering:
- ROI and ROAS calculations
- Customer metrics (CAC, CLV, CLV:CAC)
- A/B test significance analysis
- Attribution modeling (4 models)
- Sample data generation
- Report generation
"""

import pytest
import pandas as pd
import numpy as np

# Set random seed for deterministic test results
np.random.seed(42)


class TestROICalculations:
    """Test ROI and ROAS calculation functionality."""

    def test_roi_profitable_campaign(self):
        """Test ROI calculation for profitable campaign."""
        spend = 5000
        revenue = 15000
        expected_roi = ((revenue - spend) / spend) * 100  # 200%

        roi = ((revenue - spend) / spend) * 100

        assert roi == expected_roi
        assert roi == 200.0

    def test_roi_unprofitable_campaign(self):
        """Test ROI calculation for unprofitable campaign."""
        spend = 10000
        revenue = 5000
        expected_roi = ((revenue - spend) / spend) * 100  # -50%

        roi = ((revenue - spend) / spend) * 100

        assert roi == expected_roi
        assert roi == -50.0

    def test_roi_breakeven_campaign(self):
        """Test ROI calculation for break-even campaign."""
        spend = 5000
        revenue = 5000
        expected_roi = 0.0

        roi = ((revenue - spend) / spend) * 100

        assert roi == expected_roi

    def test_roas_calculation(self):
        """Test ROAS (Return on Ad Spend) calculation."""
        spend = 5000
        revenue = 15000
        expected_roas = revenue / spend  # 3.0x

        roas = revenue / spend

        assert roas == expected_roas
        assert roas == 3.0

    def test_cpa_calculation(self):
        """Test Cost Per Acquisition calculation."""
        spend = 5000
        customers = 50
        expected_cpa = spend / customers  # $100

        cpa = spend / customers

        assert cpa == expected_cpa
        assert cpa == 100.0

    def test_zero_spend_edge_case(self):
        """Test ROI calculation with zero spend (edge case)."""
        spend = 0
        revenue = 1000

        # Should handle division by zero gracefully
        roi = ((revenue - spend) / spend) * 100 if spend > 0 else 0

        assert roi == 0

    def test_zero_customers_edge_case(self):
        """Test CPA calculation with zero customers (edge case)."""
        spend = 5000
        customers = 0

        # Should handle division by zero gracefully
        cpa = spend / customers if customers > 0 else 0

        assert cpa == 0


class TestCustomerMetrics:
    """Test customer acquisition and lifetime value metrics."""

    def test_cac_calculation(self):
        """Test Customer Acquisition Cost calculation."""
        marketing_spend = 10000
        sales_costs = 5000
        new_customers = 100
        expected_cac = (marketing_spend + sales_costs) / new_customers  # $150

        cac = (marketing_spend + sales_costs) / new_customers

        assert cac == expected_cac
        assert cac == 150.0

    def test_clv_calculation(self):
        """Test Customer Lifetime Value calculation."""
        avg_purchase_value = 100
        purchase_frequency = 4  # per year
        customer_lifespan = 3  # years
        profit_margin = 0.30  # 30%

        customer_value = avg_purchase_value * purchase_frequency
        expected_clv = customer_value * customer_lifespan * profit_margin

        clv = customer_value * customer_lifespan * profit_margin

        assert clv == expected_clv
        assert clv == 360.0  # $100 × 4 × 3 × 0.30

    def test_clv_cac_ratio_healthy(self):
        """Test CLV:CAC ratio for healthy business (≥3:1)."""
        clv = 450
        cac = 50
        expected_ratio = 9.0  # Healthy

        ratio = clv / cac

        assert ratio == expected_ratio
        assert ratio >= 3.0  # Healthy threshold

    def test_clv_cac_ratio_acceptable(self):
        """Test CLV:CAC ratio for acceptable business (1-3:1)."""
        clv = 150
        cac = 75
        expected_ratio = 2.0  # Acceptable

        ratio = clv / cac

        assert ratio == expected_ratio
        assert 1.0 <= ratio < 3.0  # Acceptable range

    def test_clv_cac_ratio_poor(self):
        """Test CLV:CAC ratio for poor business (<1:1)."""
        clv = 50
        cac = 100
        expected_ratio = 0.5  # Poor

        ratio = clv / cac

        assert ratio == expected_ratio
        assert ratio < 1.0  # Poor threshold


class TestABTestSignificance:
    """Test A/B test statistical significance calculations."""

    def test_ab_test_significant_win(self):
        """Test A/B test with significant winner."""
        from modules.marketing_analytics import _calculate_ab_test_significance

        visitors_a = 5000
        conversions_a = 250  # 5%
        visitors_b = 5000
        conversions_b = 350  # 7%

        result = _calculate_ab_test_significance(
            visitors_a, conversions_a, visitors_b, conversions_b
        )

        assert result["lift"] > 0  # B is better than A
        assert result["p_value"] < 0.05  # Statistically significant
        assert result["significant"] is True

    def test_ab_test_significant_loss(self):
        """Test A/B test with significant loser."""
        from modules.marketing_analytics import _calculate_ab_test_significance

        visitors_a = 5000
        conversions_a = 350  # 7%
        visitors_b = 5000
        conversions_b = 250  # 5%

        result = _calculate_ab_test_significance(
            visitors_a, conversions_a, visitors_b, conversions_b
        )

        assert result["lift"] < 0  # B is worse than A
        assert result["p_value"] < 0.05  # Statistically significant
        assert result["significant"] is True

    def test_ab_test_not_significant(self):
        """Test A/B test with no significant difference."""
        from modules.marketing_analytics import _calculate_ab_test_significance

        visitors_a = 1000
        conversions_a = 50
        visitors_b = 1000
        conversions_b = 52  # Very small difference

        result = _calculate_ab_test_significance(
            visitors_a, conversions_a, visitors_b, conversions_b
        )

        assert result["p_value"] > 0.05  # Not significant
        assert result["significant"] is False

    def test_ab_test_small_sample_size(self):
        """Test A/B test with small sample size."""
        from modules.marketing_analytics import _calculate_ab_test_significance

        visitors_a = 10
        conversions_a = 2
        visitors_b = 10
        conversions_b = 3

        # Should still calculate, but likely not significant
        result = _calculate_ab_test_significance(
            visitors_a, conversions_a, visitors_b, conversions_b
        )

        assert "lift" in result
        assert "p_value" in result
        assert "significant" in result

    def test_ab_test_zero_conversions(self):
        """Test A/B test with zero conversions (edge case)."""
        from modules.marketing_analytics import _calculate_ab_test_significance

        visitors_a = 1000
        conversions_a = 0
        visitors_b = 1000
        conversions_b = 0

        result = _calculate_ab_test_significance(
            visitors_a, conversions_a, visitors_b, conversions_b
        )

        assert result["lift"] == 0
        assert "p_value" in result

    def test_required_sample_size_calculation(self):
        """Test sample size calculation for A/B test."""
        from modules.marketing_analytics import _calculate_required_sample_size

        baseline_rate = 0.05  # 5% conversion
        mde = 0.01  # Detect 1 percentage point difference
        confidence = 0.95
        power = 0.8

        sample_size = _calculate_required_sample_size(baseline_rate, mde, confidence, power)

        assert sample_size > 0
        assert isinstance(sample_size, int)
        assert sample_size >= 30  # Should be at least minimum


class TestAttributionModeling:
    """Test marketing attribution calculations."""

    @pytest.fixture
    def sample_journey(self):
        """Create sample customer journey data."""
        return pd.DataFrame(
            {
                "Customer": ["Customer 1"] * 5,
                "Step": [1, 2, 3, 4, 5],
                "Touchpoint": ["Social Ad", "Website", "Email", "Retarget", "Direct"],
                "Channel": ["Social Media", "Organic", "Email", "Paid Ads", "Direct"],
                "Days Since First Touch": [0, 2, 5, 7, 10],
                "Converted": [False, False, False, False, True],
            }
        )

    def test_first_touch_attribution(self, sample_journey):
        """Test First-Touch attribution model."""
        from modules.marketing_analytics import _calculate_attribution

        result = _calculate_attribution(sample_journey, "First-Touch")

        # First channel (Social Media) should get 100% credit
        social_row = result[result["channel"] == "Social Media"]
        assert len(social_row) > 0
        assert social_row.iloc[0]["credit"] == 1.0

        # Other channels should get 0% credit
        other_channels = result[result["channel"] != "Social Media"]
        assert all(other_channels["credit"] == 0.0)

    def test_last_touch_attribution(self, sample_journey):
        """Test Last-Touch attribution model."""
        from modules.marketing_analytics import _calculate_attribution

        result = _calculate_attribution(sample_journey, "Last-Touch")

        # Last channel (Direct) should get 100% credit
        direct_row = result[result["channel"] == "Direct"]
        assert len(direct_row) > 0
        assert direct_row.iloc[0]["credit"] == 1.0

        # Other channels should get 0% credit
        other_channels = result[result["channel"] != "Direct"]
        assert all(other_channels["credit"] == 0.0)

    def test_linear_attribution(self, sample_journey):
        """Test Linear attribution model."""
        from modules.marketing_analytics import _calculate_attribution

        result = _calculate_attribution(sample_journey, "Linear")

        # Each touchpoint should get equal credit
        # 5 touchpoints = 0.2 credit each (assuming unique channels)
        total_credit = result["credit"].sum()
        assert abs(total_credit - 1.0) < 0.01  # Should sum to 1.0

    def test_time_decay_attribution(self, sample_journey):
        """Test Time-Decay attribution model."""
        from modules.marketing_analytics import _calculate_attribution

        result = _calculate_attribution(sample_journey, "Time-Decay")

        # More recent touchpoints should get more credit
        # Last touchpoint should have highest credit
        total_credit = result["credit"].sum()
        assert abs(total_credit - 1.0) < 0.01  # Should sum to 1.0

        # Verify credit is distributed (no single channel gets 100%)
        max_credit = result["credit"].max()
        assert max_credit < 1.0

    def test_attribution_all_models_sum_to_one(self, sample_journey):
        """Test that all attribution models sum to 1.0."""
        from modules.marketing_analytics import (
            _calculate_attribution,
            ATTRIBUTION_MODELS,
        )

        for model in ATTRIBUTION_MODELS:
            result = _calculate_attribution(sample_journey, model)
            total_credit = result["credit"].sum()
            msg = f"{model} credits should sum to 1.0"
            assert abs(total_credit - 1.0) < 0.01, msg


class TestDataGeneration:
    """Test sample data generation functions."""

    def test_generate_campaign_data(self):
        """Test sample campaign data generation."""
        from modules.marketing_analytics import _get_sample_campaign_data

        df = _get_sample_campaign_data()

        assert len(df) > 0
        assert "campaign" in df.columns
        assert "channel" in df.columns
        assert "spend" in df.columns
        assert "revenue" in df.columns
        assert "conversions" in df.columns

    def test_generate_channel_breakdown(self):
        """Test channel breakdown data generation."""
        from modules.marketing_analytics import _get_channel_breakdown

        df = _get_channel_breakdown()

        assert len(df) > 0
        assert "channel" in df.columns
        assert "spend" in df.columns
        assert "revenue" in df.columns
        assert "conversions" in df.columns

    def test_generate_trend_data(self):
        """Test trend data generation."""
        from modules.marketing_analytics import _generate_trend_data

        dates = pd.date_range("2024-01-01", periods=30)
        channel = "Social Media"

        df = _generate_trend_data(dates, channel)

        assert len(df) == len(dates)
        assert "date" in df.columns
        assert "spend" in df.columns
        assert "revenue" in df.columns
        assert "conversion_rate" in df.columns

        # No negative values
        assert all(df["spend"] >= 0)
        assert all(df["revenue"] >= 0)

    def test_generate_cohort_data(self):
        """Test cohort retention data generation."""
        from modules.marketing_analytics import _generate_cohort_data

        df = _generate_cohort_data()

        assert len(df) > 0
        assert len(df.columns) > 0

        # First month retention should be 100%
        assert df.iloc[0, 0] == 100

        # Retention should decay over time (non-increasing)
        for i in range(len(df)):
            row_values = df.iloc[i].dropna().values
            if len(row_values) > 1:
                # Check that retention doesn't increase over time
                for j in range(len(row_values) - 1):
                    assert row_values[j] >= row_values[j + 1] or np.isnan(row_values[j + 1])

    def test_generate_journey_data(self):
        """Test customer journey data generation."""
        from modules.marketing_analytics import _get_sample_journey_data

        df = _get_sample_journey_data()

        assert len(df) > 0
        assert "Customer" in df.columns
        assert "Step" in df.columns
        assert "Touchpoint" in df.columns
        assert "Channel" in df.columns
        assert "Converted" in df.columns


class TestReportGeneration:
    """Test report generation functionality."""

    def test_generate_campaign_performance_report(self):
        """Test campaign performance report generation."""
        from modules.marketing_analytics import _generate_report_data
        from datetime import datetime, timedelta

        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()

        report = _generate_report_data("Campaign Performance", start_date, end_date)

        assert isinstance(report, pd.DataFrame)
        assert len(report) > 0

    def test_generate_customer_metrics_report(self):
        """Test customer metrics report generation."""
        from modules.marketing_analytics import _generate_report_data
        from datetime import datetime, timedelta

        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()

        report = _generate_report_data("Customer Metrics", start_date, end_date)

        assert isinstance(report, pd.DataFrame)
        assert len(report) > 0

    def test_generate_ab_test_report(self):
        """Test A/B test results report generation."""
        from modules.marketing_analytics import _generate_report_data
        from datetime import datetime, timedelta

        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()

        report = _generate_report_data("A/B Test Results", start_date, end_date)

        assert isinstance(report, pd.DataFrame)
        assert len(report) > 0

    def test_generate_attribution_report(self):
        """Test attribution analysis report generation."""
        from modules.marketing_analytics import _generate_report_data
        from datetime import datetime, timedelta

        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()

        report = _generate_report_data("Attribution Analysis", start_date, end_date)

        assert isinstance(report, pd.DataFrame)
        assert len(report) > 0


class TestModuleImports:
    """Test that module can be imported and has required functions."""

    def test_module_imports_successfully(self):
        """Test that marketing_analytics module can be imported."""
        import modules.marketing_analytics as ma

        assert ma is not None

    def test_render_function_exists(self):
        """Test that render function exists."""
        from modules.marketing_analytics import render

        assert callable(render)

    def test_required_functions_exist(self):
        """Test that all required functions are defined."""
        from modules import marketing_analytics

        required_functions = [
            "_calculate_ab_test_significance",
            "_calculate_attribution",
            "_calculate_required_sample_size",
            "_generate_cohort_data",
            "_get_sample_campaign_data",
            "_get_channel_breakdown",
            "_generate_trend_data",
            "_get_sample_journey_data",
            "_generate_report_data",
        ]

        for func_name in required_functions:
            assert hasattr(marketing_analytics, func_name), f"Missing function: {func_name}"
            assert callable(getattr(marketing_analytics, func_name))


class TestConstants:
    """Test module constants."""

    def test_constants_defined(self):
        """Test that required constants are defined."""
        from modules.marketing_analytics import (
            DEFAULT_CONFIDENCE_LEVEL,
            MIN_SAMPLE_SIZE,
            ATTRIBUTION_MODELS,
        )

        assert isinstance(DEFAULT_CONFIDENCE_LEVEL, float)
        assert 0.0 < DEFAULT_CONFIDENCE_LEVEL <= 1.0
        assert isinstance(MIN_SAMPLE_SIZE, int)
        assert MIN_SAMPLE_SIZE > 0
        assert isinstance(ATTRIBUTION_MODELS, list)
        assert len(ATTRIBUTION_MODELS) == 5

    def test_attribution_models_list(self):
        """Test attribution models constant."""
        from modules.marketing_analytics import ATTRIBUTION_MODELS

        expected_models = ["First-Touch", "Last-Touch", "Linear", "Time-Decay", "Position-Based"]
        assert ATTRIBUTION_MODELS == expected_models


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_calculate_channel_metrics_all_channels(self):
        """Test channel metrics calculation for 'All Channels'."""
        from modules.marketing_analytics import _calculate_channel_metrics

        metrics = _calculate_channel_metrics("All Channels")

        assert "spend" in metrics
        assert "revenue" in metrics
        assert "roi" in metrics
        assert "conversions" in metrics
        assert metrics["spend"] > 0
        assert metrics["revenue"] > 0

    def test_calculate_channel_metrics_specific_channel(self):
        """Test channel metrics calculation for specific channel."""
        from modules.marketing_analytics import _calculate_channel_metrics

        metrics = _calculate_channel_metrics("Social Media")

        assert "spend" in metrics
        assert "revenue" in metrics
        assert "roi" in metrics
        assert "conversions" in metrics

    def test_ab_test_with_100_percent_conversion(self):
        """Test A/B test with 100% conversion rate (edge case)."""
        from modules.marketing_analytics import _calculate_ab_test_significance

        visitors_a = 100
        conversions_a = 100
        visitors_b = 100
        conversions_b = 100

        result = _calculate_ab_test_significance(
            visitors_a, conversions_a, visitors_b, conversions_b
        )

        assert result["lift"] == 0
        assert "p_value" in result

    def test_attribution_single_touchpoint(self):
        """Test attribution with single touchpoint journey."""
        from modules.marketing_analytics import _calculate_attribution

        single_touch = pd.DataFrame(
            {
                "Customer": ["Customer 1"],
                "Step": [1],
                "Touchpoint": ["Direct"],
                "Channel": ["Direct"],
                "Days Since First Touch": [0],
                "Converted": [True],
            }
        )

        # All models should give 100% credit to the only touchpoint
        for model in ["First-Touch", "Last-Touch", "Linear", "Time-Decay"]:
            result = _calculate_attribution(single_touch, model)
            assert len(result) == 1
            assert result.iloc[0]["credit"] == 1.0

    def test_empty_campaign_data_handling(self):
        """Test handling of empty campaign data."""
        from modules.marketing_analytics import _calculate_channel_metrics

        # Should not crash with valid channel name
        try:
            metrics = _calculate_channel_metrics("Email")
            assert isinstance(metrics, dict)
        except Exception as e:
            pytest.fail(f"Failed to handle channel metrics: {str(e)}")

    def test_zero_variance_ab_test(self):
        """Test A/B test where both variants are identical."""
        from modules.marketing_analytics import _calculate_ab_test_significance

        visitors_a = 1000
        conversions_a = 50
        visitors_b = 1000
        conversions_b = 50  # Exact same as A

        result = _calculate_ab_test_significance(
            visitors_a, conversions_a, visitors_b, conversions_b
        )

        assert result["lift"] == 0
        assert result["significant"] is False


class TestMultiVariantTesting:
    """Test multi-variant testing with Chi-Square analysis."""

    def test_multivariant_three_variants(self):
        """Test multi-variant test with 3 variants."""
        from modules.marketing_analytics import _calculate_multivariant_significance

        variant_data = [
            {"name": "A", "visitors": 1000, "conversions": 50, "conv_rate": 5.0},
            {"name": "B", "visitors": 1000, "conversions": 60, "conv_rate": 6.0},
            {"name": "C", "visitors": 1000, "conversions": 70, "conv_rate": 7.0},
        ]

        result = _calculate_multivariant_significance(variant_data)

        assert "chi_square" in result
        assert "p_value" in result
        assert "degrees_of_freedom" in result
        assert "significant" in result
        assert "best_variant" in result
        assert result["best_variant"]["name"] == "C"
        assert result["best_variant"]["conv_rate"] == 7.0

    def test_multivariant_five_variants(self):
        """Test multi-variant test with 5 variants."""
        from modules.marketing_analytics import _calculate_multivariant_significance

        variant_data = [
            {"name": "A", "visitors": 5000, "conversions": 250, "conv_rate": 5.0},
            {"name": "B", "visitors": 5000, "conversions": 275, "conv_rate": 5.5},
            {"name": "C", "visitors": 5000, "conversions": 300, "conv_rate": 6.0},
            {"name": "D", "visitors": 5000, "conversions": 325, "conv_rate": 6.5},
            {"name": "E", "visitors": 5000, "conversions": 350, "conv_rate": 7.0},
        ]

        result = _calculate_multivariant_significance(variant_data)

        assert "chi_square" in result
        assert "p_value" in result
        assert result["best_variant"]["name"] == "E"
        assert result["best_variant"]["conv_rate"] == 7.0
        # With clear differences across 5 variants, should be significant
        assert result["significant"] is True

    def test_multivariant_ten_variants(self):
        """Test multi-variant test with 10 variants."""
        from modules.marketing_analytics import _calculate_multivariant_significance

        variant_data = []
        for i in range(10):
            variant_data.append(
                {
                    "name": chr(65 + i),  # A, B, C, ...
                    "visitors": 1000,
                    "conversions": 50 + i * 2,
                    "conv_rate": (50 + i * 2) / 10,
                }
            )

        result = _calculate_multivariant_significance(variant_data)

        assert "chi_square" in result
        assert "p_value" in result
        assert "best_variant" in result
        # Last variant (J) should have highest conversion rate
        assert result["best_variant"]["name"] == "J"

    def test_multivariant_significant_difference(self):
        """Test detection of significant differences."""
        from modules.marketing_analytics import _calculate_multivariant_significance

        # Large differences should be significant
        variant_data = [
            {"name": "A", "visitors": 1000, "conversions": 30, "conv_rate": 3.0},
            {"name": "B", "visitors": 1000, "conversions": 50, "conv_rate": 5.0},
            {"name": "C", "visitors": 1000, "conversions": 80, "conv_rate": 8.0},
        ]

        result = _calculate_multivariant_significance(variant_data)

        assert result["significant"] is True
        assert result["p_value"] < 0.05
        assert result["best_variant"]["name"] == "C"

    def test_multivariant_no_significant_difference(self):
        """Test when there's no significant difference."""
        from modules.marketing_analytics import _calculate_multivariant_significance

        # Very similar conversion rates
        variant_data = [
            {"name": "A", "visitors": 1000, "conversions": 50, "conv_rate": 5.0},
            {"name": "B", "visitors": 1000, "conversions": 51, "conv_rate": 5.1},
            {"name": "C", "visitors": 1000, "conversions": 52, "conv_rate": 5.2},
        ]

        result = _calculate_multivariant_significance(variant_data)

        # Small differences should not be significant
        assert result["p_value"] > 0.05
        assert result["significant"] is False

    def test_multivariant_best_variant_identification(self):
        """Test correct identification of best variant."""
        from modules.marketing_analytics import _calculate_multivariant_significance

        variant_data = [
            {"name": "A", "visitors": 1000, "conversions": 40, "conv_rate": 4.0},
            {"name": "B", "visitors": 1000, "conversions": 90, "conv_rate": 9.0},
            {"name": "C", "visitors": 1000, "conversions": 50, "conv_rate": 5.0},
        ]

        result = _calculate_multivariant_significance(variant_data)

        # B has the highest conversion rate
        assert result["best_variant"]["name"] == "B"
        assert result["best_variant"]["conv_rate"] == 9.0
        assert result["best_variant"]["conversions"] == 90

    def test_multivariant_all_same_conversion_rates(self):
        """Test edge case where all variants have identical conversion rates."""
        from modules.marketing_analytics import _calculate_multivariant_significance

        variant_data = [
            {"name": "A", "visitors": 1000, "conversions": 50, "conv_rate": 5.0},
            {"name": "B", "visitors": 1000, "conversions": 50, "conv_rate": 5.0},
            {"name": "C", "visitors": 1000, "conversions": 50, "conv_rate": 5.0},
            {"name": "D", "visitors": 1000, "conversions": 50, "conv_rate": 5.0},
        ]

        result = _calculate_multivariant_significance(variant_data)

        # No difference means not significant
        assert result["significant"] is False
        assert result["p_value"] > 0.05
        # All variants have same rate, any could be "best"
        assert result["best_variant"]["conv_rate"] == 5.0

    def test_multivariant_one_dominant_winner(self):
        """Test edge case with one clear dominant winner."""
        from modules.marketing_analytics import _calculate_multivariant_significance

        # One variant dramatically outperforms all others
        variant_data = [
            {"name": "A", "visitors": 1000, "conversions": 30, "conv_rate": 3.0},
            {"name": "B", "visitors": 1000, "conversions": 32, "conv_rate": 3.2},
            {"name": "C", "visitors": 1000, "conversions": 31, "conv_rate": 3.1},
            {"name": "D", "visitors": 1000, "conversions": 150, "conv_rate": 15.0},
        ]

        result = _calculate_multivariant_significance(variant_data)

        assert result["significant"] is True
        assert result["best_variant"]["name"] == "D"
        assert result["best_variant"]["conv_rate"] == 15.0
        assert result["p_value"] < 0.001  # Should be highly significant

    def test_multivariant_chi_square_statistic(self):
        """Test that chi-square statistic is calculated correctly."""
        from modules.marketing_analytics import _calculate_multivariant_significance

        variant_data = [
            {"name": "A", "visitors": 1000, "conversions": 50, "conv_rate": 5.0},
            {"name": "B", "visitors": 1000, "conversions": 60, "conv_rate": 6.0},
            {"name": "C", "visitors": 1000, "conversions": 70, "conv_rate": 7.0},
        ]

        result = _calculate_multivariant_significance(variant_data)

        # Chi-square statistic should be positive
        assert result["chi_square"] > 0
        # Degrees of freedom for 3 variants should be 2
        assert result["degrees_of_freedom"] == 2

    def test_multivariant_degrees_of_freedom(self):
        """Test degrees of freedom calculation for different variant counts."""
        from modules.marketing_analytics import _calculate_multivariant_significance

        # Test with 5 variants - should have 4 degrees of freedom
        variant_data = [
            {
                "name": f"Var{i}",
                "visitors": 1000,
                "conversions": 50 + i,
                "conv_rate": (50 + i) / 10,
            }
            for i in range(5)
        ]

        result = _calculate_multivariant_significance(variant_data)

        # DOF = (number of variants - 1)
        assert result["degrees_of_freedom"] == 4


class TestPositionBasedAttribution:
    """Test Position-Based attribution model."""

    def test_position_based_single_touchpoint(self):
        """Test Position-Based attribution with 1 touchpoint (should be 100%)."""
        from modules.marketing_analytics import _calculate_attribution

        journey_data = pd.DataFrame(
            {
                "Customer": ["Customer 1"],
                "Step": [1],
                "Touchpoint": ["Direct"],
                "Channel": ["Direct"],
                "Days Since First Touch": [0],
                "Converted": [True],
            }
        )

        result = _calculate_attribution(journey_data, "Position-Based")

        assert len(result) == 1
        assert result.iloc[0]["credit"] == 1.0
        # Total credit should sum to 1.0
        assert abs(result["credit"].sum() - 1.0) < 0.01

    def test_position_based_two_touchpoints(self):
        """Test Position-Based attribution with 2 touchpoints (50% each)."""
        from modules.marketing_analytics import _calculate_attribution

        journey_data = pd.DataFrame(
            {
                "Customer": ["Customer 1", "Customer 1"],
                "Step": [1, 2],
                "Touchpoint": ["Social Ad", "Direct"],
                "Channel": ["Social Media", "Direct"],
                "Days Since First Touch": [0, 5],
                "Converted": [False, True],
            }
        )

        result = _calculate_attribution(journey_data, "Position-Based")

        # Should have 2 channels
        assert len(result) == 2
        # Each should get 50% (0.5)
        assert all(result["credit"] == 0.5)
        # Total should sum to 1.0
        assert abs(result["credit"].sum() - 1.0) < 0.01

    def test_position_based_three_touchpoints(self):
        """Test Position-Based attribution with 3 touchpoints (40%-20%-40%)."""
        from modules.marketing_analytics import _calculate_attribution

        journey_data = pd.DataFrame(
            {
                "Customer": ["Customer 1", "Customer 1", "Customer 1"],
                "Step": [1, 2, 3],
                "Touchpoint": ["Social Ad", "Email", "Direct"],
                "Channel": ["Social Media", "Email", "Direct"],
                "Days Since First Touch": [0, 3, 7],
                "Converted": [False, False, True],
            }
        )

        result = _calculate_attribution(journey_data, "Position-Based")

        # Should have 3 channels
        assert len(result) == 3

        # Find each channel's credit
        social_credit = result[result["channel"] == "Social Media"]["credit"].values[0]
        email_credit = result[result["channel"] == "Email"]["credit"].values[0]
        direct_credit = result[result["channel"] == "Direct"]["credit"].values[0]

        # First touchpoint gets 40%
        assert abs(social_credit - 0.40) < 0.01
        # Middle touchpoint gets 20%
        assert abs(email_credit - 0.20) < 0.01
        # Last touchpoint gets 40%
        assert abs(direct_credit - 0.40) < 0.01

        # Total should sum to 1.0
        assert abs(result["credit"].sum() - 1.0) < 0.01

    def test_position_based_five_touchpoints(self):
        """Test Position-Based attribution with 5 touchpoints."""
        from modules.marketing_analytics import _calculate_attribution

        journey_data = pd.DataFrame(
            {
                "Customer": ["Customer 1"] * 5,
                "Step": [1, 2, 3, 4, 5],
                "Touchpoint": ["Social Ad", "Website", "Email", "Retarget", "Direct"],
                "Channel": ["Social Media", "Organic", "Email", "Paid Ads", "Direct"],
                "Days Since First Touch": [0, 2, 5, 7, 10],
                "Converted": [False, False, False, False, True],
            }
        )

        result = _calculate_attribution(journey_data, "Position-Based")

        # Should have 5 channels
        assert len(result) == 5

        # Get credits for each channel
        credits = {row["channel"]: row["credit"] for _, row in result.iterrows()}

        # First touchpoint (Social Media) gets 40%
        assert abs(credits["Social Media"] - 0.40) < 0.01

        # Last touchpoint (Direct) gets 40%
        assert abs(credits["Direct"] - 0.40) < 0.01

        # Middle 3 touchpoints share 20% equally (6.67% each)
        middle_credit = 0.20 / 3
        assert abs(credits["Organic"] - middle_credit) < 0.01
        assert abs(credits["Email"] - middle_credit) < 0.01
        assert abs(credits["Paid Ads"] - middle_credit) < 0.01

        # Total should sum to 1.0
        assert abs(result["credit"].sum() - 1.0) < 0.01

    def test_position_based_credits_sum_to_one(self):
        """Verify Position-Based credits always sum to 1.0."""
        from modules.marketing_analytics import _calculate_attribution

        # Test with various touchpoint counts
        for n_touchpoints in range(1, 11):
            journey_data = pd.DataFrame(
                {
                    "Customer": ["Customer 1"] * n_touchpoints,
                    "Step": list(range(1, n_touchpoints + 1)),
                    "Touchpoint": [f"Touch{i}" for i in range(1, n_touchpoints + 1)],
                    "Channel": [f"Channel{i}" for i in range(1, n_touchpoints + 1)],
                    "Days Since First Touch": list(range(n_touchpoints)),
                    "Converted": [False] * (n_touchpoints - 1) + [True],
                }
            )

            result = _calculate_attribution(journey_data, "Position-Based")

            # Credits should always sum to 1.0
            total_credit = result["credit"].sum()
            assert (
                abs(total_credit - 1.0) < 0.01
            ), f"Failed for {n_touchpoints} touchpoints: sum={total_credit}"

    def test_position_based_four_touchpoints(self):
        """Test Position-Based with 4 touchpoints for U-shaped distribution."""
        from modules.marketing_analytics import _calculate_attribution

        journey_data = pd.DataFrame(
            {
                "Customer": ["Customer 1"] * 4,
                "Step": [1, 2, 3, 4],
                "Touchpoint": ["Social", "Website", "Email", "Direct"],
                "Channel": ["Social Media", "Organic", "Email", "Direct"],
                "Days Since First Touch": [0, 2, 5, 8],
                "Converted": [False, False, False, True],
            }
        )

        result = _calculate_attribution(journey_data, "Position-Based")

        assert len(result) == 4

        credits = {row["channel"]: row["credit"] for _, row in result.iterrows()}

        # First gets 40%
        assert abs(credits["Social Media"] - 0.40) < 0.01
        # Last gets 40%
        assert abs(credits["Direct"] - 0.40) < 0.01
        # Middle 2 share 20% (10% each)
        assert abs(credits["Organic"] - 0.10) < 0.01
        assert abs(credits["Email"] - 0.10) < 0.01

        assert abs(result["credit"].sum() - 1.0) < 0.01

    def test_position_based_duplicate_channels(self):
        """Test Position-Based with duplicate channels in journey."""
        from modules.marketing_analytics import _calculate_attribution

        journey_data = pd.DataFrame(
            {
                "Customer": ["Customer 1"] * 5,
                "Step": [1, 2, 3, 4, 5],
                "Touchpoint": [
                    "Social Ad 1",
                    "Email 1",
                    "Social Ad 2",
                    "Email 2",
                    "Direct",
                ],
                "Channel": ["Social Media", "Email", "Social Media", "Email", "Direct"],
                "Days Since First Touch": [0, 2, 4, 6, 8],
                "Converted": [False, False, False, False, True],
            }
        )

        result = _calculate_attribution(journey_data, "Position-Based")

        # Social Media appears in positions 1 and 3 (first + middle)
        # Email appears in positions 2 and 4 (middle + middle)
        # Direct appears in position 5 (last)

        credits = {row["channel"]: row["credit"] for _, row in result.iterrows()}

        # Social Media: 40% (first) + 1/3 * 20% (middle) = 40% + 6.67% = 46.67%
        expected_social = 0.40 + (0.20 / 3)
        assert abs(credits["Social Media"] - expected_social) < 0.01

        # Email: 1/3 * 20% (middle) + 1/3 * 20% (middle) = 13.33%
        expected_email = 2 * (0.20 / 3)
        assert abs(credits["Email"] - expected_email) < 0.01

        # Direct: 40% (last)
        assert abs(credits["Direct"] - 0.40) < 0.01

        # Total should sum to 1.0
        assert abs(result["credit"].sum() - 1.0) < 0.01

    def test_position_based_vs_other_models(self):
        """Test that Position-Based produces different results than other models."""
        from modules.marketing_analytics import _calculate_attribution

        journey_data = pd.DataFrame(
            {
                "Customer": ["Customer 1"] * 5,
                "Step": [1, 2, 3, 4, 5],
                "Touchpoint": ["Social", "Web", "Email", "Retarget", "Direct"],
                "Channel": ["Social Media", "Organic", "Email", "Paid Ads", "Direct"],
                "Days Since First Touch": [0, 2, 5, 7, 10],
                "Converted": [False, False, False, False, True],
            }
        )

        position_based = _calculate_attribution(journey_data, "Position-Based")
        linear = _calculate_attribution(journey_data, "Linear")
        first_touch = _calculate_attribution(journey_data, "First-Touch")

        # Position-Based should differ from Linear (not equal distribution)
        position_social = position_based[position_based["channel"] == "Social Media"][
            "credit"
        ].values[0]
        linear_social = linear[linear["channel"] == "Social Media"]["credit"].values[0]
        assert abs(position_social - linear_social) > 0.01

        # Position-Based should differ from First-Touch
        # (first touch gives 40% not 100% when there are multiple touchpoints)
        first_touch_social = first_touch[first_touch["channel"] == "Social Media"]["credit"].values[
            0
        ]
        assert abs(position_social - first_touch_social) > 0.01
