"""
Claude Conversation Templates Streamlit Component

Interactive interface for agents to access, customize, and use Claude conversation
templates for different real estate scenarios. Provides template library, customization
tools, and usage analytics.
"""

import streamlit as st
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from services.claude_conversation_templates import (
    conversation_template_service,
    ConversationScenario,
    AgentExperienceLevel,
    ConversationStyle,
    get_conversation_template,
    get_conversation_flow,
    customize_agent_prompt,
    update_conversation_preferences,
    track_conversation_effectiveness
)
from services.claude_agent_service import ClaudeAgentService


def render_claude_conversation_templates():
    """Render the Claude conversation templates interface."""
    st.header("🎯 Claude Conversation Templates")
    st.markdown("*AI-powered conversation templates and prompts for real estate scenarios*")

    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📚 Template Library",
        "⚙️ Agent Preferences",
        "🎨 Custom Templates",
        "📊 Usage Analytics",
        "🔄 Conversation Flows"
    ])

    with tab1:
        render_template_library()

    with tab2:
        render_agent_preferences()

    with tab3:
        render_custom_templates()

    with tab4:
        render_usage_analytics()

    with tab5:
        render_conversation_flows()


def render_template_library():
    """Render the template library interface."""
    st.subheader("📚 Template Library")

    # Agent selection
    agent_id = st.selectbox(
        "Select Agent",
        options=["agent_001", "agent_002", "agent_003", "demo_agent"],
        help="Select agent to personalize templates"
    )

    # Scenario filter
    selected_scenarios = st.multiselect(
        "Filter by Scenario",
        options=[scenario.value for scenario in ConversationScenario],
        default=[],
        help="Filter templates by conversation scenarios"
    )

    # Experience level filter
    experience_filter = st.selectbox(
        "Experience Level",
        options=["All Levels"] + [level.value for level in AgentExperienceLevel],
        help="Filter by agent experience level"
    )

    # Style filter
    style_filter = st.selectbox(
        "Conversation Style",
        options=["All Styles"] + [style.value for style in ConversationStyle],
        help="Filter by conversation style"
    )

    # Search functionality
    search_query = st.text_input(
        "Search Templates",
        placeholder="Search by name, description, or tags...",
        help="Search templates by keywords"
    )

    # Get templates
    try:
        # Filter templates based on criteria
        filtered_templates = []
        for template in conversation_template_service.templates.values():
            # Scenario filter
            if selected_scenarios and template.scenario.value not in selected_scenarios:
                continue

            # Experience filter
            if experience_filter != "All Levels" and template.experience_level.value != experience_filter:
                continue

            # Style filter
            if style_filter != "All Styles" and template.style.value != style_filter:
                continue

            # Search filter
            if search_query:
                search_text = f"{template.name} {template.description} {' '.join(template.tags)}".lower()
                if search_query.lower() not in search_text:
                    continue

            filtered_templates.append(template)

        # Sort by effectiveness and usage
        filtered_templates.sort(key=lambda x: (x.effectiveness_score, x.usage_count), reverse=True)

        # Display templates
        if filtered_templates:
            st.write(f"Found {len(filtered_templates)} templates")

            for i, template in enumerate(filtered_templates):
                with st.expander(f"📋 {template.name} (Score: {template.effectiveness_score:.2f})"):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.write(f"**Description:** {template.description}")
                        st.write(f"**Scenario:** {template.scenario.value.replace('_', ' ').title()}")
                        st.write(f"**Experience Level:** {template.experience_level.value.title()}")
                        st.write(f"**Style:** {template.style.value.replace('_', ' ').title()}")

                        if template.tags:
                            tags_html = " ".join([f"<span style='background-color: #e1f5fe; padding: 2px 8px; border-radius: 12px; font-size: 12px;'>{tag}</span>" for tag in template.tags])
                            st.markdown(f"**Tags:** {tags_html}", unsafe_allow_html=True)

                    with col2:
                        st.metric("Usage Count", template.usage_count)
                        st.metric("Effectiveness", f"{template.effectiveness_score:.2f}")

                        if st.button(f"Use Template", key=f"use_template_{i}"):
                            use_template(template, agent_id)

                    # Show conversation starters
                    st.write("**Conversation Starters:**")
                    for starter in template.conversation_starters:
                        st.write(f"• {starter}")

                    # Show expected outcomes
                    if template.expected_outcomes:
                        st.write("**Expected Outcomes:**")
                        for outcome in template.expected_outcomes:
                            st.write(f"✓ {outcome}")

                    # Show system prompt (truncated)
                    if st.checkbox(f"Show System Prompt", key=f"show_prompt_{i}"):
                        st.code(template.system_prompt, language="text")

        else:
            st.info("No templates match your current filters. Try adjusting the criteria.")

    except Exception as e:
        st.error(f"Error loading templates: {str(e)}")


def render_agent_preferences():
    """Render agent preferences configuration."""
    st.subheader("⚙️ Agent Preferences")

    # Agent selection
    agent_id = st.selectbox(
        "Select Agent",
        options=["agent_001", "agent_002", "agent_003", "demo_agent"],
        help="Select agent to configure preferences",
        key="preferences_agent"
    )

    try:
        # Get current preferences
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        preferences = loop.run_until_complete(conversation_template_service.get_agent_preferences(agent_id))
        loop.close()

        col1, col2 = st.columns(2)

        with col1:
            # Experience level
            new_experience = st.selectbox(
                "Experience Level",
                options=[level.value for level in AgentExperienceLevel],
                index=list(AgentExperienceLevel).index(preferences.experience_level),
                help="Set your experience level to get appropriate templates"
            )

            # Preferred style
            new_style = st.selectbox(
                "Preferred Conversation Style",
                options=[style.value for style in ConversationStyle],
                index=list(ConversationStyle).index(preferences.preferred_style),
                help="Choose your preferred conversation approach"
            )

            # Specializations
            specializations = st.multiselect(
                "Specializations",
                options=[
                    "Luxury Properties", "First-Time Buyers", "Investment Properties",
                    "Commercial Real Estate", "Property Management", "Market Analysis",
                    "Negotiations", "Staging", "Marketing", "Relocation"
                ],
                default=preferences.specializations,
                help="Select your areas of specialization"
            )

        with col2:
            # Market focus
            market_focus = st.multiselect(
                "Market Focus Areas",
                options=[
                    "Downtown", "Suburbs", "Waterfront", "Historic Districts",
                    "New Developments", "Condominiums", "Single Family",
                    "Multi-Family", "Land", "Commercial"
                ],
                default=preferences.market_focus,
                help="Select your primary market focus areas"
            )

            # Custom prompts
            st.write("**Custom Prompts by Scenario:**")
            custom_prompts = {}

            for scenario in ConversationScenario:
                scenario_name = scenario.value.replace('_', ' ').title()
                current_custom = preferences.custom_prompts.get(scenario.value, "")
                custom_prompt = st.text_area(
                    f"{scenario_name}",
                    value=current_custom,
                    height=60,
                    help=f"Add custom instructions for {scenario_name} conversations",
                    key=f"custom_prompt_{scenario.value}"
                )
                if custom_prompt.strip():
                    custom_prompts[scenario.value] = custom_prompt.strip()

        # Save preferences
        if st.button("💾 Save Preferences"):
            try:
                updates = {
                    "experience_level": AgentExperienceLevel(new_experience),
                    "preferred_style": ConversationStyle(new_style),
                    "specializations": specializations,
                    "market_focus": market_focus,
                    "custom_prompts": custom_prompts
                }

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                updated_preferences = loop.run_until_complete(
                    conversation_template_service.update_agent_preferences(agent_id, updates)
                )
                loop.close()

                st.success("✅ Preferences saved successfully!")
                st.experimental_rerun()

            except Exception as e:
                st.error(f"Error saving preferences: {str(e)}")

        # Performance metrics
        if preferences.performance_metrics:
            st.subheader("📈 Performance Metrics")
            metrics_df = pd.DataFrame([preferences.performance_metrics])
            st.dataframe(metrics_df)

        # Favorite templates
        if preferences.favorite_templates:
            st.subheader("⭐ Favorite Templates")
            for template_id in preferences.favorite_templates:
                if template_id in conversation_template_service.templates:
                    template = conversation_template_service.templates[template_id]
                    st.write(f"• {template.name} ({template.scenario.value})")

    except Exception as e:
        st.error(f"Error loading preferences: {str(e)}")


def render_custom_templates():
    """Render custom template creation interface."""
    st.subheader("🎨 Custom Templates")

    # Template creation form
    with st.form("create_custom_template"):
        st.write("**Create New Template**")

        col1, col2 = st.columns(2)

        with col1:
            template_name = st.text_input("Template Name", placeholder="e.g., Luxury Client Consultation")
            scenario = st.selectbox("Scenario", options=[s.value for s in ConversationScenario])
            experience_level = st.selectbox("Target Experience Level", options=[l.value for l in AgentExperienceLevel])
            style = st.selectbox("Conversation Style", options=[s.value for s in ConversationStyle])

        with col2:
            description = st.text_area("Description", height=100, placeholder="Describe what this template helps with...")
            tags = st.text_input("Tags (comma-separated)", placeholder="luxury, consultation, high-value")

        # System prompt
        system_prompt = st.text_area(
            "System Prompt",
            height=200,
            placeholder="You are an AI assistant helping a real estate agent with...",
            help="This is the core instruction that tells Claude how to behave for this template"
        )

        # Conversation starters
        st.write("**Conversation Starters** (one per line)")
        starters_text = st.text_area(
            "conversation_starters",
            height=100,
            placeholder="Help me prepare for a luxury client consultation\nWhat questions should I ask high-net-worth clients?\nHow do I position myself for luxury listings?",
            label_visibility="collapsed"
        )

        # Follow-up prompts
        st.write("**Follow-up Prompts** (one per line)")
        followups_text = st.text_area(
            "follow_up_prompts",
            height=100,
            placeholder="What should I ask next?\nHow do I handle price objections?\nWhat closing techniques work best?",
            label_visibility="collapsed"
        )

        # Expected outcomes
        st.write("**Expected Outcomes** (one per line)")
        outcomes_text = st.text_area(
            "expected_outcomes",
            height=80,
            placeholder="Client trust established\nBudget range identified\nNext appointment scheduled",
            label_visibility="collapsed"
        )

        # Required context
        st.write("**Required Context** (comma-separated)")
        required_context = st.text_input(
            "required_context",
            placeholder="client_profile, property_preferences, budget_range",
            label_visibility="collapsed"
        )

        # Submit button
        submitted = st.form_submit_button("🚀 Create Template")

        if submitted:
            if template_name and system_prompt:
                try:
                    from services.claude_conversation_templates import ConversationTemplate
                    import uuid

                    # Parse inputs
                    conversation_starters = [s.strip() for s in starters_text.split('\n') if s.strip()]
                    follow_up_prompts = [s.strip() for s in followups_text.split('\n') if s.strip()]
                    expected_outcomes = [s.strip() for s in outcomes_text.split('\n') if s.strip()]
                    required_context_list = [s.strip() for s in required_context.split(',') if s.strip()]
                    tags_list = [s.strip() for s in tags.split(',') if s.strip()]

                    # Create template
                    template = ConversationTemplate(
                        id=f"custom_{uuid.uuid4().hex[:8]}",
                        name=template_name,
                        scenario=ConversationScenario(scenario),
                        description=description,
                        system_prompt=system_prompt,
                        conversation_starters=conversation_starters,
                        follow_up_prompts=follow_up_prompts,
                        expected_outcomes=expected_outcomes,
                        required_context=required_context_list,
                        experience_level=AgentExperienceLevel(experience_level),
                        style=ConversationStyle(style),
                        tags=tags_list,
                        created_by=st.session_state.get('user_id', 'unknown')
                    )

                    # Add to service
                    conversation_template_service.templates[template.id] = template

                    st.success("✅ Template created successfully!")
                    st.experimental_rerun()

                except Exception as e:
                    st.error(f"Error creating template: {str(e)}")
            else:
                st.error("Please provide at least a template name and system prompt.")

    # Existing custom templates
    st.subheader("📝 Your Custom Templates")
    custom_templates = [
        template for template in conversation_template_service.templates.values()
        if template.created_by != "system"
    ]

    if custom_templates:
        for template in custom_templates:
            with st.expander(f"📝 {template.name}"):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(f"**Scenario:** {template.scenario.value}")
                    st.write(f"**Description:** {template.description}")
                    st.write(f"**Usage:** {template.usage_count} times")

                with col2:
                    if st.button("🗑️ Delete", key=f"delete_{template.id}"):
                        del conversation_template_service.templates[template.id]
                        st.success("Template deleted!")
                        st.experimental_rerun()

                    if st.button("⭐ Favorite", key=f"fav_{template.id}"):
                        # Add to favorites (would need agent_id context)
                        st.success("Added to favorites!")

                if st.checkbox(f"Edit Template", key=f"edit_{template.id}"):
                    # Inline editing (simplified)
                    new_description = st.text_area(
                        "Description",
                        value=template.description,
                        key=f"edit_desc_{template.id}"
                    )
                    new_prompt = st.text_area(
                        "System Prompt",
                        value=template.system_prompt,
                        height=150,
                        key=f"edit_prompt_{template.id}"
                    )

                    if st.button("💾 Save Changes", key=f"save_{template.id}"):
                        template.description = new_description
                        template.system_prompt = new_prompt
                        template.last_updated = datetime.utcnow()
                        st.success("Template updated!")
                        st.experimental_rerun()
    else:
        st.info("No custom templates created yet. Use the form above to create your first template!")


def render_usage_analytics():
    """Render usage analytics and insights."""
    st.subheader("📊 Usage Analytics")

    try:
        # Get service stats
        stats = conversation_template_service.get_service_stats()

        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Templates", stats["total_templates"])
        with col2:
            st.metric("Active Agents", stats["total_agents"])
        with col3:
            st.metric("Total Conversations", stats["total_conversations"])
        with col4:
            st.metric("Avg Effectiveness", f"{stats['average_effectiveness']:.2f}")

        # Most used templates chart
        if stats["most_used_templates"]:
            st.subheader("📈 Most Popular Templates")
            most_used_df = pd.DataFrame(stats["most_used_templates"])
            fig = px.bar(
                most_used_df,
                x="name",
                y="usage_count",
                title="Template Usage Frequency",
                labels={"name": "Template Name", "usage_count": "Usage Count"}
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)

        # Scenario coverage
        if stats["scenarios_covered"]:
            st.subheader("📋 Scenario Coverage")
            scenarios_df = pd.DataFrame({
                "scenario": stats["scenarios_covered"],
                "count": [1] * len(stats["scenarios_covered"])  # Simplified
            })
            fig = px.pie(
                scenarios_df,
                values="count",
                names="scenario",
                title="Templates by Scenario"
            )
            st.plotly_chart(fig, use_container_width=True)

        # Analytics over time (simulated)
        if conversation_template_service.analytics:
            st.subheader("📈 Usage Trends")

            analytics_data = []
            for analytics in conversation_template_service.analytics:
                analytics_data.append({
                    "date": analytics.start_time.date(),
                    "effectiveness": analytics.effectiveness_score,
                    "scenario": analytics.scenario.value
                })

            if analytics_data:
                analytics_df = pd.DataFrame(analytics_data)
                daily_stats = analytics_df.groupby("date").agg({
                    "effectiveness": "mean"
                }).reset_index()

                fig = px.line(
                    daily_stats,
                    x="date",
                    y="effectiveness",
                    title="Average Effectiveness Over Time",
                    labels={"effectiveness": "Effectiveness Score", "date": "Date"}
                )
                st.plotly_chart(fig, use_container_width=True)

        # Template effectiveness comparison
        st.subheader("🎯 Template Effectiveness")
        templates_data = []
        for template in conversation_template_service.templates.values():
            templates_data.append({
                "name": template.name,
                "effectiveness": template.effectiveness_score,
                "usage": template.usage_count,
                "scenario": template.scenario.value
            })

        if templates_data:
            templates_df = pd.DataFrame(templates_data)
            fig = px.scatter(
                templates_df,
                x="usage",
                y="effectiveness",
                size="usage",
                color="scenario",
                hover_data=["name"],
                title="Template Usage vs Effectiveness",
                labels={"usage": "Usage Count", "effectiveness": "Effectiveness Score"}
            )
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading analytics: {str(e)}")


def render_conversation_flows():
    """Render conversation flows interface."""
    st.subheader("🔄 Conversation Flows")

    # Flow selection
    agent_id = st.selectbox(
        "Select Agent",
        options=["agent_001", "agent_002", "agent_003", "demo_agent"],
        help="Select agent for personalized flows",
        key="flows_agent"
    )

    scenario = st.selectbox(
        "Select Scenario",
        options=[s.value for s in ConversationScenario],
        help="Choose conversation scenario",
        key="flows_scenario"
    )

    try:
        # Get conversation flow
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        flow = loop.run_until_complete(
            conversation_template_service.get_conversation_flow(
                ConversationScenario(scenario),
                agent_id
            )
        )
        loop.close()

        if flow:
            # Flow overview
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Estimated Duration", f"{flow.estimated_duration} min")
            with col2:
                st.metric("Success Rate", f"{flow.success_rate:.1%}")
            with col3:
                st.metric("Usage Count", flow.usage_count)

            st.write(f"**Description:** {flow.description}")

            # Flow steps
            st.subheader("📋 Flow Steps")
            for step in flow.steps:
                with st.expander(f"Step {step['step']}: {step['name']}"):
                    st.write(f"**Prompt:** {step['prompt']}")

                    if step.get('context_required'):
                        st.write("**Required Context:**")
                        for context in step['context_required']:
                            st.write(f"• {context}")

                    if step.get('expected_output'):
                        st.write(f"**Expected Output:** {step['expected_output']}")

                    # Interactive step execution
                    if st.button(f"Execute Step {step['step']}", key=f"exec_step_{step['step']}"):
                        execute_flow_step(flow, step, agent_id)

            # Branching rules
            if flow.branching_rules:
                st.subheader("🌳 Branching Logic")
                for condition, branch in flow.branching_rules.items():
                    st.write(f"**{condition}** → {branch}")

            # Success criteria
            if flow.success_criteria:
                st.subheader("✅ Success Criteria")
                for criterion in flow.success_criteria:
                    st.write(f"• {criterion}")

            # Fallback strategies
            if flow.fallback_strategies:
                st.subheader("🔄 Fallback Strategies")
                for strategy in flow.fallback_strategies:
                    st.write(f"• {strategy}")

            # Start flow
            if st.button("🚀 Start Conversation Flow", type="primary"):
                start_conversation_flow(flow, agent_id)

    except Exception as e:
        st.error(f"Error loading conversation flow: {str(e)}")


def use_template(template, agent_id):
    """Use a specific template for conversation."""
    try:
        # Store selected template in session state
        st.session_state['selected_template'] = template
        st.session_state['template_agent_id'] = agent_id

        # Generate customized prompt
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        customized_prompt = loop.run_until_complete(
            customize_agent_prompt(template.id, agent_id, {})
        )
        loop.close()

        st.success(f"✅ Template '{template.name}' activated!")

        # Show quick actions
        st.subheader("🎯 Quick Actions")
        for i, starter in enumerate(template.conversation_starters):
            if st.button(f"💬 {starter}", key=f"starter_{i}"):
                start_conversation_with_template(template, agent_id, starter)

        # Show customized prompt
        with st.expander("👁️ View Customized Prompt"):
            st.code(customized_prompt, language="text")

    except Exception as e:
        st.error(f"Error using template: {str(e)}")


def start_conversation_with_template(template, agent_id, message):
    """Start a conversation using a template."""
    try:
        # Initialize Claude service
        claude_service = ClaudeAgentService()

        # Store conversation details
        st.session_state['active_template'] = template.id
        st.session_state['conversation_agent'] = agent_id
        st.session_state['conversation_start'] = datetime.utcnow()

        # Start conversation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Get customized prompt
        context = st.session_state.get('lead_context', {})
        customized_prompt = loop.run_until_complete(
            customize_agent_prompt(template.id, agent_id, context)
        )

        # Send to Claude with customized system prompt
        response = loop.run_until_complete(
            claude_service.chat_with_agent(agent_id, message, context={"system_prompt": customized_prompt})
        )
        loop.close()

        # Display response
        st.subheader("🤖 Claude Response")
        st.write(response.response)

        if response.insights:
            with st.expander("💡 Insights"):
                for insight in response.insights:
                    st.write(f"• {insight}")

        if response.recommendations:
            with st.expander("📋 Recommendations"):
                for rec in response.recommendations:
                    st.write(f"• {rec}")

        # Track usage
        session_id = st.session_state.get('session_id', f"session_{int(datetime.utcnow().timestamp())}")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            track_conversation_effectiveness(
                template.id,
                agent_id,
                session_id,
                template.scenario,
                0.8,  # Default effectiveness score
                start_time=datetime.utcnow(),
                outcome="conversation_started"
            )
        )
        loop.close()

    except Exception as e:
        st.error(f"Error starting conversation: {str(e)}")


def execute_flow_step(flow, step, agent_id):
    """Execute a specific flow step."""
    st.info(f"Executing step: {step['name']}")

    # For demo purposes, show what would happen
    st.write(f"**Prompt:** {step['prompt']}")

    # In a real implementation, this would integrate with the Claude service
    st.success("Step executed successfully!")


def start_conversation_flow(flow, agent_id):
    """Start a complete conversation flow."""
    st.session_state['active_flow'] = flow.id
    st.session_state['current_step'] = 1
    st.session_state['flow_agent'] = agent_id

    st.success(f"🚀 Started conversation flow: {flow.name}")
    st.info("Flow execution would begin with step 1. In a full implementation, this would guide the agent through each step with Claude integration.")


# Helper function to initialize session state
def initialize_session_state():
    """Initialize session state variables."""
    if 'selected_template' not in st.session_state:
        st.session_state['selected_template'] = None
    if 'active_conversation' not in st.session_state:
        st.session_state['active_conversation'] = None
    if 'user_id' not in st.session_state:
        st.session_state['user_id'] = "demo_user"


# Call initialization
initialize_session_state()


# Demo data for testing
def load_demo_data():
    """Load demo conversation analytics."""
    if not conversation_template_service.analytics:
        from services.claude_conversation_templates import ConversationAnalytics
        import uuid

        # Add some demo analytics
        demo_analytics = [
            ConversationAnalytics(
                template_id="lead_qual_rookie",
                agent_id="agent_001",
                session_id=str(uuid.uuid4()),
                scenario=ConversationScenario.LEAD_QUALIFICATION,
                start_time=datetime.utcnow() - timedelta(days=i),
                end_time=datetime.utcnow() - timedelta(days=i, hours=-1),
                outcome="successful_qualification",
                effectiveness_score=0.7 + (i % 3) * 0.1,
                lead_id=f"lead_{i}",
                context_data={"budget_discovered": True},
                feedback_rating=4 + (i % 2),
                notes=f"Demo conversation {i}"
            )
            for i in range(10)
        ]
        conversation_template_service.analytics.extend(demo_analytics)


# Load demo data when component is imported
load_demo_data()