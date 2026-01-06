"""
Commission Calculator - Interactive Demo
Real-time commission tracking and revenue projection system.
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.commission_calculator import CommissionCalculator, CommissionType, DealStage, quick_commission

st.set_page_config(
    page_title="Commission Calculator | GHL Real Estate",
    page_icon="💵",
    layout="wide"
)

# Initialize session state
if "calculator" not in st.session_state:
    st.session_state.calculator = CommissionCalculator(brokerage_split=0.80)
if "tracked_deals" not in st.session_state:
    st.session_state.tracked_deals = []

calc = st.session_state.calculator

# Header
st.title("💵 Commission Calculator")
st.markdown("### Real-Time Commission Tracking & Revenue Projection")
st.markdown("**See exactly how much $ each automation generates**")

st.divider()

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["🧮 Calculate Commission", "📊 Pipeline Tracker", "📈 Projections", "💰 Automation ROI"])

with tab1:
    st.subheader("Commission Calculator")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 🏠 Deal Details")
        
        property_price = st.number_input(
            "Property Sale Price ($)",
            value=750000,
            step=50000,
            format="%d"
        )
        
        commission_type = st.selectbox(
            "Commission Type",
            ["Buyer Agent", "Seller Agent", "Dual Agency"]
        )
        
        commission_type_map = {
            "Buyer Agent": CommissionType.BUYER_AGENT,
            "Seller Agent": CommissionType.SELLER_AGENT,
            "Dual Agency": CommissionType.DUAL_AGENCY
        }
        
        comm_type = commission_type_map[commission_type]
        
        # Commission rate
        default_rates = {
            CommissionType.BUYER_AGENT: 2.5,
            CommissionType.SELLER_AGENT: 2.5,
            CommissionType.DUAL_AGENCY: 5.0
        }
        
        custom_rate = st.number_input(
            "Commission Rate (%)",
            value=default_rates[comm_type],
            min_value=0.0,
            max_value=10.0,
            step=0.1,
            format="%.1f"
        ) / 100
        
        # Brokerage split
        brokerage_split = st.slider(
            "Your Brokerage Split (%)",
            0, 100, 80,
            help="Your share after brokerage fee"
        ) / 100
        
        # Update calculator
        calc.brokerage_split = brokerage_split
        
        # Transaction costs
        transaction_costs = st.number_input(
            "Transaction Costs ($)",
            value=0,
            step=100,
            help="Marketing, photography, staging, etc."
        )
        
        if st.button("🧮 Calculate Commission", type="primary", use_container_width=True):
            result = calc.calculate_commission(
                property_price,
                comm_type,
                custom_rate,
                transaction_costs
            )
            st.session_state.last_calculation = result
            st.rerun()
    
    with col2:
        st.markdown("#### 💰 Commission Breakdown")
        
        if hasattr(st.session_state, 'last_calculation'):
            result = st.session_state.last_calculation
            
            # Display metrics
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.metric(
                    "Gross Commission",
                    f"${result['gross_commission']:,.2f}",
                    help="Total commission before splits"
                )
                st.metric(
                    "Your Share (Before Costs)",
                    f"${result['agent_share_gross']:,.2f}",
                    help=f"{brokerage_split*100:.0f}% of gross commission"
                )
            
            with col_b:
                st.metric(
                    "Brokerage Portion",
                    f"${result['brokerage_portion']:,.2f}",
                    help="Amount going to brokerage"
                )
                st.metric(
                    "Net Commission (Your Take-Home)",
                    f"${result['net_commission']:,.2f}",
                    delta=f"{result['effective_rate']:.3f}% of sale price",
                    help="After brokerage split and costs"
                )
            
            st.divider()
            
            # Visual breakdown
            st.markdown("**📊 Commission Flow:**")
            
            labels = ["Gross Commission", "Your Share", "Brokerage Fee", "Transaction Costs", "Net to You"]
            values = [
                result['gross_commission'],
                result['agent_share_gross'],
                result['brokerage_portion'],
                result['transaction_costs'],
                result['net_commission']
            ]
            
            fig = go.Figure(data=[go.Waterfall(
                orientation="v",
                measure=["relative", "relative", "relative", "relative", "total"],
                x=["Gross", "Split", "Brokerage", "Costs", "Net"],
                textposition="outside",
                text=[f"${v:,.0f}" for v in values],
                y=[result['gross_commission'], 0, -result['brokerage_portion'], 
                   -result['transaction_costs'], 0],
                connector={"line": {"color": "rgb(63, 63, 63)"}},
            )])
            
            fig.update_layout(
                showlegend=False,
                height=400,
                yaxis_title="Amount ($)"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.info("👈 Enter deal details and click 'Calculate Commission' to see breakdown")

with tab2:
    st.subheader("📊 Deal Pipeline Tracker")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### Add Deal to Pipeline")
        
        with st.form("add_deal"):
            col_a, col_b = st.columns(2)
            
            with col_a:
                deal_id = st.text_input("Deal ID", value=f"D{len(calc.deals) + 1:03d}")
                client_name = st.text_input("Client Name", value="")
                property_price_deal = st.number_input("Property Price ($)", value=650000, step=50000)
            
            with col_b:
                comm_type_deal = st.selectbox(
                    "Commission Type",
                    ["Buyer Agent", "Seller Agent", "Dual Agency"],
                    key="deal_comm_type"
                )
                current_stage = st.selectbox(
                    "Current Stage",
                    ["Lead", "Qualified", "Showing", "Offer", "Under Contract", "Closed"]
                )
                
                # Automation features
                st.multiselect(
                    "Automation Features Used",
                    ["deal_closer_ai", "hot_lead_fastlane", "ai_listing_writer", 
                     "auto_followup", "voice_receptionist"],
                    key="automation_features"
                )
            
            submitted = st.form_submit_button("➕ Add Deal", use_container_width=True)
            
            if submitted and client_name:
                stage_map = {
                    "Lead": DealStage.LEAD,
                    "Qualified": DealStage.QUALIFIED,
                    "Showing": DealStage.SHOWING,
                    "Offer": DealStage.OFFER,
                    "Under Contract": DealStage.UNDER_CONTRACT,
                    "Closed": DealStage.CLOSED
                }
                
                deal = calc.track_deal(
                    deal_id=deal_id,
                    client_name=client_name,
                    property_price=property_price_deal,
                    commission_type=commission_type_map[comm_type_deal],
                    current_stage=stage_map[current_stage],
                    automation_features=st.session_state.automation_features
                )
                
                st.success(f"✅ Deal {deal_id} added to pipeline!")
                st.rerun()
    
    with col2:
        # Pipeline summary
        if calc.deals:
            summary = calc.get_pipeline_summary(active_only=True)
            
            st.metric("Total Deals", summary["total_deals"])
            st.metric("Expected Commission", f"${summary['total_expected_commission']:,.0f}")
            st.metric("Potential Commission", f"${summary['total_potential_commission']:,.0f}")
            st.metric("Weighted Close Rate", f"{summary['weighted_close_rate']}%")
    
    st.divider()
    
    # Deals table
    if calc.deals:
        st.markdown("#### 📋 Active Deals")
        
        deals_data = []
        for deal in calc.deals:
            if deal["current_stage"] not in ["closed", "lost"]:
                deals_data.append({
                    "ID": deal["deal_id"],
                    "Client": deal["client_name"],
                    "Price": f"${deal['property_price']:,}",
                    "Stage": deal["current_stage"].replace("_", " ").title(),
                    "Close %": f"{deal['close_probability']}%",
                    "Expected $": f"${deal['expected_value']:,.0f}",
                    "Days": deal["days_in_pipeline"],
                    "Automations": len(deal["automation_features"])
                })
        
        if deals_data:
            df = pd.DataFrame(deals_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No active deals. Add deals above to track them.")
    else:
        st.info("No deals tracked yet. Add your first deal above!")

with tab3:
    st.subheader("📈 Revenue Projections")
    
    if len(calc.deals) >= 2:
        projections = calc.get_monthly_projections(months=12)
        
        # Display total
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("12-Month Projection", f"${projections['total_12_month']:,.0f}")
        with col2:
            st.metric("Avg Monthly", f"${projections['avg_monthly']:,.0f}")
        with col3:
            st.metric("Avg Days to Close", f"{projections['avg_days_to_close']:.0f}")
        
        st.divider()
        
        # Monthly chart
        st.markdown("#### 📊 Monthly Commission Forecast")
        
        months = [p["month_name"] for p in projections["projections"]]
        amounts = [p["projected_commission"] for p in projections["projections"]]
        
        fig = go.Figure([go.Bar(
            x=months,
            y=amounts,
            text=[f"${a:,.0f}" for a in amounts],
            textposition='auto',
        )])
        
        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Projected Commission ($)",
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.caption(f"*{projections['assumptions']}*")
    
    else:
        st.info("📊 Add at least 2 deals to see revenue projections.")

with tab4:
    st.subheader("💰 Automation ROI Report")
    
    if calc.deals:
        roi_report = calc.get_automation_roi_report()
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("System Cost/Year", f"${roi_report['system_cost_annual']:,}")
        with col2:
            st.metric("Revenue Increase", f"${roi_report['revenue_increase_annual']:,.0f}")
        with col3:
            st.metric("ROI", f"{roi_report['roi_percentage']:.0f}%")
        with col4:
            st.metric("Payback Period", f"{roi_report['payback_period_days']:.0f} days")
        
        st.divider()
        
        # Summary message
        st.success(f"🎉 {roi_report['summary']}")
        
        st.divider()
        
        # Feature breakdown
        if roi_report["feature_breakdown"]:
            st.markdown("#### 🚀 Top Performing Features")
            
            for feature in roi_report["feature_breakdown"]:
                col_a, col_b, col_c = st.columns([2, 1, 1])
                
                with col_a:
                    st.markdown(f"**{feature['feature'].replace('_', ' ').title()}**")
                with col_b:
                    st.caption(f"Improvement: +{feature['improvement_pct']}%")
                with col_c:
                    st.caption(f"Value: ${feature['estimated_value']:,.0f}")
        
        st.divider()
        
        # Tracking stats
        st.markdown("#### 📊 Tracking Statistics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Deals Tracked", roi_report["deals_tracked"])
        with col2:
            st.metric("Using Automation", roi_report["deals_with_automation"])
        with col3:
            usage_rate = (roi_report["deals_with_automation"] / roi_report["deals_tracked"] * 100) if roi_report["deals_tracked"] > 0 else 0
            st.metric("Automation Usage", f"{usage_rate:.0f}%")
    
    else:
        st.info("💰 Track deals to see automation ROI analysis.")

# Sidebar
with st.sidebar:
    st.markdown("### 💵 Commission Calculator")
    st.markdown("---")
    
    st.markdown("**🎯 Key Features:**")
    st.markdown("""
    - 🧮 Instant commission calculation
    - 📊 Pipeline tracking
    - 📈 12-month projections
    - 💰 Automation ROI analysis
    - 🎯 Deal stage probability
    """)
    
    st.markdown("---")
    st.markdown("**💡 Quick Calculate:**")
    
    quick_price = st.number_input("Property Price", value=500000, step=50000, key="quick_calc")
    quick_result = quick_commission(quick_price, commission_rate=0.025, split=0.80)
    st.success(f"**Net: ${quick_result:,.2f}**")
    
    st.markdown("---")
    st.markdown("**📊 Pipeline Stats:**")
    if calc.deals:
        active = [d for d in calc.deals if d["current_stage"] not in ["closed", "lost"]]
        st.caption(f"• Active Deals: {len(active)}")
        st.caption(f"• Total Tracked: {len(calc.deals)}")
    else:
        st.caption("No deals tracked yet")
