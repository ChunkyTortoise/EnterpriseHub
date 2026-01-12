"""
AI Behavioral Tuning Component - Granular control over AI agent behavior
"""
import streamlit as st
from typing import Dict, Any


def render_behavioral_tuning_panel(phase_name: str, phase_config: Dict[str, Any]):
    """
    Render behavioral tuning controls for a specific AI phase
    
    Args:
        phase_name: Name of the phase (e.g., "Phase 1: Initial Response")
        phase_config: Current configuration for the phase
    """
    
    with st.expander(f"⚙️ {phase_name} Behavior Tuning", expanded=False):
        st.markdown("*Fine-tune how the AI behaves in this phase*")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🎯 Persistence Settings")
            
            # Follow-up frequency
            followup_count = st.slider(
                "Follow-up Attempts",
                min_value=1,
                max_value=10,
                value=phase_config.get('followup_count', 5),
                help="How many times should the AI follow up before marking as cold?",
                key=f"{phase_name}_followup"
            )
            
            # Response speed
            response_delay = st.select_slider(
                "Response Speed",
                options=["Instant", "1-5 min", "15-30 min", "1-2 hours", "Next Day"],
                value=phase_config.get('response_delay', "1-5 min"),
                help="How quickly should the AI respond?",
                key=f"{phase_name}_speed"
            )
            
            # Mention agent name
            mention_agent = st.checkbox(
                "Mention 'Jorge Sales' in intro",
                value=phase_config.get('mention_agent', True),
                help="Should the AI mention the agent's name?",
                key=f"{phase_name}_mention"
            )
        
        with col2:
            st.markdown("#### 🎨 Tone & Creativity")
            
            # Tone selector
            tone = st.select_slider(
                "Communication Tone",
                options=["Formal", "Professional", "Friendly", "Casual", "Direct"],
                value=phase_config.get('tone', "Professional"),
                help="How should the AI communicate?",
                key=f"{phase_name}_tone"
            )
            
            # Creativity level
            creativity = st.slider(
                "Response Creativity",
                min_value=0.0,
                max_value=1.0,
                value=phase_config.get('creativity', 0.5),
                step=0.1,
                format="%.1f",
                help="0.0 = Predictable, 1.0 = Unique responses",
                key=f"{phase_name}_creativity"
            )
            
            # Question aggressiveness
            question_style = st.radio(
                "Qualification Style",
                ["Subtle", "Balanced", "Direct"],
                index=1,
                help="How aggressively should the AI qualify leads?",
                key=f"{phase_name}_qual_style",
                horizontal=True
            )
        
        st.markdown("---")
        st.markdown("#### 🎭 Behavior Preview")
        
        # Generate preview based on settings
        preview_text = generate_behavior_preview(
            tone, creativity, question_style, followup_count, mention_agent
        )
        
        st.markdown(f"""
        <div style='background: #f8fafc; padding: 1rem; border-radius: 8px; border-left: 4px solid #3b82f6;'>
            <div style='font-size: 0.75rem; color: #6b7280; margin-bottom: 0.5rem;'>EXAMPLE RESPONSE</div>
            <div style='color: #374151; font-size: 0.9rem;'>{preview_text}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Save button
        col_save, col_reset = st.columns([3, 1])
        
        with col_save:
            if st.button("💾 Save Behavior Profile", use_container_width=True, key=f"{phase_name}_save"):
                save_behavior_config(phase_name, {
                    'followup_count': followup_count,
                    'response_delay': response_delay,
                    'mention_agent': mention_agent,
                    'tone': tone,
                    'creativity': creativity,
                    'question_style': question_style
                })
                st.toast(f"{phase_name} behavior saved!", icon="✅")
        
        with col_reset:
            if st.button("🔄", use_container_width=True, help="Reset to defaults", key=f"{phase_name}_reset"):
                st.toast("Reset to defaults", icon="🔄")
                st.rerun()


def generate_behavior_preview(tone: str, creativity: float, style: str, followups: int, mention_agent: bool) -> str:
    """Generate a preview message based on behavior settings"""
    
    # Base greeting
    if mention_agent:
        greeting = "Hi! This is Jorge Sales's AI assistant"
    else:
        greeting = "Hi! Thanks for reaching out"
    
    # Tone variations
    if tone == "Formal":
        body = "I would be delighted to assist you with your real estate inquiry. May I ask what type of property you are seeking?"
    elif tone == "Professional":
        body = "I'm here to help you find the perfect property. What are you looking for in terms of bedrooms and location?"
    elif tone == "Friendly":
        body = "I'd love to help you find your dream home! What's your ideal property like?"
    elif tone == "Casual":
        body = "Let's find you a great place! What are you looking for?"
    else:  # Direct
        body = "What's your budget and ideal location? I'll pull up matches right away."
    
    # Qualification style
    if style == "Direct":
        qualifier = " Quick question: what's your max budget?"
    elif style == "Balanced":
        qualifier = " To better assist you, what budget range are you considering?"
    else:  # Subtle
        qualifier = " I'm curious what type of investment you're considering."
    
    # Creativity adjustment (add unique elements at high creativity)
    if creativity > 0.7:
        creativity_element = " 🏡 (I also noticed the market in your area just heated up!)"
    else:
        creativity_element = ""
    
    return f"{greeting}. {body}{qualifier}{creativity_element}"


def save_behavior_config(phase_name: str, config: Dict[str, Any]):
    """Save behavior configuration to session state"""
    
    if 'behavior_configs' not in st.session_state:
        st.session_state.behavior_configs = {}
    
    st.session_state.behavior_configs[phase_name] = config


def get_behavior_config(phase_name: str) -> Dict[str, Any]:
    """Get behavior configuration for a phase"""
    
    if 'behavior_configs' not in st.session_state:
        st.session_state.behavior_configs = {}
    
    # Default configuration
    defaults = {
        'followup_count': 5,
        'response_delay': "1-5 min",
        'mention_agent': True,
        'tone': "Professional",
        'creativity': 0.5,
        'question_style': "Balanced"
    }
    
    return st.session_state.behavior_configs.get(phase_name, defaults)
