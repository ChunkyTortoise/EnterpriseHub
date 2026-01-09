"""
Global Header Component - Multi-Tenant Branding Orchestrator
Centralized header rendering with tenant-specific branding
"""
import streamlit as st
from typing import Literal


def render_global_header(tenant_name: Literal["GHL", "ARETE"] = "GHL"):
    """
    Render the global header with tenant-specific branding.
    
    Args:
        tenant_name: Either "GHL" or "ARETE" to determine branding style
    """
    
    # Tenant-specific configuration
    if tenant_name == "ARETE":
        logo = "🦅"
        title = "ARETE Performance"
        subtitle = "Ops & Optimization Hub"
        gradient = "linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%)"
        accent_color = "#7c3aed"
    else:
        logo = "🏠"
        title = "GHL Real Estate AI"
        subtitle = "Enterprise Command Center"
        gradient = "linear-gradient(135deg, #2563eb 0%, #1e40af 100%)"
        accent_color = "#2563eb"
    
    st.markdown(f"""
        <div style='
            padding: 2rem;
            border-radius: 24px;
            background: {gradient};
            color: white;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            margin-bottom: 2rem;
        '>
            <div style='display: flex; align-items: center; gap: 1rem;'>
                <span style='font-size: 2.5rem;'>{logo}</span>
                <div>
                    <h1 style='margin: 0; font-size: 2rem; font-weight: 900; letter-spacing: -0.025em;'>{title}</h1>
                    <p style='margin: 0.25rem 0 0 0; opacity: 0.9; font-size: 1rem; font-weight: 500;'>{subtitle}</p>
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
