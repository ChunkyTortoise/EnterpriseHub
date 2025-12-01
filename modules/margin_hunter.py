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
            
        with st.expander("Targeting", expanded=True):
            target_profit = st.number_input("Target Profit ($)", value=2000.0, step=100.0, min_value=0.0)
            current_sales_units = st.number_input("Current Sales (Units)", value=250, step=10, min_value=0)

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
    
    # Advanced Metrics
    margin_of_safety_units = current_sales_units - break_even_units
    margin_of_safety_pct = (margin_of_safety_units / current_sales_units) * 100 if current_sales_units > 0 else 0
    
    current_profit = (current_sales_units * contribution_margin) - fixed_costs
    operating_leverage = (current_sales_units * contribution_margin) / current_profit if current_profit > 0 else 0

    with col2:
        st.subheader("📊 Analysis Results")
        
        # Key Metrics Row 1
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Contribution Margin", f"${contribution_margin:.2f}", f"{contribution_margin_ratio:.1f}%")
        with m2:
            st.metric("Break-Even Units", f"{int(np.ceil(break_even_units)):,} units")
        with m3:
            st.metric("Break-Even Revenue", f"${break_even_revenue:,.2f}")
            
        # Key Metrics Row 2 (Advanced)
        m4, m5, m6 = st.columns(3)
        with m4:
            st.metric("Margin of Safety", f"{margin_of_safety_pct:.1f}%", f"{int(margin_of_safety_units):,} units")
        with m5:
            st.metric("Operating Leverage", f"{operating_leverage:.2f}x")
        with m6:
            st.metric("Current Profit", f"${current_profit:,.2f}")

        # --- CVP Visualization ---
        st.markdown("#### Cost-Volume-Profit (CVP) Analysis")
        
        # Generate data for chart
        max_units = max(int(target_units * 1.5), int(current_sales_units * 1.2), int(break_even_units * 2), 100)
        
        units_range = np.linspace(0, max_units, 100)
        revenue_curve = units_range * unit_price
        total_cost_curve = fixed_costs + (units_range * unit_cost)
        
        fig = go.Figure()
        
        # Profit/Loss Zones (Fill)
        fig.add_trace(go.Scatter(
            x=units_range, y=revenue_curve,
            name="Revenue",
            line=dict(color="#00ff88", width=3)
        ))
        
        fig.add_trace(go.Scatter(
            x=units_range, y=total_cost_curve,
            name="Total Cost",
            line=dict(color="#ff4444", width=3),
            fill='tonexty', # Fill to previous trace (Revenue)
            fillcolor='rgba(255, 68, 68, 0.1)' # Default fill (Loss) - Plotly logic is tricky here, simplified approach
        ))
        
        # Fixed Cost Line
        fig.add_trace(go.Scatter(
            x=units_range, y=[fixed_costs] * len(units_range),
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
        
        # Current Sales Point
        fig.add_trace(go.Scatter(
            x=[current_sales_units], y=[current_sales_units * unit_price],
            mode="markers",
            name="Current Sales",
            marker=dict(color="#00D9FF", size=10, symbol="circle")
        ))

        fig.update_layout(
            title="Revenue vs Costs (Green=Profit, Red=Loss)",
            xaxis_title="Units Sold",
            yaxis_title="Amount ($)",
            template="plotly_dark",
            height=400,
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # --- Sensitivity Analysis ---
        st.markdown("#### 🌡️ Sensitivity Heatmap: Net Profit")
        st.caption("Impact of changing Unit Price vs Variable Cost on Net Profit (at current sales volume)")
        
        # Create matrix
        price_range = np.linspace(unit_price * 0.8, unit_price * 1.2, 10)
        cost_range = np.linspace(unit_cost * 0.8, unit_cost * 1.2, 10)
        
        z_data = []
        for c in cost_range:
            row = []
            for p in price_range:
                # Profit = (Price - Cost) * Units - Fixed
                profit = (p - c) * current_sales_units - fixed_costs
                row.append(profit)
            z_data.append(row)
            
        fig_heat = go.Figure(data=go.Heatmap(
            z=z_data,
            x=[f"${p:.2f}" for p in price_range],
            y=[f"${c:.2f}" for c in cost_range],
            colorscale='RdBu',
            zmid=0,
            colorbar=dict(title="Net Profit ($)")
        ))
        
        fig_heat.update_layout(
            title="Profit Sensitivity Matrix",
            xaxis_title="Unit Price ($)",
            yaxis_title="Variable Cost ($)",
            template="plotly_dark",
            height=400
        )
        
        st.plotly_chart(fig_heat, use_container_width=True)
        
        # --- Scenario Table & Export ---
        st.markdown("#### 🎯 Scenarios")
        scenarios = [
            {"Scenario": "Break-Even", "Units": break_even_units, "Revenue": break_even_revenue, "Profit": 0},
            {"Scenario": "Current Status", "Units": current_sales_units, "Revenue": current_sales_units * unit_price, "Profit": current_profit},
            {"Scenario": "Target Profit", "Units": target_units, "Revenue": target_revenue, "Profit": target_profit},
        ]
        
        df_scenarios = pd.DataFrame(scenarios)
        
        # Format for display
        df_display = df_scenarios.copy()
        df_display["Units"] = df_display["Units"].apply(lambda x: f"{int(np.ceil(x)):,}")
        df_display["Revenue"] = df_display["Revenue"].apply(lambda x: f"${x:,.2f}")
        df_display["Profit"] = df_display["Profit"].apply(lambda x: f"${x:,.2f}")
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # CSV Export
        csv = df_scenarios.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Scenarios CSV",
            data=csv,
            file_name='margin_hunter_scenarios.csv',
            mime='text/csv',
        )
