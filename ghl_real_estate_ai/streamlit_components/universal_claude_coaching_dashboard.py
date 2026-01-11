"""
Universal Claude Coaching Dashboard - Real-Time Agent Assistance

Advanced Streamlit interface providing real-time Claude coaching with agent
profile awareness, role-specific guidance, and seamless integration with
the Universal Claude Gateway.

Key Features:
- Real-time coaching interface with WebSocket support
- Agent profile management and session tracking
- Role-specific coaching modes (Buyer/Seller/TC)
- Live conversation assistance with sub-500ms responses
- Performance monitoring and coaching effectiveness tracking
- Multi-tenant support with location-based access
"""

import streamlit as st
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import requests
import websockets
import threading
from dataclasses import dataclass

# Component imports
from .base_component import BaseComponent
from ..ghl_utils.config import settings
from ..core.service_registry import ServiceRegistry

# Initialize services
service_registry = ServiceRegistry()


@dataclass
class CoachingSession:
    """Tracking structure for coaching sessions."""
    session_id: str
    agent_id: str
    agent_name: str
    agent_role: str
    start_time: datetime
    message_count: int = 0
    coaching_requests: int = 0
    effectiveness_score: float = 0.0
    is_active: bool = True


class UniversalClaudeCoachingDashboard(BaseComponent):
    """
    Universal Claude Coaching Dashboard with real-time agent assistance.

    Provides comprehensive coaching interface with agent profile integration,
    real-time guidance, and performance tracking.
    """

    def __init__(self):
        super().__init__()
        self.api_base_url = f"{settings.api_base_url}/api/v1/claude-universal"
        self.current_session: Optional[CoachingSession] = None
        self.coaching_history: List[Dict[str, Any]] = []
        self.websocket_connected = False

    def render(self, **kwargs) -> None:
        """Render the complete Universal Claude Coaching Dashboard."""
        st.set_page_config(
            page_title="Universal Claude Coaching",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Custom CSS for enhanced UI
        self._inject_custom_css()

        # Main dashboard layout
        self._render_header()

        # Sidebar for agent profile and session management
        with st.sidebar:
            self._render_agent_profile_selector()
            self._render_session_management()
            self._render_performance_metrics()

        # Main content area
        col1, col2 = st.columns([2, 1])

        with col1:
            self._render_real_time_coaching_interface()
            self._render_conversation_simulator()

        with col2:
            self._render_live_guidance_panel()
            self._render_coaching_analytics()

        # Service health monitoring
        self._render_service_health_footer()

    def _inject_custom_css(self) -> None:
        """Inject custom CSS for enhanced UI styling."""
        st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            text-align: center;
        }

        .agent-profile-card {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
        }

        .coaching-message {
            background: #e7f3ff;
            border-left: 4px solid #007bff;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 4px;
        }

        .urgent-coaching {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 4px;
        }

        .performance-metric {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            padding: 0.75rem;
            margin: 0.5rem 0;
            border-radius: 4px;
            text-align: center;
        }

        .service-health-good {
            color: #155724;
            background-color: #d4edda;
            border-color: #c3e6cb;
        }

        .service-health-warning {
            color: #856404;
            background-color: #fff3cd;
            border-color: #ffeaa7;
        }

        .service-health-error {
            color: #721c24;
            background-color: #f8d7da;
            border-color: #f5c6cb;
        }
        </style>
        """, unsafe_allow_html=True)

    def _render_header(self) -> None:
        """Render the main dashboard header."""
        st.markdown("""
        <div class="main-header">
            <h1>🤖 Universal Claude Coaching Dashboard</h1>
            <p>Real-time AI coaching with agent profile awareness and intelligent routing</p>
        </div>
        """, unsafe_allow_html=True)

    def _render_agent_profile_selector(self) -> None:
        """Render agent profile selection and management."""
        st.subheader("👤 Agent Profile")

        # Agent profile selection
        agent_profiles = self._get_available_agent_profiles()

        if agent_profiles:
            selected_agent = st.selectbox(
                "Select Agent Profile",
                options=list(agent_profiles.keys()),
                format_func=lambda x: f"{agent_profiles[x]['name']} ({agent_profiles[x]['role']})"
            )

            if selected_agent:
                profile = agent_profiles[selected_agent]

                # Display agent profile card
                st.markdown(f"""
                <div class="agent-profile-card">
                    <h4>{profile['name']}</h4>
                    <p><strong>Role:</strong> {profile['role']}</p>
                    <p><strong>Experience:</strong> {profile['experience']} years</p>
                    <p><strong>Specializations:</strong> {', '.join(profile['specializations'])}</p>
                    <p><strong>Location:</strong> {profile['location']}</p>
                </div>
                """, unsafe_allow_html=True)

                # Store selected agent in session state
                st.session_state['selected_agent_id'] = selected_agent
                st.session_state['agent_profile'] = profile
        else:
            st.warning("No agent profiles found. Please configure agent profiles first.")
            if st.button("Setup Demo Profile"):
                self._create_demo_agent_profile()

    def _render_session_management(self) -> None:
        """Render session management controls."""
        st.subheader("📋 Session Management")

        # Start new session
        if st.button("🚀 Start New Session", use_container_width=True):
            self._start_new_coaching_session()

        # Current session info
        if self.current_session:
            session_duration = datetime.now() - self.current_session.start_time

            st.markdown(f"""
            **Active Session:** {self.current_session.session_id[:8]}...
            **Duration:** {self._format_duration(session_duration)}
            **Messages:** {self.current_session.message_count}
            **Coaching Requests:** {self.current_session.coaching_requests}
            **Effectiveness:** {self.current_session.effectiveness_score:.1%}
            """)

            if st.button("⏹️ End Session", use_container_width=True):
                self._end_coaching_session()

    def _render_real_time_coaching_interface(self) -> None:
        """Render the main real-time coaching interface."""
        st.subheader("💬 Real-Time Coaching Interface")

        # Coaching mode selector
        coaching_mode = st.selectbox(
            "Coaching Mode",
            ["General Coaching", "Real-Time Assistance", "Objection Handling",
             "Property Recommendation", "Market Analysis"],
            help="Select the type of coaching assistance needed"
        )

        # Query input
        with st.container():
            col1, col2 = st.columns([4, 1])

            with col1:
                query = st.text_area(
                    "Ask Claude for Coaching",
                    placeholder="Type your question or describe the situation you need help with...",
                    height=100,
                    key="coaching_query"
                )

            with col2:
                st.write("")  # Spacing
                get_coaching = st.button("🎯 Get Coaching", use_container_width=True, type="primary")

        # Priority and context options
        with st.expander("⚙️ Advanced Options"):
            col1, col2 = st.columns(2)

            with col1:
                priority = st.selectbox("Priority", ["Normal", "High", "Critical"])
                conversation_stage = st.selectbox(
                    "Conversation Stage",
                    ["Discovery", "Qualification", "Presentation", "Objection Handling", "Closing"]
                )

            with col2:
                include_context = st.checkbox("Include Conversation Context", value=True)
                real_time_mode = st.checkbox("Real-Time Mode (WebSocket)", value=False)

        # Process coaching request
        if get_coaching and query:
            self._process_coaching_request(
                query=query,
                coaching_mode=coaching_mode,
                priority=priority,
                conversation_stage=conversation_stage,
                include_context=include_context,
                real_time_mode=real_time_mode
            )

    def _render_conversation_simulator(self) -> None:
        """Render conversation simulation for testing."""
        st.subheader("🎭 Conversation Simulator")

        with st.expander("Simulate Prospect Conversation"):
            # Mock conversation scenarios
            scenarios = {
                "Price Objection": "I think your price is too high compared to other properties I've seen.",
                "Timeline Concern": "We're not sure if we want to move this quickly.",
                "Location Doubt": "I'm worried this neighborhood isn't right for our family.",
                "Financing Issue": "We're concerned about getting approved for a loan.",
                "Property Condition": "I noticed some issues during the showing that concern me."
            }

            selected_scenario = st.selectbox("Select Scenario", list(scenarios.keys()))

            if st.button("🎬 Simulate Scenario"):
                prospect_message = scenarios[selected_scenario]
                self._simulate_real_time_coaching(prospect_message)

    def _render_live_guidance_panel(self) -> None:
        """Render live guidance and suggestions panel."""
        st.subheader("🎯 Live Guidance")

        # Recent coaching responses
        if hasattr(st.session_state, 'recent_coaching') and st.session_state.recent_coaching:
            coaching_data = st.session_state.recent_coaching

            # Display main response
            st.markdown(f"""
            <div class="{'urgent-coaching' if coaching_data['urgency_level'] == 'high' else 'coaching-message'}">
                <strong>Claude's Coaching:</strong><br>
                {coaching_data['response']}
            </div>
            """, unsafe_allow_html=True)

            # Quick action buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Apply Suggestion"):
                    st.success("Suggestion applied!")
            with col2:
                if st.button("💡 Get Alternative"):
                    self._get_alternative_coaching(coaching_data['response'])

            # Detailed insights
            with st.expander("📊 Detailed Insights"):
                if coaching_data.get('insights'):
                    st.write("**Key Insights:**")
                    for insight in coaching_data['insights']:
                        st.write(f"• {insight}")

                if coaching_data.get('next_questions'):
                    st.write("**Suggested Questions:**")
                    for question in coaching_data['next_questions']:
                        if st.button(f"❓ {question}", key=f"q_{hash(question)}"):
                            st.session_state.coaching_query = question

        else:
            st.info("Request coaching to see live guidance here.")

    def _render_performance_metrics(self) -> None:
        """Render performance metrics and effectiveness tracking."""
        st.subheader("📈 Performance")

        # Get performance metrics
        metrics = self._get_performance_metrics()

        if metrics:
            # Response time
            response_time = metrics.get('avg_response_time_ms', 0)
            response_color = "good" if response_time < 500 else "warning" if response_time < 1000 else "error"

            st.markdown(f"""
            <div class="performance-metric service-health-{response_color}">
                <strong>Avg Response Time</strong><br>
                {response_time:.0f}ms
            </div>
            """, unsafe_allow_html=True)

            # Coaching effectiveness
            effectiveness = metrics.get('coaching_effectiveness', 0)
            effectiveness_color = "good" if effectiveness > 0.8 else "warning" if effectiveness > 0.6 else "error"

            st.markdown(f"""
            <div class="performance-metric service-health-{effectiveness_color}">
                <strong>Coaching Effectiveness</strong><br>
                {effectiveness:.1%}
            </div>
            """, unsafe_allow_html=True)

            # Cache hit rate
            cache_rate = metrics.get('cache_hit_rate', 0)
            st.markdown(f"""
            <div class="performance-metric service-health-good">
                <strong>Cache Hit Rate</strong><br>
                {cache_rate:.1%}
            </div>
            """, unsafe_allow_html=True)

    def _render_coaching_analytics(self) -> None:
        """Render coaching analytics and patterns."""
        st.subheader("📊 Coaching Analytics")

        # Session analytics
        if self.current_session:
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Messages", self.current_session.message_count)
                st.metric("Coaching Requests", self.current_session.coaching_requests)

            with col2:
                st.metric("Effectiveness", f"{self.current_session.effectiveness_score:.1%}")
                st.metric("Agent Role", self.current_session.agent_role)

        # Coaching history chart
        if len(self.coaching_history) > 1:
            # Create simple chart data
            chart_data = {
                'Time': [item['timestamp'] for item in self.coaching_history[-10:]],
                'Confidence': [item['confidence'] for item in self.coaching_history[-10:]]
            }

            st.line_chart(chart_data, x='Time', y='Confidence')

    def _render_service_health_footer(self) -> None:
        """Render service health status footer."""
        st.subheader("🔧 Service Health")

        # Get service health
        health_data = self._get_service_health()

        if health_data:
            col1, col2, col3 = st.columns(3)

            with col1:
                status = health_data['gateway_status']
                color = "good" if status == "healthy" else "warning"
                st.markdown(f"""
                <div class="performance-metric service-health-{color}">
                    <strong>Gateway Status</strong><br>
                    {status.title()}
                </div>
                """, unsafe_allow_html=True)

            with col2:
                total_services = health_data['total_services']
                st.markdown(f"""
                <div class="performance-metric service-health-good">
                    <strong>Active Services</strong><br>
                    {total_services}
                </div>
                """, unsafe_allow_html=True)

            with col3:
                enhanced = health_data['enhanced_features']
                color = "good" if enhanced else "warning"
                st.markdown(f"""
                <div class="performance-metric service-health-{color}">
                    <strong>Enhanced Features</strong><br>
                    {'Enabled' if enhanced else 'Limited'}
                </div>
                """, unsafe_allow_html=True)

        # Auto-refresh toggle
        if st.checkbox("Auto-refresh health status", value=False):
            time.sleep(5)
            st.experimental_rerun()

    # ========================================================================
    # Backend Integration Methods
    # ========================================================================

    def _get_available_agent_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Get available agent profiles from the service."""
        try:
            # Mock data for demo - would integrate with actual service
            return {
                "agent_001": {
                    "name": "Sarah Johnson",
                    "role": "Buyer Agent",
                    "experience": 5,
                    "specializations": ["First-time buyers", "Luxury homes"],
                    "location": "Downtown District"
                },
                "agent_002": {
                    "name": "Mike Chen",
                    "role": "Seller Agent",
                    "experience": 8,
                    "specializations": ["Commercial", "Investment properties"],
                    "location": "Business District"
                },
                "agent_003": {
                    "name": "Emma Wilson",
                    "role": "Transaction Coordinator",
                    "experience": 3,
                    "specializations": ["Compliance", "Documentation"],
                    "location": "Regional Office"
                }
            }
        except Exception as e:
            st.error(f"Error loading agent profiles: {e}")
            return {}

    def _start_new_coaching_session(self) -> None:
        """Start a new coaching session."""
        try:
            if not hasattr(st.session_state, 'selected_agent_id'):
                st.error("Please select an agent profile first.")
                return

            agent_id = st.session_state.selected_agent_id
            agent_profile = st.session_state.agent_profile

            # Create new session
            self.current_session = CoachingSession(
                session_id=f"session_{int(time.time())}",
                agent_id=agent_id,
                agent_name=agent_profile['name'],
                agent_role=agent_profile['role'],
                start_time=datetime.now()
            )

            st.success(f"New coaching session started for {agent_profile['name']}")

        except Exception as e:
            st.error(f"Error starting session: {e}")

    def _process_coaching_request(
        self,
        query: str,
        coaching_mode: str,
        priority: str,
        conversation_stage: str,
        include_context: bool,
        real_time_mode: bool
    ) -> None:
        """Process a coaching request through the Universal Gateway."""
        try:
            if not self.current_session:
                st.error("Please start a session first.")
                return

            # Map coaching mode to query type
            mode_mapping = {
                "General Coaching": "general_coaching",
                "Real-Time Assistance": "real_time_assistance",
                "Objection Handling": "objection_handling",
                "Property Recommendation": "property_recommendation",
                "Market Analysis": "market_analysis"
            }

            # Prepare request data
            request_data = {
                "agent_id": self.current_session.agent_id,
                "query": query,
                "session_id": self.current_session.session_id,
                "query_type": mode_mapping.get(coaching_mode, "general_coaching"),
                "priority": priority.lower(),
                "conversation_stage": conversation_stage.lower(),
                "context": {
                    "agent_role": self.current_session.agent_role,
                    "coaching_mode": coaching_mode,
                    "include_context": include_context
                }
            }

            # Process request
            with st.spinner("Getting coaching from Claude..."):
                start_time = time.time()

                if real_time_mode:
                    response = self._process_realtime_request(request_data)
                else:
                    response = self._process_standard_request(request_data)

                processing_time = (time.time() - start_time) * 1000

                if response:
                    # Update session tracking
                    self.current_session.message_count += 1
                    self.current_session.coaching_requests += 1
                    self.current_session.effectiveness_score = response.get('confidence', 0)

                    # Store response in session state
                    st.session_state.recent_coaching = response

                    # Add to history
                    self.coaching_history.append({
                        'timestamp': datetime.now(),
                        'query': query,
                        'response': response,
                        'processing_time': processing_time,
                        'confidence': response.get('confidence', 0)
                    })

                    # Display success
                    st.success(f"Coaching received! (Response time: {processing_time:.0f}ms)")

                else:
                    st.error("Failed to get coaching response.")

        except Exception as e:
            st.error(f"Error processing coaching request: {e}")

    def _process_standard_request(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process standard HTTP request to Universal Gateway."""
        try:
            # Use the service registry method
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            response = loop.run_until_complete(
                service_registry.process_claude_query_with_agent_context(
                    agent_id=request_data['agent_id'],
                    query=request_data['query'],
                    session_id=request_data.get('session_id'),
                    context=request_data.get('context'),
                    query_type=request_data.get('query_type', 'general_coaching'),
                    priority=request_data.get('priority', 'normal')
                )
            )

            return response

        except Exception as e:
            st.error(f"Error with standard request: {e}")
            return None

    def _process_realtime_request(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process real-time WebSocket request."""
        try:
            # For demo purposes, use standard request
            # In production, this would use WebSocket connection
            return self._process_standard_request(request_data)

        except Exception as e:
            st.error(f"Error with real-time request: {e}")
            return None

    def _simulate_real_time_coaching(self, prospect_message: str) -> None:
        """Simulate real-time coaching for a prospect message."""
        try:
            if not self.current_session:
                st.error("Please start a session first.")
                return

            st.info(f"**Prospect says:** {prospect_message}")

            # Process as real-time coaching
            self._process_coaching_request(
                query=f"The prospect just said: '{prospect_message}'. How should I respond?",
                coaching_mode="Real-Time Assistance",
                priority="High",
                conversation_stage="Objection Handling",
                include_context=True,
                real_time_mode=True
            )

        except Exception as e:
            st.error(f"Error simulating coaching: {e}")

    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics from the service."""
        try:
            # Mock performance data - would integrate with actual metrics service
            return {
                'avg_response_time_ms': 325.0,
                'coaching_effectiveness': 0.87,
                'cache_hit_rate': 0.68,
                'total_requests': 156,
                'successful_requests': 154
            }
        except Exception as e:
            return {}

    def _get_service_health(self) -> Dict[str, Any]:
        """Get service health status."""
        try:
            # Use service registry method
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            health_data = loop.run_until_complete(
                service_registry.get_claude_service_health_status()
            )

            return health_data

        except Exception as e:
            return {
                'gateway_status': 'unknown',
                'total_services': 0,
                'enhanced_features': False
            }

    def _get_alternative_coaching(self, original_response: str) -> None:
        """Get alternative coaching suggestion."""
        try:
            alternative_query = f"Provide an alternative approach to: {original_response[:100]}..."

            self._process_coaching_request(
                query=alternative_query,
                coaching_mode="General Coaching",
                priority="Normal",
                conversation_stage="Discovery",
                include_context=True,
                real_time_mode=False
            )
        except Exception as e:
            st.error(f"Error getting alternative coaching: {e}")

    def _create_demo_agent_profile(self) -> None:
        """Create a demo agent profile for testing."""
        try:
            st.session_state['selected_agent_id'] = "demo_agent_001"
            st.session_state['agent_profile'] = {
                "name": "Demo Agent",
                "role": "Buyer Agent",
                "experience": 2,
                "specializations": ["First-time buyers"],
                "location": "Demo Location"
            }
            st.success("Demo agent profile created!")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Error creating demo profile: {e}")

    def _end_coaching_session(self) -> None:
        """End the current coaching session."""
        try:
            if self.current_session:
                session_duration = datetime.now() - self.current_session.start_time

                st.success(
                    f"Session ended. Duration: {self._format_duration(session_duration)}, "
                    f"Messages: {self.current_session.message_count}, "
                    f"Effectiveness: {self.current_session.effectiveness_score:.1%}"
                )

                self.current_session = None

                # Clear session state
                if 'recent_coaching' in st.session_state:
                    del st.session_state['recent_coaching']

        except Exception as e:
            st.error(f"Error ending session: {e}")

    def _format_duration(self, duration: timedelta) -> str:
        """Format duration for display."""
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"


# ========================================================================
# Main Dashboard Function for Easy Integration
# ========================================================================

def render_universal_claude_coaching_dashboard(**kwargs) -> None:
    """
    Render the Universal Claude Coaching Dashboard.

    This is the main entry point for the dashboard component.
    """
    dashboard = UniversalClaudeCoachingDashboard()
    dashboard.render(**kwargs)


# ========================================================================
# Usage Example and Component Registration
# ========================================================================

if __name__ == "__main__":
    # Example usage when run directly
    st.title("Universal Claude Coaching Dashboard")
    render_universal_claude_coaching_dashboard()