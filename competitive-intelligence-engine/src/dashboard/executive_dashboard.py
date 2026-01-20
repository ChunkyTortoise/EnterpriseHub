"""
Executive Analytics Dashboard Page

This module provides the main entry point for the executive analytics dashboard,
integrating all analytics components into a cohesive Streamlit application.

Author: Claude
Date: January 2026
"""

import streamlit as st
import asyncio
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.executive_analytics_dashboard import ExecutiveAnalyticsDashboard


def main():
    """Main entry point for the executive analytics dashboard."""
    
    # Set page configuration
    st.set_page_config(
        page_title="Executive Analytics - Competitive Intelligence",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Add custom CSS for executive styling
    st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .metric-card {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #007bff;
            margin-bottom: 1rem;
        }
        
        .alert-success {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 0.75rem;
            border-radius: 0.375rem;
            margin-bottom: 1rem;
        }
        
        .alert-warning {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 0.75rem;
            border-radius: 0.375rem;
            margin-bottom: 1rem;
        }
        
        .alert-danger {
            background-color: #f8d7da;
            border: 1px solid #f1aeb5;
            color: #721c24;
            padding: 0.75rem;
            border-radius: 0.375rem;
            margin-bottom: 1rem;
        }
        
        .stSelectbox > div > div {
            background-color: #007bff;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header section
    st.markdown("""
    <div class="main-header">
        <h1>🎯 Executive Analytics Intelligence</h1>
        <p>AI-Powered Strategic Intelligence for Executive Decision Making</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize dashboard
    dashboard = ExecutiveAnalyticsDashboard()
    
    # Render the dashboard
    dashboard.render_dashboard()
    
    # Footer with system information
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption("🤖 **Claude 3.5 Sonnet** | AI-powered strategic analysis")
    
    with col2:
        st.caption("⚡ **Real-time Analytics** | Updated every 5 minutes")
    
    with col3:
        st.caption(f"🕐 **Last Updated**: {datetime.now().strftime('%H:%M:%S')}")


if __name__ == "__main__":
    main()