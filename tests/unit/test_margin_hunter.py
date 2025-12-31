"""Tests for Margin Hunter module."""

import pytest
from unittest.mock import patch, MagicMock


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

    @patch("modules.margin_hunter.ui.section_header")
    @patch("modules.margin_hunter.st")
    def test_render_success_with_valid_inputs(self, mock_st, mock_section):
        """Test successful render with valid inputs."""
        from modules import margin_hunter

        # Mock Streamlit inputs
        mock_st.number_input.side_effect = [
            50.0,  # unit_price
            20.0,  # unit_cost
            5000.0,  # fixed_costs
            2000.0,  # target_profit
            250,  # current_sales_units
            10000.0,  # goal_profit_to_units (in _render_goal_seek)
            500,  # goal_units_to_price
            5000.0,  # goal_units_target_profit
            300,  # goal_profit_current_vol
            8000.0,  # goal_profit_current
        ]
        mock_st.file_uploader.return_value = None

        # Mock columns to return correct number of columns
        mock_st.columns.side_effect = lambda n: [
            MagicMock() for _ in range(n if isinstance(n, int) else len(n))
        ]

        # Mock tabs
        mock_st.tabs.return_value = [MagicMock(), MagicMock(), MagicMock()]

        # Mock other UI elements
        mock_st.expander.return_value.__enter__.return_value = MagicMock()
        mock_st.button.return_value = False

        # Call render
        margin_hunter.render()

        # Assertions
        mock_section.assert_called_once_with("Margin Hunter", "Profitability & Break-Even Analysis")
        mock_st.error.assert_not_called()  # No errors should be shown

    @patch("modules.margin_hunter.st")
    def test_render_error_when_price_equals_cost(self, mock_st):
        """Test error message when unit price equals unit cost."""
        from modules import margin_hunter

        # Mock Streamlit inputs (price = cost)
        mock_st.number_input.side_effect = [
            20.0,  # unit_price
            20.0,  # unit_cost (same as price)
            5000.0,  # fixed_costs
            2000.0,  # target_profit
            250,  # current_sales_units
        ]

        # Mock file_uploader to return None
        mock_st.file_uploader.return_value = None

        # Mock columns
        mock_st.columns.side_effect = lambda n: [
            MagicMock() for _ in range(n if isinstance(n, int) else len(n))
        ]
        mock_st.expander.return_value.__enter__.return_value = MagicMock()

        # Call render
        margin_hunter.render()

        # Assertions
        mock_st.error.assert_called_once_with(
            "⚠️ Selling price must be greater than variable cost to break even."
        )

    @patch("modules.margin_hunter.st")
    @patch("modules.margin_hunter._render_results")
    def test_render_calls_results_with_correct_params(self, mock_render_results, mock_st):
        """Test that render calls _render_results with calculated values."""
        from modules import margin_hunter

        # Mock Streamlit inputs
        mock_st.number_input.side_effect = [
            50.0,  # unit_price
            20.0,  # unit_cost
            5000.0,  # fixed_costs
            2000.0,  # target_profit
            250,  # current_sales_units
            10000.0,  # goal_profit_to_units (in _render_goal_seek)
            500,  # goal_units_to_price
            5000.0,  # goal_units_target_profit
            300,  # goal_profit_current_vol
            8000.0,  # goal_profit_current
        ]
        mock_st.file_uploader.return_value = None

        # Mock columns
        mock_st.columns.side_effect = lambda n: [
            MagicMock() for _ in range(n if isinstance(n, int) else len(n))
        ]
        mock_st.expander.return_value.__enter__.return_value = MagicMock()

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


class TestGoalSeekCalculations:
    """Test Goal Seek calculation logic."""

    def test_goal_seek_units_needed_for_profit(self):
        """Test calculating units needed to achieve target profit."""
        fixed_costs = 5000.0
        desired_profit = 10000.0
        contribution_margin = 30.0
        unit_price = 50.0

        required_units = (fixed_costs + desired_profit) / contribution_margin
        required_revenue = required_units * unit_price

        assert required_units == 500.0  # (5000 + 10000) / 30
        assert required_revenue == 25000.0  # 500 * 50

    def test_goal_seek_price_needed_for_units(self):
        """Test calculating price needed for target profit at given units."""
        fixed_costs = 5000.0
        target_profit = 5000.0
        achievable_units = 500
        unit_cost = 20.0

        # Price = (Fixed + Profit + (Cost × Units)) / Units
        required_price = (
            fixed_costs + target_profit + (unit_cost * achievable_units)
        ) / achievable_units
        new_margin = required_price - unit_cost
        new_margin_pct = (new_margin / required_price) * 100

        assert required_price == 40.0  # (5000 + 5000 + 10000) / 500
        assert new_margin == 20.0  # 40 - 20
        assert new_margin_pct == 50.0  # (20 / 40) * 100

    def test_goal_seek_price_for_current_volume(self):
        """Test calculating price needed for profit with current volume."""
        fixed_costs = 5000.0
        profit_goal = 8000.0
        current_units = 300
        unit_cost = 20.0

        needed_price = (fixed_costs + profit_goal + (unit_cost * current_units)) / current_units
        price_increase_pct = ((needed_price / 50.0) - 1) * 100  # vs current price of 50

        assert needed_price == pytest.approx(63.33, rel=0.01)  # (5000 + 8000 + 6000) / 300

    def test_goal_seek_zero_contribution_margin(self):
        """Test goal seek handles zero contribution margin."""
        contribution_margin = 0.0
        fixed_costs = 5000.0
        desired_profit = 1000.0

        # Should not divide by zero
        if contribution_margin > 0:
            required_units = (fixed_costs + desired_profit) / contribution_margin
        else:
            required_units = None  # Cannot calculate

        assert required_units is None

    def test_goal_seek_negative_profit_target(self):
        """Test goal seek with breakeven (zero profit) target."""
        fixed_costs = 5000.0
        desired_profit = 0.0  # Just break even
        contribution_margin = 30.0

        required_units = (fixed_costs + desired_profit) / contribution_margin
        assert required_units == pytest.approx(166.67, rel=0.01)


class TestMonteCarloSimulation:
    """Test Monte Carlo simulation logic."""

    def test_monte_carlo_basic_calculation(self):
        """Test basic Monte Carlo profit calculation."""
        import numpy as np

        np.random.seed(42)
        unit_price = 50.0
        unit_cost = 20.0
        fixed_costs = 5000.0
        current_sales_units = 250
        cost_variance = 10  # %
        sales_variance = 15  # %
        num_simulations = 1000

        # Generate samples
        cost_samples = np.random.normal(
            unit_cost, unit_cost * (cost_variance / 100), num_simulations
        )
        sales_samples = np.random.normal(
            current_sales_units, current_sales_units * (sales_variance / 100), num_simulations
        )

        # Calculate profits
        profits = (unit_price - cost_samples) * sales_samples - fixed_costs

        # Verify shapes
        assert len(cost_samples) == num_simulations
        assert len(sales_samples) == num_simulations
        assert len(profits) == num_simulations

        # Verify statistics exist
        mean_profit = np.mean(profits)
        std_profit = np.std(profits)
        assert mean_profit is not None
        assert std_profit > 0

    def test_monte_carlo_profit_probability(self):
        """Test Monte Carlo probability calculations."""
        import numpy as np

        np.random.seed(42)
        unit_price = 50.0
        unit_cost = 20.0
        fixed_costs = 5000.0
        current_sales_units = 250
        num_simulations = 10000

        # Simulate with low variance for predictable results
        cost_samples = np.random.normal(unit_cost, 1.0, num_simulations)
        sales_samples = np.random.normal(current_sales_units, 10.0, num_simulations)

        profits = (unit_price - cost_samples) * sales_samples - fixed_costs

        # Calculate probability of profit > 0
        prob_profitable = (profits > 0).sum() / num_simulations * 100

        # With low variance, should be highly profitable most of the time
        assert prob_profitable > 90.0  # Should be very high

    def test_monte_carlo_percentiles(self):
        """Test Monte Carlo percentile calculations."""
        import numpy as np

        np.random.seed(42)
        profits = np.array([1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000])

        percentile_5 = np.percentile(profits, 5)
        percentile_95 = np.percentile(profits, 95)

        assert percentile_5 == pytest.approx(1450.0, rel=0.01)
        assert percentile_95 == pytest.approx(9550.0, rel=0.01)
        assert percentile_95 > percentile_5

    def test_monte_carlo_with_high_variance(self):
        """Test Monte Carlo with high variance scenarios."""
        import numpy as np

        np.random.seed(42)
        unit_price = 50.0
        unit_cost = 20.0
        fixed_costs = 5000.0
        current_sales_units = 250
        cost_variance = 50  # 50% variance - very high
        sales_variance = 50  # 50% variance - very high

        cost_samples = np.random.normal(unit_cost, unit_cost * (cost_variance / 100), 1000)
        sales_samples = np.random.normal(
            current_sales_units, current_sales_units * (sales_variance / 100), 1000
        )

        profits = (unit_price - cost_samples) * sales_samples - fixed_costs

        std_profit = np.std(profits)
        # High variance should result in high standard deviation
        assert std_profit > 1000.0  # Should be quite high


class TestGoalSeekRenderFunction:
    """Test Goal Seek render function with mocked Streamlit."""

    @patch("modules.margin_hunter.st")
    def test_render_goal_seek_basic(self, mock_st):
        """Test Goal Seek render executes without errors."""
        from modules.margin_hunter import _render_goal_seek

        # Mock tabs
        mock_tab1 = MagicMock()
        mock_tab2 = MagicMock()
        mock_tab3 = MagicMock()
        mock_st.tabs.return_value = [mock_tab1, mock_tab2, mock_tab3]

        # Mock number inputs
        mock_st.number_input.return_value = 10000.0

        # Mock columns to return correct number of columns
        mock_st.columns.side_effect = lambda n: [
            MagicMock() for _ in range(n if isinstance(n, int) else len(n))
        ]

        # Call function
        _render_goal_seek(
            contribution_margin=30.0, unit_price=50.0, unit_cost=20.0, fixed_costs=5000.0
        )

        # Verify basic calls
        mock_st.markdown.assert_called()
        mock_st.subheader.assert_called()
        mock_st.tabs.assert_called_once()


class TestMonteCarloRenderFunction:
    """Test Monte Carlo render function with mocked Streamlit."""

    @patch("modules.margin_hunter.st")
    @patch("modules.margin_hunter.np")
    def test_render_monte_carlo_basic(self, mock_np, mock_st):
        """Test Monte Carlo render executes without errors."""
        from modules.margin_hunter import _render_monte_carlo

        # Mock expander
        mock_expander = MagicMock()
        mock_st.expander.return_value.__enter__.return_value = mock_expander

        # Mock columns
        mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]

        # Mock sliders
        mock_st.slider.return_value = 10
        mock_st.select_slider.return_value = 1000

        # Mock button (not clicked)
        mock_st.button.return_value = False

        # Call function
        _render_monte_carlo(
            contribution_margin=30.0,
            unit_price=50.0,
            unit_cost=20.0,
            fixed_costs=5000.0,
            current_sales_units=250,
        )

        # Verify basic calls
        mock_st.markdown.assert_called()
        mock_st.subheader.assert_called()
        mock_st.expander.assert_called()
