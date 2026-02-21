import time

import streamlit as st

from ghl_real_estate_ai.streamlit_demo.async_utils import run_async

try:
    from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator

    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False


def render_conversation_simulator(services, selected_lead_name):
    """
    Renders the AI Conversation Simulator tab.
    Allows testing how the AI assistant handles specific scenarios with simulated latency and thought visualization.
    """
    st.markdown("### 💬 AI Conversation Simulator")
    st.markdown("*Test how the AI assistant would handle specific scenarios with this lead*")

    if selected_lead_name == "-- Select a Lead --":
        st.info("Select a lead to begin simulation.")
        return

    # Initialize chat history
    if "sim_messages" not in st.session_state:
        st.session_state.sim_messages = []

    # Scenario Selector
    with st.expander("⚙️ Simulation Settings", expanded=False):
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            scenario = st.selectbox(
                "Training Scenario:",
                [
                    "General Inquiry",
                    "Objection Handling",
                    "Qualification Run",
                    "Scheduling Conflict",
                    "Aggressive Negotiation",
                ],
            )
        with col_s2:
            st.info(f"Loaded Context: **{scenario}** mode for **{selected_lead_name}**")

    # Chat Interface Container
    chat_container = st.container(height=400, border=True)

    with chat_container:
        if not st.session_state.sim_messages:
            st.caption("Simulation ready. Type a message below to start.")

        for msg in st.session_state.sim_messages:
            with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🤖"):
                st.markdown(msg["content"])
                if "sentiment" in msg:
                    st.caption(f"Sentiment: {msg['sentiment']}")

    # Input Area - Tab-safe Form Implementation
    with st.form(key="simulator_input_form", clear_on_submit=True):
        col_in, col_btn = st.columns([4, 1])
        with col_in:
            prompt = st.text_input(
                f"Message as {selected_lead_name}...",
                placeholder="Type your message here...",
                label_visibility="collapsed",
            )
        with col_btn:
            submit = st.form_submit_button("Send 🚀", use_container_width=True)

    if submit and prompt:
        # 1. Add User Message
        st.session_state.sim_messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)

        # 2. AI Processing Visualization
        with chat_container:
            with st.chat_message("assistant", avatar="🤖"):
                status_placeholder = st.empty()

                # Visual Thinking Process
                with status_placeholder.status("🧠 Claude is thinking...", expanded=True) as status:
                    st.markdown("**1. Intent Recognition**")
                    st.progress(0.2)

                    st.markdown("**2. Knowledge Retrieval & Context Synthesis**")
                    lead_options = st.session_state.get("lead_options", {})
                    lead_context = lead_options.get(selected_lead_name, {})
                    lead_id = lead_context.get("lead_id", "demo_lead")

                    st.code(f"Lead: {selected_lead_name}\nScenario: {scenario}\nMemory: Active", language="text")
                    st.progress(0.5)

                    st.markdown("**3. Behavioral Alignment**")
                    st.info(f"Applying behavioral persona for {selected_lead_name}")
                    st.progress(0.7)

                    st.markdown("**4. Response Orchestration**")

                    # 3. Generate Response using Claude
                    if CLAUDE_AVAILABLE:
                        orchestrator = get_claude_orchestrator()
                        try:
                            # Run async call in Streamlit

                            # Build context for Claude
                            chat_context = {
                                "scenario": scenario,
                                "lead_name": selected_lead_name,
                                "lead_data": lead_context,
                                "history": st.session_state.sim_messages[:-1],
                            }

                            claude_response = run_async(
                                orchestrator.chat_query(query=prompt, context=chat_context, lead_id=lead_id)
                            )
                            full_response = claude_response.content
                        except Exception as e:
                            st.error(f"Claude Error: {str(e)}")
                            full_response = (
                                f"I apologize, I'm having trouble connecting to my intelligence core. Error: {str(e)}"
                            )
                    else:
                        # Fallback
                        try:
                            full_response = services["predictive_scorer"].simulate_response(selected_lead_name, prompt)
                        except Exception as e:
                            import logging

                            logging.getLogger(__name__).debug(f"Predictive scorer fallback simulation failed: {str(e)}")
                            full_response = "I see. Could you tell me more about your timeline for moving?"

                    st.progress(1.0)
                    status.update(label="✅ Response Ready", state="complete", expanded=False)

                # Simulate streaming
                message_placeholder = st.empty()
                current_text = ""
                # Split by words but keep spaces
                words = full_response.split(" ")
                for word in words:
                    current_text += word + " "
                    message_placeholder.markdown(current_text + "▌")
                    time.sleep(0.02)

                message_placeholder.markdown(full_response)
                st.session_state.sim_messages.append({"role": "assistant", "content": full_response})

    # Reset Button
    if st.button("🔄 Reset Simulation"):
        st.session_state.sim_messages = []
        st.rerun()
