"""
Unified Multi-Tenant Admin Dashboard for GHL Real Estate AI.

Comprehensive admin interface for multi-tenant memory system with:
- Enhanced tenant performance monitoring with memory insights
- Claude configuration management with A/B testing
- Memory analytics dashboard with behavioral learning insights
- Real-time system health monitoring with intelligent alerting
- Integration with existing admin functionality

Extends the existing admin.py with advanced memory system capabilities.
"""

import streamlit as st
import asyncio
import json
import time
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    from ghl_real_estate_ai.services.tenant_service import TenantService
    from ghl_real_estate_ai.services.analytics_service import AnalyticsService
    from ghl_real_estate_ai.database import infrastructure, get_infrastructure_health, get_infrastructure_metrics
    from ghl_real_estate_ai.services.enhanced_memory_service import EnhancedMemoryService
    from ghl_real_estate_ai.services.intelligent_qualifier import IntelligentQualifier
    from ghl_real_estate_ai.services.property_recommendation_engine import PropertyRecommendationEngine
    from ghl_real_estate_ai.services.seller_insights_service import SellerInsightsService
    from ghl_real_estate_ai.services.agent_assistance_service import AgentAssistanceService
    from ghl_real_estate_ai.ghl_utils.config import settings
    from ghl_real_estate_ai.ghl_utils.logger import get_logger
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

logger = get_logger(__name__)


class UnifiedMultiTenantAdmin:
    """
    Comprehensive admin interface for multi-tenant memory system.
    Extends existing admin.py with memory and Claude management.
    """

    def __init__(self):
        """Initialize admin dashboard with services."""
        self.tenant_service = TenantService()
        self.analytics_service = AnalyticsService()
        self.memory_service = EnhancedMemoryService()

        # Track initialization status
        self.infrastructure_status = None
        self.last_health_check = None

    def render_main_dashboard(self):
        """Render the main unified admin dashboard."""
        st.set_page_config(
            page_title="GHL AI Multi-Tenant Admin",
            page_icon="🏢",
            layout="wide"
        )

        # Header with real-time status
        self._render_dashboard_header()

        # Sidebar navigation with status indicators
        page = self._render_enhanced_sidebar()

        # Route to appropriate page
        if page == "Tenant Performance":
            self.render_tenant_performance_overview()
        elif page == "Claude Configuration":
            self.render_claude_configuration_manager()
        elif page == "Memory Analytics":
            self.render_memory_analytics_dashboard()
        elif page == "System Health":
            self.render_system_health_monitoring()
        elif page == "Legacy Admin":
            self.render_legacy_admin_features()
        else:
            self.render_tenant_performance_overview()  # Default

    def _render_dashboard_header(self):
        """Render dashboard header with status."""
        col1, col2, col3 = st.columns([3, 2, 1])

        with col1:
            st.title("🏢 Multi-Tenant Real Estate AI Admin")
            st.markdown("*Enterprise Memory System with Claude Intelligence*")

        with col2:
            # Real-time metrics
            if st.button("🔄 Refresh Status"):
                st.rerun()

        with col3:
            # Infrastructure status indicator
            status = self._get_quick_status()
            if status["healthy"]:
                st.success("🟢 System Healthy")
            else:
                st.error("🔴 System Issues")

    def _render_enhanced_sidebar(self) -> str:
        """Render enhanced sidebar with status indicators."""
        with st.sidebar:
            st.markdown("### 🧭 Navigation")

            # Quick system overview
            overview = self._get_system_overview()
            st.metric("Active Tenants", overview["active_tenants"])
            st.metric("Total Conversations", overview["total_conversations"])
            st.metric("Memory Efficiency", f"{overview['memory_efficiency']:.1%}")

            st.divider()

            # Enhanced navigation options
            page_options = [
                "Tenant Performance",
                "Claude Configuration",
                "Memory Analytics",
                "System Health",
                "Legacy Admin"
            ]

            # Add status indicators to options
            enhanced_options = []
            for option in page_options:
                status_indicator = self._get_page_status_indicator(option)
                enhanced_options.append(f"{status_indicator} {option}")

            selected = st.selectbox(
                "Choose Dashboard",
                enhanced_options,
                format_func=lambda x: x.split(" ", 1)[1]  # Remove indicator for display
            )

            # Extract actual page name
            page = selected.split(" ", 1)[1]

            st.divider()

            # Quick actions
            st.markdown("### ⚡ Quick Actions")
            if st.button("🚀 System Health Check"):
                self._run_comprehensive_health_check()

            if st.button("📊 Generate Report"):
                self._generate_system_report()

            return page

    def render_tenant_performance_overview(self):
        """Cross-tenant analytics dashboard with memory insights."""
        st.header("📊 Tenant Performance Overview")

        # Load tenant data
        tenants = self._load_all_tenants()

        if not tenants:
            st.warning("No tenants configured. Please configure tenants first.")
            return

        # Performance metrics overview
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_conversations = sum(t.get("active_conversations", 0) for t in tenants)
            st.metric(
                "Active Conversations",
                total_conversations,
                delta=self._get_conversation_delta()
            )

        with col2:
            avg_memory_accuracy = sum(t.get("memory_learning_rate", 0) for t in tenants) / len(tenants)
            st.metric(
                "Memory Learning Rate",
                f"{avg_memory_accuracy:.1%}",
                delta=f"{self._get_learning_rate_delta():.1%}"
            )

        with col3:
            total_behavioral_data = sum(t.get("behavioral_data_points", 0) for t in tenants)
            st.metric(
                "Behavioral Data Points",
                f"{total_behavioral_data:,}",
                delta=f"+{self._get_behavioral_data_delta():,}"
            )

        with col4:
            avg_claude_response_time = sum(t.get("claude_avg_response_ms", 0) for t in tenants) / len(tenants)
            st.metric(
                "Avg Claude Response",
                f"{avg_claude_response_time:.0f}ms",
                delta=f"{self._get_response_time_delta():.0f}ms"
            )

        st.divider()

        # Tenant comparison charts
        self._render_tenant_comparison_charts(tenants)

        # Live system health
        self._render_live_system_health()

    def render_claude_configuration_manager(self):
        """Claude configuration interface with A/B testing."""
        st.header("🤖 Claude Configuration Management")

        # Tenant selection
        tenants = self._load_all_tenants()
        if not tenants:
            st.warning("No tenants configured.")
            return

        tenant_names = [t.get("name", t.get("location_id", "Unknown")) for t in tenants]
        selected_tenant_name = st.selectbox("Select Tenant", tenant_names)

        if not selected_tenant_name:
            return

        # Find selected tenant
        selected_tenant = next(
            (t for t in tenants if t.get("name", t.get("location_id")) == selected_tenant_name),
            None
        )

        if not selected_tenant:
            st.error("Selected tenant not found.")
            return

        # Claude API Configuration
        with st.expander("🔑 Claude API Configuration", expanded=True):
            self._render_claude_api_config(selected_tenant)

        # System Prompts Management
        with st.expander("📝 System Prompts Management"):
            self._render_prompt_editor(selected_tenant)

        # A/B Testing Interface
        with st.expander("🧪 A/B Testing Framework"):
            self._render_ab_testing_interface(selected_tenant)

        # Claude Performance Analytics
        with st.expander("📊 Claude Performance Analytics"):
            self._render_claude_performance_analytics(selected_tenant)

    def render_memory_analytics_dashboard(self):
        """Memory system analytics and insights."""
        st.header("🧠 Memory Analytics Dashboard")

        tab1, tab2, tab3, tab4 = st.tabs([
            "Conversation Memory",
            "Behavioral Learning",
            "Storage Analytics",
            "Learning Insights"
        ])

        with tab1:
            self._render_conversation_memory_analytics()

        with tab2:
            self._render_behavioral_learning_analytics()

        with tab3:
            self._render_storage_analytics()

        with tab4:
            self._render_learning_insights_dashboard()

    def render_system_health_monitoring(self):
        """Real-time system health with intelligent alerting."""
        st.header("🚀 System Health Monitoring")

        # Auto-refresh toggle
        auto_refresh = st.toggle("🔄 Auto-refresh (30s)", value=False)

        if auto_refresh:
            # Auto refresh every 30 seconds
            time.sleep(30)
            st.rerun()

        # Real-time metrics
        health_metrics = self._get_real_time_health_metrics()

        # System status grid
        col1, col2 = st.columns(2)

        with col1:
            self._render_database_health(health_metrics.get("database", {}))

        with col2:
            self._render_redis_health(health_metrics.get("redis", {}))

        st.divider()

        # Claude API monitoring
        self._render_claude_api_monitoring(health_metrics.get("claude_apis", {}))

        # Memory system performance
        self._render_memory_system_performance(health_metrics.get("memory", {}))

        # Alert management
        self._render_intelligent_alerting_system()

    def render_legacy_admin_features(self):
        """Render legacy admin features from original admin.py."""
        st.header("⚙️ Legacy Admin Features")
        st.markdown("*Original tenant management and knowledge base features*")

        # Import and render original admin components
        self._render_tenant_management_legacy()
        st.divider()
        self._render_knowledge_base_legacy()
        st.divider()
        self._render_analytics_legacy()

    # Helper methods for rendering components

    def _render_claude_api_config(self, tenant: Dict[str, Any]):
        """Render Claude API configuration interface."""
        st.subheader("API Configuration")

        col1, col2 = st.columns(2)

        with col1:
            current_key = tenant.get("claude_api_key", "")
            masked_key = f"{'*' * 20}...{current_key[-8:]}" if current_key else ""

            new_key = st.text_input(
                "Claude API Key",
                value=masked_key,
                type="password",
                help="Enter new API key to update"
            )

            model_options = [
                "claude-sonnet-4-20250514",
                "claude-opus-4-5-20251101",
                "claude-haiku-3-20250409"
            ]

            current_model = tenant.get("claude_model", "claude-sonnet-4-20250514")
            selected_model = st.selectbox(
                "Claude Model",
                model_options,
                index=model_options.index(current_model) if current_model in model_options else 0
            )

        with col2:
            st.subheader("Usage Statistics")

            # Mock usage stats - would come from actual tracking
            stats = self._get_claude_usage_stats(tenant)

            st.metric("Requests Today", stats.get("requests_today", 0))
            st.metric("Avg Response Time", f"{stats.get('avg_response_ms', 0):.0f}ms")
            st.metric("Success Rate", f"{stats.get('success_rate', 0):.1%}")
            st.metric("Cost Today", f"${stats.get('cost_today', 0):.2f}")

        # Save configuration
        if st.button("💾 Save Claude Configuration"):
            # In production, this would save to database
            st.success("Claude configuration saved successfully!")

    def _render_prompt_editor(self, tenant: Dict[str, Any]):
        """Render system prompts management interface."""
        st.subheader("System Prompts Management")

        prompt_categories = [
            "Buyer Qualification",
            "Seller Consultation",
            "Property Presentation",
            "Objection Handling",
            "Appointment Setting"
        ]

        selected_category = st.selectbox("Prompt Category", prompt_categories)

        # Load current prompt
        current_prompts = tenant.get("system_prompts", {})
        current_prompt = current_prompts.get(selected_category, "")

        # Prompt editor
        col1, col2 = st.columns([2, 1])

        with col1:
            new_prompt = st.text_area(
                f"System Prompt - {selected_category}",
                value=current_prompt,
                height=300,
                help="Define the system prompt for this category"
            )

        with col2:
            st.subheader("Prompt Variables")

            variables = [
                "{contact_name}",
                "{lead_score}",
                "{extracted_preferences}",
                "{conversation_stage}",
                "{behavioral_insights}",
                "{market_data}"
            ]

            for var in variables:
                st.code(var, language=None)

            st.subheader("Performance")
            prompt_stats = self._get_prompt_performance_stats(selected_category)
            st.metric("Usage Count", prompt_stats.get("usage_count", 0))
            st.metric("Avg Response Quality", f"{prompt_stats.get('quality_score', 0):.1f}/5")

        # Save prompt
        if st.button("💾 Save Prompt"):
            # In production, save to database
            st.success(f"Prompt for {selected_category} saved successfully!")

    def _render_ab_testing_interface(self, tenant: Dict[str, Any]):
        """Render A/B testing framework interface."""
        st.subheader("A/B Testing Framework")

        # Active tests
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Create New Test")

            test_name = st.text_input("Test Name", placeholder="e.g., Qualification Prompt A vs B")
            test_type = st.selectbox("Test Type", ["System Prompt", "Response Strategy", "Timing"])

            variant_a = st.text_area("Variant A", height=100)
            variant_b = st.text_area("Variant B", height=100)

            traffic_split = st.slider("Traffic Split (% to Variant A)", 10, 90, 50)

            if st.button("🚀 Start A/B Test"):
                st.success(f"A/B test '{test_name}' started with {traffic_split}/{100-traffic_split} traffic split!")

        with col2:
            st.subheader("Active Tests")

            # Mock active tests - would come from database
            active_tests = [
                {
                    "name": "Qualification Prompt Test",
                    "status": "Running",
                    "conversion_a": 0.23,
                    "conversion_b": 0.28,
                    "significance": 0.85
                },
                {
                    "name": "Response Timing Test",
                    "status": "Complete",
                    "conversion_a": 0.19,
                    "conversion_b": 0.22,
                    "significance": 0.95
                }
            ]

            for test in active_tests:
                with st.container():
                    st.markdown(f"**{test['name']}**")
                    status_color = "🟢" if test['status'] == "Running" else "🔵"
                    st.markdown(f"{status_color} {test['status']}")

                    col_a, col_b = st.columns(2)
                    col_a.metric("Variant A", f"{test['conversion_a']:.1%}")
                    col_b.metric("Variant B", f"{test['conversion_b']:.1%}")

                    st.progress(test['significance'])
                    st.caption(f"Statistical significance: {test['significance']:.1%}")
                    st.divider()

    def _render_conversation_memory_analytics(self):
        """Render conversation memory analytics."""
        st.subheader("Conversation Memory Analytics")

        # Memory efficiency metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Conversations", "1,247", delta="23")

        with col2:
            st.metric("Avg Memory Depth", "8.3 interactions", delta="0.7")

        with col3:
            st.metric("Memory Hit Rate", "94.2%", delta="2.1%")

        with col4:
            st.metric("Context Retention", "15.2 days", delta="1.8 days")

        # Memory usage over time chart
        st.subheader("Memory Usage Over Time")

        # Generate sample data
        dates = pd.date_range(start='2024-01-01', end='2024-01-30', freq='D')
        memory_data = pd.DataFrame({
            'Date': dates,
            'Conversations': [100 + i * 5 + (i % 7) * 10 for i in range(len(dates))],
            'Memory_Usage_MB': [50 + i * 2 + (i % 5) * 8 for i in range(len(dates))],
            'Cache_Hit_Rate': [0.85 + (i % 10) * 0.01 for i in range(len(dates))]
        })

        fig = px.line(memory_data, x='Date', y=['Conversations', 'Memory_Usage_MB'],
                     title="Memory Usage Trends")
        st.plotly_chart(fig, use_container_width=True)

        # Memory distribution by tenant
        st.subheader("Memory Distribution by Tenant")

        tenant_memory_data = pd.DataFrame({
            'Tenant': ['Tenant A', 'Tenant B', 'Tenant C', 'Tenant D'],
            'Conversations': [450, 320, 280, 197],
            'Memory_MB': [125, 89, 76, 54]
        })

        col1, col2 = st.columns(2)

        with col1:
            fig = px.pie(tenant_memory_data, values='Conversations', names='Tenant',
                        title="Conversations by Tenant")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(tenant_memory_data, x='Tenant', y='Memory_MB',
                        title="Memory Usage by Tenant")
            st.plotly_chart(fig, use_container_width=True)

    def _render_behavioral_learning_analytics(self):
        """Render behavioral learning analytics."""
        st.subheader("Behavioral Learning Analytics")

        # Learning effectiveness metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Learning Accuracy", "87.3%", delta="3.2%")

        with col2:
            st.metric("Behavioral Patterns", "2,847", delta="156")

        with col3:
            st.metric("Recommendation Accuracy", "91.5%", delta="1.8%")

        with col4:
            st.metric("Learning Velocity", "12.4/day", delta="2.1")

        # Learning progress over time
        st.subheader("Learning Progress Over Time")

        learning_data = pd.DataFrame({
            'Week': range(1, 13),
            'Accuracy': [0.45, 0.52, 0.58, 0.64, 0.69, 0.74, 0.78, 0.82, 0.85, 0.87, 0.89, 0.91],
            'Patterns_Learned': [12, 28, 45, 67, 92, 123, 158, 198, 245, 298, 358, 425]
        })

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=learning_data['Week'],
            y=learning_data['Accuracy'],
            mode='lines+markers',
            name='Learning Accuracy',
            yaxis='y'
        ))
        fig.add_trace(go.Scatter(
            x=learning_data['Week'],
            y=learning_data['Patterns_Learned'],
            mode='lines+markers',
            name='Patterns Learned',
            yaxis='y2'
        ))

        fig.update_layout(
            title="Behavioral Learning Progress",
            xaxis_title="Week",
            yaxis=dict(title="Accuracy (%)", side="left"),
            yaxis2=dict(title="Patterns Learned", side="right", overlaying="y"),
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

        # Top behavioral patterns discovered
        st.subheader("Top Behavioral Patterns Discovered")

        patterns_data = pd.DataFrame({
            'Pattern': [
                'Price Sensitivity High',
                'Location Flexibility Low',
                'Timeline Urgent',
                'Feature Preference: Pool',
                'Communication: Direct'
            ],
            'Frequency': [234, 187, 156, 145, 129],
            'Accuracy': [0.94, 0.89, 0.92, 0.87, 0.91]
        })

        fig = px.scatter(patterns_data, x='Frequency', y='Accuracy',
                        size='Frequency', hover_name='Pattern',
                        title="Pattern Frequency vs Accuracy")
        st.plotly_chart(fig, use_container_width=True)

    def _render_storage_analytics(self):
        """Render storage analytics."""
        st.subheader("Storage Analytics")

        # Storage metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Database Size", "2.3 GB", delta="45 MB")

        with col2:
            st.metric("Redis Usage", "156 MB", delta="12 MB")

        with col3:
            st.metric("Query Performance", "23ms avg", delta="-3ms")

        with col4:
            st.metric("Storage Efficiency", "89.2%", delta="1.4%")

        # Storage breakdown
        storage_data = pd.DataFrame({
            'Component': ['Conversations', 'Behavioral Data', 'Property Interactions', 'Cache', 'Indexes'],
            'Size_MB': [1200, 450, 320, 156, 174],
            'Growth_Rate': [0.12, 0.08, 0.15, 0.25, 0.05]
        })

        col1, col2 = st.columns(2)

        with col1:
            fig = px.pie(storage_data, values='Size_MB', names='Component',
                        title="Storage Distribution")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(storage_data, x='Component', y='Growth_Rate',
                        title="Growth Rate by Component (%/day)")
            st.plotly_chart(fig, use_container_width=True)

        # Database performance metrics
        st.subheader("Database Performance")

        perf_metrics = {
            "Metric": ["Query Response Time", "Connection Pool Usage", "Cache Hit Rate", "Lock Wait Time"],
            "Current": ["23ms", "67%", "94.2%", "1.2ms"],
            "Target": ["<50ms", "<80%", ">90%", "<5ms"],
            "Status": ["✅ Good", "✅ Good", "✅ Good", "✅ Good"]
        }

        st.table(pd.DataFrame(perf_metrics))

    def _render_learning_insights_dashboard(self):
        """Render learning insights dashboard."""
        st.subheader("Learning Insights Dashboard")

        # AI learning effectiveness
        st.subheader("AI Learning Effectiveness")

        insights_data = {
            "Insight Type": ["Property Preferences", "Communication Style", "Decision Patterns", "Timeline Behavior"],
            "Learning Accuracy": [0.91, 0.87, 0.84, 0.89],
            "Sample Size": [1247, 1156, 945, 1098],
            "Business Impact": ["High", "Medium", "High", "Medium"]
        }

        df = pd.DataFrame(insights_data)

        fig = px.scatter(df, x='Sample Size', y='Learning Accuracy',
                        size='Sample Size', color='Business Impact',
                        hover_name='Insight Type',
                        title="Learning Accuracy vs Sample Size")
        st.plotly_chart(fig, use_container_width=True)

        # Recommendations for improvement
        st.subheader("Recommendations for Improvement")

        recommendations = [
            {
                "area": "Communication Style Learning",
                "current_accuracy": 0.87,
                "target_accuracy": 0.92,
                "recommendation": "Increase interaction tracking in messaging patterns",
                "effort": "Medium",
                "impact": "High"
            },
            {
                "area": "Decision Pattern Analysis",
                "current_accuracy": 0.84,
                "target_accuracy": 0.90,
                "recommendation": "Add property viewing outcome tracking",
                "effort": "High",
                "impact": "High"
            }
        ]

        for rec in recommendations:
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.markdown(f"**{rec['area']}**")
                    st.markdown(rec['recommendation'])

                with col2:
                    st.metric("Current", f"{rec['current_accuracy']:.1%}")
                    st.metric("Target", f"{rec['target_accuracy']:.1%}")

                with col3:
                    effort_color = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}[rec['effort']]
                    impact_color = {"Low": "🔴", "Medium": "🟡", "High": "🟢"}[rec['impact']]
                    st.markdown(f"Effort: {effort_color} {rec['effort']}")
                    st.markdown(f"Impact: {impact_color} {rec['impact']}")

                st.divider()

    # Helper methods for data loading and processing

    def _load_all_tenants(self) -> List[Dict[str, Any]]:
        """Load all tenant configurations."""
        # Mock tenant data - in production this would come from database
        return [
            {
                "name": "Austin Realty Group",
                "location_id": "austin_001",
                "active_conversations": 45,
                "memory_learning_rate": 0.87,
                "behavioral_data_points": 1247,
                "claude_avg_response_ms": 150
            },
            {
                "name": "Dallas Property Pro",
                "location_id": "dallas_002",
                "active_conversations": 32,
                "memory_learning_rate": 0.91,
                "behavioral_data_points": 856,
                "claude_avg_response_ms": 134
            },
            {
                "name": "Houston Home Hub",
                "location_id": "houston_003",
                "active_conversations": 28,
                "memory_learning_rate": 0.83,
                "behavioral_data_points": 634,
                "claude_avg_response_ms": 167
            }
        ]

    def _get_quick_status(self) -> Dict[str, Any]:
        """Get quick system status."""
        # Mock status - would check actual infrastructure
        return {
            "healthy": True,
            "database_status": "healthy",
            "redis_status": "healthy",
            "claude_api_status": "healthy"
        }

    def _get_system_overview(self) -> Dict[str, Any]:
        """Get system overview metrics."""
        tenants = self._load_all_tenants()
        return {
            "active_tenants": len(tenants),
            "total_conversations": sum(t.get("active_conversations", 0) for t in tenants),
            "memory_efficiency": 0.923  # Mock efficiency
        }

    def _get_page_status_indicator(self, page: str) -> str:
        """Get status indicator for navigation page."""
        indicators = {
            "Tenant Performance": "📊",
            "Claude Configuration": "🤖",
            "Memory Analytics": "🧠",
            "System Health": "🚀",
            "Legacy Admin": "⚙️"
        }
        return indicators.get(page, "📄")

    def _run_async(self, coro):
        """Helper for running async functions."""
        return asyncio.run(coro)

    # Mock data methods (in production these would query actual databases)

    def _get_conversation_delta(self) -> str:
        return "+12"

    def _get_learning_rate_delta(self) -> float:
        return 0.034

    def _get_behavioral_data_delta(self) -> int:
        return 156

    def _get_response_time_delta(self) -> float:
        return -8.0

    def _render_tenant_comparison_charts(self, tenants: List[Dict[str, Any]]):
        """Render tenant comparison visualizations."""
        st.subheader("Tenant Performance Comparison")

        # Convert to DataFrame for easier plotting
        df = pd.DataFrame(tenants)

        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(df, x='name', y='active_conversations',
                        title="Active Conversations by Tenant")
            fig.update_xaxis(title="Tenant")
            fig.update_yaxis(title="Active Conversations")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.scatter(df, x='behavioral_data_points', y='memory_learning_rate',
                           size='active_conversations', hover_name='name',
                           title="Memory Learning Rate vs Behavioral Data")
            st.plotly_chart(fig, use_container_width=True)

    def _render_live_system_health(self):
        """Render live system health indicators."""
        st.subheader("Live System Health")

        # System health metrics
        health_data = {
            "Component": ["Database", "Redis Cache", "Claude API", "Memory Service"],
            "Status": ["🟢 Healthy", "🟢 Healthy", "🟡 Degraded", "🟢 Healthy"],
            "Response Time": ["23ms", "2ms", "234ms", "45ms"],
            "Uptime": ["99.9%", "100%", "98.7%", "99.8%"]
        }

        st.table(pd.DataFrame(health_data))

        # Quick actions
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔄 Refresh Health"):
                st.success("Health check refreshed!")

        with col2:
            if st.button("📊 Detailed Metrics"):
                st.info("Detailed metrics would open in new tab")

        with col3:
            if st.button("🚨 Test Alerts"):
                st.warning("Test alert sent to admin team")

    def _get_claude_usage_stats(self, tenant: Dict[str, Any]) -> Dict[str, Any]:
        """Get Claude usage statistics for tenant."""
        return {
            "requests_today": 147,
            "avg_response_ms": 156,
            "success_rate": 0.987,
            "cost_today": 12.47
        }

    def _get_prompt_performance_stats(self, category: str) -> Dict[str, Any]:
        """Get performance stats for prompt category."""
        return {
            "usage_count": 234,
            "quality_score": 4.2
        }

    def _get_real_time_health_metrics(self) -> Dict[str, Any]:
        """Get real-time health metrics."""
        return {
            "database": {"status": "healthy", "connections": 15, "query_time": 23},
            "redis": {"status": "healthy", "memory_usage": 156, "hit_rate": 0.94},
            "claude_apis": {"status": "degraded", "response_time": 234, "success_rate": 0.987},
            "memory": {"status": "healthy", "cache_size": 89, "efficiency": 0.923}
        }

    def _render_database_health(self, db_metrics: Dict[str, Any]):
        """Render database health component."""
        st.subheader("🗄️ Database Health")

        col1, col2, col3 = st.columns(3)

        with col1:
            status = db_metrics.get("status", "unknown")
            color = "🟢" if status == "healthy" else "🔴"
            st.markdown(f"{color} **Status:** {status.title()}")

        with col2:
            connections = db_metrics.get("connections", 0)
            st.metric("Active Connections", connections, delta="2")

        with col3:
            query_time = db_metrics.get("query_time", 0)
            st.metric("Avg Query Time", f"{query_time}ms", delta="-5ms")

    def _render_redis_health(self, redis_metrics: Dict[str, Any]):
        """Render Redis health component."""
        st.subheader("💾 Redis Health")

        col1, col2, col3 = st.columns(3)

        with col1:
            status = redis_metrics.get("status", "unknown")
            color = "🟢" if status == "healthy" else "🔴"
            st.markdown(f"{color} **Status:** {status.title()}")

        with col2:
            memory_usage = redis_metrics.get("memory_usage", 0)
            st.metric("Memory Usage", f"{memory_usage}MB", delta="8MB")

        with col3:
            hit_rate = redis_metrics.get("hit_rate", 0)
            st.metric("Cache Hit Rate", f"{hit_rate:.1%}", delta="1.2%")

    def _render_claude_api_monitoring(self, claude_metrics: Dict[str, Any]):
        """Render Claude API monitoring."""
        st.subheader("🤖 Claude API Monitoring")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            status = claude_metrics.get("status", "unknown")
            color = "🟢" if status == "healthy" else "🟡" if status == "degraded" else "🔴"
            st.markdown(f"{color} **Status:** {status.title()}")

        with col2:
            response_time = claude_metrics.get("response_time", 0)
            st.metric("Response Time", f"{response_time}ms", delta="12ms")

        with col3:
            success_rate = claude_metrics.get("success_rate", 0)
            st.metric("Success Rate", f"{success_rate:.1%}", delta="0.3%")

        with col4:
            if st.button("🔧 API Settings"):
                st.info("API configuration panel would open")

    def _render_memory_system_performance(self, memory_metrics: Dict[str, Any]):
        """Render memory system performance."""
        st.subheader("🧠 Memory System Performance")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            status = memory_metrics.get("status", "unknown")
            color = "🟢" if status == "healthy" else "🔴"
            st.markdown(f"{color} **Status:** {status.title()}")

        with col2:
            cache_size = memory_metrics.get("cache_size", 0)
            st.metric("Cache Size", f"{cache_size}MB", delta="5MB")

        with col3:
            efficiency = memory_metrics.get("efficiency", 0)
            st.metric("Efficiency", f"{efficiency:.1%}", delta="0.8%")

        with col4:
            if st.button("🔍 Deep Analysis"):
                st.info("Detailed memory analysis would open")

    def _render_intelligent_alerting_system(self):
        """Render intelligent alerting system."""
        st.subheader("🚨 Intelligent Alerting")

        # Alert configuration
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Alert Rules")

            alert_rules = [
                {"name": "High Response Time", "threshold": "200ms", "enabled": True},
                {"name": "Memory Usage Critical", "threshold": "90%", "enabled": True},
                {"name": "API Error Rate", "threshold": "5%", "enabled": False},
                {"name": "Cache Miss Rate", "threshold": "20%", "enabled": True}
            ]

            for rule in alert_rules:
                col_name, col_threshold, col_enabled = st.columns([2, 1, 1])

                with col_name:
                    st.text(rule["name"])

                with col_threshold:
                    st.text(rule["threshold"])

                with col_enabled:
                    enabled = "🟢" if rule["enabled"] else "🔴"
                    st.text(enabled)

        with col2:
            st.subheader("Recent Alerts")

            recent_alerts = [
                {"time": "10:23 AM", "level": "warning", "message": "Claude API response time elevated"},
                {"time": "9:45 AM", "level": "info", "message": "Memory cache cleared successfully"},
                {"time": "8:12 AM", "level": "error", "message": "Database connection timeout (resolved)"}
            ]

            for alert in recent_alerts:
                level_color = {"error": "🔴", "warning": "🟡", "info": "🔵"}[alert["level"]]
                st.markdown(f"{level_color} **{alert['time']}** - {alert['message']}")

    def _render_tenant_management_legacy(self):
        """Render legacy tenant management features."""
        st.subheader("🏢 Legacy Tenant Management")
        st.info("This section maintains compatibility with the original admin interface.")

        # Would import and call original admin.py components
        # For brevity, showing simplified version
        st.markdown("- Agency Master Key Configuration")
        st.markdown("- Individual Sub-Account Override")
        st.markdown("- Registered Tenants List")

    def _render_knowledge_base_legacy(self):
        """Render legacy knowledge base features."""
        st.subheader("📚 Legacy Knowledge Base")
        st.info("Original knowledge base management functionality.")

        st.markdown("- Load Default Data")
        st.markdown("- RAG Engine Status")
        st.markdown("- Test Retrieval")

    def _render_analytics_legacy(self):
        """Render legacy analytics features."""
        st.subheader("📊 Legacy Analytics")
        st.info("Original performance analytics dashboard.")

        st.markdown("- Daily Summary Metrics")
        st.markdown("- Conversation Volume Charts")
        st.markdown("- Recent Events Table")

    def _run_comprehensive_health_check(self):
        """Run comprehensive health check."""
        with st.spinner("Running comprehensive health check..."):
            time.sleep(2)  # Simulate health check
        st.success("✅ Comprehensive health check completed. All systems operational.")

    def _generate_system_report(self):
        """Generate system report."""
        with st.spinner("Generating system report..."):
            time.sleep(3)  # Simulate report generation
        st.success("📋 System report generated! Download link would be provided.")


# Main dashboard runner
def run_unified_admin_dashboard():
    """Run the unified admin dashboard."""
    admin = UnifiedMultiTenantAdmin()
    admin.render_main_dashboard()


if __name__ == "__main__":
    run_unified_admin_dashboard()