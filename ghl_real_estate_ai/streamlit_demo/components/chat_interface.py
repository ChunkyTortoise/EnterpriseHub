
import streamlit as st
import time

def render_chat_interface():
    """
    Ultra-Premium Chat Interface
    Supports multi-agent identities, thought processes, and elite styling.
    """
    st.markdown("### 💬 AI Agent Communication")
    
    # Custom CSS for chat (inherits from styles.css but adds specific bubble styles)
    st.markdown("""
    <style>
        .chat-container {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
            padding: 1rem;
            max-height: 600px;
            overflow-y: auto;
            background: rgba(248, 250, 252, 0.5);
            border-radius: 16px;
            border: 1px solid #e2e8f0;
        }
        
        .chat-bubble {
            max-width: 80%;
            padding: 1rem 1.25rem;
            border-radius: 16px;
            font-size: 0.95rem;
            line-height: 1.5;
            position: relative;
            animation: slideUp 0.3s ease-out;
        }
        
        .bubble-user {
            align-self: flex-end;
            background: var(--primary-gradient);
            color: white;
            border-bottom-right-radius: 4px;
            box-shadow: 0 4px 12px rgba(0, 106, 255, 0.2);
        }
        
        .bubble-ai {
            align-self: flex-start;
            background: white;
            color: #1e293b;
            border-bottom-left-radius: 4px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }
        
        .agent-info {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 6px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .agent-name-ai { color: #8B5CF6; }
        .agent-name-user { color: #64748B; text-align: right; justify-content: flex-end; width: 100%; }
        
        .thought-process {
            background: #f1f5f9;
            border-radius: 8px;
            padding: 0.75rem;
            margin-top: 0.75rem;
            font-size: 0.8rem;
            color: #475569;
            border-left: 3px solid #cbd5e1;
            font-style: italic;
        }
        
        .status-pill {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 9999px;
            font-size: 0.7rem;
            background: #dcfce7;
            color: #166534;
            margin-left: 8px;
        }
    </style>
    """, unsafe_allow_html=True)

    # Mock conversation if none exists
    if 'messages' not in st.session_state or not st.session_state.messages:
        st.session_state.messages = [
            {"role": "ai", "agent": "Closer", "content": "Hi Sarah! I saw you were looking at homes in Downtown Austin. Are you looking for a primary residence or an investment property?", "thought": "Analyzing lead interest in luxury condos. Engagement score: 85%"},
            {"role": "user", "content": "Mostly looking for myself, but want something that will appreciate well."},
            {"role": "ai", "agent": "Analyst", "content": "Smart move. Downtown appreciation has averaged 8.4% annually. Based on that, I've identified 3 units that match your 'live-in investment' criteria. Would you like to see the ROI projections?", "thought": "Retrieving appreciation data for Zilker and Downtown clusters. Triggering investment-persona response."}
        ]

    # Render Chat
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    for i, msg in enumerate(st.session_state.messages):
        is_ai = msg['role'] == 'ai'
        bubble_class = "bubble-ai" if is_ai else "bubble-user"
        agent_name = msg.get('agent', 'AI Agent') if is_ai else 'Sarah Martinez'
        
        st.markdown(f"""
        <div style="display: flex; flex-direction: column; width: 100%;">
            <div class="agent-info {'agent-name-ai' if is_ai else 'agent-name-user'}">
                {f'🤖 {agent_name}' if is_ai else f'{agent_name} 👤'}
                {f'<span class="status-pill">Thinking...</span>' if is_ai and i == len(st.session_state.messages)-1 else ''}
            </div>
            <div class="chat-bubble {bubble_class}">
                {msg['content']}
                {f'<div class="thought-process">🧠 <b>Thought:</b> {msg["thought"]}</div>' if is_ai and 'thought' in msg else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Input Area
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container():
        col1, col2 = st.columns([5, 1])
        with col1:
            st.text_input("Type your message...", placeholder="Send a message to the lead or the agent swarm...", key="chat_input", label_visibility="collapsed")
        with col2:
            if st.button("🚀 Send", use_container_width=True):
                st.toast("Message sent to swarm!")

def simulate_typing():
    """Simulates a typing effect for better demo experience"""
    with st.empty():
        for i in range(3):
            st.markdown(f"AI is thinking{'.' * (i+1)}")
            time.sleep(0.5)
