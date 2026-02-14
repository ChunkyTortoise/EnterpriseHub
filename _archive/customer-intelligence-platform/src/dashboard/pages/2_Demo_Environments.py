
import streamlit as st

st.title("🎯 Demo Environments")
st.markdown("### Industry-Specific Demo Environments")

industries = {
    "Real Estate": {
        "customers": ["Premier Realty Group", "Rancho Cucamonga Metro Realty", "Texas Property Partners"],
        "features": ["Lead Scoring", "Property Matching", "Agent Analytics"],
        "roi": "3,500%"
    },
    "SaaS": {
        "customers": ["CloudTech Solutions", "ScaleUp Systems", "DataFlow Inc"], 
        "features": ["Pipeline Forecasting", "Churn Prediction", "Revenue Analytics"],
        "roi": "11,400%"
    },
    "E-commerce": {
        "customers": ["Fashion Forward", "SportsTech Store", "HomeStyle Direct"],
        "features": ["Personalization", "Cart Recovery", "Customer Journey"],
        "roi": "12,400%"
    },
    "Financial Services": {
        "customers": ["Wealth Advisors Inc", "Premier Financial", "Investment Partners"],
        "features": ["Risk Assessment", "Compliance", "Portfolio Optimization"],
        "roi": "13,500%"
    }
}

for industry, data in industries.items():
    with st.expander(f"🏢 {industry}"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Demo Customers:**")
            for customer in data["customers"]:
                st.markdown(f"• {customer}")
        
        with col2:
            st.markdown("**Key Features:**")
            for feature in data["features"]:
                st.markdown(f"• {feature}")
        
        with col3:
            st.metric("Average ROI", data["roi"])
            if st.button(f"Launch {industry} Demo", key=industry):
                st.success(f"{industry} demo environment launched!")
