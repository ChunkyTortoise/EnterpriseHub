"""
Global Header Component - Multi-Tenant Branding Orchestrator
Centralized header rendering with tenant-specific branding
"""
import streamlit as st
from typing import Literal


def render_global_header(tenant_name: Literal["GHL", "ARETE", "SALES"] = "GHL"):
    """
    Render the global header with tenant-specific branding.
    
    Args:
        tenant_name: Either "GHL", "ARETE", or "SALES" to determine branding style
    """
    
    # Tenant-specific configuration - OBSIDIAN COMMAND EDITION
    if tenant_name == "ARETE":
        logo = "🦅"
        title = "ARETE Performance"
        subtitle = "Strategic Ops & Optimization"
        gradient = "linear-gradient(135deg, #05070A 0%, #1E1B4B 100%)"
        glow = "0 20px 50px rgba(0, 0, 0, 0.8)"
    elif tenant_name == "SALES":
        logo = "💰"
        title = "Lyrio AI"
        subtitle = "Sales Copilot Active"
        gradient = "linear-gradient(135deg, #05070A 0%, #064E3B 100%)"
        glow = "0 20px 50px rgba(0, 0, 0, 0.8)"
    else:
        # DEFAULT: Obsidian Command (Deep Obsidian to Cyber Indigo)
        logo = "🕶️"
        title = "Lyrio AI"
        subtitle = "Enterprise Intelligence Cockpit"
        gradient = "linear-gradient(135deg, #05070A 0%, #1E1B4B 100%)"
        glow = "0 25px 60px rgba(0, 0, 0, 0.9)"
    
    st.markdown(f"""
        <div style='background: {gradient}; 
                    padding: 4rem 3.5rem; 
                    border-radius: 20px; 
                    margin-bottom: 3.5rem; 
                    color: #E6EDF3;
                    box-shadow: {glow};
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    border-top: 1px solid rgba(255, 255, 255, 0.1);
                    position: relative;
                    overflow: hidden;'>
            <div style='position: absolute; top: 0; left: 0; right: 0; bottom: 0; 
                        background-image: 
                            radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.08) 0%, transparent 40%),
                            radial-gradient(circle at 90% 80%, rgba(99, 102, 241, 0.05) 0%, transparent 40%);
                        opacity: 1;'></div>
            <div style='position: relative; z-index: 1;'>
                <div style='display: flex; align-items: center; gap: 2.5rem; margin-bottom: 2rem;'>
                    <div style='font-size: 5.5rem; line-height: 1; filter: drop-shadow(0 0 25px rgba(99, 102, 241, 0.3));'>{logo}</div>
                    <div>
                        <h1 style='margin: 0; font-size: 4rem; font-weight: 700; color: #FFFFFF !important; 
                                   text-shadow: 0 4px 20px rgba(0,0,0,0.5); font-family: "Space Grotesk", sans-serif; letter-spacing: -0.04em;'>
                            {title}
                        </h1>
                        <p style='margin: 0.25rem 0 0 0; font-size: 1.5rem; opacity: 0.8; font-weight: 500; color: #6366F1 !important; letter-spacing: 0.05em; font-family: "Space Grotesk", sans-serif; text-transform: uppercase;'>
                            {subtitle}
                        </p>
                    </div>
                </div>
                <p style='margin: 1.5rem 0; font-size: 1.15rem; opacity: 0.7; max-width: 850px; color: #E6EDF3 !important; line-height: 1.7; font-family: "Inter", sans-serif;'>
                    Proprietary high-stakes AI lead intelligence and autonomous workflow environment. 
                    <span style="background: rgba(99, 102, 241, 0.15); color: #6366F1; padding: 4px 10px; border-radius: 6px; font-weight: 700; border: 1px solid rgba(99, 102, 241, 0.3); font-size: 0.8rem; text-transform: uppercase; margin-left: 8px;">Obsidian Command Active</span>
                </p>
                <div style='margin-top: 2.5rem; display: flex; flex-wrap: wrap; gap: 1.5rem; font-size: 0.95rem;'>
                    <div style='background: rgba(22, 27, 34, 0.6); 
                                padding: 0.85rem 1.75rem; 
                                border-radius: 12px;
                                backdrop-filter: blur(20px);
                                border: 1px solid rgba(255,255,255,0.08);
                                display: flex;
                                align-items: center;
                                gap: 0.85rem;
                                box-shadow: 0 10px 40px rgba(0,0,0,0.4);
                                color: #FFFFFF !important;'>
                        <span class="status-pulse"></span>
                        <span style='font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif; font-size: 0.8rem;'>Neural Swarm: Online</span>
                    </div>
                    <div style='background: rgba(22, 27, 34, 0.6); 
                                padding: 0.85rem 1.75rem; 
                                border-radius: 12px;
                                backdrop-filter: blur(20px);
                                border: 1px solid rgba(255,255,255,0.08);
                                display: flex;
                                align-items: center;
                                gap: 0.85rem;
                                box-shadow: 0 10px 40px rgba(0,0,0,0.4);
                                color: #FFFFFF !important;'>
                        <span style='font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif; font-size: 0.8rem;'>Protocol: Secure</span>
                    </div>
                    <div style='background: rgba(99, 102, 241, 0.1); 
                                padding: 0.85rem 1.75rem; 
                                border-radius: 12px;
                                backdrop-filter: blur(20px);
                                border: 1px solid rgba(99, 102, 241, 0.2);
                                display: flex;
                                align-items: center;
                                gap: 0.85rem;
                                box-shadow: 0 10px 40px rgba(0,0,0,0.4);
                                color: #6366F1 !important;'>
                        <span style='font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif; font-size: 0.8rem;'>Sync: 100%</span>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_page_header(title: str, subtitle: str = "", icon: str = ""):
    """
    Render a standardized page header for internal pages.
    
    Args:
        title: Page title
        subtitle: Optional subtitle
        icon: Optional icon or text for the page
    """
    
    subtitle_html = f"<p style='margin: 0.5rem 0 0 0; color: #8B949E; font-size: 1.1rem; font-weight: 500; font-family: \"Inter\", sans-serif;'>{subtitle}</p>" if subtitle else ""
    icon_html = f"<div style='font-size: 3rem; background: rgba(99, 102, 241, 0.1); padding: 1.25rem; border-radius: 12px; border: 1px solid rgba(99, 102, 241, 0.2); box-shadow: 0 0 20px rgba(99, 102, 241, 0.1);'>{icon}</div>" if icon else ""
    
    st.markdown(f"""
        <div style='
            padding: 2.5rem;
            background: rgba(22, 27, 34, 0.5);
            backdrop-filter: blur(12px);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 12px 48px rgba(0,0,0,0.5);
            margin-bottom: 3rem;
        '>
            <div style='display: flex; align-items: center; gap: 2rem;'>
                {icon_html}
                <div>
                    <h2 style='margin: 0; font-size: 2.25rem; font-weight: 700; color: #FFFFFF !important; font-family: "Space Grotesk", sans-serif; letter-spacing: -0.02em;'>{title}</h2>
                    {subtitle_html}
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
