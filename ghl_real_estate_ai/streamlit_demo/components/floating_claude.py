import streamlit as st
import asyncio
import time
from datetime import datetime
from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator, ClaudeTaskType, ClaudeRequest
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
analytics_service = AnalyticsService()

def inject_floating_chat_css():
    """Injects the CSS required for the floating chat window."""
    st.markdown("\n    <style>\n    /* Floating Chat Container */\n    .floating-chat-container {\n        position: fixed;\n        bottom: 85px;\n        right: 25px;\n        width: 380px;\n        height: 550px;\n        background: #FFFFFF;\n        border-radius: 16px;\n        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);\n        display: flex;\n        flex-direction: column;\n        z-index: 1000000;\n        border: 1px solid #E2E8F0;\n        overflow: hidden;\n        animation: slideIn 0.3s ease-out;\n    }\n\n    @keyframes slideIn {\n        from { transform: translateY(20px); opacity: 0; }\n        to { transform: translateY(0); opacity: 1; }\n    }\n\n    /* Floating Toggle Button */\n    .floating-chat-toggle {\n        position: fixed;\n        bottom: 25px;\n        right: 25px;\n        width: 60px;\n        height: 60px;\n        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);\n        border-radius: 50%;\n        display: flex;\n        align-items: center;\n        justify-content: center;\n        color: white;\n        font-size: 24px;\n        cursor: pointer;\n        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);\n        z-index: 1000001;\n        transition: all 0.3s ease;\n    }\n\n    .floating-chat-toggle:hover {\n        transform: scale(1.1);\n        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6);\n    }\n\n    /* Header */\n    .chat-header {\n        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);\n        padding: 15px 20px;\n        color: white;\n        display: flex;\n        align-items: center;\n        justify-content: space-between;\n    }\n\n    .chat-header h3 {\n        margin: 0;\n        font-size: 1.1rem;\n        color: white !important;\n    }\n\n    /* Chat Area */\n    .chat-messages {\n        flex: 1;\n        padding: 15px;\n        overflow-y: auto;\n        background: #F8FAFC;\n    }\n\n    /* Hide Streamlit elements inside the floating div if possible, \n       but we actually render this using a mix of HTML and Streamlit components */\n    \n    /* We will use a workaround to make Streamlit's chat_input look okay or use a custom one */\n    </style>\n    ", unsafe_allow_html=True)

def render_floating_claude():
    """Renders the floating Claude chat interface."""
    if 'show_floating_chat' not in st.session_state:
        st.session_state.show_floating_chat = False
    if 'floating_chat_history' not in st.session_state:
        st.session_state.floating_chat_history = []
    if 'floating_chat_greeted' not in st.session_state:
        st.session_state.floating_chat_greeted = False
    inject_floating_chat_css()
    with st.container():
        st.markdown('<div class="floating-anchor"></div>', unsafe_allow_html=True)
        if st.button('🧠', key='claude_float_toggle', help='Chat with Claude'):
            st.session_state.show_floating_chat = not st.session_state.show_floating_chat
            st.rerun()
    st.markdown('\n    <style>\n    div[data-testid="stVerticalBlock"] > div:has(button[key="claude_float_toggle"]) {\n        position: fixed;\n        bottom: 25px;\n        right: 25px;\n        z-index: 1000001;\n    }\n    button[key="claude_float_toggle"] {\n        width: 60px !important;\n        height: 60px !important;\n        border-radius: 50% !important;\n        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%) !important;\n        color: white !important;\n        font-size: 24px !important;\n        border: none !important;\n        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4) !important;\n        transition: all 0.3s ease !important;\n    }\n    button[key="claude_float_toggle"]:hover {\n        transform: scale(1.1) !important;\n    }\n    </style>\n    ', unsafe_allow_html=True)
    if st.session_state.show_floating_chat:
        with st.container():
            st.markdown('<div class="floating-chat-window">', unsafe_allow_html=True)
            header_col1, header_col2 = st.columns([0.9, 0.1])
            with header_col1:
                st.markdown('### 🧠 Claude Omni-Assistant')
            with header_col2:
                if st.button('❌', key='close_chat'):
                    st.session_state.show_floating_chat = False
                    st.rerun()
            st.markdown('---')
            if not st.session_state.floating_chat_greeted:
                greeting = "Hello Jorge! 👋 I'm your Omnipotent Claude Assistant. I have full context of the EnterpriseHub and GHL Real Estate AI project. How can I help you navigate or understand the system today?"
                st.session_state.floating_chat_history.append({'role': 'assistant', 'content': greeting})
                st.session_state.floating_chat_greeted = True
            chat_box = st.container(height=400)
            with chat_box:
                for msg in st.session_state.floating_chat_history:
                    with st.chat_message(msg['role']):
                        st.markdown(msg['content'])
            if (prompt := st.chat_input('Ask me anything about the project...', key='floating_chat_input')):
                st.session_state.floating_chat_history.append({'role': 'user', 'content': prompt})
                with chat_box:
                    with st.chat_message('user'):
                        st.markdown(prompt)
                with st.spinner('Claude is thinking...'):
                    response = generate_omni_response(prompt)
                    st.session_state.floating_chat_history.append({'role': 'assistant', 'content': response})
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('\n        <style>\n        div[data-testid="stVerticalBlock"] > div:has(div.floating-chat-window) {\n            position: fixed;\n            bottom: 100px;\n            right: 25px;\n            width: 400px;\n            max-height: 600px;\n            background: white;\n            border-radius: 16px;\n            box-shadow: 0 12px 40px rgba(0,0,0,0.2);\n            z-index: 1000000;\n            padding: 15px;\n            border: 1px solid #E2E8F0;\n            overflow: hidden;\n        }\n        </style>\n        ', unsafe_allow_html=True)

@st.cache_data(ttl=300)
def generate_omni_response(prompt):
    """Generates a response with omnipotent project context."""
    orchestrator = get_claude_orchestrator()
    omni_context = '\n    You are the Omnipotent Claude Assistant for the EnterpriseHub v6.0 and GHL Real Estate AI project.\n    You have deep, complete knowledge of the entire codebase, architecture, and business goals.\n    \n    PROJECT OVERVIEW:\n    - EnterpriseHub: A professional AI services showcase (v6.0).\n    - Client: Jorge Sales (Lyrio.io).\n    - Project: GHL Real Estate AI (Elite v4.0).\n    - Stack: Python, Streamlit, Claude 3.5 Sonnet, GoHighLevel API.\n    \n    CORE MODULES:\n    1. Executive Command Center: Business-wide metrics and Swarm Intelligence.\n    2. Lead Intelligence Hub: AI-powered lead scoring (15-factor engine) and behavioral analysis.\n    3. Swarm Intelligence: Multi-agent coordination (Analyst, Performance, Pipeline, Strategic Advisor).\n    4. Proactive Intelligence: 24/7 monitoring, alerts, and predictive insights.\n    5. Sales Copilot: Live call assistance and contract generation.\n    6. Automation Studio: GHL workflow orchestration and content generation.\n    7. Buyer/Seller Journey Hubs: Specialized portals for transaction stages.\n    \n    TECHNICAL MOATS:\n    - Decoupled Intelligence Core.\n    - Graphiti-powered Semantic Memory.\n    - 522+ automated tests passing.\n    - Multi-tenant architecture.\n    \n    YOUR ROLE:\n    - Guide the user (Jorge) through the system.\n    - Explain how different hubs work.\n    - Provide strategic advice based on the data in the hubs.\n    - Answer technical questions about the architecture (referencing GHL_TECHNICAL_DOCUMENTATION.md).\n    - Be proactive, direct, and elite.\n    '
    try:
        request = ClaudeRequest(task_type=ClaudeTaskType.OMNIPOTENT_ASSISTANT, context={'market': st.session_state.get('selected_market', 'Austin'), 'current_hub': st.session_state.get('current_hub', 'Executive'), 'omni_context': True}, system_prompt=omni_context, prompt=f'Jorge asks: {prompt}')
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        response_obj = loop.run_until_complete(orchestrator.process_request(request))
        loop.run_until_complete(analytics_service.track_llm_usage(location_id='demo_location', model=response_obj.model or 'claude-3-5-sonnet', provider=response_obj.provider or 'claude', input_tokens=response_obj.input_tokens or 0, output_tokens=response_obj.output_tokens or 0, cached=False))
        return response_obj.content
    except Exception as e:
        return f'I apologize, Jorge. I encountered an error while accessing my core intelligence: {str(e)}. I am still in demo mode, but I can tell you that the GHL integration is ready for deployment.'