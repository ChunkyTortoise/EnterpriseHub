"""
Hot Lead Fast Lane - Interactive Demo
Priority lead routing and scoring system.
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.hot_lead_fastlane import HotLeadFastLane, LeadPriority, score_lead_quick

st.set_page_config(
    page_title="Hot Lead Fast Lane | GHL Real Estate",
    page_icon="🚀",
    layout="wide"
)

# Initialize session state
if "scored_leads" not in st.session_state:
    st.session_state.scored_leads = []
if "fastlane_queue" not in st.session_state:
    st.session_state.fastlane_queue = []

# Initialize Fast Lane
fastlane = HotLeadFastLane()

# Header
st.title("🚀 Hot Lead Fast Lane")
st.markdown("### Priority Lead Routing & Scoring System")
st.markdown("**Revenue Impact:** +$40K-60K/year | **Conversion:** +20% improvement")

st.divider()

# Main layout
tab1, tab2, tab3 = st.tabs(["🎯 Score New Lead", "📊 Fast Lane Queue", "📈 Analytics"])

with tab1:
    st.subheader("Score & Route New Lead")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 👤 Lead Information")
        
        lead_name = st.text_input("Lead Name", value="Michael Anderson")
        lead_email = st.text_input("Email", value="michael.anderson@email.com")
        lead_phone = st.text_input("Phone", value="(555) 123-4567")
        
        st.divider()
        
        st.markdown("#### 💰 Financial Profile")
        budget = st.number_input("Budget ($)", value=650000, step=50000, format="%d")
        timeline_days = st.slider("Days Until Ready to Buy", 0, 365, 60)
        
        st.divider()
        
        st.markdown("#### 📈 Engagement Metrics")
        engagement_score = st.slider("Engagement Score (0-100)", 0, 100, 65, 
                                     help="Based on opens, clicks, responses")
        
        st.markdown("**🎯 Intent Signals** (select all that apply):")
        intent_signals = []
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.checkbox("Pre-approved for financing", key="pre_approved"):
                intent_signals.append("pre_approved")
            if st.checkbox("Viewing scheduled", key="viewing"):
                intent_signals.append("viewing_scheduled")
            if st.checkbox("Asked about making offer", key="offer"):
                intent_signals.append("asked_about_offer")
            if st.checkbox("Multiple viewings", key="multiple"):
                intent_signals.append("multiple_viewings")
        
        with col_b:
            if st.checkbox("Requested disclosure docs", key="disclosure"):
                intent_signals.append("requested_disclosure")
            if st.checkbox("Discussed financing", key="financing"):
                intent_signals.append("discussed_financing")
            if st.checkbox("Asked detailed questions", key="questions"):
                intent_signals.append("asked_detailed_questions")
            if st.checkbox("Brought inspector", key="inspector"):
                intent_signals.append("brought_inspector")
        
        st.divider()
        
        st.markdown("#### 🏠 Property Matching")
        property_matches = st.number_input("Properties Matching Criteria", 0, 10, 2)
        
        st.markdown("#### 📍 Lead Source")
        source = st.selectbox("Source", [
            "referral", "past_client", "zillow_premier", "realtor_com",
            "google_ads", "facebook_ads", "instagram", "organic_search",
            "website_form", "open_house", "cold_call"
        ])
    
    with col2:
        st.markdown("#### 🎯 Lead Score & Routing")
        
        if st.button("🚀 Score & Route Lead", type="primary", use_container_width=True):
            with st.spinner("Analyzing lead..."):
                # Score the lead
                lead_data = {
                    "name": lead_name,
                    "email": lead_email,
                    "phone": lead_phone,
                    "budget": budget,
                    "timeline_days": timeline_days,
                    "engagement_score": engagement_score,
                    "intent_signals": intent_signals,
                    "property_matches": property_matches,
                    "source": source,
                    "id": f"L{len(st.session_state.scored_leads) + 1:03d}"
                }
                
                score_result = fastlane.score_lead(lead_data)
                
                # Route the lead
                routing_result = fastlane.route_lead(lead_data, {})
                
                # Combine results
                lead_data["score_result"] = score_result
                lead_data["routing"] = routing_result
                
                # Add to session state
                st.session_state.scored_leads.append(lead_data)
                
                # Add to fast lane if hot/urgent
                if score_result["priority"] in ["HOT", "URGENT"]:
                    st.session_state.fastlane_queue.append(lead_data)
                
                st.success("✅ Lead scored and routed!")
                st.rerun()
        
        # Display latest score
        if st.session_state.scored_leads:
            latest = st.session_state.scored_leads[-1]
            score_result = latest["score_result"]
            
            st.markdown("---")
            
            # Score display
            score = score_result["total_score"]
            priority = score_result["priority"]
            temperature = score_result["temperature"]
            
            # Color coding
            if priority == "URGENT":
                color = "🔴"
                border_color = "#ef4444"
            elif priority == "HOT":
                color = "🟠"
                border_color = "#f97316"
            elif priority == "WARM":
                color = "🟡"
                border_color = "#eab308"
            else:
                color = "⚪"
                border_color = "#6b7280"
            
            st.markdown(f"""
            <div style='border: 3px solid {border_color}; border-radius: 10px; padding: 20px; margin: 10px 0;'>
                <h2 style='text-align: center; margin: 0;'>{color} {score:.1f}/100</h2>
                <p style='text-align: center; font-size: 1.2em; margin: 5px 0;'>
                    <strong>{priority}</strong> Priority | {temperature.title()} Temperature
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Metrics
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Response Window", score_result["response_window"])
            with col_b:
                action_req = "YES ⚡" if score_result["action_required"] else "No"
                st.metric("Action Required", action_req)
            
            st.divider()
            
            # Score breakdown
            st.markdown("**📊 Score Breakdown:**")
            breakdown = score_result["breakdown"]
            
            for component, value in breakdown.items():
                progress = value / 100
                st.progress(progress, text=f"{component.title()}: {value:.1f}/100")
            
            st.divider()
            
            # Routing decision
            st.markdown("**🎯 Routing Decision:**")
            routing = latest["routing"]["routing"]
            
            st.info(f"""
            **Action:** {routing['action']}  
            **Assigned To:** {routing['assigned_to']}  
            **Method:** {routing['method']}  
            **Response Window:** {routing.get('response_window', 'N/A')}
            """)
            
            if "suggested_message" in routing:
                st.markdown("**💬 Suggested Message:**")
                st.text_area("", value=routing["suggested_message"], height=100, disabled=True)

with tab2:
    st.subheader("🔥 Fast Lane Queue")
    st.markdown("Leads requiring immediate attention")
    
    if st.session_state.fastlane_queue:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        urgent = [l for l in st.session_state.fastlane_queue if l["score_result"]["priority"] == "URGENT"]
        hot = [l for l in st.session_state.fastlane_queue if l["score_result"]["priority"] == "HOT"]
        
        with col1:
            st.metric("Total in Queue", len(st.session_state.fastlane_queue))
        with col2:
            st.metric("🔴 Urgent", len(urgent))
        with col3:
            st.metric("🟠 Hot", len(hot))
        with col4:
            avg_score = sum(l["score_result"]["total_score"] for l in st.session_state.fastlane_queue) / len(st.session_state.fastlane_queue)
            st.metric("Avg Score", f"{avg_score:.1f}")
        
        st.divider()
        
        # Queue table
        queue_data = []
        for lead in sorted(st.session_state.fastlane_queue, 
                          key=lambda x: x["score_result"]["total_score"], 
                          reverse=True):
            queue_data.append({
                "ID": lead["id"],
                "Name": lead["name"],
                "Score": f"{lead['score_result']['total_score']:.1f}",
                "Priority": lead["score_result"]["priority"],
                "Temperature": lead["score_result"]["temperature"],
                "Budget": f"${lead['budget']:,}",
                "Timeline": f"{lead['timeline_days']} days",
                "Response Window": lead["score_result"]["response_window"]
            })
        
        df = pd.DataFrame(queue_data)
        
        # Style the dataframe
        def highlight_priority(row):
            if row["Priority"] == "URGENT":
                return ['background-color: #fee2e2'] * len(row)
            elif row["Priority"] == "HOT":
                return ['background-color: #fed7aa'] * len(row)
            return [''] * len(row)
        
        st.dataframe(df.style.apply(highlight_priority, axis=1), use_container_width=True)
        
        st.divider()
        
        # Projected value
        st.markdown("**💰 Projected Pipeline Value:**")
        
        total_budget = sum(l["budget"] for l in st.session_state.fastlane_queue)
        avg_commission = total_budget * 0.025 * 0.80  # 2.5% commission, 80% split
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Property Value", f"${total_budget:,}")
        with col2:
            st.metric("Projected Commission", f"${avg_commission:,.0f}")
        
        if st.button("🗑️ Clear Queue"):
            st.session_state.fastlane_queue = []
            st.rerun()
    
    else:
        st.info("🎯 No leads in Fast Lane queue. Score leads with HOT or URGENT priority to see them here.")

with tab3:
    st.subheader("📈 Lead Scoring Analytics")
    
    if len(st.session_state.scored_leads) >= 3:
        # Score distribution
        scores = [l["score_result"]["total_score"] for l in st.session_state.scored_leads]
        priorities = [l["score_result"]["priority"] for l in st.session_state.scored_leads]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 Score Distribution**")
            fig = go.Figure(data=[go.Histogram(x=scores, nbinsx=10)])
            fig.update_layout(
                xaxis_title="Lead Score",
                yaxis_title="Count",
                showlegend=False,
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("**🎯 Priority Distribution**")
            priority_counts = pd.Series(priorities).value_counts()
            fig = px.pie(values=priority_counts.values, names=priority_counts.index)
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # Component breakdown
        st.markdown("**📊 Score Component Analysis**")
        
        components = ["budget", "engagement", "timeline", "intent", "property_fit", "source"]
        avg_scores = {}
        
        for comp in components:
            scores_comp = [l["score_result"]["breakdown"][comp] for l in st.session_state.scored_leads]
            avg_scores[comp] = sum(scores_comp) / len(scores_comp)
        
        fig = go.Figure([go.Bar(
            x=list(avg_scores.keys()),
            y=list(avg_scores.values()),
            text=[f"{v:.1f}" for v in avg_scores.values()],
            textposition='auto'
        )])
        fig.update_layout(
            xaxis_title="Component",
            yaxis_title="Average Score",
            yaxis_range=[0, 100],
            showlegend=False,
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # Statistics
        st.markdown("**📈 Scoring Statistics**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Scored", len(st.session_state.scored_leads))
        with col2:
            avg_score = sum(scores) / len(scores)
            st.metric("Average Score", f"{avg_score:.1f}")
        with col3:
            high_priority = len([p for p in priorities if p in ["HOT", "URGENT"]])
            st.metric("High Priority", high_priority)
        with col4:
            conversion_rate = high_priority / len(st.session_state.scored_leads) * 100
            st.metric("Hot Lead Rate", f"{conversion_rate:.1f}%")
    
    else:
        st.info("📊 Score at least 3 leads to see analytics.")

# Sidebar
with st.sidebar:
    st.markdown("### 🚀 Hot Lead Fast Lane")
    st.markdown("---")
    
    st.markdown("**🎯 Key Features:**")
    st.markdown("""
    - 🎯 Multi-factor lead scoring
    - 🔥 4-tier priority system
    - 🌡️ Temperature tracking
    - ⚡ Smart routing
    - 📊 Real-time analytics
    """)
    
    st.markdown("---")
    st.markdown("**💰 Revenue Impact:**")
    st.markdown("""
    - **+20% conversion** rate
    - **+$40K-60K/year** revenue
    - **Never miss** a hot lead
    - **Instant** prioritization
    """)
    
    st.markdown("---")
    st.markdown("**📊 Scoring Weights:**")
    st.caption("• Budget: 25%")
    st.caption("• Engagement: 20%")
    st.caption("• Timeline: 20%")
    st.caption("• Intent Signals: 15%")
    st.caption("• Property Fit: 10%")
    st.caption("• Source Quality: 10%")
    
    st.markdown("---")
    st.markdown("**⏱️ Response Windows:**")
    st.caption("🔴 Urgent: 15 minutes")
    st.caption("🟠 Hot: 1 hour")
    st.caption("🟡 Warm: 4 hours")
    st.caption("⚪ Cold: 24 hours")
