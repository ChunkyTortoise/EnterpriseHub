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
# ARETE-Architect is positioned FIRST as the flagship "Technical Co-Founder" module
MODULES = {
    "🏗️ ARETE-Architect": ("arete_architect", "ARETE-Architect: AI Technical Co-Founder", "assets/icons/arete_architect.svg"),
    "📊 Market Pulse": ("market_pulse", "Market Pulse", "assets/icons/market_pulse.png"),
    "💼 Financial Analyst": ("financial_analyst", "Financial Analyst", "assets/icons/financial_analyst.png"),
    "💰 Margin Hunter": ("margin_hunter", "Margin Hunter", "assets/icons/margin_hunter.png"),
    "🤖 Agent Logic": ("agent_logic", "Agent Logic", "assets/icons/agent_logic.svg"),
    "✍️ Content Engine": ("content_engine", "Content Engine", "assets/icons/content_engine.png"),
    "🔍 Data Detective": ("data_detective", "Data Detective", "assets/icons/data_detective.png"),
    "📈 Marketing Analytics": ("marketing_analytics", "Marketing Analytics", "assets/icons/marketing_analytics.svg"),
    "🤖 Multi-Agent Workflow": ("multi_agent", "Multi-Agent Workflow", "assets/icons/multi_agent.svg"),
    "🧠 Smart Forecast": ("smart_forecast", "Smart Forecast Engine", "assets/icons/smart_forecast.svg"),
    "🏗️ DevOps Control": ("devops_control", "DevOps Control", "assets/icons/devops.svg"),
    "🎨 Design System": ("design_system", "Design System Gallery", "assets/icons/design_system.svg"),
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
                        font-family: sans-serif;
                        font-size: 1.5rem;
                        font-weight: 800;
                        letter-spacing: -0.05em;
                        margin: 0;
                    '>
                        ENTERPRISE<span style='color: #4f46e5;'>HUB</span>
                    </h1>
                    <div style='
                        color: #64748b;
                        font-size: 0.7rem;
                        font-weight: 600;
                        letter-spacing: 0.1em;
                        text-transform: uppercase;
                    '>
                        Platform Console v4.0
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
            module_name, module_title, _ = MODULES[page]
            _load_and_render_module(module_name, module_title)
        
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
        "A production-grade business intelligence platform consolidating "
        "9 mission-critical tools into a single, cloud-native interface."
    )

    # Metrics Row - Highlighting ARETE and Technical Co-Founder capabilities
    col1, col2, col3, col4 = st.columns(4)
    with col1: ui.card_metric("Flagship Module", "ARETE", "Self-Maintaining AI")
    with col2: ui.card_metric("Active Modules", f"{len(MODULES)}", "LangGraph + Claude")
    with col3: ui.card_metric("Test Coverage", "220+", "Production-Ready")
    with col4: ui.card_metric("Architecture", "Stateful Agents", "Autonomous")

    ui.spacer(40)
    st.markdown("### 🛠️ Module Suite")

    # Feature Grid - Row 1 - ARETE FIRST (Flagship)
    c1, c2, c3 = st.columns(3)

    with c1:
        module_info = MODULES.get("🏗️ ARETE-Architect")
        ui.feature_card(
            icon=module_info[2] if module_info[2] else "🏗️",
            title=module_info[1],
            description=(
                "Self-maintaining AI Technical Co-Founder with LangGraph workflows. "
                "Autonomous GitHub integration, code generation, and deployment. "
                "The future of software development."
            ),
            status="hero",
            icon_path=module_info[2] if module_info[2] else None,
        )
    with c2:
        module_info = MODULES.get("💰 Margin Hunter")
        ui.feature_card(
            icon=module_info[2] if module_info[2] else "💰",
            title=module_info[1],
            description=(
                "Real-time Cost-Volume-Profit analysis with 10x10 "
                "sensitivity heatmaps and break-even modeling."
            ),
            status="active",
            icon_path=module_info[2] if module_info[2] else None,
        )
    with c3:
        module_info = MODULES.get("📊 Market Pulse")
        ui.feature_card(
            icon=module_info[2] if module_info[2] else "📊",
            title=module_info[1],
            description=(
                "Institutional-grade technical analysis dashboard "
                "with RSI, MACD, and multi-panel charting."
            ),
            status="active",
            icon_path=module_info[2] if module_info[2] else None,
        )

    ui.spacer(20)

    # Feature Grid - Row 2
    c4, c5, c6 = st.columns(3)

    with c4:
        module_info = MODULES.get("🔍 Data Detective")
        ui.feature_card(
            icon=module_info[2] if module_info[2] else "🔍",
            title=module_info[1],
            description=(
                "AI-powered data profiling and statistical analysis. "
                "Upload any CSV/Excel for instant insights."
            ),
            status="new",
            icon_path=module_info[2] if module_info[2] else None,
        )
    with c5:
        module_info = MODULES.get("📈 Marketing Analytics")
        ui.feature_card(
            icon=module_info[2] if module_info[2] else "📈",
            title=module_info[1],
            description=(
                "Comprehensive campaign tracking, ROI calculators, "
                "multi-variant testing, and attribution modeling."
            ),
            status="new",
            icon_path=module_info[2] if module_info[2] else None,
        )
    with c6:
        module_info = MODULES.get("✍️ Content Engine")
        ui.feature_card(
            icon=module_info[2] if module_info[2] else "✍️",
            title=module_info[1],
            description=(
                "Generate professional LinkedIn content in seconds "
                "using Anthropic's Claude 3.5 Sonnet API."
            ),
            status="active",
            icon_path=module_info[2] if module_info[2] else None,
        )

    # Row 3: Agent Logic, Financial Analyst, Multi-Agent
    ui.spacer(20)
    c7, c8, c9 = st.columns(3)

    with c7:
        module_info = MODULES.get("🤖 Agent Logic")
        ui.feature_card(
            icon=module_info[2] if module_info[2] else "🤖",
            title=module_info[1],
            description=(
                "Automated market research and news sentiment analysis using NLP and web scraping."
            ),
            status="active",
            icon_path=module_info[2] if module_info[2] else None,
        )
    with c8:
        module_info = MODULES.get("💼 Financial Analyst")
        ui.feature_card(
            icon=module_info[2] if module_info[2] else "💼",
            title=module_info[1],
            description=(
                "Fundamental stock analysis with financial statements, "
                "ratios, and valuation metrics."
            ),
            status="active",
            icon_path=module_info[2] if module_info[2] else None,
        )

    with c9:
        module_info = MODULES.get("🤖 Multi-Agent Workflow")
        ui.feature_card(
            icon=module_info[2] if module_info[2] else "🤖",
            title=module_info[1],
            description=(
                "Orchestrates 4 specialized agents (Data, Tech, News, Chief) "
                "to perform deep-dive asset analysis."
            ),
            status="new",
            icon_path=module_info[2] if module_info[2] else None,
        )

    with c9:
        module_info = MODULES.get("🧠 Smart Forecast")
        ui.feature_card(
            icon=module_info[2] if module_info[2] else "🧠",
            title=module_info[1],
            description=(
                "AI-powered time series forecasting using Random Forest "
                "and Rolling Window analysis."
            ),
            status="new",
            icon_path=module_info[2] if module_info[2] else None,
        )

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