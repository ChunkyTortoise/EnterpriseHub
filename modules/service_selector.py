"""
Service Selector Module
Interactive AI Strategy Planner to recommend the right services from the 31-service catalog.
"""
import streamlit as st
import utils.ui as ui

# Categorized Services from the Catalog
SERVICES = {
    "Strategic": {
        "S1": {"title": "AI Strategy & Readiness", "roi": "Prevents $50k-$200k misallocated spend", "investment": "$6,400+"},
        "S2": {"title": "Technical Due Diligence", "roi": "Identifies $50k-$300k hidden costs", "investment": "$8,000+"},
        "S25": {"title": "Fractional AI Leadership", "roi": "119% 12-month ROI", "investment": "$8,000/mo"},
        "S23": {"title": "AI Compliance (HIPAA/SOC2)", "roi": "Mitigates $200k-$2M risk", "investment": "$4,000+"}
    },
    "Automation": {
        "S3": {"title": "Custom RAG Agents", "roi": "60% reduction in support load", "investment": "$3,600+"},
        "S4": {"title": "Multi-Agent Swarms", "roi": "10,000%+ ROI (Lead Research)", "investment": "$5,200+"},
        "S6": {"title": "Business Automation (Zapier/n8n)", "roi": "15-20 hours saved weekly", "investment": "$1,400+"},
        "S12": {"title": "Programmatic SEO Engine", "roi": "17,000%+ 12-month ROI", "investment": "$4,400+"}
    },
    "Data & BI": {
        "S8": {"title": "Interactive BI Dashboards", "roi": "8,000% ROI (Churn Reduction)", "investment": "$3,200+"},
        "S9": {"title": "Automated Reporting", "roi": "19 hours saved weekly", "investment": "$2,200+"},
        "S10": {"title": "Predictive Lead Scoring", "roi": "8,000% ROI (Sales focus)", "investment": "$4,400+"},
        "S11": {"title": "Data Rescue (Cleanup)", "roi": "800% ROI (Data accuracy)", "investment": "$960+"}
    }
}

def render():
    """Main render function for the Service Selector."""
    # Note: Header is rendered by app.py load_and_render_module
    
    tabs = st.tabs(["🎯 Strategy Diagnostic", "💰 Fixed-Price Catalog", "🎓 Credentials"])
    
    with tabs[0]:
        _render_diagnostic()
        
    with tabs[1]:
        _render_catalog()

    with tabs[2]:
        ui.credential_inventory()

def _render_diagnostic():
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 🔍 Business Diagnostic")
        st.write("Answer a few questions to receive a tailored implementation roadmap.")
        
        industry = st.selectbox("Industry Vertical", ["B2B SaaS", "E-commerce", "Healthcare", "Professional Services", "Real Estate", "Manufacturing"])
        
        challenge = st.multiselect(
            "Primary Challenges (Select all that apply)",
            [
                "Manual processes consuming team time",
                "Poor data visibility / decision-making",
                "Growth / Customer acquisition issues",
                "Legacy systems / Fragile Excel sheets",
                "Regulatory / Compliance concerns (HIPAA/SOC2)",
                "Need high-level AI strategy guidance"
            ]
        )
        
        budget = st.select_slider(
            "Available Budget Range",
            options=["Under $2k", "$2k - $10k", "$10k - $25k", "$25k+"]
        )
        
        st.divider()
        if st.button("Generate Strategy Roadmap", type="primary"):
            _generate_roadmap(industry, challenge, budget)
    
    with col2:
        st.markdown("#### 💡 Recommended Architecture")
        if "recommended_services_v2" in st.session_state:
            for svc_code in st.session_state.recommended_services_v2:
                # Find service in categories
                found = False
                for cat, svcs in SERVICES.items():
                    if svc_code in svcs:
                        svc = svcs[svc_code]
                        ui.use_case_card(
                            icon="✅",
                            title=svc["title"],
                            description=f"<strong>{svc_code}</strong><br>Target ROI: {svc['roi']}<br>Starting at: {svc['investment']}"
                        )
                        st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
                        found = True
                if not found:
                    st.write(f"Ref: {svc_code}")
        else:
            st.info("Complete the diagnostic on the left to see your recommended AI architecture.")

def _render_catalog():
    st.markdown("### 📋 2026 Professional Services Catalog")
    st.write("Fixed-price transparency eliminating hourly billing uncertainty. 30-day money-back guarantee.")
    
    for category, items in SERVICES.items():
        with st.expander(f"**{category} Services**", expanded=True):
            cols = st.columns(2)
            item_list = list(items.items())
            for i in range(0, len(item_list), 2):
                with cols[0]:
                    code, svc = item_list[i]
                    st.markdown(f"**{code}: {svc['title']}**")
                    st.markdown(f"*ROI: {svc['roi']}*")
                    st.markdown(f"**Investment: {svc['investment']}**")
                    st.divider()
                if i + 1 < len(item_list):
                    with cols[1]:
                        code, svc = item_list[i+1]
                        st.markdown(f"**{code}: {svc['title']}**")
                        st.markdown(f"*ROI: {svc['roi']}*")
                        st.markdown(f"**Investment: {svc['investment']}**")
                        st.divider()

def _generate_roadmap(industry, challenges, budget):
    """Determine recommended services based on catalog logic."""
    recs = []
    
    # Challenge-based logic
    if "Manual processes consuming team time" in challenges:
        recs.extend(["S3", "S4", "S6"])
    if "Poor data visibility / decision-making" in challenges:
        recs.extend(["S8", "S9", "S10"])
    if "Growth / Customer acquisition issues" in challenges:
        recs.extend(["S12", "S10"])
    if "Regulatory / Compliance concerns (HIPAA/SOC2)" in challenges:
        recs.append("S23")
    if "Need high-level AI strategy guidance" in challenges:
        recs.append("S1")

    # Budget filtering (Simple)
    if budget == "Under $2k":
        recs = [r for r in recs if r in ["S6", "S11"]] # Automation or cleanup
    elif budget == "$2k - $10k":
        recs = [r for r in recs if r not in ["S2", "S25"]]
        
    # Deduplicate and limit
    recs = list(dict.fromkeys(recs))[:4]
    if not recs: recs = ["S1"] # Default to strategy
    
    st.session_state.recommended_services_v2 = recs
    st.success("Strategy Roadmap Generated!")