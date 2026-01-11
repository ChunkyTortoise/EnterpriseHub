"""
AI Engines Integration Example

Demonstrates how to integrate the Competitive Intelligence and Predictive Lead Lifecycle engines
with existing EnterpriseHub components including GHL webhooks, Streamlit UI, and performance monitoring.

This example shows:
- Integration with GHL webhook processing
- Real-time AI analysis triggers
- Streamlit dashboard integration
- Performance monitoring integration
- Error handling and fallback strategies
"""

import asyncio
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
import json

# Import existing services
from ..services.ai_engines_integration_service import (
    AIEnginesIntegrationService,
    get_ai_engines_integration_service,
    AnalysisScope,
    ProcessingPriority
)
from ..config.ai_engines_config import get_config, validate_environment
from ..api.ai_engines_api import router as ai_engines_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIEnginesWebhookIntegration:
    """
    Integration layer between GHL webhooks and AI engines for real-time analysis.
    """

    def __init__(self):
        self.ai_service: Optional[AIEnginesIntegrationService] = None
        self.initialized = False

    async def initialize(self):
        """Initialize AI engines integration"""
        try:
            # Validate environment
            if not validate_environment():
                raise Exception("Environment validation failed")

            # Get configuration
            config = get_config()

            # Initialize AI service
            self.ai_service = await get_ai_engines_integration_service(config.to_dict())
            self.initialized = True

            logger.info("✅ AI Engines Webhook Integration initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize AI engines integration: {e}")
            raise

    async def process_webhook_with_ai_analysis(
        self,
        webhook_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process GHL webhook with integrated AI analysis.

        This demonstrates how to trigger AI analysis when leads are updated.
        """
        if not self.initialized or not self.ai_service:
            logger.warning("AI engines not initialized, processing webhook without AI")
            return webhook_data

        try:
            # Extract lead information from webhook
            lead_id = webhook_data.get('contactId')
            event_type = webhook_data.get('type', '')

            if not lead_id:
                logger.warning("No contactId in webhook data, skipping AI analysis")
                return webhook_data

            # Determine if AI analysis should be triggered
            should_analyze = await self._should_trigger_ai_analysis(event_type, webhook_data)

            if should_analyze:
                logger.info(f"🧠 Triggering AI analysis for lead {lead_id} due to {event_type}")

                # Prepare context from webhook data
                lead_context = self._extract_lead_context(webhook_data)
                property_context = self._extract_property_context(webhook_data)

                # Determine analysis scope and priority
                analysis_scope = self._determine_analysis_scope(event_type, webhook_data)
                priority = self._determine_priority(event_type, webhook_data)

                # Execute unified AI analysis
                ai_result = await self.ai_service.analyze_lead_unified(
                    lead_id=lead_id,
                    analysis_scope=analysis_scope,
                    priority=priority,
                    lead_context=lead_context,
                    property_context=property_context
                )

                # Add AI insights to webhook response
                webhook_data['ai_analysis'] = {
                    'analysis_id': ai_result.request_id,
                    'processing_time_ms': ai_result.processing_time_ms,
                    'confidence_level': ai_result.confidence_level,
                    'immediate_actions': ai_result.immediate_actions,
                    'strategic_recommendations': ai_result.strategic_recommendations,
                    'risk_level': self._calculate_overall_risk_level(ai_result),
                    'conversion_probability': self._extract_conversion_probability(ai_result),
                    'competitive_threats': self._extract_threat_count(ai_result),
                    'recommended_interventions': len(ai_result.intervention_windows),
                    'analysis_timestamp': ai_result.created_at.isoformat()
                }

                # Trigger real-time actions based on AI analysis
                await self._execute_ai_driven_actions(lead_id, ai_result)

                logger.info(f"✅ AI analysis completed for lead {lead_id} in {ai_result.processing_time_ms:.1f}ms")

            else:
                logger.debug(f"Skipping AI analysis for {event_type} event")

            return webhook_data

        except Exception as e:
            logger.error(f"❌ AI analysis failed for webhook: {e}")
            # Return original webhook data on error
            webhook_data['ai_analysis_error'] = str(e)
            return webhook_data

    async def _should_trigger_ai_analysis(
        self,
        event_type: str,
        webhook_data: Dict[str, Any]
    ) -> bool:
        """Determine if AI analysis should be triggered for this webhook"""

        # High-priority events that should trigger AI analysis
        high_priority_events = [
            'contact.created',
            'contact.updated',
            'opportunity.status_changed',
            'appointment.created',
            'conversation.message.added'
        ]

        if event_type in high_priority_events:
            return True

        # Check for specific conditions that warrant analysis
        custom_fields = webhook_data.get('customFields', {})

        # Trigger if AI Assistant is enabled
        if custom_fields.get('ai_assistant_enabled') == 'true':
            return True

        # Trigger if high-value lead (budget > $500k)
        budget = custom_fields.get('budget', '').lower()
        if any(val in budget for val in ['500k', '750k', '1m', 'million']):
            return True

        # Trigger if timeline is urgent
        timeline = custom_fields.get('timeline', '').lower()
        if any(val in timeline for val in ['immediate', 'asap', 'urgent']):
            return True

        return False

    def _extract_lead_context(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract lead context from webhook data"""
        custom_fields = webhook_data.get('customFields', {})

        return {
            'source': webhook_data.get('source'),
            'tags': webhook_data.get('tags', []),
            'budget': custom_fields.get('budget'),
            'timeline': custom_fields.get('timeline'),
            'property_type': custom_fields.get('property_type'),
            'location_preference': custom_fields.get('location'),
            'phone': webhook_data.get('phone'),
            'email': webhook_data.get('email'),
            'last_activity': webhook_data.get('dateUpdated')
        }

    def _extract_property_context(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract property context from webhook data"""
        custom_fields = webhook_data.get('customFields', {})

        property_context = {}

        if custom_fields.get('property_type'):
            property_context['property_type'] = custom_fields['property_type']

        if custom_fields.get('bedrooms'):
            property_context['bedrooms'] = custom_fields['bedrooms']

        if custom_fields.get('bathrooms'):
            property_context['bathrooms'] = custom_fields['bathrooms']

        if custom_fields.get('square_feet'):
            property_context['square_feet'] = custom_fields['square_feet']

        return property_context if property_context else None

    def _determine_analysis_scope(
        self,
        event_type: str,
        webhook_data: Dict[str, Any]
    ) -> AnalysisScope:
        """Determine appropriate analysis scope based on event type"""

        # For new leads, do full unified analysis
        if event_type == 'contact.created':
            return AnalysisScope.UNIFIED_ANALYSIS

        # For status changes, focus on competitive analysis
        if event_type == 'opportunity.status_changed':
            return AnalysisScope.COMPETITIVE_ONLY

        # For conversations, focus on predictive analysis
        if event_type == 'conversation.message.added':
            return AnalysisScope.PREDICTIVE_ONLY

        # Default to unified analysis
        return AnalysisScope.UNIFIED_ANALYSIS

    def _determine_priority(
        self,
        event_type: str,
        webhook_data: Dict[str, Any]
    ) -> ProcessingPriority:
        """Determine processing priority based on event and data"""

        custom_fields = webhook_data.get('customFields', {})

        # High priority for immediate timeline or high budget
        timeline = custom_fields.get('timeline', '').lower()
        budget = custom_fields.get('budget', '').lower()

        if 'immediate' in timeline or 'urgent' in timeline:
            return ProcessingPriority.HIGH

        if any(val in budget for val in ['1m', 'million', '750k']):
            return ProcessingPriority.HIGH

        # Medium priority for opportunity changes
        if event_type == 'opportunity.status_changed':
            return ProcessingPriority.HIGH

        return ProcessingPriority.NORMAL

    async def _execute_ai_driven_actions(
        self,
        lead_id: str,
        ai_result
    ):
        """Execute real-time actions based on AI analysis results"""
        try:
            # Check for critical threats that require immediate action
            if ai_result.competitive_analysis:
                high_threats = [
                    threat for threat in ai_result.competitive_analysis.active_threats
                    if hasattr(threat, 'threat_level') and threat.threat_level in ['high', 'critical']
                ]

                if high_threats:
                    logger.warning(f"🚨 High competitive threats detected for lead {lead_id}")
                    # Could trigger automated responses here

            # Check for urgent intervention windows
            urgent_interventions = [
                intervention for intervention in ai_result.intervention_windows
                if hasattr(intervention, 'priority') and intervention.priority > 0.9
            ]

            if urgent_interventions:
                logger.info(f"⚡ Urgent interventions recommended for lead {lead_id}")
                # Could trigger notification to agent here

            # Check for high-risk factors
            critical_risks = [
                risk for risk in ai_result.consolidated_risks
                if hasattr(risk, 'severity') and risk.severity > 0.8
            ]

            if critical_risks:
                logger.warning(f"⚠️ Critical risk factors identified for lead {lead_id}")
                # Could trigger risk mitigation workflows here

        except Exception as e:
            logger.error(f"Error executing AI-driven actions: {e}")

    def _calculate_overall_risk_level(self, ai_result) -> str:
        """Calculate overall risk level from AI analysis"""
        if not ai_result.consolidated_risks:
            return "low"

        max_severity = max(
            risk.severity for risk in ai_result.consolidated_risks
            if hasattr(risk, 'severity')
        ) if ai_result.consolidated_risks else 0.0

        if max_severity > 0.8:
            return "critical"
        elif max_severity > 0.6:
            return "high"
        elif max_severity > 0.4:
            return "medium"
        else:
            return "low"

    def _extract_conversion_probability(self, ai_result) -> Optional[float]:
        """Extract conversion probability from AI result"""
        if ai_result.conversion_forecast:
            return ai_result.conversion_forecast.conversion_probability
        return None

    def _extract_threat_count(self, ai_result) -> int:
        """Extract number of competitive threats"""
        if ai_result.competitive_analysis:
            return len(ai_result.competitive_analysis.active_threats)
        return 0


class AIEnginesStreamlitDashboard:
    """
    Streamlit dashboard integration for AI engines monitoring and control.
    """

    def __init__(self):
        self.ai_service: Optional[AIEnginesIntegrationService] = None

    async def initialize(self):
        """Initialize Streamlit dashboard integration"""
        try:
            config = get_config()
            self.ai_service = await get_ai_engines_integration_service(config.to_dict())
            logger.info("✅ AI Engines Streamlit Dashboard initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize dashboard: {e}")
            raise

    def render_ai_engines_dashboard(self):
        """Render the main AI engines dashboard"""

        st.title("🧠 AI Engines Control Center")
        st.markdown("Monitor and control Competitive Intelligence and Predictive Lead Lifecycle engines")

        # Health Status Section
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔍 Check Health Status"):
                if self.ai_service:
                    health_status = asyncio.run(self.ai_service.health_check())

                    if health_status.get('healthy', False):
                        st.success("✅ All AI engines healthy")
                    else:
                        st.error("❌ AI engines experiencing issues")

                    st.json(health_status)
                else:
                    st.error("AI service not initialized")

        with col2:
            if st.button("📊 Performance Metrics"):
                if self.ai_service:
                    metrics = asyncio.run(self.ai_service.get_performance_metrics())
                    st.json(metrics)
                else:
                    st.error("AI service not initialized")

        with col3:
            if st.button("🧹 Clear Cache"):
                st.warning("Cache clearing functionality would be implemented here")

        # AI Analysis Section
        st.header("🎯 Lead Analysis")

        lead_id = st.text_input("Lead ID", placeholder="Enter lead ID to analyze")

        analysis_scope = st.selectbox(
            "Analysis Scope",
            ["unified_analysis", "competitive_only", "predictive_only", "cross_engine_fusion"]
        )

        priority = st.selectbox(
            "Priority",
            ["normal", "high", "critical"]
        )

        if st.button("🚀 Analyze Lead") and lead_id and self.ai_service:
            with st.spinner("Analyzing lead..."):
                try:
                    scope_mapping = {
                        "unified_analysis": AnalysisScope.UNIFIED_ANALYSIS,
                        "competitive_only": AnalysisScope.COMPETITIVE_ONLY,
                        "predictive_only": AnalysisScope.PREDICTIVE_ONLY,
                        "cross_engine_fusion": AnalysisScope.CROSS_ENGINE_FUSION
                    }

                    priority_mapping = {
                        "normal": ProcessingPriority.NORMAL,
                        "high": ProcessingPriority.HIGH,
                        "critical": ProcessingPriority.CRITICAL
                    }

                    result = asyncio.run(
                        self.ai_service.analyze_lead_unified(
                            lead_id=lead_id,
                            analysis_scope=scope_mapping[analysis_scope],
                            priority=priority_mapping[priority]
                        )
                    )

                    # Display results
                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("📈 Analysis Summary")
                        st.metric("Processing Time", f"{result.processing_time_ms:.1f}ms")
                        st.metric("Confidence Level", f"{result.confidence_level:.2f}")
                        st.metric("Accuracy Score", f"{result.accuracy_score:.2f}")

                    with col2:
                        st.subheader("🎯 Key Insights")
                        if result.immediate_actions:
                            st.write("**Immediate Actions:**")
                            for action in result.immediate_actions:
                                st.write(f"• {action}")

                    # Detailed results
                    if st.checkbox("Show Detailed Results"):
                        st.json(result.to_dict())

                except Exception as e:
                    st.error(f"Analysis failed: {e}")

        # Real-time Monitoring Section
        st.header("📡 Real-time Monitoring")

        if st.checkbox("Enable Real-time Updates"):
            placeholder = st.empty()

            # This would be replaced with actual real-time updates
            for i in range(10):
                with placeholder.container():
                    st.write(f"Update {i+1}: System running normally")
                    if self.ai_service:
                        metrics = asyncio.run(self.ai_service.get_performance_metrics())

                        # Display key metrics
                        col1, col2, col3, col4 = st.columns(4)

                        integration_metrics = metrics.get('integration_service', {})

                        with col1:
                            st.metric(
                                "Total Requests",
                                integration_metrics.get('total_requests', 0)
                            )

                        with col2:
                            st.metric(
                                "Success Rate",
                                f"{metrics.get('success_rate', 0):.1f}%"
                            )

                        with col3:
                            st.metric(
                                "Avg Response Time",
                                f"{integration_metrics.get('average_processing_time', 0):.1f}ms"
                            )

                        with col4:
                            st.metric(
                                "Cache Hit Rate",
                                f"{metrics.get('cache_hit_rate', 0):.1f}%"
                            )

                # Update every 5 seconds
                import time
                time.sleep(5)


# Example usage functions

async def example_webhook_processing():
    """Example of processing a GHL webhook with AI integration"""

    # Initialize webhook integration
    webhook_integration = AIEnginesWebhookIntegration()
    await webhook_integration.initialize()

    # Simulate GHL webhook data
    webhook_data = {
        'contactId': 'lead_12345',
        'type': 'contact.updated',
        'phone': '+1234567890',
        'email': 'lead@example.com',
        'source': 'website_form',
        'tags': ['hot_lead', 'immediate_timeline'],
        'customFields': {
            'budget': '750k-1m',
            'timeline': 'immediate',
            'property_type': 'single_family',
            'location': 'downtown',
            'ai_assistant_enabled': 'true'
        },
        'dateUpdated': datetime.now().isoformat()
    }

    # Process webhook with AI integration
    result = await webhook_integration.process_webhook_with_ai_analysis(webhook_data)

    print("🎯 Webhook processing completed with AI analysis:")
    print(json.dumps(result.get('ai_analysis', {}), indent=2))


def example_streamlit_dashboard():
    """Example of running the Streamlit dashboard"""

    dashboard = AIEnginesStreamlitDashboard()

    # Initialize dashboard
    try:
        asyncio.run(dashboard.initialize())

        # Render dashboard
        dashboard.render_ai_engines_dashboard()

    except Exception as e:
        st.error(f"Failed to initialize dashboard: {e}")


# Main execution
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "webhook":
        # Run webhook example
        asyncio.run(example_webhook_processing())
    elif len(sys.argv) > 1 and sys.argv[1] == "dashboard":
        # Run Streamlit dashboard
        example_streamlit_dashboard()
    else:
        print("🧠 AI Engines Integration Examples")
        print("\nUsage:")
        print("  python ai_engines_integration_example.py webhook    # Run webhook example")
        print("  python ai_engines_integration_example.py dashboard  # Run Streamlit dashboard")
        print("\nOr use in your own code:")
        print("  from ai_engines_integration_example import AIEnginesWebhookIntegration")
        print("  from ai_engines_integration_example import AIEnginesStreamlitDashboard")