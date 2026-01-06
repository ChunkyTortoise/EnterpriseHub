"""
🛒 Workflow Marketplace
Browse, search, and install pre-built workflow templates
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.workflow_marketplace import WorkflowMarketplaceService, TemplateSortBy
from services.template_installer import TemplateInstallerService
from services.template_manager import TemplateManagerService


# Page config
st.set_page_config(
    page_title="Workflow Marketplace",
    page_icon="🛒",
    layout="wide"
)

# Initialize services
@st.cache_resource
def get_services():
    marketplace = WorkflowMarketplaceService()
    installer = TemplateInstallerService()
    manager = TemplateManagerService()
    return marketplace, installer, manager

marketplace, installer, manager = get_services()

# Session state
if 'selected_template' not in st.session_state:
    st.session_state.selected_template = None
if 'show_install_modal' not in st.session_state:
    st.session_state.show_install_modal = False
if 'tenant_id' not in st.session_state:
    st.session_state.tenant_id = "demo_user"  # In production, get from auth

# Header
st.title("🛒 Workflow Marketplace")
st.markdown("Browse and install pre-built workflow templates to automate your real estate business")

# Get marketplace stats
stats = marketplace.get_stats()

# Top metrics
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("📦 Total Templates", stats['total_templates'])
with col2:
    st.metric("🆓 Free", stats['free_templates'])
with col3:
    st.metric("💎 Premium", stats['premium_templates'])
with col4:
    st.metric("⭐ Avg Rating", f"{stats['average_rating']:.1f}")
with col5:
    st.metric("📥 Downloads", f"{stats['total_downloads']:,}")

st.divider()

# Sidebar filters
with st.sidebar:
    st.header("🔍 Filters")
    
    # Search
    search_query = st.text_input("🔎 Search templates", placeholder="e.g., appointment, welcome...")
    
    # Category filter
    categories = marketplace.get_categories()
    category_options = ["All Categories"] + [f"{cat['icon']} {cat['name']}" for cat in categories]
    selected_category = st.selectbox("📂 Category", category_options)
    
    # Price filter
    price_filter = st.radio(
        "💰 Price",
        ["All", "Free Only", "Premium Only"]
    )
    
    # Rating filter
    min_rating = st.slider("⭐ Minimum Rating", 0.0, 5.0, 0.0, 0.5)
    
    # Difficulty filter
    difficulty_filter = st.selectbox(
        "📊 Difficulty",
        ["All", "Beginner", "Intermediate", "Advanced"]
    )
    
    # Sort options
    sort_by = st.selectbox(
        "🔽 Sort By",
        ["Popular", "Trending", "Highest Rated", "Newest", "Name"]
    )
    
    st.divider()
    
    # Quick links
    st.markdown("### 🔗 Quick Links")
    if st.button("⭐ Featured Templates", use_container_width=True):
        st.session_state.filter_featured = True
    if st.button("📱 My Installed", use_container_width=True):
        st.session_state.show_my_templates = True
    if st.button("➕ Create Template", use_container_width=True):
        st.session_state.show_create_template = True

# Parse filters
category_id = None
if selected_category != "All Categories":
    # Extract category ID from selection
    for cat in categories:
        if f"{cat['icon']} {cat['name']}" == selected_category:
            category_id = cat['id']
            break

max_price = None
if price_filter == "Free Only":
    max_price = 0
elif price_filter == "Premium Only":
    max_price = 999999
    min_rating = 0  # Show all premium

difficulty = None if difficulty_filter == "All" else difficulty_filter.lower()

# Map sort option to enum
sort_map = {
    "Popular": TemplateSortBy.POPULAR.value,
    "Trending": TemplateSortBy.TRENDING.value,
    "Highest Rated": TemplateSortBy.RATING.value,
    "Newest": TemplateSortBy.NEWEST.value,
    "Name": TemplateSortBy.NAME.value
}
sort_value = sort_map[sort_by]

# Browse templates with filters
templates = marketplace.browse_templates(
    category=category_id,
    search_query=search_query if search_query else None,
    min_rating=min_rating,
    max_price=max_price,
    difficulty=difficulty,
    sort_by=sort_value,
    limit=50
)

# Special filters
if price_filter == "Premium Only":
    templates = [t for t in templates if t.is_premium]

# Results header
st.markdown(f"### 📋 Templates ({len(templates)} found)")

if len(templates) == 0:
    st.info("No templates found matching your filters. Try adjusting your search criteria.")
else:
    # Display templates in grid
    cols_per_row = 3
    
    for i in range(0, len(templates), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j, col in enumerate(cols):
            if i + j < len(templates):
                template = templates[i + j]
                
                with col:
                    # Template card
                    with st.container():
                        st.markdown(f"### {template.icon} {template.name}")
                        
                        # Badge row
                        badge_cols = st.columns([1, 1, 1])
                        with badge_cols[0]:
                            if template.is_premium:
                                st.markdown(f"💎 **${template.price}**")
                            else:
                                st.markdown("🆓 **FREE**")
                        with badge_cols[1]:
                            st.markdown(f"⭐ **{template.rating}** ({template.reviews_count})")
                        with badge_cols[2]:
                            st.markdown(f"📥 **{template.downloads_count:,}**")
                        
                        # Description
                        st.markdown(template.description[:120] + "..." if len(template.description) > 120 else template.description)
                        
                        # Tags
                        tags_html = " ".join([f'<span style="background-color: #f0f2f6; padding: 2px 8px; border-radius: 10px; font-size: 12px; margin-right: 4px;">{tag}</span>' for tag in template.tags[:3]])
                        st.markdown(tags_html, unsafe_allow_html=True)
                        
                        st.markdown("")  # Spacing
                        
                        # Metadata
                        meta_cols = st.columns(3)
                        with meta_cols[0]:
                            st.caption(f"⏱️ {template.estimated_time}")
                        with meta_cols[1]:
                            st.caption(f"📊 {template.difficulty.title()}")
                        with meta_cols[2]:
                            st.caption(f"🔢 {template.steps_count} steps")
                        
                        # Action buttons
                        btn_cols = st.columns([1, 1])
                        with btn_cols[0]:
                            if st.button("👁️ Details", key=f"details_{template.id}", use_container_width=True):
                                st.session_state.selected_template = template.id
                                st.rerun()
                        with btn_cols[1]:
                            if st.button("⚡ Install", key=f"install_{template.id}", use_container_width=True, type="primary"):
                                st.session_state.selected_template = template.id
                                st.session_state.show_install_modal = True
                                st.rerun()
                        
                        st.divider()

# Template details modal
if st.session_state.selected_template:
    template = marketplace.get_template_details(st.session_state.selected_template)
    
    if template:
        with st.expander(f"📄 Template Details: {template.name}", expanded=True):
            # Close button
            if st.button("❌ Close", key="close_details"):
                st.session_state.selected_template = None
                st.session_state.show_install_modal = False
                st.rerun()
            
            st.markdown(f"## {template.icon} {template.name}")
            
            # Metadata row
            meta_row = st.columns(5)
            with meta_row[0]:
                st.metric("Rating", f"{template.rating}⭐")
            with meta_row[1]:
                st.metric("Reviews", template.reviews_count)
            with meta_row[2]:
                st.metric("Downloads", f"{template.downloads_count:,}")
            with meta_row[3]:
                st.metric("Steps", template.steps_count)
            with meta_row[4]:
                price_display = "FREE" if template.price == 0 else f"${template.price}"
                st.metric("Price", price_display)
            
            # Description
            st.markdown("### 📝 Description")
            st.markdown(template.description)
            
            # Documentation
            if template.documentation:
                st.markdown("### 📚 Documentation")
                st.markdown(template.documentation)
            
            # Template info
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### ℹ️ Template Info")
                st.markdown(f"**Category:** {template.category.replace('_', ' ').title()}")
                st.markdown(f"**Trigger:** {template.trigger.replace('_', ' ').title()}")
                st.markdown(f"**Difficulty:** {template.difficulty.title()}")
                st.markdown(f"**Estimated Time:** {template.estimated_time}")
                st.markdown(f"**Version:** {template.version}")
                st.markdown(f"**Author:** {template.author}")
            
            with col2:
                st.markdown("### 🏷️ Tags")
                tags_display = ", ".join(template.tags)
                st.markdown(tags_display)
                
                if template.variables:
                    st.markdown("### ⚙️ Customizable Variables")
                    for var in template.variables:
                        st.markdown(f"- **{var['name']}** ({var['type']}): {var.get('description', 'No description')}")
            
            # Similar templates
            st.markdown("### 🔗 Similar Templates")
            similar = marketplace.get_similar_templates(template.id, limit=3)
            if similar:
                sim_cols = st.columns(len(similar))
                for idx, sim_template in enumerate(similar):
                    with sim_cols[idx]:
                        st.markdown(f"**{sim_template.icon} {sim_template.name}**")
                        st.caption(f"⭐ {sim_template.rating} | 📥 {sim_template.downloads_count:,}")
                        if st.button("View", key=f"similar_{sim_template.id}"):
                            st.session_state.selected_template = sim_template.id
                            st.rerun()
            
            # Reviews section
            st.markdown("### ⭐ Reviews")
            reviews = marketplace.get_template_reviews(template.id)
            
            if reviews:
                for review in reviews[:5]:  # Show first 5
                    st.markdown(f"**{review.rating}⭐** - {review.comment}")
                    st.caption(f"By {review.user_id} on {review.created_at[:10]}")
            else:
                st.info("No reviews yet. Be the first to review this template!")
            
            # Installation section
            if st.session_state.show_install_modal:
                st.markdown("---")
                st.markdown("### ⚡ Install Template")
                
                with st.form(key="install_form"):
                    workflow_name = st.text_input(
                        "Workflow Name",
                        value=template.name,
                        help="Give your workflow a custom name"
                    )
                    
                    # Show customizable variables
                    customizations = {}
                    if template.variables:
                        st.markdown("**Customize Variables:**")
                        for var in template.variables:
                            default_val = var.get('default', '')
                            customizations[var['name']] = st.text_input(
                                var['name'],
                                value=default_val if not default_val.startswith('{{') else '',
                                help=var.get('description', ''),
                                key=f"var_{var['name']}"
                            )
                    
                    enable_workflow = st.checkbox("Enable workflow immediately", value=True)
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        submit = st.form_submit_button("✅ Install Now", type="primary", use_container_width=True)
                    with col2:
                        cancel = st.form_submit_button("❌ Cancel", use_container_width=True)
                    
                    if submit:
                        try:
                            # Validate customizations
                            validation = installer.validate_customizations(template.__dict__, customizations)
                            
                            if validation['is_valid']:
                                # Install template
                                workflow = installer.install_template(
                                    template.__dict__,
                                    tenant_id=st.session_state.tenant_id,
                                    customizations=customizations,
                                    workflow_name=workflow_name,
                                    enabled=enable_workflow
                                )
                                
                                # Increment download count
                                marketplace.increment_downloads(template.id)
                                
                                st.success(f"✅ Successfully installed '{workflow_name}'!")
                                st.balloons()
                                
                                # Reset state
                                st.session_state.selected_template = None
                                st.session_state.show_install_modal = False
                                st.rerun()
                            else:
                                st.error(f"Validation failed: {', '.join(validation['errors'])}")
                        
                        except Exception as e:
                            st.error(f"Installation failed: {str(e)}")
                    
                    if cancel:
                        st.session_state.show_install_modal = False
                        st.rerun()

# Footer
st.divider()
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>🛒 <strong>Workflow Marketplace</strong> | 
    Build your automation library | 
    <a href='#'>Browse All</a> • 
    <a href='#'>Premium Templates</a> • 
    <a href='#'>Create Your Own</a></p>
</div>
""", unsafe_allow_html=True)
