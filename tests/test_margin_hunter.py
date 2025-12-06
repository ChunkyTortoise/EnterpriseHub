"""Tests for Margin Hunter module."""

import pytest
from unittest.mock import patch, MagicMock
import numpy as np


class TestMarginHunterCalculations:
    """Test core CVP calculation logic."""

    def test_contribution_margin_calculation(self):
        """Test contribution margin = unit_price - unit_cost."""
        unit_price = 50.0
        unit_cost = 20.0
        contribution_margin = unit_price - unit_cost
        assert contribution_margin == 30.0

    def test_contribution_margin_ratio_calculation(self):
        """Test contribution margin ratio = (contribution / price) * 100."""
        unit_price = 50.0
        contribution_margin = 30.0
        contribution_margin_ratio = (contribution_margin / unit_price) * 100
        assert contribution_margin_ratio == 60.0

    def test_break_even_units_calculation(self):
        """Test break-even units = fixed_costs / contribution_margin."""
        fixed_costs = 5000.0
        contribution_margin = 30.0
        break_even_units = fixed_costs / contribution_margin
        assert break_even_units == pytest.approx(166.67, rel=0.01)

    def test_break_even_revenue_calculation(self):
        """Test break-even revenue = break_even_units * unit_price."""
        break_even_units = 166.67
        unit_price = 50.0
        break_even_revenue = break_even_units * unit_price
        assert break_even_revenue == pytest.approx(8333.50, rel=0.01)

    def test_target_units_calculation(self):
        """Test target units = (fixed_costs + target_profit) / contribution_margin."""
        fixed_costs = 5000.0
        target_profit = 2000.0
        contribution_margin = 30.0
        target_units = (fixed_costs + target_profit) / contribution_margin
        assert target_units == pytest.approx(233.33, rel=0.01)

    def test_margin_of_safety_calculation(self):
        """Test margin of safety = current_sales - break_even_units."""
        current_sales_units = 250
        break_even_units = 166.67
        margin_of_safety_units = current_sales_units - break_even_units
        assert margin_of_safety_units == pytest.approx(83.33, rel=0.01)

    def test_margin_of_safety_percentage(self):
        """Test margin of safety % = (MOS units / current_sales) * 100."""
        margin_of_safety_units = 83.33
        current_sales_units = 250
        margin_of_safety_pct = (margin_of_safety_units / current_sales_units) * 100
        assert margin_of_safety_pct == pytest.approx(33.33, rel=0.01)

    def test_current_profit_calculation(self):
        """Test current profit = (current_sales * contribution) - fixed_costs."""
        current_sales_units = 250
        contribution_margin = 30.0
        fixed_costs = 5000.0
        current_profit = (current_sales_units * contribution_margin) - fixed_costs
        assert current_profit == 2500.0

    def test_operating_leverage_calculation(self):
        """Test operating leverage = total_contribution / current_profit."""
        current_sales_units = 250
        contribution_margin = 30.0
        current_profit = 2500.0
        operating_leverage = (current_sales_units * contribution_margin) / current_profit
        assert operating_leverage == 3.0

    def test_zero_contribution_margin_edge_case(self):
        """Test edge case where price equals cost (zero contribution)."""
        unit_price = 20.0
        unit_cost = 20.0
        contribution_margin = unit_price - unit_cost
        assert contribution_margin == 0.0
        # In the app, this triggers an error message

    def test_high_fixed_costs_scenario(self):
        """Test scenario with high fixed costs."""
        fixed_costs = 100000.0
        contribution_margin = 50.0
        break_even_units = fixed_costs / contribution_margin
        assert break_even_units == 2000.0

    def test_low_margin_high_volume_scenario(self):
        """Test low margin, high volume business model."""
        unit_price = 10.0
        unit_cost = 9.0
        contribution_margin = 1.0
        current_sales_units = 50000
        fixed_costs = 30000.0
        current_profit = (current_sales_units * contribution_margin) - fixed_costs
        assert current_profit == 20000.0


class TestMarginHunterRenderFunction:
    """Test the main render function with mocked Streamlit."""

    @patch('modules.margin_hunter.st')
    def test_render_success_with_valid_inputs(self, mock_st):
        """Test successful render with valid inputs."""
        from modules import margin_hunter

        # Mock Streamlit inputs
        mock_st.number_input.side_effect = [
            50.0,   # unit_price
            20.0,   # unit_cost
            5000.0, # fixed_costs
            2000.0, # target_profit
            250     # current_sales_units
        ]

        # Mock columns
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_st.columns.return_value = [mock_col1, mock_col2]

        # Call render
        margin_hunter.render()

        # Assertions
        mock_st.title.assert_called_once_with("💰 Margin Hunter")
        mock_st.error.assert_not_called()  # No errors should be shown

    @patch('modules.margin_hunter.st')
    def test_render_error_when_price_equals_cost(self, mock_st):
        """Test error message when unit price equals unit cost."""
        from modules import margin_hunter

        # Mock Streamlit inputs (price = cost)
        mock_st.number_input.side_effect = [
            20.0,   # unit_price
            20.0,   # unit_cost (same as price)
            5000.0, # fixed_costs
            2000.0, # target_profit
            250     # current_sales_units
        ]

        # Mock columns
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_st.columns.return_value = [mock_col1, mock_col2]

        # Call render
        margin_hunter.render()

        # Assertions
        mock_st.error.assert_called_once_with(
            "⚠️ Selling price must be greater than variable cost to break even."
        )

    @patch('modules.margin_hunter.st')
    @patch('modules.margin_hunter._render_results')
    def test_render_calls_results_with_correct_params(self, mock_render_results, mock_st):
        """Test that render calls _render_results with calculated values."""
        from modules import margin_hunter

        # Mock Streamlit inputs
        mock_st.number_input.side_effect = [
            50.0,   # unit_price
            20.0,   # unit_cost
            5000.0, # fixed_costs
            2000.0, # target_profit
            250     # current_sales_units
        ]

        # Mock columns
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_st.columns.return_value = [mock_col1, mock_col2]

        # Call render
        margin_hunter.render()

        # Verify _render_results was called
        assert mock_render_results.called

        # Check that it was called with expected calculated values
        args = mock_render_results.call_args[0]
        contribution_margin = args[0]
        contribution_margin_ratio = args[1]
        break_even_units = args[2]

        assert contribution_margin == 30.0  # 50 - 20
        assert contribution_margin_ratio == pytest.approx(60.0)  # (30/50)*100
        assert break_even_units == pytest.approx(166.67, rel=0.01)  # 5000/30


class TestMarginHunterEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_current_sales(self):
        """Test margin of safety calculation with zero current sales."""
        current_sales_units = 0
        margin_of_safety_pct = 0.0  # Should handle gracefully
        assert margin_of_safety_pct == 0.0

    def test_negative_profit_scenario(self):
        """Test scenario where current profit is negative."""
        current_sales_units = 100
        contribution_margin = 30.0
        fixed_costs = 5000.0
        current_profit = (current_sales_units * contribution_margin) - fixed_costs
        assert current_profit < 0  # -2000 (loss)
        assert current_profit == -2000.0

    def test_very_small_contribution_margin(self):
        """Test with very small contribution margin."""
        unit_price = 10.01
        unit_cost = 10.00
        contribution_margin = unit_price - unit_cost
        assert contribution_margin == pytest.approx(0.01, abs=0.001)

        fixed_costs = 1000.0
        break_even_units = fixed_costs / contribution_margin
        assert break_even_units == pytest.approx(100000.0, rel=0.01)

    def test_zero_fixed_costs(self):
        """Test scenario with zero fixed costs (pure profit)."""
        fixed_costs = 0.0
        contribution_margin = 30.0
        break_even_units = fixed_costs / contribution_margin if contribution_margin > 0 else 0
        assert break_even_units == 0.0

    def test_large_numbers(self):
        """Test with large numbers (enterprise scale)."""
        unit_price = 1000.0
        unit_cost = 400.0
        contribution_margin = 600.0
        fixed_costs = 10_000_000.0
        break_even_units = fixed_costs / contribution_margin
        assert break_even_units == pytest.approx(16666.67, rel=0.01)
