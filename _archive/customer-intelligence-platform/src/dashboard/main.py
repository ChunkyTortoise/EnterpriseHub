"""
Customer Intelligence Platform - Main Dashboard Application

This is the main Streamlit dashboard that brings together all components:
- Chat interface for customer intelligence
- Scoring dashboard for predictive analytics
- Analytics dashboard for business intelligence
"""

import streamlit as st
import sys
from pathlib import Path
import asyncio

# Add src to path for imports
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from dashboard.components.chat_interface import render_chat_interface
from dashboard.components.scoring_dashboard import render_scoring_dashboard
from dashboard.components.analytics_dashboard import render_analytics_dashboard
from utils.logger import get_logger

# Configure page
st.set_page_config(
    page_title="Customer Intelligence Platform",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

logger = get_logger(__name__)


def render_sidebar():
    """Render the sidebar navigation."""
    st.sidebar.markdown("## 🎯 Customer Intelligence")
    st.sidebar.markdown("### Navigation")
    
    # Navigation options
    pages = {
        "🏠 Overview": "overview",
        "💬 Chat Intelligence": "chat",
        "📊 Scoring Dashboard": "scoring", 
        "📈 Analytics": "analytics"
    }
    
    selected_page = st.sidebar.radio(
        "Choose a view:",
        list(pages.keys()),
        key="main_navigation"
    )
    
    # API Configuration
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Configuration")
    
    api_base_url = st.sidebar.text_input(
        "API Base URL",
        value="http://localhost:8000/api/v1",
        key="api_base_url"
    )
    
    # Store in session state
    st.session_state['api_base_url'] = api_base_url
    
    # Quick actions
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🚀 Quick Actions")
    
    if st.sidebar.button("🔄 Refresh Data", key="sidebar_refresh"):
        st.cache_data.clear()
        st.rerun()
    
    if st.sidebar.button("🧹 Clear Cache", key="sidebar_clear_cache"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("Cache cleared!")
    
    # System status
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📡 System Status")
    
    # API Health Check
    try:
        import requests
        response = requests.get(f"{api_base_url.rstrip('/api/v1')}/health", timeout=5)
        if response.status_code == 200:
            st.sidebar.success("🟢 API Online")
        else:
            st.sidebar.error("🔴 API Issues")
    except:
        st.sidebar.warning("🟡 API Checking...")
    
    return pages[selected_page]


def render_overview():
    """Render the overview page."""
    st.title("🎯 Customer Intelligence Platform")
    st.markdown("### AI-Powered Customer Intelligence with RAG and Predictive Scoring")
    
    # Hero section
    st.markdown("""
    <div style='background: linear-gradient(135deg, #1e3a8a 0%, #3730a3 100%); 
                padding: 2rem; border-radius: 10px; color: white; margin: 1rem 0;'>
        <h2 style='margin: 0; color: white;'>Welcome to Customer Intelligence Platform</h2>
        <p style='margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;'>
            Leverage AI to understand customers, predict behavior, and drive growth
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        #### 💬 Chat Intelligence
        - **RAG-powered conversations** with knowledge base
        - **Context-aware responses** using customer history
        - **Real-time insights** and recommendations
        - **Multi-department** support and routing
        """)
        
        if st.button("🚀 Launch Chat", key="launch_chat", use_container_width=True):
            st.session_state['main_navigation'] = "💬 Chat Intelligence"
            st.rerun()
    
    with col2:
        st.markdown("""
        #### 📊 Scoring Dashboard
        - **Predictive lead scoring** with ML models
        - **Real-time scoring** for new customers
        - **Model performance** monitoring
        - **Feature importance** analysis
        """)
        
        if st.button("📈 View Scores", key="launch_scoring", use_container_width=True):
            st.session_state['main_navigation'] = "📊 Scoring Dashboard"
            st.rerun()
    
    with col3:
        st.markdown("""
        #### 📈 Analytics
        - **Interactive dashboards** with drill-down
        - **Customer engagement** trends
        - **Conversion funnel** analysis
        - **Performance metrics** and KPIs
        """)
        
        if st.button("📊 Explore Analytics", key="launch_analytics", use_container_width=True):
            st.session_state['main_navigation'] = "📈 Analytics"
            st.rerun()
    
    # Quick stats
    st.markdown("---")
    st.markdown("### 📊 Quick Stats")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Customers", "247", "+12")
    with col2:
        st.metric("Avg Lead Score", "0.72", "+0.05")
    with col3:
        st.metric("Conversion Rate", "23.4%", "+2.1%")
    with col4:
        st.metric("Response Time", "1.2s", "-0.3s")
    
    # Getting started
    st.markdown("---")
    st.markdown("### 🚀 Getting Started")
    
    with st.expander("💡 Quick Start Guide"):
        st.markdown("""
        1. **Chat Intelligence**: Ask questions about your customers and get AI-powered insights
        2. **Score Customers**: Use ML models to predict customer behavior and conversion probability
        3. **Analyze Performance**: Explore interactive dashboards to understand your business metrics
        4. **Monitor Models**: Track model performance and retrain when needed
        
        **Pro Tips**:
        - Use the sidebar to navigate between different views
        - Check the API status in the sidebar to ensure all services are running
        - Refresh data using the sidebar button to get the latest information
        """)
    
    # Architecture overview
    with st.expander("🏗️ Platform Architecture"):
        st.markdown("""
        **Core Components**:
        - **Knowledge Engine**: RAG-powered document search and retrieval
        - **AI Client**: Multi-provider LLM integration (Claude, Gemini, Perplexity)
        - **ML Pipeline**: Automated model training and prediction
        - **Database**: Customer and scoring data management
        - **Cache**: High-performance caching for faster responses
        
        **Technology Stack**:
        - **Backend**: FastAPI, Python 3.11+, SQLite/PostgreSQL
        - **Frontend**: Streamlit, Plotly, Interactive components
        - **AI/ML**: Anthropic Claude, ChromaDB, Scikit-learn
        - **Infrastructure**: Docker, Redis, Async processing
        """)


def main():
    """Main application entry point."""
    # Initialize session state
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        logger.info("Dashboard application started")
    
    # Render sidebar and get selected page
    selected_page = render_sidebar()
    
    # Render selected page
    try:
        if selected_page == "overview":
            render_overview()
        elif selected_page == "chat":
            render_chat_interface(st.session_state.get('api_base_url', 'http://localhost:8000/api/v1'))
        elif selected_page == "scoring":
            render_scoring_dashboard(st.session_state.get('api_base_url', 'http://localhost:8000/api/v1'))
        elif selected_page == "analytics":
            render_analytics_dashboard()
        else:
            st.error(f"Unknown page: {selected_page}")
            
    except Exception as e:
        st.error(f"Error rendering page: {e}")
        logger.error(f"Page rendering error: {e}")
        
        with st.expander("🐛 Error Details"):
            st.exception(e)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; opacity: 0.6; font-size: 0.8rem;'>"
        "Customer Intelligence Platform v1.0 | Built with Streamlit & FastAPI"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()