"""
One-Click Property Launch Demo - Agent 4: Automation Genius
Demo page for multi-platform property listing automation
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.one_click_property_launch import OneClickPropertyLaunch, Platform, ListingStatus

# Page config
st.set_page_config(
    page_title="One-Click Property Launch",
    page_icon="🚀",
    layout="wide"
)

# Initialize service
if 'property_launch_service' not in st.session_state:
    st.session_state.property_launch_service = OneClickPropertyLaunch()

# Header
st.title("🚀 One-Click Property Launch")
st.markdown("### Publish to 10+ platforms instantly with auto-generated materials")

# Metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Time Saved", "4-6 hrs/listing")
with col2:
    st.metric("Platforms", "10+")
with col3:
    st.metric("Revenue Impact", "+$40K-50K/yr")
with col4:
    st.metric("Sync Status", "Real-time")

st.divider()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📝 Create Listing", "🌐 Platform Status", "📊 Analytics", "⚙️ Settings"])

with tab1:
    st.subheader("Create New Listing Package")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Property Details**")
        address = st.text_input("Property Address", "123 Main St")
        city = st.text_input("City", "Austin")
        state = st.text_input("State", "TX")
        zipcode = st.text_input("ZIP Code", "78701")
        
        price = st.number_input("List Price", min_value=0, value=450000, step=5000)
        bedrooms = st.number_input("Bedrooms", min_value=0, max_value=10, value=3)
        bathrooms = st.number_input("Bathrooms", min_value=0, max_value=10, value=2)
        sqft = st.number_input("Square Feet", min_value=0, value=1800, step=50)
    
    with col2:
        st.markdown("**Listing Options**")
        property_type = st.selectbox("Property Type", ["Single Family", "Condo", "Townhouse", "Multi-Family"])
        year_built = st.number_input("Year Built", min_value=1800, max_value=2026, value=2015)
        
        st.markdown("**Photos**")
        num_photos = st.number_input("Number of Photos", min_value=1, max_value=50, value=10)
        has_virtual_tour = st.checkbox("Has Virtual Tour", value=True)
        has_video = st.checkbox("Has Video Walkthrough", value=False)
        
        st.markdown("**Features**")
        features = st.multiselect(
            "Property Features",
            ["Hardwood Floors", "Granite Counters", "Updated Kitchen", "Pool", "2-Car Garage"],
            default=["Hardwood Floors", "Updated Kitchen"]
        )
    
    st.markdown("**Select Platforms**")
    platform_cols = st.columns(5)
    selected_platforms = []
    
    platform_options = {
        "MLS": Platform.MLS,
        "Zillow": Platform.ZILLOW,
        "Realtor.com": Platform.REALTOR_COM,
        "Redfin": Platform.REDFIN,
        "Trulia": Platform.TRULIA,
        "Facebook": Platform.FACEBOOK_MARKETPLACE,
        "Instagram": Platform.INSTAGRAM,
        "Website": Platform.COMPANY_WEBSITE,
        "OpenDoor": Platform.OPEN_DOOR,
        "OfferPad": Platform.OFFERPAD
    }
    
    for i, (name, platform) in enumerate(platform_options.items()):
        with platform_cols[i % 5]:
            if st.checkbox(name, value=(i < 4)):
                selected_platforms.append(platform)
    
    col1, col2, col3 = st.columns(3)
    with col2:
        if st.button("🚀 Create & Publish Listing", type="primary", use_container_width=True):
            with st.spinner("Creating listing package..."):
                # Create property data
                property_data = {
                    "id": f"prop_{int(st.session_state.get('demo_counter', 0))}",
                    "address": address,
                    "city": city,
                    "state": state,
                    "zip": zipcode,
                    "price": price,
                    "bedrooms": bedrooms,
                    "bathrooms": bathrooms,
                    "square_feet": sqft,
                    "property_type": property_type,
                    "year_built": year_built,
                    "photos": [f"https://example.com/photo{i}.jpg" for i in range(num_photos)],
                    "features": features
                }
                
                # Create package
                package = st.session_state.property_launch_service.create_listing_package(property_data)
                
                # Publish
                results = st.session_state.property_launch_service.publish_to_platforms(
                    package,
                    selected_platforms
                )
                
                st.session_state.last_publish = results
                st.session_state.demo_counter = st.session_state.get('demo_counter', 0) + 1
                
                st.success(f"✅ Published to {results['summary']['successful']}/{results['summary']['total']} platforms!")
                
                # Show results
                st.markdown("**Publication Results:**")
                for platform, result in results['platforms'].items():
                    if result['status'] == 'published':
                        st.success(f"✅ {platform.upper()}: {result['url']}")
                    else:
                        st.error(f"❌ {platform.upper()}: Failed")

with tab2:
    st.subheader("Platform Status & Performance")
    
    if 'last_publish' in st.session_state:
        property_id = st.session_state.last_publish['property_id']
        
        # Get status
        status = st.session_state.property_launch_service.get_listing_status(property_id)
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Views", f"{status['aggregated_metrics']['total_views']:,}")
        with col2:
            st.metric("Total Leads", status['aggregated_metrics']['total_leads'])
        with col3:
            st.metric("Total Inquiries", status['aggregated_metrics']['total_inquiries'])
        with col4:
            st.metric("Avg Engagement", f"{status['aggregated_metrics']['avg_engagement_rate']:.1%}")
        
        st.divider()
        
        # Platform details
        st.markdown("**Platform Performance**")
        for platform, platform_status in status['platforms'].items():
            with st.expander(f"📍 {platform.upper()} - {platform_status.get('status', 'unknown').upper()}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Views", platform_status.get('views', 0))
                with col2:
                    st.metric("Leads", platform_status.get('leads', 0))
                with col3:
                    st.metric("Engagement", f"{platform_status.get('engagement_rate', 0):.1%}")
    else:
        st.info("👆 Create and publish a listing first to see platform status")

with tab3:
    st.subheader("Listing Analytics")
    
    # Sample analytics
    import pandas as pd
    import plotly.express as px
    
    # Views over time
    views_data = pd.DataFrame({
        'Date': pd.date_range('2026-01-01', periods=7, freq='D'),
        'Views': [45, 67, 89, 123, 145, 167, 189]
    })
    
    fig = px.line(views_data, x='Date', y='Views', title='Views Over Time')
    st.plotly_chart(fig, use_container_width=True)
    
    # Platform comparison
    col1, col2 = st.columns(2)
    
    with col1:
        platform_views = pd.DataFrame({
            'Platform': ['MLS', 'Zillow', 'Realtor.com', 'Facebook'],
            'Views': [150, 120, 95, 85]
        })
        fig = px.bar(platform_views, x='Platform', y='Views', title='Views by Platform')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        platform_leads = pd.DataFrame({
            'Platform': ['MLS', 'Zillow', 'Realtor.com', 'Facebook'],
            'Leads': [12, 8, 6, 4]
        })
        fig = px.pie(platform_leads, values='Leads', names='Platform', title='Leads by Platform')
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("Platform Settings")
    
    st.markdown("**API Credentials**")
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("MLS API Key", type="password", value="••••••••")
        st.text_input("Zillow API Key", type="password", value="••••••••")
        st.text_input("Realtor.com API Key", type="password", value="••••••••")
    
    with col2:
        st.text_input("DocuSign API Key", type="password", value="••••••••")
        st.text_input("Facebook Access Token", type="password", value="••••••••")
        st.text_input("Instagram API Key", type="password", value="••••••••")
    
    st.divider()
    
    st.markdown("**Default Settings**")
    st.checkbox("Auto-publish to all platforms", value=True)
    st.checkbox("Auto-sync price changes", value=True)
    st.checkbox("Send notification on new leads", value=True)
    
    if st.button("💾 Save Settings"):
        st.success("Settings saved!")

# Footer
st.divider()
st.markdown("""
**💡 Pro Tips:**
- Upload high-quality photos for better engagement
- Use virtual tours to increase views by 40%
- Cross-post to social media for maximum reach
- Monitor platform performance and optimize accordingly
""")
