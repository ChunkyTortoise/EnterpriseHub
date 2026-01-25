"""
Socket.IO Adapter for Jorge's Real Estate AI Platform

Bridges the gap between native WebSocket backend and Socket.IO frontend
by providing Socket.IO compatibility layer on top of the existing
WebSocket infrastructure.

This adapter ensures horizontal scalability by:
- Maintaining existing WebSocket server infrastructure
- Adding Socket.IO compatibility for frontend integration
- Supporting multiple backend instances with session affinity
- Preserving enterprise authentication and event broadcasting
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Set, List
from datetime import datetime, timezone
import socketio
from socketio import AsyncNamespace

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.websocket_server import (
    get_websocket_manager,
    WebSocketClient,
    RealTimeEvent,
    EventType,
    ConnectionStatus
)
from ghl_real_estate_ai.services.auth_service import UserRole
from ghl_real_estate_ai.api.enterprise.auth import enterprise_auth_service
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)

class JorgeSocketNamespace(AsyncNamespace):
    """
    Socket.IO Namespace for Jorge's Real Estate Platform

    Provides Socket.IO compatibility while leveraging the existing
    enterprise WebSocket infrastructure for connection management,
    authentication, and event broadcasting.
    """

    def __init__(self, namespace: str = '/'):
        super().__init__(namespace)
        self.websocket_manager = get_websocket_manager()
        self.auth_service = enterprise_auth_service
        self.cache_service = get_cache_service()

        # Session tracking for Socket.IO compatibility
        self.socketio_sessions: Dict[str, Dict[str, Any]] = {}
        self.user_sessions: Dict[int, Set[str]] = {}  # user_id -> session_ids

        logger.info("Jorge Socket.IO Namespace initialized")

    async def on_connect(self, sid: str, environ: Dict, auth: Optional[Dict] = None):
        """
        Handle Socket.IO client connection

        Args:
            sid: Socket.IO session ID
            environ: WSGI environment
            auth: Authentication data from client
        """
        try:
            logger.info(f"Socket.IO connection attempt: {sid}")

            # Extract authentication token - preferring enterprise_jwt_token for platform consistency
            token = None
            if auth:
                token = auth.get('enterprise_jwt_token') or auth.get('token')

            if not token:
                # Check standard Authorization header
                if 'HTTP_AUTHORIZATION' in environ:
                    auth_header = environ['HTTP_AUTHORIZATION']
                    if auth_header.startswith('Bearer '):
                        token = auth_header[7:]
                # Fallback to specific enterprise header
                elif 'HTTP_X_ENTERPRISE_TOKEN' in environ:
                    token = environ['HTTP_X_ENTERPRISE_TOKEN']

            if not token:
                logger.warning(f"Socket.IO connection rejected - missing token: {sid}")
                return False

            # Authenticate using existing WebSocket authentication
            user = await self._authenticate_token(token)
            if not user:
                logger.warning(f"Socket.IO authentication failed: {sid}")
                return False

            # Create session tracking
            session_data = {
                'user_id': user.id,
                'username': user.username,
                'role': user.role,
                'connected_at': datetime.now(timezone.utc),
                'last_activity': datetime.now(timezone.utc),
                'subscribed_events': self._get_default_subscriptions(user.role),
                'location_id': auth.get('location_id') if auth else None
            }

            self.socketio_sessions[sid] = session_data

            # Track by user
            if user.id not in self.user_sessions:
                self.user_sessions[user.id] = set()
            self.user_sessions[user.id].add(sid)

            # Cache session info
            await self.cache_service.set(
                f"socketio:session:{sid}",
                session_data,
                ttl=3600  # 1 hour
            )

            logger.info(f"Socket.IO authenticated: {user.username} (sid: {sid}, role: {user.role.value})")

            # Send welcome message in Socket.IO format
            await self.emit('connection_established', {
                'message': f'Welcome, {user.username}! Jorge Real Estate AI Platform connected.',
                'session_id': sid,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'role': user.role.value
                },
                'subscriptions': [event.value for event in session_data['subscribed_events']],
                'server_time': datetime.now(timezone.utc).isoformat()
            }, room=sid)

            # Broadcast user connection event
            await self._broadcast_to_websockets(RealTimeEvent(
                event_type=EventType.USER_ACTIVITY,
                data={
                    'action': 'socketio_user_connected',
                    'username': user.username,
                    'role': user.role.value,
                    'session_id': sid
                },
                timestamp=datetime.now(timezone.utc),
                priority='low'
            ), target_roles={UserRole.ADMIN})

            return True

        except Exception as e:
            logger.error(f"Socket.IO connection error for {sid}: {e}")
            return False

    async def on_disconnect(self, sid: str):
        """Handle Socket.IO client disconnection"""
        try:
            if sid not in self.socketio_sessions:
                return

            session = self.socketio_sessions[sid]
            user_id = session['user_id']
            username = session['username']

            # Remove session tracking
            del self.socketio_sessions[sid]

            if user_id in self.user_sessions:
                self.user_sessions[user_id].discard(sid)
                if not self.user_sessions[user_id]:
                    del self.user_sessions[user_id]

            # Clean up cache
            await self.cache_service.delete(f"socketio:session:{sid}")

            # Calculate session duration
            session_duration = (datetime.now(timezone.utc) - session['connected_at']).total_seconds()

            # Broadcast disconnection event
            await self._broadcast_to_websockets(RealTimeEvent(
                event_type=EventType.USER_ACTIVITY,
                data={
                    'action': 'socketio_user_disconnected',
                    'username': username,
                    'role': session['role'].value,
                    'session_id': sid,
                    'session_duration': session_duration
                },
                timestamp=datetime.now(timezone.utc),
                priority='low'
            ), target_roles={UserRole.ADMIN})

            logger.info(f"Socket.IO disconnected: {username} (sid: {sid})")

        except Exception as e:
            logger.error(f"Socket.IO disconnect error for {sid}: {e}")

    async def on_join_dashboard(self, sid: str, data: Dict[str, Any]):
        """Handle dashboard join request"""
        try:
            if sid not in self.socketio_sessions:
                return

            session = self.socketio_sessions[sid]
            session['last_activity'] = datetime.now(timezone.utc)

            client_type = data.get('client_type', 'unknown')
            dashboard_version = data.get('dashboard_version', '1.0.0')

            logger.info(f"Dashboard joined: {session['username']} (client: {client_type}, version: {dashboard_version})")

            # Send current system status
            await self.emit('dashboard_status', {
                'status': 'connected',
                'platform': 'Jorge Real Estate AI',
                'version': dashboard_version,
                'user': {
                    'username': session['username'],
                    'role': session['role'].value
                },
                'timestamp': datetime.now(timezone.utc).isoformat()
            }, room=sid)

        except Exception as e:
            logger.error(f"Dashboard join error for {sid}: {e}")

    async def on_subscribe_contact(self, sid: str, data: Dict[str, Any]):
        """Subscribe to contact-specific events"""
        try:
            if sid not in self.socketio_sessions:
                return

            contact_id = data.get('contact_id')
            location_id = data.get('location_id')

            if not contact_id:
                await self.emit('error', {'message': 'contact_id required'}, room=sid)
                return

            # Store subscription in session
            session = self.socketio_sessions[sid]
            if 'contact_subscriptions' not in session:
                session['contact_subscriptions'] = set()
            session['contact_subscriptions'].add(contact_id)
            session['last_activity'] = datetime.now(timezone.utc)

            await self.emit('subscription_confirmed', {
                'contact_id': contact_id,
                'location_id': location_id,
                'status': 'subscribed'
            }, room=sid)

            logger.debug(f"Contact subscription: {session['username']} -> {contact_id}")

        except Exception as e:
            logger.error(f"Contact subscription error for {sid}: {e}")

    async def on_request_bot_status(self, sid: str, data: Dict[str, Any]):
        """Handle bot status request"""
        try:
            if sid not in self.socketio_sessions:
                return

            bot_type = data.get('bot_type')
            session = self.socketio_sessions[sid]
            session['last_activity'] = datetime.now(timezone.utc)

            # This would integrate with actual bot status services
            # For now, return mock status
            bot_status = {
                'bot_type': bot_type,
                'status': 'operational',
                'active_conversations': 12,
                'response_time_ms': 245,
                'success_rate': 0.94,
                'last_updated': datetime.now(timezone.utc).isoformat()
            }

            await self.emit('bot_status_response', bot_status, room=sid)

        except Exception as e:
            logger.error(f"Bot status request error for {sid}: {e}")

    async def on_request_bot_handoff(self, sid: str, data: Dict[str, Any]):
        """Handle bot handoff requests"""
        try:
            if sid not in self.socketio_sessions:
                return

            session = self.socketio_sessions[sid]
            conversation_id = data.get('conversation_id')
            target_bot = data.get('target_bot')
            handoff_reason = data.get('reason', 'manual_request')

            if not conversation_id or not target_bot:
                await self.emit('error', {'message': 'conversation_id and target_bot required'}, room=sid)
                return

            # Generate handoff ID and emit handoff request event
            handoff_id = f"handoff_{int(datetime.now(timezone.utc).timestamp())}_{sid[:8]}"

            await self._broadcast_to_websockets(RealTimeEvent(
                event_type=EventType.BOT_HANDOFF_REQUEST,
                data={
                    'handoff_id': handoff_id,
                    'from_bot': 'claude-concierge',
                    'to_bot': target_bot,
                    'contact_id': data.get('contact_id', ''),
                    'handoff_reason': handoff_reason,
                    'context_summary': {
                        'conversation_length': data.get('conversation_length', 0),
                        'initiated_by': session['username']
                    },
                    'urgency': data.get('urgency', 'normal')
                },
                timestamp=datetime.now(timezone.utc),
                user_id=session['user_id']
            ))

            await self.emit('bot_handoff_initiated', {
                'handoff_id': handoff_id,
                'target_bot': target_bot,
                'status': 'initiated'
            }, room=sid)

            logger.info(f"Bot handoff requested: {session['username']} → {target_bot} (ID: {handoff_id})")

        except Exception as e:
            logger.error(f"Bot handoff request error for {sid}: {e}")

    async def on_provide_coaching(self, sid: str, data: Dict[str, Any]):
        """Handle real-time coaching from Claude Concierge"""
        try:
            if sid not in self.socketio_sessions:
                return

            session = self.socketio_sessions[sid]
            conversation_id = data.get('conversation_id')
            coaching_type = data.get('coaching_type')
            coaching_message = data.get('coaching_message')

            if not conversation_id or not coaching_type:
                await self.emit('error', {'message': 'conversation_id and coaching_type required'}, room=sid)
                return

            # Emit coaching event
            await self._broadcast_to_websockets(RealTimeEvent(
                event_type=EventType.COACHING_OPPORTUNITY_DETECTED,
                data={
                    'conversation_id': conversation_id,
                    'coaching_type': coaching_type,
                    'coaching_message': coaching_message,
                    'urgency': data.get('urgency', 'informational'),
                    'provided_by': session['username']
                },
                timestamp=datetime.now(timezone.utc),
                user_id=session['user_id']
            ))

            await self.emit('coaching_delivered', {
                'conversation_id': conversation_id,
                'coaching_type': coaching_type,
                'status': 'delivered'
            }, room=sid)

            logger.info(f"Coaching provided: {session['username']} → {coaching_type} (conversation: {conversation_id})")

        except Exception as e:
            logger.error(f"Coaching provision error for {sid}: {e}")

    async def on_request_coordination_metrics(self, sid: str, data: Dict[str, Any]):
        """Handle coordination metrics requests"""
        try:
            if sid not in self.socketio_sessions:
                return

            session = self.socketio_sessions[sid]

            # Mock coordination metrics - would integrate with actual coordination engine
            metrics = {
                'active_bot_sessions': 8,
                'handoffs_today': 12,
                'avg_handoff_time_ms': 850,
                'coaching_opportunities_detected': 5,
                'coordination_success_rate': 0.94,
                'omnipresent_conversations': 3,
                'last_updated': datetime.now(timezone.utc).isoformat()
            }

            await self.emit('coordination_metrics_response', metrics, room=sid)

        except Exception as e:
            logger.error(f"Coordination metrics request error for {sid}: {e}")

    async def on_sync_context_request(self, sid: str, data: Dict[str, Any]):
        """Handle context synchronization requests across bots"""
        try:
            if sid not in self.socketio_sessions:
                return

            session = self.socketio_sessions[sid]
            conversation_id = data.get('conversation_id')
            context_update = data.get('context_update', {})

            if not conversation_id:
                await self.emit('error', {'message': 'conversation_id required'}, room=sid)
                return

            # Emit context sync event
            await self._broadcast_to_websockets(RealTimeEvent(
                event_type=EventType.CONTEXT_SYNC_UPDATE,
                data={
                    'conversation_id': conversation_id,
                    'context_update': context_update,
                    'sync_initiated_by': session['username'],
                    'sync_timestamp': datetime.now(timezone.utc).isoformat()
                },
                timestamp=datetime.now(timezone.utc),
                user_id=session['user_id']
            ))

            await self.emit('context_sync_confirmed', {
                'conversation_id': conversation_id,
                'status': 'synchronized'
            }, room=sid)

            logger.info(f"Context sync requested: {session['username']} (conversation: {conversation_id})")

        except Exception as e:
            logger.error(f"Context sync error for {sid}: {e}")

    # Additional Socket.IO event handlers for Jorge-specific events
    async def on_enable_omnipresent_monitoring(self, sid: str, data: Dict[str, Any]):
        """Enable omnipresent monitoring for conversation coordination"""
        try:
            if sid not in self.socketio_sessions:
                return

            session = self.socketio_sessions[sid]
            conversation_id = data.get('conversation_id')
            contact_id = data.get('contact_id')
            location_id = data.get('location_id')

            # Store omnipresent monitoring subscription
            if 'omnipresent_subscriptions' not in session:
                session['omnipresent_subscriptions'] = {}

            session['omnipresent_subscriptions'][conversation_id] = {
                'contact_id': contact_id,
                'location_id': location_id,
                'monitoring_level': data.get('monitoring_level', 'full'),
                'capabilities': data.get('capabilities', []),
                'subscribed_at': datetime.now(timezone.utc)
            }

            await self.emit('omnipresent_monitoring_enabled', {
                'conversation_id': conversation_id,
                'status': 'active',
                'capabilities': data.get('capabilities', [])
            }, room=sid)

            logger.info(f"Omnipresent monitoring enabled: {session['username']} -> {conversation_id}")

        except Exception as e:
            logger.error(f"Omnipresent monitoring error for {sid}: {e}")

    async def on_send_message(self, sid: str, data: Dict[str, Any]):
        """Handle incoming message from user to lead"""
        try:
            if sid not in self.socketio_sessions:
                return

            session = self.socketio_sessions[sid]
            message = data.get('message')
            contact_id = data.get('contact_id')

            logger.info(f"Message sent from {session['username']} to {contact_id}: {message}")

            # Emit back confirmation
            await self.emit('message_delivered', {
                'status': 'sent',
                'message_id': f"msg_{int(datetime.now().timestamp())}",
                'timestamp': datetime.now().isoformat()
            }, room=sid)

            # INTEGRATION: Submit task to mesh for conversation analysis
            from ghl_real_estate_ai.services.agent_mesh_coordinator import get_mesh_coordinator, AgentTask, TaskPriority, AgentCapability
            mesh = get_mesh_coordinator()
            
            task = AgentTask(
                task_id=f"msg_analysis_{int(datetime.now().timestamp())}",
                task_type="conversation_analysis",
                priority=TaskPriority.NORMAL,
                capabilities_required=[AgentCapability.CONVERSATION_ANALYSIS],
                payload={"message": message, "contact_id": contact_id},
                created_at=datetime.now(),
                deadline=datetime.now() + timedelta(seconds=30),
                max_cost=0.05,
                requester_id=str(session['user_id'])
            )
            await mesh.submit_task(task)
            
        except Exception as e:
            logger.error(f"Error in on_send_message: {e}")

    async def on_request_handoff(self, sid: str, data: Dict[str, Any]):
        """Handle manual handoff request from UI"""
        try:
            if sid not in self.socketio_sessions:
                return

            session = self.socketio_sessions[sid]
            contact_id = data.get('contact_id')
            target_agent = data.get('target_agent', 'jorge_seller')

            logger.info(f"Handoff requested by {session['username']} for {contact_id} to {target_agent}")

            # INTEGRATION: Trigger handoff task in mesh
            from ghl_real_estate_ai.services.agent_mesh_coordinator import get_mesh_coordinator, AgentTask, TaskPriority, AgentCapability
            mesh = get_mesh_coordinator()
            
            task = AgentTask(
                task_id=f"handoff_{int(datetime.now().timestamp())}",
                task_type="lead_qualification",
                priority=TaskPriority.HIGH,
                capabilities_required=[AgentCapability.LEAD_QUALIFICATION],
                payload={"action": "handoff", "target": target_agent, "contact_id": contact_id},
                created_at=datetime.now(),
                deadline=datetime.now() + timedelta(seconds=60),
                max_cost=0.10,
                requester_id=str(session['user_id'])
            )
            await mesh.submit_task(task)

            # Emit handoff confirmation
            await self.emit('handoff_status', {
                'status': 'processing',
                'handoff_id': task.task_id,
                'target': target_agent
            }, room=sid)

        except Exception as e:
            logger.error(f"Error in on_request_handoff: {e}")

    async def on_simulate_traffic(self, sid: str, data: Dict[str, Any] = None):
        """Mock traffic generator for UI evaluation"""
        try:
            import random
            names = ["Alice Smith", "Bob Johnson", "Carol Williams", "David Brown", "Eve Davis"]
            locations = ["Austin, TX", "Dallas, TX", "San Antonio, TX", "Houston, TX"]
            actions = ["SCHEDULE_SHOWING", "ACCELERATE_SEQUENCE", "RE_ENGAGEMENT_REQUIRED", "SOFT_FOLLOWUP"]
            
            lead_name = random.choice(names)
            
            # 1. Send immediate lead update
            await self.emit('lead_update', {
                'lead_name': lead_name,
                'location': random.choice(locations),
                'pcs_score': random.randint(40, 95)
            }, room=sid)
            
            # 2. Send AI Intent Signal
            await self.emit('realtime_intent_update', {
                'contact_id': f"contact_{int(datetime.now().timestamp())}",
                'intent_update': {
                    'recommended_action': random.choice(actions),
                    'frs_delta': random.uniform(-5, 10),
                    'pcs_delta': random.uniform(-2, 15)
                }
            }, room=sid)
            
            # 3. Update mesh stats
            await self.emit('performance_metrics', {
                'current_hour_cost': random.uniform(10.0, 25.0),
                'total_tasks': random.randint(50, 200)
            }, room=sid)
            
            logger.info(f"Enhanced simulated traffic sent to session {sid}")
        except Exception as e:
            logger.error(f"Error in simulation: {e}")

    # Helper methods
    async def _authenticate_token(self, token: str) -> Optional[Any]:
        """Authenticate JWT token using enterprise auth service"""
        try:
            auth_data = await self.auth_service.validate_enterprise_token(token)
            if not auth_data or 'user' not in auth_data:
                return None

            # Create a simple object-like structure for compatibility with existing logic
            user_data = auth_data['user']
            
            class UserInfo:
                def __init__(self, data):
                    self.id = data.get('user_id')
                    self.username = data.get('email')  # Using email as username for enterprise users
                    self.role = UserRole.ADMIN if "tenant_admin" in data.get('roles', []) else UserRole.AGENT
            
            return UserInfo(user_data)

        except Exception as e:
            logger.error(f"Token authentication error: {e}")
            return None

    def _get_default_subscriptions(self, role: UserRole) -> Set[EventType]:
        """Get default event subscriptions based on user role"""
        if role == UserRole.ADMIN:
            return set(EventType)
        elif role == UserRole.AGENT:
            return {
                EventType.LEAD_UPDATE,
                EventType.CONVERSATION_UPDATE,
                EventType.COMMISSION_UPDATE,
                EventType.DASHBOARD_REFRESH,
                EventType.PERFORMANCE_UPDATE,
                EventType.PROPERTY_ALERT
            }
        else:  # VIEWER
            return {
                EventType.DASHBOARD_REFRESH,
                EventType.SYSTEM_ALERT
            }

    async def _broadcast_to_websockets(self, event: RealTimeEvent, target_roles: Optional[Set[UserRole]] = None):
        """Bridge to native WebSocket system for event broadcasting"""
        try:
            await self.websocket_manager.broadcast_event(event, target_roles=target_roles)
        except Exception as e:
            logger.error(f"WebSocket bridge error: {e}")

    async def broadcast_to_socketio(self, event: RealTimeEvent, target_users: Optional[Set[int]] = None):
        """
        Broadcast event to Socket.IO clients

        This method is called by the WebSocket system to relay events
        to Socket.IO clients for compatibility.
        """
        try:
            # Convert WebSocket event to Socket.IO format
            socketio_event_map = {
                EventType.LEAD_UPDATE: 'lead_update',
                EventType.CONVERSATION_UPDATE: 'conversation_event',
                EventType.COMMISSION_UPDATE: 'commission_update',
                EventType.SYSTEM_ALERT: 'system_health_update',
                EventType.PERFORMANCE_UPDATE: 'performance_metrics',
                EventType.USER_ACTIVITY: 'user_activity',
                EventType.DASHBOARD_REFRESH: 'dashboard_refresh',
                EventType.PROPERTY_ALERT: 'property_alert',
                EventType.LEAD_METRIC_UPDATE: 'lead_metric_update'
            }

            socketio_event_name = socketio_event_map.get(event.event_type, 'real_time_event')

            # Determine target sessions
            target_sessions = []

            if target_users:
                # Target specific users
                for user_id in target_users:
                    if user_id in self.user_sessions:
                        target_sessions.extend(self.user_sessions[user_id])
            else:
                # Target all sessions that should receive this event type
                for sid, session in self.socketio_sessions.items():
                    if event.event_type in session.get('subscribed_events', set()):
                        target_sessions.append(sid)

            # Send to target sessions
            if target_sessions:
                await self.emit(socketio_event_name, event.to_dict(), room=target_sessions)
                logger.debug(f"Broadcasted {socketio_event_name} to {len(target_sessions)} Socket.IO sessions")

        except Exception as e:
            logger.error(f"Socket.IO broadcast error: {e}")


class SocketIOManager:
    """
    Socket.IO Server Manager for horizontal scalability

    Manages Socket.IO server with Redis adapter for multi-instance scaling
    and integration with existing WebSocket infrastructure.
    """

    def __init__(self):
        self.sio = None
        self.jorge_namespace = None
        self.websocket_manager = get_websocket_manager()
        logger.info("Socket.IO Manager initialized")

    def create_server(self, app=None, cors_allowed_origins="*"):
        """Create Socket.IO server with Redis adapter for scaling"""
        try:
            # Create Socket.IO server with Redis adapter for horizontal scaling
            import os
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

            mgr = socketio.AsyncRedisManager(redis_url)

            self.sio = socketio.AsyncServer(
                async_mode='asgi',
                cors_allowed_origins=cors_allowed_origins,
                client_manager=mgr,  # Redis adapter for scaling
                logger=True,
                engineio_logger=False
            )

            # Create Jorge namespace
            self.jorge_namespace = JorgeSocketNamespace('/')
            self.sio.register_namespace(self.jorge_namespace)

            # Bridge events from WebSocket manager to Socket.IO
            self._setup_websocket_bridge()

            logger.info("Socket.IO server created with Redis adapter for scaling")
            return self.sio

        except Exception as e:
            logger.error(f"Socket.IO server creation error: {e}")
            raise

    def _setup_websocket_bridge(self):
        """Setup bridge between WebSocket manager and Socket.IO"""
        # This would be called by the WebSocket manager to relay events
        # In a production setup, this would use Redis pub/sub or message queues

        # For now, we'll add a method to the WebSocket manager to call Socket.IO
        if hasattr(self.websocket_manager, 'socketio_bridge'):
            self.websocket_manager.socketio_bridge = self.jorge_namespace.broadcast_to_socketio

    def get_server(self) -> socketio.AsyncServer:
        """Get Socket.IO server instance"""
        return self.sio

# Global Socket.IO manager instance
_socketio_manager = None

def get_socketio_manager() -> SocketIOManager:
    """Get singleton Socket.IO manager instance"""
    global _socketio_manager
    if _socketio_manager is None:
        _socketio_manager = SocketIOManager()
    return _socketio_manager