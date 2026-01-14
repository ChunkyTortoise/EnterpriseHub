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
    
    # Tenant-specific configuration
    if tenant_name == "ARETE":
        logo = "🦅"
        title = "ARETE Performance"
        subtitle = "Ops & Optimization Hub"
        gradient = "linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%)"
        glow = "0 20px 40px rgba(124, 58, 237, 0.3)"
    elif tenant_name == "SALES":
        logo = "💰"
        title = "Lyrio.io AI Ecosystem"
        subtitle = "Sales Copilot Active"
        gradient = "linear-gradient(135deg, #10B981 0%, #059669 100%)"
        glow = "0 20px 40px rgba(16, 185, 129, 0.3)"
    else:
        logo = "🏠"
        title = "Lyrio.io AI Ecosystem"
        subtitle = "Enterprise Architectural Command Center"
        gradient = "linear-gradient(135deg, #006AFF 0%, #0047AB 100%)"
        glow = "0 20px 40px rgba(0, 106, 255, 0.3)"
    
    st.markdown(f"""
        <div style='background: {gradient}; 
                    padding: 3rem 2.5rem; 
                    border-radius: 20px; 
                    margin-bottom: 2.5rem; 
                    color: white;
                    box-shadow: {glow};
                    position: relative;
                    overflow: hidden;'>
            <div style='position: absolute; top: 0; left: 0; right: 0; bottom: 0; 
                        background-image: 
                            radial-gradient(circle at 20% 50%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
                            radial-gradient(circle at 80% 80%, rgba(255, 255, 255, 0.1) 0%, transparent 50%);
                        opacity: 0.6;'></div>
            <div style='position: relative; z-index: 1;'>
                <div style='display: flex; align-items: center; gap: 1.5rem; margin-bottom: 1rem;'>
                    <div style='font-size: 4rem; line-height: 1;'>{logo}</div>
                    <div>
                        <h1 style='margin: 0; font-size: 2.75rem; font-weight: 800; color: white !important; 
                                   text-shadow: 0 2px 10px rgba(0,0,0,0.2);'>
                            {title}
                        </h1>
                        <p style='margin: 0.25rem 0 0 0; font-size: 1.15rem; opacity: 0.95; font-weight: 500; color: white !important;'>
                            {subtitle}
                        </p>
                    </div>
                </div>
                <p style='margin: 1.5rem 0; font-size: 1.05rem; opacity: 0.9; max-width: 800px; color: white !important;'>
                    Proprietary AI-powered lead intelligence and autonomous workflow environment for <strong>Jorge Sales</strong>
                </p>
                <div style='margin-top: 1.5rem; display: flex; flex-wrap: wrap; gap: 1rem; font-size: 0.95rem;'>
                    <div style='background: rgba(255,255,255,0.25); 
                                padding: 0.75rem 1.25rem; 
                                border-radius: 10px;
                                backdrop-filter: blur(10px);
                                display: flex;
                                align-items: center;
                                gap: 0.5rem;
                                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                                color: white !important;'>
                        <span style='font-size: 1.2rem;'>✅</span>
                        <span style='font-weight: 600;'>AI Mode: Active</span>
                    </div>
                    <div style='background: rgba(255,255,255,0.25); 
                                padding: 0.75rem 1.25rem; 
                                border-radius: 10px;
                                backdrop-filter: blur(10px);
                                display: flex;
                                align-items: center;
                                gap: 0.5rem;
                                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                                color: white !important;'>
                        <span style='font-size: 1.2rem;'>🔗</span>
                        <span style='font-weight: 600;'>GHL Sync: Live</span>
                    </div>
                    <div style='background: rgba(255,255,255,0.25); 
                                padding: 0.75rem 1.25rem; 
                                border-radius: 10px;
                                backdrop-filter: blur(10px);
                                display: flex;
                                align-items: center;
                                gap: 0.5rem;
                                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                                color: white !important;'>
                        <span style='font-size: 1.2rem;'>📊</span>
                        <span style='font-weight: 600;'>Multi-Tenant Ready</span>
                    </div>
                    <div style='background: rgba(16, 185, 129, 0.9); 
                                padding: 0.75rem 1.25rem; 
                                border-radius: 10px;
                                backdrop-filter: blur(10px);
                                display: flex;
                                align-items: center;
                                gap: 0.5rem;
                                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                                color: white !important;'>
                        <span style='font-size: 1.2rem;'>🚀</span>
                        <span style='font-weight: 700;'>5 Hubs Live</span>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_page_header(title: str, subtitle: str = "", icon: str = "📊"):
    """
    Render a standardized page header for internal pages.
    
    Args:
        title: Page title
        subtitle: Optional subtitle
        icon: Emoji icon for the page
    """
    
    subtitle_html = f"<p style='margin: 0.5rem 0 0 0; color: #64748b; font-size: 1rem;'>{subtitle}</p>" if subtitle else ""
    
    st.markdown(f"""
        <div style='
            padding: 1.5rem;
            background: white;
            border-radius: 16px;
            border: 1px solid #f1f5f9;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            margin-bottom: 2rem;
        '>
            <div style='display: flex; align-items: center; gap: 1rem;'>
                <span style='font-size: 2rem;'>{icon}</span>
                <div>
                    <h2 style='margin: 0; font-size: 1.5rem; font-weight: 800; color: #0f172a;'>{title}</h2>
                    {subtitle_html}
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
