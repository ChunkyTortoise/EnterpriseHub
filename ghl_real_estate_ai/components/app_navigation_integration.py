"""
Smart Navigation Integration for Main App (Phase 1 Enhancement)

This module provides integration functions to add smart navigation
to the existing app.py without breaking current functionality.
"""

import streamlit as st
import sys
from pathlib import Path

# Add components to path
COMPONENTS_DIR = Path(__file__).parent
if str(COMPONENTS_DIR) not in sys.path:
    sys.path.insert(0, str(COMPONENTS_DIR))

from smart_navigation import (
    initialize_smart_navigation,
    get_current_navigation_context,
    render_smart_navigation,
    BreadcrumbComponent,
    ContextActionsComponent,
    ProgressiveDisclosureComponent
)


def enhance_app_with_smart_navigation():
    """
    Add smart navigation enhancements to the main app.

    Call this function at the beginning of your main app content area,
    after the sidebar but before the hub content.
    """

    # Initialize smart navigation service
    nav_service = initialize_smart_navigation()

    # Update navigation context based on current state
    current_hub = st.session_state.get("current_hub", "Executive Command Center")

    # Set current tab if we're in a tab context
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = None

    # Update session data for context awareness
    if 'session_data' not in st.session_state:
        st.session_state.session_data = {
            "recent_leads": [
                {"id": "lead_123", "name": "John Smith"},
                {"id": "lead_456", "name": "Sarah Johnson"}
            ],
            "pending_tasks": [
                {"id": "task_1", "title": "Follow up with hot leads"},
                {"id": "task_2", "title": "Update property listings"}
            ]
        }

    # Render smart navigation
    navigation_result = render_smart_navigation()

    # Handle navigation actions
    if navigation_result["action"]:
        handle_navigation_action(navigation_result)

    return navigation_result


def handle_navigation_action(navigation_result):
    """Handle navigation actions from smart navigation system."""
    action = navigation_result["action"]
    target = navigation_result["target"]

    if action == "navigate":
        # Handle hub navigation
        if target in ["Executive Command Center", "Lead Intelligence Hub", "Automation Studio", "Sales Copilot", "Ops & Optimization"]:
            st.session_state.current_hub = target
            st.rerun()
        elif "/" in target:
            # Handle nested navigation (hub/tab/section)
            parts = target.split("/")
            st.session_state.current_hub = parts[0]
            if len(parts) > 1:
                st.session_state.current_tab = parts[1]
            st.rerun()

    elif action == "modal":
        # Handle modal actions
        show_modal(target)

    elif action == "function":
        # Handle function calls
        execute_function(target)


def show_modal(modal_type):
    """Show modal dialogs for quick actions."""

    if modal_type == "revenue_pipeline":
        show_revenue_pipeline_modal()
    elif modal_type == "schedule_report":
        show_schedule_report_modal()
    elif modal_type == "lead_scoring":
        show_lead_scoring_modal()
    elif modal_type == "create_workflow":
        show_workflow_creation_modal()
    elif modal_type == "ai_coaching":
        show_ai_coaching_modal()
    # Add more modal handlers as needed


def show_revenue_pipeline_modal():
    """Show revenue pipeline quick overview modal."""
    with st.expander("💰 Revenue Pipeline Overview", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Active Pipeline", "$2.4M", "+15%")

        with col2:
            st.metric("Expected Close", "$680K", "+8%")

        with col3:
            st.metric("This Quarter", "$1.2M", "+22%")

        st.markdown("**Top 5 Opportunities:**")
        pipeline_data = [
            {"Property": "Downtown Condo", "Value": "$485K", "Probability": "85%"},
            {"Property": "Suburban House", "Value": "$320K", "Probability": "70%"},
            {"Property": "Luxury Villa", "Value": "$750K", "Probability": "60%"},
            {"Property": "Investment Duplex", "Value": "$425K", "Probability": "75%"},
            {"Property": "Commercial Space", "Value": "$1.2M", "Probability": "45%"}
        ]

        for deal in pipeline_data:
            st.markdown(f"• **{deal['Property']}**: {deal['Value']} (Prob: {deal['Probability']})")


def show_schedule_report_modal():
    """Show report scheduling modal."""
    with st.expander("📅 Schedule Automated Report", expanded=True):
        report_name = st.text_input("Report Name", "Weekly Executive Summary")

        col1, col2 = st.columns(2)
        with col1:
            report_type = st.selectbox(
                "Report Type",
                ["Revenue Intelligence PDF", "Excel Dashboard", "PowerBI Dataset"]
            )
        with col2:
            frequency = st.selectbox(
                "Frequency",
                ["Daily", "Weekly", "Monthly"]
            )

        recipients = st.text_area(
            "Email Recipients (one per line)",
            "jorge@realestate.com\nexecutive@company.com"
        )

        if st.button("Schedule Report", type="primary"):
            st.success(f"✅ Scheduled '{report_name}' to run {frequency.lower()}")
            st.balloons()


def show_lead_scoring_modal():
    """Show quick lead scoring modal."""
    with st.expander("🎯 Quick Lead Scoring", expanded=True):
        st.markdown("**Score a new lead quickly:**")

        col1, col2 = st.columns(2)
        with col1:
            lead_name = st.text_input("Lead Name", "New Prospect")
            budget = st.selectbox("Budget Range", ["<$200K", "$200K-$400K", "$400K-$600K", "$600K+"])

        with col2:
            timeline = st.selectbox("Timeline", ["ASAP", "3-6 months", "6-12 months", "Exploring"])
            location = st.selectbox("Preferred Area", ["Downtown", "Suburbs", "Luxury District", "Investment Zone"])

        # Mock scoring calculation
        score = 65  # Would be calculated by actual scoring service

        if st.button("Calculate Score", type="primary"):
            if score >= 70:
                st.success(f"🔥 **Hot Lead** - Score: {score}/100")
            elif score >= 40:
                st.warning(f"🌡️ **Warm Lead** - Score: {score}/100")
            else:
                st.info(f"❄️ **Cold Lead** - Score: {score}/100")


def show_workflow_creation_modal():
    """Show workflow creation modal."""
    with st.expander("⚡ Quick Workflow Creator", expanded=True):
        workflow_name = st.text_input("Workflow Name", "New Lead Follow-up")

        trigger = st.selectbox(
            "Trigger",
            ["New Lead Created", "Lead Score Changed", "Property Match Found", "Appointment Scheduled"]
        )

        action = st.selectbox(
            "Action",
            ["Send Email", "Create Task", "Update CRM", "Schedule Follow-up", "Send SMS"]
        )

        delay = st.selectbox("Delay", ["Immediate", "5 minutes", "1 hour", "1 day", "3 days"])

        if st.button("Create Workflow", type="primary"):
            st.success(f"✅ Created workflow: '{workflow_name}' with trigger '{trigger}' and action '{action}'")


def show_ai_coaching_modal():
    """Show AI coaching modal."""
    with st.expander("🎓 AI Coaching Assistant", expanded=True):
        st.markdown("**Get AI-powered coaching for your current situation:**")

        situation = st.selectbox(
            "Current Situation",
            ["Handling Objections", "Price Negotiation", "Closing Techniques", "Lead Qualification", "Property Showing"]
        )

        context = st.text_area(
            "Additional Context",
            "Client is concerned about market conditions and wants to wait..."
        )

        if st.button("Get Coaching", type="primary"):
            # Mock coaching response
            coaching_responses = {
                "Handling Objections": "🎯 **Strategy**: Acknowledge their concern, provide market data showing stability, and create urgency through limited inventory. Use the 'Feel, Felt, Found' technique.",
                "Price Negotiation": "💪 **Approach**: Present comparable sales data, highlight unique property features, and suggest creative financing options. Maintain firm but flexible stance.",
                "Closing Techniques": "🎬 **Close**: Use assumptive close - 'When would you like to schedule the inspection?' Focus on next steps rather than yes/no questions.",
                "Lead Qualification": "🔍 **Questions**: Ask about timeline, budget confirmation, and decision-making process. Use BANT (Budget, Authority, Need, Timeline) framework.",
                "Property Showing": "🏠 **Preparation**: Research comparable properties, prepare benefit statements for each room, and have financing options ready to discuss."
            }

            st.info(coaching_responses.get(situation, "💡 **Tip**: Focus on building rapport and understanding client needs first."))


def execute_function(function_name):
    """Execute function-type quick actions."""

    if function_name == "export_executive_data":
        export_executive_data()
    elif function_name == "show_hot_leads":
        show_hot_leads_alert()
    elif function_name == "suggest_action":
        suggest_next_best_action()
    elif function_name == "quality_check":
        run_quality_check()


def export_executive_data():
    """Export current executive dashboard data."""
    st.success("📊 Executive data exported to 'executive_dashboard_export.csv'")

    # Create sample export data
    import pandas as pd
    export_data = pd.DataFrame({
        "Metric": ["Pipeline Value", "Hot Leads", "Conversion Rate", "Avg Deal Size"],
        "Current": ["$2.4M", "23", "34%", "$385K"],
        "Previous": ["$2.1M", "19", "32%", "$373K"],
        "Change": ["+14.3%", "+21.1%", "+6.3%", "+3.2%"]
    })

    csv = export_data.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Download Export",
        data=csv,
        file_name="executive_dashboard_export.csv",
        mime="text/csv"
    )


def show_hot_leads_alert():
    """Show hot leads alert."""
    st.warning("🔥 **3 Hot Leads Need Immediate Attention!**")

    hot_leads = [
        {"name": "Sarah Johnson", "score": 85, "last_contact": "2 hours ago"},
        {"name": "Mike Chen", "score": 92, "last_contact": "4 hours ago"},
        {"name": "Emily Davis", "score": 78, "last_contact": "1 day ago"}
    ]

    for lead in hot_leads:
        st.markdown(f"• **{lead['name']}** - Score: {lead['score']} (Last contact: {lead['last_contact']})")


def suggest_next_best_action():
    """Suggest next best action based on current context."""
    suggestions = [
        "📞 Call Mike Chen (Hot lead, 92 score, last contact 4 hours ago)",
        "📧 Send follow-up email to Sarah Johnson about property viewing",
        "📅 Schedule property tour for Emily Davis this week",
        "📋 Update CRM with latest conversation notes",
        "🎯 Review and score 5 new leads from this morning"
    ]

    st.info("💡 **Next Best Actions:**")
    for i, suggestion in enumerate(suggestions, 1):
        st.markdown(f"{i}. {suggestion}")


def run_quality_check():
    """Run quality assurance check."""
    st.success("✅ Quality Check Complete")

    st.markdown("**System Health:**")
    checks = [
        {"item": "CRM Data Sync", "status": "✅ Healthy"},
        {"item": "AI Model Performance", "status": "✅ Optimal"},
        {"item": "Pipeline Accuracy", "status": "⚠️ Needs Review"},
        {"item": "Response Times", "status": "✅ Under 2s"},
        {"item": "Lead Scoring", "status": "✅ 98% Accuracy"}
    ]

    for check in checks:
        st.markdown(f"• **{check['item']}**: {check['status']}")


def add_progressive_disclosure_example():
    """Example of how to use progressive disclosure in your app."""

    def revenue_content(summary_mode=False):
        if summary_mode:
            return "Pipeline: $2.4M | Hot Leads: 23 | Conversion: 34%"
        else:
            st.metric("Total Pipeline", "$2.4M", "+15%")
            st.metric("Hot Leads", "23", "+8")
            st.metric("Conversion Rate", "34%", "+2%")
            # Add more detailed content here

    def analytics_content(summary_mode=False):
        if summary_mode:
            return "Response time: 1.2s | Accuracy: 98% | Uptime: 99.9%"
        else:
            st.metric("Avg Response Time", "1.2s", "-0.3s")
            st.metric("AI Accuracy", "98%", "+1%")
            st.metric("System Uptime", "99.9%", "0%")
            # Add charts and detailed analytics

    # Use progressive disclosure
    ProgressiveDisclosureComponent.render_expandable_section(
        "Revenue Intelligence",
        revenue_content,
        icon="💰",
        expanded=False
    )

    ProgressiveDisclosureComponent.render_expandable_section(
        "Performance Analytics",
        analytics_content,
        icon="📊",
        expanded=False
    )


# Export integration functions
__all__ = [
    "enhance_app_with_smart_navigation",
    "handle_navigation_action",
    "add_progressive_disclosure_example"
]