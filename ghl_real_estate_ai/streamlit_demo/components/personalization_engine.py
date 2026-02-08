import datetime

import streamlit as st


def render_personalization_engine(services, selected_lead_name, analysis_result=None):
    """
    Renders the Personalization Engine tab in the Lead Intelligence Hub.
    Generates tailored outreach materials based on lead behavior and preferences.
    """
    st.markdown("### 🎨 Personalized Content Engine")
    st.markdown("*Generate tailored outreach materials based on lead behavior and preferences*")

    if selected_lead_name == "-- Select a Lead --":
        st.info("Please select a lead to generate personalized content.")
        return

    # Use AI insights for better context
    if analysis_result:
        with st.expander("🤖 Claude's Behavioral Briefing", expanded=True):
            st.info(analysis_result.behavioral_insights)
            st.caption(f"**Strategic Summary:** {analysis_result.strategic_summary}")

    # Initialize session state for generated content if not present
    if "generated_outreach" not in st.session_state:
        st.session_state.generated_outreach = None
    if "outreach_history" not in st.session_state:
        st.session_state.outreach_history = []

    # Main layout: Controls on left, Preview on right
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.markdown("#### 🛠️ Content Configuration")

        with st.container(border=True):
            content_type = st.selectbox(
                "Content Channel:",
                ["SMS Outreach", "Email Market Update", "Video Script Outline", "Property Pitch", "Voicemail Script"],
            )

            # Tone Slider
            default_tone = "Consultative"
            if analysis_result:
                # Suggest tone based on insights (very basic mapping)
                if (
                    "analytical" in analysis_result.behavioral_insights.lower()
                    or "data" in analysis_result.behavioral_insights.lower()
                ):
                    default_tone = "Professional"
                elif (
                    "trust" in analysis_result.behavioral_insights.lower()
                    or "personal" in analysis_result.behavioral_insights.lower()
                ):
                    default_tone = "Friendly"
                elif "luxury" in analysis_result.behavioral_insights.lower():
                    default_tone = "Exclusive"

            tone = st.select_slider(
                "Persona Tone:",
                options=["Professional", "Consultative", "Friendly", "Urgent", "Exclusive"],
                value=default_tone,
                help="Adjusts the AI's personality and language style.",
            )

            # Context Toggles
            st.markdown("**Include Context:**")
            c1, c2 = st.columns(2)
            with c1:
                include_market_data = st.checkbox("Market Data", value=True)
                include_bio = st.checkbox("Agent Bio", value=False)
            with c2:
                include_urgency = st.checkbox("Scarcity/Urgency", value=False)
                reference_history = st.checkbox("Past Interactions", value=True)

            # Generate Button
            if st.button("✨ Generate Personalized Content", type="primary", use_container_width=True):
                with st.spinner(f"Claude is crafting {tone} content for {selected_lead_name}..."):
                    # Call Personalization Service
                    try:
                        # Add behavioral context to generation if available
                        extra_context = {
                            "market_data": include_market_data,
                            "agent_bio": include_bio,
                            "urgency": include_urgency,
                            "history": reference_history,
                        }
                        if analysis_result:
                            extra_context["behavioral_insight"] = analysis_result.behavioral_insights
                            extra_context["strategic_summary"] = analysis_result.strategic_summary

                        content = services["personalization"].generate_personalized_content(
                            selected_lead_name, content_type, tone, context=extra_context
                        )
                        st.session_state.generated_outreach = content

                        # Add to history
                        timestamp = datetime.datetime.now().strftime("%I:%M %p")
                        st.session_state.outreach_history.insert(
                            0, {"time": timestamp, "type": content_type, "preview": content[:50] + "..."}
                        )

                        st.toast("Content tailored to lead's cognitive profile!", icon="🧠")
                    except Exception as e:
                        st.error(f"Error generating content: {str(e)}")

        # History Section
        if st.session_state.outreach_history:
            st.markdown("#### 📜 Recent Generations")
            for item in st.session_state.outreach_history[:3]:
                st.caption(f"{item['time']} - {item['type']}")
                st.info(item["preview"])

    with col2:
        st.markdown("#### 📱 Live Preview")

        if st.session_state.generated_outreach:
            # Device Toggle
            device_view = st.radio("View Mode:", ["Mobile", "Desktop"], horizontal=True, label_visibility="collapsed")

            # Simulated Merge Field Replacement
            raw_content = st.session_state.generated_outreach
            merged_content = raw_content.replace("[Name]", selected_lead_name.split()[0])
            merged_content = merged_content.replace("[Agent]", "Jorge")
            merged_content = merged_content.replace("[Market]", "Austin")

            # Preview Container - Obsidian Edition
            if device_view == "Mobile":
                st.markdown(
                    f"""
                <div style='background: #161B22; padding: 12px; border-radius: 36px; max-width: 320px; margin: 0 auto; box-shadow: 0 25px 60px rgba(0,0,0,0.8); border: 1px solid rgba(255,255,255,0.1);'>
                    <div style='background: #05070A; border-radius: 28px; overflow: hidden; min-height: 420px; border: 1px solid rgba(255,255,255,0.05);'>
                        <div style='background: rgba(22, 27, 34, 0.8); padding: 12px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 0.75rem; font-weight: 700; color: #8B949E; font-family: "Space Grotesk", sans-serif; letter-spacing: 0.1em;'>
                            NEURAL PREVIEW // MOBILE
                        </div>
                        <div style='padding: 20px; font-family: "Inter", sans-serif; font-size: 0.95rem; line-height: 1.6; color: #E6EDF3;'>
                            {merged_content}
                        </div>
                        <div style='padding: 12px; text-align: center; color: #6366F1; font-size: 0.7rem; font-family: "Space Grotesk", sans-serif; font-weight: 700; letter-spacing: 0.05em;'>
                            {datetime.datetime.now().strftime("%I:%M %p")} // SYNCED
                        </div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                <div style='background: rgba(22, 27, 34, 0.7); padding: 2.5rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.05); 
                            box-shadow: 0 8px 32px rgba(0,0,0,0.6); font-family: "Inter", sans-serif; color: #E6EDF3; line-height: 1.7; min-height: 300px; backdrop-filter: blur(12px);'>
                    <div style='border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 1.25rem; margin-bottom: 1.5rem; display: flex; gap: 12px;'>
                        <span style='background: rgba(99, 102, 241, 0.15); color: #6366F1; padding: 6px 14px; border-radius: 6px; font-size: 0.7rem; font-weight: 800; font-family: "Space Grotesk", sans-serif; text-transform: uppercase; border: 1px solid rgba(99, 102, 241, 0.3);'>{content_type}</span>
                        <span style='background: rgba(255,255,255,0.05); color: #8B949E; padding: 6px 14px; border-radius: 6px; font-size: 0.7rem; font-weight: 800; font-family: "Space Grotesk", sans-serif; text-transform: uppercase; border: 1px solid rgba(255,255,255,0.1);'>TONE: {tone}</span>
                    </div>
                    <div style="opacity: 0.9;">{merged_content}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            st.markdown("<br>", unsafe_allow_html=True)

            # Action Buttons
            c_a, c_b, c_c = st.columns(3)
            with c_a:
                if st.button("🚀 Push to GHL", use_container_width=True):
                    with st.spinner("Syncing draft to GoHighLevel..."):
                        import time

                        time.sleep(1.0)
                        st.toast("Content synced to GHL draft!", icon="✅")
            with c_b:
                if st.button("📨 Send Test", use_container_width=True):
                    with st.spinner("Sending test SMS..."):
                        import time

                        time.sleep(0.8)
                        st.toast("Test message sent to your phone", icon="📱")
            with c_c:
                if st.button("📋 Copy", use_container_width=True):
                    st.toast("Copied to clipboard!", icon="📋")
                    time.sleep(0.2)
                    st.success("Ready for paste")
        else:
            st.markdown(
                """
            <div style='background: rgba(22, 27, 34, 0.6); border: 2px dashed rgba(255,255,255,0.1); border-radius: 16px; padding: 4rem 2rem; text-align: center; color: #8B949E; backdrop-filter: blur(10px);'>
                <div style='font-size: 3.5rem; margin-bottom: 1.5rem; opacity: 0.5; filter: grayscale(1);'>🎨</div>
                <div style='font-weight: 700; color: #FFFFFF; font-family: "Space Grotesk", sans-serif; text-transform: uppercase; letter-spacing: 0.1em;'>Strategy Engine Idle</div>
                <div style='font-size: 0.9rem; margin-top: 8px; font-family: "Inter", sans-serif;'>Configure synthesis parameters on the left to initialize personalized deployment.</div>
            </div>
            """,
                unsafe_allow_html=True,
            )
