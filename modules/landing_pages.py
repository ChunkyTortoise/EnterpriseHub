"""
Landing Pages Module
High-impact service landing page for EnterpriseHub.
"""
import streamlit as st
import utils.ui as ui

def render():
    st.markdown(
        """
        <div style='text-align: center; padding: 40px 0;'>
            <h1 style='font-size: 3.5rem; font-weight: 800;'>Production-Grade <span style='color: #10B981;'>AI Systems</span></h1>
            <p style='font-size: 1.2rem; color: #64748b;'>19 Certifications | 1,768 Training Hours | 31 Professional Services</p>
        </div>
        """, unsafe_allow_html=True
    )

    cols = st.columns(4)
    with cols[0]: ui.card_metric("Certifications", "19", "IBM, Google, Meta")
    with cols[1]: ui.card_metric("Training Hours", "1,768", "Advanced AI/Data")
    with cols[2]: ui.card_metric("Delivery", "2x Faster", "Full-Time Focus")
    with cols[3]: ui.card_metric("Pricing", "Fixed", "20% Below Market")

    ui.spacer(40)
    ui.credential_inventory()
    
    ui.spacer(60)
    ui.section_header("Vertical Industry Solutions", "Deeply integrated AI architectures")
    c1, c2 = st.columns(2)
    with c1:
        ui.use_case_card(icon="🚀", title="B2B SaaS", description="CAC reduction and churn prevention. **Service Bundle 2** recommended.")
        ui.use_case_card(icon="🛍️", title="E-commerce", description="Dynamic pricing and programmatic SEO. **Service Bundle 4** recommended.")
    with c2:
        ui.use_case_card(icon="🏥", title="Healthcare", description="HIPAA-compliant agents and clinical knowledge. **Service Bundle 5** recommended.")
        ui.use_case_card(icon="💼", title="Professional Services", description="Automated proposals and knowledge linking. **Service Bundle 3** recommended.")

    ui.spacer(60)
    st.markdown(
        """
        <div style='background: #F8FAFC; padding: 40px; border-radius: 20px; text-align: center; border: 1px solid #E2E8F0;'>
            <h2>Ready to Architect Your AI Future?</h2>
            <p>Explore the service modules in the sidebar or use the Strategy Planner to get started.</p>
            <a href='mailto:caymanroden@gmail.com' style='background: #0F172A; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;'>Book a Free Assessment</a>
        </div>
        """, unsafe_allow_html=True
    )

    # Virtual Consultant Integration
    from modules import virtual_consultant
    virtual_consultant.render()
