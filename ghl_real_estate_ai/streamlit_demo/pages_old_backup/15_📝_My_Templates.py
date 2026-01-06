"""
📝 My Templates
Manage your installed workflows and create custom templates
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.workflow_marketplace import WorkflowMarketplaceService
from services.template_installer import TemplateInstallerService
from services.template_manager import TemplateManagerService
from services.workflow_builder import WorkflowBuilderService

# Page config
st.set_page_config(
    page_title="My Templates",
    page_icon="📝",
    layout="wide"
)

# Initialize services
@st.cache_resource
def get_services():
    marketplace = WorkflowMarketplaceService()
    installer = TemplateInstallerService()
    manager = TemplateManagerService()
    builder = WorkflowBuilderService()
    return marketplace, installer, manager, builder

marketplace, installer, manager, builder = get_services()

# Session state
if 'tenant_id' not in st.session_state:
    st.session_state.tenant_id = "demo_user"

# Header
st.title("📝 My Templates")
st.markdown("Manage your installed workflows and create custom templates")

# Tabs
tab1, tab2, tab3 = st.tabs(["📥 Installed Templates", "➕ Create Template", "📦 Published Templates"])

# Tab 1: Installed Templates
with tab1:
    st.header("📥 Your Installed Templates")
    
    # Get installed templates
    installed = installer.get_installed_templates(st.session_state.tenant_id)
    
    if not installed:
        st.info("You haven't installed any templates yet. Visit the Marketplace to get started!")
        if st.button("🛒 Browse Marketplace", type="primary"):
            st.switch_page("pages/14_🛒_Workflow_Marketplace.py")
    else:
        st.success(f"You have {len(installed)} installed template(s)")
        
        # Display installed templates
        for template in installed:
            with st.expander(f"📋 {template['template_name']}", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Template ID:** `{template['template_id']}`")
                    st.markdown(f"**Workflow ID:** `{template['workflow_id']}`")
                    st.markdown(f"**Installed:** {template['installed_at'][:10]}")
                    if template.get('installation_count', 1) > 1:
                        st.markdown(f"**Times Installed:** {template['installation_count']}")
                
                with col2:
                    if st.button("🗑️ Uninstall", key=f"uninstall_{template['workflow_id']}"):
                        if installer.uninstall_workflow(template['workflow_id']):
                            st.success("Template uninstalled!")
                            st.rerun()
                        else:
                            st.error("Failed to uninstall")
    
    # Installation statistics
    st.divider()
    st.subheader("📊 Installation Statistics")
    
    stats = installer.get_installation_stats()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Installations", stats['total_installations'])
    with col2:
        st.metric("Unique Templates", stats['unique_templates'])
    with col3:
        st.metric("Most Installed", 
                 stats['most_installed'][0]['template_id'][:10] + "..." if stats['most_installed'] else "N/A")

# Tab 2: Create Template
with tab2:
    st.header("➕ Create Custom Template")
    st.markdown("Export an existing workflow as a template or create a new one from scratch")
    
    # Choose creation method
    creation_method = st.radio(
        "How would you like to create your template?",
        ["Export Existing Workflow", "Create from Scratch"]
    )
    
    if creation_method == "Export Existing Workflow":
        st.subheader("Export Workflow as Template")
        
        # Get available workflows
        workflows = builder.list_workflows()
        
        if not workflows:
            st.warning("No workflows found. Create a workflow first in the Workflow Builder.")
        else:
            workflow_options = {f"{w.name} (ID: {w.workflow_id[:8]}...)": w for w in workflows}
            selected_workflow_name = st.selectbox(
                "Select Workflow to Export",
                list(workflow_options.keys())
            )
            
            if selected_workflow_name:
                workflow = workflow_options[selected_workflow_name]
                
                with st.form("export_workflow_form"):
                    st.markdown("### Template Details")
                    
                    template_name = st.text_input(
                        "Template Name",
                        value=workflow.name,
                        help="Give your template a descriptive name"
                    )
                    
                    template_description = st.text_area(
                        "Description",
                        value=workflow.description,
                        help="Describe what this template does and when to use it"
                    )
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        category = st.selectbox(
                            "Category",
                            ["lead_nurturing", "re_engagement", "appointments", 
                             "transactions", "relationship", "education", "events", "luxury", "custom"]
                        )
                        
                        difficulty = st.selectbox(
                            "Difficulty Level",
                            ["beginner", "intermediate", "advanced"]
                        )
                    
                    with col2:
                        icon = st.text_input("Icon (emoji)", value="📋")
                        estimated_time = st.text_input("Estimated Setup Time", value="5 minutes")
                    
                    tags = st.text_input(
                        "Tags (comma-separated)",
                        placeholder="automation, welcome, leads",
                        help="Add tags to help others find your template"
                    )
                    
                    documentation = st.text_area(
                        "Documentation (Markdown)",
                        placeholder="# How to Use\n\nThis template...",
                        help="Provide detailed instructions for using this template"
                    )
                    
                    visibility = st.radio(
                        "Visibility",
                        ["Private (only you)", "Public (marketplace)"]
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        submit = st.form_submit_button("✅ Create Template", type="primary", use_container_width=True)
                    with col2:
                        cancel = st.form_submit_button("❌ Cancel", use_container_width=True)
                    
                    if submit:
                        try:
                            # Convert workflow to dict
                            workflow_dict = {
                                "workflow_id": workflow.workflow_id,
                                "name": workflow.name,
                                "description": workflow.description,
                                "trigger": workflow.trigger.__dict__,
                                "actions": [
                                    {
                                        "action_id": a.action_id,
                                        "action_type": a.action_type,
                                        "config": a.config,
                                        "conditions": [c.__dict__ for c in a.conditions],
                                        "next_action_id": a.next_action_id,
                                        "delay_seconds": a.delay_seconds
                                    }
                                    for a in workflow.actions
                                ]
                            }
                            
                            # Export as template
                            template = manager.export_workflow_as_template(
                                workflow_dict,
                                metadata={
                                    "name": template_name,
                                    "description": template_description,
                                    "category": category,
                                    "difficulty": difficulty,
                                    "icon": icon,
                                    "estimated_time": estimated_time,
                                    "tags": [t.strip() for t in tags.split(",") if t.strip()],
                                    "documentation": documentation
                                }
                            )
                            
                            # Validate
                            validation = manager.validate_template(template)
                            
                            if not validation.is_valid:
                                st.error(f"Validation errors: {', '.join(validation.errors)}")
                            else:
                                # Publish
                                vis = "public" if "Public" in visibility else "private"
                                published = manager.publish_template(template, visibility=vis)
                                
                                st.success(f"✅ Template created: {published['name']}")
                                st.balloons()
                                
                                # Show validation warnings if any
                                if validation.warnings:
                                    st.warning(f"Warnings: {', '.join(validation.warnings)}")
                        
                        except Exception as e:
                            st.error(f"Failed to create template: {str(e)}")
    
    else:  # Create from Scratch
        st.info("🚧 Create from Scratch feature coming soon! For now, create a workflow in the Workflow Builder first, then export it as a template.")

# Tab 3: Published Templates
with tab3:
    st.header("📦 Your Published Templates")
    
    my_templates = manager.get_my_templates()
    
    if not my_templates:
        st.info("You haven't published any templates yet. Create your first template in the 'Create Template' tab!")
    else:
        st.success(f"You have {len(my_templates)} published template(s)")
        
        for template in my_templates:
            with st.expander(f"{template['icon']} {template['name']}", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(template['description'])
                    st.markdown(f"**Category:** {template['category'].replace('_', ' ').title()}")
                    st.markdown(f"**Version:** {template['version']}")
                    st.markdown(f"**Created:** {template['created_at'][:10]}")
                    
                    if template.get('variables'):
                        st.markdown(f"**Variables:** {len(template['variables'])}")
                    
                    tags_display = ", ".join(template.get('tags', []))
                    if tags_display:
                        st.markdown(f"**Tags:** {tags_display}")
                
                with col2:
                    if st.button("✏️ Edit", key=f"edit_{template['id']}"):
                        st.info("Edit functionality coming soon!")
                    
                    if st.button("🗑️ Delete", key=f"delete_{template['id']}"):
                        if manager.delete_template(template['id']):
                            st.success("Template deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete")

# Footer
st.divider()
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>📝 <strong>My Templates</strong> | 
    Build and share your automation library | 
    <a href='#'>Help</a> • 
    <a href='#'>Documentation</a></p>
</div>
""", unsafe_allow_html=True)
