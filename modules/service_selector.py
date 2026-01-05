"""
Service Selector Module
Interactive AI Strategy Planner to recommend the right services based on business needs.
"""
import streamlit as st
import utils.ui as ui

SERVICES = {
    "lead_scoring": {
        "title": "Predictive Lead Scoring",
        "icon": "🔮",
        "desc": "Prioritize your sales pipeline using ensemble-based conversion forecasting.",
        "impact": "High conversion lift",
        "best_for": "Businesses with high lead volume (>100/mo)"
    },
    "reengagement": {
        "title": "Automated Re-engagement",
        "icon": "🔄",
        "desc": "Recover lost opportunities through intelligent multi-channel follow-up sequences.",
        "impact": "Recovered revenue",
        "best_for": "Businesses with many cold leads or high churn"
    },
    "analytics": {
        "title": "Advanced Attribution Analytics",
        "icon": "📊",
        "desc": "Full-funnel tracking to quantify exactly which channels drive revenue.",
        "impact": "Budget optimization",
        "best_for": "Marketing-heavy teams needing ROI visibility"
    },
    "agent_logic": {
        "title": "Autonomous Agent Logic",
        "icon": "🤖",
        "desc": "24/7 intelligent response and qualification for instant lead engagement.",
        "impact": "Operational efficiency",
        "best_for": "Teams struggling with response times or 24/7 coverage"
    },
    "executive": {
        "title": "Executive Strategic Dashboard",
        "icon": "👔",
        "desc": "High-level portfolio analysis and AI-driven strategic recommendations.",
        "impact": "Strategic clarity",
        "best_for": "Decision makers managing multiple tenants or locations"
    }
}

def render():
    """Main render function for the Service Selector."""
    ui.section_header("AI Strategy Planner", "Find the optimal AI orchestration for your business challenges.")
    
    tabs = st.tabs(["🎯 Strategy Diagnostic", "🎓 Credentials & Certifications"])
    
    with tabs[0]:
        _render_diagnostic()
        
    with tabs[1]:
        _render_credentials()

def _render_diagnostic():
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 🔍 Business Diagnostic")
        st.write("Answer a few questions to receive a tailored implementation roadmap.")
        
        industry = st.selectbox("Industry Vertical", ["Real Estate", "SaaS", "E-commerce", "Healthcare", "Professional Services"])
        
        challenge = st.multiselect(
            "Primary Challenges (Select all that apply)",
            [
                "Slow lead response times",
                "Low lead quality / wasted sales time",
                "High churn / lost leads",
                "No visibility into marketing ROI",
                "Manual reporting takes too long",
                "Need 24/7 coverage"
            ]
        )
        
        volume = st.radio(
            "Monthly Lead Volume",
            ["0 - 50", "51 - 200", "201 - 1000", "1000+"]
        )
        
        st.divider()
        if st.button("Generate Strategy Roadmap", type="primary"):
            _generate_roadmap(industry, challenge, volume)
    
    with col2:
        st.markdown("#### 💡 Recommended Architecture")
        if "recommended_services" in st.session_state:
            for svc_id in st.session_state.recommended_services:
                svc = SERVICES[svc_id]
                ui.use_case_card(
                    icon=svc["icon"],
                    title=svc["title"],
                    description=f"<strong>{svc['desc']}</strong><br><br>Target Impact: {svc['impact']}<br>Best For: {svc['best_for']}"
                )
                st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
        else:
            st.info("Complete the diagnostic on the left to see your recommended AI architecture.")

def _render_credentials():
    st.markdown("#### 🎓 Institutional-Grade Expertise")
    st.write("1,768+ hours of technical training across 19 professional certifications from the world's leading institutions.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ui.feature_card(
            icon="🧠",
            title="Generative AI & LLMOps",
            description="""
            • Vanderbilt: GenAI Strategic Leader<br>
            • IBM: GenAI Engineering (144 hrs)<br>
            • IBM: RAG & Agentic AI Architect<br>
            • Duke: LLMOps Specialization<br>
            • Google: GenAI Leader Specialization
            """,
            status="hero"
        )
    
    with col2:
        ui.feature_card(
            icon="📊",
            title="Data Science & ML",
            description="""
            • Google: Advanced Analytics (200 hrs)<br>
            • Google: Data Analytics Professional<br>
            • DeepLearning.AI: DL Specialization<br>
            • Microsoft: AI & ML Engineering<br>
            • UMich: Python for Everybody
            """,
            status="active"
        )
        
    with col3:
        ui.feature_card(
            icon="👔",
            title="Business Intelligence",
            description="""
            • IBM: BI Analyst (141 hrs)<br>
            • Google: BI Professional (80 hrs)<br>
            • Microsoft: Data Visualization<br>
            • Meta: Social Media Marketing<br>
            • Google: Digital Marketing
            """,
            status="active"
        )

    st.divider()
    st.info("🔗 [View Detailed Verification Document](https://github.com/ChunkyTortoise/enterprise-hub/blob/main/docs/sales/CERTIFICATION_VERIFICATION.md)")


def _generate_roadmap(industry, challenges, volume):
    """Determine recommended services based on inputs."""
    recommendations = []
    
    # Logic based on challenges
    if "Slow lead response times" in challenges or "Need 24/7 coverage" in challenges:
        recommendations.append("agent_logic")
        
    if "Low lead quality / wasted sales time" in challenges:
        recommendations.append("lead_scoring")
        
    if "High churn / lost leads" in challenges:
        recommendations.append("reengagement")
        
    if "No visibility into marketing ROI" in challenges or "Manual reporting takes too long" in challenges:
        recommendations.append("analytics")
        recommendations.append("executive")
        
    # Lead volume weight
    if volume in ["201 - 1000", "1000+"] and "lead_scoring" not in recommendations:
        recommendations.append("lead_scoring")
        
    # Deduplicate and limit to top 3
    recommendations = list(dict.fromkeys(recommendations))[:3]
    
    st.session_state.recommended_services = recommendations
    st.success("Roadmap generated! See your recommendations on the right.")
