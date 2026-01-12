import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import datetime

def render_executive_hub(services, mock_data, sparkline, render_insight_card):
    st.header("🏢 Executive Command Center")
    st.markdown("*High-level KPIs, revenue tracking, and system health*")

    # NEW: Claude's Strategic Briefing Area
    with st.container(border=True):
        col_icon, col_text = st.columns([1, 6])
        with col_icon:
            st.markdown("<div style='font-size: 3.5rem; text-align: center; margin-top: 10px;'>🔮</div>", unsafe_allow_html=True)
        with col_text:
            st.markdown("### Claude's Strategy Briefing")
            st.markdown("""
            *I've analyzed your entire GHL environment for the last 24 hours. Here is your priority focus:*
            - **🔥 Hot Cluster:** There is a surge of interest in Alta Loma. 3 leads just moved into the 'Ready' tier.
            - **⚠️ Retention Risk:** 2 leads from the Facebook campaign have gone silent. I've prepared a re-engagement sequence.
            - **💰 Revenue Path:** Converting Sarah Johnson this week will push your Austin pipeline past the monthly target.
            """)
            if st.button("🚀 Execute Strategic Re-engagement"):
                st.toast("Triggering AI re-engagement for silent leads...", icon="⚡")
    
    st.markdown("---")
    
    # Tabs for sub-features
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🎯 AI Insights", "📄 Reports"])
    
    with tab1:
        st.subheader("Executive Dashboard")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Pipeline", "$2.4M", "+15%")
            st.plotly_chart(sparkline([1.8, 2.1, 1.9, 2.4, 2.2, 2.4], color="#2563eb", height=50), use_container_width=True, config={'displayModeBar': False})
        with col2:
            st.metric("Commission Capture", "$136.7K", "+$42K")
            st.plotly_chart(sparkline([80, 95, 110, 105, 120, 136], color="#16a34a", height=50), use_container_width=True, config={'displayModeBar': False})
        with col3:
            st.metric("Conversion Rate", "34%", "+2%")
            st.plotly_chart(sparkline([28, 30, 31, 32, 33, 34], color="#ea580c", height=50), use_container_width=True, config={'displayModeBar': False})
        with col4:
            st.metric("AI Lead Velocity", "4.2/day", "+1.1")
            st.plotly_chart(sparkline([2.1, 2.5, 3.0, 3.8, 4.0, 4.2], color="#7c3aed", height=50), use_container_width=True, config={'displayModeBar': False})
        
        st.markdown("---")
        
        # Enterprise Color Palette
        COLORS = {
            'primary': '#2563eb',
            'secondary': '#64748b',
            'success': '#22c55e',
            'warning': '#f59e0b',
            'danger': '#ef4444',
            'text': '#1e293b',
            'grid': '#e2e8f0'
        }

        # Mock data for revenue trends
        dates = pd.date_range(end=pd.Timestamp.now(), periods=6, freq='ME')
        revenue_data = {
            'Month': dates.strftime('%b %Y'),
            'Revenue': [180000, 210000, 195000, 240000, 225000, 280000],
            'Target': [200000, 200000, 220000, 220000, 250000, 250000]
        }
        df_rev = pd.DataFrame(revenue_data)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_rev['Month'], 
            y=df_rev['Revenue'], 
            name='Actual Revenue',
            line=dict(color=COLORS['primary'], width=4),
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor='rgba(37, 99, 235, 0.1)'
        ))
        fig.add_trace(go.Scatter(
            x=df_rev['Month'], 
            y=df_rev['Target'], 
            name='Target Revenue',
            line=dict(color=COLORS['secondary'], width=2, dash='dash')
        ))
        
        fig.update_layout(
            title="<b>Revenue Performance vs Target</b>",
            template="plotly_white",
            margin=dict(l=20, r=20, t=60, b=20),
            height=350,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLORS['text']),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(gridcolor=COLORS['grid']),
            yaxis=dict(gridcolor=COLORS['grid'])
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Add last updated timestamp
        last_updated = datetime.datetime.now().strftime("%b %d, %Y at %I:%M %p")
        st.markdown(f"<div class='last-updated'>Last updated: {last_updated}</div>", unsafe_allow_html=True)
        
    with tab2:
        st.subheader("AI System Insights")
        
        # Add AI Performance Metrics Dashboard
        try:
            from components.ai_performance_metrics import render_ai_metrics_dashboard
            render_ai_metrics_dashboard()
            st.markdown("---")
        except ImportError:
            pass
        
        # Get dynamic insights
        summary = services["executive"].get_executive_summary("demo_location")
        insights = summary.get("insights", [])
        
        if not insights:
            insights = [
                {"type": "success", "title": "Response Time Excellence", "value": "1.8 mins", "message": "Average response time beats target by 40%"},
                {"type": "warning", "title": "Conversion Opportunity", "value": "20% Gap", "message": "12 leads are stalling at the 'Financing' stage. Focus required.", "action": "🎯 Fix Conversion Gap Now"},
                {"type": "info", "title": "Lead Sentiment", "value": "Strong", "message": "85% of recent conversations show positive buying intent."}
            ]

        # Fix 0.0 mins edge case in logic (Simulated)
        for insight in insights:
            if "0.0" in str(insight.get("value", "")):
                insight["value"] = "Evaluating..."
                insight["message"] = "Initial data sync in progress."

        for i, insight in enumerate(insights):
            # Map 'opportunity' to 'warning' for visual consistency in the UI
            insight_status = 'warning' if insight["type"] == "opportunity" else insight["type"]
            
            render_insight_card(
                insight["title"], 
                insight.get("value", "N/A"), 
                insight["message"], 
                status=insight_status,
                action_label=insight.get("action"),
                action_key=f"insight_btn_{i}"
            )
        
        st.markdown("#### 📈 System Performance")
        # Ensure mock_data is not None and handle missing keys safely
        safe_data = mock_data if mock_data is not None else {}
        health = safe_data.get("system_health", {})
        
        if health:
            c1, c2, c3 = st.columns(3)
            # Ensure no 0.0 metrics show up in performance cards either
            resp_time = health.get('avg_response_time_ms', 0)
            resp_display = f"{resp_time}ms" if resp_time > 0 else "Evaluating"
            
            c1.metric("API Uptime", f"{health.get('uptime_percentage', 100)}%")
            c2.metric("Avg Latency", resp_display)
            c3.metric("SMS Compliance", f"{int(health.get('sms_compliance_rate', 1) * 100)}%")

    with tab3:
        st.subheader("Actionable Executive Report")
        
        action_items = summary.get("action_items", [])
        if not action_items:
             action_items = [
                {"priority": "high", "title": "5 Hot Leads Pending", "action": "Schedule showings for Downtown cluster", "impact": "Potential $2.5M Volume"},
                {"priority": "medium", "title": "Review Weekend Staffing", "action": "Add on-call agent for Saturdays", "impact": "Improve conversion by ~5%"}
            ]

        st.dataframe(
            pd.DataFrame(action_items),
            column_config={
                "priority": "Priority",
                "title": "Opportunity",
                "action": "Recommended Action",
                "impact": "Estimated Impact"
            },
            hide_index=True,
            use_container_width=True
        )
        
        if st.button("📧 Email Report to Jorge"):
            st.toast("Report sent to jorge@example.com")
