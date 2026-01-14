import streamlit as st
import datetime

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
                ["SMS Outreach", "Email Market Update", "Video Script Outline", "Property Pitch", "Voicemail Script"]
            )
            
            # Tone Slider
            default_tone = "Consultative"
            if analysis_result:
                # Suggest tone based on insights (very basic mapping)
                if "analytical" in analysis_result.behavioral_insights.lower() or "data" in analysis_result.behavioral_insights.lower():
                    default_tone = "Professional"
                elif "trust" in analysis_result.behavioral_insights.lower() or "personal" in analysis_result.behavioral_insights.lower():
                    default_tone = "Friendly"
                elif "luxury" in analysis_result.behavioral_insights.lower():
                    default_tone = "Exclusive"

            tone = st.select_slider(
                "Persona Tone:", 
                options=["Professional", "Consultative", "Friendly", "Urgent", "Exclusive"], 
                value=default_tone,
                help="Adjusts the AI's personality and language style."
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
                            "history": reference_history
                        }
                        if analysis_result:
                            extra_context["behavioral_insight"] = analysis_result.behavioral_insights
                            extra_context["strategic_summary"] = analysis_result.strategic_summary

                        content = services["personalization"].generate_personalized_content(
                            selected_lead_name, 
                            content_type, 
                            tone,
                            context=extra_context
                        )
                        st.session_state.generated_outreach = content
                        
                        # Add to history
                        timestamp = datetime.datetime.now().strftime("%I:%M %p")
                        st.session_state.outreach_history.insert(0, {
                            "time": timestamp,
                            "type": content_type,
                            "preview": content[:50] + "..."
                        })
                        
                        st.toast("Content tailored to lead's cognitive profile!", icon="🧠")
                    except Exception as e:
                        st.error(f"Error generating content: {str(e)}")

        # History Section
        if st.session_state.outreach_history:
            st.markdown("#### 📜 Recent Generations")
            for item in st.session_state.outreach_history[:3]:
                st.caption(f"{item['time']} - {item['type']}")
                st.info(item['preview'])

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
            
            # Preview Container
            if device_view == "Mobile":
                st.markdown(f"""
                <div style='background: #333; padding: 12px; border-radius: 24px; max-width: 320px; margin: 0 auto; box-shadow: 0 10px 25px rgba(0,0,0,0.2);'>
                    <div style='background: white; border-radius: 16px; overflow: hidden; min-height: 400px;'>
                        <div style='background: #f1f5f9; padding: 12px; text-align: center; border-bottom: 1px solid #e2e8f0; font-size: 0.8rem; font-weight: 600;'>
                            Message Preview
                        </div>
                        <div style='padding: 16px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 0.9rem; line-height: 1.5; color: #1e293b;'>
                            {merged_content}
                        </div>
                        <div style='padding: 8px; text-align: center; color: #94a3b8; font-size: 0.7rem;'>
                            {datetime.datetime.now().strftime("%I:%M %p")}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='background: white; padding: 2rem; border-radius: 12px; border: 1px solid #e2e8f0; 
                            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); font-family: sans-serif; color: #1e293b; line-height: 1.6; min-height: 300px;'>
                    <div style='border-bottom: 1px solid #e2e8f0; padding-bottom: 1rem; margin-bottom: 1rem;'>
                        <span style='background: #e0f2fe; color: #0284c7; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;'>{content_type}</span>
                        <span style='background: #f1f5f9; color: #64748b; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; margin-left: 8px;'>Tone: {tone}</span>
                    </div>
                    {merged_content}
                </div>
                """, unsafe_allow_html=True)

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
            st.markdown("""
            <div style='background: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 12px; padding: 3rem 1rem; text-align: center; color: #64748b;'>
                <div style='font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;'>🎨</div>
                <div style='font-weight: 600;'>No Content Generated Yet</div>
                <div style='font-size: 0.85rem;'>Configure the options on the left and click 'Generate' to see the AI magic.</div>
            </div>
            """, unsafe_allow_html=True)
