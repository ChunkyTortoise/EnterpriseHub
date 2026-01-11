"""
Claude Integration Templates
=============================

Ready-to-use templates for integrating Claude AI capabilities into
different types of Streamlit components.

Templates for:
- Dashboard components (analytics, monitoring, business intelligence)
- Data components (lead management, property matching)
- Coaching components (real-time coaching, training)
- Workflow components (campaigns, nurturing)

Author: EnterpriseHub Development Team
Date: January 2026
Version: 1.0.0
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass


class ComponentCategory(Enum):
    """Categories of Streamlit components."""
    DASHBOARD = "dashboard"
    DATA_VISUALIZATION = "data_visualization"
    COACHING = "coaching"
    WORKFLOW = "workflow"
    ANALYTICS = "analytics"
    MONITORING = "monitoring"
    LEAD_MANAGEMENT = "lead_management"
    PROPERTY = "property"


@dataclass
class IntegrationTemplate:
    """Template for Claude integration."""
    category: ComponentCategory
    imports: str
    mixin_initialization: str
    example_methods: str
    ui_rendering: str
    performance_considerations: str


class ClaudeIntegrationTemplates:
    """
    Collection of templates for integrating Claude AI into Streamlit components.

    Each template provides:
    - Required imports
    - Mixin initialization code
    - Example integration methods
    - UI rendering patterns
    - Performance optimization tips
    """

    # =========================================================================
    # Dashboard Template - For analytics and monitoring dashboards
    # =========================================================================

    DASHBOARD_TEMPLATE = IntegrationTemplate(
        category=ComponentCategory.DASHBOARD,
        imports='''
# === CLAUDE AI INTEGRATION ===
from .claude_component_mixin import (
    ClaudeComponentMixin,
    ClaudeOperationType,
    ClaudeServiceStatus,
    ClaudePerformanceStats
)

# === ENTERPRISE BASE ===
from .enhanced_enterprise_base import (
    EnterpriseDashboardComponent,
    ComponentMetrics
)

# === CACHE INTEGRATION ===
from .streamlit_cache_integration import (
    StreamlitCacheIntegration,
    ComponentCacheConfig
)
''',

        mixin_initialization='''
class MyDashboard(EnterpriseDashboardComponent, ClaudeComponentMixin):
    """
    Dashboard component with Claude AI integration.

    Features:
    - AI-powered executive summaries
    - Intelligent trend analysis
    - Natural language data explanations
    - Predictive insights
    """

    def __init__(self, demo_mode: bool = False):
        """Initialize dashboard with Claude AI capabilities."""
        # Initialize enterprise base
        EnterpriseDashboardComponent.__init__(
            self,
            component_id="my_dashboard",
            theme_variant=ThemeVariant.ENTERPRISE_LIGHT,
            enable_metrics=True,
            enable_caching=True
        )

        # Initialize Claude integration
        ClaudeComponentMixin.__init__(
            self,
            enable_claude_caching=True,
            cache_ttl_seconds=300,  # 5 minutes
            enable_performance_monitoring=True,
            demo_mode=demo_mode
        )

        # Initialize cache for performance
        self.cache = StreamlitCacheIntegration(
            component_id="my_dashboard",
            config=ComponentCacheConfig(
                component_id="my_dashboard",
                default_ttl_seconds=300
            )
        )
''',

        example_methods='''
    async def render_ai_summary(self, data: Dict[str, Any]) -> None:
        """Render AI-powered executive summary."""
        # Generate summary using Claude
        summary = await self.generate_executive_summary(
            data=data,
            context="business_intelligence",
            tone="executive",
            max_length=300
        )

        if summary.get('fallback_mode'):
            self.create_status_indicator(
                status="warning",
                message="AI summary in fallback mode",
                show_icon=True
            )
        else:
            # Render AI insights card
            self.create_info_card(
                content=f"""
                    <h4>AI Executive Summary</h4>
                    <p>{summary.get('summary', 'No summary available')}</p>
                    <h5>Key Insights</h5>
                    <ul>
                        {''.join(f'<li>{insight}</li>' for insight in summary.get('key_insights', []))}
                    </ul>
                """,
                title="Claude AI Analysis",
                variant="elevated",
                icon="🤖"
            )

    async def render_trend_analysis(self, metrics: List[Dict]) -> None:
        """Render AI-powered trend analysis."""
        # Get AI explanation of trends
        explanation = await self.explain_model_prediction(
            prediction={
                'metrics': metrics,
                'type': 'trend_analysis'
            },
            model_type="performance_prediction",
            include_factors=True
        )

        with st.expander("🔮 AI Trend Analysis", expanded=True):
            st.markdown(f"**Analysis:** {explanation.get('explanation', '')}")

            if explanation.get('key_factors'):
                st.markdown("**Contributing Factors:**")
                for factor in explanation['key_factors']:
                    st.markdown(f"- **{factor['factor']}** ({factor['contribution']:.0%}): {factor['description']}")

            if explanation.get('recommendations'):
                st.markdown("**Recommendations:**")
                for rec in explanation['recommendations']:
                    st.info(rec)
''',

        ui_rendering='''
    def render_claude_status_panel(self) -> None:
        """Render Claude AI status panel in sidebar."""
        with st.sidebar:
            st.markdown("### AI Status")
            self.render_claude_status_badge()

            # Show performance stats
            stats = self.get_claude_performance_stats()
            if stats:
                st.markdown("**Performance:**")
                for op_type, op_stats in stats.items():
                    with st.expander(f"{op_type}"):
                        st.write(f"- Calls: {op_stats.get('total_operations', 0)}")
                        st.write(f"- Success: {op_stats.get('success_rate', '0%')}")
                        st.write(f"- Latency: {op_stats.get('avg_latency_ms', '0ms')}")
''',

        performance_considerations='''
    """
    Performance Optimization Guidelines for Dashboard Integration:

    1. CACHING STRATEGY
       - Use cache_ttl_seconds=300 for executive summaries (5 min refresh)
       - Use cache_ttl_seconds=60 for real-time coaching (1 min max)
       - Use cache_ttl_seconds=600 for historical analysis (10 min)

    2. ASYNC PATTERNS
       - Use asyncio.gather() for parallel Claude operations
       - Implement progressive loading for large datasets
       - Use background refresh for non-critical insights

    3. FALLBACK HANDLING
       - Always check for fallback_mode in responses
       - Provide meaningful fallback UI for degraded state
       - Log fallback occurrences for monitoring

    4. RESOURCE MANAGEMENT
       - Limit concurrent Claude operations to 3-5
       - Implement request queuing for heavy load
       - Use lazy loading for AI features

    Example of parallel operations:
    ```python
    async def render_all_insights(self, data: Dict) -> None:
        # Run Claude operations in parallel
        summary_task = self.generate_executive_summary(data)
        trend_task = self.explain_model_prediction(data['predictions'])
        question_task = self.get_intelligent_questions(data['lead'])

        summary, trends, questions = await asyncio.gather(
            summary_task,
            trend_task,
            question_task
        )

        # Render results
        self._render_summary(summary)
        self._render_trends(trends)
        self._render_questions(questions)
    ```
    """
'''
    )

    # =========================================================================
    # Coaching Template - For real-time agent coaching
    # =========================================================================

    COACHING_TEMPLATE = IntegrationTemplate(
        category=ComponentCategory.COACHING,
        imports='''
# === CLAUDE AI COACHING ===
from .claude_component_mixin import (
    ClaudeComponentMixin,
    ClaudeOperationType,
    ClaudeServiceStatus
)

# === COACHING ENGINE ===
from ..services.ai_powered_coaching_engine import (
    AIPoweredCoachingEngine,
    CoachingSession,
    CoachingAlert,
    get_coaching_engine
)

# === ENTERPRISE BASE ===
from .enhanced_enterprise_base import (
    EnhancedEnterpriseComponent,
    ComponentState
)
''',

        mixin_initialization='''
class CoachingDashboard(EnhancedEnterpriseComponent, ClaudeComponentMixin):
    """
    Real-time coaching dashboard with Claude AI integration.

    Features:
    - Live conversation coaching suggestions
    - Objection detection and response recommendations
    - Intelligent question suggestions
    - Performance tracking and improvement tips
    """

    def __init__(self, agent_id: str, demo_mode: bool = False):
        """Initialize coaching dashboard."""
        EnhancedEnterpriseComponent.__init__(
            self,
            component_id=f"coaching_{agent_id}",
            enable_metrics=True,
            enable_caching=True
        )

        ClaudeComponentMixin.__init__(
            self,
            enable_claude_caching=True,
            cache_ttl_seconds=60,  # Short TTL for coaching
            enable_performance_monitoring=True,
            demo_mode=demo_mode
        )

        self.agent_id = agent_id
        self.coaching_engine = get_coaching_engine()
''',

        example_methods='''
    async def get_live_coaching(
        self,
        conversation_context: Dict[str, Any],
        latest_message: str,
        stage: str = "discovery"
    ) -> Dict[str, Any]:
        """Get real-time coaching suggestions."""
        return await self.get_real_time_coaching(
            agent_id=self.agent_id,
            conversation_context=conversation_context,
            prospect_message=latest_message,
            conversation_stage=stage,
            use_cache=True
        )

    async def analyze_conversation(
        self,
        messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze conversation for coaching insights."""
        return await self.analyze_lead_semantics(
            conversation_messages=messages,
            include_preferences=True,
            include_qualification=True,
            use_cache=True
        )

    async def get_next_questions(
        self,
        lead_profile: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Get intelligent next questions."""
        return await self.get_intelligent_questions(
            lead_profile=lead_profile,
            conversation_context=context,
            max_questions=5
        )
''',

        ui_rendering='''
    def render_live_coaching_panel(
        self,
        coaching: Dict[str, Any]
    ) -> None:
        """Render live coaching suggestions panel."""
        # Coaching suggestions
        with st.container():
            st.markdown("### 🎯 Live Coaching Suggestions")

            # Check for objection
            if coaching.get('objection_detected'):
                st.error(f"⚠️ Objection Detected: {coaching.get('objection_type', 'Unknown')}")

            # Recommended response
            if coaching.get('recommended_response'):
                st.success(f"**Suggested Response:**\\n{coaching['recommended_response']}")

            # Additional suggestions
            if coaching.get('suggestions'):
                st.markdown("**Coaching Tips:**")
                for tip in coaching['suggestions']:
                    st.markdown(f"- {tip}")

            # Next questions
            if coaching.get('next_questions'):
                st.markdown("**Consider Asking:**")
                for q in coaching['next_questions']:
                    st.info(f"💬 {q}")

    def render_qualification_progress(
        self,
        analysis: Dict[str, Any]
    ) -> None:
        """Render qualification progress from semantic analysis."""
        qual = analysis.get('qualification_assessment', {})
        score = qual.get('overall_qualification_score', 0)

        st.markdown("### 📊 Qualification Progress")

        # Progress bar
        st.progress(score / 100)
        st.markdown(f"**Overall Score:** {score}%")

        # Dimension breakdown
        dimensions = qual.get('qualification_dimensions', {})
        cols = st.columns(len(dimensions))

        for i, (dim, data) in enumerate(dimensions.items()):
            with cols[i]:
                st.metric(
                    label=dim.title(),
                    value=f"{data.get('score', 0)}%"
                )
''',

        performance_considerations='''
    """
    Performance Optimization for Coaching Integration:

    1. LATENCY REQUIREMENTS
       - Real-time coaching: < 100ms total round-trip
       - Use cache_ttl_seconds=60 for coaching (balance freshness vs speed)
       - Pre-fetch coaching for common objection patterns

    2. CACHING STRATEGY
       - Cache coaching by conversation stage + objection type
       - Use shorter cache for active conversations
       - Invalidate cache on conversation stage change

    3. BACKGROUND PROCESSING
       - Run semantic analysis in background while user types
       - Pre-compute next questions based on conversation flow
       - Use WebSocket for real-time updates

    4. GRACEFUL DEGRADATION
       - Always provide fallback coaching suggestions
       - Show cached suggestions while fetching new ones
       - Maintain responsive UI even when Claude is slow

    Example of optimized coaching flow:
    ```python
    async def optimized_coaching_flow(self, message: str) -> None:
        # Start coaching fetch immediately
        coaching_task = self.get_live_coaching(
            self.conversation_context,
            message
        )

        # Update UI with loading state
        with self.coaching_placeholder:
            st.spinner("Getting coaching suggestions...")

        # Wait for result with timeout
        try:
            coaching = await asyncio.wait_for(coaching_task, timeout=0.1)
            self._render_coaching(coaching)
        except asyncio.TimeoutError:
            # Show cached/fallback while waiting
            self._render_fallback_coaching()
            coaching = await coaching_task
            self._render_coaching(coaching)
    ```
    """
'''
    )

    # =========================================================================
    # Analytics Template - For data analysis components
    # =========================================================================

    ANALYTICS_TEMPLATE = IntegrationTemplate(
        category=ComponentCategory.ANALYTICS,
        imports='''
# === CLAUDE AI ANALYTICS ===
from .claude_component_mixin import (
    ClaudeComponentMixin,
    ClaudeOperationType
)

# === ENTERPRISE DATA COMPONENT ===
from .enhanced_enterprise_base import (
    EnterpriseDataComponent,
    ComponentMetrics
)
''',

        mixin_initialization='''
class AnalyticsDashboard(EnterpriseDataComponent, ClaudeComponentMixin):
    """
    Analytics dashboard with Claude AI-powered insights.

    Features:
    - Natural language data explanations
    - Trend interpretation
    - Anomaly detection and explanation
    - Recommendation generation
    """

    def __init__(self, demo_mode: bool = False):
        EnterpriseDataComponent.__init__(
            self,
            component_id="analytics_dashboard",
            enable_metrics=True,
            enable_caching=True
        )

        ClaudeComponentMixin.__init__(
            self,
            enable_claude_caching=True,
            cache_ttl_seconds=600,  # 10 minutes for analytics
            enable_performance_monitoring=True,
            demo_mode=demo_mode
        )
''',

        example_methods='''
    async def explain_data_trend(
        self,
        data: pd.DataFrame,
        metric_name: str
    ) -> Dict[str, Any]:
        """Generate natural language explanation of data trend."""
        # Prepare trend summary
        trend_data = {
            'metric': metric_name,
            'current_value': float(data[metric_name].iloc[-1]),
            'previous_value': float(data[metric_name].iloc[-2]),
            'min': float(data[metric_name].min()),
            'max': float(data[metric_name].max()),
            'mean': float(data[metric_name].mean()),
            'trend': 'up' if data[metric_name].iloc[-1] > data[metric_name].iloc[-2] else 'down'
        }

        return await self.explain_model_prediction(
            prediction=trend_data,
            model_type="trend_analysis",
            include_factors=True
        )

    async def detect_and_explain_anomalies(
        self,
        data: pd.DataFrame,
        column: str
    ) -> Dict[str, Any]:
        """Detect anomalies and provide AI explanation."""
        # Simple anomaly detection
        mean = data[column].mean()
        std = data[column].std()
        anomalies = data[abs(data[column] - mean) > 2 * std]

        if anomalies.empty:
            return {'has_anomalies': False, 'message': 'No anomalies detected'}

        return await self.generate_executive_summary(
            data={
                'anomaly_points': anomalies.to_dict(),
                'column': column,
                'threshold': f'{mean:.2f} +/- {2*std:.2f}'
            },
            context="anomaly_detection",
            tone="technical"
        )
''',

        ui_rendering='''
    def render_ai_insights_panel(
        self,
        insights: Dict[str, Any]
    ) -> None:
        """Render AI insights panel for analytics."""
        with st.expander("🤖 AI-Powered Insights", expanded=True):
            # Main insight
            if insights.get('explanation'):
                st.markdown(f"**Analysis:** {insights['explanation']}")

            # Key factors
            if insights.get('key_factors'):
                st.markdown("---")
                st.markdown("**Key Contributing Factors:**")
                for factor in insights['key_factors']:
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        st.metric(factor['factor'], f"{factor['contribution']:.0%}")
                    with col2:
                        st.write(factor['description'])

            # Recommendations
            if insights.get('recommendations'):
                st.markdown("---")
                st.markdown("**AI Recommendations:**")
                for i, rec in enumerate(insights['recommendations'], 1):
                    st.write(f"{i}. {rec}")
''',

        performance_considerations='''
    """
    Performance Optimization for Analytics Integration:

    1. CACHING STRATEGY
       - Use longer cache TTL (600s) for historical analysis
       - Cache by data hash to handle changing datasets
       - Implement incremental analysis for large datasets

    2. BATCH PROCESSING
       - Batch multiple metric explanations into single Claude call
       - Use background jobs for comprehensive analysis
       - Implement progressive insight loading

    3. DATA PREPARATION
       - Pre-aggregate data before sending to Claude
       - Limit data points to essential summary statistics
       - Use sampling for very large datasets
    """
'''
    )

    # =========================================================================
    # Property Template - For property-related components
    # =========================================================================

    PROPERTY_TEMPLATE = IntegrationTemplate(
        category=ComponentCategory.PROPERTY,
        imports='''
# === CLAUDE AI PROPERTY ANALYSIS ===
from .claude_component_mixin import (
    ClaudeComponentMixin,
    ClaudeOperationType
)

# === PROPERTY SERVICES ===
from ..services.property_valuation_engine import PropertyValuationEngine
''',

        mixin_initialization='''
class PropertyComponent(EnhancedEnterpriseComponent, ClaudeComponentMixin):
    """
    Property component with Claude AI-powered analysis.

    Features:
    - AI-powered valuation insights
    - Market trend interpretation
    - Comparable property analysis
    - Pricing strategy recommendations
    """

    def __init__(self, demo_mode: bool = False):
        EnhancedEnterpriseComponent.__init__(
            self,
            component_id="property_component",
            enable_metrics=True
        )

        ClaudeComponentMixin.__init__(
            self,
            enable_claude_caching=True,
            cache_ttl_seconds=300,
            enable_performance_monitoring=True,
            demo_mode=demo_mode
        )

        self.valuation_engine = PropertyValuationEngine()
''',

        example_methods='''
    async def get_valuation_insights(
        self,
        property_data: Dict[str, Any],
        market_data: Dict[str, Any],
        comparables: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get AI-powered valuation insights."""
        return await self.analyze_property_valuation(
            property_data=property_data,
            market_data=market_data,
            comparable_properties=comparables
        )

    async def explain_valuation(
        self,
        valuation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate natural language valuation explanation."""
        return await self.explain_model_prediction(
            prediction=valuation_result,
            model_type="property_valuation",
            include_factors=True
        )
''',

        ui_rendering='''
    def render_valuation_insights(
        self,
        insights: Dict[str, Any]
    ) -> None:
        """Render AI valuation insights."""
        st.markdown("### 🏠 AI Valuation Analysis")

        # Valuation summary
        if insights.get('valuation_summary'):
            st.info(insights['valuation_summary'])

        # Confidence range
        if insights.get('confidence_range'):
            range_data = insights['confidence_range']
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Low Estimate", f"${range_data['low']:,.0f}")
            with col2:
                st.metric("Mid Estimate", f"${range_data['mid']:,.0f}")
            with col3:
                st.metric("High Estimate", f"${range_data['high']:,.0f}")

        # Market insights
        if insights.get('market_insights'):
            st.markdown("**Market Insights:**")
            for insight in insights['market_insights']:
                st.write(f"- {insight}")

        # Pricing strategy
        if insights.get('pricing_strategy'):
            strategy = insights['pricing_strategy']
            st.success(f"**Recommended List Price:** ${strategy['recommended_list_price']:,.0f}")
            st.write(f"*{strategy['reasoning']}*")
''',

        performance_considerations='''
    """
    Performance Optimization for Property Integration:

    1. CACHING STRATEGY
       - Cache valuation insights by property ID
       - Invalidate on property data changes
       - Use longer TTL for market analysis

    2. PARALLEL PROCESSING
       - Fetch property data, comparables, and market data in parallel
       - Generate Claude insights while processing ML model

    3. PROGRESSIVE LOADING
       - Show ML valuation immediately
       - Add Claude insights progressively
       - Load comparables analysis last
    """
'''
    )

    @classmethod
    def get_template(cls, category: ComponentCategory) -> IntegrationTemplate:
        """Get integration template for category."""
        templates = {
            ComponentCategory.DASHBOARD: cls.DASHBOARD_TEMPLATE,
            ComponentCategory.COACHING: cls.COACHING_TEMPLATE,
            ComponentCategory.ANALYTICS: cls.ANALYTICS_TEMPLATE,
            ComponentCategory.PROPERTY: cls.PROPERTY_TEMPLATE,
            ComponentCategory.DATA_VISUALIZATION: cls.ANALYTICS_TEMPLATE,
            ComponentCategory.MONITORING: cls.DASHBOARD_TEMPLATE,
            ComponentCategory.LEAD_MANAGEMENT: cls.COACHING_TEMPLATE,
            ComponentCategory.WORKFLOW: cls.DASHBOARD_TEMPLATE,
        }
        return templates.get(category, cls.DASHBOARD_TEMPLATE)

    @classmethod
    def get_template_for_component(cls, file_name: str) -> IntegrationTemplate:
        """Determine appropriate template based on component name."""
        name_lower = file_name.lower()

        if any(k in name_lower for k in ['coaching', 'agent', 'training']):
            return cls.COACHING_TEMPLATE
        elif any(k in name_lower for k in ['property', 'valuation', 'listing']):
            return cls.PROPERTY_TEMPLATE
        elif any(k in name_lower for k in ['analytics', 'intelligence', 'report']):
            return cls.ANALYTICS_TEMPLATE
        else:
            return cls.DASHBOARD_TEMPLATE

    @classmethod
    def generate_integration_code(
        cls,
        component_name: str,
        category: ComponentCategory
    ) -> str:
        """Generate complete integration code for a component."""
        template = cls.get_template(category)

        code = f'''"""
{component_name} - Claude AI Integration
{'=' * (len(component_name) + 28)}

Auto-generated Claude AI integration template.
Customize the methods below for your specific use case.
"""

{template.imports}

{template.mixin_initialization.replace('MyDashboard', component_name).replace('CoachingDashboard', component_name).replace('AnalyticsDashboard', component_name).replace('PropertyComponent', component_name)}

    # =========================================================================
    # Claude AI Integration Methods
    # =========================================================================

{template.example_methods}

    # =========================================================================
    # UI Rendering with Claude Insights
    # =========================================================================

{template.ui_rendering}


{template.performance_considerations}
'''
        return code


# Export
__all__ = [
    'ClaudeIntegrationTemplates',
    'ComponentCategory',
    'IntegrationTemplate'
]
