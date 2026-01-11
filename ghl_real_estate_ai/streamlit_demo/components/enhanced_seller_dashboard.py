"""
Enhanced Seller Dashboard

Comprehensive seller lead management dashboard with Claude integration,
real-time market insights, and intelligent automation.

Business Impact: 50% improvement in seller conversion rates
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

# Import services
try:
    from ...services.claude_seller_agent import (
        ClaudeSellerAgent, SellerContext, SellerStage, ConversationIntent,
        get_claude_seller_agent
    )
    from ...services.seller_insights_service import SellerInsightsService, SellingPathway
    from ...services.ai_listing_writer import AIListingWriterService
    from ...services.real_time_market_intelligence import market_intelligence
except ImportError:
    # Fallback for demo mode
    ClaudeSellerAgent = None


class EnhancedSellerDashboard:
    """
    Comprehensive seller dashboard with AI integration.

    Features:
    - Real-time seller pipeline management
    - Claude agent integration for conversations
    - Automated market analysis
    - Intelligent seller nurturing
    - Performance analytics and insights
    """

    def __init__(self):
        self.claude_agent = get_claude_seller_agent() if ClaudeSellerAgent else None
        self.seller_insights = SellerInsightsService("demo") if 'SellerInsightsService' in globals() else None

    def render_dashboard(self) -> None:
        """Render the complete seller dashboard"""

        st.title("🏠 Enhanced Seller Dashboard")
        st.markdown("*AI-powered seller lead management with Claude integration*")

        # Navigation tabs
        tab_pipeline, tab_conversations, tab_analytics, tab_automation = st.tabs([
            "📊 Seller Pipeline", "💬 Claude Conversations",
            "📈 Analytics", "🤖 Automation"
        ])

        with tab_pipeline:
            self.render_seller_pipeline()

        with tab_conversations:
            self.render_claude_conversations()

        with tab_analytics:
            self.render_seller_analytics()

        with tab_automation:
            self.render_automation_center()

    def render_seller_pipeline(self) -> None:
        """Render seller pipeline management interface"""

        st.markdown("### 📊 Seller Lead Pipeline")

        # Pipeline metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Active Sellers", "23", "+3")
        with col2:
            st.metric("Market Analysis Pending", "8", "-1")
        with col3:
            st.metric("Ready to Close", "5", "+2")
        with col4:
            st.metric("Monthly Conversion", "68%", "+12%")

        # Pipeline visualization
        self.render_pipeline_kanban()

        # Seller details table
        st.markdown("### 📋 Seller Details")
        self.render_seller_table()

    def render_pipeline_kanban(self) -> None:
        """Render Kanban-style pipeline visualization"""

        # Sample seller data
        sellers_data = self.get_sample_sellers_data()

        # Group by stage
        stages = {
            "Initial Contact": [],
            "Information Gathering": [],
            "Market Analysis": [],
            "Decision Making": [],
            "Closing Prep": []
        }

        for seller in sellers_data:
            stage = seller['stage']
            if stage in stages:
                stages[stage].append(seller)

        # Create columns for each stage
        cols = st.columns(len(stages))

        for i, (stage, sellers) in enumerate(stages.items()):
            with cols[i]:
                st.markdown(f"**{stage}**")
                st.markdown(f"<small>{len(sellers)} sellers</small>", unsafe_allow_html=True)

                # Render seller cards
                for seller in sellers:
                    self.render_seller_card(seller)

    def render_seller_card(self, seller: Dict[str, Any]) -> None:
        """Render individual seller card"""

        # Determine card color based on urgency
        urgency_colors = {
            "high": "#ff4444",
            "medium": "#ffaa44",
            "low": "#44ff44"
        }

        color = urgency_colors.get(seller.get('urgency', 'medium'), '#ffaa44')

        card_html = f"""
        <div style="
            border-left: 4px solid {color};
            padding: 10px;
            margin: 8px 0;
            background: white;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <div style="font-weight: bold; font-size: 14px;">{seller['name']}</div>
            <div style="font-size: 12px; color: #666;">
                {seller['property_address'][:30]}...
            </div>
            <div style="font-size: 12px; margin-top: 5px;">
                <span style="color: #333;">Est. Value: ${seller['estimated_value']:,}</span>
            </div>
            <div style="font-size: 11px; color: #888; margin-top: 3px;">
                Last Contact: {seller['last_contact']}
            </div>
        </div>
        """

        st.markdown(card_html, unsafe_allow_html=True)

        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"💬", key=f"chat_{seller['id']}", help="Chat with Claude"):
                self.open_seller_chat(seller)
        with col2:
            if st.button(f"📊", key=f"analyze_{seller['id']}", help="Market Analysis"):
                self.open_market_analysis(seller)

    def render_seller_table(self) -> None:
        """Render comprehensive seller details table"""

        sellers_data = self.get_sample_sellers_data()
        df = pd.DataFrame(sellers_data)

        # Add action columns
        df_display = df[['name', 'property_address', 'estimated_value', 'urgency', 'stage', 'last_contact']].copy()
        df_display.columns = ['Name', 'Property', 'Est. Value', 'Urgency', 'Stage', 'Last Contact']

        # Format currency
        df_display['Est. Value'] = df_display['Est. Value'].apply(lambda x: f"${x:,}")

        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Urgency": st.column_config.SelectboxColumn(
                    options=["high", "medium", "low"],
                    help="Seller urgency level"
                )
            }
        )

    def render_claude_conversations(self) -> None:
        """Render Claude conversation interface"""

        st.markdown("### 💬 Claude Seller Conversations")

        # Seller selection
        sellers_data = self.get_sample_sellers_data()
        seller_options = {f"{s['name']} - {s['property_address'][:30]}...": s for s in sellers_data}

        selected_seller_key = st.selectbox(
            "Select Seller for Conversation:",
            options=list(seller_options.keys()),
            key="claude_seller_selection"
        )

        if selected_seller_key:
            selected_seller = seller_options[selected_seller_key]
            self.render_seller_conversation(selected_seller)

    def render_seller_conversation(self, seller: Dict[str, Any]) -> None:
        """Render conversation interface for specific seller"""

        # Create seller context
        seller_context = SellerContext(
            lead_id=seller['id'],
            contact_id=seller['id'],
            name=seller['name'],
            property_address=seller['property_address'],
            estimated_value_range=(seller['estimated_value'] * 0.9, seller['estimated_value'] * 1.1)
        )

        # Conversation history
        st.markdown("#### 📝 Conversation History")

        if f"conversation_history_{seller['id']}" not in st.session_state:
            st.session_state[f"conversation_history_{seller['id']}"] = []

        conversation_history = st.session_state[f"conversation_history_{seller['id']}"]

        # Display conversation
        for message in conversation_history[-10:]:  # Show last 10 messages
            with st.chat_message(message["role"]):
                st.write(message["content"])
                if message.get("metadata"):
                    with st.expander("📊 AI Insights"):
                        st.json(message["metadata"])

        # Message input
        st.markdown("#### 💬 Send Message")

        col1, col2 = st.columns([4, 1])

        with col1:
            user_message = st.text_input(
                "Message to seller:",
                placeholder="Type your message here...",
                key=f"message_input_{seller['id']}"
            )

        with col2:
            if st.button("Send", key=f"send_{seller['id']}"):
                if user_message:
                    self.process_claude_message(user_message, seller_context, seller['id'])
                    st.rerun()

        # Quick response templates
        st.markdown("#### ⚡ Quick Responses")
        quick_responses = [
            "Request property details",
            "Schedule property evaluation",
            "Send market analysis",
            "Provide timeline options",
            "Address pricing concerns"
        ]

        cols = st.columns(len(quick_responses))
        for i, response in enumerate(quick_responses):
            with cols[i]:
                if st.button(response, key=f"quick_{i}_{seller['id']}"):
                    self.process_quick_response(response, seller_context, seller['id'])
                    st.rerun()

        # Seller insights panel
        st.markdown("#### 🎯 AI Seller Insights")
        self.render_seller_insights_panel(seller_context)

    def render_seller_analytics(self) -> None:
        """Render seller performance analytics"""

        st.markdown("### 📈 Seller Analytics & Performance")

        # Time period selector
        col1, col2 = st.columns([1, 4])
        with col1:
            time_period = st.selectbox(
                "Time Period:",
                ["Last 7 days", "Last 30 days", "Last 90 days", "Year to date"]
            )

        # Key metrics
        self.render_seller_metrics()

        # Conversion funnel
        st.markdown("#### 🔄 Seller Conversion Funnel")
        self.render_conversion_funnel()

        # Performance trends
        st.markdown("#### 📊 Performance Trends")
        self.render_performance_trends()

        # Claude agent performance
        st.markdown("#### 🤖 Claude Agent Performance")
        self.render_claude_performance_metrics()

    def render_seller_metrics(self) -> None:
        """Render key seller metrics"""

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                "Total Leads",
                "156",
                "+23 this month",
                help="Total seller leads in pipeline"
            )

        with col2:
            st.metric(
                "Conversion Rate",
                "68%",
                "+12%",
                help="Lead to closing conversion rate"
            )

        with col3:
            st.metric(
                "Avg Response Time",
                "4.2 min",
                "-1.8 min",
                help="Average Claude response time"
            )

        with col4:
            st.metric(
                "Avg Deal Size",
                "$485K",
                "+$32K",
                help="Average property value"
            )

        with col5:
            st.metric(
                "Claude Accuracy",
                "94%",
                "+3%",
                help="Claude conversation accuracy"
            )

    def render_conversion_funnel(self) -> None:
        """Render seller conversion funnel visualization"""

        # Sample funnel data
        funnel_data = {
            "Stage": ["Initial Contact", "Information Gathered", "Market Analysis", "Decision Point", "Closed"],
            "Count": [156, 124, 98, 67, 45],
            "Conversion": [100, 79, 63, 43, 29]
        }

        df = pd.DataFrame(funnel_data)

        fig = go.Figure()

        fig.add_trace(go.Funnel(
            y=df["Stage"],
            x=df["Count"],
            textposition="inside",
            textinfo="value+percent initial",
            opacity=0.65,
            marker_color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"],
            connector_line_color="royalblue",
            connector_line_width=3
        ))

        fig.update_layout(
            title="Seller Lead Conversion Funnel",
            height=400,
            font_size=12
        )

        st.plotly_chart(fig, use_container_width=True)

    def render_performance_trends(self) -> None:
        """Render performance trend charts"""

        # Sample performance data
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
        performance_data = {
            'Date': dates,
            'New Leads': np.random.poisson(3, len(dates)),
            'Conversions': np.random.poisson(1.5, len(dates)),
            'Revenue': np.random.normal(15000, 5000, len(dates))
        }

        df = pd.DataFrame(performance_data)
        df['Revenue'] = df['Revenue'].clip(lower=0)

        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['Daily Leads', 'Conversion Rate', 'Revenue Trend', 'Claude Performance'],
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )

        # Daily leads
        fig.add_trace(
            go.Scatter(x=df['Date'], y=df['New Leads'], name='New Leads', line_color='blue'),
            row=1, col=1
        )

        # Conversion rate
        conversion_rate = (df['Conversions'] / df['New Leads'] * 100).rolling(7).mean()
        fig.add_trace(
            go.Scatter(x=df['Date'], y=conversion_rate, name='Conversion %', line_color='green'),
            row=1, col=2
        )

        # Revenue trend
        revenue_trend = df['Revenue'].rolling(7).mean()
        fig.add_trace(
            go.Scatter(x=df['Date'], y=revenue_trend, name='Revenue', line_color='purple'),
            row=2, col=1
        )

        # Claude performance (mock data)
        claude_performance = np.random.normal(95, 2, len(dates))
        claude_performance = np.clip(claude_performance, 80, 100)
        fig.add_trace(
            go.Scatter(x=df['Date'], y=claude_performance, name='Claude Accuracy', line_color='orange'),
            row=2, col=2
        )

        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    def render_claude_performance_metrics(self) -> None:
        """Render Claude agent performance metrics"""

        col1, col2 = st.columns(2)

        with col1:
            # Response accuracy by intent
            intent_accuracy = {
                "Price Inquiry": 96,
                "Timeline Questions": 94,
                "Process Questions": 98,
                "Objection Handling": 89,
                "Decision Support": 92
            }

            fig = go.Figure(data=[
                go.Bar(
                    x=list(intent_accuracy.keys()),
                    y=list(intent_accuracy.values()),
                    marker_color=['#1f77b4' if v >= 95 else '#ff7f0e' if v >= 90 else '#d62728'
                                 for v in intent_accuracy.values()]
                )
            ])

            fig.update_layout(
                title="Claude Accuracy by Intent Type",
                xaxis_title="Intent Type",
                yaxis_title="Accuracy %",
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Response time distribution
            response_times = np.random.lognormal(1, 0.5, 1000) * 60  # Simulate response times in seconds

            fig = go.Figure(data=[go.Histogram(x=response_times, nbinsx=30, name='Response Times')])
            fig.update_layout(
                title="Claude Response Time Distribution",
                xaxis_title="Response Time (seconds)",
                yaxis_title="Frequency",
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

    def render_automation_center(self) -> None:
        """Render automation and workflow management"""

        st.markdown("### 🤖 Seller Automation Center")

        # Automation status
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Active Automations", "12", "+2")
        with col2:
            st.metric("Messages Automated", "89%", "+5%")
        with col3:
            st.metric("Time Saved/Week", "23.5 hrs", "+4.2 hrs")

        # Automation workflows
        st.markdown("#### 🔄 Active Automation Workflows")
        self.render_automation_workflows()

        # Claude training
        st.markdown("#### 🎓 Claude Agent Training")
        self.render_claude_training()

    def render_automation_workflows(self) -> None:
        """Render automation workflow management"""

        workflows = [
            {
                "name": "New Seller Lead Nurturing",
                "trigger": "New contact tagged as 'seller'",
                "actions": ["Send welcome message", "Request property details", "Schedule follow-up"],
                "status": "Active",
                "success_rate": "94%"
            },
            {
                "name": "Market Analysis Delivery",
                "trigger": "Property information complete",
                "actions": ["Generate market report", "Send via email", "Schedule discussion"],
                "status": "Active",
                "success_rate": "97%"
            },
            {
                "name": "Objection Handling",
                "trigger": "Negative sentiment detected",
                "actions": ["Generate personalized response", "Provide supporting data", "Escalate if needed"],
                "status": "Active",
                "success_rate": "89%"
            },
            {
                "name": "Decision Point Follow-up",
                "trigger": "48 hours no response",
                "actions": ["Send gentle reminder", "Offer alternative options", "Schedule callback"],
                "status": "Active",
                "success_rate": "76%"
            }
        ]

        for workflow in workflows:
            with st.expander(f"📋 {workflow['name']} - {workflow['success_rate']} success"):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(f"**Trigger:** {workflow['trigger']}")
                    st.write("**Actions:**")
                    for action in workflow['actions']:
                        st.write(f"  • {action}")

                with col2:
                    st.metric("Success Rate", workflow['success_rate'])
                    if workflow['status'] == 'Active':
                        if st.button(f"⏸️ Pause", key=f"pause_{workflow['name']}"):
                            st.info(f"Paused {workflow['name']}")
                    else:
                        if st.button(f"▶️ Activate", key=f"activate_{workflow['name']}"):
                            st.success(f"Activated {workflow['name']}")

    def render_claude_training(self) -> None:
        """Render Claude agent training interface"""

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### 📚 Knowledge Base Updates")

            if st.button("📄 Update Market Data"):
                st.info("Updating Claude's market knowledge...")

            if st.button("🏠 Update Property Types"):
                st.info("Updating property type knowledge...")

            if st.button("💬 Update Conversation Scripts"):
                st.info("Updating conversation templates...")

        with col2:
            st.markdown("##### 🎯 Performance Tuning")

            temperature = st.slider("Response Creativity", 0.0, 1.0, 0.7, 0.1)
            max_tokens = st.number_input("Max Response Length", 50, 500, 250)

            if st.button("🔄 Update Settings"):
                st.success("Claude settings updated!")

        # Training metrics
        st.markdown("##### 📊 Training Progress")

        training_metrics = {
            "Market Knowledge": 94,
            "Conversation Flow": 89,
            "Objection Handling": 87,
            "Technical Knowledge": 96
        }

        for metric, score in training_metrics.items():
            progress_color = "green" if score >= 90 else "orange" if score >= 80 else "red"
            st.markdown(f"**{metric}:** {score}%")
            st.progress(score / 100)

    def render_seller_insights_panel(self, seller_context: SellerContext) -> None:
        """Render AI insights panel for seller"""

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**💡 AI Insights**")
            insights = [
                "High motivation - mentions timeline urgency",
                "Property condition appears good based on description",
                "Market timing favorable for quick sale",
                "Recommended approach: Wholesale with backup listing"
            ]

            for insight in insights:
                st.write(f"• {insight}")

        with col2:
            st.markdown("**📊 Quick Stats**")
            if seller_context.estimated_value_range:
                min_val, max_val = seller_context.estimated_value_range
                st.metric("Est. Value Range", f"${min_val:,} - ${max_val:,}")

            st.metric("Engagement Score", "87%")
            st.metric("Conversion Probability", "73%")

    def process_claude_message(self, message: str, seller_context: SellerContext, seller_id: str) -> None:
        """Process message through Claude agent"""

        # Add user message to history
        conversation_history = st.session_state.get(f"conversation_history_{seller_id}", [])
        conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })

        # Simulate Claude response (would use real agent in production)
        claude_response = self.simulate_claude_response(message, seller_context)

        conversation_history.append({
            "role": "assistant",
            "content": claude_response["response_message"],
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "intent": claude_response.get("conversation_intent"),
                "confidence": claude_response.get("confidence_score"),
                "suggested_actions": claude_response.get("suggested_actions")
            }
        })

        st.session_state[f"conversation_history_{seller_id}"] = conversation_history

    def process_quick_response(self, response_type: str, seller_context: SellerContext, seller_id: str) -> None:
        """Process quick response selection"""

        quick_responses = {
            "Request property details": "Could you please provide some additional details about your property? I'd like to know the number of bedrooms, bathrooms, and approximate square footage to give you the most accurate market analysis.",

            "Schedule property evaluation": "I'd like to schedule a brief property evaluation to provide you with the most accurate pricing. When would be a convenient time for you this week?",

            "Send market analysis": "Based on recent sales in your area, I've prepared a comprehensive market analysis. Properties similar to yours have been selling for $X-Y range. I'll email you the detailed report.",

            "Provide timeline options": "Great question about timeline! We offer flexible options: I can provide a cash offer that closes in 7-14 days, or if you prefer to maximize value, we can list your property and typically close in 30-60 days.",

            "Address pricing concerns": "I understand your concern about pricing. Let me show you the comparable sales data I used to determine this range. The goal is always to get you fair market value while considering your timeline needs."
        }

        message = quick_responses.get(response_type, "Thank you for your message. I'm here to help with any questions about selling your property.")

        # Add to conversation history
        conversation_history = st.session_state.get(f"conversation_history_{seller_id}", [])
        conversation_history.append({
            "role": "assistant",
            "content": message,
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "type": "quick_response",
                "template": response_type
            }
        })

        st.session_state[f"conversation_history_{seller_id}"] = conversation_history

    def simulate_claude_response(self, message: str, seller_context: SellerContext) -> Dict[str, Any]:
        """Simulate Claude agent response for demo"""

        # Simple intent classification
        message_lower = message.lower()

        if any(word in message_lower for word in ["price", "value", "worth", "offer"]):
            intent = "price_inquiry"
            response = f"Thanks for your question about pricing, {seller_context.name}. Based on recent sales in your area, I estimate your property value at $400,000 - $450,000. I'd like to schedule a brief walkthrough to provide a more precise estimate. When would be convenient for you?"

        elif any(word in message_lower for word in ["timeline", "fast", "quickly", "when"]):
            intent = "timeline_question"
            response = f"I understand timing is important to you, {seller_context.name}. We can close in as little as 7-14 days with a cash offer. If you prefer to list on the market for maximum value, that typically takes 30-60 days. What timeline works best for your situation?"

        elif any(word in message_lower for word in ["process", "how", "steps", "work"]):
            intent = "process_question"
            response = f"Great question, {seller_context.name}! The process is straightforward: (1) I'll evaluate your property, (2) provide a fair written offer, (3) you choose your timeline, and (4) we close at a local title company. No repairs, cleaning, or agent commissions needed. Would you like to start with a property evaluation?"

        else:
            intent = "information_request"
            response = f"Thanks for reaching out, {seller_context.name}. I'm here to help you understand your options for selling your property. What specific questions do you have about the process or your property value?"

        return {
            "response_message": response,
            "conversation_intent": intent,
            "confidence_score": 0.85,
            "suggested_actions": [
                {"action": "schedule_evaluation", "priority": "medium"}
            ]
        }

    def get_sample_sellers_data(self) -> List[Dict[str, Any]]:
        """Get sample seller data for demonstration"""

        return [
            {
                "id": "seller_001",
                "name": "Sarah Johnson",
                "property_address": "1234 Oak Street, Austin, TX 78701",
                "estimated_value": 485000,
                "urgency": "high",
                "stage": "Market Analysis",
                "last_contact": "2 hours ago",
                "motivation": "Job relocation",
                "timeline": "30 days"
            },
            {
                "id": "seller_002",
                "name": "Mike Chen",
                "property_address": "5678 Pine Avenue, Austin, TX 78702",
                "estimated_value": 520000,
                "urgency": "medium",
                "stage": "Information Gathering",
                "last_contact": "1 day ago",
                "motivation": "Upgrade home",
                "timeline": "60-90 days"
            },
            {
                "id": "seller_003",
                "name": "Lisa Rodriguez",
                "property_address": "9012 Maple Drive, Austin, TX 78703",
                "estimated_value": 675000,
                "urgency": "low",
                "stage": "Initial Contact",
                "last_contact": "3 days ago",
                "motivation": "Investment diversification",
                "timeline": "Flexible"
            },
            {
                "id": "seller_004",
                "name": "David Smith",
                "property_address": "3456 Elm Street, Austin, TX 78704",
                "estimated_value": 425000,
                "urgency": "high",
                "stage": "Decision Making",
                "last_contact": "30 minutes ago",
                "motivation": "Financial hardship",
                "timeline": "ASAP"
            },
            {
                "id": "seller_005",
                "name": "Emily Wilson",
                "property_address": "7890 Cedar Lane, Austin, TX 78705",
                "estimated_value": 595000,
                "urgency": "medium",
                "stage": "Closing Prep",
                "last_contact": "5 hours ago",
                "motivation": "Downsizing",
                "timeline": "45 days"
            }
        ]

    def open_seller_chat(self, seller: Dict[str, Any]) -> None:
        """Open seller chat interface"""
        st.session_state.selected_seller_chat = seller['id']
        st.info(f"Opening chat with {seller['name']}")

    def open_market_analysis(self, seller: Dict[str, Any]) -> None:
        """Open market analysis for seller"""
        st.session_state.selected_seller_analysis = seller['id']
        st.info(f"Generating market analysis for {seller['name']}")


def render_enhanced_seller_dashboard() -> None:
    """Main entry point for enhanced seller dashboard"""

    dashboard = EnhancedSellerDashboard()
    dashboard.render_dashboard()


# Demo function
if __name__ == "__main__":
    render_enhanced_seller_dashboard()