import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import utils.ui as ui
from modules.auth import delete_scenario, get_user_scenarios, save_scenario
from utils.logger import get_logger

logger = get_logger(__name__)


def render() -> None:
    """Render the Margin Hunter module."""
    ui.section_header("Margin Hunter", "Profitability & Break-Even Analysis")

    try:
        # Layout: Inputs on left, Results on right
        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader("⚙️ Parameters")

            with st.expander("Product Costs", expanded=True):
                unit_price = st.number_input(
                    "Unit Selling Price ($)",
                    value=st.session_state.get("mh_unit_price", 50.0),
                    step=1.0,
                    min_value=0.0,
                    key="mh_unit_price_input",
                )
                unit_cost = st.number_input(
                    "Unit Variable Cost ($)",
                    value=st.session_state.get("mh_unit_cost", 20.0),
                    step=1.0,
                    min_value=0.0,
                    key="mh_unit_cost_input",
                )

            with st.expander("Fixed Costs", expanded=True):
                fixed_costs = st.number_input(
                    "Total Fixed Costs ($)",
                    value=st.session_state.get("mh_fixed_costs", 5000.0),
                    step=100.0,
                    min_value=0.0,
                    key="mh_fixed_costs_input",
                )

            with st.expander("Targeting", expanded=True):
                target_profit = st.number_input(
                    "Target Profit ($)",
                    value=st.session_state.get("mh_target_profit", 2000.0),
                    step=100.0,
                    min_value=0.0,
                    key="mh_target_profit_input",
                )
                current_sales_units = st.number_input(
                    "Current Sales (Units)",
                    value=st.session_state.get("mh_current_sales_units", 250),
                    step=10,
                    min_value=0,
                    key="mh_current_sales_units_input",
                )

            # Update session state for next reload
            st.session_state.mh_unit_price = unit_price
            st.session_state.mh_unit_cost = unit_cost
            st.session_state.mh_fixed_costs = fixed_costs
            st.session_state.mh_target_profit = target_profit
            st.session_state.mh_current_sales_units = current_sales_units

            st.markdown("---")
            st.subheader("📁 Bulk Analysis")
            uploaded_file = st.file_uploader(
                "Upload Product List (CSV)",
                type=["csv"],
                help="Upload a CSV with columns: Product, Unit Price, Unit Cost, Fixed Cost",
            )

            if uploaded_file:
                try:
                    bulk_df = pd.read_csv(uploaded_file)
                    required = ["Product", "Unit Price", "Unit Cost"]
                    if all(col in bulk_df.columns for col in required):
                        st.success(f"✅ Loaded {len(bulk_df)} products.")
                        # Processing logic moved to results panel
                    else:
                        st.error(f"❌ CSV must contain columns: {', '.join(required)}")
                        bulk_df = None
                except Exception as e:
                    st.error(f"❌ Error reading CSV: {e}")
                    bulk_df = None
            else:
                bulk_df = None

        # Calculations (Single Product)
        # ... (keep existing single product logic)

        # Calculations
        contribution_margin = unit_price - unit_cost

        if contribution_margin <= 0:
            st.error("⚠️ Selling price must be greater than variable cost to break even.")
            # Stop execution if there's no contribution margin
            return

        contribution_margin_ratio = (
            (contribution_margin / unit_price) * 100 if unit_price > 0 else 0
        )
        break_even_units = fixed_costs / contribution_margin
        break_even_revenue = break_even_units * unit_price

        target_units = (fixed_costs + target_profit) / contribution_margin
        target_revenue = target_units * unit_price

        # Advanced Metrics
        margin_of_safety_units = current_sales_units - break_even_units
        margin_of_safety_pct = (
            (margin_of_safety_units / current_sales_units) * 100 if current_sales_units > 0 else 0
        )

        current_profit = (current_sales_units * contribution_margin) - fixed_costs
        operating_leverage = (
            (current_sales_units * contribution_margin) / current_profit
            if current_profit > 0
            else 0
        )

        with col2:
            if bulk_df is not None:
                _render_bulk_results(bulk_df, fixed_costs)
            else:
                _render_results(
                    contribution_margin,
                    contribution_margin_ratio,
                    break_even_units,
                    break_even_revenue,
                    margin_of_safety_pct,
                    margin_of_safety_units,
                    operating_leverage,
                    current_profit,
                    target_units,
                    current_sales_units,
                    unit_price,
                    unit_cost,
                    fixed_costs,
                    target_revenue,
                    target_profit,
                )

    except Exception as e:
        logger.error(f"An unexpected error occurred in Margin Hunter: {e}", exc_info=True)
        st.error("An unexpected error occurred during analysis.")
        if st.checkbox("Show error details", key="mh_error_details"):
            st.exception(e)


def _render_results(
    contribution_margin,
    contribution_margin_ratio,
    break_even_units,
    break_even_revenue,
    margin_of_safety_pct,
    margin_of_safety_units,
    operating_leverage,
    current_profit,
    target_units,
    current_sales_units,
    unit_price,
    unit_cost,
    fixed_costs,
    target_revenue,
    target_profit,
):
    """Render the results and visualizations panel."""
    st.markdown("### 📈 Analysis Results")

    # --- Key Metrics ---
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    with m1:
        ui.animated_metric("Break-even Units", f"{break_even_units:,.0f}", icon="🎯")
    with m2:
        ui.animated_metric("Break-even Revenue", f"${break_even_revenue:,.2f}", icon="💰")
    with m3:
        ui.animated_metric("Contr. Margin", f"${contribution_margin:.2f}", icon="📈")
    with m4:
        ui.animated_metric("Margin Safety %", f"{margin_of_safety_pct:.1f}%", icon="🛡️")
    with m5:
        ui.animated_metric("Op. Leverage", f"{operating_leverage:.2f}x", icon="⚡")
    with m6:
        ui.animated_metric("Current Profit", f"${current_profit:,.2f}", icon="💵")

    ui.spacer(30)
    # --- Executive Summary ---
    st.markdown(
        f"""
        <div style='background-color: {ui.THEME["surface"]}; border-left: 5px solid {ui.THEME["accent"]}; 
                    padding: 2rem; border-radius: 8px; border: 1px solid {ui.THEME["border"]}; border-left-width: 5px;'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;'>
                <h3 style='margin: 0; color: {ui.THEME["primary"]};'>📝 Consultant's Executive Summary</h3>
                {ui.status_badge("HEALTHY" if current_profit > target_profit else "ACTION REQUIRED")}
            </div>
            <p style='color: #334155; line-height: 1.6; font-size: 1.05rem;'>
                Based on current cost structures and sales volume, the business is operating 
                <strong>{margin_of_safety_pct:.1f}%</strong> above its break-even point. 
                The contribution margin of <strong>${contribution_margin:.2f}</strong> provides 
                sufficient coverage for fixed costs.
            </p>
            <hr style='border: 0; border-top: 1px solid {ui.THEME["border"]}; margin: 1.5rem 0;'>
            <p style='color: #475569; font-size: 0.95rem;'>
                <strong>Strategic Recommendation:</strong> To achieve your target profit of 
                <strong>${target_profit:,.2f}</strong>, an additional sales volume of 
                <strong>{int(np.ceil(target_units - current_sales_units)):,} units</strong> is required.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    ui.spacer(30)

    # --- CVP Visualization ---
    _render_cvp_chart(
        target_units,
        current_sales_units,
        break_even_units,
        unit_price,
        unit_cost,
        fixed_costs,
        break_even_revenue,
    )

    # --- Sensitivity Analysis ---
    _render_sensitivity_heatmap(unit_price, unit_cost, current_sales_units, fixed_costs)

    # --- Scenario Table & Export ---
    _render_scenario_table(
        break_even_units,
        break_even_revenue,
        current_sales_units,
        unit_price,
        current_profit,
        target_units,
        target_revenue,
        target_profit,
    )

    # --- Goal Seek ---
    _render_goal_seek(contribution_margin, unit_price, unit_cost, fixed_costs)

    # --- Monte Carlo Simulation ---
    _render_monte_carlo(
        contribution_margin, unit_price, unit_cost, fixed_costs, current_sales_units
    )

    # --- Persistence ---
    _render_save_load_section(
        unit_price, unit_cost, fixed_costs, target_profit, current_sales_units
    )


def _render_cvp_chart(
    target_units,
    current_sales_units,
    break_even_units,
    unit_price,
    unit_cost,
    fixed_costs,
    break_even_revenue,
):
    """Render the Cost-Volume-Profit (CVP) Analysis chart."""
    st.markdown("#### Cost-Volume-Profit (CVP) Analysis")
    max_units = max(
        int(target_units * 1.5),
        int(current_sales_units * 1.2),
        int(break_even_units * 2),
        100,
    )
    units_range = np.linspace(0, max_units, 100)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=units_range,
            y=units_range * unit_price,
            name="Revenue",
            line=dict(color="#00ff88", width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=units_range,
            y=fixed_costs + (units_range * unit_cost),
            name="Total Cost",
            line=dict(color="#ff4444", width=3),
            fill="tonexty",
            fillcolor="rgba(255, 68, 68, 0.1)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=units_range,
            y=[fixed_costs] * len(units_range),
            name="Fixed Costs",
            line=dict(color="#888888", dash="dash"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[break_even_units],
            y=[break_even_revenue],
            mode="markers",
            name="Break-Even Point",
            marker=dict(color="white", size=12, symbol="star"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[current_sales_units],
            y=[current_sales_units * unit_price],
            mode="markers",
            name="Current Sales",
            marker=dict(color="#00D9FF", size=10, symbol="circle"),
        )
    )

    fig.update_layout(
        title="Revenue vs Costs",
        xaxis_title="Units Sold",
        yaxis_title="Amount ($)",
        template=ui.get_plotly_template(),
        height=400,
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_sensitivity_heatmap(
    unit_price: float, unit_cost: float, current_sales_units: int, fixed_costs: float
) -> None:
    """Render the sensitivity analysis heatmap."""
    st.markdown("#### 🌡️ Sensitivity Heatmap: Net Profit")
    st.caption(
        "Impact of changing Unit Price vs Variable Cost on Net Profit (at current sales volume)"
    )

    price_range = np.linspace(unit_price * 0.8, unit_price * 1.2, 10)
    cost_range = np.linspace(unit_cost * 0.8, unit_cost * 1.2, 10)
    z_data = [
        [(p - c) * current_sales_units - fixed_costs for p in price_range] for c in cost_range
    ]

    colorscale = [
        [0, ui.THEME["danger"]],
        [0.5, ui.THEME["surface"]],
        [1, ui.THEME["success"]],
    ]

    fig_heat = go.Figure(
        data=go.Heatmap(
            z=z_data,
            x=[f"${p:.2f}" for p in price_range],
            y=[f"${c:.2f}" for c in cost_range],
            colorscale=colorscale,
            zmid=0,
            colorbar=dict(title="Net Profit ($)"),
        )
    )
    fig_heat.update_layout(
        title="Profit Sensitivity Matrix",
        xaxis_title="Unit Price ($)",
        yaxis_title="Variable Cost ($)",
        template=ui.get_plotly_template(),
        height=400,
    )
    st.plotly_chart(fig_heat, use_container_width=True)


def _render_scenario_table(
    break_even_units: float,
    break_even_revenue: float,
    current_sales_units: int,
    unit_price: float,
    current_profit: float,
    target_units: float,
    target_revenue: float,
    target_profit: float,
) -> None:
    """Render the scenario summary table and download button."""
    st.markdown("#### 🎯 Scenarios")
    scenarios = [
        {
            "Scenario": "Break-Even",
            "Units": break_even_units,
            "Revenue": break_even_revenue,
            "Profit": 0,
        },
        {
            "Scenario": "Current Status",
            "Units": current_sales_units,
            "Revenue": current_sales_units * unit_price,
            "Profit": current_profit,
        },
        {
            "Scenario": "Target Profit",
            "Units": target_units,
            "Revenue": target_revenue,
            "Profit": target_profit,
        },
    ]
    df_scenarios = pd.DataFrame(scenarios)

    df_display = df_scenarios.copy()
    df_display["Units"] = df_display["Units"].apply(lambda x: f"{int(np.ceil(x)):,}")
    df_display["Revenue"] = df_display["Revenue"].apply(lambda x: f"${x:,.2f}")
    df_display["Profit"] = df_display["Profit"].apply(lambda x: f"${x:,.2f}")

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    csv = df_scenarios.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Scenarios CSV",
        data=csv,
        file_name="margin_hunter_scenarios.csv",
        mime="text/csv",
    )


def _render_bulk_results(df: pd.DataFrame, global_fixed_costs: float):
    """Render the results for multiple products from a CSV upload."""
    st.subheader("📁 Bulk Analysis Results")

    # Calculate metrics for each product
    df["Contribution Margin"] = df["Unit Price"] - df["Unit Cost"]
    df["Margin %"] = (df["Contribution Margin"] / df["Unit Price"]) * 100

    # If Fixed Cost is not in CSV, use the global one from the slider
    if "Fixed Cost" not in df.columns:
        df["Fixed Cost"] = global_fixed_costs

    df["Break-Even Units"] = df["Fixed Cost"] / df["Contribution Margin"]
    df["Break-Even Revenue"] = df["Break-Even Units"] * df["Unit Price"]

    # Handle negative margins (use a very large number instead of inf for better DF display)
    df.loc[df["Contribution Margin"] <= 0, ["Break-Even Units", "Break-Even Revenue"]] = 999999

    # Metrics Summary
    avg_margin = df["Margin %"].mean()
    total_products = len(df)
    unprofitable = len(df[df["Contribution Margin"] <= 0])

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Products", total_products)
    c2.metric("Avg Margin %", f"{avg_margin:.1f}%")
    c3.metric("Unprofitable Items", unprofitable)

    if unprofitable > 0:
        st.warning(
            f"⚠️ {unprofitable} products have a negative or zero contribution margin "
            f"and will never break even."
        )

    # Sortable Table
    st.markdown("#### 📋 Product Mix Analysis")
    st.dataframe(
        df.sort_values("Margin %", ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Unit Price": st.column_config.NumberColumn(format="$%.2f"),
            "Unit Cost": st.column_config.NumberColumn(format="$%.2f"),
            "Fixed Cost": st.column_config.NumberColumn(format="$%.2f"),
            "Contribution Margin": st.column_config.NumberColumn(format="$%.2f"),
            "Margin %": st.column_config.NumberColumn(format="%.1f%%"),
            "Break-Even Units": st.column_config.NumberColumn(format="%d"),
            "Break-Even Revenue": st.column_config.NumberColumn(format="$%.2f"),
        },
    )

    # Visualization: Margin % by Product
    st.markdown("#### 📈 Margin Comparison")
    fig = go.Figure(
        go.Bar(
            x=df["Product"],
            y=df["Margin %"],
            marker_color=[
                ui.THEME["success"] if m > 0 else ui.THEME["danger"] for m in df["Margin %"]
            ],
        )
    )
    fig.update_layout(
        title="Contribution Margin % by Product",
        yaxis_title="Margin %",
        template=ui.get_plotly_template(),
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Export
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Full Bulk Analysis (CSV)",
        csv,
        "bulk_margin_analysis.csv",
        "text/csv",
        use_container_width=True,
    )


def _render_goal_seek(
    contribution_margin: float, unit_price: float, unit_cost: float, fixed_costs: float
):
    """
    Render Goal Seek calculator - reverse engineer required inputs to hit profit targets.

    Args:
        contribution_margin: Contribution margin per unit
        unit_price: Selling price per unit
        unit_cost: Variable cost per unit
        fixed_costs: Total fixed costs
    """
    st.markdown("---")
    st.subheader("🎯 Goal Seek: What Do I Need?")
    st.caption("Want a specific profit? Find out what price, volume, or costs you need.")

    goal_tab1, goal_tab2, goal_tab3 = st.tabs(
        [
            "💰 Target Profit → Units Needed",
            "📦 Target Units → Price Needed",
            "💵 Target Profit → Price Needed",
        ]
    )

    with goal_tab1:
        st.markdown("#### If I want to make $X profit, how many units do I need to sell?")
        desired_profit = st.number_input(
            "Desired Profit ($)",
            value=10000.0,
            step=1000.0,
            min_value=0.0,
            key="goal_profit_to_units",
        )

        if contribution_margin > 0:
            required_units = (fixed_costs + desired_profit) / contribution_margin
            required_revenue = required_units * unit_price

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Units Needed", f"{required_units:,.0f}")
            with col2:
                st.metric("Revenue Needed", f"${required_revenue:,.2f}")

            st.success(
                f"✅ Sell **{required_units:,.0f} units** at ${unit_price:.2f} each "
                f"to achieve ${desired_profit:,.2f} profit"
            )
        else:
            st.error("⚠️ Cannot calculate - contribution margin is zero or negative")

    with goal_tab2:
        st.markdown("#### If I can sell X units, what price do I need to charge?")
        achievable_units = st.number_input(
            "Units You Can Sell", value=500, step=50, min_value=1, key="goal_units_to_price"
        )
        target_profit_price = st.number_input(
            "Target Profit ($)",
            value=5000.0,
            step=500.0,
            min_value=0.0,
            key="goal_units_target_profit",
        )

        # Price = (Fixed Costs + Target Profit + (Variable Cost × Units)) / Units
        required_price = (
            fixed_costs + target_profit_price + (unit_cost * achievable_units)
        ) / achievable_units
        new_margin = required_price - unit_cost
        new_margin_pct = (new_margin / required_price) * 100 if required_price > 0 else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Required Price", f"${required_price:.2f}")
        with col2:
            delta_price = required_price - unit_price
            st.metric("vs Current Price", f"${unit_price:.2f}", delta=f"${delta_price:+.2f}")
        with col3:
            st.metric("New Margin %", f"{new_margin_pct:.1f}%")

        if required_price > unit_cost:
            st.success(
                f"✅ Charge **${required_price:.2f}** per unit to achieve "
                f"${target_profit_price:,.2f} profit on {achievable_units:,.0f} units"
            )
        else:
            st.error("⚠️ Required price is below or at variable cost - not profitable")

    with goal_tab3:
        st.markdown("#### If I want $X profit with current volumes, what price do I need?")
        current_units_goal = st.number_input(
            "Current Sales Volume", value=300, step=50, min_value=1, key="goal_profit_current_vol"
        )
        profit_goal_current = st.number_input(
            "Profit Goal ($)", value=8000.0, step=500.0, min_value=0.0, key="goal_profit_current"
        )

        # Same formula as tab 2
        needed_price = (
            fixed_costs + profit_goal_current + (unit_cost * current_units_goal)
        ) / current_units_goal
        price_increase = needed_price - unit_price
        price_increase_pct = (price_increase / unit_price) * 100 if unit_price > 0 else 0

        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Needed Price",
                f"${needed_price:.2f}",
                delta=f"{price_increase_pct:+.1f}% increase"
                if price_increase > 0
                else "No change needed",
            )
        with col2:
            st.metric("Price Change", f"${price_increase:+.2f}")

        if needed_price > unit_cost:
            if price_increase > 0:
                st.warning(
                    f"⚠️ You need to **increase price by ${price_increase:.2f}** "
                    f"({price_increase_pct:.1f}%) to hit your profit goal"
                )
            else:
                st.success("✅ Current pricing already achieves your profit goal!")
        else:
            st.error("⚠️ Required price is at or below variable cost - restructure costs instead")


def _render_monte_carlo(
    contribution_margin: float,
    unit_price: float,
    unit_cost: float,
    fixed_costs: float,
    current_sales_units: int,
):
    """
    Render Monte Carlo simulation for profit uncertainty analysis.

    Args:
        contribution_margin: Contribution margin per unit
        unit_price: Selling price per unit
        unit_cost: Variable cost per unit
        fixed_costs: Total fixed costs
        current_sales_units: Current sales volume
    """
    st.markdown("---")
    st.subheader("🎲 Monte Carlo Simulation: Profit Probability")
    st.caption("Model uncertainty in costs and sales to understand profit risk.")

    with st.expander("⚙️ Simulation Parameters", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            cost_variance = st.slider(
                "Cost Variance (%)",
                min_value=0,
                max_value=50,
                value=10,
                step=5,
                help="How much can variable costs fluctuate? (e.g., supplier price changes)",
            )

        with col2:
            sales_variance = st.slider(
                "Sales Variance (%)",
                min_value=0,
                max_value=50,
                value=15,
                step=5,
                help="How much can sales volume fluctuate? (e.g., demand uncertainty)",
            )

        with col3:
            num_simulations = st.select_slider(
                "Simulations",
                options=[100, 500, 1000, 5000, 10000],
                value=1000,
                help="More simulations = more accurate probability estimates",
            )

    if st.button("🚀 Run Monte Carlo Simulation", use_container_width=True):
        with st.spinner(f"Running {num_simulations:,} simulations..."):
            # Run simulations
            np.random.seed(42)  # For reproducibility

            # Generate random samples
            cost_samples = np.random.normal(
                unit_cost, unit_cost * (cost_variance / 100), num_simulations
            )
            sales_samples = np.random.normal(
                current_sales_units, current_sales_units * (sales_variance / 100), num_simulations
            )

            # Calculate profit for each simulation
            profits = (unit_price - cost_samples) * sales_samples - fixed_costs

            # Calculate statistics
            mean_profit = np.mean(profits)
            median_profit = np.median(profits)
            std_profit = np.std(profits)
            min_profit = np.min(profits)
            max_profit = np.max(profits)

            # Probability calculations
            prob_profitable = (profits > 0).sum() / num_simulations * 100
            prob_target = (profits > 5000).sum() / num_simulations * 100  # Arbitrary target
            percentile_5 = np.percentile(profits, 5)
            percentile_95 = np.percentile(profits, 95)

            # Display results
            st.markdown("#### 📊 Simulation Results")

            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

            with metric_col1:
                st.metric("Mean Profit", f"${mean_profit:,.0f}")

            with metric_col2:
                st.metric("Median Profit", f"${median_profit:,.0f}")

            with metric_col3:
                st.metric("Std Deviation", f"${std_profit:,.0f}")

            with metric_col4:
                prob_color = (
                    "🟢" if prob_profitable >= 90 else "🟡" if prob_profitable >= 70 else "🔴"
                )
                st.metric(f"{prob_color} Probability of Profit", f"{prob_profitable:.1f}%")

            # Risk analysis
            st.markdown("#### 🎯 Risk Analysis")

            risk_col1, risk_col2 = st.columns(2)

            with risk_col1:
                st.metric("Best Case (95th percentile)", f"${percentile_95:,.0f}")
                st.metric("Worst Case (5th percentile)", f"${percentile_5:,.0f}")

            with risk_col2:
                st.metric("Best Possible", f"${max_profit:,.0f}")
                st.metric("Worst Possible", f"${min_profit:,.0f}")

            # Interpretation
            if prob_profitable >= 90:
                st.success(
                    f"✅ **Low Risk:** {prob_profitable:.1f}% chance of profitability. "
                    "Your business model is robust to cost and sales fluctuations."
                )
            elif prob_profitable >= 70:
                st.warning(
                    f"⚠️ **Moderate Risk:** {prob_profitable:.1f}% chance of profitability. "
                    "Consider strategies to reduce cost variance or stabilize sales."
                )
            else:
                st.error(
                    f"🚨 **High Risk:** Only {prob_profitable:.1f}% chance of profitability. "
                    "Recommend restructuring costs or increasing prices significantly."
                )

            # Histogram
            st.markdown("#### 📈 Profit Distribution")

            fig = go.Figure()

            fig.add_trace(
                go.Histogram(x=profits, nbinsx=50, name="Profit", marker_color=ui.THEME["primary"])
            )

            # Add vertical lines for key metrics
            fig.add_vline(
                x=mean_profit,
                line_dash="dash",
                line_color="cyan",
                annotation_text=f"Mean: ${mean_profit:,.0f}",
                annotation_position="top",
            )

            fig.add_vline(
                x=0,
                line_dash="solid",
                line_color="red",
                annotation_text="Break-Even",
                annotation_position="bottom",
            )

            fig.update_layout(
                title=f"Profit Distribution ({num_simulations:,} Simulations)",
                xaxis_title="Profit ($)",
                yaxis_title="Frequency",
                template=ui.get_plotly_template(),
                height=400,
                showlegend=False,
            )

            st.plotly_chart(fig, use_container_width=True)

            # Summary table
            st.markdown("#### 📋 Summary Statistics")

            summary_data = {
                "Metric": [
                    "Mean",
                    "Median",
                    "Std Dev",
                    "Min",
                    "Max",
                    "5th Percentile",
                    "95th Percentile",
                    "Probability > $0",
                    "Probability > $5,000",
                ],
                "Value": [
                    f"${mean_profit:,.0f}",
                    f"${median_profit:,.0f}",
                    f"${std_profit:,.0f}",
                    f"${min_profit:,.0f}",
                    f"${max_profit:,.0f}",
                    f"${percentile_5:,.0f}",
                    f"${percentile_95:,.0f}",
                    f"{prob_profitable:.1f}%",
                    f"{prob_target:.1f}%",
                ],
            }

            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)


def _render_save_load_section(unit_price, unit_cost, fixed_costs, target_profit, current_sales_units):
    """Render the section to save and load analysis scenarios."""
    if not st.session_state.get("authenticated"):
        st.info("💡 Login to save analysis scenarios.")
        return

    st.markdown("---")
    st.subheader("💾 Saved Scenarios")

    # Save current
    with st.expander("Save Current Scenario"):
        scenario_name = st.text_input("Scenario Name", placeholder="e.g., Q1 Optimization")
        if st.button("Save", use_container_width=True):
            if not scenario_name:
                st.error("Please enter a name for the scenario.")
            else:
                data = {
                    "unit_price": unit_price,
                    "unit_cost": unit_cost,
                    "fixed_costs": fixed_costs,
                    "target_profit": target_profit,
                    "current_sales_units": current_sales_units
                }
                if save_scenario(st.session_state.username, "margin_hunter", scenario_name, data):
                    st.success(f"Scenario '{scenario_name}' saved!")
                    st.rerun()
                else:
                    st.error("Failed to save scenario.")

    # Load existing
    scenarios = get_user_scenarios(st.session_state.username, "margin_hunter")
    if scenarios:
        for s in scenarios:
            cols = st.columns([3, 1, 1])
            with cols[0]:
                st.write(f"**{s['name']}**")
                st.caption(f"Created: {s['created_at'][:10]}")
            with cols[1]:
                if st.button("Load", key=f"load_{s['id']}", use_container_width=True):
                    data = json.loads(s['data'])
                    st.session_state.mh_unit_price = float(data['unit_price'])
                    st.session_state.mh_unit_cost = float(data['unit_cost'])
                    st.session_state.mh_fixed_costs = float(data['fixed_costs'])
                    st.session_state.mh_target_profit = float(data['target_profit'])
                    st.session_state.mh_current_sales_units = int(data['current_sales_units'])
                    st.success(f"Loaded '{s['name']}'")
                    st.rerun()
            with cols[2]:
                if st.button("🗑️", key=f"del_{s['id']}", use_container_width=True):
                    if delete_scenario(s['id'], st.session_state.username):
                        st.rerun()
    else:
        st.caption("No saved scenarios found.")
