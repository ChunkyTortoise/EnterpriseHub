"""
Enterprise Hub - Main Application Entry Point.

A unified platform for market analysis and enterprise tooling
with multiple mission-critical modules.
"""

import streamlit as st
import sys

# FAST BOOT: Minimal imports at top level
# We delay importing 'utils.ui' and 'modules.*' until inside main()

# ENTERPRISE CONFIGURATION
st.set_page_config(
    page_title="Unified Enterprise Hub | Cayman Roden",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/ChunkyTortoise/enterprise-hub",
        "Report a bug": "https://github.com/ChunkyTortoise/enterprise-hub/issues",
        "About": (
            "# Enterprise Hub\nA unified platform for market analysis and enterprise tooling."
        ),
    },
)

# --- MODULE REGISTRY ---
# Flagship AI Technical Co-Founder module takes precedence
MODULES = {
    "🏗️ ARETE-Architect": {
        "name": "arete_architect",
        "title": "ARETE-Architect: AI Technical Co-Founder",
        "icon": "assets/icons/arete_architect.svg",
        "desc": "Flagship autonomous technical co-founder powered by LangGraph. Features self-healing code generation, deep architectural mapping, and automated CI/CD integration.",
        "status": "hero"
    },
    "💰 Margin Hunter": {
        "name": "margin_hunter",
        "title": "Margin Hunter",
        "icon": "assets/icons/margin_hunter.png",
        "desc": "Advanced institutional-grade unit economics engine. Delivers high-fidelity sensitivity analysis, real-time break-even modeling, and multi-scenario margin optimization.",
        "status": "active"
    },
    "📊 Market Pulse": {
        "name": "market_pulse",
        "title": "Market Pulse",
        "icon": "assets/icons/market_pulse.png",
        "desc": "Institutional-grade technical analysis suite. High-performance charting engine featuring RSI, MACD, and volume profile analysis for professional asset evaluation.",
        "status": "active"
    },
    "🔍 Data Detective": {
        "name": "data_detective",
        "title": "Data Detective",
        "icon": "assets/icons/data_detective.png",
        "desc": "Heuristic data profiling engine. Automates exploratory data analysis (EDA) with advanced correlation mapping, statistical quality scoring, and automated insight generation.",
        "status": "new"
    },
    "📈 Marketing Analytics": {
        "name": "marketing_analytics",
        "title": "Marketing Analytics",
        "icon": "assets/icons/marketing_analytics.svg",
        "desc": "Enterprise-scale marketing attribution and ROI orchestration engine. Features multi-variant statistical testing, cohort analysis, and sophisticated attribution modeling.",
        "status": "new"
    },
    "✍️ Content Engine": {
        "name": "content_engine",
        "title": "Content Engine",
        "icon": "assets/icons/content_engine.png",
        "desc": "Strategic content synthesis platform leveraging Anthropic's Claude 3.5 Sonnet to generate high-authority LinkedIn thought leadership and technical documentation.",
        "status": "active"
    },
    "🧠 Smart Forecast": {
        "name": "smart_forecast",
        "title": "Smart Forecast Engine",
        "icon": "assets/icons/smart_forecast.svg",
        "desc": "Predictive intelligence engine leveraging Random Forest ensembles and rolling-window backtesting to deliver statistically rigorous time-series forecasting.",
        "status": "new"
    },
    "🤖 Multi-Agent Workflow": {
        "name": "multi_agent",
        "title": "Multi-Agent Workflow",
        "icon": "assets/icons/multi_agent.svg",
        "desc": "State-of-the-art agentic orchestration. Synchronizes specialized sub-agents (Data, Tech, News, Chief) for comprehensive 360° asset intelligence.",
        "status": "new"
    },
    "🏗️ DevOps Control": {
        "name": "devops_control",
        "title": "DevOps Control",
        "icon": "assets/icons/devops.svg",
        "desc": "Full-spectrum CI/CD orchestration console. Real-time monitoring of build pipelines, test coverage analytics, and autonomous deployment status tracking.",
        "status": "active"
    },
    "🤖 Agent Logic": {
        "name": "agent_logic",
        "title": "Agent Logic",
        "icon": "assets/icons/agent_logic.svg",
        "desc": "Autonomous market intelligence agent. Orchestrates NLP-driven sentiment analysis and real-time news aggregation for proactive market positioning.",
        "status": "active"
    },
    "💼 Financial Analyst": {
        "name": "financial_analyst",
        "title": "Financial Analyst",
        "icon": "assets/icons/financial_analyst.png",
        "desc": "Comprehensive fundamental analysis framework. Delivers deep-dive financial statement audits, ratio analysis, and intrinsic valuation modeling.",
        "status": "active"
    },
    "🎨 Design System": {
        "name": "design_system",
        "title": "Design System Gallery",
        "icon": "assets/icons/design_system.svg",
        "desc": "Centralized UI/UX architecture laboratory showcasing the project's institutional-grade glassmorphic components and WCAG-compliant theme engine.",
        "status": "active"
    },
}

def main():
    """Main application function with Lazy Loading."""
    
    # Lazy Import UI to prevent import loops or early crashes
    try:
        import utils.ui as ui
        from utils.logger import get_logger
        logger = get_logger(__name__)
    except ImportError as e:
        st.error(f"Critical System Error: Failed to load core utilities. {e}")
        st.stop()

    # Initialize session state
    if "theme" not in st.session_state:
        st.session_state.theme = "light"
    if "username" not in st.session_state:
        st.session_state.username = "Guest"

    try:
        # PRODUCTION GATEWAY (Optional - removed for public demo)
        # if not ui.login_modal(): st.stop()

        # Initialize page variable
        page = "🏠 Overview"

        # SIDEBARNAVIGATION
        with st.sidebar:
            st.markdown(
                f"""
                <div style='margin-bottom: 32px;'>
                    <h1 style='
                        font-family: "Space Grotesk", sans-serif;
                        font-size: 1.5rem;
                        font-weight: 800;
                        letter-spacing: -0.05em;
                        margin: 0;
                        color: #0F172A;
                    '>
                        ENTERPRISE<span style='color: #10B981;'>HUB</span>
                    </h1>
                    <div style='
                        color: #64748b;
                        font-size: 0.7rem;
                        font-weight: 600;
                        letter-spacing: 0.1em;
                        text-transform: uppercase;
                    '>
                        Platform Console v5.0.1
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Theme Toggle - RESTORED ALL 4 THEMES
            st.markdown("---")
            st.markdown("**🎨 Theme**")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("☀️ Light", use_container_width=True):
                    st.session_state.theme = "light"
                    st.rerun()
                if st.button("🌊 Ocean", use_container_width=True):
                    st.session_state.theme = "ocean"
                    st.rerun()
            with col2:
                if st.button("🌙 Dark", use_container_width=True):
                    st.session_state.theme = "dark"
                    st.rerun()
                if st.button("🌅 Sunset", use_container_width=True):
                    st.session_state.theme = "sunset"
                    st.rerun()

            # Navigation
            st.markdown("---")
            pages = ["🏠 Overview"] + list(MODULES.keys())
            page = st.radio("Navigate:", pages, label_visibility="collapsed")

            st.markdown("---")
            st.markdown("### 👤 **Cayman Roden**")
            st.markdown("Full-Stack Python Developer")
            st.markdown("[View Portfolio](https://chunkytortoise.github.io/EnterpriseHub/)")

        # Setup UI
        ui.setup_interface(st.session_state.theme)

        # MAIN CONTAINER
        if page == "🏠 Overview":
            _render_overview(ui)
        elif page in MODULES:
            module_info = MODULES[page]
            _load_and_render_module(module_info["name"], module_info["title"])
        
        # Footer
        ui.footer()

    except Exception as e:
        st.error("❌ An unexpected error occurred in the application.")
        st.exception(e)

def _load_and_render_module(module_name, module_title):
    """Dynamically imports and renders a module to save memory/startup time."""
    import importlib
    import streamlit as st
    import utils.ui as ui  # Re-import locally to be safe

    ui.section_header(module_title)

    with st.spinner(f"Loading {module_title}..."):
        try:
            # THIS IS THE KEY FIX: Import only when requested
            module = importlib.import_module(f"modules.{module_name}")
            module.render()
        except ModuleNotFoundError:
            st.warning(f"⚠️ Module '{module_name}' is not yet deployed.")
        except Exception as e:
            st.error(f"❌ Failed to load {module_title}")
            st.exception(e)

def _render_overview(ui):
    """Render the overview/home page - RESTORED TO FULL RICH UI."""
    import streamlit as st
    
    # Hero Section
    ui.hero_section(
        "Unified Enterprise Hub",
        f"A production-grade business intelligence platform consolidating "
        f"{len(MODULES)} mission-critical tools into a single, cloud-native interface."
    )

    # Metrics Row - Highlighting ARETE and Technical Co-Founder capabilities
    col1, col2, col3, col4 = st.columns(4)
    with col1: ui.card_metric("Flagship Module", "ARETE", "Self-Maintaining AI")
    with col2: ui.card_metric("Active Modules", f"{len(MODULES)}", "LangGraph + Claude")
    with col3: ui.card_metric("Test Coverage", "220+", "Production-Ready")
    with col4: ui.card_metric("Architecture", "Stateful Agents", "Autonomous")

    ui.spacer(40)
    st.markdown("### 🛠️ Module Suite")

    # Dynamic Feature Grid (Rows of 3)
    module_keys = list(MODULES.keys())
    for i in range(0, len(module_keys), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(module_keys):
                key = module_keys[i + j]
                info = MODULES[key]
                with cols[j]:
                    ui.feature_card(
                        icon=info["icon"] if info["icon"] else "🚀",
                        title=info["title"],
                        description=info["desc"],
                        status=info["status"],
                        icon_path=info["icon"] if info.get("icon") else None,
                    )
        ui.spacer(20)

    ui.spacer(40)
    ui.section_header(
        "Built For Real Business Challenges",
        ("See how EnterpriseHub replaces manual workflows and expensive subscriptions"),
    )

    col1, col2 = st.columns(2)
    with col1:
        ui.use_case_card(
            icon="💡",
            title="For SaaS Founders",
            description="""
                <strong>Margin Hunter</strong> replaces Excel spreadsheet
                chaos for pricing decisions. Run 100 profit scenarios
                simultaneously with sensitivity heatmaps. Break-even
                analysis that updates in real-time as you adjust prices.
            """,
        )

        st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

        ui.use_case_card(
            icon="📊",
            title="For Finance Teams",
            description="""
                <strong>Market Pulse</strong> eliminates Bloomberg Terminal
                dependency for basic technical analysis. 4-panel charts
                (Price/RSI/MACD/Volume) with institutional-grade indicators.
                Save $24,000/year in subscriptions.
            """,
        )

    with col2:
        ui.use_case_card(
            icon="🔍",
            title="For Data Analysts",
            description="""
                <strong>Data Detective</strong> reduces exploratory data
                analysis from 2 hours to 2 minutes. AI-powered insights,
                correlation heatmaps, and quality scoring. Upload CSV → Get
                actionable findings instantly.
            """,
        )

        st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

        ui.use_case_card(
            icon="📈",
            title="For Marketing Teams",
            description="""
                **Marketing Analytics** replaces agency dashboards costing
                $200-500/month. 5 attribution models, A/B test calculators,
                and campaign ROI tracking. One-time build you own forever.
            """,
        )

if __name__ == "__main__":
    main()