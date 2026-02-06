# ============================================================================
# UI COMPONENTS FOR JORGE STANDALONE DASHBOARD
# ============================================================================

def render_jorge_header():
    """Render the professional Jorge-branded header."""
    st.markdown("""
        <div class="jorge-header">
            <h1 class="jorge-brand">🤖 JORGE AI</h1>
            <p class="jorge-tagline">Unified Bot Command Center | Real Estate Intelligence Platform</p>
        </div>
    """, unsafe_allow_html=True)

def render_sidebar_navigation():
    """Render optimized sidebar navigation."""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h2 style="color: #1E88E5; font-family: 'Space Grotesk', sans-serif; margin-bottom: 0;">🤖 JORGE AI</h2>
            <p style="color: #8B949E; font-size: 0.8rem; letter-spacing: 0.1em; margin-top: 0.5rem;">BOT COMMAND CENTER</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Bot selection
        selected_bot = st.radio(
            "**Select Bot:**",
            ["🎯 Lead Bot", "🏠 Buyer Bot", "💼 Seller Bot"],
            index=0,
            key="bot_selection"
        )

        st.markdown("---")

        # System health status
        st.markdown("### 🔗 System Health")
        manager = get_jorge_bot_manager()
        health = run_async_safe(manager.get_system_health())

        for system, status in health.items():
            status_class = "status-online" if "🟢" in status else "status-warning" if "🟡" in status else "status-offline"
            st.markdown(f'<p class="{status_class}"><strong>{system.replace("_", " ").title()}:</strong> {status}</p>', unsafe_allow_html=True)

        st.markdown("---")

        # Quick actions
        st.markdown("### ⚡ Quick Actions")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh", use_container_width=True):
                st.cache_resource.clear()
                st.rerun()

        with col2:
            if st.button("📊 Export", use_container_width=True):
                st.toast("Export initiated!", icon="📊")

        if st.button("📱 Mobile View", use_container_width=True, help="Optimize for mobile devices"):
            st.session_state['mobile_mode'] = not st.session_state.get('mobile_mode', False)
            st.rerun()

        st.markdown("---")
        st.caption("v2.0.0 Standalone | Jorge Real Estate")

        return selected_bot

def render_performance_metrics_grid(metrics: Dict[str, Any], bot_type: str):
    """Render a responsive metrics grid."""
    mobile_mode = st.session_state.get('mobile_mode', False)
    cols = 2 if mobile_mode else 4

    if bot_type == "lead":
        metric_groups = [
            [
                ("Active Sequences", metrics.get("active_sequences", 0), "+5"),
                ("Day 3 Response", f"{metrics.get('day_3_response_rate', 0):.1f}%", "+3.2%")
            ],
            [
                ("Re-engagement Rate", f"{metrics.get('reengagement_rate', 0):.1f}%", "+5.8%"),
                ("Day 7 Success", f"{metrics.get('day_7_call_success', 0):.1f}%", "+2.1%")
            ],
            [
                ("Hot Leads", metrics.get("hot_leads_generated", 0), "+3"),
                ("Avg Score", f"{metrics.get('avg_engagement_score', 0):.1f}", "+1.5")
            ],
            [
                ("Conversion", f"{metrics.get('pipeline_conversion', 0):.1f}%", "+4.2%"),
                ("Recovery Rate", f"{metrics.get('day_30_recovery_rate', 0):.1f}%", "+1.8%")
            ]
        ]
    elif bot_type == "seller":
        metric_groups = [
            [
                ("Qualifications", metrics.get("total_qualifications", 0), "+12"),
                ("Qualification Rate", f"{metrics.get('qualification_rate', 0):.1f}%", "+3.4%")
            ],
            [
                ("Stall Detection", f"{metrics.get('stall_detection_rate', 0):.1f}%", "+5.2%"),
                ("Take-Away Success", f"{metrics.get('takeaway_close_success', 0):.1f}%", "+8.1%")
            ],
            [
                ("Avg FRS Score", f"{metrics.get('avg_frs_score', 0):.1f}", "+2.3"),
                ("Hot Leads", metrics.get("hot_leads", 0), "+4")
            ],
            [
                ("Voice Handoffs", metrics.get("voice_handoffs", 0), "+2"),
                ("Listing Conv.", f"{metrics.get('conversion_to_listing', 0):.1f}%", "+6.7%")
            ]
        ]
    else:  # buyer
        metric_groups = [
            [
                ("Buyers Qualified", metrics.get("total_buyers_qualified", 0), "+8"),
                ("Financial Ready", f"{metrics.get('avg_financial_readiness', 0):.1f}%", "+2.3%")
            ],
            [
                ("Matches Sent", metrics.get("property_matches_sent", 0), "+23"),
                ("Match Accuracy", f"{metrics.get('avg_match_accuracy', 0):.1f}%", "+1.8%")
            ],
            [
                ("Showings", metrics.get("showing_bookings", 0), "+5"),
                ("Offers", metrics.get("offer_submissions", 0), "+2")
            ],
            [
                ("Closed", metrics.get("closed_transactions", 0), "+1"),
                ("Days to Offer", f"{metrics.get('avg_days_to_offer', 0):.1f}", "-2.3")
            ]
        ]

    # Create responsive grid
    if mobile_mode:
        for i in range(0, len(metric_groups), 2):
            col1, col2 = st.columns(2)
            with col1:
                if i < len(metric_groups):
                    for label, value, delta in metric_groups[i]:
                        st.metric(label, value, delta)
            with col2:
                if i + 1 < len(metric_groups):
                    for label, value, delta in metric_groups[i + 1]:
                        st.metric(label, value, delta)
    else:
        col1, col2, col3, col4 = st.columns(4)
        for i, col in enumerate([col1, col2, col3, col4]):
            if i < len(metric_groups):
                with col:
                    for label, value, delta in metric_groups[i]:
                        st.metric(label, value, delta)

def render_chat_interface(manager, bot_type: str):
    """Render unified chat interface for all bots."""
    st.subheader(f"💬 {bot_type.title()} Bot Chat Interface")

    # Chat history key
    chat_key = f"{bot_type}_chat_history"

    col1, col2 = st.columns([1, 2] if not st.session_state.get('mobile_mode', False) else [1, 1])

    with col1:
        # Bot-specific selection panel
        if bot_type == "lead":
            st.markdown("**Active Lead Selection**")
            selected_contact = st.selectbox(
                "Select Lead:",
                ["Sarah Johnson (Day 7)", "Mike Chen (Day 3)", "Jennifer White (Day 30)"],
                key=f"{bot_type}_contact_selection"
            )
            sequence_step = st.selectbox(
                "Sequence Step:",
                ["day_3", "day_7", "day_14", "day_30"],
                index=1,
                key=f"{bot_type}_sequence_step"
            )
        elif bot_type == "seller":
            st.markdown("**Active Seller Selection**")
            selected_contact = st.selectbox(
                "Select Seller:",
                ["Robert Miller (Motivated)", "Lisa Davis (Price Testing)", "Tom Wilson (Unresponsive)"],
                key=f"{bot_type}_contact_selection"
            )
            st.write("**Profile:**")
            st.write("• Property: 123 Maple St")
            st.write("• Est. Value: $850K")
            st.write("• Timeline: 30 days")
        else:  # buyer
            st.markdown("**Active Buyer Selection**")
            selected_contact = st.selectbox(
                "Select Buyer:",
                ["Alex Thompson (Pre-approved)", "Maria Garcia (Searching)", "John Smith (First-time)"],
                key=f"{bot_type}_contact_selection"
            )
            st.write("**Profile:**")
            st.write("• Budget: $600K-$800K")
            st.write("• Areas: Rancho Cucamonga, Victoria Gardens")
            st.write("• Timeline: 60 days")

    with col2:
        st.markdown("**Live Conversation**")

        # Initialize chat history
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []

        # Display chat history with improved styling
        chat_container = st.container()
        with chat_container:
            for i, msg in enumerate(st.session_state[chat_key]):
                if msg['sender'] == 'user':
                    st.markdown(f"""
                        <div style="text-align: right; margin: 0.5rem 0;">
                            <div style="background: #1E88E5; color: white; padding: 0.5rem 1rem; border-radius: 1rem 1rem 0.2rem 1rem; display: inline-block; max-width: 70%;">
                                <strong>Contact:</strong> {msg['content']}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div style="text-align: left; margin: 0.5rem 0;">
                            <div style="background: #22272E; color: white; padding: 0.5rem 1rem; border-radius: 1rem 1rem 1rem 0.2rem; display: inline-block; max-width: 70%;">
                                <strong>{bot_type.title()} Bot:</strong> {msg['content']}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

        # Input section
        if bot_type == "lead":
            placeholder = "I might be interested but need to think about it..."
        elif bot_type == "seller":
            placeholder = "I'll get back to you next week, pretty busy right now..."
        else:
            placeholder = "I'm looking for a 3BR home with a good school district..."

        user_message = st.text_input(
            "Type message:",
            placeholder=placeholder,
            key=f"{bot_type}_user_input"
        )

        col_send, col_clear = st.columns([3, 1])
        with col_send:
            send_clicked = st.button(f"Send to {bot_type.title()} Bot", use_container_width=True, key=f"{bot_type}_send")
        with col_clear:
            if st.button("Clear", use_container_width=True, key=f"{bot_type}_clear"):
                st.session_state[chat_key] = []
                st.rerun()

        if send_clicked and user_message:
            # Add user message
            st.session_state[chat_key].append({
                'sender': 'user',
                'content': user_message,
                'timestamp': datetime.now()
            })

            # Get bot response
            try:
                if bot_type == "lead":
                    response = run_async_safe(manager.lead_bot.process_lead_message("demo_lead", user_message, sequence_step))
                elif bot_type == "seller":
                    response = run_async_safe(manager.seller_bot.process_seller_message("demo_seller", "Contact", [{"role": "user", "content": user_message}]))
                else:
                    response = run_async_safe(manager.buyer_bot.process_buyer_message("demo_buyer", user_message))

                # Add bot response
                st.session_state[chat_key].append({
                    'sender': 'bot',
                    'content': response['response_content'],
                    'timestamp': datetime.now()
                })

                # Show additional info for seller bot
                if bot_type == "seller" and 'stall_detected' in response:
                    if response['stall_detected']:
                        st.warning(f"⚠️ Stall Detected: {response.get('detected_stall_type', 'Unknown')}")
                        st.info(f"🎯 Jorge Strategy: {response.get('next_action', 'Continue')}")
                    else:
                        st.success("✅ Positive engagement detected")

                st.rerun()

            except Exception as e:
                st.error(f"Error processing message: {str(e)}")

def render_analytics_charts(metrics: Dict[str, Any], bot_type: str):
    """Render analytics charts optimized for each bot type."""
    col1, col2 = st.columns(2)

    with col1:
        if bot_type == "lead":
            st.markdown("**Sequence Performance**")
            step_data = pd.DataFrame({
                "Step": ["Day 3", "Day 7", "Day 14", "Day 30"],
                "Response Rate": [45.2, 62.8, 38.5, 23.4],
                "Conversion Rate": [12.5, 28.7, 15.2, 8.1]
            })
            fig = px.bar(step_data, x="Step", y=["Response Rate", "Conversion Rate"],
                        title="Lead Sequence Performance", barmode="group")

        elif bot_type == "seller":
            st.markdown("**Jorge Strategy Performance**")
            strategy_data = pd.DataFrame({
                "Strategy": ["Direct", "Take-Away", "Pressure", "Reality"],
                "Success Rate": [78.5, 84.2, 67.3, 72.8],
                "Usage": [45, 32, 16, 7]
            })
            fig = px.scatter(strategy_data, x="Usage", y="Success Rate", size="Success Rate",
                           hover_name="Strategy", title="Strategy Effectiveness vs Usage")

        else:  # buyer
            st.markdown("**Conversion Funnel**")
            funnel_data = pd.DataFrame({
                "Stage": ["Inquiry", "Qualified", "Matched", "Showing", "Offer", "Closed"],
                "Count": [100, 64, 45, 23, 7, 3]
            })
            fig = px.funnel(funnel_data, x="Count", y="Stage", title="Buyer Conversion Funnel")

        fig = style_chart_professional(fig)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        if bot_type == "lead":
            st.markdown("**Engagement Trends (7 Days)**")
            dates = pd.date_range(start=datetime.now().date() - timedelta(days=6), periods=7)
            trend_data = pd.DataFrame({
                "Date": dates,
                "Engagements": [23, 31, 28, 35, 42, 38, 45],
                "Conversions": [3, 5, 4, 7, 9, 6, 8]
            })
            fig2 = px.line(trend_data, x="Date", y=["Engagements", "Conversions"], title="Weekly Trends")

        elif bot_type == "seller":
            st.markdown("**FRS Score Distribution**")
            frs_data = pd.DataFrame({
                "Score Range": ["90-100", "80-89", "70-79", "60-69"],
                "Count": [12, 23, 34, 18],
                "Conversion %": [85, 72, 54, 34]
            })
            fig2 = px.bar(frs_data, x="Score Range", y=["Count", "Conversion %"],
                         title="FRS Performance", barmode="group")

        else:  # buyer
            st.markdown("**Match Accuracy by Price Range**")
            accuracy_data = pd.DataFrame({
                "Price Range": ["$300-500K", "$500-700K", "$700-900K", "$900K+"],
                "Accuracy %": [85.2, 89.7, 92.1, 87.3]
            })
            fig2 = px.bar(accuracy_data, x="Price Range", y="Accuracy %", title="Match Accuracy")

        fig2 = style_chart_professional(fig2)
        st.plotly_chart(fig2, use_container_width=True)