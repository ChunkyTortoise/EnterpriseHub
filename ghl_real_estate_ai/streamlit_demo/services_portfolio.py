"""
Services Portfolio - Professional Services Showcase
Displays 31 services with filtering, pricing, and ROI models
"""

from typing import Dict, List

import streamlit as st

from ghl_real_estate_ai.streamlit_demo.data.services_data import (
    CATEGORIES,
    DIFFERENTIATORS,
    INDUSTRIES,
    SERVICES,
)


def render_services_portfolio():
    """Render the services portfolio page."""
    st.set_page_config(page_title="Services Portfolio", page_icon="💼", layout="wide")
    
    # Header
    st.markdown("# 💼 Professional Services Portfolio")
    st.markdown("### Production-Grade AI Systems and Data Infrastructure That Generate Measurable Business Outcomes")
    st.markdown("---")
    
    # Core differentiators banner
    render_differentiators()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        category_filter = st.selectbox(
            "Category",
            ["All Categories"] + list(CATEGORIES.keys()),
            key="category_filter"
        )
    
    with col2:
        industry_filter = st.selectbox(
            "Industry",
            ["All Industries"] + INDUSTRIES,
            key="industry_filter"
        )
    
    with col3:
        price_filter = st.selectbox(
            "Price Range",
            ["All Prices", "Under $2,000", "$2,000-$5,000", "$5,000-$10,000", "$10,000+"],
            key="price_filter"
        )
    
    with col4:
        timeline_filter = st.selectbox(
            "Timeline",
            ["All Timelines", "1-2 days", "3-5 days", "5-10 days", "10+ days"],
            key="timeline_filter"
        )
    
    st.markdown("---")
    
    # Filter services
    filtered_services = filter_services(
        category_filter, industry_filter, price_filter, timeline_filter
    )
    
    # Display service count
    st.markdown(f"### Showing {len(filtered_services)} Services")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Display services in grid
    render_services_grid(filtered_services)
    
    # Footer CTA
    st.markdown("---")
    render_footer_cta()


def render_differentiators():
    """Render core differentiators banner."""
    st.markdown(
        f"""
        <div style='background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(16, 185, 129, 0.1) 100%); 
                    padding: 2rem; border-radius: 16px; border: 1px solid rgba(99, 102, 241, 0.2);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);'>
            <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1.5rem;'>
                <div style='text-align: center;'>
                    <div style='font-size: 2.5rem; font-weight: 800; color: #6366F1;'>{DIFFERENTIATORS["certifications"]}</div>
                    <div style='font-size: 0.9rem; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;'>Professional Certifications</div>
                </div>
                <div style='text-align: center;'>
                    <div style='font-size: 2.5rem; font-weight: 800; color: #10B981;'>{DIFFERENTIATORS["training_hours"]}</div>
                    <div style='font-size: 0.9rem; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;'>Hours Training</div>
                </div>
                <div style='text-align: center;'>
                    <div style='font-size: 2.5rem; font-weight: 800; color: #8B5CF6;'>{DIFFERENTIATORS["typical_tests_per_project"]}</div>
                    <div style='font-size: 0.9rem; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;'>Automated Tests/Project</div>
                </div>
                <div style='text-align: center;'>
                    <div style='font-size: 2.5rem; font-weight: 800; color: #F59E0B;'>{DIFFERENTIATORS["market_discount"]}</div>
                    <div style='font-size: 0.9rem; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;'>Below Market Rate</div>
                </div>
                <div style='text-align: center;'>
                    <div style='font-size: 2.5rem; font-weight: 800; color: #EF4444;'>{DIFFERENTIATORS["guarantee_days"]}</div>
                    <div style='font-size: 0.9rem; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;'>Day Guarantee</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def filter_services(category: str, industry: str, price: str, timeline: str) -> List[Dict]:
    """Filter services based on selected criteria."""
    filtered = []
    
    for service_id, service in SERVICES.items():
        # Category filter
        if category != "All Categories" and service["category"] != category:
            continue
        
        # Industry filter
        if industry != "All Industries" and industry not in service.get("industries", []):
            continue
        
        # Price filter
        if price != "All Prices":
            price_range = service["price_range"]
            if not matches_price_filter(price_range, price):
                continue
        
        # Timeline filter
        if timeline != "All Timelines":
            service_timeline = service["timeline"]
            if not matches_timeline_filter(service_timeline, timeline):
                continue
        
        filtered.append(service)
    
    return filtered


def matches_price_filter(price_range: str, price_filter: str) -> bool:
    """Check if price range matches filter."""
    # Extract min price from range (e.g., "$3,600-$5,200" -> 3600)
    min_price = int(price_range.split("-")[0].replace("$", "").replace(",", "").replace("/month", ""))
    
    if price_filter == "Under $2,000":
        return min_price < 2000
    elif price_filter == "$2,000-$5,000":
        return 2000 <= min_price < 5000
    elif price_filter == "$5,000-$10,000":
        return 5000 <= min_price < 10000
    elif price_filter == "$10,000+":
        return min_price >= 10000
    
    return True


def matches_timeline_filter(service_timeline: str, timeline_filter: str) -> bool:
    """Check if service timeline matches filter."""
    # Extract max days from timeline (e.g., "3-5 business days" -> 5)
    parts = service_timeline.split()
    if "-" in parts[0]:
        max_days = int(parts[0].split("-")[1])
    else:
        max_days = int(parts[0])
    
    if timeline_filter == "1-2 days":
        return max_days <= 2
    elif timeline_filter == "3-5 days":
        return 3 <= max_days <= 5
    elif timeline_filter == "5-10 days":
        return 5 <= max_days <= 10
    elif timeline_filter == "10+ days":
        return max_days >= 10
    
    return True


def render_services_grid(services: List[Dict]):
    """Render services in a responsive grid."""
    # Display 2 services per row
    for i in range(0, len(services), 2):
        cols = st.columns(2)
        
        for j, col in enumerate(cols):
            if i + j < len(services):
                with col:
                    render_service_card(services[i + j])


def render_service_card(service: Dict):
    """Render individual service card."""
    # Category color mapping
    category_colors = {
        "Strategic Services": "#6366F1",
        "AI Intelligent Automation": "#10B981",
        "Business Intelligence": "#8B5CF6",
        "Marketing & Growth": "#F59E0B",
        "Infrastructure & Operations": "#3B82F6",
        "Consulting & Advisory": "#EC4899",
    }
    
    category_color = category_colors.get(service["category"], "#64748B")
    
    st.markdown(
        f"""
        <div style='background: white; padding: 1.5rem; border-radius: 12px; 
                    border: 1px solid #E2E8F0; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
                    height: 100%; display: flex; flex-direction: column;'>
            <div style='background: {category_color}; color: white; 
                        padding: 0.5rem 1rem; border-radius: 6px; 
                        font-size: 0.75rem; font-weight: 700; text-transform: uppercase; 
                        letter-spacing: 0.05em; display: inline-block; margin-bottom: 1rem;'>
                {service["category"]}
            </div>
            <h3 style='color: #1E293B; margin: 0.5rem 0; font-size: 1.25rem;'>{service["title"]}</h3>
            <p style='color: #64748B; font-size: 0.9rem; font-style: italic; margin-bottom: 1rem;'>{service["tagline"]}</p>
            <p style='color: #475569; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1rem;'>{service["description"]}</p>
            
            <div style='margin-top: auto;'>
                <div style='background: #F8FAFC; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;'>
                    <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;'>
                        <div>
                            <div style='color: #64748B; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;'>Investment</div>
                            <div style='color: #10B981; font-size: 1.1rem; font-weight: 700;'>{service["price_range"]}</div>
                        </div>
                        <div>
                            <div style='color: #64748B; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;'>Timeline</div>
                            <div style='color: #6366F1; font-size: 1.1rem; font-weight: 700;'>{service["timeline"]}</div>
                        </div>
                    </div>
                </div>
                
                <div style='background: #FEF3C7; border-left: 4px solid #F59E0B; padding: 0.75rem; border-radius: 6px; margin-bottom: 1rem;'>
                    <div style='color: #92400E; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; margin-bottom: 0.25rem;'>ROI Example</div>
                    <div style='color: #78350F; font-size: 0.85rem; line-height: 1.5;'>{service["roi_example"]}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Expandable details
    with st.expander("View Details"):
        st.markdown("**Key Benefits:**")
        for benefit in service["key_benefits"]:
            st.markdown(f"- {benefit}")
        
        st.markdown("**Industries:**")
        st.markdown(", ".join(service.get("industries", [])))
        
        st.markdown("**Relevant Certifications:**")
        for cert in service.get("certifications", []):
            st.markdown(f"- {cert}")
    
    # CTA buttons
    col1, col2 = st.columns(2)
    with col1:
        st.button("Request Quote", key=f"quote_{service['title']}", use_container_width=True)
    with col2:
        st.button("Schedule Consultation", key=f"consult_{service['title']}", use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)


def render_footer_cta():
    """Render footer call-to-action."""
    st.markdown(
        """
        <div style='background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%); 
                    padding: 3rem; border-radius: 16px; text-align: center; color: white;'>
            <h2 style='color: white; margin-bottom: 1rem;'>Ready to Transform Your Business?</h2>
            <p style='font-size: 1.1rem; margin-bottom: 2rem; opacity: 0.9;'>
                Get a free consultation to discuss which services fit your needs.
            </p>
            <div style='display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;'>
                <div style='background: white; color: #6366F1; padding: 1rem 2rem; 
                            border-radius: 8px; font-weight: 700; cursor: pointer;'>
                    Schedule Free Consultation
                </div>
                <div style='background: rgba(255, 255, 255, 0.2); color: white; 
                            padding: 1rem 2rem; border-radius: 8px; font-weight: 700; 
                            cursor: pointer; border: 2px solid white;'>
                    View Case Studies
                </div>
            </div>
            <div style='margin-top: 2rem; padding-top: 2rem; border-top: 1px solid rgba(255, 255, 255, 0.2);'>
                <p style='font-size: 0.9rem; opacity: 0.8; margin: 0;'>
                    📧 caymanroden@gmail.com | 🔗 LinkedIn | 💼 Portfolio
                </p>
                <p style='font-size: 0.85rem; opacity: 0.7; margin-top: 0.5rem;'>
                    30-Day Money-Back Guarantee | Fixed-Price Transparency | 19 Professional Certifications
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    render_services_portfolio()
