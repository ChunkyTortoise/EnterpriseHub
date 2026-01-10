"""
Mobile Agent Experience Service for GHL Real Estate AI Platform

This service provides a comprehensive mobile-responsive interface for real estate agents
to manage their lead nurturing campaigns, view analytics, and take quick actions while
on the go. It integrates with the ML personalization engine, video messaging system,
and ROI attribution system for complete mobile functionality.

Author: AI Assistant
Created: 2026-01-09
Version: 1.0.0
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid

from pydantic import BaseModel, Field, validator
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .advanced_ml_personalization_engine import AdvancedMLPersonalizationEngine
from .video_message_integration import VideoMessageIntegration
from .roi_attribution_system import ROIAttributionSystem
from .base_service import BaseService

logger = logging.getLogger(__name__)


class MobilePriority(str, Enum):
    """Mobile notification and alert priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class MobileActionType(str, Enum):
    """Types of mobile actions available to agents."""
    SEND_MESSAGE = "send_message"
    SCHEDULE_CALL = "schedule_call"
    CREATE_TASK = "create_task"
    SEND_VIDEO = "send_video"
    UPDATE_LEAD_STATUS = "update_lead_status"
    VIEW_PROPERTY = "view_property"
    SHARE_LISTING = "share_listing"
    QUICK_RESPONSE = "quick_response"
    EMERGENCY_CONTACT = "emergency_contact"


class MobileViewType(str, Enum):
    """Different mobile view types for the agent interface."""
    DASHBOARD = "dashboard"
    LEADS = "leads"
    CAMPAIGNS = "campaigns"
    ANALYTICS = "analytics"
    QUICK_ACTIONS = "quick_actions"
    NOTIFICATIONS = "notifications"
    SETTINGS = "settings"


# Pydantic Models

class MobileNotification(BaseModel):
    """Mobile notification model with priority and action capabilities."""
    notification_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    title: str
    message: str
    priority: MobilePriority
    action_type: Optional[MobileActionType] = None
    action_data: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.now)
    read_at: Optional[datetime] = None
    dismissed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class QuickAction(BaseModel):
    """Quick action button configuration for mobile interface."""
    action_id: str
    label: str
    action_type: MobileActionType
    icon: str
    color: str
    requires_input: bool = False
    input_type: Optional[str] = None
    confirmation_required: bool = False


class MobileLeadSummary(BaseModel):
    """Condensed lead information optimized for mobile viewing."""
    lead_id: str
    name: str
    phone: str
    email: str
    lead_status: str
    lead_score: float
    last_interaction: datetime
    next_action: str
    property_interest: str
    engagement_level: str
    priority: MobilePriority
    quick_actions: List[QuickAction]


class MobileCampaignSummary(BaseModel):
    """Campaign summary optimized for mobile viewing."""
    campaign_id: str
    name: str
    status: str
    active_leads: int
    conversion_rate: float
    roi: float
    next_milestone: str
    last_updated: datetime
    performance_trend: str  # "up", "down", "stable"


class MobileAnalytics(BaseModel):
    """Analytics data optimized for mobile charts and KPIs."""
    date_range: str
    total_leads: int
    active_campaigns: int
    conversion_rate: float
    total_roi: float
    top_performing_channel: str
    urgent_actions_needed: int
    daily_metrics: List[Dict[str, Union[str, int, float]]]
    channel_performance: List[Dict[str, Union[str, float]]]
    conversion_funnel: List[Dict[str, Union[str, int]]]


class MobileAgentProfile(BaseModel):
    """Agent profile and preferences for mobile experience."""
    agent_id: str
    name: str
    phone: str
    email: str
    timezone: str
    notification_preferences: Dict[str, bool]
    quick_action_preferences: List[str]
    dashboard_layout: List[str]
    offline_sync_enabled: bool = True
    location_services_enabled: bool = True


class MobileSession(BaseModel):
    """Mobile session tracking for offline capability and sync."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    device_type: str
    device_id: str
    app_version: str
    last_sync: datetime = Field(default_factory=datetime.now)
    offline_actions: List[Dict[str, Any]] = Field(default_factory=list)
    sync_pending: bool = False


# Main Service Class

class MobileAgentExperience(BaseService):
    """
    Mobile Agent Experience Service

    Provides a comprehensive mobile-responsive interface for real estate agents
    to manage their lead nurturing campaigns on the go.
    """

    def __init__(self):
        """Initialize the mobile agent experience service."""
        super().__init__()
        self.personalization_engine = AdvancedMLPersonalizationEngine()
        self.video_integration = VideoMessageIntegration()
        self.roi_attribution = ROIAttributionSystem()

        # Mobile-specific configurations
        self.default_quick_actions = self._configure_default_quick_actions()
        self.notification_templates = self._configure_notification_templates()
        self.mobile_sessions: Dict[str, MobileSession] = {}

        logger.info("Mobile Agent Experience service initialized")

    def _configure_default_quick_actions(self) -> List[QuickAction]:
        """Configure default quick actions for mobile interface."""
        return [
            QuickAction(
                action_id="quick_call",
                label="Call Lead",
                action_type=MobileActionType.SCHEDULE_CALL,
                icon="📞",
                color="#4CAF50",
                confirmation_required=True
            ),
            QuickAction(
                action_id="quick_message",
                label="Send Text",
                action_type=MobileActionType.SEND_MESSAGE,
                icon="💬",
                color="#2196F3",
                requires_input=True,
                input_type="text"
            ),
            QuickAction(
                action_id="send_video",
                label="Send Video",
                action_type=MobileActionType.SEND_VIDEO,
                icon="🎥",
                color="#FF5722"
            ),
            QuickAction(
                action_id="share_listing",
                label="Share Listing",
                action_type=MobileActionType.SHARE_LISTING,
                icon="🏠",
                color="#795548",
                requires_input=True,
                input_type="property_select"
            ),
            QuickAction(
                action_id="emergency_contact",
                label="Emergency",
                action_type=MobileActionType.EMERGENCY_CONTACT,
                icon="🚨",
                color="#F44336",
                confirmation_required=True
            )
        ]

    def _configure_notification_templates(self) -> Dict[str, str]:
        """Configure notification templates for different scenarios."""
        return {
            "hot_lead": "🔥 Hot lead alert: {lead_name} is highly engaged!",
            "urgent_response": "⚡ Urgent: {lead_name} needs immediate response",
            "appointment_reminder": "📅 Reminder: Showing at {time} with {lead_name}",
            "campaign_milestone": "🎯 Campaign milestone reached: {milestone}",
            "roi_alert": "💰 ROI alert: Campaign {campaign_name} exceeding targets",
            "system_update": "🔧 System update: {message}",
            "lead_activity": "👀 {lead_name} viewed {property_address}",
            "conversion_opportunity": "💎 Conversion opportunity: {lead_name} ready to buy"
        }

    async def initialize_mobile_session(
        self,
        agent_id: str,
        device_info: Dict[str, str]
    ) -> MobileSession:
        """Initialize a new mobile session for an agent."""
        try:
            session = MobileSession(
                agent_id=agent_id,
                device_type=device_info.get('type', 'unknown'),
                device_id=device_info.get('device_id', 'unknown'),
                app_version=device_info.get('app_version', '1.0.0')
            )

            self.mobile_sessions[session.session_id] = session

            logger.info(f"Mobile session initialized for agent {agent_id}")
            return session

        except Exception as e:
            logger.error(f"Error initializing mobile session: {e}")
            raise

    async def get_mobile_dashboard(
        self,
        agent_id: str,
        view_type: MobileViewType = MobileViewType.DASHBOARD
    ) -> Dict[str, Any]:
        """Get mobile dashboard data optimized for the specified view type."""
        try:
            dashboard_data = {}

            if view_type == MobileViewType.DASHBOARD:
                dashboard_data = await self._build_dashboard_view(agent_id)
            elif view_type == MobileViewType.LEADS:
                dashboard_data = await self._build_leads_view(agent_id)
            elif view_type == MobileViewType.CAMPAIGNS:
                dashboard_data = await self._build_campaigns_view(agent_id)
            elif view_type == MobileViewType.ANALYTICS:
                dashboard_data = await self._build_analytics_view(agent_id)
            elif view_type == MobileViewType.QUICK_ACTIONS:
                dashboard_data = await self._build_quick_actions_view(agent_id)
            elif view_type == MobileViewType.NOTIFICATIONS:
                dashboard_data = await self._build_notifications_view(agent_id)

            return {
                "view_type": view_type,
                "timestamp": datetime.now().isoformat(),
                "data": dashboard_data
            }

        except Exception as e:
            logger.error(f"Error building mobile dashboard: {e}")
            return {
                "view_type": view_type,
                "timestamp": datetime.now().isoformat(),
                "data": {},
                "error": str(e)
            }

    async def _build_dashboard_view(self, agent_id: str) -> Dict[str, Any]:
        """Build the main dashboard view with key metrics and quick access."""
        # Get key performance indicators
        analytics = await self._get_mobile_analytics(agent_id, days=7)
        urgent_notifications = await self._get_urgent_notifications(agent_id)
        top_leads = await self._get_priority_leads(agent_id, limit=5)
        active_campaigns = await self._get_active_campaigns(agent_id, limit=3)

        return {
            "kpis": {
                "total_leads": analytics.total_leads,
                "conversion_rate": analytics.conversion_rate,
                "roi": analytics.total_roi,
                "urgent_actions": analytics.urgent_actions_needed
            },
            "urgent_notifications": urgent_notifications,
            "priority_leads": top_leads,
            "active_campaigns": active_campaigns,
            "quick_actions": self.default_quick_actions
        }

    async def _build_leads_view(self, agent_id: str) -> Dict[str, Any]:
        """Build the leads view with searchable, filterable lead list."""
        all_leads = await self._get_all_agent_leads(agent_id)

        # Group leads by priority and status
        leads_by_priority = {
            "critical": [lead for lead in all_leads if lead.priority == MobilePriority.CRITICAL],
            "high": [lead for lead in all_leads if lead.priority == MobilePriority.HIGH],
            "normal": [lead for lead in all_leads if lead.priority == MobilePriority.NORMAL],
            "low": [lead for lead in all_leads if lead.priority == MobilePriority.LOW]
        }

        return {
            "total_leads": len(all_leads),
            "leads_by_priority": leads_by_priority,
            "filter_options": {
                "status": ["new", "contacted", "qualified", "nurturing", "ready", "closed"],
                "engagement": ["hot", "warm", "cold"],
                "property_type": ["residential", "commercial", "luxury", "investment"]
            }
        }

    async def _build_campaigns_view(self, agent_id: str) -> Dict[str, Any]:
        """Build the campaigns view with performance metrics and controls."""
        campaigns = await self._get_agent_campaigns(agent_id)

        return {
            "active_campaigns": len([c for c in campaigns if c.status == "active"]),
            "campaigns": campaigns,
            "performance_summary": {
                "best_performing": max(campaigns, key=lambda c: c.roi, default=None),
                "needs_attention": [c for c in campaigns if c.conversion_rate < 0.05]
            }
        }

    async def _build_analytics_view(self, agent_id: str) -> Dict[str, Any]:
        """Build the analytics view with mobile-optimized charts and insights."""
        analytics = await self._get_mobile_analytics(agent_id, days=30)

        return {
            "time_range": "30 days",
            "metrics": analytics,
            "chart_data": {
                "daily_leads": analytics.daily_metrics,
                "channel_performance": analytics.channel_performance,
                "conversion_funnel": analytics.conversion_funnel
            },
            "insights": await self._generate_mobile_insights(analytics)
        }

    async def _build_quick_actions_view(self, agent_id: str) -> Dict[str, Any]:
        """Build the quick actions view with customizable action buttons."""
        agent_profile = await self._get_agent_profile(agent_id)

        # Get context-aware quick actions based on current leads
        priority_leads = await self._get_priority_leads(agent_id, limit=3)
        contextual_actions = await self._generate_contextual_actions(priority_leads)

        return {
            "default_actions": self.default_quick_actions,
            "contextual_actions": contextual_actions,
            "preferences": agent_profile.quick_action_preferences if agent_profile else []
        }

    async def _build_notifications_view(self, agent_id: str) -> Dict[str, Any]:
        """Build the notifications view with categorized alerts and actions."""
        notifications = await self._get_agent_notifications(agent_id)

        # Group notifications by priority and type
        grouped_notifications = {
            "unread": [n for n in notifications if not n.read_at],
            "urgent": [n for n in notifications if n.priority in [MobilePriority.URGENT, MobilePriority.CRITICAL]],
            "actionable": [n for n in notifications if n.action_type],
            "recent": notifications[:10]
        }

        return {
            "total_unread": len(grouped_notifications["unread"]),
            "notifications": grouped_notifications
        }

    async def send_mobile_notification(
        self,
        agent_id: str,
        title: str,
        message: str,
        priority: MobilePriority = MobilePriority.NORMAL,
        action_type: Optional[MobileActionType] = None,
        action_data: Optional[Dict[str, Any]] = None,
        expires_in_minutes: Optional[int] = None
    ) -> MobileNotification:
        """Send a mobile notification to an agent."""
        try:
            expires_at = None
            if expires_in_minutes:
                expires_at = datetime.now() + timedelta(minutes=expires_in_minutes)

            notification = MobileNotification(
                agent_id=agent_id,
                title=title,
                message=message,
                priority=priority,
                action_type=action_type,
                action_data=action_data,
                expires_at=expires_at
            )

            # Store notification (in production, this would go to a database)
            await self._store_notification(notification)

            # Send push notification if enabled
            await self._send_push_notification(notification)

            logger.info(f"Mobile notification sent to agent {agent_id}: {title}")
            return notification

        except Exception as e:
            logger.error(f"Error sending mobile notification: {e}")
            raise

    async def execute_mobile_action(
        self,
        session_id: str,
        action_type: MobileActionType,
        action_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a mobile action with offline capability."""
        try:
            session = self.mobile_sessions.get(session_id)
            if not session:
                raise ValueError(f"Invalid session ID: {session_id}")

            # Check if we're online or offline
            is_online = await self._check_connectivity()

            if is_online:
                # Execute action immediately
                result = await self._execute_action_online(action_type, action_data)

                # Sync any pending offline actions
                if session.offline_actions:
                    await self._sync_offline_actions(session)

            else:
                # Queue action for offline execution
                result = await self._queue_offline_action(session, action_type, action_data)

            return {
                "success": True,
                "action_type": action_type,
                "executed_online": is_online,
                "result": result
            }

        except Exception as e:
            logger.error(f"Error executing mobile action: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _execute_action_online(
        self,
        action_type: MobileActionType,
        action_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an action when online."""
        if action_type == MobileActionType.SEND_MESSAGE:
            return await self._send_message_action(action_data)
        elif action_type == MobileActionType.SEND_VIDEO:
            return await self._send_video_action(action_data)
        elif action_type == MobileActionType.SCHEDULE_CALL:
            return await self._schedule_call_action(action_data)
        elif action_type == MobileActionType.UPDATE_LEAD_STATUS:
            return await self._update_lead_status_action(action_data)
        elif action_type == MobileActionType.SHARE_LISTING:
            return await self._share_listing_action(action_data)
        else:
            return {"message": f"Action {action_type} executed"}

    async def _send_message_action(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute send message action using the personalization engine."""
        lead_id = action_data.get('lead_id')
        message_template = action_data.get('message', 'Quick mobile message')

        # Use the personalization engine for optimized messaging
        personalized_output = await self.personalization_engine.generate_personalized_communication(
            lead_id=lead_id,
            evaluation_result=action_data.get('evaluation_result'),
            message_template=message_template,
            interaction_history=[],
            context=action_data.get('context', {})
        )

        return {
            "message_sent": True,
            "personalized_content": personalized_output.personalized_content[:100],
            "optimal_channel": personalized_output.optimal_channel
        }

    async def _send_video_action(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute send video action using the video integration system."""
        lead_id = action_data.get('lead_id')
        template_id = action_data.get('template_id', 'quick_intro')

        # Use the video integration system
        video_message = await self.video_integration.generate_personalized_video(
            lead_id=lead_id,
            template_id=template_id,
            evaluation_result=action_data.get('evaluation_result'),
            context=action_data.get('context', {})
        )

        return {
            "video_sent": True,
            "video_id": video_message.video_id,
            "template_used": template_id
        }

    async def get_mobile_analytics_chart(
        self,
        agent_id: str,
        chart_type: str,
        time_range: str = "7d"
    ) -> Dict[str, Any]:
        """Generate mobile-optimized analytics charts."""
        try:
            days = int(time_range.rstrip('d'))
            analytics = await self._get_mobile_analytics(agent_id, days)

            if chart_type == "daily_leads":
                chart_data = self._create_daily_leads_chart(analytics.daily_metrics)
            elif chart_type == "channel_performance":
                chart_data = self._create_channel_performance_chart(analytics.channel_performance)
            elif chart_type == "conversion_funnel":
                chart_data = self._create_conversion_funnel_chart(analytics.conversion_funnel)
            elif chart_type == "roi_trend":
                chart_data = self._create_roi_trend_chart(analytics.daily_metrics)
            else:
                raise ValueError(f"Unknown chart type: {chart_type}")

            return {
                "chart_type": chart_type,
                "data": chart_data,
                "mobile_optimized": True
            }

        except Exception as e:
            logger.error(f"Error generating mobile chart: {e}")
            return {"error": str(e)}

    def _create_daily_leads_chart(self, daily_metrics: List[Dict]) -> Dict[str, Any]:
        """Create a mobile-optimized daily leads chart."""
        df = pd.DataFrame(daily_metrics)

        fig = px.line(
            df, x='date', y='leads',
            title='Daily Leads Trend',
            line_shape='linear'
        )

        # Mobile optimization
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=40, b=20),
            font=dict(size=12),
            showlegend=False
        )

        return fig.to_dict()

    def _create_channel_performance_chart(self, channel_data: List[Dict]) -> Dict[str, Any]:
        """Create a mobile-optimized channel performance chart."""
        df = pd.DataFrame(channel_data)

        fig = px.bar(
            df, x='channel', y='performance',
            title='Channel Performance',
            color='performance',
            color_continuous_scale='viridis'
        )

        # Mobile optimization
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=40, b=20),
            font=dict(size=10),
            xaxis_tickangle=-45
        )

        return fig.to_dict()

    async def configure_mobile_notifications(
        self,
        agent_id: str,
        notification_preferences: Dict[str, bool]
    ) -> Dict[str, Any]:
        """Configure mobile notification preferences for an agent."""
        try:
            # Update agent profile with notification preferences
            profile = await self._get_agent_profile(agent_id)
            if profile:
                profile.notification_preferences = notification_preferences
                await self._update_agent_profile(profile)

            return {
                "success": True,
                "preferences": notification_preferences,
                "message": "Notification preferences updated successfully"
            }

        except Exception as e:
            logger.error(f"Error configuring mobile notifications: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # Helper methods (simplified implementations for demonstration)

    async def _get_mobile_analytics(self, agent_id: str, days: int) -> MobileAnalytics:
        """Get mobile analytics data for the specified time period."""
        # In production, this would query actual data
        return MobileAnalytics(
            date_range=f"{days} days",
            total_leads=45,
            active_campaigns=3,
            conversion_rate=0.15,
            total_roi=2.3,
            top_performing_channel="Email",
            urgent_actions_needed=2,
            daily_metrics=[
                {"date": "2026-01-09", "leads": 8, "conversions": 1, "roi": 2.1},
                {"date": "2026-01-08", "leads": 12, "conversions": 2, "roi": 2.5}
            ],
            channel_performance=[
                {"channel": "Email", "performance": 0.18},
                {"channel": "SMS", "performance": 0.12},
                {"channel": "Phone", "performance": 0.25}
            ],
            conversion_funnel=[
                {"stage": "Initial Contact", "count": 100},
                {"stage": "Qualified Lead", "count": 45},
                {"stage": "Property Viewing", "count": 25},
                {"stage": "Offer Made", "count": 8},
                {"stage": "Closed", "count": 3}
            ]
        )

    async def _get_priority_leads(self, agent_id: str, limit: int = 5) -> List[MobileLeadSummary]:
        """Get priority leads for mobile display."""
        # In production, this would query actual lead data
        return [
            MobileLeadSummary(
                lead_id="lead_001",
                name="John Smith",
                phone="555-0123",
                email="john@email.com",
                lead_status="qualified",
                lead_score=0.85,
                last_interaction=datetime.now() - timedelta(hours=2),
                next_action="Schedule showing",
                property_interest="Single family home",
                engagement_level="hot",
                priority=MobilePriority.HIGH,
                quick_actions=self.default_quick_actions[:3]
            )
        ]

    async def _get_urgent_notifications(self, agent_id: str) -> List[MobileNotification]:
        """Get urgent notifications for an agent."""
        # In production, this would query actual notifications
        return []

    async def _get_active_campaigns(self, agent_id: str, limit: int = 3) -> List[MobileCampaignSummary]:
        """Get active campaigns for mobile display."""
        # In production, this would query actual campaign data
        return []

    async def _store_notification(self, notification: MobileNotification) -> None:
        """Store a notification (placeholder for database storage)."""
        pass

    async def _send_push_notification(self, notification: MobileNotification) -> None:
        """Send push notification to mobile device (placeholder for push service)."""
        pass

    async def _check_connectivity(self) -> bool:
        """Check if the device is online."""
        return True  # Simplified for demonstration

    async def _queue_offline_action(
        self,
        session: MobileSession,
        action_type: MobileActionType,
        action_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Queue an action for offline execution."""
        offline_action = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "action_data": action_data
        }

        session.offline_actions.append(offline_action)
        session.sync_pending = True

        return {"queued_for_sync": True, "action": offline_action}

    async def _sync_offline_actions(self, session: MobileSession) -> None:
        """Sync pending offline actions when connectivity is restored."""
        for action in session.offline_actions:
            try:
                await self._execute_action_online(
                    MobileActionType(action["action_type"]),
                    action["action_data"]
                )
            except Exception as e:
                logger.error(f"Error syncing offline action: {e}")

        session.offline_actions.clear()
        session.sync_pending = False
        session.last_sync = datetime.now()


# Streamlit Mobile Components

class MobileDashboardComponent:
    """Streamlit component for mobile dashboard interface."""

    def __init__(self, mobile_service: MobileAgentExperience):
        self.mobile_service = mobile_service

    def render_mobile_dashboard(self, agent_id: str) -> None:
        """Render the main mobile dashboard."""
        st.set_page_config(
            page_title="Mobile Agent Dashboard",
            layout="wide",
            initial_sidebar_state="collapsed"
        )

        # Mobile-optimized styling
        st.markdown("""
        <style>
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin: 0.5rem 0;
        }
        .quick-action-btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 0.8rem;
            border-radius: 8px;
            margin: 0.2rem;
            width: 100%;
            font-size: 16px;
        }
        .notification-urgent {
            background: #ff4444;
            color: white;
            padding: 0.5rem;
            border-radius: 5px;
            margin: 0.2rem 0;
        }
        .mobile-container {
            max-width: 480px;
            margin: 0 auto;
        }
        </style>
        """, unsafe_allow_html=True)

        # Main container
        with st.container():
            st.markdown('<div class="mobile-container">', unsafe_allow_html=True)

            # Header
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.title("📱 Agent Hub")

            # Quick metrics
            dashboard_data = asyncio.run(
                self.mobile_service.get_mobile_dashboard(
                    agent_id, MobileViewType.DASHBOARD
                )
            )

            if 'data' in dashboard_data and 'kpis' in dashboard_data['data']:
                kpis = dashboard_data['data']['kpis']

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>{kpis['total_leads']}</h3>
                        <p>Active Leads</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>{kpis['conversion_rate']:.1%}</h3>
                        <p>Conversion Rate</p>
                    </div>
                    """, unsafe_allow_html=True)

                col3, col4 = st.columns(2)
                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>${kpis['roi']:.1f}x</h3>
                        <p>ROI</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col4:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>{kpis['urgent_actions']}</h3>
                        <p>Urgent Actions</p>
                    </div>
                    """, unsafe_allow_html=True)

            # Quick actions
            st.subheader("Quick Actions")
            quick_actions = dashboard_data.get('data', {}).get('quick_actions', [])

            for i in range(0, len(quick_actions), 2):
                col1, col2 = st.columns(2)

                with col1:
                    if i < len(quick_actions):
                        action = quick_actions[i]
                        if st.button(f"{action.icon} {action.label}", key=f"action_{i}"):
                            st.success(f"{action.label} action triggered!")

                with col2:
                    if i + 1 < len(quick_actions):
                        action = quick_actions[i + 1]
                        if st.button(f"{action.icon} {action.label}", key=f"action_{i+1}"):
                            st.success(f"{action.label} action triggered!")

            # Recent notifications
            if 'urgent_notifications' in dashboard_data.get('data', {}):
                urgent_notifications = dashboard_data['data']['urgent_notifications']
                if urgent_notifications:
                    st.subheader("Urgent Notifications")
                    for notification in urgent_notifications[:3]:
                        st.markdown(f"""
                        <div class="notification-urgent">
                            <strong>{notification.title}</strong><br>
                            {notification.message}
                        </div>
                        """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    # Example usage for testing
    mobile_service = MobileAgentExperience()

    # Initialize a test session
    session = asyncio.run(mobile_service.initialize_mobile_session(
        "agent_001",
        {"type": "mobile", "device_id": "test_device", "app_version": "1.0.0"}
    ))

    print(f"Mobile session initialized: {session.session_id}")

    # Send a test notification
    notification = asyncio.run(mobile_service.send_mobile_notification(
        "agent_001",
        "Hot Lead Alert",
        "John Smith is highly engaged and ready to view properties!",
        MobilePriority.HIGH,
        MobileActionType.SCHEDULE_CALL,
        {"lead_id": "lead_001", "phone": "555-0123"}
    ))

    print(f"Notification sent: {notification.notification_id}")