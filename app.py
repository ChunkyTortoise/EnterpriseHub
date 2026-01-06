"""
Enterprise Hub - Main Application Entry Point.
A unified platform for professional AI services and engineering excellence.
"""

import streamlit as st
import sys
import importlib

# ENTERPRISE CONFIGURATION
st.set_page_config(
    page_title="Unified Enterprise Hub | Cayman Roden",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- SERVICE CATEGORIES & MODULE REGISTRY ---
CATEGORIES = {
    "⭐ Flagship": ["🏗️ ARETE-Architect"],
    "🤖 Intelligent Automation": ["Custom RAG Agents", "Multi-Agent Swarms", "Content Engine", "Business Automation"],
    "📊 BI & Analytics": ["Margin Hunter", "Market Pulse", "Data Detective", "Marketing Analytics", "Smart Forecast", "Automated Reporting"],
    "🏢 Vertical Solutions": ["GHL Real Estate AI", "Vertical Insights"],
    "🛠️ Infrastructure & Strategy": ["Technical Due Diligence", "DevOps Control", "AI Strategy Planner", "ROI Calculators", "Design System"]
}

MODULES = {
    "🏗️ ARETE-Architect": {
        "name": "arete_architect", "title": "ARETE-Architect: AI Technical Co-Founder",
        "icon": "assets/icons/arete_architect.svg", "status": "hero", "service_id": "S4",
        "category": "Intelligent Automation", "roi_model": "340 hours saved/week | 10,450% ROI"
    },
    "Custom RAG Agents": {
        "name": "real_estate_ai", "title": "Knowledge-Augmented RAG Agents",
        "icon": "assets/icons/arete_architect.svg", "status": "active", "service_id": "S3",
        "category": "Intelligent Automation", "roi_model": "60% reduction in support workload"
    },
    "Multi-Agent Swarms": {
        "name": "multi_agent", "title": "Multi-Agent Swarm Orchestration",
        "icon": "assets/icons/multi_agent.svg", "status": "active", "service_id": "S4",
        "category": "Intelligent Automation", "roi_model": "85% automation of manual lead research"
    },
    "Content Engine": {
        "name": "content_engine", "title": "Programmatic SEO & Content Engine",
        "icon": "assets/icons/content_engine.svg", "status": "active", "service_id": "S12",
        "category": "Intelligent Automation", "roi_model": "50x increase in volume at 1/300th cost"
    },
    "Business Automation": {
        "name": "business_automation", "title": "Workflow & Business Automation",
        "icon": "assets/icons/calculator.svg", "status": "active", "service_id": "S6",
        "category": "Intelligent Automation", "roi_model": "Recover 85-90% of manual task productivity"
    },
    "Margin Hunter": {
        "name": "margin_hunter", "title": "Margin Hunter: Unit Economics Engine",
        "icon": "assets/icons/margin_hunter.svg", "status": "active", "service_id": "S1",
        "category": "BI & Analytics", "roi_model": "Identifies 5-10 initiatives with 6-12 month payback"
    },
    "Market Pulse": {
        "name": "market_pulse", "title": "Market Pulse: Technical Analysis",
        "icon": "assets/icons/market_pulse.svg", "status": "active", "service_id": "S8",
        "category": "BI & Analytics", "roi_model": "$24,000/year savings on Terminal subs"
    },
    "Data Detective": {
        "name": "data_detective", "title": "Data Detective: Automated EDA",
        "icon": "assets/icons/data_detective.svg", "status": "active", "service_id": "S11",
        "category": "BI & Analytics", "roi_model": "Reduces analysis from 2 hours to 2 minutes"
    },
    "Marketing Analytics": {
        "name": "marketing_analytics", "title": "Marketing Attribution Hub",
        "icon": "assets/icons/marketing_analytics.svg", "status": "active", "service_id": "S16",
        "category": "BI & Analytics", "roi_model": "20-40% improvement in spend efficiency"
    },
    "Smart Forecast": {
        "name": "smart_forecast", "title": "Smart Forecast: Predictive Intelligence",
        "icon": "assets/icons/smart_forecast.svg", "status": "active", "service_id": "S10",
        "category": "BI & Analytics", "roi_model": "15-25% improvement in forecast accuracy"
    },
    "Automated Reporting": {
        "name": "automated_reporting", "title": "Automated Reporting Pipelines",
        "icon": "assets/icons/strategy.svg", "status": "active", "service_id": "S9",
        "category": "BI & Analytics", "roi_model": "Eliminate 8+ hours/week of manual Excel work"
    },
    "GHL Real Estate AI": {
        "name": "real_estate_ai", "title": "GHL Real Estate AI",
        "icon": "assets/icons/real_estate.svg", "status": "active", "service_id": "V1",
        "category": "Vertical Solutions", "roi_model": "$518,400/year incremental revenue potential"
    },
    "Vertical Insights": {
        "name": "landing_pages", "title": "Industry-Specific Value Stacks",
        "icon": "assets/icons/verticals.svg", "status": "new", "service_id": "STRAT",
        "category": "Vertical Solutions", "roi_model": "20% reduction in churn via industry patterns"
    },
    "Technical Due Diligence": {
        "name": "technical_due_diligence", "title": "Technical Due Diligence",
        "icon": "assets/icons/design_system.svg", "status": "active", "service_id": "S2",
        "category": "Infrastructure & Strategy", "roi_model": "Prevents $200k-$2M+ acquisition value loss"
    },
    "AI Strategy Planner": {
        "name": "service_selector", "title": "AI Strategy & Readiness Planner",
        "icon": "assets/icons/strategy.svg", "status": "new", "service_id": "S1",
        "category": "Infrastructure & Strategy", "roi_model": "Prevents $50k-$200k in misallocated spend"
    },
    "ROI Calculators": {
        "name": "roi_calculators", "title": "ROI & Growth Calculators",
        "icon": "assets/icons/calculator.svg", "status": "new", "service_id": "STRAT",
        "category": "Infrastructure & Strategy", "roi_model": "Instant data-driven investment justification"
    },
    "DevOps Control": {
        "name": "devops_control", "title": "DevOps & MLOps Control",
        "icon": "assets/icons/devops_control.svg", "status": "active", "service_id": "S18",
        "category": "Infrastructure & Strategy", "roi_model": "80% reduction in maintenance overhead"
    },
    "Design System": {
        "name": "design_system", "title": "Design System Gallery",
        "icon": "assets/icons/design_system.svg", "status": "active", "service_id": "UI",
        "category": "Infrastructure & Strategy", "roi_model": "WCAG AAA compliance for all deployments"
    },
}

def main():
    import utils.ui as ui
    if "theme" not in st.session_state: st.session_state.theme = "light"
    
    with st.sidebar:
        st.markdown("<h1 style='color: #10B981;'>ENTERPRISE HUB</h1>", unsafe_allow_html=True)
        st.markdown("Cayman Roden | Services Console")
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("☀️ Light", use_container_width=True):
                st.session_state.theme = "light"; st.rerun()
        with col2:
            if st.button("🌙 Dark", use_container_width=True):
                st.session_state.theme = "dark"; st.rerun()
        
        st.divider()
        st.markdown("### 🧭 Navigation")
        nav_options = ["🏠 Overview"]
        for cat, mods in CATEGORIES.items():
            nav_options.append(f"--- {cat} ---")
            nav_options.extend(mods)
        
        selection = st.radio("Go to:", nav_options, label_visibility="collapsed")
        page = selection if selection in MODULES or selection == "🏠 Overview" else "🏠 Overview"
        
        st.divider()
        st.markdown("### 👤 Cayman Roden")
        st.markdown("AI Systems Architect")
        st.markdown("[View Portfolio](https://chunkytortoise.github.io/EnterpriseHub/)")

    ui.setup_interface(st.session_state.theme)

    if page == "🏠 Overview":
        from modules import landing_pages
        landing_pages.render()
    elif page in MODULES:
        _load_and_render_module(MODULES[page])
    
    ui.footer()

def _load_and_render_module(module_info):
    import utils.ui as ui
    ui.service_header(
        title=module_info["title"],
        category=module_info.get("category", "General"),
        service_id=module_info.get("service_id", "N/A"),
        roi_model=module_info.get("roi_model", "N/A")
    )
    with st.spinner(f"Loading {module_info['title']}..."):
        try:
            module = importlib.import_module(f"modules.{module_info['name']}")
            module.render()
        except Exception as e:
            st.error(f"❌ Failed to load {module_info['title']}"); st.exception(e)

if __name__ == "__main__":
    main()
