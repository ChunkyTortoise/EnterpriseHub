"""
Lead Intelligence Simulation Component
"The Dojo" - AI Conversation Simulator & Roleplay
"""

import streamlit as st
import time

def render_simulation_tab():
    """
    Renders the 'Simulation' (Dojo) tab within the Lead Intelligence Hub.
    """
    st.markdown("### 🥋 The Dojo: AI Conversation Simulator")
    st.caption("Practice your scripts against realistic AI personas before talking to real leads.")

    col_config, col_main = st.columns([1, 3])

    with col_config:
        st.markdown(f"""
        <div style='background: #f1f5f9; padding: 1.5rem; border-radius: 12px;'>
            <h4 style='margin-top:0;'>⚙️ Scenario Setup</h4>
        </div>
        """, unsafe_allow_html=True)
        
        scenario = st.selectbox(
            "Select Persona",
            [
                "🟢 First-Time Buyer (Nervous)",
                "🔴 Angry Seller (Expired Listing)",
                "🟡 Investor (Just the numbers)",
                "🔵 Window Shopper (Just looking)"
            ]
        )
        
        difficulty = st.select_slider("Difficulty", options=["Easy", "Normal", "Hard", "Nightmare"], value="Normal")
        
        st.markdown("---")
        if st.button("🔄 Start Simulation", type="primary", use_container_width=True):
            st.session_state['simulation_active'] = True
            st.session_state['sim_messages'] = [{
                "role": "assistant", 
                "content": _get_opening_line(scenario)
            }]
            st.rerun()

    with col_main:
        if st.session_state.get('simulation_active', False):
            _render_active_simulation(scenario)
        else:
            _render_empty_state()

def _get_opening_line(scenario):
    if "First-Time" in scenario:
        return "Hi... I'm looking at this house on Main St, but I've never done this before. Is it still available?"
    elif "Angry" in scenario:
        return "Look, I'm sick of agents calling me. My house didn't sell, I'm taking it off the market. What do you want?"
    elif "Investor" in scenario:
        return "I saw 123 Oak St. What's the cap rate? I don't care about the kitchen, just the numbers."
    return "Just browsing, thanks."

def _render_empty_state():
    st.info("👈 Configure a scenario on the left to start practicing.")
    st.markdown("""
    <div style='text-align: center; padding: 3rem; color: #94a3b8;'>
        <div style='font-size: 4rem;'>🥋</div>
        <h3>Ready to Train?</h3>
        <p>Select a persona like 'Angry Seller' to test your objection handling skills.</p>
    </div>
    """, unsafe_allow_html=True)

def _render_active_simulation(scenario):
    # Chat container
    chat_container = st.container(height=500)
    
    # Initialize history if needed
    if 'sim_messages' not in st.session_state:
        st.session_state['sim_messages'] = []

    # Display chat
    with chat_container:
        for msg in st.session_state['sim_messages']:
            with st.chat_message(msg['role'], avatar="🤖" if msg['role'] == "assistant" else "👤"):
                st.write(msg['content'])

    # Input area
    user_input = st.chat_input("Type your response...")
    if user_input:
        # User message
        st.session_state['sim_messages'].append({"role": "user", "content": user_input})
        
        # AI Response (Mock for UI demo)
        with chat_container:
            with st.chat_message("user", avatar="👤"):
                st.write(user_input)
            
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Thinking..."):
                    time.sleep(1) # Fake latency
                    response = "That's an interesting point. [AI Logic would reply here based on persona]"
                    st.write(response)
                    st.session_state['sim_messages'].append({"role": "assistant", "content": response})
        
        st.rerun()

    # Real-time Coach Sidebar (Right side, technically below in mobile but side-by-side in desktop if we used columns, 
    # but here let's put it in an expander or just below chat)
    
    with st.expander("👨‍🏫 Real-time Coach (Feedback)", expanded=True):
        st.markdown(f"""
        <div style='background: #fffbeb; border-left: 4px solid #f59e0b; padding: 1rem; border-radius: 4px;'>
            <strong>Feedback:</strong> precise and helpful. You handled the objection well, but try to ask an open-ended question next time.
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    render_simulation_tab()
