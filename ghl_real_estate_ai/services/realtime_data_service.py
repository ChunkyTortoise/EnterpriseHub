"""
Real-Time Data Service for GHL Real Estate AI Dashboard

Provides WebSocket-based real-time updates with intelligent caching and fallback polling.
Supports live scoring, alerts, analytics, and performance metrics.
"""

import asyncio
import json
import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import streamlit as st

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

@dataclass
class RealtimeEvent:
    """Real-time event data structure"""
    id: str
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    priority: int = 1  # 1=low, 2=normal, 3=high, 4=critical
    source: str = "system"

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat()
        }

class EventType(Enum):
    """Supported real-time event types"""
    LEAD_SCORE_UPDATE = "lead_score_update"
    NEW_ALERT = "new_alert"
    PERFORMANCE_UPDATE = "performance_update"
    ANALYTICS_UPDATE = "analytics_update"
    SYSTEM_STATUS = "system_status"
    USER_ACTION = "user_action"

class RealtimeDataService:
    """
    Production-grade real-time data service with hybrid approach:
    - WebSocket for instant updates when available
    - Intelligent polling as fallback
    - Event caching and deduplication
    - Mobile-optimized data compression
    """

    def __init__(self, use_websocket: bool = True, poll_interval: int = 2):
        self.use_websocket = use_websocket and WEBSOCKETS_AVAILABLE
        self.poll_interval = poll_interval
        self.is_running = False

        # Event management
        self.event_queue: List[RealtimeEvent] = []
        self.event_cache: Dict[str, RealtimeEvent] = {}
        self.subscribers: Dict[str, List[Callable]] = {}
        self.max_events = 1000

        # WebSocket connection
        self.websocket_url = "ws://localhost:8765"  # Configure based on environment
        self.websocket = None
        self.connection_attempts = 0
        self.max_reconnect_attempts = 5

        # Polling thread
        self.poll_thread = None
        self.last_poll_time = datetime.now()

        # Performance metrics
        self.metrics = {
            'events_processed': 0,
            'events_sent': 0,
            'connection_errors': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }

        # Initialize session state
        if 'realtime_service' not in st.session_state:
            st.session_state.realtime_service = self

    def start(self) -> bool:
        """Start the real-time service"""
        if self.is_running:
            return True

        self.is_running = True

        if self.use_websocket:
            success = self._start_websocket()
            if not success:
                # Fallback to polling
                self._start_polling()
        else:
            self._start_polling()

        return True

    def stop(self):
        """Stop the real-time service"""
        self.is_running = False

        if self.websocket:
            asyncio.create_task(self.websocket.close())

        if self.poll_thread and self.poll_thread.is_alive():
            self.poll_thread.join(timeout=1)

    def _start_websocket(self) -> bool:
        """Start WebSocket connection"""
        if not WEBSOCKETS_AVAILABLE:
            return False

        try:
            # Create WebSocket connection in background
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def websocket_client():
                try:
                    async with websockets.connect(self.websocket_url) as websocket:
                        self.websocket = websocket
                        self.connection_attempts = 0

                        async for message in websocket:
                            if not self.is_running:
                                break

                            try:
                                event_data = json.loads(message)
                                event = RealtimeEvent(**event_data)
                                self._process_event(event)
                            except Exception as e:
                                print(f"Error processing WebSocket message: {e}")

                except Exception as e:
                    self.connection_attempts += 1
                    self.metrics['connection_errors'] += 1
                    print(f"WebSocket connection failed (attempt {self.connection_attempts}): {e}")

                    if self.connection_attempts < self.max_reconnect_attempts:
                        await asyncio.sleep(2 ** self.connection_attempts)  # Exponential backoff
                        return await websocket_client()
                    else:
                        print("Max WebSocket reconnection attempts reached, falling back to polling")
                        self._start_polling()
                        return False

            # Run WebSocket client in background thread
            def run_websocket():
                loop.run_until_complete(websocket_client())

            websocket_thread = threading.Thread(target=run_websocket, daemon=True)
            websocket_thread.start()

            return True

        except Exception as e:
            print(f"Failed to start WebSocket: {e}")
            return False

    def _start_polling(self):
        """Start polling fallback"""
        def poll_loop():
            while self.is_running:
                try:
                    self._poll_data_sources()
                    time.sleep(self.poll_interval)
                except Exception as e:
                    print(f"Polling error: {e}")
                    time.sleep(self.poll_interval * 2)  # Longer sleep on error

        self.poll_thread = threading.Thread(target=poll_loop, daemon=True)
        self.poll_thread.start()

    def _poll_data_sources(self):
        """Poll various data sources for updates"""
        current_time = datetime.now()

        # Only poll if enough time has passed
        if (current_time - self.last_poll_time).total_seconds() < self.poll_interval:
            return

        self.last_poll_time = current_time

        # Generate sample events for demonstration
        # In production, this would poll actual services
        sample_events = self._generate_sample_events()

        for event in sample_events:
            self._process_event(event)

    def _generate_sample_events(self) -> List[RealtimeEvent]:
        """Generate sample events for demonstration"""
        import random

        events = []
        current_time = datetime.now()

        # Lead score update (30% chance)
        if random.random() < 0.3:
            events.append(RealtimeEvent(
                id=str(uuid.uuid4()),
                event_type=EventType.LEAD_SCORE_UPDATE.value,
                timestamp=current_time,
                data={
                    'lead_id': f'lead_{random.randint(1000, 9999)}',
                    'score': random.randint(60, 95),
                    'previous_score': random.randint(40, 80),
                    'factors': ['engagement', 'budget_qualified', 'timeline_ready']
                },
                priority=2
            ))

        # New alert (15% chance)
        if random.random() < 0.15:
            alert_types = ['hot_lead', 'stale_lead', 'booking_reminder', 'follow_up_needed']
            events.append(RealtimeEvent(
                id=str(uuid.uuid4()),
                event_type=EventType.NEW_ALERT.value,
                timestamp=current_time,
                data={
                    'alert_type': random.choice(alert_types),
                    'message': f'New {random.choice(alert_types).replace("_", " ")} detected',
                    'lead_id': f'lead_{random.randint(1000, 9999)}',
                    'action_required': True
                },
                priority=3
            ))

        # Performance update (20% chance)
        if random.random() < 0.2:
            events.append(RealtimeEvent(
                id=str(uuid.uuid4()),
                event_type=EventType.PERFORMANCE_UPDATE.value,
                timestamp=current_time,
                data={
                    'agent_id': f'agent_{random.randint(1, 10)}',
                    'metric': random.choice(['calls_made', 'emails_sent', 'meetings_booked']),
                    'value': random.randint(1, 50),
                    'trend': random.choice(['up', 'down', 'stable'])
                },
                priority=1
            ))

        return events

    def _process_event(self, event: RealtimeEvent):
        """Process incoming event"""
        # Check for duplicates
        event_key = f"{event.event_type}_{event.data.get('lead_id', 'unknown')}"

        if event_key in self.event_cache:
            # Check if this is a duplicate within 30 seconds
            cached_event = self.event_cache[event_key]
            if (event.timestamp - cached_event.timestamp).total_seconds() < 30:
                self.metrics['cache_hits'] += 1
                return  # Skip duplicate

        self.metrics['cache_misses'] += 1
        self.metrics['events_processed'] += 1

        # Add to queue and cache
        self.event_queue.append(event)
        self.event_cache[event_key] = event

        # Maintain queue size
        if len(self.event_queue) > self.max_events:
            self.event_queue = self.event_queue[-self.max_events:]

        # Notify subscribers
        self._notify_subscribers(event)

    def _notify_subscribers(self, event: RealtimeEvent):
        """Notify all subscribers of new event"""
        event_type = event.event_type

        # Notify specific event type subscribers
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Error in subscriber callback: {e}")

        # Notify all-events subscribers
        if 'all' in self.subscribers:
            for callback in self.subscribers['all']:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Error in all-events callback: {e}")

        self.metrics['events_sent'] += len(
            self.subscribers.get(event_type, []) + self.subscribers.get('all', [])
        )

    def subscribe(self, event_type: str, callback: Callable[[RealtimeEvent], None]) -> str:
        """Subscribe to events"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []

        self.subscribers[event_type].append(callback)

        # Return subscription ID for unsubscribing
        return f"{event_type}_{len(self.subscribers[event_type])}"

    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from events"""
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(callback)
            except ValueError:
                pass  # Callback not found

    def get_recent_events(self,
                         event_type: Optional[str] = None,
                         limit: int = 50,
                         since: Optional[datetime] = None) -> List[RealtimeEvent]:
        """Get recent events"""
        events = self.event_queue

        # Filter by event type
        if event_type:
            events = [e for e in events if e.event_type == event_type]

        # Filter by time
        if since:
            events = [e for e in events if e.timestamp > since]

        # Sort by timestamp and limit
        events = sorted(events, key=lambda x: x.timestamp, reverse=True)[:limit]

        return events

    def emit_event(self, event_type: str, data: Dict[str, Any], priority: int = 1):
        """Emit a custom event"""
        event = RealtimeEvent(
            id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.now(),
            data=data,
            priority=priority,
            source="user"
        )

        self._process_event(event)

    def get_metrics(self) -> Dict[str, Any]:
        """Get service performance metrics"""
        return {
            **self.metrics,
            'is_running': self.is_running,
            'use_websocket': self.use_websocket,
            'websockets_available': WEBSOCKETS_AVAILABLE,
            'queue_size': len(self.event_queue),
            'cache_size': len(self.event_cache),
            'subscribers': {k: len(v) for k, v in self.subscribers.items()},
            'uptime_seconds': (datetime.now() - self.last_poll_time).total_seconds()
        }

    def clear_cache(self):
        """Clear event cache"""
        self.event_cache.clear()
        self.metrics['cache_hits'] = 0
        self.metrics['cache_misses'] = 0


# Singleton instance for global access
_realtime_service_instance = None

def get_realtime_service(use_websocket: bool = True, poll_interval: int = 2) -> RealtimeDataService:
    """Get or create singleton real-time service instance"""
    global _realtime_service_instance

    if _realtime_service_instance is None:
        _realtime_service_instance = RealtimeDataService(use_websocket, poll_interval)
        _realtime_service_instance.start()

    return _realtime_service_instance


# Streamlit helper functions
def init_realtime_dashboard():
    """Initialize real-time dashboard in Streamlit"""
    if 'realtime_initialized' not in st.session_state:
        st.session_state.realtime_service = get_realtime_service()
        st.session_state.realtime_initialized = True

        # Auto-refresh every 2 seconds
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = True

    return st.session_state.realtime_service

@st.cache_data(ttl=1)  # Cache for 1 second to prevent excessive API calls
def get_cached_events(event_type: Optional[str] = None, limit: int = 50):
    """Get cached events with Streamlit caching"""
    service = get_realtime_service()
    return [event.to_dict() for event in service.get_recent_events(event_type, limit)]


# Demo data generators for testing
class DemoDataGenerator:
    """Generate realistic demo data for dashboard testing"""

    @staticmethod
    def generate_lead_scores(count: int = 10) -> List[Dict[str, Any]]:
        """Generate sample lead scores"""
        import random

        leads = []
        for i in range(count):
            score = random.randint(30, 95)
            leads.append({
                'id': f'lead_{1000 + i}',
                'name': f'Lead {i + 1}',
                'score': score,
                'previous_score': score + random.randint(-15, 15),
                'status': 'hot' if score > 80 else 'warm' if score > 60 else 'cold',
                'factors': random.sample([
                    'budget_qualified', 'timeline_ready', 'decision_maker',
                    'high_engagement', 'referral_source', 'repeat_customer'
                ], random.randint(2, 4)),
                'last_activity': datetime.now() - timedelta(minutes=random.randint(1, 60))
            })

        return leads

    @staticmethod
    def generate_alerts(count: int = 5) -> List[Dict[str, Any]]:
        """Generate sample alerts"""
        import random

        alert_types = [
            {'type': 'hot_lead', 'message': 'Hot lead needs immediate attention', 'priority': 4},
            {'type': 'stale_lead', 'message': 'Lead has been inactive for 7 days', 'priority': 2},
            {'type': 'booking_reminder', 'message': 'Upcoming appointment in 30 minutes', 'priority': 3},
            {'type': 'follow_up_needed', 'message': 'Follow-up call scheduled for today', 'priority': 2},
            {'type': 'budget_qualified', 'message': 'Lead confirmed budget over $500k', 'priority': 3}
        ]

        alerts = []
        for i in range(count):
            alert_type = random.choice(alert_types)
            alerts.append({
                'id': f'alert_{i + 1}',
                'type': alert_type['type'],
                'message': alert_type['message'],
                'priority': alert_type['priority'],
                'timestamp': datetime.now() - timedelta(minutes=random.randint(1, 30)),
                'lead_id': f'lead_{random.randint(1000, 1100)}',
                'read': random.choice([True, False])
            })

        return alerts

    @staticmethod
    def generate_performance_metrics() -> Dict[str, Any]:
        """Generate sample performance metrics"""
        import random

        return {
            'total_leads': random.randint(150, 300),
            'hot_leads': random.randint(20, 50),
            'conversion_rate': round(random.uniform(15, 35), 1),
            'avg_response_time': random.randint(5, 45),
            'calls_made_today': random.randint(25, 100),
            'emails_sent_today': random.randint(50, 200),
            'meetings_booked_today': random.randint(3, 15),
            'revenue_pipeline': random.randint(500000, 2000000),
            'deals_closed_this_month': random.randint(5, 25)
        }