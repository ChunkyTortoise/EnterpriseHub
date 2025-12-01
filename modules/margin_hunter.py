import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from utils.logger import get_logger

logger = get_logger(__name__)

def render() -> None:
    """Render the Margin Hunter module."""
    st.title("💰 Margin Hunter")
    st.markdown("### Profitability & Break-Even Analysis")

    # Layout: Inputs on left, Results on right
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("⚙️ Parameters")
        
        with st.expander("Product Costs", expanded=True):
            unit_price = st.number_input("Unit Selling Price ($)", value=50.0, step=1.0, min_value=0.0)
            unit_cost = st.number_input("Unit Variable Cost ($)", value=20.0, step=1.0, min_value=0.0)
            
        with st.expander("Fixed Costs", expanded=True):
            fixed_costs = st.number_input("Total Fixed Costs ($)", value=5000.0, step=100.0, min_value=0.0)
            
        with st.expander("Targeting"):
            target_profit = st.number_input("Target Profit ($)", value=2000.0, step=100.0, min_value=0.0)

    # Calculations
    contribution_margin = unit_price - unit_cost
    contribution_margin_ratio = (contribution_margin / unit_price) * 100 if unit_price > 0 else 0
    
    if contribution_margin <= 0:
        st.error("⚠️ Selling price must be greater than variable cost to break even.")
        return

    break_even_units = fixed_costs / contribution_margin
    break_even_revenue = break_even_units * unit_price
    
    target_units = (fixed_costs + target_profit) / contribution_margin
    target_revenue = target_units * unit_price

    with col2:
        st.subheader("📊 Analysis Results")
        
        # Key Metrics
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Contribution Margin", f"${contribution_margin:.2f}", f"{contribution_margin_ratio:.1f}%")
        with m2:
            st.metric("Break-Even Units", f"{int(np.ceil(break_even_units)):,} units")
        with m3:
            st.metric("Break-Even Revenue", f"${break_even_revenue:,.2f}")

        # Visualization
        st.markdown("#### Cost-Volume-Profit (CVP) Analysis")
        
        # Generate data for chart
        max_units = int(target_units * 1.5) if target_units > 0 else int(break_even_units * 2)
        max_units = max(max_units, 100) # Minimum range
        
        units_range = np.linspace(0, max_units, 100)
        revenue_curve = units_range * unit_price
        total_cost_curve = fixed_costs + (units_range * unit_cost)
        fixed_cost_curve = [fixed_costs] * len(units_range)
        
        fig = go.Figure()
        
        # Total Revenue Line
        fig.add_trace(go.Scatter(
            x=units_range, y=revenue_curve,
            name="Total Revenue",
            line=dict(color="#00ff88", width=3)
        ))
        
        # Total Cost Line
        fig.add_trace(go.Scatter(
            x=units_range, y=total_cost_curve,
            name="Total Cost",
            line=dict(color="#ff4444", width=3)
        ))
        
        # Fixed Cost Line
        fig.add_trace(go.Scatter(
            x=units_range, y=fixed_cost_curve,
            name="Fixed Costs",
            line=dict(color="#888888", dash="dash")
        ))
        
        # Break-Even Point
        fig.add_trace(go.Scatter(
            x=[break_even_units], y=[break_even_revenue],
            mode="markers",
            name="Break-Even Point",
            marker=dict(color="white", size=12, symbol="star")
        ))

        fig.update_layout(
            title="Revenue vs Costs",
            xaxis_title="Units Sold",
            yaxis_title="Amount ($)",
            template="plotly_dark",
            height=400,
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Scenario Table
        st.markdown("#### 🎯 Scenarios")
        scenarios = [
            {"Scenario": "Break-Even", "Units": break_even_units, "Revenue": break_even_revenue, "Profit": 0},
            {"Scenario": "Target Profit", "Units": target_units, "Revenue": target_revenue, "Profit": target_profit},
            {"Scenario": "+10% Sales", "Units": target_units * 1.1, "Revenue": target_revenue * 1.1, "Profit": (target_units * 1.1 * contribution_margin) - fixed_costs},
        ]
        
        df_scenarios = pd.DataFrame(scenarios)
        df_scenarios["Units"] = df_scenarios["Units"].apply(lambda x: f"{int(np.ceil(x)):,}")
        df_scenarios["Revenue"] = df_scenarios["Revenue"].apply(lambda x: f"${x:,.2f}")
        df_scenarios["Profit"] = df_scenarios["Profit"].apply(lambda x: f"${x:,.2f}")
        
        st.dataframe(df_scenarios, use_container_width=True, hide_index=True)
