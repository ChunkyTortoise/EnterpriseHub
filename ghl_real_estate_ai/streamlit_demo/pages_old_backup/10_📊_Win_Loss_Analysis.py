"""
Win/Loss Analysis - Interactive Demo
Learn from closed and lost deals to improve performance.
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.win_loss_analysis import WinLossAnalysis, DealOutcome, LossReason, WinReason

st.set_page_config(
    page_title="Win/Loss Analysis | GHL Real Estate",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if "analyzer" not in st.session_state:
    st.session_state.analyzer = WinLossAnalysis()

analyzer = st.session_state.analyzer

# Header
st.title("📊 Win/Loss Analysis")
st.markdown("### Learn From Every Deal - Continuous Improvement Dashboard")
st.markdown("**Revenue Impact:** +$30K-50K/year through pattern recognition")

st.divider()

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["📝 Record Outcome", "📈 Win Rate", "🔍 Patterns", "📊 Comprehensive Report"])

with tab1:
    st.subheader("Record Deal Outcome")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### Deal Information")
        
        deal_id = st.text_input("Deal ID", value=f"D{len(analyzer.deals) + 1:03d}")
        client_name = st.text_input("Client Name")
        property_address = st.text_input("Property Address")
        property_price = st.number_input("Property Price ($)", value=650000, step=50000, format="%d")
        
        st.divider()
        
        st.markdown("#### Outcome")
        outcome = st.radio(
            "Deal Result",
            ["Won", "Lost", "Pending"],
            horizontal=True
        )
        
        outcome_map = {
            "Won": DealOutcome.WON,
            "Lost": DealOutcome.LOST,
            "Pending": DealOutcome.PENDING
        }
        
        deal_outcome = outcome_map[outcome]
        
        st.divider()
        
        # Different fields based on outcome
        if outcome == "Won":
            st.markdown("#### 🎉 Win Details")
            
            reason = st.text_area(
                "Why did you win this deal?",
                placeholder="e.g., Strong relationship, quick response, local expertise..."
            )
            
            commission_value = st.number_input(
                "Commission Earned ($)",
                value=16250,
                step=1000
            )
            
            st.markdown("**Select Win Factors:**")
            win_factors = []
            col_a, col_b = st.columns(2)
            
            with col_a:
                if st.checkbox("Strong Relationship", key="rel"):
                    win_factors.append("relationship")
                if st.checkbox("Local Expertise", key="exp"):
                    win_factors.append("expertise")
                if st.checkbox("Quick Responsiveness", key="resp"):
                    win_factors.append("responsiveness")
                if st.checkbox("Competitive Pricing", key="price"):
                    win_factors.append("pricing")
            
            with col_b:
                if st.checkbox("Effective Marketing", key="mark"):
                    win_factors.append("marketing")
                if st.checkbox("Strong Negotiation", key="neg"):
                    win_factors.append("negotiation")
                if st.checkbox("Referral/Trust", key="ref"):
                    win_factors.append("referral")
                if st.checkbox("Technology Advantage", key="tech"):
                    win_factors.append("technology")
        
        else:  # Lost or Pending
            st.markdown("#### ❌ Loss Details" if outcome == "Lost" else "#### ⏳ Pending Details")
            
            reason = st.text_area(
                "What happened?" if outcome == "Lost" else "Current status?",
                placeholder="Describe the situation..."
            )
            
            commission_value = 0
            
            if outcome == "Lost":
                competitor_name = st.text_input("Competitor Name (if applicable)")
            else:
                competitor_name = None
        
        deal_duration = st.number_input(
            "Deal Duration (days)",
            value=45,
            step=5
        )
        
        automation_features = st.multiselect(
            "Automation Features Used",
            ["deal_closer_ai", "hot_lead_fastlane", "ai_listing_writer", 
             "auto_followup", "voice_receptionist", "workflow_automation"]
        )
        
        notes = st.text_area("Additional Notes")
    
    with col2:
        st.markdown("#### Preview & Submit")
        
        if st.button("💾 Record Outcome", type="primary", use_container_width=True):
            if client_name and reason:
                result = analyzer.record_outcome(
                    deal_id=deal_id,
                    client_name=client_name,
                    property_address=property_address,
                    property_price=property_price,
                    outcome=deal_outcome,
                    reason=reason,
                    competitor_name=competitor_name if outcome == "Lost" else None,
                    deal_duration_days=deal_duration,
                    commission_value=commission_value,
                    automation_features_used=automation_features,
                    notes=notes
                )
                
                st.success(f"✅ Deal {deal_id} recorded successfully!")
                st.balloons()
                st.rerun()
            else:
                st.error("⚠️ Please fill in Client Name and Reason")
        
        st.divider()
        
        # Preview
        if client_name:
            st.markdown("**📋 Deal Summary:**")
            st.info(f"""
            **Client:** {client_name}  
            **Property:** {property_address}  
            **Value:** ${property_price:,}  
            **Outcome:** {outcome}  
            **Duration:** {deal_duration} days  
            **Automations:** {len(automation_features)}
            """)

with tab2:
    st.subheader("📈 Win Rate Analysis")
    
    if analyzer.deals:
        # Time period selector
        period = st.selectbox(
            "Time Period",
            ["Last 30 days", "Last 90 days", "Last 6 months", "All time"]
        )
        
        days_map = {
            "Last 30 days": 30,
            "Last 90 days": 90,
            "Last 6 months": 180,
            "All time": None
        }
        
        win_rate = analyzer.get_win_rate(days=days_map[period])
        
        # Main metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Deals", win_rate["total_deals"])
        with col2:
            st.metric("Won", win_rate["won"], delta=f"+{win_rate['won']}")
        with col3:
            st.metric("Lost", win_rate["lost"], delta=f"-{win_rate['lost']}", delta_color="inverse")
        with col4:
            wr = win_rate["win_rate"]
            color = "normal" if wr >= 50 else "inverse"
            st.metric("Win Rate", f"{wr}%", delta=f"{'Above' if wr >= 50 else 'Below'} 50%", delta_color=color)
        
        st.divider()
        
        # Commission metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Commission Won", f"${win_rate['total_commission_won']:,.2f}")
        with col2:
            st.metric("Avg Commission/Win", f"${win_rate['avg_commission_per_win']:,.2f}")
        
        st.divider()
        
        # Visual representation
        st.markdown("#### 📊 Win/Loss Distribution")
        
        labels = ["Won", "Lost", "Pending"]
        values = [win_rate["won"], win_rate["lost"], win_rate["pending"]]
        colors = ['#10b981', '#ef4444', '#eab308']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=.4,
            marker_colors=colors
        )])
        
        fig.update_layout(
            annotations=[dict(text=f'{wr}%<br>Win Rate', x=0.5, y=0.5, font_size=20, showarrow=False)],
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("📊 No deals recorded yet. Start by recording your first deal outcome!")

with tab3:
    st.subheader("🔍 Pattern Analysis")
    
    if len(analyzer.deals) >= 3:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### ❌ Loss Patterns")
            loss_analysis = analyzer.analyze_loss_patterns(limit=10)
            
            if loss_analysis["total_losses"] > 0:
                st.metric("Total Losses", loss_analysis["total_losses"])
                st.metric("Estimated Lost Commission", f"${loss_analysis['estimated_lost_commission']:,.0f}")
                
                st.divider()
                
                st.markdown("**Top Loss Reasons:**")
                for reason_data in loss_analysis["top_reasons"]:
                    st.progress(
                        reason_data["percentage"] / 100,
                        text=f"{reason_data['reason'].replace('_', ' ').title()}: {reason_data['count']} ({reason_data['percentage']}%)"
                    )
                
                if loss_analysis["top_competitors"]:
                    st.divider()
                    st.markdown("**Top Competitors:**")
                    for comp in loss_analysis["top_competitors"]:
                        st.caption(f"• {comp['name']}: {comp['losses_to']} losses")
                
                st.divider()
                st.markdown("**💡 Recommendations:**")
                for rec in loss_analysis["recommendations"]:
                    st.info(rec)
            else:
                st.success("🎉 No losses yet - keep it up!")
        
        with col2:
            st.markdown("#### ✅ Win Patterns")
            win_analysis = analyzer.analyze_win_patterns(limit=10)
            
            if win_analysis["total_wins"] > 0:
                st.metric("Total Wins", win_analysis["total_wins"])
                st.metric("Total Commission", f"${win_analysis['total_commission']:,.0f}")
                
                st.divider()
                
                st.markdown("**Top Win Factors:**")
                for factor in win_analysis["top_win_factors"]:
                    st.progress(
                        factor["percentage"] / 100,
                        text=f"{factor['factor'].replace('_', ' ').title()}: {factor['count']} ({factor['percentage']}%)"
                    )
                
                if win_analysis["top_automation_features"]:
                    st.divider()
                    st.markdown("**🤖 Top Automation Features:**")
                    for feature in win_analysis["top_automation_features"]:
                        st.caption(f"• {feature['feature'].replace('_', ' ').title()}: {feature['wins_with_feature']} wins ({feature['percentage']}%)")
                
                st.divider()
                st.markdown("**💡 Amplify These Strengths:**")
                for rec in win_analysis["recommendations"]:
                    st.success(rec)
            else:
                st.info("Record your first win to see patterns!")
    
    else:
        st.info("📊 Record at least 3 deals to see pattern analysis.")

with tab4:
    st.subheader("📊 Comprehensive Report")
    
    if len(analyzer.deals) >= 5:
        report = analyzer.get_comprehensive_report(days=90)
        
        # Key insights
        st.markdown("### 🎯 Key Insights")
        for insight in report["key_insights"]:
            st.info(insight)
        
        st.divider()
        
        # Action items
        st.markdown("### ✅ Priority Action Items")
        for i, action in enumerate(report["action_items"], 1):
            st.checkbox(f"{i}. {action}", key=f"action_{i}")
        
        st.divider()
        
        # Trends
        trends = report["trends"]
        st.markdown("### 📈 Performance Trends")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Recent Win Rate", f"{trends['recent_win_rate']}%")
        with col2:
            trend_dir = trends['trend_direction']
            emoji = "📈" if trend_dir == "improving" else "📉" if trend_dir == "declining" else "➡️"
            st.metric("Trend", f"{emoji} {trend_dir.title()}")
        with col3:
            st.metric("Win Rate Change", f"{trends['win_rate_trend']:+.1f}%")
        
        st.caption(trends['comparison_period'])
        
        st.divider()
        
        # Competitive intelligence
        if report["competitive_intelligence"]["competitors_identified"] > 0:
            st.markdown("### 🔍 Competitive Intelligence")
            for comp in report["competitive_intelligence"]["top_competitors"]:
                st.caption(f"• **{comp['name']}**: {comp['losses_to']} losses")
    
    else:
        st.info("📊 Record at least 5 deals to generate comprehensive report.")

# Sidebar
with st.sidebar:
    st.markdown("### 📊 Win/Loss Analysis")
    st.markdown("---")
    
    st.markdown("**🎯 Key Features:**")
    st.markdown("""
    - 📝 Outcome tracking
    - 📈 Win rate analysis
    - 🔍 Pattern detection
    - 💡 Recommendations
    - 🏆 Competitive intel
    """)
    
    st.markdown("---")
    st.markdown("**📊 Current Stats:**")
    if analyzer.deals:
        wr = analyzer.get_win_rate()
        st.caption(f"• Total Deals: {wr['total_deals']}")
        st.caption(f"• Win Rate: {wr['win_rate']}%")
        st.caption(f"• Won: {wr['won']}")
        st.caption(f"• Lost: {wr['lost']}")
    else:
        st.caption("No data yet")
    
    st.markdown("---")
    st.markdown("**💰 Revenue Impact:**")
    st.markdown("""
    - **+$30K-50K/year** through learning
    - **Continuous improvement**
    - **Data-driven decisions**
    - **Competitive advantage**
    """)
