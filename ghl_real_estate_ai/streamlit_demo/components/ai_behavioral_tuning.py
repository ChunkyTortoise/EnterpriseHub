"""
AI Behavioral Tuning Component - Granular control over AI agent behavior
"""
import streamlit as st
from typing import Dict, Any

def render_behavioral_tuning_panel(phase_name: str, phase_config: Dict[str, Any]):
    """
    Render behavioral tuning controls for a specific AI phase
    Enhanced with Elite Control Deck styling.
    """
    with st.expander(f'🎛️ {phase_name} AI Control Deck', expanded=False):
        st.markdown(f'\n        <div style="background: var(--primary-gradient); padding: 10px 15px; border-radius: 8px; color: white; margin-bottom: 20px;">\n            <div style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase;">Engine Status</div>\n            <div style="font-size: 1.1rem; font-weight: 600;">Calibrating {phase_name} Swarm</div>\n        </div>\n        ', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('### 🎯 Engagement Strategy')
            followup_count = st.slider('Persistence Level', min_value=1, max_value=10, value=phase_config.get('followup_count', 5), help='Higher values increase follow-up frequency.', key=f'{phase_name}_followup')
            response_delay = st.select_slider('Agent Response Latency', options=['Instant', '1-5 min', '15-30 min', '1-2 hours', 'Next Day'], value=phase_config.get('response_delay', '1-5 min'), key=f'{phase_name}_speed')
            mention_agent = st.toggle('Personal Branding (Mention Jorge)', value=phase_config.get('mention_agent', True), key=f'{phase_name}_mention')
        with col2:
            st.markdown('### 🎭 Cognitive Parameters')
            tone = st.select_slider('Communication Archetype', options=['Formal', 'Professional', 'Friendly', 'Casual', 'Direct'], value=phase_config.get('tone', 'Professional'), key=f'{phase_name}_tone')
            creativity = st.slider('Linguistic Variance (Creativity)', min_value=0.0, max_value=1.0, value=phase_config.get('creativity', 0.5), step=0.1, key=f'{phase_name}_creativity')
            question_style = st.segmented_control('Inquiry Depth', ['Subtle', 'Balanced', 'Direct'], default='Balanced', key=f'{phase_name}_qual_style')
        st.markdown('---')
        st.markdown('### 👁️ Response Simulation')
        preview_text = generate_behavior_preview(tone, creativity, question_style, followup_count, mention_agent)
        st.markdown(f'''\n        <div class="glass-card" style="padding: 1.5rem; border-radius: 12px; border-left: 5px solid #8B5CF6;">\n            <div style="font-size: 0.75rem; color: #8B5CF6; font-weight: 700; margin-bottom: 0.5rem; letter-spacing: 0.1em;">SIMULATED OUTPUT</div>\n            <div style="color: #1e293b; font-size: 1rem; line-height: 1.6; font-family: 'Inter', sans-serif;">\n                "{preview_text}"\n            </div>\n        </div>\n        ''', unsafe_allow_html=True)
        st.markdown('<br>', unsafe_allow_html=True)
        col_save, col_reset = st.columns([1, 1])
        with col_save:
            if st.button('🚀 Commit Behavior Changes', use_container_width=True, type='primary', key=f'{phase_name}_save'):
                save_behavior_config(phase_name, {'followup_count': followup_count, 'response_delay': response_delay, 'mention_agent': mention_agent, 'tone': tone, 'creativity': creativity, 'question_style': question_style})
                st.toast(f'✅ Swarm calibrated for {phase_name}', icon='🚀')
        with col_reset:
            if st.button('🔄 Factory Reset', use_container_width=True, key=f'{phase_name}_reset'):
                st.toast('Resetting to baseline protocols...', icon='🔄')
                st.rerun()

@st.cache_data(ttl=300)
def generate_behavior_preview(tone: str, creativity: float, style: str, followups: int, mention_agent: bool) -> str:
    """Generate a preview message based on behavior settings"""
    if mention_agent:
        greeting = "Hi! This is Jorge Sales's AI assistant"
    else:
        greeting = 'Hi! Thanks for reaching out'
    if tone == 'Formal':
        body = 'I would be delighted to assist you with your real estate inquiry. May I ask what type of property you are seeking?'
    elif tone == 'Professional':
        body = "I'm here to help you find the perfect property. What are you looking for in terms of bedrooms and location?"
    elif tone == 'Friendly':
        body = "I'd love to help you find your dream home! What's your ideal property like?"
    elif tone == 'Casual':
        body = "Let's find you a great place! What are you looking for?"
    else:
        body = "What's your budget and ideal location? I'll pull up matches right away."
    if style == 'Direct':
        qualifier = " Quick question: what's your max budget?"
    elif style == 'Balanced':
        qualifier = ' To better assist you, what budget range are you considering?'
    else:
        qualifier = " I'm curious what type of investment you're considering."
    if creativity > 0.7:
        creativity_element = ' 🏡 (I also noticed the market in your area just heated up!)'
    else:
        creativity_element = ''
    return f'{greeting}. {body}{qualifier}{creativity_element}'

def save_behavior_config(phase_name: str, config: Dict[str, Any]):
    """Save behavior configuration to session state"""
    if 'behavior_configs' not in st.session_state:
        st.session_state.behavior_configs = {}
    st.session_state.behavior_configs[phase_name] = config

@st.cache_data(ttl=300)
def get_behavior_config(phase_name: str) -> Dict[str, Any]:
    """Get behavior configuration for a phase"""
    if 'behavior_configs' not in st.session_state:
        st.session_state.behavior_configs = {}
    defaults = {'followup_count': 5, 'response_delay': '1-5 min', 'mention_agent': True, 'tone': 'Professional', 'creativity': 0.5, 'question_style': 'Balanced'}
    return st.session_state.behavior_configs.get(phase_name, defaults)