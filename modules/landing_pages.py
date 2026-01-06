import streamlit as st
import utils.ui as ui

def render():
    """
    Renders the Service-First Landing Page for EnterpriseHub.
    This page serves as the high-impact entry point for potential clients,
    showcase Cayman's certifications, skills, and the Professional Services Catalog.
    """
    
    # Hero Section: Professional Positioning
    st.markdown(
        """
        <div style='text-align: center; padding: 60px 0 40px 0;'>
            <h1 style='font-size: 3.5rem; font-weight: 800; line-height: 1.1; margin-bottom: 20px;'>
                Production-Grade <span style='color: #10B981;'>AI Systems</span><br>
                & Data Infrastructure
            </h1>
            <p style='font-size: 1.4rem; color: #64748b; max-width: 800px; margin: 0 auto 40px auto;'>
                Delivering measurable business outcomes through institutional-grade expertise 
                in Generative AI, LLMOps, and Business Intelligence.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Trust Bar: Certifications & Hours
    cols = st.columns(4)
    with cols[0]:
        ui.card_metric("Certifications", "19", "IBM, Google, Microsoft")
    with cols[1]:
        ui.card_metric("Training Hours", "1,768", "Advanced AI & Data")
    with cols[2]:
        ui.card_metric("Project Delivery", "2x Faster", "Full-Time Focus")
    with cols[3]:
        ui.card_metric("Fixed Pricing", "Transparent", "20% Below Market")

    ui.spacer(60)

    # Decision Tree: "Find Your Solution"
    st.markdown("### 🎯 Find Your Ideal AI Solution")
    st.markdown("Answer a few questions to see which service delivers the highest ROI for your current challenge.")
    
    with st.container(border=True):
        col1, col2 = st.columns([1, 1])
        with col1:
            challenge = st.selectbox(
                "What is your primary business challenge?",
                [
                    "Manual processes consuming team time",
                    "Poor data visibility and decision-making",
                    "Growth and customer acquisition challenges",
                    "Legacy systems blocking progress",
                    "Need strategic guidance first"
                ]
            )
        with col2:
            industry = st.selectbox(
                "What industry are you in?",
                ["B2B SaaS", "E-commerce", "Healthcare", "Professional Services", "Real Estate", "Manufacturing"]
            )
        
        # Simple Recommendation Engine based on Catalog Decision Tree
        recommendations = {
            "Manual processes consuming team time": ["Service 3: Custom RAG Agents", "Service 4: Multi-Agent Workflows", "Service 6: Business Automation"],
            "Poor data visibility and decision-making": ["Service 8: BI Dashboards", "Service 9: Automated Reporting", "Service 10: Predictive Analytics"],
            "Growth and customer acquisition challenges": ["Service 12: Programmatic SEO", "Service 13: Email Automation", "Service 16: Marketing Attribution"],
            "Legacy systems blocking progress": ["Service 19: Excel to Web App Modernization", "Service 20: Competitor Intelligence"],
            "Need strategic guidance first": ["Service 1: AI Strategy Assessment", "Service 25: Fractional AI Leadership"]
        }
        
        st.markdown(f"**Recommended focus for {industry}:**")
        recs = recommendations.get(challenge, [])
        for rec in recs:
            st.markdown(f"- ✅ {rec}")
        
        if st.button("Generate Detailed Implementation Roadmap", type="primary"):
            st.success("Roadmap initialized. Navigate to 'Strategy Planner' for the full diagnostic.")

    ui.spacer(60)

    # Credential Inventory (Summary of Courses.md and Catalog)
    ui.credential_inventory()

    ui.spacer(60)

    # Industry Solutions Section
    ui.section_header("Vertical Industry Solutions", "Deeply integrated AI architectures for your sector")
    
    col1, col2 = st.columns(2)
    with col1:
        ui.use_case_card(
            icon="🚀",
            title="B2B SaaS",
            description="""
                Focus on CAC reduction, churn prevention, and automated unit economics. 
                <strong>Service Bundle 2</strong> recommended for growth-stage startups.
            """,
        )
        st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
        ui.use_case_card(
            icon="🛍️",
            title="E-commerce",
            description="""
                Dynamic pricing, inventory forecasting, and programmatic SEO for 100+ product pages. 
                <strong>Service Bundle 4</strong> optimized for high-volume stores.
            """,
        )
    with col2:
        ui.use_case_card(
            icon="🏥",
            title="Healthcare",
            description="""
                HIPAA-compliant patient agents and clinical knowledge management. 
                <strong>Service Bundle 5</strong> addresses critical regulatory and operational gaps.
            """,
        )
        st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
        ui.use_case_card(
            icon="💼",
            title="Professional Services",
            description="""
                Automated proposal generation and knowledge linking for law and consulting firms. 
                <strong>Service Bundle 3</strong> for scaling delivery without adding headcount.
            """,
        )

    ui.spacer(60)

    # "The Cayman Advantage" Grid
    ui.section_header("The Cayman Advantage", "Why mid-market companies choose this platform")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🛡️ Enterprise Grade")
        st.markdown("Every project includes 300+ automated tests, ensuring your AI systems are reliable, secure, and production-ready.")
    with col2:
        st.markdown("### 💰 ROI Obsessed")
        st.markdown("We don't just build features; we build outcomes. Every service is mapped to a clear ROI model with measurable payback periods.")
    with col3:
        st.markdown("### ⚡ Full-Time Velocity")
        st.markdown("By maintaining a limited client roster and working full-time on your project, I deliver 2x faster than part-time freelancers.")

    ui.spacer(60)

    # Call to Action
    st.markdown(
        """
        <div style='background: #F8FAFC; padding: 40px; border-radius: 20px; text-align: center; border: 1px solid #E2E8F0;'>
            <h2>Ready to Architect Your AI Future?</h2>
            <p style='color: #64748b; margin-bottom: 24px;'>Explore the modules in the sidebar to see live demos of these services in action.</p>
            <div style='display: flex; justify-content: center; gap: 16px;'>
                <a href='mailto:caymanroden@gmail.com' style='background: #0F172A; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;'>Get a Free Assessment</a>
                <a href='https://chunkytortoise.github.io/EnterpriseHub/' style='background: white; color: #0F172A; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; border: 1px solid #E2E8F0;'>View Portfolio</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    render()