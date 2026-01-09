"""
Contact Timing Component - Urgency Badges with Success Rates
Enhanced visualization for optimal contact times
"""
import streamlit as st
from typing import List, Dict, Literal


def render_contact_timing_badges(times: List[Dict]):
    """
    Render contact timing with urgency badges and success rate indicators.
    
    Args:
        times: List of dictionaries containing:
            - day: str (e.g., "Tomorrow", "Friday")
            - time: str (e.g., "2:00 PM - 4:00 PM")
            - urgency: Literal["high", "medium", "low"]
            - probability: int (success rate percentage)
    """
    
    st.markdown("### 📞 Best Time to Contact")
    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
    
    for t in times:
        urgency = t.get('urgency', 'medium')
        
        # Color scheme based on urgency
        if urgency == 'high':
            bg_color = "#dcfce7"
            text_color = "#166534"
            border_color = "#22c55e"
            badge_bg = "#22c55e"
            urgency_icon = "🔥"
        elif urgency == 'medium':
            bg_color = "#fef9c3"
            text_color = "#854d0e"
            border_color = "#eab308"
            badge_bg = "#eab308"
            urgency_icon = "⭐"
        else:
            bg_color = "#f1f5f9"
            text_color = "#475569"
            border_color = "#94a3b8"
            badge_bg = "#94a3b8"
            urgency_icon = "📅"
        
        probability = t.get('probability', t.get('confidence', 'N/A'))
        
        # Convert confidence text to probability if needed
        if isinstance(probability, str):
            if probability.lower() == 'high':
                probability = 85
            elif probability.lower() == 'medium':
                probability = 65
            else:
                probability = 45
        
        st.markdown(f"""
            <div style='
                display: flex; 
                justify-content: space-between; 
                align-items: center; 
                background: {bg_color}; 
                padding: 1rem 1.25rem; 
                border-radius: 12px; 
                margin-bottom: 0.75rem;
                border: 2px solid {border_color};
                box-shadow: 0 1px 3px rgba(0,0,0,0.08);
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            '>
                <div style='flex: 1;'>
                    <div style='
                        color: {text_color}; 
                        font-weight: 700; 
                        font-size: 1rem;
                        margin-bottom: 0.25rem;
                    '>
                        {urgency_icon} {t['day']} ({t['time']})
                    </div>
                    <div style='
                        font-size: 0.75rem; 
                        color: {text_color}; 
                        opacity: 0.8;
                    '>
                        Optimal window for engagement
                    </div>
                </div>
                <div style='
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                '>
                    <div style='
                        background: white; 
                        padding: 0.5rem 1rem; 
                        border-radius: 8px;
                        text-align: center;
                        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                    '>
                        <div style='
                            font-size: 0.65rem; 
                            color: #64748b; 
                            font-weight: 600;
                            text-transform: uppercase;
                            letter-spacing: 0.05em;
                        '>
                            Success Rate
                        </div>
                        <div style='
                            font-size: 1.25rem; 
                            font-weight: 800; 
                            color: {border_color};
                            line-height: 1;
                            margin-top: 0.25rem;
                        '>
                            {probability}%
                        </div>
                    </div>
                    <div style='
                        background: {badge_bg}; 
                        color: white; 
                        padding: 0.5rem 0.75rem; 
                        border-radius: 8px; 
                        font-size: 0.75rem; 
                        font-weight: 700;
                        text-transform: uppercase;
                        letter-spacing: 0.05em;
                    '>
                        {urgency.upper()}
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)


def render_contact_timing_simple(times: List[Dict]):
    """
    Render a simplified version for compact layouts.
    
    Args:
        times: List of dictionaries with day, time, confidence/urgency
    """
    
    for t in times:
        confidence = t.get('confidence', t.get('urgency', 'medium'))
        
        if isinstance(confidence, str):
            if confidence.lower() == 'high':
                color = "#10b981"
                icon = "🔥"
            elif confidence.lower() == 'medium':
                color = "#f59e0b"
                icon = "⭐"
            else:
                color = "#94a3b8"
                icon = "📅"
        else:
            color = "#3b82f6"
            icon = t.get('icon', "📞")
        
        st.markdown(f"""
        <div style='
            background: white; 
            padding: 0.75rem; 
            border-radius: 8px; 
            border-left: 4px solid {color}; 
            margin-bottom: 0.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        '>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <div style='font-weight: 600; color: #1e293b;'>{icon} {t['day']}</div>
                    <div style='font-size: 0.875rem; color: #64748b;'>{t['time']}</div>
                </div>
                <div style='
                    background: {color}; 
                    color: white; 
                    padding: 0.25rem 0.5rem; 
                    border-radius: 4px; 
                    font-size: 0.75rem; 
                    font-weight: 600;
                '>
                    {confidence if isinstance(confidence, str) else f"{confidence}%"}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
