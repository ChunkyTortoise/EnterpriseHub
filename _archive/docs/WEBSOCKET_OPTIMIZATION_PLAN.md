# WebSocket Event Streaming Optimization Plan
## Target: <10ms Event Delivery Latency for Enterprise Scale

### **Current Performance Baseline**

| Component | Current Performance | Target Performance |
|-----------|-------------------|------------------|
| Backend Batch Interval | 500ms | 5-10ms |
| Frontend Latency Threshold | 5000ms | 50ms warning, 100ms critical |
| Reconnection Delay | 5000ms | 1000-2000ms with exponential backoff |
| Event Processing | Sequential | Parallel with priority lanes |
| Connection Monitoring | 1000ms | 500ms with smart intervals |

### **Phase 1: Backend Event Publisher Optimization**

#### **1.1 Micro-Batching Implementation**
```python
# ghl_real_estate_ai/services/event_publisher.py
class EventPublisher:
    def __init__(self):
        # Ultra-low latency configuration
        self.batch_interval = 0.01  # 10ms maximum delay
        self.max_batch_size = 50    # Increased capacity
        self.critical_bypass = True # Critical events bypass batching

        # Priority-based processing lanes
        self.critical_queue = asyncio.Queue()
        self.high_queue = asyncio.Queue()
        self.normal_queue = asyncio.Queue()

        # Performance monitoring
        self.latency_tracking = []
        self.throughput_metrics = {}
```

#### **1.2 Priority Lane Processing**
```python
async def _process_event_batch(self):
    """Process events with priority lane optimization."""
    start_time = time.perf_counter()

    # Process critical events immediately (no batching)
    while not self.critical_queue.empty():
        try:
            event = self.critical_queue.get_nowait()
            await self.websocket_manager.publish_event(event)
            self._track_event_latency(event, start_time)
        except asyncio.QueueEmpty:
            break

    # Batch process high priority events
    high_events = []
    while not self.high_queue.empty() and len(high_events) < self.max_batch_size:
        try:
            high_events.append(self.high_queue.get_nowait())
        except asyncio.QueueEmpty:
            break

    if high_events:
        await asyncio.gather(*[
            self.websocket_manager.publish_event(event)
            for event in high_events
        ])

    # Process normal events with larger batches
    await self._process_normal_events_batch()
```

#### **1.3 Event Latency Tracking**
```python
def _track_event_latency(self, event: RealTimeEvent, start_time: float):
    """Track per-event delivery latency."""
    end_time = time.perf_counter()
    latency_ms = (end_time - start_time) * 1000

    self.latency_tracking.append({
        'event_type': event.event_type.value,
        'priority': event.priority,
        'latency_ms': latency_ms,
        'timestamp': event.timestamp
    })

    # Alert on high latency
    if latency_ms > 10:
        logger.warning(f"High event latency: {latency_ms:.2f}ms for {event.event_type.value}")

    # Keep only recent measurements (last 1000)
    if len(self.latency_tracking) > 1000:
        self.latency_tracking = self.latency_tracking[-1000:]
```

### **Phase 2: WebSocket Connection Optimization**

#### **2.1 Connection Pool Enhancement**
```python
# ghl_real_estate_ai/services/websocket_server.py
class WebSocketManager:
    def __init__(self):
        # Connection optimization
        self.heartbeat_interval = 15  # Reduced from 30s
        self.heartbeat_timeout = 25   # Reduced from 60s

        # Performance tracking
        self.connection_latencies = {}
        self.message_timestamps = {}

    async def send_personal_message(self, connection_id: str, message: Dict[str, Any]):
        """Optimized message sending with latency tracking."""
        if connection_id not in self.active_connections:
            return

        client = self.active_connections[connection_id]
        send_start = time.perf_counter()

        try:
            # Add timestamp for latency measurement
            message['_server_timestamp'] = time.time() * 1000  # milliseconds

            await client.websocket.send_text(json.dumps(message))

            # Track send latency
            send_latency = (time.perf_counter() - send_start) * 1000
            self.connection_latencies[connection_id] = send_latency

            self.metrics["messages_sent"] += 1

            # Alert on high send latency
            if send_latency > 5.0:  # 5ms warning threshold
                logger.warning(f"High send latency: {send_latency:.2f}ms to {connection_id}")

        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {e}")
            await self.disconnect(connection_id)
```

#### **2.2 Smart Heartbeat System**
```python
async def _heartbeat_monitor(self):
    """Enhanced heartbeat monitoring with adaptive intervals."""
    while True:
        try:
            current_time = datetime.now(timezone.utc)

            # Adaptive heartbeat based on connection health
            for connection_id, client in self.active_connections.items():
                connection_latency = self.connection_latencies.get(connection_id, 0)

                # Increase heartbeat frequency for high-latency connections
                if connection_latency > 10:  # 10ms threshold
                    heartbeat_interval = 10  # More frequent for problematic connections
                else:
                    heartbeat_interval = self.heartbeat_interval

                time_since_heartbeat = (current_time - client.last_heartbeat).total_seconds()

                if time_since_heartbeat > heartbeat_interval:
                    await self._send_heartbeat_ping(connection_id)

        except Exception as e:
            logger.error(f"Heartbeat monitor error: {e}")

        await asyncio.sleep(5)  # Check every 5 seconds
```

### **Phase 3: Frontend Performance Optimization**

#### **3.1 Enhanced WebSocket Manager**
```typescript
// enterprise-ui/src/lib/socket.ts
class SocketManager {
  private latencyTracking: Array<{
    sent_at: number;
    received_at: number;
    latency_ms: number;
    event_type: string;
  }> = [];

  private setupConnectionMonitoring(): void {
    // Reduced monitoring interval for better responsiveness
    setInterval(() => {
      if (this.socket?.connected) {
        const pingTime = Date.now();
        this.socket.emit('ping', { timestamp: pingTime, client_id: this.clientId });
      }
    }, 15000); // 15 second ping interval

    // Enhanced pong handling with latency tracking
    this.socket?.on('pong', (data) => {
      const receiveTime = Date.now();
      const latency = receiveTime - data.timestamp;

      this.latencyTracking.push({
        sent_at: data.timestamp,
        received_at: receiveTime,
        latency_ms: latency,
        event_type: 'heartbeat'
      });

      // Progressive latency warnings
      if (latency > 100) {
        console.error('🚨 Critical socket latency:', latency, 'ms');
        this.emit('connection_degraded', { latency, severity: 'critical' });
      } else if (latency > 50) {
        console.warn('⚠️ High socket latency:', latency, 'ms');
        this.emit('connection_degraded', { latency, severity: 'warning' });
      }

      // Keep last 100 measurements
      if (this.latencyTracking.length > 100) {
        this.latencyTracking = this.latencyTracking.slice(-100);
      }
    });
  }

  // Enhanced message handling with client-side latency tracking
  private setupBotEventHandlers() {
    if (!this.socket) return;

    this.socket.onAny((eventName: string, eventData: any) => {
      const clientReceiveTime = Date.now();

      // Calculate end-to-end latency if server timestamp is available
      if (eventData._server_timestamp) {
        const endToEndLatency = clientReceiveTime - eventData._server_timestamp;

        this.latencyTracking.push({
          sent_at: eventData._server_timestamp,
          received_at: clientReceiveTime,
          latency_ms: endToEndLatency,
          event_type: eventName
        });

        // Real-time latency monitoring
        if (endToEndLatency > 10) {
          console.warn(`High event latency: ${endToEndLatency}ms for ${eventName}`);
        }

        // Remove server timestamp before processing
        delete eventData._server_timestamp;
      }

      // Emit to application handlers
      this.emit(eventName, eventData);
    });
  }
}
```

#### **3.2 Intelligent Reconnection Strategy**
```typescript
// enterprise-ui/src/components/providers/WebSocketProvider.tsx
const connect = async () => {
  try {
    setConnectionState('connecting');

    // Progressive timeout based on attempt number
    const baseTimeout = 2000; // 2 seconds base
    const maxTimeout = 15000; // 15 seconds max
    const timeout = Math.min(baseTimeout * Math.pow(1.2, reconnectAttempts), maxTimeout);

    await socketManager.connect();

    setConnected(true);
    setConnectionState('connected');
    setReconnectAttempts(0); // Reset on successful connection

  } catch (err: any) {
    setConnectionState('error');
    setConnected(false);

    // Intelligent backoff with jitter
    if (reconnectAttempts < maxReconnectAttempts) {
      const jitter = Math.random() * 1000; // 0-1 second jitter
      const delay = Math.min(1000 * Math.pow(1.5, reconnectAttempts) + jitter, 30000);

      setTimeout(() => {
        setReconnectAttempts(prev => prev + 1);
        connect();
      }, delay);
    }
  }
};
```

### **Phase 4: Event Batching and Filtering Optimization**

#### **4.1 Smart Event Aggregation**
```python
def _aggregate_similar_events(self, events: List[RealTimeEvent]) -> List[RealTimeEvent]:
    """Intelligent event aggregation to reduce message volume."""
    aggregated = {}
    standalone_events = []

    for event in events:
        # AI Concierge events can be aggregated by contact
        if event.event_type in [EventType.PROACTIVE_INSIGHT, EventType.STRATEGY_RECOMMENDATION]:
            key = f"{event.event_type.value}_{event.user_id}_{event.location_id}"

            if key not in aggregated:
                aggregated[key] = {
                    'base_event': event,
                    'insights': [],
                    'latest_timestamp': event.timestamp
                }

            aggregated[key]['insights'].append(event.data)
            if event.timestamp > aggregated[key]['latest_timestamp']:
                aggregated[key]['latest_timestamp'] = event.timestamp
        else:
            # Critical events never get aggregated
            standalone_events.append(event)

    # Create aggregated events
    final_events = standalone_events.copy()

    for agg_data in aggregated.values():
        base_event = agg_data['base_event']
        aggregated_event = RealTimeEvent(
            event_type=base_event.event_type,
            data={
                'aggregated_insights': agg_data['insights'],
                'insight_count': len(agg_data['insights']),
                'time_window': f"{base_event.timestamp} to {agg_data['latest_timestamp']}"
            },
            timestamp=agg_data['latest_timestamp'],
            user_id=base_event.user_id,
            location_id=base_event.location_id,
            priority=base_event.priority
        )
        final_events.append(aggregated_event)

    return final_events
```

### **Phase 5: Performance Monitoring and Alerting**

#### **5.1 Real-time Performance Dashboard**
```python
# ghl_real_estate_ai/api/routes/websocket_performance.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

router = APIRouter(prefix="/api/v1/websocket-performance", tags=["WebSocket Performance"])

@router.get("/latency-metrics")
async def get_latency_metrics() -> Dict[str, Any]:
    """Get real-time WebSocket latency metrics."""
    publisher = get_event_publisher()
    websocket_manager = get_websocket_manager()

    latency_data = publisher.latency_tracking[-100:]  # Last 100 events

    if not latency_data:
        return {"message": "No latency data available"}

    # Calculate statistics
    latencies = [event['latency_ms'] for event in latency_data]

    return {
        "current_stats": {
            "avg_latency_ms": sum(latencies) / len(latencies),
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies),
            "p95_latency_ms": sorted(latencies)[int(len(latencies) * 0.95)],
            "p99_latency_ms": sorted(latencies)[int(len(latencies) * 0.99)]
        },
        "target_compliance": {
            "under_10ms_percentage": len([l for l in latencies if l < 10]) / len(latencies) * 100,
            "under_50ms_percentage": len([l for l in latencies if l < 50]) / len(latencies) * 100
        },
        "by_event_type": {
            event_type: {
                "count": len([e for e in latency_data if e['event_type'] == event_type]),
                "avg_latency": sum([e['latency_ms'] for e in latency_data if e['event_type'] == event_type]) /
                              max(1, len([e for e in latency_data if e['event_type'] == event_type]))
            }
            for event_type in set(e['event_type'] for e in latency_data)
        },
        "connection_health": websocket_manager.get_connection_health_summary()
    }

@router.get("/throughput-metrics")
async def get_throughput_metrics() -> Dict[str, Any]:
    """Get WebSocket message throughput metrics."""
    websocket_manager = get_websocket_manager()
    metrics = websocket_manager.get_metrics()

    return {
        "active_connections": metrics["active_connections"],
        "messages_per_second": metrics.get("messages_per_second", 0),
        "events_per_second": metrics.get("events_per_second", 0),
        "queue_depth": metrics.get("queue_size", 0),
        "connection_distribution": metrics["active_connections_by_role"]
    }
```

### **Phase 6: Mobile and Offline Optimization**

#### **6.1 Service Worker Integration**
```javascript
// enterprise-ui/public/sw-websocket.js
self.addEventListener('message', async (event) => {
  if (event.data.type === 'WEBSOCKET_MESSAGE') {
    // Cache critical AI insights for offline access
    if (event.data.event_type === 'proactive_insight' ||
        event.data.event_type === 'coaching_opportunity') {

      const cache = await caches.open('ai-insights-v1');
      await cache.put(
        `/insights/${event.data.data.insight_id}`,
        new Response(JSON.stringify(event.data))
      );
    }

    // Background sync for failed WebSocket sends
    if (event.data.failed_send) {
      await self.registration.sync.register('websocket-retry');
    }
  }
});

self.addEventListener('sync', async (event) => {
  if (event.tag === 'websocket-retry') {
    // Retry failed WebSocket operations
    event.waitUntil(retryFailedWebSocketOperations());
  }
});
```

### **Implementation Timeline**

| Phase | Duration | Priority | Performance Impact |
|-------|----------|----------|-------------------|
| Phase 1: Backend Optimization | 3-4 days | Critical | 70% latency reduction |
| Phase 2: Connection Optimization | 2-3 days | High | 20% latency reduction |
| Phase 3: Frontend Optimization | 2-3 days | High | 15% latency reduction |
| Phase 4: Event Optimization | 1-2 days | Medium | 10% throughput increase |
| Phase 5: Performance Monitoring | 2-3 days | Medium | Observability |
| Phase 6: Mobile Optimization | 3-4 days | Low | Mobile performance |

### **Success Metrics**

#### **Primary KPIs**
- **Event Delivery Latency**: <10ms for 95% of events
- **Connection Recovery**: <2s for reconnection
- **Throughput**: >10,000 events/second sustained
- **Connection Stability**: >99.9% uptime

#### **Secondary KPIs**
- **Memory Usage**: <50MB WebSocket buffer
- **CPU Usage**: <5% for WebSocket processing
- **Network Efficiency**: <1KB average message size
- **Mobile Performance**: <20ms additional latency on mobile

### **Next Steps**

1. **Start with Phase 1** - Backend optimization has the highest impact
2. **Implement gradual rollout** - Test with 10% of connections first
3. **Monitor performance metrics** - Track improvements in real-time
4. **Load testing** - Validate under enterprise scale (1000+ concurrent connections)
5. **Documentation** - Update performance guarantees and SLA documentation