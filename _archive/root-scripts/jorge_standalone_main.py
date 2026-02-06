"""
Jorge AI Standalone Dashboard - Main Application
=============================================

Complete standalone dashboard combining all components.
Optimized for Jorge's real estate team deployment.

Run with: streamlit run jorge_standalone_main.py --server.port 8505
"""

# Import all components from separate files
exec(open('jorge_standalone_dashboard.py').read())
exec(open('jorge_standalone_dashboard_ui.py').read())

# ============================================================================
# TAB RENDERING FUNCTIONS
# ============================================================================

def render_lead_bot_tab():
    """Render complete Lead Bot interface."""
    st.header("🎯 Lead Bot Command Center")
    st.markdown("**3-7-30 Day Follow-up Sequences & Lead Nurturing**")

    manager = get_jorge_bot_manager()
    metrics = run_async_safe(manager.get_lead_bot_metrics())

    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Live Chat", "📊 KPIs", "📈 Analytics", "⚙️ Settings"])

    with tab1:
        render_chat_interface(manager, "lead")

    with tab2:
        st.subheader("📊 Lead Bot Performance KPIs")
        render_performance_metrics_grid(metrics, "lead")

        # Additional insights
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**💡 Performance Insights**")
            insights = [
                "🟢 Response time improved 15% this week",
                "🟡 Day 30 sequences need optimization",
                "🟢 Success rate above 85% target",
                "🔵 Peak performance during 9-5 PM"
            ]
            for insight in insights:
                st.markdown(f"• {insight}")

        with col2:
            st.markdown("**📈 Optimization Recommendations**")
            recommendations = [
                "📈 **Day 30 Refresh**: Update messaging templates",
                "⏰ **Weekend Strategy**: Deploy lighter approach",
                "🎯 **Peak Hours**: Increase capacity 9-5 PM",
                "🔄 **A/B Testing**: Try new email templates"
            ]
            for rec in recommendations:
                st.markdown(f"• {rec}")

    with tab3:
        st.subheader("📈 Lead Bot Analytics")
        render_analytics_charts(metrics, "lead")

        # Pipeline overview
        st.markdown("---")
        st.markdown("**🔄 Active Lead Pipeline**")
        pipeline_data = [
            {"Name": "Sarah Johnson", "Step": "Day 7 Call", "Status": "Scheduled", "Score": 85},
            {"Name": "Mike Chen", "Step": "Day 3 SMS", "Status": "Sent", "Score": 73},
            {"Name": "Jennifer White", "Step": "Day 30 Nudge", "Status": "Delivered", "Score": 91},
            {"Name": "David Brown", "Step": "Day 14 Email", "Status": "Opened", "Score": 67}
        ]

        df_pipeline = pd.DataFrame(pipeline_data)
        st.dataframe(df_pipeline, use_container_width=True)

    with tab4:
        st.subheader("⚙️ Lead Bot Configuration")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Sequence Timing**")
            day_3_delay = st.slider("Day 3 Delay (hours)", 24, 120, 72)
            day_7_delay = st.slider("Day 7 Delay (hours)", 120, 240, 168)

            st.markdown("**Response Thresholds**")
            engagement_threshold = st.slider("Engagement Score Threshold", 50, 100, 75)

        with col2:
            st.markdown("**Channel Preferences**")
            enable_sms = st.checkbox("Enable SMS Sequences", value=True)
            enable_calls = st.checkbox("Enable Voice AI Calls", value=True)
            enable_email = st.checkbox("Enable Email Follow-ups", value=True)

            st.markdown("**AI Behavior**")
            response_tone = st.selectbox("Response Tone", ["Professional", "Friendly", "Urgent"])

def render_seller_bot_tab():
    """Render complete Seller Bot interface."""
    st.header("💼 Jorge Seller Bot Command Center")
    st.markdown("**Confrontational Qualification & Stall-Breaking Protocol**")

    manager = get_jorge_bot_manager()
    metrics = run_async_safe(manager.get_seller_bot_metrics())

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Live Chat", "📊 KPIs", "📈 Analytics", "🧠 Jorge Insights"])

    with tab1:
        render_chat_interface(manager, "seller")

        # Jorge strategy monitor
        st.markdown("---")
        st.markdown("**🔴 Live Jorge Strategy Monitor**")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.info("🟢 3 active qualifications")
            st.caption("Avg session: 3.2 minutes")

        with col2:
            st.warning("🟡 2 stalls detected")
            st.caption("Auto-handling with take-away")

        with col3:
            st.success("🚀 1 take-away deployed")
            st.caption("Result pending...")

    with tab2:
        st.subheader("📊 Jorge Performance KPIs")
        render_performance_metrics_grid(metrics, "seller")

        # Jorge vs Human comparison
        st.markdown("---")
        st.markdown("**🤖 Jorge vs Human Agent Performance**")
        comparison_data = pd.DataFrame({
            "Metric": ["Qualification Time", "Close Rate", "Lead Quality", "Consistency"],
            "Jorge": [4.2, 67.8, 84.7, 98.2],
            "Human Average": [8.7, 45.3, 72.1, 76.5],
            "Industry Avg": [12.3, 38.7, 68.9, 65.2]
        })

        fig = px.bar(comparison_data, x="Metric", y=["Jorge", "Human Average", "Industry Avg"],
                     title="Performance Comparison", barmode="group")
        fig = style_chart_professional(fig)
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("📈 Jorge Analytics")
        render_analytics_charts(metrics, "seller")

        # Stall detection insights
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🎯 Jorge's Tactical Performance**")
            jorge_moves = [
                {"move": "Price Reality Check", "success": 89.2},
                {"move": "Timeline Pressure", "success": 76.5},
                {"move": "Competition Angle", "success": 83.7},
                {"move": "Take-Away Close", "success": 91.4}
            ]

            for move in jorge_moves:
                st.markdown(f"**{move['move']}**")
                st.progress(move['success']/100)
                st.caption(f"Success Rate: {move['success']}%")

        with col2:
            st.markdown("**📊 Psychological Commitment Tracking**")
            pcs_data = [
                ("Initial Contact", 45.2, 12.3),
                ("2nd Exchange", 62.8, 34.7),
                ("3rd Exchange", 74.3, 58.9),
                ("4th+ Exchange", 81.7, 73.2)
            ]

            for interaction, pcs, conversion in pcs_data:
                st.metric(interaction, f"PCS: {pcs}", f"{conversion}% convert")

    with tab4:
        st.subheader("🧠 Jorge's Seller Intelligence")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Recent Qualification Insights**")
            insights = [
                {"seller": "Robert Miller", "insight": "High motivation but unrealistic timeline", "confidence": 87},
                {"seller": "Lisa Davis", "insight": "Price testing market, not serious", "confidence": 92},
                {"seller": "Tom Wilson", "insight": "Financial distress detected", "confidence": 78},
                {"seller": "Amy Chen", "insight": "Perfect candidate for quick close", "confidence": 95}
            ]

            for insight in insights:
                with st.container():
                    st.markdown(f"**{insight['seller']}**")
                    st.write(insight['insight'])
                    st.progress(insight['confidence']/100, text=f"Confidence: {insight['confidence']}%")
                    st.divider()

        with col2:
            st.markdown("**🧠 Market Psychology Patterns**")
            patterns = [
                "73% mention Zillow in first 3 messages",
                "'Get back to you' spikes 40% in tax season",
                "Motivated sellers use future tense 67% more",
                "Price objections peak on Mondays (+47%)"
            ]

            for pattern in patterns:
                st.markdown(f"• {pattern}")

            st.markdown("**💡 Jorge's Recommendations**")
            st.success("✅ Increase confrontational tone on Mondays")
            st.info("💡 Pre-emptive Zillow defense in opener")
            st.warning("⚠️ Timeline pressure more effective Q1")

def render_buyer_bot_tab():
    """Render complete Buyer Bot interface."""
    st.header("🏠 Buyer Bot Command Center")
    st.markdown("**Property Matching & Buyer Qualification**")

    manager = get_jorge_bot_manager()
    metrics = run_async_safe(manager.get_buyer_bot_metrics())

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Live Chat", "📊 KPIs", "🏠 Properties", "📈 Analytics"])

    with tab1:
        render_chat_interface(manager, "buyer")

    with tab2:
        st.subheader("📊 Buyer Bot Performance KPIs")
        render_performance_metrics_grid(metrics, "buyer")

        # Performance by hour heatmap
        st.markdown("---")
        st.markdown("**⏰ Performance by Hour of Day**")
        hours = list(range(24))
        performance_by_hour = [
            65, 70, 72, 68, 71, 75, 78, 82, 89, 91, 93, 92,
            90, 88, 87, 89, 91, 88, 85, 82, 78, 75, 72, 68
        ]

        fig_heatmap = go.Figure(data=go.Heatmap(
            z=[performance_by_hour],
            x=hours,
            y=["Performance"],
            colorscale='Blues',
            showscale=True
        ))
        fig_heatmap.update_layout(title="Performance Heatmap", height=200)
        fig_heatmap = style_chart_professional(fig_heatmap)
        st.plotly_chart(fig_heatmap, use_container_width=True)

    with tab3:
        st.subheader("🏠 Property Matching Interface")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Search Criteria**")
            price_min, price_max = st.slider("Price Range", 700000, 1200000, (600000, 800000), format="$%d")
            bedrooms = st.selectbox("Bedrooms", [2, 3, 4, 5], index=1)
            areas = st.multiselect("Areas", ["Rancho Cucamonga", "Victoria Gardens", "Etiwanda", "Day Creek"], default=["Rancho Cucamonga"])

            if st.button("🔍 Find Matches", use_container_width=True):
                st.session_state['search_triggered'] = True

        with col2:
            st.markdown("**Recent Property Matches**")
            properties = [
                {"Address": "123 Oak St, Rancho Cucamonga", "Price": "$725K", "Beds": 3, "Match": "92%"},
                {"Address": "456 Pine Ave, Victoria Gardens", "Price": "$685K", "Beds": 4, "Match": "88%"},
                {"Address": "789 Elm Dr, Etiwanda", "Price": "$750K", "Beds": 3, "Match": "85%"},
                {"Address": "321 Maple Ln, Day Creek", "Price": "$645K", "Beds": 3, "Match": "90%"}
            ]

            df_properties = pd.DataFrame(properties)
            st.dataframe(df_properties, use_container_width=True)

    with tab4:
        st.subheader("📈 Buyer Bot Analytics")
        render_analytics_charts(metrics, "buyer")

        # Advanced funnel analysis
        st.markdown("---")
        st.markdown("**🔄 Advanced Buyer Journey Analysis**")

        funnel_metrics = [
            ("Initial Inquiry", 100, 0),
            ("Properties Viewed", 78, 22),
            ("Matches Sent", 45, 42),
            ("Showings Scheduled", 34, 24),
            ("Offers Made", 23, 32),
            ("Closed Deals", 3, 87)
        ]

        for stage, count, drop in funnel_metrics:
            col_stage, col_count, col_drop = st.columns([2, 1, 1])
            with col_stage:
                st.write(f"**{stage}**")
            with col_count:
                st.write(f"{count} leads")
            with col_drop:
                if drop > 0:
                    st.write(f"📉 {drop}% drop")
                else:
                    st.write("🟢 Entry point")

def render_performance_summary():
    """Render cross-bot performance summary."""
    st.markdown("---")
    st.header("⚡ Cross-Bot Performance Dashboard")

    manager = get_jorge_bot_manager()
    performance_summary = run_async_safe(manager.get_performance_summary())
    real_time = run_async_safe(manager.get_real_time_activity())

    # Performance comparison
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**🎯 Lead Bot**")
        lead_perf = performance_summary.get("lead_bot", {})
        st.metric("Success Rate", f"{lead_perf.get('success_rate', 0):.1f}%")
        st.metric("Response Time", f"{lead_perf.get('response_time', 0):.1f}s")
        st.metric("Efficiency", f"{lead_perf.get('efficiency', 0):.1f}/100")

    with col2:
        st.markdown("**🏠 Buyer Bot**")
        buyer_perf = performance_summary.get("buyer_bot", {})
        st.metric("Match Accuracy", f"{buyer_perf.get('match_accuracy', 0):.1f}%")
        st.metric("Response Time", f"{buyer_perf.get('response_time', 0):.1f}s")
        st.metric("Conversion Rate", f"{buyer_perf.get('conversion_rate', 0):.1f}%")

    with col3:
        st.markdown("**💼 Seller Bot**")
        seller_perf = performance_summary.get("seller_bot", {})
        st.metric("Close Rate", f"{seller_perf.get('close_rate', 0):.1f}%")
        st.metric("Response Time", f"{seller_perf.get('response_time', 0):.1f}s")
        st.metric("Effectiveness", f"{seller_perf.get('effectiveness', 0):.1f}/100")

    # Real-time activity monitor
    st.markdown("---")
    st.markdown("**🔴 Live Activity Monitor**")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        active_total = sum(real_time.get("active_conversations", {}).values())
        st.metric("Active Conversations", active_total, "+3 vs 1hr")

    with col2:
        messages_total = sum(real_time.get("messages_per_minute", {}).values())
        st.metric("Messages/Min", f"{messages_total:.1f}", "+0.8/min")

    with col3:
        st.metric("System Status", "🟢 Operational", "99.8% uptime")

    with col4:
        peak_bot = max(real_time.get("active_conversations", {}), key=real_time.get("active_conversations", {}).get, default="Seller Bot")
        st.metric("Peak Load Bot", peak_bot.replace("_", " ").title())

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point."""

    # Apply Jorge branding and styling
    inject_jorge_branding_css()

    # Render header
    render_jorge_header()

    # Sidebar navigation
    selected_bot = render_sidebar_navigation()

    # Main content area based on selection
    if selected_bot == "🎯 Lead Bot":
        render_lead_bot_tab()
    elif selected_bot == "🏠 Buyer Bot":
        render_buyer_bot_tab()
    elif selected_bot == "💼 Seller Bot":
        render_seller_bot_tab()

    # Global performance summary
    render_performance_summary()

    # Footer
    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: #8B949E; padding: 1rem;">
            <p>Jorge AI Unified Bot Dashboard v2.0 | Standalone Edition</p>
            <p>Optimized for Jorge Real Estate Team | © 2026</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()