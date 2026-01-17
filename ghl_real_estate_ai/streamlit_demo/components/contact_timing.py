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
    
    st.markdown("### 📞 OPTIMAL SYNC WINDOWS")
    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
    
    for t in times:
        urgency = t.get('urgency', 'medium')
        
        # Color scheme based on urgency - Obsidian Edition
        if urgency == 'high':
            bg_color = "rgba(16, 185, 129, 0.1)"
            text_color = "#10b981"
            border_color = "rgba(16, 185, 129, 0.3)"
            badge_bg = "#10b981"
            urgency_icon = "🔥"
        elif urgency == 'medium':
            bg_color = "rgba(245, 158, 11, 0.1)"
            text_color = "#f59e0b"
            border_color = "rgba(245, 158, 11, 0.3)"
            badge_bg = "#f59e0b"
            urgency_icon = "⭐"
        else:
            bg_color = "rgba(99, 102, 241, 0.1)"
            text_color = "#6366F1"
            border_color = "rgba(99, 102, 241, 0.3)"
            badge_bg = "#6366F1"
            urgency_icon = "📅"
        
        probability = t.get('probability', t.get('confidence', 'N/A'))
        # ... logic ...
        
        st.markdown(f"""
            <div style='
                display: flex; 
                justify-content: space-between; 
                align-items: center; 
                background: rgba(22, 27, 34, 0.7); 
                padding: 1.25rem 1.5rem; 
                border-radius: 12px; 
                margin-bottom: 1rem;
                border: 1px solid rgba(255,255,255,0.05);
                border-left: 4px solid {text_color};
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
                backdrop-filter: blur(12px);
            '>
                <div style='flex: 1;'>
                    <div style='
                        color: #FFFFFF; 
                        font-weight: 700; 
                        font-size: 1.1rem;
                        font-family: "Space Grotesk", sans-serif;
                        margin-bottom: 0.25rem;
                    '>
                        {urgency_icon} {t['day']} ({t['time']})
                    </div>
                    <div style='
                        font-size: 0.75rem; 
                        color: #8B949E; 
                        font-weight: 600;
                        text-transform: uppercase;
                        letter-spacing: 0.05em;
                        font-family: "Inter", sans-serif;
                    '>
                        MAXIMUM SIGNAL STRENGTH WINDOW
                    </div>
                </div>
                <div style='
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                '>
                    <div style='
                        background: rgba(255,255,255,0.03); 
                        padding: 0.6rem 1.25rem; 
                        border-radius: 8px;
                        text-align: center;
                        border: 1px solid rgba(255,255,255,0.05);
                    '>
                        <div style='
                            font-size: 0.6rem; 
                            color: #8B949E; 
                            font-weight: 700;
                            text-transform: uppercase;
                            letter-spacing: 0.1em;
                            font-family: "Space Grotesk", sans-serif;
                        '>
                            PROBABILITY
                        </div>
                        <div style='
                            font-size: 1.5rem; 
                            font-weight: 700; 
                            color: {text_color};
                            line-height: 1;
                            margin-top: 4px;
                            font-family: "Space Grotesk", sans-serif;
                        '>
                            {probability}%
                        </div>
                    </div>
                    <div style='
                        background: {badge_bg}; 
                        color: white; 
                        padding: 0.6rem 1rem; 
                        border-radius: 8px; 
                        font-size: 0.75rem; 
                        font-weight: 800;
                        text-transform: uppercase;
                        letter-spacing: 0.1em;
                        font-family: "Space Grotesk", sans-serif;
                        box-shadow: 0 0 15px {bg_color};
                    '>
                        {urgency.upper()}
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)


def render_contact_timing_simple(times: List[Dict]):
    """
    Render a simplified version for compact layouts - Obsidian Edition
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
                color = "#6366F1"
                icon = "📅"
        else:
            color = "#6366F1"
            icon = t.get('icon', "📞")
        
        st.markdown(f"""
        <div style='
            background: rgba(22, 27, 34, 0.7); 
            padding: 1rem; 
            border-radius: 10px; 
            border-left: 4px solid {color}; 
            margin-bottom: 0.75rem;
            border: 1px solid rgba(255,255,255,0.05);
            border-left: 4px solid {color};
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            backdrop-filter: blur(8px);
        '>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <div style='font-weight: 700; color: #FFFFFF; font-family: "Space Grotesk", sans-serif;'>{icon} {t['day']}</div>
                    <div style='font-size: 0.85rem; color: #8B949E; font-family: "Inter", sans-serif;'>{t['time']}</div>
                </div>
                <div style='
                    background: {color}20; 
                    color: {color}; 
                    padding: 0.4rem 0.75rem; 
                    border-radius: 6px; 
                    font-size: 0.7rem; 
                    font-weight: 800;
                    text-transform: uppercase;
                    border: 1px solid {color}40;
                    font-family: "Space Grotesk", sans-serif;
                '>
                    {confidence if isinstance(confidence, str) else f"{confidence}%"}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
