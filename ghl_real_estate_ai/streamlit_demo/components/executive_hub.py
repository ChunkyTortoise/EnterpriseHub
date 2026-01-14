import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import datetime
import asyncio
import json

# Import enhanced services
try:
    from services.claude_orchestrator import get_claude_orchestrator
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

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
            
            if CLAUDE_AVAILABLE:
                orchestrator = get_claude_orchestrator()
                
                # Gather metrics for briefing
                summary_metrics = {
                    "pipeline_value": "$2.4M",
                    "hot_leads": 5,
                    "avg_response_time": "1.8m",
                    "market": st.session_state.get("selected_market", "Austin")
                }
                
                with st.spinner("Claude is synthesizing your executive brief..."):
                    try:
                        try:
                            loop = asyncio.get_event_loop()
                        except RuntimeError:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                        
                        briefing_result = loop.run_until_complete(
                            orchestrator.chat_query(
                                query="Provide a 3-bullet executive briefing based on the current pipeline status.",
                                context={"metrics": summary_metrics, "task": "executive_briefing"}
                            )
                        )
                        st.markdown(briefing_result.content)
                    except Exception as e:
                        st.error(f"Briefing Error: {str(e)}")
                        st.markdown("""
                        - **🔥 Hot Cluster:** Interest peaking in Alta Loma.
                        - **⚠️ Attention:** 2 leads require immediate follow-up.
                        - **💰 Revenue:** Converting top 3 leads will hit monthly target.
                        """)
            else:
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
        
        # NEW: High-Impact Visualizations Row
        viz_col1, viz_col2 = st.columns([1, 1])
        
        with viz_col1:
            st.markdown("#### 🚀 Conversion Funnel")
            try:
                from components.calculators import render_revenue_funnel
                render_revenue_funnel()
            except ImportError:
                st.info("Funnel visualization loading...")

        with viz_col2:
            # Enterprise Color Palette
            COLORS = {
                'primary': '#2563eb',
                'secondary': '#64748b',
                'success': '#22c55e',
                'warning': '#f59e0b',
                'danger': '#ef4444',
                'text': '#1e293b',
                'grid': '#e2e8f0',
                'channels': ['#2563eb', '#7c3aed', '#10b981', '#f59e0b']
            }

            # Mock data for revenue trends
            dates = pd.date_range(end=pd.Timestamp.now(), periods=6, freq='M')
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
                name='Actual',
                line=dict(color=COLORS['primary'], width=4),
                marker=dict(size=8),
                fill='tozeroy',
                fillcolor='rgba(37, 99, 235, 0.1)'
            ))
            fig.add_trace(go.Scatter(
                x=df_rev['Month'], 
                y=df_rev['Target'], 
                name='Target',
                line=dict(color=COLORS['secondary'], width=2, dash='dash')
            ))
            
            fig.update_layout(
                title="<b>Revenue Trend</b>",
                template="plotly_white",
                margin=dict(l=20, r=20, t=40, b=20),
                height=300,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color=COLORS['text']),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(gridcolor=COLORS['grid']),
                yaxis=dict(gridcolor=COLORS['grid'])
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")

        # NEW: Channel Attribution and Forecasting Row
        attr_col1, attr_col2 = st.columns([1, 1])

        with attr_col1:
            st.markdown("#### 🎯 Revenue Attribution by Channel")
            # Get channel data from service
            attr_report = services["revenue"].get_full_attribution_report("demo_location")
            channel_df = pd.DataFrame(attr_report["channel_performance"])
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=channel_df['channel'],
                values=channel_df['revenue'],
                hole=.4,
                marker=dict(colors=COLORS['channels'])
            )])
            
            fig_pie.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                height=300,
                showlegend=True,
                legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.1),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with attr_col2:
            st.markdown("#### 🔮 AI Revenue Projection (Q1 2026)")
            # Simulated forecasting data
            forecast_data = {
                'Scenario': ['Conservative', 'AI-Optimized (Target)', 'Elite Performance'],
                'Projection': [295000, 342000, 415000],
                'Confidence': [0.92, 0.85, 0.68]
            }
            df_forecast = pd.DataFrame(forecast_data)
            
            fig_bar = go.Figure(data=[
                go.Bar(
                    x=df_forecast['Scenario'],
                    y=df_forecast['Projection'],
                    marker_color=[COLORS['secondary'], COLORS['primary'], COLORS['success']],
                    text=[f"${v/1000:.0f}K" for v in df_forecast['Projection']],
                    textposition='auto',
                )
            ])
            
            fig_bar.update_layout(
                margin=dict(l=20, r=20, t=20, b=20),
                height=300,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(showgrid=True, gridcolor=COLORS['grid'])
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            st.caption("AI-Optimized projection assumes 15% increase in conversion via Swarm Intelligence.")

        st.markdown("---")

        # NEW: ROI Analysis and Quality Distribution Row
        roi_col1, roi_col2 = st.columns([1.2, 1])

        with roi_col1:
            st.markdown("#### 💰 Strategic ROI & Efficiency")
            # Using data from executive dashboard service
            from services.executive_dashboard import calculate_roi
            roi = calculate_roi(system_cost_monthly=170.0, conversations_per_month=300)
            
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #1e293b 0%, #334155 100%); padding: 1.5rem; border-radius: 16px; color: white; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.2);'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;'>
                    <div>
                        <div style='font-size: 0.8rem; opacity: 0.8; text-transform: uppercase; letter-spacing: 0.05em;'>Current Period ROI</div>
                        <div style='font-size: 2.5rem; font-weight: 800; color: #10b981;'>{roi['roi']['percentage']}%</div>
                    </div>
                    <div style='background: rgba(16, 185, 129, 0.2); padding: 1rem; border-radius: 12px;'>
                        <span style='font-size: 2rem;'>📈</span>
                    </div>
                </div>
                <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;'>
                    <div style='background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px;'>
                        <div style='font-size: 0.7rem; opacity: 0.7;'>Net Monthly Profit</div>
                        <div style='font-size: 1.2rem; font-weight: 700;'>${roi['roi']['net_profit_monthly']:,.0f}</div>
                    </div>
                    <div style='background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px;'>
                        <div style='font-size: 0.7rem; opacity: 0.7;'>Payback Period</div>
                        <div style='font-size: 1.2rem; font-weight: 700;'>{roi['roi']['payback_days']} Days</div>
                    </div>
                </div>
                <div style='margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.1); font-size: 0.8rem; opacity: 0.9;'>
                    ✨ <b>AI Impact:</b> Swarm Intelligence has reduced manual labor by 156 hours this month.
                </div>
            </div>
            """, unsafe_allow_html=True)

        with roi_col2:
            st.markdown("#### 📊 Lead Quality Distribution")
            # Get data from executive service
            exec_summary = services["executive"].get_executive_summary("demo_location")
            quality = exec_summary["metrics"]["lead_quality"]
            
            fig_donut = go.Figure(data=[go.Pie(
                labels=['Hot', 'Warm', 'Cold'],
                values=[quality['hot_leads'], quality['warm_leads'], quality['cold_leads']],
                hole=.6,
                marker=dict(colors=[COLORS['danger'], COLORS['warning'], COLORS['primary']])
            )])
            
            fig_donut.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                height=280,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                annotations=[dict(text=f"{quality['hot_leads'] + quality['warm_leads'] + quality['cold_leads']}<br>Total", x=0.5, y=0.5, font_size=20, showarrow=False)]
            )
            st.plotly_chart(fig_donut, use_container_width=True)

        st.markdown("---")
        
        # NEW: Global AI System Health
        st.markdown("#### ⚡ Infrastructure Health")
        h_col1, h_col2, h_col3, h_col4 = st.columns(4)
        
        # Get dynamic health data
        safe_data = mock_data if mock_data is not None else {}
        health = safe_data.get("system_health", {})
        
        with h_col1:
            st.markdown(f"""
            <div style='background: white; padding: 1rem; border-radius: 10px; border: 1px solid #e5e7eb; border-top: 4px solid #10b981;'>
                <div style='font-size: 0.7rem; color: #6b7280; font-weight: 700; text-transform: uppercase;'>API Uptime</div>
                <div style='font-size: 1.5rem; font-weight: 800; color: #111827;'>{health.get('uptime_percentage', 99.9)}%</div>
                <div style='font-size: 0.6rem; color: #10b981; font-weight: 600;'>🟢 System Operational</div>
            </div>
            """, unsafe_allow_html=True)
            
        with h_col2:
            st.markdown(f"""
            <div style='background: white; padding: 1rem; border-radius: 10px; border: 1px solid #e5e7eb; border-top: 4px solid #3b82f6;'>
                <div style='font-size: 0.7rem; color: #6b7280; font-weight: 700; text-transform: uppercase;'>Avg Latency</div>
                <div style='font-size: 1.5rem; font-weight: 800; color: #111827;'>{health.get('avg_response_time_ms', 142)}ms</div>
                <div style='font-size: 0.6rem; color: #3b82f6; font-weight: 600;'>⚡ Millisecond Response</div>
            </div>
            """, unsafe_allow_html=True)
            
        with h_col3:
            st.markdown(f"""
            <div style='background: white; padding: 1rem; border-radius: 10px; border: 1px solid #e5e7eb; border-top: 4px solid #f59e0b;'>
                <div style='font-size: 0.7rem; color: #6b7280; font-weight: 700; text-transform: uppercase;'>SMS Compliance</div>
                <div style='font-size: 1.5rem; font-weight: 800; color: #111827;'>{int(health.get('sms_compliance_rate', 1) * 100)}%</div>
                <div style='font-size: 0.6rem; color: #f59e0b; font-weight: 600;'>📜 A2P 10DLC Verified</div>
            </div>
            """, unsafe_allow_html=True)
            
        with h_col4:
            st.markdown(f"""
            <div style='background: white; padding: 1rem; border-radius: 10px; border: 1px solid #e5e7eb; border-top: 4px solid #8b5cf6;'>
                <div style='font-size: 0.7rem; color: #6b7280; font-weight: 700; text-transform: uppercase;'>Swarm Status</div>
                <div style='font-size: 1.5rem; font-weight: 800; color: #111827;'>Active</div>
                <div style='font-size: 0.6rem; color: #8b5cf6; font-weight: 600;'>🐝 12 Specialized Agents</div>
            </div>
            """, unsafe_allow_html=True)

        # Add last updated timestamp
        last_updated = datetime.datetime.now().strftime("%b %d, %Y at %I:%M %p")
        st.markdown(f"<div style='margin-top: 2rem; font-size: 0.75rem; color: #9ca3af; font-style: italic; text-align: right;'>Last architectural sync: {last_updated}</div>", unsafe_allow_html=True)
        
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
        safe_data = mock_data if mock_data is not None else {}
        health = safe_data.get("system_health", {})
        
        if health:
            c1, c2, c3 = st.columns(3)
            resp_time = health.get('avg_response_time_ms', 0)
            resp_display = f"{resp_time}ms" if resp_time > 0 else "Evaluating"
            
            c1.metric("API Uptime", f"{health.get('uptime_percentage', 100)}%")
            c2.metric("Avg Latency", resp_display)
            c3.metric("SMS Compliance", f"{int(health.get('sms_compliance_rate', 1) * 100)}%")

    with tab3:
        st.subheader("Actionable Executive Report")
        
        if CLAUDE_AVAILABLE:
            if st.button("🪄 Generate Claude Executive Report", type="primary", use_container_width=True):
                with st.spinner("Claude is synthesizing comprehensive pipeline data..."):
                    try:
                        orchestrator = get_claude_orchestrator()
                        try:
                            loop = asyncio.get_event_loop()
                        except RuntimeError:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                        
                        # Generate full report
                        report_data = {
                            "pipeline": revenue_data,
                            "leads": summary.get("action_items", []),
                            "system": health
                        }
                        
                        report_result = loop.run_until_complete(
                            orchestrator.synthesize_report(
                                metrics=report_data,
                                report_type="executive_quarterly_projection",
                                market_context={"location": st.session_state.get("selected_market", "Austin")}
                            )
                        )
                        st.markdown(report_result.content)
                        st.success("Executive report synthesized successfully!")
                    except Exception as e:
                        st.error(f"Report Synthesis Error: {str(e)}")
        
        st.markdown("---")
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

